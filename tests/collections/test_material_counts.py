import uuid

import pytest

from app.api.collections.material_counts import (
    material_counts,
    MaterialCounts,
)
from app.api.collections.tree import tree
from app.core.constants import COLLECTION_NAME_TO_ID
from tests.conftest import elastic_search_mock


@pytest.mark.asyncio
async def test_get_material_counts():
    biology = uuid.UUID(COLLECTION_NAME_TO_ID["Biologie"])
    with elastic_search_mock(resource="tree"):
        collection = tree(node_id=biology)
    with elastic_search_mock(resource="material-counts"):
        result = await material_counts(collection=collection)

    counts_by_id = {item.node_id: item for item in result}

    assert all(
        node.node_id in counts_by_id for node in collection.flatten(root=True)
    ), "count result does not contain counts for all nodes of the collection tree"

    expected = [
        MaterialCounts(
            node_id=uuid.UUID("2e674483-0eae-4088-b51a-c4f4bbf86bcc"),
            title="Evolution",
            materials_count=0,
        ),
        MaterialCounts(
            node_id=uuid.UUID("220f48a8-4b53-4179-919d-7cd238ed567e"),
            title="Chemische Grundlagen",
            materials_count=5,
        ),
        MaterialCounts(
            node_id=uuid.UUID("15fce411-54d9-467f-8f35-61ea374a298d"),
            title="Biologie",
            materials_count=8,
        ),
        MaterialCounts(
            node_id=uuid.UUID("a5ce08a9-1e78-4028-bf5e-9205f598f11a"),
            title="Wasser - Grundstoff des Lebens",
            materials_count=10,
        ),
        MaterialCounts(
            node_id=uuid.UUID("81445550-fcc4-4f9e-99af-652dda269175"),
            title="Luft und Atmosphäre",
            materials_count=15,
        ),
    ]

    assert result == expected
