import uuid

import pytest

from app.api.collections.pending_collections import (
    get_pending_collections,
)
from app.core.constants import COLLECTION_NAME_TO_ID
from app.elastic.attributes import ElasticResourceAttribute
from tests.conftest import elastic_search_mock


@pytest.mark.asyncio
async def test_pending_collections():
    collection_id = uuid.UUID(COLLECTION_NAME_TO_ID["Chemie"])

    with elastic_search_mock("pending-collections"):
        collections = await get_pending_collections(
            collection_id=collection_id,
            missing=ElasticResourceAttribute.COLLECTION_DESCRIPTION,
        )

    assert all(collection.description is None for collection in collections)
    assert len(collections) == 8
