import uuid

from fastapi_utils.tasks import repeat_every
from pydantic import BaseModel

from app.api.collections.tree import get_tree
from app.core.config import ELASTIC_TOTAL_SIZE, BACKGROUND_TASK_TIME_INTERVAL
from app.core.constants import COLLECTION_NAME_TO_ID
from app.core.logging import logger
from app.elastic.attributes import ElasticResourceAttribute
from app.elastic.search import MaterialSearch


class IncompleteMaterials(BaseModel):
    # title: 'Materialien ohne Titel',
    # learning_resource_type: 'Materialien ohne Kategorie',
    # taxon_id: 'Materialien ohne Fachgebiet',
    # license: 'Materialien ohne Lizenz',
    # publisher: 'Materialien ohne Herkunft',
    # description: 'Materialien ohne Beschreibungstext',
    # intended_end_user_role: 'Materialien ohne Zielgruppe',
    # edu_context: 'Materialien ohne Bildungsstufe',

    collection_id: uuid.UUID
    title: list[uuid.UUID]
    edu_context: list[uuid.UUID]
    url: list[uuid.UUID]
    description: list[uuid.UUID]
    license: list[uuid.UUID]
    learning_resource_type: list[uuid.UUID]
    taxon_id: list[uuid.UUID]
    publisher: list[uuid.UUID]
    intended_end_user_role: list[uuid.UUID]


class MaterialValidationResponse(BaseModel):
    collection_id: uuid.UUID
    missing_materials: list[IncompleteMaterials]


def _get_material_validation_single_collection(collection_id: uuid.UUID, title: str) -> IncompleteMaterials:
    """
    Build the stats object holding material count statistics for a singular collection.

    Note that this does not consider materials that are in any (nested-)child collection of the collection, the
    material has to be _exactly_ in the specified collection.
    """
    logger.info(f" - Analyzing collection: {title} ({collection_id})")

    # the field names and attributes which to check, note that the keys have to exactly match the field
    # names of the PendingMaterials struct.
    relevant_attributes = {
        "title": ElasticResourceAttribute.TITLE,
        "edu_context": ElasticResourceAttribute.EDU_CONTEXT,
        "description": ElasticResourceAttribute.DESCRIPTION,
        "license": ElasticResourceAttribute.LICENSES,
        "learning_resource_type": ElasticResourceAttribute.LEARNINGRESOURCE_TYPE,
        "taxon_id": ElasticResourceAttribute.SUBJECTS,
        "publisher": ElasticResourceAttribute.PUBLISHER,
        "intended_end_user_role": ElasticResourceAttribute.EDU_ENDUSERROLE_DE,
    }

    # to avoid looping through the results multiple times, we here initialize with empty lists
    materials = IncompleteMaterials(
        collection_id=collection_id,
        title=[],
        edu_context=[],
        url=[],
        description=[],
        license=[],
        learning_resource_type=[],
        taxon_id=[],
        publisher=[],
        intended_end_user_role=[],
    )

    # Don't do a transitive search: We only want the materials that are exactly in this collection
    # also the constructed search will return materials for which any of the attributes is missing.
    search = (
        MaterialSearch()
        .collection_filter(collection_id=collection_id, transitive=False)
        .non_series_objects_filter()
        .missing_attribute_filter(**relevant_attributes)
        .extra(size=ELASTIC_TOTAL_SIZE, from_=0)
        .source(includes=["nodeRef.id"])
    )

    hits = search.execute().hits

    # now we loop over the results a single time and append to the respective list where appropriate
    for hit in hits:
        node_id = uuid.UUID(hit["nodeRef"]["id"])

        assert (
            len(hit.meta.matched_queries) > 0
        ), f"Found 'matched_queries' of length 0 which should never happen. nodeRef.id: {node_id}"

        for match in hit.meta.matched_queries:
            # we need to strip the "missing_" prefix from the matched query name :-/
            getattr(materials, match).append(node_id)

    return materials


def get_material_validation(collection_id: uuid.UUID) -> MaterialValidationResponse:
    """
    Build the response for the /material-validation endpoint.

    :param collection_id: The id of top level collection
    """

    tree = get_tree(node_id=collection_id)
    logger.info(f"Working on {tree.title} ({collection_id})")
    children = tree.flatten(root=False)

    return MaterialValidationResponse(
        collection_id=collection_id,
        missing_materials=[
            # fixme: we need to include the top level node here because we use a really inadequate data model...
            #        and it needs to be included, because there could be materials that are only in the top level
            #        collection and those materials would otherwise not be included anywhere.
            _get_material_validation_single_collection(collection_id, title=tree.title),
            *(_get_material_validation_single_collection(node.node_id, title=node.title) for node in children),
        ],
    )


# FIXME: Try to eliminate the last non-realtime calculation
material_validation_cache: dict[uuid.UUID, MaterialValidationResponse] = {}


@repeat_every(seconds=BACKGROUND_TASK_TIME_INTERVAL, logger=logger)
def background_task():

    logger.info(f"Updating material validation cache. Length: {len(COLLECTION_NAME_TO_ID)}")

    for counter, (title, collection) in enumerate(COLLECTION_NAME_TO_ID.items()):
        collection = uuid.UUID(collection)
        logger.info(f"Working on: {title}")
        material_validation_cache[collection] = get_material_validation(collection_id=collection)

    logger.info("Storing in cache.")
    logger.info("Background task done")
