import json
import uuid
from unittest import mock
from unittest.mock import MagicMock

from app.api.analytics.background_task import (
    build_pending_materials,
    pending_materials_search,
    search_query,
    update_values_with_pending_materials,
)
from app.api.analytics.stats import Row
from app.api.analytics.storage import PendingMaterials
from app.core.models import essential_frontend_properties
from app.elastic.elastic import ResourceType


def test_search_query_collections():
    query = search_query(resource_type=ResourceType.COLLECTION, path="path")
    query_dict = query.to_dict()

    assert (
        len(query_dict["_source"]["includes"]) == 11
    )  # length of essential properties plus 2
    assert query_dict["_source"]["includes"] == [
        "nodeRef.*",
        "path",
        *essential_frontend_properties,
    ]
    query_dict["_source"] = {}
    assert query_dict == {
        "_source": {},
        "query": {
            "bool": {
                "filter": [
                    {"term": {"permissions.Read.keyword": "GROUP_EVERYONE"}},
                    {"term": {"properties.cm:edu_metadataset.keyword": "mds_oeh"}},
                    {"term": {"nodeRef.storeRef.protocol": "workspace"}},
                    {"term": {"type": "ccm:map"}},
                    {"term": {"path": "5e40e372-735c-4b17-bbf7-e827a5702b57"}},
                ]
            }
        },
    }


def test_search_query_materials():
    query = search_query(
        resource_type=ResourceType.MATERIAL, path="collections.nodeRef.id"
    )
    query_dict = query.to_dict()

    assert (
        len(query_dict["_source"]["includes"]) == 11
    )  # length of essential properties plus 2
    assert query_dict["_source"]["includes"] == [
        "nodeRef.*",
        "collections.nodeRef.id",
        *essential_frontend_properties,
    ]
    query_dict["_source"] = {}
    assert query_dict == {
        "_source": {},
        "query": {
            "bool": {
                "filter": [
                    {"term": {"permissions.Read.keyword": "GROUP_EVERYONE"}},
                    {"term": {"properties.cm:edu_metadataset.keyword": "mds_oeh"}},
                    {"term": {"nodeRef.storeRef.protocol": "workspace"}},
                    {"term": {"type": "ccm:io"}},
                    {
                        "term": {
                            "collections.path.keyword": "5e40e372-735c-4b17-bbf7-e827a5702b57"
                        }
                    },
                ]
            }
        },
    }


