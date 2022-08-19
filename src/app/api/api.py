import json
import uuid
from typing import Mapping, Optional

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
    overall_stats,
)
from app.api.analytics.storage import global_storage, global_store
from app.api.collections.counts import (
    AggregationMappings,
    CollectionTreeCount,
    oer_collection_counts,
)
from app.api.collections.material_counts import (
    CollectionMaterialCount,
    get_collection_material_counts,
)
from app.api.collections.pending_materials import (
    LearningMaterial,
    MissingAttributeFilter,
    materials_filter_params,
    search_materials_with_missing_attributes,
)
from app.api.collections.models import CollectionNode
from app.api.collections.pending_collections import (
    search_collections_with_missing_attributes,
    MissingMaterials,
)
from app.api.collections.tree import build_collection_tree
from app.api.quality_matrix.collections import collection_quality_matrix
from app.api.quality_matrix.models import Mode, QualityMatrix, Timeline
from app.api.quality_matrix.replication_source import source_quality_matrix
from app.api.quality_matrix.timeline import quality_backup, timestamps
from app.api.score.models import ScoreOutput
from app.api.score.score import get_score
from app.core.config import API_DEBUG
from app.core.constants import COLLECTION_NAME_TO_ID, COLLECTION_ROOT_ID
from app.core.models import ElasticResourceAttribute


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
        raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="Node id invalid")


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
    response_model=QualityMatrix,
    responses={HTTP_404_NOT_FOUND: {"description": "Quality matrix not determinable"}},
    tags=[_TAG_STATISTICS],
    summary="Calculate the replication source or collection quality matrix",
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
      [vocabulary](https://vocabs.openeduhub.de/w3id.org/openeduhub/vocabs/oeh-topics/5e40e372-735c-4b17-bbf7-e827a5702b57.html).
    - For the replication source quality matrix, the columns correspond to the content source domain (e.g. "YouTube",
      "Wikipedia", ...) from which the content was crawled, the rows correspond to the metadata fields.

    For both cases, the individual cells hold the rations of materials where the metadata is "OK". The definition of
    "OK" depends on the meta data field (e.g. "non-empty string" for the title of a material).

    Parameters:
    - node_id: The toplevel collection for which to compute the quality matrix.
                It must come from the collection
                [vocabulary](https://vocabs.openeduhub.de/w3id.org/openeduhub/vocabs/oeh-topics/5e40e372-735c-4b17-bbf7-e827a5702b57.html).
                In the "collections" mode, this essentially defines the rows of the output matrix.
                It serves as an overall filter for materials in both cases.
    - mode: Defines the mode of the quality matrix, i.e. whether to compute the collection ("collections") or
            replication source ("replication_source"). Defaults to "replication_source".
    """
    validate_node_id(uuid.UUID(node_id))
    if mode is Mode.REPLICATION_SOURCE:
        return await source_quality_matrix(uuid.UUID(node_id))
    elif mode is Mode.COLLECTIONS:
        return await collection_quality_matrix(uuid.UUID(node_id))
    else:
        raise HTTPException(status_code=400, detail=f"Invalid mode: {mode}")


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
    response_model=QualityMatrix,
    responses={HTTP_404_NOT_FOUND: {"description": "Quality matrix not determinable"}},
    tags=[_TAG_STATISTICS],
    summary="Get a historic quality matrix for a given timestamp",
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
    return QualityMatrix(data=quality, total=total)


@router.get(
    "/quality_timestamps",
    status_code=HTTP_200_OK,
    response_model=list[int],
    responses={HTTP_404_NOT_FOUND: {"description": "Timestamps of old quality matrix results not determinable"}},
    tags=[_TAG_STATISTICS],
    summary="Get the timestamps for which history quality matrices are available",
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
    """
    Return timestamps in seconds since epoch of past calculations of the quality matrix.

    Parameters:
      - mode: The desired mode of quality. This is used to query only the relevant type of data.
      - node_id: The id of the collection for which the timestamps should be queried.
    """
    validate_node_id(uuid.UUID(node_id))
    return await timestamps(database, mode, uuid.UUID(node_id))


@router.get(
    "/collections/{node_id}/score",
    response_model=ScoreOutput,
    status_code=HTTP_200_OK,
    responses={HTTP_404_NOT_FOUND: {"description": "Collection not found"}},
    tags=[_TAG_COLLECTIONS],
    summary="The average ratio of non-empty properties for the chosen collection",
)
async def score(*, node_id: uuid.UUID = Depends(node_ids_for_major_collections)):
    """
    Validate attributes of sub-collections and materials of the given collection grouped by OER and non-OER content.

    **fixme: document what "missing attribute" means here. E.g.: Is an empty title a missing attribute - or is it really
             missing in Elasticsearch?**

    Both, collections and materials, are checked for the following missing attributes:
     - title (cclom:title for materials, cm:title for collections)
     - description (cclom:general_description for materials, cm:description for collections)
     - educational context (ccm:educationalcontext for both, probably provided via "ccm:educontext" aspect)

    For materials the following additional attributes are checked:
    - learning resource type (ccm:oeh_lrt)
    - subjects (ccm:taxonid)
    - URL (ccm:wwwurl)
    - license (ccm:commonlicense_key, fixme: document extra logic!)
    - publisher (ccm:oeh_publisher_combined)
    - intended enduser role (i18n.de_DE.ccm:educationalintendedenduserrole)

    **fixme: Why do we use i18n.de_DE.ccm:educationalintendedenduserrole here? There is also
             properties.ccm:educationalintendedenduserrole that seems much more reasonable to use.**

    For collections, besides checking that an attribute is present, title, keywords, and description are also validated
    w.r.t their length:
    - missing keywords (no keywords)
    - few keywords (less than 3 keywords)
    - short title (less than 5 characters)
    - short description (less than 30 characters)

    For materials, the above analysis is grouped w.r.t. whether the material is an OER or not. A material is considered
    OER via its license (ccm:commonlicense_key, currently "CC_0", "PDM", "CC_BY", and "CC_BY_SA" are considered OER).

    The overall score is a combination of material and collection ratios.

    **fixme: Improve documentation of overall score, or eventually completely refactor it (separate collection and
             materials)**
    """
    validate_node_id(node_id)
    return await get_score(node_id)


class Ping(BaseModel):
    status: str = Field(
        default="not ok",
        description="Ping output. Should be 'ok' in happy case.",
    )


@router.get(
    "/_ping",
    response_model=Ping,
    tags=["Healthcheck"],
)
async def ping_api():
    """
    Ping function for automatic health check.
    """
    return {"status": "ok"}


@router.get(
    "/collections/{node_id}/tree",
    response_model=list[CollectionNode],
    status_code=HTTP_200_OK,
    responses={HTTP_404_NOT_FOUND: {"description": "Collection not found"}},
    tags=[_TAG_COLLECTIONS],
    summary="Provide the sub-tree of the collection hierarchy starting at given node",
)
async def get_collection_tree(*, node_id: uuid.UUID = Depends(node_ids_for_major_collections)):
    """
    Returns a list of the immediate child nodes of the provided parent node (`node_id` path parameter).

    The individual entries of the list hold their respective child collections until the leafs of the collection tree
    are reached.

    **FIXME: See [Issue-86](https://github.com/openeduhub/metaqs-main/issues/86)**
    """
    validate_node_id(node_id)
    return build_collection_tree(node_id).children


@router.get(
    "/collections/{node_id}/counts",
    summary="Provide the number of materials in the collection subtree grouped by the provided facet.",
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
    """
    Returns a list where each entry corresponds to a sub-collection of the provided collection id (`node_id` path
    parameter).

    **⚠️Elements of the list are not necessarily direct children of the requested node - i.e. the list is a flattened
    version of the subtree of the requested node with unspecified order.
    See also [Issue-88](https://github.com/openeduhub/metaqs-main/issues/88)⚠️**

    Within the elements of the list, the number of materials is grouped by OER vs Non-OER and the selected facet.
    """
    validate_node_id(node_id)
    return await oer_collection_counts(node_id=node_id, facet=facet)


@router.get(
    "/collections/{node_id}/pending-subcollections/{missing_attribute}",
    response_model=list[MissingMaterials],
    response_model_exclude_unset=True,
    status_code=HTTP_200_OK,
    responses={HTTP_404_NOT_FOUND: {"description": "Collection not found"}},
    tags=[_TAG_COLLECTIONS],
)
async def filter_pending_collections(
    *,
    node_id: uuid.UUID = Depends(node_ids_for_major_collections),
    missing_attribute: str = Path(
        ...,
        examples={
            form.name: {"value": form.value}
            for form in [
                ElasticResourceAttribute.KEYWORDS,
                ElasticResourceAttribute.COLLECTION_DESCRIPTION,
            ]
        },
    ),
):
    """
    Provides a list of missing entries for different types of materials by sub-collection.

    Searches for entries with one of the following properties being empty or missing:

      - title (cm:title)
      - name (cm:name)
      - keywords (cclom:general_keyword)
      - description (cclom:general_description)
      - license (ccm:commonlicense_key)

    <b>
    TODO:
      - how can a collection have a license? why is it part of the missing_attribute_filter?
      - why do we use cclom:general_description? Isn't this an attribute of a material?
      - why do we use cm:name? According to T.S. cm:name does not have any user relevance.
      - why do we use cclom:general_keyword? I think this is an attribute of a material.
      - while cclom:general_keyword seems not to be a collection attribute, cclom:general_description is one?
    </b>
    """
    validate_node_id(node_id)

    if missing_attribute == ElasticResourceAttribute.KEYWORDS.path:
        missing_attribute = ElasticResourceAttribute.KEYWORDS
    elif missing_attribute == ElasticResourceAttribute.COLLECTION_DESCRIPTION.path:
        missing_attribute = ElasticResourceAttribute.COLLECTION_DESCRIPTION
    else:
        raise HTTPException(status_code=400, detail=f"Invalid collection attribute: {missing_attribute}")
    return await search_collections_with_missing_attributes(node_id, missing=missing_attribute)


@router.get(
    "/collections/{node_id}/pending-materials/{missing_attr}",
    response_model=list[LearningMaterial],
    response_model_exclude_unset=True,
    status_code=HTTP_200_OK,
    responses={HTTP_404_NOT_FOUND: {"description": "Collection not found"}},
    tags=[_TAG_COLLECTIONS],
)
async def filter_materials_with_missing_attributes(
    *,
    node_id: uuid.UUID = Depends(node_ids_for_major_collections),
    missing_attr_filter: MissingAttributeFilter = Depends(materials_filter_params),
):
    """
    A list of missing entries for different types of materials belonging to the collection and its sub-collections
    specified by 'node_id'.

    Searches for materials with one of the following properties being empty or missing:
    - title (properties.cclom:title)
    - learning resource type or category (properties.ccm:oeh_lrt)
    - subjects (properties.ccm:taxonid)
    - URL (properties.ccm:wwwurl)
    - license (properties.ccm:commonlicense_key)
    - publisher (properties.ccm:oeh_publisher_combined)
    - description (properties.cclom:general_description)
    - educational end user role (i18n.de_DE.ccm:educationalintendedenduserrole)
    - educational context (properties.ccm:educationalcontext)
    - cover (preview)
    - node id (nodeRef.id)
    - name (properties.cm:name)
    - type (type)
    - keywords (properties.cclom:general_keyword)

    <b>
    TODO:
      - align implementation of pending-materials and pending-collection endpoints
        - path parameter name
        - path parameter handling (pending-materials works via an enum hence allows only the possible choices.
          however, it leaks the elasticsearch internals)
      - Use properties.ccm:educationalintendedenduserrole instead of i18n.de_DE.ccm:educationalintendedenduserrole?
      - remove nodeRef.id search functionality? Can this even be missing/empty? How would that be relevant for the user?
      - remove name (cm:name) search functionality? According to T.S. this is purely technical and is unrelated to
        content or metadata quality.
      - remove type search functionality! We search for materials, i.e. all found documents will have type=ccm:io...
      -
    </b>
    """
    validate_node_id(node_id)
    return await search_materials_with_missing_attributes(
        collection_id=node_id,
        # fixme: resolve the whole attribute identification mess
        missing=getattr(ElasticResourceAttribute, str(missing_attr_filter.attr.name)),
    )


@router.get(
    "/collections/{node_id}/material_counts",
    response_model=list[CollectionMaterialCount],
    status_code=HTTP_200_OK,
    responses={HTTP_404_NOT_FOUND: {"description": "Collection not found"}},
    tags=[_TAG_COLLECTIONS],
    summary="Provide the total number of materials per collection",
)
async def collection_material_counts(*, node_id: uuid.UUID = Depends(node_ids_for_major_collections)):
    """
    Returns the number of materials connected to all collections below this 'node_id' as a flat list.
    """
    validate_node_id(node_id)
    collection = build_collection_tree(node_id=node_id)
    return await get_collection_material_counts(collection=collection)


@router.get(
    "/analytics/{node_id}",
    response_model=StatsResponse,
    status_code=HTTP_200_OK,
    responses={HTTP_404_NOT_FOUND: {"description": "Collection not found"}},
    tags=[_TAG_STATISTICS],
)
async def read_stats(
    *,
    node_id: uuid.UUID = Depends(node_ids_for_major_collections),
):
    """
    Returns the number of materials found connected to the collection (`node_id` path parameter) and its
    sub-collections as well as materials containing the name of the respective collection, e.g., in the title.
    It is therefore an overview of materials, which could be added to a collection in the future.

    This endpoint relies on an internal periodic background process which is scheduled to regularly update the data.
    Its frequency can be configured via the BACKGROUND_TASK_TIME_INTERVAL environment variable.
    """
    validate_node_id(node_id)
    return await overall_stats(node_id)


@router.get(
    "/analytics/{node_id}/validation/collections",
    response_model=list[ValidationStatsResponse[CollectionValidationStats]],
    response_model_exclude_unset=True,
    status_code=HTTP_200_OK,
    responses={HTTP_404_NOT_FOUND: {"description": "Collection not found"}},
    tags=[_TAG_STATISTICS],
)
async def read_stats_validation_collection(
    *,
    node_id: uuid.UUID = Depends(node_ids_for_major_collections),
):
    """
    Returns the number of collections missing certain properties for this collection's 'node_id' and its
    sub-collections.

    This endpoint relies on an internal periodic background process which is scheduled to regularly update the data.
    Its frequency can be configured via the BACKGROUND_TASK_TIME_INTERVAL environment variable.
    """
    validate_node_id(node_id)
    return collections_with_missing_properties(node_id)


@router.get(
    "/material-validation/{node_id}",
    response_model=PendingMaterialsResponse,
    response_model_exclude_unset=True,
    status_code=HTTP_200_OK,
    responses={HTTP_404_NOT_FOUND: {"description": "Collection not found"}},
    tags=[_TAG_STATISTICS],
)
async def read_material_validationn(
    *,
    node_id: uuid.UUID = Depends(node_ids_for_major_collections),
):
    """
    Returns the number of materials missing certain properties for this collection's 'node_id' and its
    sub-collections.

    This endpoint is similar to '/analytics/node_id/validation/collections', but instead of showing missing
    properties in collections, it counts the materials inside each collection that are missing that property.

    This endpoint relies on an internal periodic background process which is scheduled to regularly update the data.
    Its frequency can be configured via the BACKGROUND_TASK_TIME_INTERVAL environment variable.
    """
    validate_node_id(node_id)
    try:
        return global_store.pending_materials[node_id]
    except KeyError:
        raise HTTPException(
            status_code=503,
            detail=f"Background calculation for collection {node_id} incomplete. Please try again in a while.",
        )


if API_DEBUG:

    @router.get(
        "/global",
        description="""A debug endpoint to access the data stored inside the global storage.""",
    )
    async def get_global():
        return global_storage
