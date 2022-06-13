import uuid

from app.api.collections.counts import query_portal_counts


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
