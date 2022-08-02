from app.api.analytics.background_task import search_query
from app.core.models import required_collection_properties
from app.elastic.elastic import ResourceType, query_many


def test_search_query_collections():
    query = search_query(
        lambda node_id: query_many(ResourceType.COLLECTION, node_id), "path"
    )
    query_dict = query.to_dict()

    assert len(query_dict["_source"]["includes"]) == 63
    assert query_dict["_source"]["includes"] == [
        "nodeRef.*",
        "path",
        *list(required_collection_properties.keys()),
    ]
    query_dict["_source"] = {}
    assert query_dict == {
        "_source": {},
        "query": {
            "bool": {
                "filter": [
                    {"term": {"type": "ccm:map"}},
                    {"term": {"path": "5e40e372-735c-4b17-bbf7-e827a5702b57"}},
                ]
            }
        },
    }


def test_search_query_materials():
    query = search_query(
        lambda node_id: query_many(ResourceType.MATERIAL, node_id),
        "collections.nodeRef.id",
    )
    query_dict = query.to_dict()

    assert len(query_dict["_source"]["includes"]) == 63
    assert query_dict["_source"]["includes"] == [
        "nodeRef.*",
        "collections.nodeRef.id",
        *list(required_collection_properties.keys()),
    ]
    query_dict["_source"] = {}
    assert query_dict == {
        "_source": {},
        "query": {
            "bool": {
                "filter": [
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
