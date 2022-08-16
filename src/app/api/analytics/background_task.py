import asyncio
import os
import uuid
from datetime import datetime

from uuid import UUID
from elasticsearch_dsl.query import Query, Wildcard, Bool
from fastapi_utils.tasks import repeat_every

import app.api.analytics.storage
from app.api.analytics.analytics import PendingMaterialsResponse, PendingMaterials
from app.api.analytics.stats import (
    search_hits_by_material_type,
)
from app.api.analytics.storage import (
    _COLLECTION_COUNT,
    _COLLECTION_COUNT_OER,
    _COLLECTIONS,
    SearchStore,
    StorageModel,
    global_store,
)
from app.api.collections.counts import AggregationMappings, collection_counts
from app.api.collections.missing_materials import base_missing_material_search
from app.api.collections.tree import build_collection_tree
from app.core.config import BACKGROUND_TASK_TIME_INTERVAL
from app.core.constants import COLLECTION_NAME_TO_ID, COLLECTION_ROOT_ID
from app.core.logging import logger
from app.core.models import (
    ElasticResourceAttribute,
    essential_frontend_properties,
)
from app.elastic.elastic import ResourceType, query_missing_material_license
from app.elastic.search import Search


def import_data_from_elasticsearch(
    derived_at: datetime, resource_type: ResourceType, path: str
):
    search = search_query(resource_type=resource_type, path=path)

    seen = set()
    collections = []
    for hit in search.scan():
        node_id = hit.nodeRef["id"]
        if node_id not in seen:
            seen.add(node_id)
            collections.append(
                StorageModel(
                    id=str(node_id),
                    doc=hit.to_dict(),
                    derived_at=derived_at,
                )
            )
    return collections


def search_query(resource_type: ResourceType, path: str) -> Search:
    return (
        Search()
        .base_filters()
        .node_filter(resource_type=resource_type, node_id=COLLECTION_ROOT_ID)
        .source(includes=["nodeRef.*", path, *essential_frontend_properties])
    )


@repeat_every(seconds=BACKGROUND_TASK_TIME_INTERVAL, logger=logger)
def background_task():
    derived_at = datetime.now()
    logger.info(f"{os.getpid()}: Starting analytics import at: {derived_at}")

    app.api.analytics.storage.global_storage[
        _COLLECTIONS
    ] = import_data_from_elasticsearch(
        derived_at=derived_at,
        resource_type=ResourceType.COLLECTION,
        path=ElasticResourceAttribute.PATH.path,
    )

    logger.info("Collection imported")

    app.api.analytics.storage.global_storage[_COLLECTION_COUNT] = asyncio.run(
        collection_counts(COLLECTION_ROOT_ID, AggregationMappings.lrt)
    )
    app.api.analytics.storage.global_storage[_COLLECTION_COUNT_OER] = asyncio.run(
        collection_counts(COLLECTION_ROOT_ID, AggregationMappings.lrt, oer_only=True)
    )

    logger.info("Counts imported")

    logger.info(f"Tree ready to iterate. Length: {len(COLLECTION_NAME_TO_ID)}")

    # TODO Refactor, this is very expensive
    search_store = []
    oer_search_store = []
    for counter, (title, collection) in enumerate(COLLECTION_NAME_TO_ID.items()):
        collection = uuid.UUID(
            collection
        )  # fixme change types of COLLECTION_NAME_TO_ID map
        nodes = {
            node.node_id: node
            # flatten without including the root!
            for node in build_collection_tree(node_id=collection).flatten(root=False)
        }

        logger.info(
            f"Working on: {title}, #{counter} of {len(COLLECTION_NAME_TO_ID)}, # of subcollections: {len(nodes)}"
        )

        missing_materials = {
            node.node_id: search_hits_by_material_type(node.title)
            for node in nodes.values()
        }

        search_store.append(
            SearchStore(node_id=collection, missing_materials=missing_materials)
        )

        missing_materials = {
            node.node_id: search_hits_by_material_type(node.title, oer_only=True)
            for node in nodes.values()
        }

        oer_search_store.append(
            SearchStore(node_id=collection, missing_materials=missing_materials)
        )

        global_store.pending_materials[collection] = build_pending_materials_response(
            collection_id=collection,
            title=title
        )

    logger.info("Storing in global store.")
    logger.info(
        f"Global Store pending material keys: {list(global_store.pending_materials.keys())}"
    )
    global_store.search = search_store
    global_store.oer_search = oer_search_store

    logger.info("Background task done")


