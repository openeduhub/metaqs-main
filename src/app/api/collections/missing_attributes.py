from __future__ import annotations

import uuid
from typing import Optional

from elasticsearch_dsl.query import Q
from glom import Coalesce, Iter

from app.api.collections.models import MissingMaterials
from app.api.collections.utils import all_source_fields, map_elastic_response_to_model
from app.core.config import ELASTIC_TOTAL_SIZE
from app.core.models import ElasticResourceAttribute
from app.elastic.dsl import qbool, qmatch
from app.elastic.elastic import ResourceType, type_filter
from app.elastic.search import Search

missing_attribute_filter = [
    ElasticResourceAttribute.COLLECTION_TITLE,
    ElasticResourceAttribute.NAME,
    ElasticResourceAttribute.KEYWORDS,
    ElasticResourceAttribute.DESCRIPTION,
    ElasticResourceAttribute.LICENSES,
]


missing_attributes_spec = {
    "title": Coalesce(ElasticResourceAttribute.TITLE.path, default=""),
    "keywords": (
        Coalesce(ElasticResourceAttribute.KEYWORDS.path, default=[]),
        Iter().all(),
    ),
    "description": Coalesce(ElasticResourceAttribute.DESCRIPTION.path, default=""),
    "path": (
        Coalesce(ElasticResourceAttribute.PATH.path, default=[]),
        Iter().all(),
    ),
    "parent_id": Coalesce(ElasticResourceAttribute.PARENT_ID.path, default=""),
    "node_id": Coalesce(ElasticResourceAttribute.NODE_ID.path, default=""),
    "name": Coalesce(ElasticResourceAttribute.NAME.path, default=""),
    "type": Coalesce(ElasticResourceAttribute.TYPE.path, default=""),
    "children": Coalesce("", default=[]),  # workaround to map easier to pydantic model
}


def missing_attributes_search(
    node_id: uuid.UUID, missing_attribute: str, max_hits: int
) -> Search:
    query = {
        "filter": [*type_filter[ResourceType.COLLECTION]],
        "minimum_should_match": 1,
        "should": [
            qmatch(**{"path": node_id}),
            qmatch(**{"nodeRef.id": node_id}),
        ],
        "must_not": Q("wildcard", **{missing_attribute: {"value": "*"}}),
    }

    return (
        Search()
        .base_filters()
        .query(qbool(**query))
        .source(includes=[source.path for source in all_source_fields])[:max_hits]
    )


async def collections_with_missing_attributes(
    node_id: uuid.UUID,
    missing_attribute: str,
    max_hits: Optional[int] = ELASTIC_TOTAL_SIZE,
) -> list[MissingMaterials]:
    search = missing_attributes_search(node_id, missing_attribute, max_hits)

    response = search.execute()
    if response.success():
        return map_elastic_response_to_model(
            response, missing_attributes_spec, MissingMaterials
        )
