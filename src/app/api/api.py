import uuid

from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi.params import Param
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from starlette.status import (
    HTTP_200_OK,
    HTTP_404_NOT_FOUND,
)

from app.api.collections.collection_validation import collection_validation, CollectionValidation
from app.api.collections.counts import AggregationMappings, Counts, counts
from app.api.collections.material_counts import (
    MaterialCounts,
    material_counts,
)
from app.api.collections.material_validation import (
    material_validation,
    MaterialValidation,
    material_validation_cache,
)
from app.api.collections.pending_collections import (
    pending_collections,
    PendingCollection,
)
from app.api.collections.pending_materials import (
    PendingMaterial,
    MissingAttributeFilter,
    materials_filter_params,
    pending_materials,
)
from app.api.collections.quality_matrix import (
    QualityMatrixMode,
    quality_matrix,
    timestamps,
    QualityMatrix,
    past_quality_matrix,
)
from app.api.collections.score import Score, score
from app.api.collections.statistics import statistics, Statistics
from app.api.collections.tree import Tree
from app.api.collections.tree import tree
from app.core.constants import COLLECTION_NAME_TO_ID, COLLECTION_ROOT_ID
from app.db.tasks import get_session
from app.elastic.attributes import ElasticResourceAttribute

router = APIRouter()

valid_node_ids = {
    "Alle Fachportale": {"value": COLLECTION_ROOT_ID},
    **{key: {"value": value} for key, value in COLLECTION_NAME_TO_ID.items()},
}


def toplevel_collections(
    node_id: uuid.UUID = Path(default=..., examples=valid_node_ids),
) -> uuid.UUID:
    if str(node_id) not in {value["value"] for value in valid_node_ids.values()}:
        raise HTTPException(status_code=404, detail=f"Could not find collection with node id {node_id}")
    return node_id


@router.get(
    "/collections/{node_id}/quality-matrix/{mode}",
    status_code=HTTP_200_OK,
    response_model=QualityMatrix,
    responses={HTTP_404_NOT_FOUND: {"description": "Quality matrix not determinable"}},
    tags=["Collections"],
    summary="Calculate the replication-source or collection quality matrix",
)
async def get_quality_matrix(*, node_id: uuid.UUID = Depends(toplevel_collections), mode: QualityMatrixMode):
    """
    Calculate the quality matrix w.r.t. the replication source, or collection.

    A quality matrix is a tabular datastructure holding the number of materials that have a certain missing
    will represent a different replication source (the content source domain (e.g. "YouTube", "Wikipedia", ...) from
    which the content was crawled, for 'collection' each row will correspond to a specific collection (
    [vocabulary](https://vocabs.openeduhub.de/w3id.org/openeduhub/vocabs/oeh-topics/5e40e372-735c-4b17-bbf7-e827a5702b57.html).

    The columns of the matrix are defined by the meta data fields of the materials, and their counts denote how many
    of the materials of the given row contain the metadata of the respective column. Together with the total number
    of materials in each row, this allows to compute the completeness as `(row.counts[column])/row.total`
    (and incompleteness as `(row.total-row.counts[column])/row.total`).

    Parameters:
    - node_id: The toplevel collection for which to compute the quality matrix.
              It must come from the collection
              [vocabulary](https://vocabs.openeduhub.de/w3id.org/openeduhub/vocabs/oeh-topics/5e40e372-735c-4b17-bbf7-e827a5702b57.html).
              In the "collections" mode, this essentially defines the rows of the output matrix.
              It serves as an overall filter for materials in both cases.
    - mode: Defines the mode of the quality matrix, i.e. whether to compute the collection ("collections") or
          replication source ("replication-source").
    """

    root = tree(node_id)
    return quality_matrix(collection=root, mode=mode)


