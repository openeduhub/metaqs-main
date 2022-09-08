import uuid

import pytest

from app.api.collections.pending_materials import (
    get_pending_materials,
)
from app.core.constants import COLLECTION_NAME_TO_ID
from app.elastic.attributes import ElasticResourceAttribute
from tests.conftest import elastic_search_mock


@pytest.mark.asyncio
async def test_pending_materials_description():
    biologie = uuid.UUID(COLLECTION_NAME_TO_ID["Biologie"])

    with elastic_search_mock("pending-materials-description"):
        materials = await get_pending_materials(
            collection_id=biologie,
            missing=ElasticResourceAttribute.DESCRIPTION,
        )

    assert all(
        mat.description is None for mat in materials
    ), "material has a description for a query that should only return materials with missing descriptions"
    assert len(materials) == 11, "some of the response hits were dropped"


@pytest.mark.asyncio
async def test_pending_materials_license():
    biologie = uuid.UUID(COLLECTION_NAME_TO_ID["Biologie"])

    with elastic_search_mock("pending-materials-license"):
        materials = await get_pending_materials(
            collection_id=biologie,
            missing=ElasticResourceAttribute.LICENSES,
        )

    assert all(
        mat.licenses is None for mat in materials
    ), "material has a description for a query that should only return materials with missing license"
    assert len(materials) == 4, "some of the response hits were dropped"
