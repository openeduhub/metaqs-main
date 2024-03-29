import uuid

import pytest
from aiohttp import ClientSession

from app.api.collections.tree import Tree
from app.api.collections.tree import tree as load_tree
from app.core.vocabs import tree_from_vocabs
from tests.conftest import elastic_search_mock


@pytest.mark.asyncio
async def test_collection_tree_vocabs():
    root_node_id = uuid.UUID("5e40e372-735c-4b17-bbf7-e827a5702b57")
    async with ClientSession() as session:
        data = await tree_from_vocabs(session, root_node_id)
    assert len(data) == 27
    count = sum(len(list(collection.flatten())) for collection in data)
    assert count >= 2200  # adapt this number to the current state, may change regularly


def test_tree_from_elastic():
    node_id_biology = uuid.UUID("15fce411-54d9-467f-8f35-61ea374a298d")
    with elastic_search_mock("tree"):
        tree = load_tree(node_id_biology)

    expected = Tree(
        node_id=node_id_biology,
        title="Biologie",
        parent_id=None,
        level=0,
        children=[
            Tree(
                node_id=uuid.UUID("220f48a8-4b53-4179-919d-7cd238ed567e"),
                title="Chemische Grundlagen",
                parent_id=node_id_biology,
                level=1,
                children=[
                    Tree(
                        node_id=uuid.UUID("81445550-fcc4-4f9e-99af-652dda269175"),
                        title="Luft und Atmosphäre",
                        parent_id=uuid.UUID("220f48a8-4b53-4179-919d-7cd238ed567e"),
                        level=2,
                        children=[],
                    ),
                    Tree(
                        node_id=uuid.UUID("a5ce08a9-1e78-4028-bf5e-9205f598f11a"),
                        title="Wasser - Grundstoff des Lebens",
                        parent_id=uuid.UUID("220f48a8-4b53-4179-919d-7cd238ed567e"),
                        level=2,
                        children=[],
                    ),
                ],
            ),
            Tree(
                node_id=uuid.UUID("2e674483-0eae-4088-b51a-c4f4bbf86bcc"),
                title="Evolution",
                parent_id=node_id_biology,
                level=1,
                children=[],
            ),
        ],
    )
    assert tree == expected