@router.get(
    "/collections/{node_id}/quality-matrix/{mode}/timestamps/{timestamp}",
    status_code=HTTP_200_OK,
    response_model=QualityMatrix,
    responses={HTTP_404_NOT_FOUND: {"description": "No quality matrix stored for given timestamp"}},
    tags=["Collections"],
    summary="Get a historic quality matrix for a given timestamp",
)
async def get_quality_matrix_by_timestamp(
    *,
    node_id: uuid.UUID = Depends(toplevel_collections),
    mode: QualityMatrixMode,
    timestamp: int,
    session: Session = Depends(get_session),
):
    """
    Return the quality matrix for the given timestamp.

    This endpoint serves as a comparison to the current quality matrix. This way, differences due to automatic or
    manual work on the metadata can be seen.
    """
    return past_quality_matrix(session=session, mode=mode, collection_id=node_id, timestamp=timestamp)


@router.get(
    "/collections/{node_id}/quality-matrix/{mode}/timestamps",
    status_code=HTTP_200_OK,
    response_model=list[int],
    responses={HTTP_404_NOT_FOUND: {"description": "Timestamps of old quality matrix results not determinable"}},
    tags=["Collections"],
    summary="Get the timestamps for which history quality matrices are available",
)
async def get_quality_matrix_timestamps(
    *,
    node_id: uuid.UUID = Depends(toplevel_collections),
    mode: QualityMatrixMode,
    session: Session = Depends(get_session),
):
    """
    Return timestamps in seconds since epoch of past calculations of the quality matrix.

    Parameters:
      - mode: The desired mode of quality. This is used to query only the relevant type of data.
      - node_id: The id of the collection for which the timestamps should be queried.
    """
    return timestamps(session=session, mode=mode, node_id=node_id)


@router.get(
    "/collections/{node_id}/score",
    response_model=Score,
    status_code=HTTP_200_OK,
    responses={HTTP_404_NOT_FOUND: {"description": "Collection not found"}},
    tags=["Collections"],
    summary="The average ratio of non-empty properties for the chosen collection",
)
async def get_score(*, node_id: uuid.UUID = Depends(toplevel_collections)):
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
    return await score(node_id)


@router.get(
    "/collections/{node_id}/tree",
    response_model=Tree,
    status_code=HTTP_200_OK,
    responses={HTTP_404_NOT_FOUND: {"description": "Collection not found"}},
    tags=["Collections"],
    summary="Provide the sub-tree of the collection hierarchy starting at given node",
)
async def get_tree(*, node_id: uuid.UUID = Depends(toplevel_collections)):
    """
    Returns the collection tree starting at the provided parent node (`node_id` path parameter).
    """
    return tree(node_id)


