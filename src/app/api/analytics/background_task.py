import asyncio
import os
import uuid
from datetime import datetime
from typing import Callable

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
    _MATERIALS,
    SearchStore,
    StorageModel,
    global_store,
)
from app.api.collections.counts import AggregationMappings, collection_counts
from app.core.config import BACKGROUND_TASK_TIME_INTERVAL
from app.core.constants import COLLECTION_NAME_TO_ID, COLLECTION_ROOT_ID
from app.core.logging import logger
from app.core.models import ElasticResourceAttribute, required_collection_properties
from app.elastic.elastic import ResourceType, query_many
from app.elastic.search import Search

background_router = APIRouter(tags=["Background"])


@background_router.post("/run-analytics", status_code=HTTP_202_ACCEPTED)
async def run_analytics(*, background_tasks: BackgroundTasks):
    background_tasks.add_task(run)


@repeat_every(seconds=BACKGROUND_TASK_TIME_INTERVAL, logger=logger)
def background_task():
    run()


def import_data_from_elasticsearch(derived_at: datetime, query: Callable, path: str):
    search = search_query(query, path)

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


def search_query(query: Callable, path: str) -> Search:
    search = (
        Search()
        .query(query(node_id=COLLECTION_ROOT_ID))
        .source(
            includes=["nodeRef.*", path, *list(required_collection_properties.keys())]
        )
    )
    return search


def run():
    derived_at = datetime.now()
    logger.info(f"{os.getpid()}: Starting analytics import at: {derived_at}")

    app.api.analytics.storage.global_storage[
        _COLLECTIONS
    ] = import_data_from_elasticsearch(
        derived_at=derived_at,
        query=lambda node_id: query_many(ResourceType.COLLECTION, node_id),
        path=ElasticResourceAttribute.PATH.path,
    )

    app.api.analytics.storage.global_storage[
        _MATERIALS
    ] = import_data_from_elasticsearch(
        derived_at=derived_at,
        query=lambda node_id: query_many(ResourceType.MATERIAL, node_id),
        path=ElasticResourceAttribute.COLLECTION_NODEREF_ID.path,
    )

    logger.info("Collection and materials imported")

    app.api.analytics.storage.global_storage[_COLLECTION_COUNT] = asyncio.run(
        collection_counts(COLLECTION_ROOT_ID, AggregationMappings.lrt)
    )
    app.api.analytics.storage.global_storage[_COLLECTION_COUNT_OER] = asyncio.run(
        collection_counts(COLLECTION_ROOT_ID, AggregationMappings.lrt, oer_only=True)
    )

    all_collections = [
        Row(id=uuid.UUID(value), title=key)
        for key, value in COLLECTION_NAME_TO_ID.items()
    ]
    logger.info(f"Tree ready to iterate. Length: {len(all_collections)}")

    # TODO Refactor, this is very expensive
    search_store = []
    for row in all_collections:
        sub_collections: list[Row] = asyncio.run(get_ids_to_iterate(node_id=row.id))
        logger.info(f"Working on: {row.title}, {len(sub_collections)}")
        missing_materials = {
            sub.id: search_hits_by_material_type(sub.title) for sub in sub_collections
        }

        search_store.append(
            SearchStore(node_id=row.id, missing_materials=missing_materials)
        )

    global_store.search = search_store

    logger.info("Background task done")
