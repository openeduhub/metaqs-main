import json
import uuid
from unittest import mock

import pytest

from app.api.analytics.models import Collection
from app.api.analytics.stats import (
    Row,
    build_material_search,
    collections_with_missing_properties,
    materials_with_missing_properties,
    overall_stats,
    query_material_types,
)
from app.api.collections.counts import CollectionTreeCount


@pytest.mark.asyncio
async def test_overall_stats():
    test_node = "11bdb8a0-a9f5-4028-becc-cbf8e328dd4b"  # Spanish

    directory = "tests/unit_tests/resources"
    with open(f"{directory}/test_global.json") as file:
        global_response = json.load(file)

    # TODO: Refactor with wrapper/fixture/decorator
    with mock.patch("app.api.analytics.stats.global_storage") as mocked_global:

        def _get_item(_, key):
            if key == "collections":
                return [
                    Collection(
                        id=entry["id"],
                        doc=entry["doc"],
                        derived_at=entry["derived_at"],
                    )
                    for entry in global_response[key]
                ]
            if key == "counts":
                return [
                    CollectionTreeCount(
                        noderef_id=entry["noderef_id"],
                        total=entry["total"],
                        counts=entry["counts"],
                    )
                    for entry in global_response[key]
                ]
            return global_response[key]

        mocked_global.__getitem__ = _get_item

        with mock.patch(
            "app.api.analytics.stats.search_hits_by_material_type"
        ) as mocked_search:
            with mock.patch("app.api.analytics.stats.get_ids_to_iterate") as mocked_ids:
                mocked_search.return_value = {"total": 30}
                mocked_ids.return_value = [
                    Row(
                        id=uuid.UUID("f3dc9ea1-d608-4b4e-a78c-98063a3e8461"),
                        title="test_title",
                    )
                ]
                stats = await overall_stats(test_node)

    assert len(stats.stats) == 1
    first_key_values = stats.stats[list(stats.stats.keys())[0]]

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
                                "i18n.de_DE.ccm:oeh_lrt_aggregated",
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
                    "field": "properties.ccm:oeh_lrt_aggregated.keyword",
                }
            }
        },
    }


def test_query_material_types():
    directory = "tests/unit_tests/resources"

    with open(f"{directory}/test_global.json") as file:
        global_response = json.load(file)

    dummy_node = uuid.UUID("11bdb8a0-a9f5-4028-becc-cbf8e328dd4b")
    with mock.patch("app.api.analytics.stats.global_storage") as mocked_global:

        def _get_item(_, key):
            if key == "collections":
                return [
                    Collection(
                        id=entry["id"],
                        doc=entry["doc"],
                        derived_at=entry["derived_at"],
                    )
                    for entry in global_response[key]
                ]
            if key == "counts":
                return [
                    CollectionTreeCount(
                        noderef_id=entry["noderef_id"],
                        total=entry["total"],
                        counts=entry["counts"],
                    )
                    for entry in global_response[key]
                ]
            return global_response[key]

        mocked_global.__getitem__ = _get_item

        result = query_material_types(dummy_node)

    assert len(result) == 1
    first_value = result[list(result.keys())[0]]
    assert "total" in first_value.keys()


def test_collections_with_missing_properties():
    directory = "tests/unit_tests/resources"

    with open(f"{directory}/test_global.json") as file:
        global_response = json.load(file)

    dummy_node = uuid.UUID("11bdb8a0-a9f5-4028-becc-cbf8e328dd4b")
    with mock.patch("app.api.analytics.stats.global_storage") as mocked_global:

        def _get_item(_, key):
            if key == "collections":
                return [
                    Collection(
                        id=entry["id"],
                        doc=entry["doc"],
                        derived_at=entry["derived_at"],
                    )
                    for entry in global_response[key]
                ]
            if key == "counts":
                return [
                    CollectionTreeCount(
                        noderef_id=entry["noderef_id"],
                        total=entry["total"],
                        counts=entry["counts"],
                    )
                    for entry in global_response[key]
                ]
            return global_response[key]

        mocked_global.__getitem__ = _get_item

        result = collections_with_missing_properties(dummy_node)

    assert len(result) == 1
    assert result[0].noderef_id == uuid.UUID("f3dc9ea1-d608-4b4e-a78c-98063a3e8461")
    assert result[0].validation_stats == {
        "title": None,
        "keywords": ["missing"],
        "description": ["missing"],
        "edu_context": None,
    }


def test_materials_with_missing_properties():
    directory = "tests/unit_tests/resources"

    with open(f"{directory}/test_global.json") as file:
        global_response = json.load(file)

    dummy_node = uuid.UUID("11bdb8a0-a9f5-4028-becc-cbf8e328dd4b")
    with mock.patch("app.api.analytics.stats.global_storage") as mocked_global:

        def _get_item(_, key):
            if key in ["collections", "materials"]:
                return [
                    Collection(
                        id=entry["id"],
                        doc=entry["doc"],
                        derived_at=entry["derived_at"],
                    )
                    for entry in global_response[key]
                ]
            if key == "counts":
                return [
                    CollectionTreeCount(
                        noderef_id=entry["noderef_id"],
                        total=entry["total"],
                        counts=entry["counts"],
                    )
                    for entry in global_response[key]
                ]
            return global_response[key]

        mocked_global.__getitem__ = _get_item

        result = materials_with_missing_properties(dummy_node)

    assert len(result) == 1
    assert result[0].noderef_id == uuid.UUID("f3dc9ea1-d608-4b4e-a78c-98063a3e8461")
    dummy_material_node = uuid.UUID("263afc5b-6445-4a5a-b014-a77f1db473b9")
    assert result[0].validation_stats.ads_qualifier.missing == [dummy_material_node]
    assert result[0].validation_stats.object_type is None
