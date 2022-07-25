import json
import uuid
from typing import Mapping, Optional

from databases import Database
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi.params import Param
from pydantic import BaseModel, Field
from sqlalchemy import select
from starlette.requests import Request
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from app.api.analytics.analytics import (
    CollectionValidationStats,
    MaterialValidationStats,
    StatsResponse,
    ValidationStatsResponse,
)
from app.api.analytics.background_task import background_router
from app.api.analytics.stats import (
    collections_with_missing_properties,
    materials_with_missing_properties,
    overall_stats,
)
from app.api.analytics.storage import global_storage
from app.api.collections.counts import (
    AggregationMappings,
    CollectionTreeCount,
    collection_counts,
)
from app.api.collections.descendants import (
    CollectionMaterialsCount,
    get_material_count_tree,
)
from app.api.collections.missing_materials import (
    LearningMaterial,
    MissingAttributeFilter,
    get_materials_with_missing_attributes,
    material_response_fields,
    materials_filter_params,
)
from app.api.collections.models import CollectionNode, MissingMaterials
from app.api.collections.pending_collections import (
    missing_attribute_filter,
    pending_collections,
)
from app.api.collections.tree import collection_tree
from app.api.quality_matrix.collections import collection_quality
from app.api.quality_matrix.models import Forms, QualityOutputModel, Timeline
from app.api.quality_matrix.quality_matrix import source_quality, store_in_timeline
from app.api.quality_matrix.timeline import timestamps
from app.api.quality_matrix.utils import transpose
from app.api.score.models import ScoreOutput
from app.api.score.score import (
    aggs_collection_validation,
    aggs_material_validation,
    field_names_used_for_score_calculation,
    get_score,
    node_id_param,
)
from app.core.config import API_DEBUG, BACKGROUND_TASK_TIME_INTERVAL
from app.core.constants import COLLECTION_NAME_TO_ID, COLLECTION_ROOT_ID
from app.core.models import ElasticResourceAttribute
from app.core.utils import create_examples


def get_database(request: Request) -> Database:
    return request.app.state._db


router = APIRouter()
router.include_router(background_router)

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

_TAG_STATISTICS = "Statistics"
_TAG_COLLECTIONS = "Collections"


def node_ids_for_major_collections(
    *,
    node_id: uuid.UUID = Path(
        ...,
        examples={
            "Alle Fachportale": {"value": COLLECTION_ROOT_ID},
            **create_examples(COLLECTION_NAME_TO_ID),
        },
    ),
) -> uuid.UUID:
    return node_id


@router.get(
    "/quality",
    status_code=HTTP_200_OK,
    response_model=list[QualityOutputModel],
    responses={HTTP_404_NOT_FOUND: {"description": "Quality matrix not determinable"}},
    tags=[_TAG_STATISTICS],
    description=QUALITY_MATRIX_DESCRIPTION,
)
async def get_quality(
    *,
    database: Database = Depends(get_database),
    node_id: str = Query(
        default=COLLECTION_ROOT_ID,
        examples={
            "Alle Fachportale": {"value": COLLECTION_ROOT_ID},
            **create_examples(COLLECTION_NAME_TO_ID),
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
    response_model=list[QualityOutputModel],
    responses={HTTP_404_NOT_FOUND: {"description": "Quality matrix not determinable"}},
    tags=[_TAG_STATISTICS],
    description="""An unix timestamp in integer seconds since epoch yields the
    quality matrix at the respective date.""",
)
async def get_past_quality_matrix(
    *, timestamp: int, database: Database = Depends(get_database)
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
    tags=[_TAG_STATISTICS],
    description="""Return timestamps in seconds since epoch of past calculations of the quality matrix.
    Additional parameters:
        form: The desired form of quality. This is used to query only the relevant type of data.""",
)
async def get_timestamps(
    *,
    database: Database = Depends(get_database),
    form: Forms = Query(
        default=Forms.REPLICATION_SOURCE,
        examples={form: {"value": form} for form in Forms},
    ),
):
    return await timestamps(database, form)


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
async def score(*, node_id: uuid.UUID = Depends(node_id_param)):
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
    counts = await collection_counts(node_id=node_id, facet=facet)
    return counts


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
    return await pending_collections(node_id, missing_attribute)


@router.get(
    "/collections/{node_id}/pending-materials/{missing_attr}",
    response_model=list[LearningMaterial],
    response_model_exclude_unset=True,
    status_code=HTTP_200_OK,
    responses={HTTP_404_NOT_FOUND: {"description": "Collection not found"}},
    tags=[_TAG_COLLECTIONS],
    description="""A list of missing entries for different types of materials by subcollection.
    Searches for materials with one of the following properties being empty or missing: """
    + f"{', '.join([entry.value for entry in missing_attribute_filter])}.",
)
async def filter_materials_with_missing_attributes(
    *,
    node_id: uuid.UUID = Depends(node_ids_for_major_collections),
    missing_attr_filter: MissingAttributeFilter = Depends(materials_filter_params),
    response_fields: Optional[set[ElasticResourceAttribute]] = Depends(
        material_response_fields
    ),
):
    return await get_materials_with_missing_attributes(
        missing_attr_filter, node_id, response_fields
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
    oer_only: bool = Query(default=False),
):
    return await overall_stats(node_id, oer_only)


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
    return collections_with_missing_properties(node_id)


@router.get(
    "/analytics/{node_id}/validation",
    response_model=list[ValidationStatsResponse[MaterialValidationStats]],
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
async def read_stats_validation(
    *,
    node_id: uuid.UUID = Depends(node_ids_for_major_collections),
):
    return materials_with_missing_properties(node_id)


if API_DEBUG:

    @router.get(
        "/global",
        description="""A debug endpoint to access the data stored inside the global storage.""",
    )
    async def get_global():
        return global_storage
