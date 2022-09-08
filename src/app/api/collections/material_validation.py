import uuid

from elasticsearch_dsl import A
from fastapi import HTTPException
from pydantic import BaseModel

from app.core.config import ELASTIC_TOTAL_SIZE
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


def get_material_validation(collection_id: uuid.UUID) -> MaterialValidationResponse:
    """
    Build the response for the /material-validation endpoint.

    :param collection_id: The id of top level collection
    """
    logger.info(f"Analyzing collection for materials with missing attributes: {collection_id}")

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

    # Do a transitive search: We want the materials of any collection of the given subtree (including the root of the
    # subtree)
    search = (
        MaterialSearch()
        .collection_filter(collection_id=collection_id, transitive=True)
        .non_series_objects_filter()
        .extra(size=0, from_=0)  # we only care about the aggregations
    )

    search.aggs.bucket(
        "collections",
        A(
            "terms",
            field="collections.nodeRef.id.keyword",
            size=10000,
            aggs={
                name: {
                    # sub-sub-aggregation yielding all material ids of the nested (collection,missing-attribute) bucket
                    "aggs": {"material-ids": {"top_hits": {"size": ELASTIC_TOTAL_SIZE, "_source": ["nodeRef.id"]}}},
                    # define the actual nested bucket within the collection buckets
                    "missing": {"field": attr.keyword},
                }
                for name, attr in relevant_attributes.items()
            },
        ),
    )

    response = search.execute()

    if not response.success():
        raise HTTPException(status_code=502, detail="Failed to issue elastic search query.")

    return MaterialValidationResponse(
        collection_id=collection_id,
        missing_materials=[
            IncompleteMaterials(
                collection_id=uuid.UUID(bucket["key"]),
                **{
                    name: [
                        uuid.UUID(hit["_source"]["nodeRef"]["id"]) for hit in bucket[name]["docs"]["hits"]["hits"]
                    ]  # yes, it is very nested...
                    for name in relevant_attributes.keys()
                },
            )
            for bucket in response.aggregations["buckets"]
        ],
    )
