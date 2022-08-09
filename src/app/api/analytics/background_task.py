import asyncio
import os
import uuid
from datetime import datetime
from typing import Union

from elasticsearch_dsl import Q
from elasticsearch_dsl.query import Query, Wildcard
from fastapi import APIRouter
from fastapi_utils.tasks import repeat_every
from starlette.background import BackgroundTasks
from starlette.status import HTTP_202_ACCEPTED

import app.api.analytics.storage
from app.api.analytics.stats import (
    Row,
    get_ids_to_iterate,
    search_hits_by_material_type,
)
from app.api.analytics.storage import (
    _COLLECTION_COUNT,
    _COLLECTION_COUNT_OER,
    _COLLECTIONS,
    PendingMaterials,
    PendingMaterialsStore,
    SearchStore,
    StorageModel,
    global_store,
)
from app.api.collections.counts import AggregationMappings, collection_counts
from app.api.collections.missing_materials import (
    base_missing_material_search,
    missing_attributes_search,
)
from app.core.config import BACKGROUND_TASK_TIME_INTERVAL
from app.core.constants import COLLECTION_NAME_TO_ID, COLLECTION_ROOT_ID
from app.core.logging import logger
from app.core.models import (
    ElasticResourceAttribute,
    essential_frontend_properties,
    required_collection_properties,
)
from app.elastic.elastic import ResourceType, query_missing_material_license
from app.elastic.search import Search

background_router = APIRouter(tags=["Background"])


@background_router.post("/run-analytics", status_code=HTTP_202_ACCEPTED)
async def run_analytics(*, background_tasks: BackgroundTasks):
    background_tasks.add_task(run)


@repeat_every(seconds=BACKGROUND_TASK_TIME_INTERVAL, logger=logger)
def background_task():
    run()


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


def filter_by_id(hit, node_id):
    for collection in hit.collections:
        if node_id in collection["path"] or node_id == collection["nodeRef"]["id"]:
            return True
    return False


def uuids_of_materials_with_missing_attributes(
    node_id: uuid.UUID, attribute: str
) -> list[uuid.UUID]:
    """
    Returns a list of UUIDS for the materials that lack the given attribute and are part of the given collection
    (node_id).
    """

    return [
        uuid.UUID(hit.to_dict()["nodeRef"]["id"])
        for hit in missing_attributes_search(node_id, attribute).execute().hits
    ]


def run():
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

    all_collections = [
        Row(id=uuid.UUID(value), title=key)
        for key, value in COLLECTION_NAME_TO_ID.items()
    ]
    logger.info(f"Tree ready to iterate. Length: {len(all_collections)}")

    # TODO Refactor, this is very expensive
    search_store = []
    oer_search_store = []
    pending_materials_store = []
    for counter, collection in enumerate(all_collections):
        sub_collections: list[Row] = asyncio.run(
            get_ids_to_iterate(node_id=collection.id)
        )
        logger.info(
            f"Working on: {collection.title}, #{counter} of {len(all_collections)}, "
            f"# of subcollections: {len(sub_collections)}"
        )

        missing_materials = {
            sub.id: search_hits_by_material_type(sub.title) for sub in sub_collections
        }

        search_store.append(
            SearchStore(node_id=collection.id, missing_materials=missing_materials)
        )

        missing_materials = {
            sub.id: search_hits_by_material_type(sub.title, oer_only=True)
            for sub in sub_collections
        }

        oer_search_store.append(
            SearchStore(node_id=collection.id, missing_materials=missing_materials)
        )

        materials = [
            PendingMaterials(**build_pending_materials(collection))
            for collection in sub_collections
        ]

        pending_materials_store.append(
            PendingMaterialsStore(
                collection_id=collection.id, missing_materials=materials
            )
        )

    logger.info("Storing in global store.")

    global_store.search = search_store
    global_store.oer_search = oer_search_store
    global_store.pending_materials = pending_materials_store

    logger.info("Background task done")


def build_pending_materials(
    collection: Row,
) -> dict[str, Union[uuid.UUID, list[uuid.UUID]]]:
    logger.info(f"Working on {collection.title}")

    pending_materials: dict[str, Union[uuid.UUID, list[uuid.UUID]]] = {
        "node_id": collection.id,
        **{
            required_collection_properties[attribute]: []
            for attribute in essential_frontend_properties
        },
    }

    for hit in pending_materials_search(collection.id).execute().hits:
        data = hit.to_dict()
        for attribute in essential_frontend_properties:
            if value := update_values_with_pending_materials(attribute, data):
                pending_materials[required_collection_properties[attribute]].append(
                    value
                )
    return pending_materials


def update_values_with_pending_materials(attribute, data):
    if attribute == ElasticResourceAttribute.EDU_ENDUSERROLE_DE.path:
        if (
            "i18n" not in data.keys()
            or "de_DE" not in data["i18n"].keys()
            or attribute.split(".")[-1] not in data["i18n"]["de_DE"].keys()
        ):
            return uuid.UUID(data["nodeRef"]["id"])
    elif attribute.split(".")[-1] not in data["properties"].keys():
        return uuid.UUID(data["nodeRef"]["id"])
    return


def pending_materials_search(node_id: uuid.UUID):
    base_search = base_missing_material_search(node_id)

    def attribute_specific_query(attribute: str) -> Query:
        if attribute == ElasticResourceAttribute.LICENSES.path:
            return query_missing_material_license().to_dict()
        return ~Wildcard(**{attribute: {"value": "*"}})

    return base_search.filter(
        Q(
            "bool",
            **{
                "minimum_should_match": 1,
                "should": [
                    attribute_specific_query(attribute)
                    for attribute in essential_frontend_properties
                ],
            },
        )
    )
