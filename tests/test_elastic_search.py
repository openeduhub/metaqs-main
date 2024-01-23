from app.elastic.search import MaterialSearch


def test_material_search():
    excpectation = {
        "query": {
            "bool": {
                "filter": [
                    {"term": {"permissions.Read.keyword": "GROUP_EVERYONE"}},
                    {"term": {"properties.cm:edu_metadataset.keyword": "mds_oeh"}},
                    {"term": {"nodeRef.storeRef.protocol": "workspace"}},
                    {"term": {"type": "ccm:io"}},
                    {'bool': {'must_not': [{'term': {'aspects': 'ccm:io_childobject'}}]}},
                ]
            }
        }
    }

    assert MaterialSearch().to_dict() == excpectation
