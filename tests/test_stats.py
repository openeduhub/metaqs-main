import json
import uuid
from unittest import mock

import pytest

from app.api.analytics.models import Collection
from app.api.analytics.stats import (
    build_material_search,
    overall_stats,
    query_material_types,
)
from app.api.collections.counts import CollectionTreeCount
from app.elastic.utils import connect_to_elastic


@pytest.mark.asyncio
async def test_overall_stats():
    await connect_to_elastic()

    test_node = "4940d5da-9b21-4ec0-8824-d16e0409e629"  # Biology, cell types

    directory = "tests/unit_tests/resources"
    with open(f"{directory}/global_response.json") as file:
        global_response = json.load(file)

    # TODO: Refactor with wrapper/fixture/decorator
    with mock.patch("app.api.analytics.stats.global_storage") as mocked_global:

        def _get_item(_, key):
            if key == "collections":
                return [
                    Collection(
                        id=entry["id"],
                        doc=json.dumps(entry["doc"]),
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

        stats = await overall_stats(test_node)

    assert len(stats.stats) == 225
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

    with open(f"{directory}/global_response.json") as file:
        global_response = json.load(file)

    dummy_node = uuid.UUID("77caf20c-36cc-481e-a842-67fc7c56697a")
    with mock.patch("app.api.analytics.stats.global_storage") as mocked_global:

        def _get_item(_, key):
            if key == "collections":
                return [
                    Collection(
                        id=entry["id"],
                        doc=json.dumps(entry["doc"]),
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

    assert len(result) == 26
    first_value = result[list(result.keys())[0]]
    assert "total" in first_value.keys()
