import contextlib
import os.path
from pathlib import Path
from uuid import UUID
from unittest import mock

from app.api.analytics.analytics import PendingMaterials
from app.api.analytics.background_task import (
    build_pending_materials,
    search_query,
)
from app.core.constants import COLLECTION_NAME_TO_ID
from app.core.models import essential_frontend_properties
from app.elastic.elastic import ResourceType


@contextlib.contextmanager
def elastic_search_mock(resource: str):
    """
    Mock the execute call of the elasticsearch-dsl Search class package.
    fixme: write docstring.
    """
    import json

    resource_path = Path(__file__).parent / ".." / ".." / "resources"

    # request is optional. if no request is provided, the search will simply
    # be mocked to return the respective response.
    if os.path.exists(resource_path / f"{resource}-request.json"):
        with open(resource_path / f"{resource}-request.json", "r") as request:
            request = json.load(request)
    else:
        request = None

    with open(resource_path / f"{resource}-response.json", "r") as response:
        response = json.load(response)

    def execute_mock(self, ignore_cache=False):  # noqa
        assert (
            request is not None and self.to_dict() == request
        ), "Executed request did not match expected request"
        # just use the dictionary deserialized from the resource file and pass it through the original
        # elasticsearch_dsl machinery. I.e. search.execute() should behave __exactly__ as if the result was
        # received via a http call.
        self._response = self._response_class(self, response)
        return self._response

    with mock.patch("elasticsearch_dsl.search.Search.execute", execute_mock):
        yield


def test_build_pending_materials():
    chemie = UUID(COLLECTION_NAME_TO_ID["Chemie"])

    with elastic_search_mock(resource="build-pending-material"):
        response = build_pending_materials(collection_id=chemie, title="Chemie")

    assert response == PendingMaterials(
        collection_id=chemie,
        # 'Materialien ohne Beschreibungstext'
        description=[UUID("6cc8e664-1bd6-4b75-838c-b4091f96676e")],
        # 'Materialien ohne Bildungsstufe'
        edu_context=[UUID("4ac9e3a1-04b7-44fc-ac6f-94c116eb4b6b")],
        # 'Materialien ohne Zielgruppe'
        intended_end_user_role=[
            UUID("6cc8e664-1bd6-4b75-838c-b4091f96676e"),
            UUID("dd0b4df4-dff2-4519-a018-401c062d2192"),
        ],
        # 'Materialien ohne Kategorie',
        learning_resource_type=[UUID("dd0b4df4-dff2-4519-a018-401c062d2192")],
        # 'Materialien ohne Lizenz'
        license=[UUID("dd0b4df4-dff2-4519-a018-401c062d2192")],
        # 'Materialien ohne Herkunft'
        publisher=[UUID("4ac9e3a1-04b7-44fc-ac6f-94c116eb4b6b")],
        # 'Materialien ohne Fachgebiet'
        taxon_id=[],
        # 'Materialien ohne Titel'
        title=[],
        url=[],  # not used -> empty
    )


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
