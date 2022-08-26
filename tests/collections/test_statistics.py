from uuid import UUID

import pytest

from app.api.collections.statistics import materials_by_collection_title, materials_by_collection_id
from app.api.collections.tree import Tree
from app.core.constants import COLLECTION_NAME_TO_ID
from tests.conftest import elastic_search_mock


@pytest.mark.asyncio
async def test_materials_by_collection_title():
    with elastic_search_mock(resource="materials-by-collection-title"):
        # fmt: off
        result: dict[UUID, dict[str, int]] = materials_by_collection_title(
            nodes=[
                Tree(
                    node_id=UUID(COLLECTION_NAME_TO_ID["Chemie"]), title="Chemie", children=[], parent_id=None, level=0
                ),
                Tree(
                    node_id=UUID(COLLECTION_NAME_TO_ID["Biologie"]), title="Biologie", children=[], parent_id=None, level=0
                ),
            ],
            oer_only=True,
        )
        # fmt: on
    assert len(result) == 2
    assert set(result.keys()) == {UUID(COLLECTION_NAME_TO_ID["Chemie"]), UUID(COLLECTION_NAME_TO_ID["Biologie"])}
    assert all(isinstance(value, dict) for value in result.values())


@pytest.mark.asyncio
async def test_materials_by_collection_id():
    with elastic_search_mock(resource="materials-by-collection-id"):
        result: dict[UUID, dict[str, int]] = materials_by_collection_id(
            collection_id=UUID(COLLECTION_NAME_TO_ID["Chemie"]),
            oer_only=True,
        )
    assert len(result) == 251
    assert UUID(COLLECTION_NAME_TO_ID["Chemie"]) in result
    assert all(isinstance(value, dict) for value in result.values())
