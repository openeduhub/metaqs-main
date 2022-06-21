from typing import Optional, TypeVar, Union
from uuid import UUID

from elasticsearch_dsl.query import Q, Query
from fastapi.params import Path
from fastapi.params import Query as ParamQuery
from glom import Coalesce, Iter
from pydantic import BaseModel

from app.api.collections.models import MissingMaterials
from app.api.collections.utils import hits_to_object
from app.core.config import ELASTIC_TOTAL_SIZE
from app.elastic.dsl import qbool, qmatch
from app.elastic.elastic import ResourceType, type_filter
from app.elastic.fields import Field
from app.elastic.search import Search
from app.models import CollectionAttribute

MissingCollectionField = Field(
    "MissingCollectionField",
    [
        (f.name, (f.value, f.field_type))
        for f in [
            CollectionAttribute.NAME,
            CollectionAttribute.TITLE,
            CollectionAttribute.KEYWORDS,
            CollectionAttribute.DESCRIPTION,
        ]
    ],
)


class MissingAttributeFilter(BaseModel):
    attr: MissingCollectionField

    def __call__(self, query_dict: dict):
        query_dict["must_not"] = qwildcard(qfield=self.attr, value="*")
        return query_dict


def collections_filter_params(
    *, missing_attr: MissingCollectionField = Path(...)
) -> MissingAttributeFilter:
    return MissingAttributeFilter(attr=missing_attr.value)


CollectionResponseField = Field(
    "CollectionAttribute",
    [(f.name, (f.value, f.field_type)) for f in CollectionAttribute],
)


def collection_response_fields(
    *, response_fields: set[CollectionResponseField] = ParamQuery(None)
) -> set[CollectionAttribute]:
    return response_fields


_COLLECTION = TypeVar("_COLLECTION")


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


class MissingAttributeFilter(BaseModel):
    attr: MissingCollectionField

    def __call__(self, query_dict: dict):
        query_dict["must_not"] = qwildcard(qfield=self.attr, value="*")
        return query_dict


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
    noderef_id: UUID, missing_attr_filter: MissingAttributeFilter, max_hits: int
) -> Search:
    query_dict = get_many_base_query(
        resource_type=ResourceType.COLLECTION,
        noderef_id=noderef_id,
    )
    # TODO: Refactor, simplify
    query_dict = missing_attr_filter.__call__(query_dict=query_dict)

    search = (
        Search()
        .base_filters()
        .query(qbool(**query_dict))
        .source(includes=[source.path for source in all_source_fields])[:max_hits]
    )
    return search


missing_attributes_spec = {
    "title": Coalesce(CollectionAttribute.TITLE.path, default=None),
    "keywords": (
        Coalesce(CollectionAttribute.KEYWORDS.path, default=[]),
        Iter().all(),
    ),
    "description": Coalesce(CollectionAttribute.DESCRIPTION.path, default=None),
    "path": (
        Coalesce(CollectionAttribute.PATH.path, default=[]),
        Iter().all(),
    ),
    "parent_id": Coalesce(CollectionAttribute.PARENT_ID.path, default=None),
    "noderef_id": Coalesce(CollectionAttribute.NODE_ID.path, default=None),
    "name": Coalesce(CollectionAttribute.NAME.path, default=None),
    "type": Coalesce(CollectionAttribute.TYPE.path, default=None),
    "children": Coalesce("", default=[]),  # workaround to map easier to pydantic model
}


async def get_child_collections_with_missing_attributes(
    noderef_id: UUID,
    missing_attr_filter: MissingAttributeFilter,
    max_hits: Optional[int] = ELASTIC_TOTAL_SIZE,
) -> list[MissingMaterials]:
    s = missing_attributes_search(noderef_id, missing_attr_filter, max_hits)

    response = s.execute()
    if response.success():
        return hits_to_object(response, missing_attributes_spec, MissingMaterials)
