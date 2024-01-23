import uuid

import pytest

from app.api.collections.collection_validation import collection_validation
from app.core.constants import COLLECTION_NAME_TO_ID
from tests.conftest import elastic_search_mock


@pytest.mark.asyncio
async def test_collection_validation():
    biology = uuid.UUID(COLLECTION_NAME_TO_ID["Biologie"])
    with elastic_search_mock("collection-validation"):
        result = collection_validation(collection_id=biology)

    assert len(result) == 82
    assert all(r.title == [] for r in result), "Contradiction with response which indicated no missing titles"
    assert all(
        r.description == [] for r in result
    ), "Contradiction with response which indicated no missing descriptions"
    assert all(r.keywords == [] for r in result), "Contradiction with response which indicated no missing keywords"
    assert all(r.description == [] for r in result)
