import json
import uuid
from typing import Mapping

from databases import Database
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi.params import Param
from pydantic import BaseModel, Field
from sqlalchemy import select
from starlette.requests import Request
from starlette.status import (
    HTTP_200_OK,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from app.api.analytics.analytics import (
    CollectionValidationStats,
    PendingMaterialsResponse,
    StatsResponse,
    ValidationStatsResponse,
)
from app.api.analytics.stats import (
    collections_with_missing_properties,
    material_validation,
    overall_stats,
)
from app.api.analytics.storage import global_storage, global_store
from app.api.collections.counts import (
    AggregationMappings,
    CollectionTreeCount,
    oer_collection_counts,
)
from app.api.collections.material_counts import (
    CollectionMaterialsCount,
    get_material_count_tree,
)
from app.api.collections.missing_materials import (
    LearningMaterial,
    MissingAttributeFilter,
    materials_filter_params,
    search_materials_with_missing_attributes,
)
from app.api.collections.models import CollectionNode, MissingMaterials
from app.api.collections.pending_collections import (
    missing_attribute_filter,
    pending_collections,
)
from app.api.collections.tree import collection_tree
from app.api.quality_matrix.collections import collection_quality
from app.api.quality_matrix.models import Mode, QualityOutputResponse, Timeline
from app.api.quality_matrix.replication_source import source_quality
from app.api.quality_matrix.timeline import quality_backup, timestamps
from app.api.score.models import ScoreOutput
from app.api.score.score import (
    aggs_collection_validation,
    aggs_material_validation,
    field_names_used_for_score_calculation,
    get_score,
)
from app.core.config import API_DEBUG, BACKGROUND_TASK_TIME_INTERVAL
from app.core.constants import COLLECTION_NAME_TO_ID, COLLECTION_ROOT_ID


def get_database(request: Request) -> Database:
    return request.app.state._db


router = APIRouter()

_TAG_STATISTICS = "Statistics"
_TAG_COLLECTIONS = "Collections"

valid_node_ids = {
    "Alle Fachportale": {"value": COLLECTION_ROOT_ID},
    **{key: {"value": value} for key, value in COLLECTION_NAME_TO_ID.items()},
}


def validate_node_id(node_id: uuid.UUID):
    if str(node_id) not in {value["value"] for value in valid_node_ids.values()}:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="Node id invalid"
        )


def node_ids_for_major_collections(
    *,
    node_id: uuid.UUID = Path(
        default=...,
        examples=valid_node_ids,
    ),
) -> uuid.UUID:
    return node_id


@router.get(
    "/quality",
    status_code=HTTP_200_OK,
    response_model=QualityOutputResponse,
    responses={HTTP_404_NOT_FOUND: {"description": "Quality matrix not determinable"}},
    tags=[_TAG_STATISTICS],
)
async def get_quality(
    *,
    node_id: str = Query(
        default=...,
        examples=valid_node_ids,
    ),
    mode: Mode = Query(
        default=Mode.REPLICATION_SOURCE,
        examples={mode: {"value": mode} for mode in Mode},
    ),
):
    """
    Calculate the quality matrix w.r.t. the replication source, or collection.

    A quality matrix is a tabular datastructure that has two possible layouts depending on whether it is computed for
    the replication source ('replication_source') or collection ('collections').

    - For the collection quality matrix, each column correspond to metadata fields and the rows correspond to
      collections, identified via their UUID from the
      [vocabulary](https://vocabs.openeduhub.de/w3id.org/openeduhub/vocabs/discipline/index.html).
    - For the replication source quality matrix, the columns correspond to the replication source (e.g. "YouTube",
      "Wikipedia", ...), the rows correspond to the metadata fields.

    For both cases, the individual cells hold the rations of materials where the metadata is "OK". The definition of
    "OK" depends on the meta data field (e.g. "non-empty string" for the title of a material).

    Parameters:

    - node_id: The toplevel collection for which to compute the quality matrix.
                It must come from the collection
                [vocabulary](https://vocabs.openeduhub.de/w3id.org/openeduhub/vocabs/discipline/index.html).
                In the "collections" mode, this essentially defines the rows of the output matrix.
                It serves as an overall filter for materials in both cases.
    - Mode: Defines the mode of the quality matrix, i.e. whether to compute the collection ("collections") or
            replication source ("replication_source"). Defaults to "replication_source".
    """
    validate_node_id(uuid.UUID(node_id))
    if mode == Mode.REPLICATION_SOURCE:
        quality_data, total = await source_quality(uuid.UUID(node_id))
    else:  # Mode.COLLECTIONS:
        quality_data, total = await collection_quality(uuid.UUID(node_id))
    return {"data": quality_data, "total": total}


