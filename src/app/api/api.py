import json
import uuid
from typing import Mapping
from uuid import UUID

from databases import Database
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi.params import Param
from pydantic import BaseModel, Field
from sqlalchemy import select
from starlette.requests import Request
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from app.api.collections.counts import (
    AggregationMappings,
    PortalTreeCount,
    portal_counts,
)
from app.api.collections.models import CollectionNode
from app.api.collections.tree import collection_tree
from app.api.quality_matrix.collections import collection_quality
from app.api.quality_matrix.models import ColumnOutputModel, Forms, Timeline
from app.api.quality_matrix.quality_matrix import source_quality, store_in_timeline
from app.api.quality_matrix.timeline import timestamps
from app.api.quality_matrix.utils import transpose
from app.api.score.models import ScoreOutput
from app.api.score.score import (
    aggs_collection_validation,
    aggs_material_validation,
    calc_scores,
    calc_weighted_score,
    collection_id_param,
    field_names_used_for_score_calculation,
    search_score,
)
from app.core.constants import COLLECTION_NAME_TO_ID, COLLECTION_ROOT_ID
from app.elastic.elastic import ResourceType


def get_database(request: Request) -> Database:
    return request.app.state._db


router = APIRouter()

QUALITY_MATRIX_DESCRIPTION = """Calculation of the quality matrix.
    Depending on the chosen form the quality matrix returns the ratio of entries which miss this property compared to
    the total number of entries.
    A missing entry may be `cm:creator = null`.
    Additional parameters:
        node_id: Default collection root id. Node id of the collection for which to evaluate the quality.
        store_to_db: Default False. Causes returned quality matrix to also be stored in the backend database.
        forms: Default replication source. Choose what type of quality determination you want.
        transpose_output: Default false. Transpose the output matrix.

    The user chooses the node id in the editorial environment (german: Redaktionsumgebung) in the "Fach" selection.
    """

TAG_STATISTICS = "Statistics"


def node_ids_for_major_collections(
    *,
    node_id: UUID = Path(
        ...,
        examples={
            "Alle Fachportale": {"value": COLLECTION_ROOT_ID},
            **COLLECTION_NAME_TO_ID,
        },
    ),
) -> UUID:
    return node_id


@router.get(
    "/quality",
    status_code=HTTP_200_OK,
    response_model=list[ColumnOutputModel],
    responses={HTTP_404_NOT_FOUND: {"description": "Quality matrix not determinable"}},
    tags=[TAG_STATISTICS],
    description=QUALITY_MATRIX_DESCRIPTION,
)
async def get_quality(
    database: Database = Depends(get_database),
    node_id: str = Query(
        default=COLLECTION_ROOT_ID,
        examples={
            "Alle Fachportale": {"value": COLLECTION_ROOT_ID},
            **COLLECTION_NAME_TO_ID,
        },
    ),
    store_to_db: bool = Query(default=False),
    form: Forms = Query(
        default=Forms.REPLICATION_SOURCE,
        examples={form: {"value": form} for form in Forms},
    ),
    transpose_output: bool = Query(default=False),
):
    if form == Forms.REPLICATION_SOURCE:
        _quality_matrix = await source_quality(uuid.UUID(node_id))
    elif form == Forms.COLLECTIONS:
        _quality_matrix = await collection_quality(uuid.UUID(node_id))
        _quality_matrix = transpose(_quality_matrix)
    else:
        return HTTP_400_BAD_REQUEST
    if transpose_output:
        _quality_matrix = transpose(_quality_matrix)
    if store_to_db:
        await store_in_timeline(_quality_matrix, database, form)
    return _quality_matrix