@router.get(
    "/collections/{node_id}/counts",
    summary="Provide the number of materials in the collection subtree grouped by the provided facet.",
    response_model=list[Counts],
    status_code=HTTP_200_OK,
    responses={HTTP_404_NOT_FOUND: {"description": "Collection not found"}},
    tags=["Collections"],
)
async def get_counts(
    *,
    node_id: uuid.UUID = Depends(toplevel_collections),
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
    return await counts(node_id=node_id, facet=facet)


@router.get(
    "/collections/{node_id}/pending-collections/{missing_attribute}",
    response_model=list[PendingCollection],
    status_code=HTTP_200_OK,
    responses={HTTP_404_NOT_FOUND: {"description": "Collection not found"}},
    tags=["Collections"],
)
async def get_pending_collections(
    *,
    node_id: uuid.UUID = Depends(toplevel_collections),
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
      - keywords (cclom:general_keyword)
      - description (cclom:general_description)
    <b>
    TODO:
      - why do we use cclom:general_description? Isn't this an attribute of a material?
      - why do we use cclom:general_keyword? I think this is an attribute of a material.
      - while cclom:general_keyword seems not to be a collection attribute, cclom:general_description is one?
    </b>
    """
    if missing_attribute == ElasticResourceAttribute.KEYWORDS.path:
        missing_attribute = ElasticResourceAttribute.KEYWORDS
    elif missing_attribute == ElasticResourceAttribute.COLLECTION_DESCRIPTION.path:
        missing_attribute = ElasticResourceAttribute.COLLECTION_DESCRIPTION
    else:
        raise HTTPException(status_code=400, detail=f"Invalid collection attribute: {missing_attribute}")
    return await pending_collections(node_id, missing=missing_attribute)


@router.get(
    "/collections/{node_id}/pending-materials/{missing_attr}",
    response_model=list[PendingMaterial],
    status_code=HTTP_200_OK,
    responses={HTTP_404_NOT_FOUND: {"description": "Collection not found"}},
    tags=["Collections"],
)
async def get_pending_materials(
    *,
    node_id: uuid.UUID = Depends(toplevel_collections),
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
    return await pending_materials(
        collection_id=node_id,
        # fixme: resolve the whole attribute identification mess
        missing=getattr(ElasticResourceAttribute, str(missing_attr_filter.attr.name)),
    )


@router.get(
    "/collections/{node_id}/material-counts",
    response_model=list[MaterialCounts],
    status_code=HTTP_200_OK,
    responses={HTTP_404_NOT_FOUND: {"description": "Collection not found"}},
    tags=["Collections"],
    summary="Provide the total number of materials per collection",
)
async def get_material_counts(*, node_id: uuid.UUID = Depends(toplevel_collections)):
    """
    Returns the number of materials connected to all collections below this 'node_id' as a flat list.
    """
    collection = tree(node_id=node_id)
    return await material_counts(collection=collection)


@router.get(
    "/collections/{node_id}/statistics",
    response_model=Statistics,
    status_code=HTTP_200_OK,
    responses={HTTP_404_NOT_FOUND: {"description": "Collection not found"}},
    tags=["Collections"],
)
async def get_statistics(
    *,
    node_id: uuid.UUID = Depends(toplevel_collections),
):
    """
    Returns the number of materials found connected to the collection (`node_id` path parameter) and its
    sub-collections as well as materials containing the name of the respective collection, e.g., in the title.
    It is therefore an overview of materials, which could be added to a collection in the future.
    """
    return await statistics(node_id)


@router.get(
    "/collections/{node_id}/collection-validation",
    response_model=list[CollectionValidation],
    status_code=HTTP_200_OK,
    responses={HTTP_404_NOT_FOUND: {"description": "Collection not found"}},
    tags=["Collections"],
)
async def get_collection_validation(
    *,
    node_id: uuid.UUID = Depends(toplevel_collections),
):
    """
    Returns a list of child collections of the given parent collection where
    `title`, `description`, `keywords`, or `edu_context` are missing.
    """
    return collection_validation(node_id)


@router.get(
    "/collections/{node_id}/material-validation",
    response_model=list[MaterialValidation],
    status_code=HTTP_200_OK,
    responses={HTTP_404_NOT_FOUND: {"description": "Collection not found"}},
    tags=["Collections"],
)
async def get_material_validation(
    *,
    node_id: uuid.UUID = Depends(toplevel_collections),
):
    """
    Returns the ids of materials missing certain properties for this collection's 'node_id' and its
    sub-collections.

    This endpoint is similar to '/collections/{node_id}/collection-validation', but instead of listing missing
    properties in the child collections, it selects the materials inside each collection by the
    w.r.t. the materials missing properties.

    This endpoint relies on an internal periodic background process which is scheduled to regularly update the data.
    Its frequency can be configured via the BACKGROUND_TASK_TIME_INTERVAL environment variable.
    """
    try:
        if False:  # Fixme: if possible optimize the query and return real time data
            return material_validation(collection_id=node_id)  # noqa
        return material_validation_cache[node_id]
    except KeyError:
        raise HTTPException(
            status_code=503,
            detail=f"Background calculation for collection {node_id} incomplete. Please try again in a while.",
        )


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
