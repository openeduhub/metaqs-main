from __future__ import (  # Needed for recursive type annotation, can be dropped with Python>3.10
    annotations,
)

from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class CollectionNode(BaseModel):
    noderef_id: UUID
    title: Optional[str]  # might be none due to data model
    children: list[CollectionNode]
    parent_id: Optional[UUID]


class MissingMaterials(CollectionNode):
    """
    A model containing information about entries which miss, e.g, a description.
    By returning this model the editors know enough about the entry to find and correct it

    param
        description: a free text description of the context
        path: the complete id path, i.e., from parent node id up to the root id of elastic search
        type: Indicates the type of content, must be ccm:map in the current implementation
    """

    keywords: list[str]
    description: str
    path: list[str]
    type: str
    name: str
