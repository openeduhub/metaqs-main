import json
import uuid
from pathlib import Path
from unittest import mock

import pytest

from app.api.collections.collection_validation import (
    build_material_search,
    collections_with_missing_properties,
    overall_stats,
    query_material_types,
)
from app.api.analytics.storage import SearchStore, StorageModel
from app.api.collections.counts import CollectionTreeCount


@pytest.mark.asyncio
async def test_overall_stats():
    test_node = "11bdb8a0-a9f5-4028-becc-cbf8e328dd4b"  # Spanish

    directory = Path(__file__).parent / "unit_tests" / "resources"
    with open(directory / "test_global.json") as file:
        global_response = json.load(file)

    # TODO: Refactor with wrapper/fixture/decorator
    with mock.patch(
        "app.api.collections.collection_validation.global_storage"
    ) as mocked_global:

        def _get_item(_, key):
            if key == "collections":
                return [
                    StorageModel(
                        id=entry["id"],
                        doc=entry["doc"],
                        derived_at=entry["derived_at"],
                    )
                    for entry in global_response[key]
                ]
            if key == "counts" or key == "counts_oer":
                return [
                    CollectionTreeCount(
                        node_id=entry["noderef_id"],
                        total=entry["total"],
                        counts=entry["counts"],
                    )
                    for entry in global_response[key]
                ]
            if key == "search":
                return [
                    SearchStore(
                        node_id=uuid.UUID(test_node),
                        missing_materials={
                            key: item["missing_materials"]
                            for key, item in entry["collections"].items()
                        },
                    )
                    for entry in global_response[key]
                ]
            return global_response[key]

        mocked_global.__getitem__ = _get_item

        with mock.patch(
            "app.api.collections.collection_validation.global_store"
        ) as mocked_store:
            mocked_store.search = _get_item(None, "search")

            with mock.patch(
                "app.api.collections.collection_validation.search_hits_by_material_type"
            ):
                with mock.patch(
                    "app.api.collections.collection_validation.oer_ratio"
                ) as mocked_oer_ratio:
                    mocked_oer_ratio.return_value = 0
                    stats = await overall_stats(uuid.UUID(test_node))

    assert len(stats.total_stats) == 1
    first_key_values = stats.total_stats[list(stats.total_stats.keys())[0]]

    # assert correct structure
    assert list(first_key_values.keys()) == ["search", "material_types"]
    assert "total" in list(first_key_values["search"].keys())


def test_build_material_search():
    dummy_query = "dummy_query"
    search = build_material_search(dummy_query)

    assert search.to_dict() == {
        "query": {
            "bool": {
                "filter": [
                    {"term": {"permissions.Read.keyword": "GROUP_EVERYONE"}},
                    {"term": {"properties.cm:edu_metadataset.keyword": "mds_oeh"}},
                    {"term": {"nodeRef.storeRef.protocol": "workspace"}},
                    {"term": {"type": "ccm:io"}},
                ],
                "must": [
                    {
                        "simple_query_string": {
                            "default_operator": "and",
                            "query": dummy_query,
                            "fields": [
                                "properties.cclom:title",
                                "properties.cclom:general_keyword",
                                "properties.cclom:general_description",
                                "content.fulltext",
                                "i18n.de_DE.ccm:taxonid",
                                "i18n.de_DE.ccm:oeh_lrt",
                                "i18n.de_DE.ccm:educationalcontext",
                                "i18n.de_DE.ccm:educationalintendedenduserrole",
                            ],
                        }
                    }
                ],
            }
        },
        "aggs": {
            "material_types": {
                "terms": {
                    "missing": "N/A",
                    "size": 500000,
                    "field": "properties.ccm:oeh_lrt.keyword",
                }
            }
        },
    }


def test_query_material_types():
    directory = Path(__file__).parent / "unit_tests" / "resources"

    with open(directory / "test_global.json") as file:
        global_response = json.load(file)

    dummy_node = uuid.UUID("11bdb8a0-a9f5-4028-becc-cbf8e328dd4b")
    with mock.patch(
        "app.api.collections.collection_validation.global_storage"
    ) as mocked_global:

        def _get_item(_, key):
            if key == "collections":
                return [
                    StorageModel(
                        id=entry["id"],
                        doc=entry["doc"],
                        derived_at=entry["derived_at"],
                    )
                    for entry in global_response[key]
                ]
            if key == "counts":
                return [
                    CollectionTreeCount(
                        node_id=entry["noderef_id"],
                        total=entry["total"],
                        counts=entry["counts"],
                    )
                    for entry in global_response[key]
                ]
            return global_response[key]

        mocked_global.__getitem__ = _get_item

        result = query_material_types(dummy_node, "counts")

    assert len(result) == 1
    first_value = result[list(result.keys())[0]]
    assert "total" in first_value.keys()


def test_collections_with_missing_properties():
    directory = Path(__file__).parent / "unit_tests" / "resources"

    with open(directory / "test_global.json") as file:
        global_response = json.load(file)

    dummy_node = uuid.UUID("11bdb8a0-a9f5-4028-becc-cbf8e328dd4b")
    with mock.patch(
        "app.api.collections.collection_validation.global_storage"
    ) as mocked_global:

        def _get_item(_, key):
            if key == "collections":
                return [
                    StorageModel(
                        id=entry["id"],
                        doc=entry["doc"],
                        derived_at=entry["derived_at"],
                    )
                    for entry in global_response[key]
                ]
            if key == "counts":
                return [
                    CollectionTreeCount(
                        node_id=entry["noderef_id"],
                        total=entry["total"],
                        counts=entry["counts"],
                    )
                    for entry in global_response[key]
                ]
            return global_response[key]

        mocked_global.__getitem__ = _get_item

        result = collections_with_missing_properties(dummy_node)

    assert len(result) == 1
    assert result[0].node_id == uuid.UUID("f3dc9ea1-d608-4b4e-a78c-98063a3e8461")
    assert result[0].description == ["missing"]
    assert result[0].title is None
    assert result[0].edu_context == ["missing"]
