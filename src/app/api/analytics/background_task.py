import asyncio
import os
from datetime import datetime

from fastapi import APIRouter
from fastapi_utils.tasks import repeat_every
from starlette.background import BackgroundTasks
from starlette.status import HTTP_202_ACCEPTED

import app.api.analytics.storage
from app.api.analytics.models import Collection
from app.api.analytics.stats import get_ids_to_iterate, search_hits_by_material_type
from app.api.analytics.storage import (
    _COLLECTION_COUNT,
    _COLLECTIONS,
    _MATERIALS,
    _SEARCH,
)
from app.api.collections.counts import AggregationMappings, collection_counts
from app.api.score.models import required_collection_properties
from app.core.config import BACKGROUND_TASK_TIME_INTERVAL
from app.core.constants import COLLECTION_ROOT_ID
from app.core.logging import logger
from app.elastic.elastic import query_collections, query_materials
from app.elastic.search import Search

background_router = APIRouter(tags=["Background"])


@background_router.post("/run-analytics", status_code=HTTP_202_ACCEPTED)
async def run_analytics(*, background_tasks: BackgroundTasks):
    background_tasks.add_task(run)


@repeat_every(seconds=BACKGROUND_TASK_TIME_INTERVAL, logger=logger)
def background_task():
    run()


def import_collections(derived_at: datetime):
    s = (
        Search()
        .query(query_collections(node_id=COLLECTION_ROOT_ID))
        .source(
            includes=["nodeRef.*", "path", *list(required_collection_properties.keys())]
        )
    )

    seen = set()
    collections = []
    for hit in s.scan():
        if hit.nodeRef["id"] in seen:
            continue

        seen.add(hit.nodeRef["id"])
        collections.append(
            Collection(
                id=str(hit.nodeRef["id"]),
                doc=hit.to_dict(),
                derived_at=derived_at,
            )
        )
    app.api.analytics.storage.global_storage[_COLLECTIONS] = collections


def import_materials(derived_at: datetime):
    s = (
        Search()
        .query(query_materials(node_id=COLLECTION_ROOT_ID))
        .source(
            includes=[
                "nodeRef.*",
                "collections.nodeRef.id",
                *list(required_collection_properties.keys()),
            ]
        )
    )

    seen = set()
    collections = []
    for hit in s.scan():
        node_id = hit.nodeRef["id"]
        if node_id not in seen:
            seen.add(node_id)
            collections.append(
                Collection(
                    id=str(node_id),
                    doc=hit.to_dict(),
                    derived_at=derived_at,
                )
            )
    app.api.analytics.storage.global_storage[_MATERIALS] = collections


def run():
    derived_at = datetime.now()
    logger.info(f"{os.getpid()}: Starting analytics import at: {derived_at}")

    import_collections(derived_at=derived_at)

    import_materials(derived_at=derived_at)

    print("Collection and materials imported")

    app.api.analytics.storage.global_storage[_COLLECTION_COUNT] = asyncio.run(
        collection_counts(COLLECTION_ROOT_ID, AggregationMappings.lrt)
    )

    all_collections = asyncio.run(get_ids_to_iterate(node_id=COLLECTION_ROOT_ID))
    print("Tree ready to iterate. Length: ", len(all_collections))

    # TODO Refactor, this is very expensive
    app.api.analytics.storage.global_storage[_SEARCH] = {
        row.id: search_hits_by_material_type(row.title) for row in all_collections
    }
    print("Background task done")
