import uuid
from dataclasses import dataclass

from app.api.analytics.analytics import CountStatistics

_COLLECTIONS = "collections"
_MATERIALS = "materials"
_COLLECTION_COUNT = "counts"
_COLLECTION_COUNT_OER = "counts_oer"

"""
A quick fix for a global storage
"""
global_storage = {
    _COLLECTIONS: [],
    _MATERIALS: [],
    _COLLECTION_COUNT: {},
    _COLLECTION_COUNT_OER: {},
}  # TODO: Refactor me ASAP


@dataclass(frozen=True)
class SearchStore:
    __slots__ = "node_id", "missing_materials"
    node_id: uuid.UUID
    missing_materials: dict[uuid.UUID, CountStatistics]


@dataclass(frozen=False)
class Store:
    __slots__ = "search"
    search: list[SearchStore]


global_store = Store(search=[])
