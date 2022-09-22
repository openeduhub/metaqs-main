import json
import uuid
from unittest.mock import MagicMock

from elasticsearch_dsl.response import Response

from app.api.collections.counts import (
    AggregationMappings,
    _build_counts,
    _collection_counts_search,
)


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
                    {'bool': {'must_not': [{'term': {'aspects': 'ccm:io_childobject'}}]}},
                    {
                        "bool": {
                            "should": [
                                {"term": {"collections.nodeRef.id.keyword": str(node_id)}},
                                {"match": {"collections.path.keyword": str(node_id)}},
                            ]
                        }
                    },
                ]
            }
        },
        "aggs": {
            "collection_id": {
                "terms": {"field": "collections.nodeRef.id.keyword", "size": total_size_elastic},
                "aggs": {"facet": {"terms": {"field": facet, "size": total_size_elastic, "missing": "N/A"}}},
            }
        },
        "size": 0,
    }
    print(json.dumps(expected_query))
    search = _collection_counts_search(node_id, facet=facet, oer_only=False)
    assert search.to_dict() == expected_query


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
                    {'bool': {'must_not': [{'term': {'aspects': 'ccm:io_childobject'}}]}},
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
                    {
                        "bool": {
                            "should": [
                                {"term": {"collections.nodeRef.id.keyword": str(node_id)}},
                                {"match": {"collections.path.keyword": str(node_id)}},
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
                "aggs": {"facet": {"terms": {"field": facet, "size": total_size_elastic, "missing": "N/A"}}},
            }
        },
        "size": 0,
    }
    search = _collection_counts_search(node_id, facet=facet, oer_only=True)
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

    result = _build_counts(mocked_response)

    assert len(result) == 1
    assert result[0].total == 1
    assert list(result[0].counts.values())[0] == -1
    assert isinstance(result[0].node_id, uuid.UUID)
