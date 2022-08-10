import asyncio
import uuid

import pytest

from app.api.analytics.background_task import build_pending_materials
from app.api.analytics.stats import Row, get_ids_to_iterate
from app.api.analytics.storage import PendingMaterials
from app.api.collections.missing_materials import (
    MissingAttributeFilter,
    MissingMaterialField,
    search_materials_with_missing_attributes,
)
from app.core.config import ELASTICSEARCH_URL
from app.core.models import ElasticResourceAttribute
from app.elastic.utils import connect_to_elastic


@pytest.mark.asyncio
@pytest.mark.skipif(
    condition=ELASTICSEARCH_URL is None, reason="No connection to Elasticsearch"
)
async def test_integration_materials_with_missing_publisher():
    await connect_to_elastic()

    chemistry_id = uuid.UUID("4940d5da-9b21-4ec0-8824-d16e0409e629")
    attribute = MissingAttributeFilter(
        attr=MissingMaterialField(ElasticResourceAttribute.PUBLISHER.path)
    )

    # pending materials widget
    response = await search_materials_with_missing_attributes(chemistry_id, attribute)
    assert response != []

    found_uuids = []
    for entry in response:
        found_uuids.append(entry.node_id)

    # background task
    sub_collections: list[Row] = await get_ids_to_iterate(node_id=chemistry_id)

    materials = [
        PendingMaterials(**build_pending_materials(collection))
        for collection in sub_collections
    ]

    found_background_uuids = []
    for entry in materials:
        found_background_uuids.append(entry.collection_id)
    print(len(found_uuids))
    print(len(found_background_uuids))

    assert len(found_uuids) == 962
    assert len(found_background_uuids) == 185

    unfound = []
    for entry in found_background_uuids:
        if entry not in found_uuids:
            unfound.append(entry)

    assert unfound == []

    assert len(found_uuids) == len(found_background_uuids)
