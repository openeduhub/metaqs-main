from __future__ import (  # Needed for recursive type annotation, can be dropped with Python>3.10
    annotations,
)

import uuid
from typing import Iterable, Optional

from elasticsearch_dsl import Search
from elasticsearch_dsl.response import Response
from fastapi import HTTPException
from pydantic import BaseModel

from app.core import portals
from app.core.config import ELASTIC_TOTAL_SIZE
from app.core.custom_logging import logger
from app.elastic.attributes import ElasticResourceAttribute
from app.elastic.search import CollectionSearch


class Tree(BaseModel):
    node_id: uuid.UUID
    level: int
    title: str
    children: list[Tree]
    parent_id: Optional[uuid.UUID]

    def flatten(self, root: bool = True) -> Iterable[Tree]:
        """
        A generator that will iterate through all nodes of the tree in unspecified order.
        :param root: If true, the root node (self) will be included, if false, it will be skipped.
        """
        if root:
            yield self
        for child in self.children:
            yield from child.flatten(root=True)

    def bft(self, root: bool = True) -> Iterable[Tree]:
        """Traverse the tree in breadth-first order."""
        if root:
            yield self
        for child in self.children:
            yield child
        for child in self.children:
            yield from child.bft(root=False)


def tree_search(node_id: uuid.UUID) -> Search:
    """
    Build an elastic search query that will return all nodes of the collection subtree defined by given collection id.
    Note: The result will _not_ include the actual root node of the queried subtree.
    :param node_id: The root node of the subtree for which to build the search.
    """
    return (
        CollectionSearch()
        .collection_filter(collection_id=node_id)
        .source(
            [
                ElasticResourceAttribute.NODE_ID.path,
                ElasticResourceAttribute.COLLECTION_TITLE.path,
                ElasticResourceAttribute.COLLECTION_PATH.path,
                ElasticResourceAttribute.PARENT_ID.path,
            ]
        )
        .sort(ElasticResourceAttribute.FULLPATH.path)
        .extra(size=ELASTIC_TOTAL_SIZE, from_=0)
    )


def tree(node_id: uuid.UUID) -> Tree:
    """
    Build the collection tree for given top level collection_id.

    All direct and indirect child nodes of given node_id will be queried,
    and the received list will be transformed in the subtree defined by the input node_id.

    :param node_id: The toplevel collection that defines the subtree
    :return: The generated tree starting with the root node defined by the node_id argument.
    """
    response: Response = tree_search(node_id).execute()

    if not response.success():
        raise HTTPException(
            status_code=502,
            detail="Could not query elastic search to fetch collection tree.",
        )

    id_to_name = {id: name for name, id in portals.portal_data_cache.items()}

    # note the "root" here is actually a toplevel collection (e.g. Chemie, Deutsch,...)
    # i.e. it is the root of the returned subtree.
    root = Tree(
        node_id=node_id,
        level=0,
        title=id_to_name[str(node_id)],
        children=[],  # will be filled in below
        parent_id=None,
    )

    def try_node(hit, level) -> Optional[Tree]:
        """
        Some hits from elasticsearch may be incomplete (e.g. missing title).
        For those hits this function can return None to skip them, or fill in the UUID as title if desired.
        """
        try:
            return Tree(
                node_id=uuid.UUID(hit["nodeRef"]["id"]),
                title=hit["properties"]["cm:title"],
                children=[],  # noqa will be appended upon in recursion below
                level=level,
                parent_id=uuid.UUID(hit["parentRef"]["id"]),
            )
        except KeyError as e:
            node_id = hit["nodeRef"]["id"]
            logger.warning(f"Collection node {node_id} will be skipped. Missing attribute: {e} ")
            return None

    # gather all nodes in a set to track if the tree building covers all nodes
    node_ids = {uuid.UUID(hit["nodeRef"]["id"]) for hit in response.hits}

    # gather all (valid) nodes in a dictionary by their parent id.
    hits_by_parent_id: dict[uuid.UUID, list[dict]] = {}
    for hit in response.hits:
        parent_id = uuid.UUID(hit["parentRef"]["id"])
        if parent_id not in hits_by_parent_id:
            hits_by_parent_id[parent_id] = []
        hits_by_parent_id[parent_id].append(hit)

    # build up tree
    def recurse(parent: Tree):
        for hit in hits_by_parent_id.get(parent.node_id, []):
            if (node := try_node(hit, level=parent.level + 1)) is not None:
                parent.children.append(node)
                node_ids.remove(node.node_id)
                recurse(node)

    recurse(root)  # actually initiate the recursion :)

    if len(node_ids) != 0:
        logger.warning(f"Not all nodes could be arranged in the tree. Left over: {node_ids}")

    return root
