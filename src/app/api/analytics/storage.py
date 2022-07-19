_COLLECTIONS = "collections"
_MATERIALS = "materials"
_SEARCH = "search"
_COLLECTION_COUNT = "counts"
_COLLECTION_COUNT_OER = "counts_oer"

"""
A quick fix for a global storage
"""
global_storage = {
    _COLLECTIONS: [],
    _MATERIALS: [],
    _SEARCH: {},
    _COLLECTION_COUNT: {},
    _COLLECTION_COUNT_OER: {},
}  # TODO: Refactor me ASAP
