from __future__ import annotations

from itertools import chain
from typing import ClassVar, Dict, List, Optional, Type, TypeVar
from uuid import UUID

from glom import Coalesce, Iter, glom

from app.elastic.fields import Field, FieldType

from .base import BaseModel, ResponseModel
from .elastic import ElasticResource, ElasticResourceAttribute
from .util import EmptyStrToNone

_COLLECTION = TypeVar("_COLLECTION")


class _CollectionAttribute(Field):
    TITLE = ("properties.cm:title", FieldType.TEXT)
    DESCRIPTION = ("properties.cm:description", FieldType.TEXT)
    PATH = ("path", FieldType.KEYWORD)
    PARENT_ID = ("parentRef.id", FieldType.KEYWORD)


CollectionAttribute = Field(
    "CollectionAttribute",
    [
        (f.name, (f.value, f.field_type))
        for f in chain(ElasticResourceAttribute, _CollectionAttribute)
    ],
)


class CollectionBase(ElasticResource):
    title: Optional[EmptyStrToNone] = None
    keywords: Optional[List[str]] = None
    description: Optional[EmptyStrToNone] = None
    path: Optional[List[UUID]] = None
    parent_id: Optional[UUID] = None

    source_fields: ClassVar[set] = {
        CollectionAttribute.NODEREF_ID,
        CollectionAttribute.TYPE,
        CollectionAttribute.NAME,
        CollectionAttribute.TITLE,
        CollectionAttribute.KEYWORDS,
        CollectionAttribute.DESCRIPTION,
        CollectionAttribute.PATH,
        CollectionAttribute.PARENT_ID,
    }

    @classmethod
    def parse_elastic_hit_to_dict(
        cls: Type[_COLLECTION],
        hit: Dict,
    ) -> dict:
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
        }
        return {
            **super(CollectionBase, cls).parse_elastic_hit_to_dict(hit),
            **glom(hit, spec),
        }

    @classmethod
    def parse_elastic_hit(
        cls: Type[_COLLECTION],
        hit: Dict,
    ) -> _COLLECTION:
        collection = cls.construct(**cls.parse_elastic_hit_to_dict(hit))
        try:
            collection.parent_id = collection.path[-1]
        except IndexError:
            pass
        return collection


class Collection(ResponseModel, CollectionBase):
    pass


# TODO: move to api package
class CollectionMaterialsCount(ResponseModel):
    noderef_id: UUID
    title: str
    materials_count: int


# TODO: move to api package
class PortalTreeNode(BaseModel):
    noderef_id: UUID
    title: str
    children: List[PortalTreeNode]


PortalTreeNode.update_forward_refs()
