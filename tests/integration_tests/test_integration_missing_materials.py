import uuid

import pytest

from app.api.analytics.background_task import build_pending_materials
from app.api.analytics.stats import Row
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
async def test_integration_materials_with_missing_attributes():
    """
    Here we test whether material-validation and pending-materials yield the same result for the same collection id.
    The first is more detailed than the second, but must yield the same result.

    :return:
    """
    await connect_to_elastic()

    chemistry_id = uuid.UUID("4940d5da-9b21-4ec0-8824-d16e0409e629")

    for missing_attribute in [
        ElasticResourceAttribute.LICENSES.path,
        ElasticResourceAttribute.PUBLISHER.path,
    ]:
        attribute = MissingAttributeFilter(attr=MissingMaterialField(missing_attribute))

        # pending materials
        response = await search_materials_with_missing_attributes(
            chemistry_id, attribute
        )
        assert response != []

        found_uuids = []
        for entry in response:
            found_uuids.append(entry.node_id)

        # material-validation
        row = Row(
            id=chemistry_id,
            title="chemistry",
        )
        materials = build_pending_materials(row)

        if missing_attribute == ElasticResourceAttribute.PUBLISHER.path:
            found_background_uuids = materials.publisher
        else:
            found_background_uuids = materials.license

        assert len(found_uuids) == len(found_background_uuids)

        # TODO: If this runs, Revert TODO Revert in background_task
        assert False
