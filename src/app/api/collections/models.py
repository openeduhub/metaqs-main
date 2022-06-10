from __future__ import (  # Needed for recursive type annotation, can be dropped with Python>3.10
    annotations,
)

from itertools import chain
from uuid import UUID

from pydantic import BaseModel

from app.elastic.fields import Field, FieldType
from app.models import ElasticResourceAttribute


class CollectionTreeNode(BaseModel):
    noderef_id: UUID
    title: str
    children: list[CollectionTreeNode]


class Collection(BaseModel):
    noderef_id: UUID
    title: str
    children: list[CollectionTreeNode]
    parent_id: UUID


class _CollectionAttribute(Field):
    TITLE = ("properties.cm:title", FieldType.TEXT)
    DESCRIPTION = ("properties.cm:description", FieldType.TEXT)
    PATH = ("path", FieldType.KEYWORD)
    PARENT_ID = ("parentRef.id", FieldType.KEYWORD)
    NODE_ID = ("nodeRef.id", FieldType.KEYWORD)


CollectionAttribute = Field(
    "CollectionAttribute",
    [
        (f.name, (f.value, f.field_type))
        for f in chain(ElasticResourceAttribute, _CollectionAttribute)
    ],
)
