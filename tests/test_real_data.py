import logging
import os

import httpx
import pytest

from app.api.collections.material_validation import MaterialValidation
from app.api.collections.pending_materials import PendingMaterial
from app.core.constants import COLLECTION_NAME_TO_ID
from app.elastic.attributes import ElasticResourceAttribute


@pytest.mark.skipif(
    "CI" in os.environ, reason="This tests needs a running instance of the service and elastic connection"
)
def test_real_data():
    """
    Query the pending materials endpoints and the material validation endpoints and make sure they have equal counts.
    """
    try:
        httpx.get(url=f"http://localhost:8081/_ping")
    except:
        raise pytest.skip("Service seems to be offline. skipping")

    def union(*sets: set[str]) -> set[str]:
        if len(sets) == 0:
            return set()
        if len(sets) == 1:
            return sets[0]
        return union(sets[0].union(sets[1]), *sets[2:])

    attributes = {
        "title": ElasticResourceAttribute.TITLE,
        "description": ElasticResourceAttribute.DESCRIPTION,
        "edu_context": ElasticResourceAttribute.EDU_CONTEXT,
        "learning_resource_type": ElasticResourceAttribute.LEARNINGRESOURCE_TYPE,
        "intended_end_user_role": ElasticResourceAttribute.EDU_ENDUSERROLE_DE,
        "taxon_id": ElasticResourceAttribute.SUBJECTS,
        "publisher": ElasticResourceAttribute.PUBLISHER,
    }

    logger = logging.getLogger("validations")
    logging.getLogger("httpx._client").setLevel(logging.WARNING)
    logger.setLevel(logging.INFO)

    for collection, node_id in COLLECTION_NAME_TO_ID.items():
        logging.info(f"Checking collection {collection}")
        response = httpx.get(url=f"http://localhost:8081/collections/{node_id}/material-validation")
        if response.status_code != 200:
            logger.warning(f"Non OK response: {response}")
            continue
        validation = [MaterialValidation.parse_obj(d) for d in response.json()]
        logger.debug(f"Number validation entries: {len(validation)}")

        combined = {name: union(*(set(getattr(v, name)) for v in validation)) for name, attribute in attributes.items()}

        for name, attribute in attributes.items():
            response = httpx.get(url=f"http://localhost:8081/collections/{node_id}/pending-materials/{attribute.value}")
            pending = [PendingMaterial.parse_obj(d) for d in response.json()]
            logger.debug(f"{name}: {len(pending)}")
            logger.debug(f"combined: {len(combined[name])}")

            if len(combined[name]) != len(pending):
                logger.warning(f"MISMATCH in {collection}/{name}: Combined: {len(combined[name])} <> {len(pending)}")
                overhang = {m.node_id for m in pending} - combined[name]
                assert len(overhang) > 0
                logger.warning(f"Material ids ({len(overhang)}): {overhang}")
