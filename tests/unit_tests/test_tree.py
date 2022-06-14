import asyncio
import json
import uuid
from unittest import mock
from unittest.mock import MagicMock

import pytest
from elasticsearch_dsl.response import Response

from app.api.collections.models import CollectionNode
from app.api.collections.tree import (
    build_portal_tree,
    collection_tree,
    tree_from_elastic,
    tree_search,
)
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

    query = tree_search(node_id_biology)
    expected_search = {
        "_source": [
            "nodeRef.id",
            "properties.cm:title",
            "collections.path",
            "parentRef.id",
        ],
        "from": 0,
        "query": {
            "bool": {
                "filter": [
                    {"term": {"permissions.Read.keyword": "GROUP_EVERYONE"}},
                    {"term": {"properties.cm:edu_metadataset.keyword": "mds_oeh"}},
                    {"term": {"nodeRef.storeRef.protocol": "workspace"}},
                    {"term": {"path": node_id_biology}},
                ],
            }
        },
        "size": 500000,
        "sort": ["fullpath"],
    }

    assert query.to_dict() == expected_search

    directory = "tests/unit_tests/resources"

    with open(f"{directory}/test_tree.json") as file:
        expected_tree = json.load(file)
    with open(f"{directory}/test_tree_response.json") as file:
        response = [hit["_source"] for hit in json.load(file)]

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

    def tree_to_json(_tree: list[CollectionNode]) -> list:
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

    def flatten_list(list_of_lists):
        flat_list = []
        for item in list_of_lists:
            if type(item) == list:
                flat_list += flatten_list(item)
            else:
                flat_list.append(str(item))

        return flat_list

    def nodes(data: list) -> list:
        return [
            nodes(collection["children"])
            if collection["children"]
            else collection["noderef_id"]
            for collection in data
        ]

    parsed_and_expected_tree_contain_the_same_node_ids = (
        flatten_list(nodes(json_tree)).sort()
        == flatten_list(nodes(expected_tree)).sort()
    )
    assert parsed_and_expected_tree_contain_the_same_node_ids

    has_tree_expected_length = len(flatten_list(nodes(json_tree))) == 3
    assert has_tree_expected_length


def test_build_portal_tree():
    dummy_uuid = uuid.uuid4()

    # empty collections case
    empty_input = []
    result = build_portal_tree(empty_input, dummy_uuid)
    assert result == empty_input

    # single collection case with missing title
    dummy_child_uuid = uuid.uuid4()
    dummy_node = CollectionNode(
        title=None,
        noderef_id=dummy_child_uuid,
        children=[],
        parent_id=dummy_uuid,
    )
    result = build_portal_tree([dummy_node], dummy_uuid)
    assert result == []

    # single collection case
    dummy_child_uuid = uuid.uuid4()
    dummy_node = CollectionNode(
        title="dummy_node",
        noderef_id=dummy_child_uuid,
        children=[],
        parent_id=dummy_uuid,
    )
    result = build_portal_tree([dummy_node], dummy_uuid)
    dummy_node.parent_id = None
    assert result == [dummy_node]
    dummy_node.parent_id = dummy_uuid

    # single collection with single child collection case
    another_child_uuid = uuid.uuid4()
    another_node = CollectionNode(
        title="dummy_node",
        noderef_id=another_child_uuid,
        children=[],
        parent_id=dummy_child_uuid,
    )
    result = build_portal_tree([dummy_node, another_node], dummy_uuid)
    another_node.parent_id = None
    dummy_node.children = [another_node]
    dummy_node.parent_id = None
    assert result == [dummy_node]
