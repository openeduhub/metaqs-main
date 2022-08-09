import uuid

import pytest

from app.api.analytics.background_task import (
    pending_materials_search,
    search_query,
    uuids_of_materials_with_missing_attributes,
)
from app.api.analytics.stats import Row, get_ids_to_iterate
from app.core.config import ELASTICSEARCH_URL
from app.core.models import ElasticResourceAttribute, essential_frontend_properties
from app.elastic.elastic import ResourceType
from app.elastic.utils import connect_to_elastic


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


@pytest.mark.asyncio
@pytest.mark.skipif(
    condition=True or ELASTICSEARCH_URL is None, reason="No connection to Elasticsearch"
)
async def test_uuids_of_materials_with_missing_attributes_chemistry():
    await connect_to_elastic()

    chemistry = "4940d5da-9b21-4ec0-8824-d16e0409e629"
    attribute = ElasticResourceAttribute.WWW_URL
    response = uuids_of_materials_with_missing_attributes(chemistry, attribute)

    assert len(response) == 1


@pytest.mark.asyncio
@pytest.mark.skipif(
    condition=True or ELASTICSEARCH_URL is None, reason="No connection to Elasticsearch"
)
async def test_uuids_of_materials_with_missing_attributes_sub_collections():
    await connect_to_elastic()

    chemistry = "4940d5da-9b21-4ec0-8824-d16e0409e629"
    attribute = ElasticResourceAttribute.WWW_URL  # so far 35, but found 501
    # attribute = ElasticResourceAttribute.DESCRIPTION  # so far 57, but found 385ish
    # attribute = ElasticResourceAttribute.LICENSES  # so far 1, but 206

    expected = uuids_of_materials_with_missing_attributes(chemistry, attribute)
    assert len(expected) == len(set(expected)), "Found duplicate materials"
    assert len(expected) == 35, "Currently know value. replace ASAP"

    sub_collections: list[Row] = await get_ids_to_iterate(node_id=uuid.UUID(chemistry))

    seen = set()
    for collection in sub_collections:
        ids = uuids_of_materials_with_missing_attributes(collection.id, attribute)
        print(collection, ids)
        seen = seen.union(set(ids))

    print("seen")
    print(seen)
    assert len(seen) == len(expected)


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
                        "terms": {
                            "content.mimetype.keyword": [
                                "application/pdf",
                                "application/msword",
                                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                                "application/vnd.oasis.opendocument.text",
                                "text/html",
                                "application/vnd.ms-powerpoint",
                            ]
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
