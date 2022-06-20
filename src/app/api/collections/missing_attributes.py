from typing import Optional, TypeVar, Union
from uuid import UUID

from elasticsearch_dsl.query import Q, Query
from elasticsearch_dsl.response import Response
from fastapi.params import Path
from fastapi.params import Query as ParamQuery
from glom import Coalesce, Iter, glom
from pydantic import BaseModel

from app.api.collections.models import MissingMaterials
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
) -> list[MissingMaterials]:
    return await get_many(
        ancestor_id=noderef_id,
        missing_attr_filter=missing_attr_filter,
        source_fields=source_fields,
        max_hits=max_hits,
    )


def hits_to_missing_attributes(hits: Response) -> list[MissingMaterials]:
    collections = []
    for hit in hits:
        entry = hit.to_dict()
        spec = {
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
        }
        parsed_entry = glom(entry, spec)
        if parsed_entry["title"] is not None:
            collections.append(
                MissingMaterials(
                    noderef_id=parsed_entry["noderef_id"],
                    title=parsed_entry["title"],
                    children=[],
                    parent_id=parsed_entry["parent_id"],
                    keywords=parsed_entry["keywords"],
                    name=parsed_entry["name"],
                    description=parsed_entry["description"],
                    type=parsed_entry["type"],
                    path=parsed_entry["path"],
                )
            )
    return collections


async def get_many(
    ancestor_id: Optional[UUID] = None,
    missing_attr_filter: Optional[MissingAttributeFilter] = None,
    max_hits: Optional[int] = ELASTIC_TOTAL_SIZE,
    source_fields: Optional[set[CollectionAttribute]] = None,
) -> list[MissingMaterials]:
    query_dict = get_many_base_query(
        resource_type=ResourceType.COLLECTION,
        ancestor_id=ancestor_id,
    )
    if missing_attr_filter:
        query_dict = missing_attr_filter.__call__(query_dict=query_dict)
    s = Search().base_filters().query(qbool(**query_dict))

    response = s.source()[:max_hits].execute()

    if response.success():
        # rewind to parse with elastic hit
        return hits_to_missing_attributes(response)


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
