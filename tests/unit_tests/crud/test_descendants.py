import uuid

from app.api.collections.descendants import descendants_search, material_counts_search


def test_descendants_search():
    dummy_node = uuid.UUID("f3dc9ea1-d608-4b4e-a78c-98063a3e8461")
    dummy_maximum_hits = 30
    search = descendants_search(dummy_node, dummy_maximum_hits)

    assert search.to_dict() == {
        "_source": {
            "includes": [
                "nodeRef.id",
                "type",
                "properties.cm:name",
                "properties.cm:title",
                "properties.cclom:general_keyword",
                "properties.cm:description",
                "path",
                "parentRef.id",
            ]
        },
        "from": 0,
        "query": {
            "bool": {
                "filter": [
                    {"term": {"permissions.Read.keyword": "GROUP_EVERYONE"}},
                    {"term": {"properties.cm:edu_metadataset.keyword": "mds_oeh"}},
                    {"term": {"nodeRef.storeRef.protocol": "workspace"}},
                    {"term": {"type": "ccm:map"}},
                ],
                "minimum_should_match": 1,
                "should": [
                    {"match": {"path": dummy_node}},
                    {"match": {"nodeRef.id": dummy_node}},
                ],
            }
        },
        "size": dummy_maximum_hits,
    }


def test_material_counts_search():
    dummy_node = uuid.UUID("f3dc9ea1-d608-4b4e-a78c-98063a3e8461")
    search = material_counts_search(dummy_node)

    assert search.to_dict() == {
        "aggs": {
            "grouped_by_collection": {
                "aggs": {
                    "sorted_by_count": {
                        "bucket_sort": {"sort": [{"_count": {"order": "asc"}}]}
                    }
                },
                "composite": {
                    "size": 65536,
                    "sources": [
                        {
                            "noderef_id": {
                                "terms": {"field": "collections.nodeRef.id.keyword"}
                            }
                        }
                    ],
                },
            }
        },
        "query": {
            "bool": {
                "filter": [
                    {"term": {"permissions.Read.keyword": "GROUP_EVERYONE"}},
                    {"term": {"properties.cm:edu_metadataset.keyword": "mds_oeh"}},
                    {"term": {"nodeRef.storeRef.protocol": "workspace"}},
                    {"term": {"type": "ccm:io"}},
                    {"term": {"collections.path.keyword": dummy_node}},
                ]
            }
        },
    }
