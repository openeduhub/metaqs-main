from app.elastic.search import Search


def test_search_base_filters():
    search = Search().base_filters()
    assert search.to_dict() == {
        "query": {
            "bool": {
                "filter": [
                    {"term": {"permissions.Read.keyword": "GROUP_EVERYONE"}},
                    {"term": {"properties.cm:edu_metadataset.keyword": "mds_oeh"}},
                    {"term": {"nodeRef.storeRef.protocol": "workspace"}},
                ]
            }
        }
    }
