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

expected_output_particle_model = {
    "derived_at": "1970-01-01T00:00:00",
    "stats": {
        "f75eec46-f7a9-44b3-ad2a-1fee76a3b1a3": {
            "search": {
                "N/A": 10,
                "total": 244,
                "http://w3id.org/openeduhub/vocabs/new_lrt_aggregated/05aa0f49-7e1b-498b-a7d5-c5fc8e73b2e2": 29,
                "http://w3id.org/openeduhub/vocabs/new_lrt_aggregated/0b2d7dec-8eb1-4a28-9cf2-4f3a4f5a511b": 3,
                "http://w3id.org/openeduhub/vocabs/new_lrt_aggregated/101c0c66-5202-4eba-9ebf-79f4903752b9": 2,
                "http://w3id.org/openeduhub/vocabs/new_lrt_aggregated/38774279-af36-4ec2-8e70-811d5a51a6a1": 149,
                "http://w3id.org/openeduhub/vocabs/new_lrt_aggregated/8526273b-2b21-46f2-ac8d-bbf362c8a690": 5,
                "http://w3id.org/openeduhub/vocabs/new_lrt_aggregated/b8fb5fb2-d8bf-4bbe-ab68-358b65a26bed": 2,
                "http://w3id.org/openeduhub/vocabs/new_lrt_aggregated/c8e52242-361b-4a2a-b95d-25e516b28b45": 18,
                "http://w3id.org/openeduhub/vocabs/new_lrt_aggregated/cf8929a7-d521-4f17-bbe3-96748c862486": 4,
                "http://w3id.org/openeduhub/vocabs/new_lrt_aggregated/f1341358-3f91-449b-b6eb-f58636f756a0": 8,
                "http://w3id.org/openeduhub/vocabs/new_lrt_aggregated/ffe4d8e8-3cfd-4e9a-b025-83f129eb5c9d": 14,
            },
            "material_types": {
                "total": 26,
                "http://w3id.org/openeduhub/vocabs/new_lrt_aggregated/02bfd0fe-96ab-4dd6-a306-ec362ec25ea0": 1,
                "http://w3id.org/openeduhub/vocabs/new_lrt_aggregated/05aa0f49-7e1b-498b-a7d5-c5fc8e73b2e2": 5,
                "http://w3id.org/openeduhub/vocabs/new_lrt_aggregated/0b2d7dec-8eb1-4a28-9cf2-4f3a4f5a511b": 8,
                "http://w3id.org/openeduhub/vocabs/new_lrt_aggregated/101c0c66-5202-4eba-9ebf-79f4903752b9": 1,
                "http://w3id.org/openeduhub/vocabs/new_lrt_aggregated/11f438d7-cb11-49c2-8e67-2dd7df677092": 1,
                "http://w3id.org/openeduhub/vocabs/new_lrt_aggregated/2e678af3-1026-4171-b88e-3b3a915d1673": 7,
                "http://w3id.org/openeduhub/vocabs/new_lrt_aggregated/37a3ad9c-727f-4b74-bbab-27d59015c695": 3,
                "http://w3id.org/openeduhub/vocabs/new_lrt_aggregated/38774279-af36-4ec2-8e70-811d5a51a6a1": 4,
                "http://w3id.org/openeduhub/vocabs/new_lrt_aggregated/8526273b-2b21-46f2-ac8d-bbf362c8a690": 1,
                "http://w3id.org/openeduhub/vocabs/new_lrt_aggregated/9bbb50a2-10c5-4a8b-9e0e-6a5fc86c40fe": 1,
                "http://w3id.org/openeduhub/vocabs/new_lrt_aggregated/b8fb5fb2-d8bf-4bbe-ab68-358b65a26bed": 2,
                "http://w3id.org/openeduhub/vocabs/new_lrt_aggregated/c8e52242-361b-4a2a-b95d-25e516b28b45": 11,
                "http://w3id.org/openeduhub/vocabs/new_lrt_aggregated/e10e9add-700e-4b57-a9c5-8f1088bb0545": 2,
                "http://w3id.org/openeduhub/vocabs/new_lrt_aggregated/f1341358-3f91-449b-b6eb-f58636f756a0": 8,
                "http://w3id.org/openeduhub/vocabs/new_lrt_aggregated/ffe4d8e8-3cfd-4e9a-b025-83f129eb5c9d": 2,
            },
        }
    },
}


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
