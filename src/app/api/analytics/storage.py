import uuid
from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel

from app.api.analytics.analytics import CountStatistics

_COLLECTIONS = "collections"
_COLLECTION_COUNT = "counts"
_COLLECTION_COUNT_OER = "counts_oer"

"""
A quick fix for a global storage
"""
global_storage = {
    _COLLECTIONS: [],
    _COLLECTION_COUNT: {},
    _COLLECTION_COUNT_OER: {},
}  # TODO: Refactor me ASAP


@dataclass(frozen=True)
class SearchStore:
    __slots__ = "node_id", "missing_materials"
    node_id: uuid.UUID
    missing_materials: dict[uuid.UUID, CountStatistics]


@dataclass(frozen=True)
class PendingMaterials:
    __slots__ = (
        "node_id",
        "title",
        "edu_context",
        "url",
        "description",
        "license",
        "learning_resource_type",
        "taxon_id",
        "publisher",
        "intended_end_user_role",
    )
    node_id: uuid.UUID
    title: list[uuid.UUID]
    edu_context: list[uuid.UUID]
    url: list[uuid.UUID]
    description: list[uuid.UUID]
    license: list[uuid.UUID]
    learning_resource_type: list[uuid.UUID]
    taxon_id: list[uuid.UUID]
    publisher: list[uuid.UUID]
    intended_end_user_role: list[uuid.UUID]


@dataclass(frozen=True)
class PendingMaterialsStore:
    __slots__ = "collection_id", "missing_materials"
    collection_id: uuid.UUID
    missing_materials: list[PendingMaterials]


@dataclass(frozen=False)
class Store:
    __slots__ = "search", "oer_search", "pending_materials"
    search: list[SearchStore]
    oer_search: list[SearchStore]
    pending_materials: list[PendingMaterialsStore]


global_store = Store(search=[], oer_search=[], pending_materials=[])


# TODO: Rename, as used for materials in background_task, as well
class StorageModel(BaseModel):
    id: str  # TODO: Refactored to UUID
    doc: dict
    derived_at: datetime
