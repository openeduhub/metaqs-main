import asyncio
import json
import uuid
from unittest import mock
from unittest.mock import MagicMock

import pytest

from app.api.collections.tree import collection_tree, parsed_tree


def node_count_dict(data: list):
    return sum(
        node_count_dict(collection["children"])
        if "children" in collection.keys() and collection["children"]
        else 1
        for collection in data
    )


def test_tree():
    with open("unit_tests/tree_prod_response.json") as file:
        prod = json.loads("".join(file.readlines()))
    with open("unit_tests/tree_dev_response.json") as file:
        dev = json.loads("".join(file.readlines()))
    assert len(prod) == 30
    assert len(dev) == 26
    assert node_count_dict(prod) == 2898
    assert node_count_dict(dev) == 2219


def node_count(data: list):
    return sum(
        node_count(collection.children) if collection.children else 1
        for collection in data
    )


@pytest.mark.asyncio
async def test_collection_tree():
    root_node_id = "5e40e372-735c-4b17-bbf7-e827a5702b57"
    data = await collection_tree(root_node_id)
    assert len(data) == 26
    count = node_count(data)
    assert count == 2219


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

        data = await parsed_tree(mocked_client, root_node_id)
        assert len(data) == 0
