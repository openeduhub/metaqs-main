import json
import uuid
from typing import Mapping, Optional

from databases import Database
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi.params import Param
from pydantic import BaseModel, Field
from sqlalchemy import select
from starlette.requests import Request
from starlette.responses import Response
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from app.api.analytics.analytics import (
    CollectionValidationStats,
    MaterialFieldValidation,
    MaterialValidationStats,
    OehValidationError,
    StatsResponse,
    StatType,
    ValidationStatsResponse,
)
from app.api.analytics.background_task import background_router
from app.api.analytics.stats import overall_stats, stats_latest
from app.api.analytics.storage import global_storage
from app.api.collections.counts import (
    AggregationMappings,
    CollectionTreeCount,
    collection_counts,
)
from app.api.collections.descendants import (
    CollectionMaterialsCount,
    get_many_descendants,
    material_counts_by_descendant,
)
from app.api.collections.missing_attributes import (
    collections_with_missing_attributes,
    missing_attribute_filter,
)
from app.api.collections.missing_materials import (
    LearningMaterial,
    MissingAttributeFilter,
    filter_response_fields,
    get_child_materials_with_missing_attributes,
    material_response_fields,
    materials_filter_params,
)
from app.api.collections.models import CollectionNode, MissingMaterials
from app.api.collections.tree import collection_tree
from app.api.quality_matrix.collections import collection_quality
from app.api.quality_matrix.models import ColumnOutputModel, Forms, Timeline
from app.api.quality_matrix.quality_matrix import source_quality, store_in_timeline
from app.api.quality_matrix.timeline import timestamps
from app.api.quality_matrix.utils import transpose
from app.api.score.models import LearningMaterialAttribute, ScoreOutput
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
from app.models import CollectionAttribute


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

TAG_STATISTICS = "Statistics"
_TAG_COLLECTIONS = "Collections"


def node_ids_for_major_collections(
    *,
    node_id: uuid.UUID = Path(
        ...,
        examples={
            "Alle Fachportale": {"value": COLLECTION_ROOT_ID},
            **COLLECTION_NAME_TO_ID,
        },
    ),
) -> uuid.UUID:
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
    *,
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
    tags=[TAG_STATISTICS],
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
    "/collections/{collection_id}/stats/score",
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
async def score(*, collection_id: uuid.UUID = Depends(collection_id_param)):
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
    tags=[_TAG_COLLECTIONS],
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
async def filter_collections_with_missing_attributes(
    *,
    node_id: uuid.UUID = Depends(node_ids_for_major_collections),
    missing_attribute: str = Path(
        ...,
        examples={
            form.name: {"value": form.value} for form in missing_attribute_filter
        },
    ),
):
    return await collections_with_missing_attributes(node_id, missing_attribute)


@router.get(
    "/collections/{node_id}/pending-materials/{missing_attr}",
    response_model=list[LearningMaterial],
    response_model_exclude_unset=True,
    status_code=HTTP_200_OK,
    responses={HTTP_404_NOT_FOUND: {"description": "Collection not found"}},
    tags=["Materials"],
)
async def filter_materials_with_missing_attributes(
    *,
    node_id: uuid.UUID = Depends(node_ids_for_major_collections),
    missing_attr_filter: MissingAttributeFilter = Depends(materials_filter_params),
    response_fields: Optional[set[LearningMaterialAttribute]] = Depends(
        material_response_fields
    ),
):
    if response_fields:
        response_fields.add(LearningMaterialAttribute.NODEREF_ID)

    materials = await get_child_materials_with_missing_attributes(
        noderef_id=node_id,
        missing_attr_filter=missing_attr_filter,
        source_fields=response_fields,
    )

    return filter_response_fields(materials, response_fields=response_fields)


@router.get(
    "/collections/{node_id}/stats/descendant-collections-materials-counts",
    response_model=list[CollectionMaterialsCount],
    status_code=HTTP_200_OK,
    responses={HTTP_404_NOT_FOUND: {"description": "Collection not found"}},
    tags=["Statistics"],
)
async def material_counts_tree(
    *,
    node_id: uuid.UUID = Depends(node_ids_for_major_collections),
    response: Response,
):
    descendant_collections = await get_many_descendants(
        ancestor_id=node_id,
        source_fields={
            CollectionAttribute.NODE_ID,
            CollectionAttribute.PATH,
            CollectionAttribute.TITLE,
        },
    )
    materials_counts = await material_counts_by_descendant(
        ancestor_id=node_id,
    )

    descendant_collections = {
        collection.noderef_id: collection.title for collection in descendant_collections
    }
    stats = []
    errors = []
    for record in materials_counts.results:
        try:
            title = descendant_collections.pop(record.noderef_id)
        except KeyError:
            errors.append(record.noderef_id)
            continue

        stats.append(
            CollectionMaterialsCount(
                noderef_id=record.noderef_id,
                title=title,
                materials_count=record.materials_count,
            )
        )

    stats = [
        *[
            CollectionMaterialsCount(
                noderef_id=noderef_id,
                title=title,
                materials_count=0,
            )
            for (noderef_id, title) in descendant_collections.items()
        ],
        *stats,
    ]

    return stats


@router.get(
    "/analytics/{node_id}",
    response_model=StatsResponse,
    status_code=HTTP_200_OK,
    responses={HTTP_404_NOT_FOUND: {"description": "Collection not found"}},
    tags=["Analytics"],
)
async def read_stats(*, node_id: uuid.UUID = Depends(node_ids_for_major_collections)):
    return await overall_stats(node_id)


@router.get(
    "/analytics/{node_id}/validation/collections",
    response_model=list[ValidationStatsResponse[CollectionValidationStats]],
    response_model_exclude_unset=True,
    status_code=HTTP_200_OK,
    responses={HTTP_404_NOT_FOUND: {"description": "Collection not found"}},
    tags=["Analytics"],
)
async def read_stats_validation_collection(
    *,
    node_id: uuid.UUID = Depends(node_ids_for_major_collections),
):
    stats = await stats_latest(
        stat_type=StatType.VALIDATION_COLLECTIONS, node_id=node_id
    )

    if not stats:
        pass
        # raise StatsNotFoundException

    response = [
        ValidationStatsResponse[CollectionValidationStats](
            noderef_id=stat["collection_id"],
            validation_stats=CollectionValidationStats(
                **{
                    k.lower(): [OehValidationError.MISSING]
                    for k in stat["missing_fields"]
                }
            ),
        )
        for stat in stats
    ]

    return response


@router.get(
    "/{node_id}/validation",
    response_model=list[ValidationStatsResponse[MaterialValidationStats]],
    response_model_exclude_unset=True,
    status_code=HTTP_200_OK,
    responses={HTTP_404_NOT_FOUND: {"description": "Collection not found"}},
    tags=["Analytics"],
)
async def read_stats_validation(
    *,
    node_id: uuid.UUID = Depends(node_ids_for_major_collections),
):
    # TODO: See if this can be removed, partially needed in unused components in the frontend
    stats = await stats_latest(stat_type=StatType.VALIDATION_MATERIALS, node_id=node_id)

    if not stats:
        pass
        # raise StatsNotFoundException

    response = [
        ValidationStatsResponse[MaterialValidationStats](
            noderef_id=stat["collection_id"],
            validation_stats=MaterialValidationStats(
                **{
                    field.lower(): MaterialFieldValidation(missing=material_ids)
                    for field, material_ids in stat["missing_fields"].items()
                },
            ),
        )
        for stat in stats
    ]

    return response


@router.get(
    "/global",
)
async def get_global():
    return global_storage
