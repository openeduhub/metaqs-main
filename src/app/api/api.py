import json
import uuid
from typing import List, Mapping, Optional
from uuid import UUID

from databases import Database
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from starlette.requests import Request
from starlette.status import HTTP_200_OK, HTTP_404_NOT_FOUND

from app.api.collections.tree import (
    PORTAL_ROOT_ID,
    PortalTreeNode,
    collection_tree,
    portal_id_with_root_param,
)
from app.api.quality_matrix.collections import collection_quality_matrix
from app.api.quality_matrix.models import ColumnOutputModel, Timeline
from app.api.quality_matrix.quality_matrix import quality_matrix, stored_in_timeline
from app.api.quality_matrix.timeline import timestamps
from app.api.quality_matrix.utils import transpose
from app.api.score.models import ScoreOutput
from app.api.score.score import (
    calc_scores,
    calc_weighted_score,
    collection_id_param,
    query_score,
)
from app.elastic.elastic import (
    ResourceType,
    aggs_collection_validation,
    aggs_material_validation,
    field_names_used_for_score_calculation,
)


def get_database(request: Request) -> Database:
    return request.app.state._db


router = APIRouter()

QUALITY_MATRIX_DESCRIPTION = """Calculation of the quality matrix.
    For each replication source and each property, e.g., `cm:creator`, the quality matrix returns the ratio of
    elements which miss this entry compared to the total number of entries.
    A missing entry may be `cm:creator = null`.
    Additional parameters:
        store_to_db: Default False. Causes returned quality matrix to also be stored in the backend database."""

TAG_STATISTICS = "Statistics"


@router.get(
    "/collection_quality_matrix",
    status_code=HTTP_200_OK,
    response_model=List[ColumnOutputModel],
    responses={HTTP_404_NOT_FOUND: {"description": "Quality matrix not determinable"}},
    tags=[TAG_STATISTICS],
    description=QUALITY_MATRIX_DESCRIPTION,
)
async def get_collection_quality_matrix(
    database: Database = Depends(get_database),
    node_id: Optional[str] = PORTAL_ROOT_ID,
    # Using UUID here leads to https://github.com/OpenAPITools/openapi-generator/issues/3516
    store_to_db=False,
    transpose_output=True,
):
    _quality_matrix = await collection_quality_matrix(uuid.UUID(node_id))
    if transpose_output:
        _quality_matrix = transpose(_quality_matrix)
    if store_to_db and node_id == PORTAL_ROOT_ID:  # only store standard case
        await stored_in_timeline(_quality_matrix, database)
    return _quality_matrix


@router.get(
    "/quality_matrix",
    status_code=HTTP_200_OK,
    response_model=List[ColumnOutputModel],
    responses={HTTP_404_NOT_FOUND: {"description": "Quality matrix not determinable"}},
    tags=[TAG_STATISTICS],
    description=QUALITY_MATRIX_DESCRIPTION,
)
async def get_quality_matrix(
    database: Database = Depends(get_database),
    store_to_db=False,
):
    _quality_matrix = await quality_matrix()
    if store_to_db:
        await stored_in_timeline(_quality_matrix, database)
    return _quality_matrix


@router.get(
    "/quality_matrix/{timestamp}",
    status_code=HTTP_200_OK,
    response_model=List[ColumnOutputModel],
    responses={HTTP_404_NOT_FOUND: {"description": "Quality matrix not determinable"}},
    tags=[TAG_STATISTICS],
    description=QUALITY_MATRIX_DESCRIPTION
    + """An unix timestamp in integer seconds since epoch yields the quality matrix at the respective date.""",
)
async def get_past_quality_matrix(
    timestamp: int, database: Database = Depends(get_database)
):
    if not timestamp:
        raise HTTPException(status_code=400, detail="Invalid or no timestamp given")

    s = select([Timeline]).where(Timeline.timestamp == timestamp)
    await database.connect()
    result: list[Mapping[Timeline]] = await database.fetch_all(s)
    await database.disconnect()

    if len(result) == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    elif len(result) > 1:
        raise HTTPException(status_code=500, detail="More than one item found")
    return json.loads(result[0].quality_matrix)


@router.get(
    "/quality_matrix_timestamps",
    status_code=HTTP_200_OK,
    response_model=List[int],
    responses={
        HTTP_404_NOT_FOUND: {
            "description": "Timestamps of old quality matrix results not determinable"
        }
    },
    tags=[TAG_STATISTICS],
    description="""Return timestamps of the format XYZ of past calculations of the quality matrix.""",
)
async def get_timestamps(database: Database = Depends(get_database)):
    return await timestamps(database)


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
    collection_stats = await query_score(
        noderef_id=collection_id, resource_type=ResourceType.COLLECTION
    )

    collection_scores = calc_scores(stats=collection_stats)

    material_stats = await query_score(
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
    response_model=List[PortalTreeNode],
    status_code=HTTP_200_OK,
    responses={HTTP_404_NOT_FOUND: {"description": "Collection not found"}},
    tags=["Collections"],
)
async def get_portal_tree(*, node_id: UUID = Depends(portal_id_with_root_param)):
    return await collection_tree(node_id)