def build_pending_materials(collection_id: UUID, title: str) -> PendingMaterials:
    """
    Build the stats object holding material count statistics for a singular collection.

    Note that this does not consider materials that are in any (nested-)child collection of the collection, the
    material has to be _exactly_ in the specified collection.
    """
    logger.info(f" - Analyzing collection: {title} ({collection_id})")

    # the keys of below dict will be used as names in the elastic named queries.
    relevant_attributes = {
        "missing_title": ElasticResourceAttribute.TITLE,
        "missing_edu_context": ElasticResourceAttribute.EDU_CONTEXT,
        "missing_description": ElasticResourceAttribute.DESCRIPTION,
        "missing_license": ElasticResourceAttribute.LICENSES,
        "missing_learning_resource_type": ElasticResourceAttribute.LEARNINGRESOURCE_TYPE,
        "missing_taxon_id": ElasticResourceAttribute.SUBJECTS,
        "missing_publisher": ElasticResourceAttribute.PUBLISHER,
        "missing_intended_end_user_role": ElasticResourceAttribute.EDU_ENDUSERROLE_DE,
    }

    # to avoid looping through the results multiple times, we here initialize with empty lists
    materials = PendingMaterials(
        collection_id=collection_id,
        title=[],
        edu_context=[],
        url=[],
        description=[],
        license=[],
        learning_resource_type=[],
        taxon_id=[],
        publisher=[],
        intended_end_user_role=[],
    )
    # Don't do a transitive search: We only want the materials that are exactly in this collection
    # also the constructed search will return materials for which any of the attributes is missing.
    # This means, we need a way to figure out which of the relevant attributes were missing for each
    # hit. We do that with the help of [named queries](1).
    # By doing so, we avoid mixing elastic search validation of attributes with python code validation. I.e.
    # whether an attribute is missing is fully defined via the elastic search query. This is important, because
    # If we would do manual validation here we would essentially reimplement the elastic search query as python
    # if statement.
    #
    # 1: https://www.elastic.co/guide/en/elasticsearch/reference/7.17/query-dsl-bool-query.html#named-queries)

    search = base_missing_material_search(collection_id, transitive=False)

    def attribute_specific_query(
        attribute: ElasticResourceAttribute, alias: str
    ) -> Query:
        if attribute == ElasticResourceAttribute.LICENSES:
            return query_missing_material_license(name=alias).to_dict()
        return Bool(must_not=Wildcard(**{attribute.path: {"value": "*"}}), _name=alias)

    search = search.filter(
        Bool(
            minimum_should_match=1,
            should=[
                attribute_specific_query(attribute, alias=key)
                for key, attribute in relevant_attributes.items()
            ],
        )
    )
    search = search.source(includes=["nodeRef.id"])

    hits = search.execute().hits

    # now we loop over the results a single time and append to the respective list where appropriate
    for hit in hits:
        node_id = UUID(hit["nodeRef"]["id"])

        assert (
            len(hit.meta.matched_queries) > 0
        ), f"Found 'matched_queries' of length 0 which should never happen. nodeRef.id: {node_id}"

        for match in hit.meta.matched_queries:
            # we need to strip the "missing_" prefix from the matched query name :-/
            getattr(materials, match[len("missing_"):]).append(node_id)

    return materials


def build_pending_materials_response(
    collection_id: UUID, title: str
) -> PendingMaterialsResponse:
    """
    Build the response for the /material-validation endpoint.

    :param collection_id: The id of top level collection
    :param title: The title of the collection (only used for logging)
    """
    logger.info(f"Working on {title} ({collection_id})")
    children = build_collection_tree(node_id=collection_id).flatten(root=False)

    return PendingMaterialsResponse(
        collection_id=collection_id,
        missing_materials=[
            # fixme: we need to include the top level node here because we use a really inadequate data model...
            #        and it needs to be included, because there could be materials that are only in the top level
            #        collection and those materials would otherwise not be included anywhere.
            build_pending_materials(collection_id, title=title),
            *(
                build_pending_materials(node.node_id, title=node.title)
                for node in children
            ),
        ],
    )
