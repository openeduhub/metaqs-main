import uuid

from elasticsearch_dsl import AttrDict
from glom import glom

from app.api.collections.missing_attributes import (
    missing_attribute_filter,
    missing_attributes_search,
    missing_attributes_spec,
)
from app.api.collections.models import MissingMaterials


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


def test_missing_attributes_spec():
    parent_ref = uuid.uuid4()
    node_ref = uuid.uuid4()
    entry = {
        "path": [
            "00abdb05-6c96-4604-831c-b9846eae7d2d",
            "c73dd8be-e520-42bb-b6f1-f989714d09fc",
            "d1afbeaa-1d20-4d1d-a1aa-8d8903edff38",
            "3305f552-c931-4bcc-842b-939c99752bd5",
            "ef7e295e-d931-49eb-b1e2-76475f849e8a",
            "572c19f6-37df-4090-a116-cc93b648785d",
            "7050d184-db61-4e4b-86a0-74f35604a7da",
            "7dfccbf5-191f-4856-849a-0e6c11ff1a8d",
            "4156d4d0-79ec-4606-aab3-0133f0602561",
            "35054614-72c8-49b2-9924-7b04c7f3bf71",
            "5e40e372-735c-4b17-bbf7-e827a5702b57",
            "742d8c87-e5a3-4658-86f9-419c2cea6574",
            "db536584-55dc-4645-bc85-6ebe30c653b7",
            "38c0c48e-f74f-45a5-9b11-e5d7dce526b3",
        ],
        "nodeRef": {"id": node_ref},
        "type": "ccm:map",
        "properties": {
            "cm:title": "HTML",
            "cm:name": "HTML",
            "cclom:general_keyword": [""],
            "cm:description": "",
        },
        "parentRef": {"id": parent_ref},
    }

    mocked_response = [AttrDict(entry)]
    result = [MissingMaterials(**glom(hit.to_dict(), missing_attributes_spec)) for hit in mocked_response]

    assert len(result) == 1
    assert len(result[0].children) == 0
    assert result[0].description == ""
    assert result[0].parent_id == parent_ref
    assert result[0].noderef_id == node_ref
