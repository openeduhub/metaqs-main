def test_missing_attributes_search():
    dummy_uuid = uuid.uuid4()
    dummy_attribute = "properties.cm:title"
    dummy_missing_attribute = missing_attribute_filter[0].value
    dummy_maximum_size = 3
    search = missing_attributes_search(
        dummy_uuid, dummy_missing_attribute, dummy_maximum_size
    )
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
                "must_not": [{"wildcard": {dummy_attribute: {"value": "*"}}}],
                "should": [
                    {"match": {"path": dummy_uuid}},
                    {"match": {"nodeRef.id": dummy_uuid}},
                ],
            }
        },
        "size": dummy_maximum_size,
    }
