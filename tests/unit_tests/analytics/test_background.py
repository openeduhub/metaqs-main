from app.api.analytics.background_task import search_query
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