def test_pending_materials_search():
    dummy_uuid = uuid.uuid4()
    search = pending_materials_search(dummy_uuid)
    expected = {
        "_source": {},
        "from": 0,
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
                    {
                        "bool": {
                            "minimum_should_match": 1,
                            "should": [
                                {
                                    "bool": {
                                        "must_not": [
                                            {
                                                "wildcard": {
                                                    "properties.cclom:title": {
                                                        "value": "*"
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                },
                                {
                                    "bool": {
                                        "must_not": [
                                            {
                                                "wildcard": {
                                                    "properties.ccm:oeh_lrt": {
                                                        "value": "*"
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                },
                                {
                                    "bool": {
                                        "must_not": [
                                            {
                                                "wildcard": {
                                                    "properties.ccm:taxonid": {
                                                        "value": "*"
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                },
                                {
                                    "bool": {
                                        "must_not": [
                                            {
                                                "wildcard": {
                                                    "properties.ccm:wwwurl": {
                                                        "value": "*"
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                },
                                {
                                    "bool": {
                                        "minimum_should_match": 1,
                                        "should": [
                                            {
                                                "terms": {
                                                    "properties.ccm:commonlicense_key.keyword": [
                                                        "UNTERRICHTS_UND_LEHRMEDIEN",
                                                        "NONE",
                                                        "",
                                                    ]
                                                }
                                            },
                                            {
                                                "bool": {
                                                    "must_not": [
                                                        {
                                                            "exists": {
                                                                "field": "properties.ccm:commonlicense_key"
                                                            }
                                                        }
                                                    ]
                                                }
                                            },
                                        ],
                                    }
                                },
                                {
                                    "bool": {
                                        "must_not": [
                                            {
                                                "wildcard": {
                                                    "properties.ccm:oeh_publisher_combined": {
                                                        "value": "*"
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                },
                                {
                                    "bool": {
                                        "must_not": [
                                            {
                                                "wildcard": {
                                                    "properties.cclom:general_description": {
                                                        "value": "*"
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                },
                                {
                                    "bool": {
                                        "must_not": [
                                            {
                                                "wildcard": {
                                                    "i18n.de_DE.ccm:educationalintendedenduserrole": {
                                                        "value": "*"
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                },
                                {
                                    "bool": {
                                        "must_not": [
                                            {
                                                "wildcard": {
                                                    "properties.ccm:educationalcontext": {
                                                        "value": "*"
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                },
                            ],
                        }
                    },
                ],
                "minimum_should_match": 1,
                "should": [
                    {"match": {"collections.path.keyword": dummy_uuid}},
                    {"match": {"collections.nodeRef.id.keyword": dummy_uuid}},
                ],
            }
        },
        "size": 500000,
    }
    response = search.to_dict()
    actual_source = response["_source"]
    response["_source"] = {}
    assert response == expected

    expected_source = {
        "includes": [
            "nodeRef.id",
            "properties.ccm:taxonid",
            "properties.cclom:general_description",
            "properties.cm:name",
            "properties.ccm:educationalcontext",
            "properties.ccm:wwwurl",
            "i18n.de_DE.ccm:educationalintendedenduserrole",
            "properties.cclom:general_keyword",
            "properties.ccm:oeh_lrt",
            "preview",
            "type",
            "properties.ccm:oeh_publisher_combined",
            "properties.ccm:commonlicense_key",
            "properties.cclom:title",
        ]
    }

    assert sorted(actual_source) == sorted(expected_source)


def test_update_values_with_pending_materials():
    dummy_uuid = uuid.uuid4()
    node_ref_dictionary: dict = {"nodeRef": {"id": str(dummy_uuid)}}
    assert update_values_with_pending_materials("", node_ref_dictionary) == dummy_uuid

    data = node_ref_dictionary.copy()
    data.update({"properties": {}})
    assert update_values_with_pending_materials("", data) == dummy_uuid

    data = node_ref_dictionary.copy()
    data.update({"properties": {"dummy_attribute": []}})
    assert (
        update_values_with_pending_materials("properties.dummy_attribute", data) is None
    )

    data = node_ref_dictionary.copy()
    data.update({"i18n": {}})
    end_user_role_attribute = "i18n.de_DE.ccm:educationalintendedenduserrole"
    assert (
        update_values_with_pending_materials(end_user_role_attribute, data)
        == dummy_uuid
    )

    data = node_ref_dictionary.copy()
    data.update({"i18n": {"de_DE": {}}})
    end_user_role_attribute = "i18n.de_DE.ccm:educationalintendedenduserrole"
    assert (
        update_values_with_pending_materials(end_user_role_attribute, data)
        == dummy_uuid
    )

    data = node_ref_dictionary.copy()
    end_user_role_attribute = "i18n.de_DE.ccm:educationalintendedenduserrole"
    data.update({"i18n": {"de_DE": {"ccm:educationalintendedenduserrole": []}}})
    assert update_values_with_pending_materials(end_user_role_attribute, data) is None


def test_build_pending_materials():
    collection_id = uuid.UUID("2fbc1287-b67e-43d0-a3e5-370b22dc3c8c")
    collection = Row(title="dummy_row", id=collection_id)

    directory = "tests/unit_tests/resources"
    with open(f"{directory}/test_background.json") as file:
        global_response = json.load(file)

    data = []
    for entry in global_response["hits"]:
        mocked_data = MagicMock()
        mocked_data.to_dict.return_value = entry
        data.append(mocked_data)

    with mock.patch(
        "app.api.analytics.background_task.pending_materials_search"
    ) as mocked_search:
        mocked_search().execute().hits = data
        response = build_pending_materials(collection)
    assert response == PendingMaterials(
        collection_id=collection_id,
        description=[],
        edu_context=[],
        intended_end_user_role=[
            uuid.UUID("2eafdfa7-e50b-4cf2-8ea3-22f0b8384b87"),
            uuid.UUID("e7f72160-95b5-47b4-8a9e-34087119058d"),
        ],
        learning_resource_type=[],
        license=[],
        publisher=[
            uuid.UUID("2eafdfa7-e50b-4cf2-8ea3-22f0b8384b87"),
            uuid.UUID("e7f72160-95b5-47b4-8a9e-34087119058d"),
        ],
        taxon_id=[],
        title=[],
        url=[
            uuid.UUID("2eafdfa7-e50b-4cf2-8ea3-22f0b8384b87"),
            uuid.UUID("e7f72160-95b5-47b4-8a9e-34087119058d"),
        ],
    )