@router.get(
    "/quality/{timestamp}",
    status_code=HTTP_200_OK,
    response_model=list[ColumnOutputModel],
    responses={HTTP_404_NOT_FOUND: {"description": "Quality matrix not determinable"}},
    tags=[TAG_STATISTICS],
    description="""An unix timestamp in integer seconds since epoch yields the quality matrix at the respective date.""",
)
async def get_past_quality_matrix(
    timestamp: int, database: Database = Depends(get_database)
):
    if not timestamp:
        raise HTTPException(status_code=400, detail="Invalid or no timestamp given")

    s = select([Timeline]).where(Timeline.timestamp == timestamp)
    await database.connect()
    result: list[Mapping[Timeline]] = await database.fetch_all(s)

    if len(result) == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    elif len(result) > 1:
        raise HTTPException(status_code=500, detail="More than one item found")
    return json.loads(result[0].quality_matrix)


@router.get(
    "/quality_timestamps",
    status_code=HTTP_200_OK,
    response_model=list[int],
    responses={
        HTTP_404_NOT_FOUND: {
            "description": "Timestamps of old quality matrix results not determinable"
        }
    },
    tags=[TAG_STATISTICS],
    description="""Return timestamps in seconds since epoch of past calculations of the quality matrix.
    Additional parameters:
        form: The desired form of quality. This is used to query only the relevant type of data.""",
)
async def get_timestamps(
    database: Database = Depends(get_database),
    form: Forms = Query(
        default=Forms.REPLICATION_SOURCE,
        examples={form: {"value": form} for form in Forms},
    ),
):
    return await timestamps(database, form)


@router.get(
    "/collections/{collection_id}/stats/score",
    response_model=ScoreOutput,
    status_code=HTTP_200_OK,
    responses={HTTP_404_NOT_FOUND: {"description": "Collection not found"}},
    tags=[TAG_STATISTICS],
    description=f"""Returns the average ratio of non-empty properties for the chosen collection.
    For certain properties, e.g. `properties.cclom:title`, the ratio of
    elements which miss this entry compared to the total number of entries is calculated.
    A missing entry may be `properties.cclom:title = null`. Not all properties are considered here.
    The overall score is the average of all these ratios.
    The queried properties are:
    `{field_names_used_for_score_calculation(aggs_collection_validation)
      + field_names_used_for_score_calculation(aggs_material_validation)}`.
    """,
)
async def score(*, collection_id: UUID = Depends(collection_id_param)):
    collection_stats = await search_score(
        noderef_id=collection_id, resource_type=ResourceType.COLLECTION
    )

    collection_scores = calc_scores(stats=collection_stats)

    material_stats = await search_score(
        noderef_id=collection_id, resource_type=ResourceType.MATERIAL
    )

    material_scores = calc_scores(stats=material_stats)

    score_ = calc_weighted_score(
        collection_scores=collection_scores,
        material_scores=material_scores,
    )

    return {
        "score": score_,
        "collections": {"total": collection_stats["total"], **collection_scores},
        "materials": {"total": material_stats["total"], **material_scores},
    }


class Ping(BaseModel):
    status: str = Field(
        default="not ok",
        description="Ping output. Should be 'ok' in happy case.",
    )


@router.get(
    "/_ping",
    description="Ping function for automatic health check.",
    response_model=Ping,
    tags=["Healthcheck"],
)
async def ping_api():
    return {"status": "ok"}


@router.get(
    "/collections/{node_id}/tree",
    response_model=list[CollectionNode],
    status_code=HTTP_200_OK,
    responses={HTTP_404_NOT_FOUND: {"description": "Collection not found"}},
    tags=["Collections"],
)
async def gCleanupet_collection_tree(
    *, node_id: UUID = Depends(node_ids_for_major_collections)
):
    return await collection_tree(node_id)


@router.get(
    "/collections/{node_id}/counts",
    summary="Return the material counts for each collection id which this portal tree includes",
    response_model=list[PortalTreeCount],
    status_code=HTTP_200_OK,
    responses={HTTP_404_NOT_FOUND: {"description": "Collection not found"}},
    tags=["Collections"],
)
async def get_portal_counts(
    *,
    node_id: UUID = Depends(node_ids_for_major_collections),
    facet: AggregationMappings = Param(
        default=AggregationMappings.lrt,
        examples={key: {"value": key} for key in AggregationMappings},
    ),
):
    counts = await portal_counts(node_id=node_id, facet=facet)
    return counts
