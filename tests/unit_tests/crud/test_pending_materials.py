import uuid

import pytest

from app.api.collections.pending_materials import (
    search_materials_with_missing_attributes,
)
from app.core.constants import COLLECTION_NAME_TO_ID
from app.core.models import ElasticResourceAttribute
from tests.conftest import elastic_search_mock


@pytest.mark.asyncio
async def test_search_materials_with_missing_description():
    biologie = uuid.UUID(COLLECTION_NAME_TO_ID["Biologie"])

    with elastic_search_mock("materials-with-missing-attributes-description"):
        materials = await search_materials_with_missing_attributes(
            collection_id=biologie,
            missing=ElasticResourceAttribute.DESCRIPTION,
        )

    assert all(
        mat.description is None for mat in materials
    ), "material has a description for a query that should only return materials with missing descriptions"
    assert len(materials) == 11, "some of the response hits were dropped"


@pytest.mark.asyncio
async def test_search_materials_with_missing_license():
    biologie = uuid.UUID(COLLECTION_NAME_TO_ID["Biologie"])

    with elastic_search_mock("materials-with-missing-attributes-license"):
        materials = await search_materials_with_missing_attributes(
            collection_id=biologie,
            missing=ElasticResourceAttribute.LICENSES,
        )

    assert all(
        mat.licenses is None for mat in materials
    ), "material has a description for a query that should only return materials with missing license"
    assert len(materials) == 4, "some of the response hits were dropped"