@router.get(
    "/quality/backup",
    status_code=HTTP_200_OK,
    responses={HTTP_404_NOT_FOUND: {"description": "Quality matrix not determinable"}},
    tags=[_TAG_STATISTICS],
)
async def get_quality_backup(
    *,
    database: Database = Depends(get_database),
):
    await quality_backup(database)


@router.get(
    "/quality/{timestamp}",
    status_code=HTTP_200_OK,
    response_model=QualityOutputResponse,
    responses={HTTP_404_NOT_FOUND: {"description": "Quality matrix not determinable"}},
    tags=[_TAG_STATISTICS],
)
async def get_past_quality_matrix(
    *,
    timestamp: int,
    database: Database = Depends(get_database),
    mode: Mode = Query(
        default=Mode.REPLICATION_SOURCE,
        examples={mode: {"value": mode} for mode in Mode},
    ),
    node_id: str = Query(
        default=...,
        examples=valid_node_ids,
    ),
):
    """
    Return the quality matrix for the given timestamp.

    This endpoint serves as a comparison to the current quality matrix. This way, differences due to automatic or
    manual work on the metadata can be seen.
    """
    validate_node_id(uuid.UUID(node_id))
    if not timestamp:
        raise HTTPException(status_code=400, detail="Invalid or no timestamp given")

    s = (
        select([Timeline])
        .where(Timeline.timestamp == timestamp)
        .where(Timeline.mode == mode)
        .where(Timeline.node_id == node_id)
    )
    await database.connect()
    result: list[Mapping[Timeline]] = await database.fetch_all(s)

    if len(result) == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    elif len(result) > 1:
        raise HTTPException(status_code=500, detail="More than one item found")

    quality = json.loads(result[0].quality)
    total = json.loads(result[0].total)
    return QualityOutputResponse(data=quality, total=total)


@router.get(
    "/quality_timestamps",
    status_code=HTTP_200_OK,
    response_model=list[int],
    responses={
        HTTP_404_NOT_FOUND: {
            "description": "Timestamps of old quality matrix results not determinable"
        }
    },
    tags=[_TAG_STATISTICS],
    description="""Return timestamps in seconds since epoch of past calculations of the quality matrix.
    Additional parameters:
        mode: The desired mode of quality. This is used to query only the relevant type of data.""",
)
async def get_timestamps(
    *,
    database: Database = Depends(get_database),
    mode: Mode = Query(
        default=Mode.REPLICATION_SOURCE,
        examples={mode: {"value": mode} for mode in Mode},
    ),
    node_id: str = Query(
        default=...,
        examples=valid_node_ids,
    ),
):
    validate_node_id(uuid.UUID(node_id))
    return await timestamps(database, mode, uuid.UUID(node_id))


@router.get(
    "/collections/{node_id}/score",
    response_model=ScoreOutput,
    status_code=HTTP_200_OK,
    responses={HTTP_404_NOT_FOUND: {"description": "Collection not found"}},
    tags=[_TAG_COLLECTIONS],
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
async def score(*, node_id: uuid.UUID = Depends(node_ids_for_major_collections)):
    validate_node_id(node_id)
    return await get_score(node_id)


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
    tags=[_TAG_COLLECTIONS],
    description="Returns the tree of collections.",
)
async def get_collection_tree(
    *, node_id: uuid.UUID = Depends(node_ids_for_major_collections)
):
    validate_node_id(node_id)
    return await collection_tree(node_id)


@router.get(
    "/collections/{node_id}/counts",
    summary="Return the material counts for each collection id which this collection tree includes",
    response_model=list[CollectionTreeCount],
    status_code=HTTP_200_OK,
    responses={HTTP_404_NOT_FOUND: {"description": "Collection not found"}},
    tags=[_TAG_COLLECTIONS],
)
async def get_collection_counts(
    *,
    node_id: uuid.UUID = Depends(node_ids_for_major_collections),
    facet: AggregationMappings = Param(
        default=AggregationMappings.lrt,
        examples={key: {"value": key} for key in AggregationMappings},
    ),
):
    validate_node_id(node_id)
    return await oer_collection_counts(node_id=node_id, facet=facet)


@router.get(
    "/collections/{node_id}/pending-subcollections/{missing_attribute}",
    response_model=list[MissingMaterials],
    response_model_exclude_unset=True,
    status_code=HTTP_200_OK,
    responses={HTTP_404_NOT_FOUND: {"description": "Collection not found"}},
    tags=[_TAG_COLLECTIONS],
    description="""A list of missing entries for different types of materials by subcollection.
    Searches for entries with one of the following properties being empty or missing: """
    + f"{', '.join([entry.value for entry in missing_attribute_filter])}.",
)
async def filter_pending_collections(
    *,
    node_id: uuid.UUID = Depends(node_ids_for_major_collections),
    missing_attribute: str = Path(
        ...,
        examples={
            form.name: {"value": form.value} for form in missing_attribute_filter
        },
    ),
):
    validate_node_id(node_id)
    return await pending_collections(node_id, missing_attribute)


