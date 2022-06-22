from __future__ import annotations

from typing import Optional, Union
from uuid import UUID

from elasticsearch_dsl.query import Q, Query
from glom import Coalesce, Iter

from app.api.collections.models import MissingMaterials
from app.api.collections.utils import map_elastic_response_to_model
from app.core.config import ELASTIC_TOTAL_SIZE
from app.elastic.dsl import qbool, qmatch
from app.elastic.elastic import ResourceType, type_filter
from app.elastic.fields import Field
from app.elastic.search import Search
from app.models import (
    CollectionAttribute,
    ElasticResourceAttribute,
    _CollectionAttribute,
)


def qwildcard(qfield: Union[Field, str], value: str) -> Query:
    if isinstance(qfield, Field):
        qfield = qfield.path
    return Q("wildcard", **{qfield: {"value": value}})


all_source_fields: list = [
    CollectionAttribute.NODEREF_ID,
    CollectionAttribute.TYPE,
    CollectionAttribute.NAME,
    CollectionAttribute.TITLE,
    CollectionAttribute.KEYWORDS,
    CollectionAttribute.DESCRIPTION,
    CollectionAttribute.PATH,
    CollectionAttribute.PARENT_ID,
]


def get_many_base_query(
    resource_type: ResourceType,
    noderef_id: UUID,
) -> dict:
    query_dict = {"filter": [*type_filter[resource_type]]}

    prefix = "collections." if resource_type == ResourceType.MATERIAL else ""
    query_dict["should"] = [
        qmatch(**{f"{prefix}path": noderef_id}),
        qmatch(**{f"{prefix}nodeRef.id": noderef_id}),
    ]
    query_dict["minimum_should_match"] = 1

    return query_dict


def missing_attributes_search(
    noderef_id: UUID, missing_attribute: str, max_hits: int
) -> Search:
    query_dict = get_many_base_query(
        resource_type=ResourceType.COLLECTION,
        noderef_id=noderef_id,
    )

    query_dict["must_not"] = Q("wildcard", **{missing_attribute: {"value": "*"}})

    search = (
        Search()
        .base_filters()
        .query(qbool(**query_dict))
        .source(includes=[source.path for source in all_source_fields])[:max_hits]
    )
    return search


missing_attributes_spec = {
    "title": Coalesce(CollectionAttribute.TITLE.path, default=""),
    "keywords": (
        Coalesce(CollectionAttribute.KEYWORDS.path, default=[]),
        Iter().all(),
    ),
    "description": Coalesce(CollectionAttribute.DESCRIPTION.path, default=""),
    "path": (
        Coalesce(CollectionAttribute.PATH.path, default=[]),
        Iter().all(),
    ),
    "parent_id": Coalesce(CollectionAttribute.PARENT_ID.path, default=""),
    "noderef_id": Coalesce(CollectionAttribute.NODE_ID.path, default=""),
    "name": Coalesce(CollectionAttribute.NAME.path, default=""),
    "type": Coalesce(CollectionAttribute.TYPE.path, default=""),
    "children": Coalesce("", default=[]),  # workaround to map easier to pydantic model
}


async def collections_with_missing_attributes(
    noderef_id: UUID,
    missing_attribute: str,
    max_hits: Optional[int] = ELASTIC_TOTAL_SIZE,
) -> list[MissingMaterials]:
    search = missing_attributes_search(noderef_id, missing_attribute, max_hits)

    response = search.execute()
    if response.success():
        return map_elastic_response_to_model(
            response, missing_attributes_spec, MissingMaterials
        )


missingPropertyFilter = [
    _CollectionAttribute.TITLE,
    ElasticResourceAttribute.NAME,
    ElasticResourceAttribute.KEYWORDS,
    _CollectionAttribute.DESCRIPTION,
]
