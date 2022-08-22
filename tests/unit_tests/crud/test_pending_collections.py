import uuid

import pytest

from app.api.collections.pending_collections import (
    search_collections_with_missing_attributes,
)
from app.core.constants import COLLECTION_NAME_TO_ID
from app.core.models import ElasticResourceAttribute
from tests.conftest import elastic_search_mock


@pytest.mark.asyncio
async def test_search_collections_with_missing_attributes():
    collection_id = uuid.UUID(COLLECTION_NAME_TO_ID["Chemie"])

    with elastic_search_mock("collections-with-missing-attributes"):
        collections = await search_collections_with_missing_attributes(
            collection_id=collection_id,
            missing=ElasticResourceAttribute.COLLECTION_DESCRIPTION,
        )

    assert all(collection.description is None for collection in collections)
    assert len(collections) == 8