@router.get(
    "/collections/{node_id}/pending-materials/{missing_attr}",
    response_model=list[LearningMaterial],
    response_model_exclude_unset=True,
    status_code=HTTP_200_OK,
    responses={HTTP_404_NOT_FOUND: {"description": "Collection not found"}},
    tags=[_TAG_COLLECTIONS],
    description="""A list of missing entries for different types of materials belonging to the collection and
    its subcollectionsspecified by 'node_id'.
    Searches for materials with one of the following properties being empty or missing: """
    + f"{', '.join([entry.value for entry in missing_attribute_filter])}.",
)
async def filter_materials_with_missing_attributes(
    *,
    node_id: uuid.UUID = Depends(node_ids_for_major_collections),
    missing_attr_filter: MissingAttributeFilter = Depends(materials_filter_params),
):
    validate_node_id(node_id)
    return await search_materials_with_missing_attributes(
        node_id=node_id,
        missing_attr_filter=missing_attr_filter,
    )


@router.get(
    "/collections/{node_id}/material_counts",
    response_model=list[CollectionMaterialsCount],
    status_code=HTTP_200_OK,
    responses={HTTP_404_NOT_FOUND: {"description": "Collection not found"}},
    tags=[_TAG_COLLECTIONS],
    description="""Returns the number of materials connected to all collections
    below this 'node_id' as a flat list.""",
)
async def material_counts_tree(
    *, node_id: uuid.UUID = Depends(node_ids_for_major_collections)
):
    validate_node_id(node_id)
    return await get_material_count_tree(node_id)


@router.get(
    "/analytics/{node_id}",
    response_model=StatsResponse,
    status_code=HTTP_200_OK,
    responses={HTTP_404_NOT_FOUND: {"description": "Collection not found"}},
    tags=[_TAG_STATISTICS],
    description=f"""
    Returns the number of materials found connected to the this collection's 'node_id' and its sub
    collections as well as materials containing the name of the respective collection, e.g., in the title.
    It is therefore an overview of materials, which could be added to a collection in the future.
    It relies on background data and is read every {BACKGROUND_TASK_TIME_INTERVAL}s.
    This is the granularity of the data.""",
)
async def read_stats(
    *,
    node_id: uuid.UUID = Depends(node_ids_for_major_collections),
):
    validate_node_id(node_id)
    return await overall_stats(node_id)


@router.get(
    "/analytics/{node_id}/validation/collections",
    response_model=list[ValidationStatsResponse[CollectionValidationStats]],
    response_model_exclude_unset=True,
    status_code=HTTP_200_OK,
    responses={HTTP_404_NOT_FOUND: {"description": "Collection not found"}},
    tags=[_TAG_STATISTICS],
    description=f"""
    Returns the number of collections missing certain properties for this collection's 'node_id' and its sub
    collections. It relies on background data and is read every {BACKGROUND_TASK_TIME_INTERVAL}s.
    This is the granularity of the data.""",
)
async def read_stats_validation_collection(
    *,
    node_id: uuid.UUID = Depends(node_ids_for_major_collections),
):
    validate_node_id(node_id)
    return collections_with_missing_properties(node_id)


@router.get(
    "/material-validation/{node_id}",
    response_model=PendingMaterialsResponse,
    response_model_exclude_unset=True,
    status_code=HTTP_200_OK,
    responses={HTTP_404_NOT_FOUND: {"description": "Collection not found"}},
    tags=[_TAG_STATISTICS],
    description="""
    Returns the number of materials missing certain properties for this collection's 'node_id' and its sub collections.

    This endpoint is similar to '/analytics/node_id/validation/collections', but instead of showing missing
    properties in collections, it counts the materials inside each collection that are missing that property."""
    + f"It relies on background data and is read every {BACKGROUND_TASK_TIME_INTERVAL}s. "
    + "This is the granularity of the data.",
)
async def read_material_validationn(
    *,
    node_id: uuid.UUID = Depends(node_ids_for_major_collections),
):
    validate_node_id(node_id)
    return material_validation(
        collection_id=node_id, pending_materials=global_store.pending_materials
    )


if API_DEBUG:

    @router.get(
        "/global",
        description="""A debug endpoint to access the data stored inside the global storage.""",
    )
    async def get_global():
        return global_storage
