import uuid
from dataclasses import dataclass

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


@dataclass
class SearchStoreCollection:
    node_id: uuid.UUID
    missing_materials: dict[str, int]


@dataclass
class SearchStore:
    __slots__ = "node_id", "collections"
    node_id: uuid.UUID
    collections: dict[uuid.UUID, SearchStoreCollection]


@dataclass
class Store:
    __slots__ = "search"
    search: list[SearchStore]


global_store = Store(search=[])
