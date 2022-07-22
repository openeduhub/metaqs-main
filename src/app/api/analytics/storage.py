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
class SearchStoreCollection:
    node_id: uuid.UUID
    missing_materials: CountStatistics


@dataclass(frozen=True)
class SearchStore:
    __slots__ = "node_id", "collections"
    node_id: uuid.UUID
    collections: dict[uuid.UUID, SearchStoreCollection]


@dataclass(frozen=True)
class Store:
    __slots__ = "search"
    search: list[SearchStore]


global_store = Store(search=[])
