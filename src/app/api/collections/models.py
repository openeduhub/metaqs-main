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

    def bft(self, root: bool = True) -> Iterable[CollectionNode]:
        """Traverse the tree in breadth-first order."""
        if root:
            yield self
        for child in self.children:
            yield child
        for child in self.children:
            yield from child.bft(root=False)
