import uuid
from unittest.mock import MagicMock

from elasticsearch_dsl.response import Response

from app.api.collections.counts import build_counts, query_portal_counts


def test_query_portal_counts():
    node_id = uuid.UUID("15fce411-54d9-467f-8f35-61ea374a298d")
    total_size_elastic = 500_000
    expected_query = {
        "query": {
            "bool": {
                "filter": [
                    {"term": {"permissions.Read.keyword": "GROUP_EVERYONE"}},
                    {"term": {"properties.cm:edu_metadataset.keyword": "mds_oeh"}},
                    {"term": {"nodeRef.storeRef.protocol": "workspace"}},
                    {"term": {"type": "ccm:io"}},
                    {"term": {"collections.path.keyword": node_id}},
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
                    "lrt": {
                        "terms": {
                            "field": "properties.ccm:oeh_lrt_aggregated.keyword",
                            "size": total_size_elastic,
                        }
                    }
                },
            }
        },
        "from": 0,
        "size": total_size_elastic,
        "_source": ["nodeRef.id", "properties.cm:title", "path", "parentRef.id"],
    }
    search = query_portal_counts(node_id)
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

    mocked_data.return_value = {"key": uuid.uuid4(), "doc_count": -1}
    mocked_data.lrt.buckets = [mocked_data]
    mocked_response.aggregations["collection_id"].buckets = [mocked_data]

    result = build_counts(mocked_response)

    assert len(result) == 1
    assert result[0].counts["total"] == -1
    assert isinstance(result[0].noderef_id, uuid.UUID)
