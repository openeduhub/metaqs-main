import uuid

from app.api.collections.descendants import descendants_search


def test_descendants_search():
    dummy_node = uuid.UUID("f3dc9ea1-d608-4b4e-a78c-98063a3e8461")
    dummy_maximum_hits = 30
    search = descendants_search(dummy_node, dummy_maximum_hits, "", "")

    assert search.to_dict() == {
        "_source": [],
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
