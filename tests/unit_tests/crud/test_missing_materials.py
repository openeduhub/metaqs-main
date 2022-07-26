import uuid

from app.api.collections.missing_materials import missing_attributes_search
from app.api.collections.pending_collections import missing_attribute_filter


def test_missing_materials_search():
    dummy_uuid = uuid.uuid4()
    dummy_attribute = "properties.cm:title"
    dummy_missing_attribute = missing_attribute_filter[0].value
    dummy_maximum_size = 3
    search = missing_attributes_search(
        dummy_uuid, dummy_missing_attribute, dummy_maximum_size
    )
    actual = search.to_dict()
    actual_source = actual["_source"]["includes"]
    actual["_source"] = []
    assert actual == {
        "query": {
            "bool": {
                "filter": [
                    {"term": {"permissions.Read.keyword": "GROUP_EVERYONE"}},
                    {"term": {"properties.cm:edu_metadataset.keyword": "mds_oeh"}},
                    {"term": {"nodeRef.storeRef.protocol": "workspace"}},
                    {"term": {"type": "ccm:io"}},
                    {
                        "bool": {
                            "must_not": [{"term": {"aspects": "ccm:io_childobject"}}]
                        }
                    },
                    {"term": {"content.mimetype.keyword": "text/plain"}},
                ],
                "should": [
                    {"match": {"collections.path": dummy_uuid}},
                    {"match": {"collections.nodeRef.id": dummy_uuid}},
                ],
                "minimum_should_match": 1,
                "must_not": [{"wildcard": {dummy_attribute: {"value": "*"}}}],
            }
        },
        "from": 0,
        "size": dummy_maximum_size,
        "_source": [],
    }
    expected_source = [
        "properties.cclom:general_keyword",
        "properties.ccm:taxonid",
        "properties.ccm:wwwurl",
        "nodeRef.id",
        "type",
        "properties.ccm:commonlicense_key",
        "properties.cclom:general_description",
        "properties.cm:name",
        "properties.cclom:title",
        "properties.ccm:educationalcontext",
        "properties.ccm:oeh_lrt",
        "properties.ccm:oeh_publisher_combined",
        "i18n.de_DE.ccm:educationalintendedenduserrole",
        "preview",
    ]
    assert sorted(actual_source) == sorted(expected_source)


def test_missing_materials_search_license():
    dummy_uuid = uuid.uuid4()
    dummy_attribute = "properties.ccm:commonlicense_key"
    dummy_missing_attribute = missing_attribute_filter[4].value
    dummy_maximum_size = 3
    search = missing_attributes_search(
        dummy_uuid, dummy_missing_attribute, dummy_maximum_size
    )
    actual = search.to_dict()
    actual["_source"] = []

    assert actual == {
        "query": {
            "bool": {
                "filter": [
                    {"term": {"permissions.Read.keyword": "GROUP_EVERYONE"}},
                    {"term": {"properties.cm:edu_metadataset.keyword": "mds_oeh"}},
                    {"term": {"nodeRef.storeRef.protocol": "workspace"}},
                    {"term": {"type": "ccm:io"}},
                    {
                        "bool": {
                            "must_not": [{"term": {"aspects": "ccm:io_childobject"}}]
                        }
                    },
                    {"term": {"content.mimetype.keyword": "text/plain"}},
                    {
                        "bool": {
                            "should": [
                                {
                                    "terms": {
                                        dummy_attribute
                                        + ".keyword": [
                                            "UNTERRICHTS_UND_LEHRMEDIEN",
                                            "NONE",
                                            "",
                                        ]
                                    }
                                },
                                {
                                    "bool": {
                                        "must_not": [
                                            {"exists": {"field": dummy_attribute}}
                                        ]
                                    }
                                },
                            ],
                            "minimum_should_match": 1,
                        }
                    },
                ],
                "should": [
                    {"match": {"collections.path": dummy_uuid}},
                    {"match": {"collections.nodeRef.id": dummy_uuid}},
                ],
                "minimum_should_match": 1,
            }
        },
        "from": 0,
        "size": dummy_maximum_size,
        "_source": [],
    }
