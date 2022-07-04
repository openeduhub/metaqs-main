import json
import os
from datetime import datetime
from uuid import UUID

from elasticsearch_dsl.query import Query
from fastapi import APIRouter
from fastapi_utils.tasks import repeat_every
from starlette.background import BackgroundTasks
from starlette.status import HTTP_202_ACCEPTED

from app.api.analytics.models import Collection
from app.api.collections.missing_materials import base_filter
from app.api.score.models import LearningMaterialAttribute
from app.core.constants import COLLECTION_ROOT_ID
from app.core.logging import logger
from app.elastic.dsl import qbool, qterm
from app.elastic.elastic import ResourceType, type_filter
from app.elastic.search import Search
from app.models import CollectionAttribute

background_router = APIRouter()

_COLLECTIONS = "collections"
_MATERIALS = "materials"
"""
A quick fix for a global storage
"""
global_storage = {_COLLECTIONS: [], _MATERIALS: []}  # TODO: Refactor me ASAP


@background_router.post(
    "/run-analytics",
    status_code=HTTP_202_ACCEPTED,
    tags=["Background Tasks", "Authenticated"],
)
async def run_analytics(*, background_tasks: BackgroundTasks):
    background_tasks.add_task(run)


@repeat_every(seconds=10, logger=logger)
def background_task():
    run()


def query_many(resource_type: ResourceType, ancestor_id: UUID = None) -> Query:
    qfilter = [*base_filter, *type_filter[resource_type]]
    if ancestor_id:
        if resource_type is ResourceType.COLLECTION:
            qfilter.append(qterm(qfield=CollectionAttribute.PATH, value=ancestor_id))
        elif resource_type is ResourceType.MATERIAL:
            qfilter.append(
                qterm(
                    qfield=LearningMaterialAttribute.COLLECTION_PATH, value=ancestor_id
                )
            )

    return qbool(filter=qfilter)


def query_collections(ancestor_id: UUID = None) -> Query:
    return query_many(ResourceType.COLLECTION, ancestor_id=ancestor_id)


def import_collections(derived_at: datetime):
    s = (
        Search()
        .query(query_collections(ancestor_id=COLLECTION_ROOT_ID))
        .source(includes=["type", "aspects", "properties.*", "nodeRef.*", "path"])
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
                doc=json.dumps(hit.to_dict()),
                derived_at=derived_at,
            )
        )
    global global_storage
    global_storage[_COLLECTIONS] = collections


def query_materials(ancestor_id: UUID = None) -> Query:
    return query_many(ResourceType.MATERIAL, ancestor_id=ancestor_id)


def import_materials(derived_at: datetime):
    s = (
        Search()
        .query(query_materials(ancestor_id=COLLECTION_ROOT_ID))
        .source(
            includes=[
                "type",
                "aspects",
                "properties.*",
                "nodeRef.*",
                "collections.nodeRef.id",
            ]
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
                doc=json.dumps(hit.to_dict()),
                derived_at=derived_at,
            )
        )
    global global_storage
    global_storage[_MATERIALS] = collections


def run():
    derived_at = datetime.now()

    logger.info(f"{os.getpid()}: Starting analytics import at: {derived_at}")
    print(f"{os.getpid()}: Starting analytics import at: {derived_at}")

    import_collections(derived_at=derived_at)
    import_materials(derived_at=derived_at)
