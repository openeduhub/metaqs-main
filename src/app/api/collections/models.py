from __future__ import (  # Needed for recursive type annotation, can be dropped with Python>3.10
    annotations,
)

from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from app.models import ElasticResourceAttribute, _CollectionAttribute


class CollectionNode(BaseModel):
    noderef_id: UUID
    title: Optional[str]  # might be none due to data model
    children: list[CollectionNode]
    parent_id: Optional[UUID]


class MissingMaterials(CollectionNode):
    keywords: list[str]
    description: str
    path: list[str]
    type: str
    name: str


class MissingPropertyFilter(Enum):
    TITLE = _CollectionAttribute.TITLE
    NAME = ElasticResourceAttribute.NAME
    KEYWORDS = ElasticResourceAttribute.KEYWORDS
    DESCRIPTION = _CollectionAttribute.DESCRIPTION
