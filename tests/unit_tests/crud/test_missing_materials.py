"""

import uuid

import pytest

from app.api.collections.missing_materials import (
    LearningMaterialAttribute,
    MissingAttributeFilter,
    MissingMaterialField,
)

# TODO: More tests cases to also enable filtering, see __call__ MissingAttributeFilter
@pytest.mark.skip(reason="Outdated")
def test_missing_materials_search():
    dummy_uuid = uuid.uuid4()
    attribute = LearningMaterialAttribute.KEYWORDS
    dummy_missing_attribute = MissingAttributeFilter(
        attr=MissingMaterialField[attribute.name]
    )
    dummy_maximum_size = 3
    search = missing_materials_search(
        dummy_uuid, dummy_missing_attribute, dummy_maximum_size
    )
    actual = search.to_dict()
    actual_source = actual["_source"]
    actual["_source"] = []
    assert actual == {
        "query": {
            "bool": {
                "filter": [
                    {"term": {"permissions.Read.keyword": "GROUP_EVERYONE"}},
                    {"term": {"properties.cm:edu_metadataset.keyword": "mds_oeh"}},
                    {"term": {"nodeRef.storeRef.protocol": "workspace"}},
                    {"term": {"type": "ccm:io"}},
                ],
                "should": [
                    {"match": {"collections.path": dummy_uuid}},
                    {"match": {"collections.nodeRef.id": dummy_uuid}},
                ],
                "minimum_should_match": 1,
                "must_not": [
                    {"wildcard": {dummy_missing_attribute.attr.value: {"value": "*"}}}
                ],
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
    ]

    actual_source.sort()
    expected_source.sort()
    source_contains_equal_elements = actual_source == expected_source
    assert source_contains_equal_elements

"""
