import datetime
import uuid
from enum import Enum

from fastapi import HTTPException
from pydantic import BaseModel

from app.core.config import ELASTIC_TOTAL_SIZE
from app.elastic.attributes import ElasticResourceAttribute
from app.elastic.search import Search, CollectionSearch


class OehValidationError(str, Enum):
    MISSING = "missing"
    TOO_SHORT = "too_short"
    TOO_FEW = "too_few"


class CollectionValidationStats(BaseModel):
    node_id: uuid.UUID
    derived_at: datetime.datetime  # fixme: eventually remove?
    title: list[OehValidationError]
    keywords: list[OehValidationError]
    description: list[OehValidationError]
    edu_context: list[OehValidationError]


def get_collection_validation(collection_id: uuid.UUID) -> list[CollectionValidationStats]:
    """
    Get a list of collections (part of the sub-tree defined by given collection id, including the root of the subtree)
    where one of the following attributes is missing:

    - title # fixme: can a title be empty @tsimon
    - description
    - keywords
    - edu_context # fixme: does this even make sense?

    TODO: Eventually align the return data structure with PendingMaterialsResponse as we do the same thing for
          collections that is done for materials with PendingMaterialsResponse.
    """
    search: Search = (
        CollectionSearch()
        .collection_filter(collection_id=collection_id)
        .missing_attribute_filter(
            title=ElasticResourceAttribute.COLLECTION_TITLE,
            description=ElasticResourceAttribute.COLLECTION_DESCRIPTION,
            edu_context=ElasticResourceAttribute.EDU_CONTEXT,  # fixme: no edu context for collections?
            keywords=ElasticResourceAttribute.KEYWORDS,  # fixme: no keywords for collection?
        )
        .source(
            includes=["nodeRef.id", "properties.cm:title"]  # title is nice for debugging but actually not needed here
        )
        .extra(size=ELASTIC_TOTAL_SIZE, from_=0)
    )

    result = search.execute()

    if not result.success():
        raise HTTPException(status_code=502, detail="Failed to run elastic search query.")

    derived_at = datetime.datetime.now()
    return [
        CollectionValidationStats(
            node_id=uuid.UUID(hit["nodeRef"]["id"]),
            derived_at=derived_at,
            title=[OehValidationError.MISSING] if "title" in hit.meta.matched_queries else [],
            description=[OehValidationError.MISSING] if "description" in hit.meta.matched_queries else [],
            keywords=[OehValidationError.MISSING] if "keywords" in hit.meta.matched_queries else [],
            edu_context=[OehValidationError.MISSING] if "edu_context" in hit.meta.matched_queries else [],
        )
        for hit in result.hits
    ]
