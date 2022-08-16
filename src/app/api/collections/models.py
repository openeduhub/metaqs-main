from __future__ import (  # Needed for recursive type annotation, can be dropped with Python>3.10
    annotations,
)

import uuid
from typing import Optional, Iterable

from pydantic import BaseModel


class CollectionNode(BaseModel):
    node_id: uuid.UUID
    title: str
    children: list[CollectionNode]
    parent_id: Optional[uuid.UUID]

    def flatten(self, root: bool = True) -> Iterable[CollectionNode]:
        """
        A generator that will iterate through all nodes of the tree in unspecified order.
        :param root: If true, the root node (self) will be included, if false, it will be skipped.
        """
        if root:
            yield self
        for child in self.children:
            yield from child.flatten(root=True)


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
