import asyncio
import json
import uuid
from unittest import mock
from unittest.mock import MagicMock

import pytest
from elasticsearch_dsl.response import Response

from app.api.collections.tree import collection_tree, tree_from_elastic, tree_query
from app.api.collections.vocabs import tree_from_vocabs


def node_count(data: list):
    return sum(
        node_count(collection.children) if collection.children else 1
        for collection in data
    )


@pytest.mark.asyncio
async def test_collection_tree():
    root_node_id = uuid.UUID("5e40e372-735c-4b17-bbf7-e827a5702b57")
    data = await collection_tree(root_node_id, use_vocabs=True)
    assert len(data) == 26
    count = node_count(data)
    assert count == 2216


@pytest.mark.asyncio
async def test_parsed_tree_empty_json():
    root_node_id = uuid.UUID("5e40e372-735c-4b17-bbf7-e827a5702b57")
    with mock.patch("app.api.collections.tree.ClientSession") as mocked_client:
        mocked_response = MagicMock()
        mocked_response.status = 200

        future = asyncio.Future()
        future.set_result({"hasTopConcept": []})
        mocked_response.json.return_value = future

        future = asyncio.Future()
        future.set_result(mocked_response)
        mocked_client.get.return_value = future

        data = await tree_from_vocabs(mocked_client, root_node_id)
        assert len(data) == 0


def test_parse_tree():
    node_id_biology = uuid.UUID("15fce411-54d9-467f-8f35-61ea374a298d")

    query = tree_query(node_id_biology)
    expected_query = {
        "_source": [
            "nodeRef.id",
            "properties.cm:title",
            "collections.path",
            "parentRef.id",
        ],
        "from": 0,
        "query": {
            "bool": {
                "filter": [{"term": {"path": node_id_biology}}],
                "must": [
                    {"match": {"permissions.Read": "GROUP_EVERYONE"}},
                    {"match": {"properties.cm:edu_metadataset": "mds_oeh"}},
                    {"match": {"nodeRef.storeRef.protocol": "workspace"}},
                ],
            }
        },
        "size": 500000,
        "sort": ["fullpath"],
    }

    assert query.to_dict() == expected_query

    with open("unit_tests/resources/test_tree.json") as file:
        expected_tree = json.loads("".join(file.readlines()))
    with open("unit_tests/resources/test_tree_response.json") as file:
        response = json.loads("".join(file.readlines()))
        response = [hit["_source"] for hit in response]

    with mock.patch("app.api.collections.tree.Search.execute") as mocked_execute:
        dummy_hits = {"hits": {"hits": response}}
        mocked_response = Response(
            search=query,
            response={"test": "hello", "aggregations": {}, "hits": dummy_hits},
        )
        mocked_response._d_ = dummy_hits
        mocked_response._hits = response
        mocked_response.success = MagicMock()
        mocked_response.success.return_value = True
        mocked_execute.return_value = mocked_response
        tree = tree_from_elastic(node_id_biology)

    def tree_to_json(_tree: dict) -> list:
        return [
            {
                "noderef_id": collection.noderef_id,
                "title": collection.title,
                "children": tree_to_json(collection.children)
                if collection.children
                else [],
            }
            for collection in _tree
        ]

    json_tree = tree_to_json(tree)

    assert len(json_tree) == len(expected_tree)

    def top_nodes(data: list) -> set:
        return {str(entry["noderef_id"]) for entry in data}

    assert top_nodes(json_tree) == top_nodes(expected_tree)
    assert json_tree == expected_tree
