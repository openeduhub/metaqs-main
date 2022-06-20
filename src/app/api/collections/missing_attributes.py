from itertools import chain
from typing import Optional, Type, TypeVar, Union
from uuid import UUID

from elasticsearch_dsl.query import Q, Query
from fastapi.params import Path
from fastapi.params import Query as ParamQuery
from pydantic import BaseModel

from app.api.collections.models import CollectionNode
from app.api.collections.tree import hits_to_collection
from app.core.config import ELASTIC_TOTAL_SIZE
from app.elastic.dsl import qbool, qmatch
from app.elastic.elastic import ResourceType, type_filter
from app.elastic.fields import Field, FieldType
from app.elastic.search import Search


class _CollectionAttribute(Field):
    TITLE = ("properties.cm:title", FieldType.TEXT)
    DESCRIPTION = ("properties.cm:description", FieldType.TEXT)
    PATH = ("path", FieldType.KEYWORD)
    PARENT_ID = ("parentRef.id", FieldType.KEYWORD)


class ElasticResourceAttribute(Field):
    NODEREF_ID = ("nodeRef.id", FieldType.KEYWORD)
    TYPE = ("type", FieldType.KEYWORD)
    NAME = ("properties.cm:name", FieldType.TEXT)
    PERMISSION_READ = ("permissions.Read", FieldType.TEXT)
    EDU_METADATASET = ("properties.cm:edu_metadataset", FieldType.TEXT)
    PROTOCOL = ("nodeRef.storeRef.protocol", FieldType.KEYWORD)
    FULLPATH = ("fullpath", FieldType.KEYWORD)
    KEYWORDS = ("properties.cclom:general_keyword", FieldType.TEXT)
    EDU_CONTEXT = ("properties.ccm:educationalcontext", FieldType.TEXT)
    EDU_CONTEXT_DE = ("i18n.de_DE.ccm:educationalcontext", FieldType.TEXT)
    REPLICATION_SOURCE_DE = ("replicationsource", FieldType.TEXT)


CollectionAttribute = Field(
    "CollectionAttribute",
    [
        (f.name, (f.value, f.field_type))
        for f in chain(ElasticResourceAttribute, _CollectionAttribute)
    ],
)

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


source_fields: set = {
    CollectionAttribute.NODEREF_ID,
    CollectionAttribute.TYPE,
    CollectionAttribute.NAME,
    CollectionAttribute.TITLE,
    CollectionAttribute.KEYWORDS,
    CollectionAttribute.DESCRIPTION,
    CollectionAttribute.PATH,
    CollectionAttribute.PARENT_ID,
}

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


async def get_child_collections_with_missing_attributes(
    noderef_id: UUID,
    missing_attr_filter: MissingAttributeFilter,
    source_fields: Optional[set[CollectionAttribute]],
    max_hits: Optional[int] = ELASTIC_TOTAL_SIZE,
) -> list[CollectionNode]:
    return await get_many(
        ancestor_id=noderef_id,
        missing_attr_filter=missing_attr_filter,
        source_fields=source_fields,
        max_hits=max_hits,
    )


async def get_many(
    ancestor_id: Optional[UUID] = None,
    missing_attr_filter: Optional[MissingAttributeFilter] = None,
    max_hits: Optional[int] = ELASTIC_TOTAL_SIZE,
    source_fields: Optional[set[CollectionAttribute]] = None,
) -> list[CollectionNode]:
    query_dict = get_many_base_query(
        resource_type=ResourceType.COLLECTION,
        ancestor_id=ancestor_id,
    )
    if missing_attr_filter:
        query_dict = missing_attr_filter.__call__(query_dict=query_dict)
    s = Search().base_filters().query(qbool(**query_dict))

    response = s.source(source_fields if source_fields else source_fields)[
        :max_hits
    ].execute()

    if response.success():
        return hits_to_collection(response)


# TODO: eliminate; use query_many instead
def get_many_base_query(
    resource_type: ResourceType,
    ancestor_id: Optional[UUID] = None,
) -> dict:
    query_dict = {"filter": [*type_filter[resource_type]]}

    if ancestor_id:
        prefix = "collections." if resource_type == ResourceType.MATERIAL else ""
        query_dict["should"] = [
            qmatch(**{f"{prefix}path": ancestor_id}),
            qmatch(**{f"{prefix}nodeRef.id": ancestor_id}),
        ]
        query_dict["minimum_should_match"] = 1

    return query_dict


def filter_response_fields(
    items: list[BaseModel], response_fields: set[Field] = None
) -> list[BaseModel]:
    if response_fields:
        return [
            i.copy(include={f.name.lower() for f in response_fields}) for i in items
        ]
    return items


def parse_elastic_hit(
    cls: Type[_COLLECTION],
    hit: dict,
) -> _COLLECTION:
    collection = cls.construct(**cls.parse_elastic_hit_to_dict(hit))
    try:
        collection.parent_id = collection.path[-1]
    except IndexError:
        pass
    return collection
