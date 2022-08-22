import pprint
import uuid
from unittest.mock import MagicMock

import pytest
from elasticsearch_dsl.response import Response

from app.api.collections.counts import (
    AggregationMappings,
    build_counts,
    collection_counts_search,
)
from app.api.collections.material_counts import (
    get_collection_material_counts,
    CollectionMaterialCount,
)
from app.api.collections.tree import build_collection_tree
from app.core.constants import COLLECTION_NAME_TO_ID
from app.elastic.utils import connect_to_elastic
from tests.conftest import elastic_search_mock


def test_query_collection_counts():
    node_id = uuid.UUID("15fce411-54d9-467f-8f35-61ea374a298d")
    total_size_elastic = 500_000
    facet = AggregationMappings.lrt
    expected_query = {
        "query": {
            "bool": {
                "filter": [
                    {"term": {"permissions.Read.keyword": "GROUP_EVERYONE"}},
                    {"term": {"properties.cm:edu_metadataset.keyword": "mds_oeh"}},
                    {"term": {"nodeRef.storeRef.protocol": "workspace"}},
                    {"term": {"type": "ccm:io"}},
                    {"term": {"collections.path.keyword": str(node_id)}},
                ]
            }
        },
        "aggs": {
            "collection_id": {
                "terms": {
                    "field": "collections.nodeRef.id.keyword",
                    "size": total_size_elastic,
                },
                "aggs": {
                    "facet": {
                        "terms": {
                            "field": facet,
                            "size": total_size_elastic,
                        }
                    }
                },
            }
        },
        "size": 0,
    }
    search = collection_counts_search(node_id, facet=facet, oer_only=False)
    assert search.to_dict() == expected_query


@pytest.mark.asyncio
async def test_get_collection_material_counts():
    biology = uuid.UUID(COLLECTION_NAME_TO_ID["Biologie"])
    with elastic_search_mock(resource="build-collection-tree"):
        collection = build_collection_tree(node_id=biology)
    with elastic_search_mock(resource="collection-material-counts"):
        result = await get_collection_material_counts(collection=collection)

    counts_by_id = {item.node_id: item for item in result}

    assert all(
        node.node_id in counts_by_id for node in collection.flatten(root=True)
    ), "count result does not contain counts for all nodes of the collection tree"

    expected = [
        CollectionMaterialCount(
            node_id=uuid.UUID("2e674483-0eae-4088-b51a-c4f4bbf86bcc"),
            title="Evolution",
            materials_count=0,
        ),
        CollectionMaterialCount(
            node_id=uuid.UUID("220f48a8-4b53-4179-919d-7cd238ed567e"),
            title="Chemische Grundlagen",
            materials_count=5,
        ),
        CollectionMaterialCount(
            node_id=uuid.UUID("15fce411-54d9-467f-8f35-61ea374a298d"),
            title="Biologie",
            materials_count=8,
        ),
        CollectionMaterialCount(
            node_id=uuid.UUID("a5ce08a9-1e78-4028-bf5e-9205f598f11a"),
            title="Wasser - Grundstoff des Lebens",
            materials_count=10,
        ),
        CollectionMaterialCount(
            node_id=uuid.UUID("81445550-fcc4-4f9e-99af-652dda269175"),
            title="Luft und Atmosphäre",
            materials_count=15,
        ),
    ]

    assert result == expected


def test_query_collection_counts_oer():
    node_id = uuid.UUID("15fce411-54d9-467f-8f35-61ea374a298d")
    total_size_elastic = 500_000
    facet = AggregationMappings.lrt
    expected_query = {
        "query": {
            "bool": {
                "filter": [
                    {"term": {"permissions.Read.keyword": "GROUP_EVERYONE"}},
                    {"term": {"properties.cm:edu_metadataset.keyword": "mds_oeh"}},
                    {"term": {"nodeRef.storeRef.protocol": "workspace"}},
                    {"term": {"type": "ccm:io"}},
                    {"term": {"collections.path.keyword": str(node_id)}},
                    {
                        "terms": {
                            "properties.ccm:commonlicense_key.keyword": [
                                "CC_0",
                                "PDM",
                                "CC_BY",
                                "CC_BY_SA",
                            ]
                        }
                    },
                ]
            }
        },
        "aggs": {
            "collection_id": {
                "terms": {
                    "field": "collections.nodeRef.id.keyword",
                    "size": total_size_elastic,
                },
                "aggs": {
                    "facet": {
                        "terms": {
                            "field": facet,
                            "size": total_size_elastic,
                        }
                    }
                },
            }
        },
        "size": 0,
    }
    search = collection_counts_search(node_id, facet=facet, oer_only=True)
    assert search.to_dict() == expected_query


def _get_key(key):
    mocked_data = {"key": uuid.uuid4().__str__(), "doc_count": -1}
    return mocked_data[key]


def test_build_counts():
    mocked_response = Response(
        "",
        {
            "aggregations": MagicMock(),
        },
    )

    mocked_data = MagicMock()
    mocked_data.__getitem__.side_effect = _get_key

    dummy_id = uuid.uuid4()
    mocked_data.return_value = {"key": dummy_id, "doc_count": -1}
    mocked_data.facet.buckets = [mocked_data]
    mocked_response.aggregations["collection_id"].buckets = [mocked_data]

    result = build_counts(mocked_response)

    assert len(result) == 1
    assert result[0].total == 1
    assert list(result[0].counts.values())[0] == -1
    assert isinstance(result[0].node_id, uuid.UUID)
