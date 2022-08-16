import uuid
from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel

from app.api.analytics.analytics import CountStatistics, PendingMaterialsResponse

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


@dataclass
class Store:
    __slots__ = "search", "oer_search", "pending_materials"
    search: list[SearchStore]
    oer_search: list[SearchStore]
    pending_materials: dict[uuid.UUID, PendingMaterialsResponse]


global_store = Store(search=[], oer_search=[], pending_materials={})


# TODO: Rename, as used for materials in background_task, as well
class StorageModel(BaseModel):
    id: str  # TODO: Refactored to UUID
    doc: dict
    derived_at: datetime
