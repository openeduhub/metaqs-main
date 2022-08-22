from __future__ import (  # Needed for recursive type annotation, can be dropped with Python>3.10
    annotations,
)

import uuid
from typing import Optional, Iterable

from elasticsearch_dsl.response import Response
from fastapi import HTTPException
from pydantic import BaseModel

from app.core.config import ELASTIC_TOTAL_SIZE
from app.core.constants import COLLECTION_NAME_TO_ID
from app.core.logging import logger
from app.core.models import ElasticResourceAttribute
from app.elastic.dsl import qbool, qterm
from app.elastic.elastic import ResourceType
from app.elastic.search import Search


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


def tree_search(node_id: uuid.UUID) -> Search:
    """
    Build an elastic search query that will return all nodes of the collection subtree defined by given collection id.
    Note: The result will _not_ include the actual root node of the queried subtree.
    :param node_id: The root node of the subtree for which to build the search.
    """
    # make search.to_dict() result JSON serializable
    node_id = str(node_id)
    return (
        Search()
        .base_filters()
        .type_filter(ResourceType.COLLECTION)
        .query(qbool(filter=qterm(qfield=ElasticResourceAttribute.PATH.path, value=node_id)))
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


def build_collection_tree(node_id: uuid.UUID) -> CollectionNode:
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

    id_to_name = {id: name for name, id in COLLECTION_NAME_TO_ID.items()}

    # note the "root" here is actually a toplevel collection (e.g. Chemie, Deutsch,...)
    # i.e. it is the root of the returned subtree.
    root = CollectionNode(
        node_id=node_id,
        title=id_to_name[str(node_id)],
        children=[],  # will be filled in below
        parent_id=None,
    )

    def try_node(hit) -> Optional[CollectionNode]:
        """
        Some hits from elasticsearch may be incomplete (e.g. missing title).
        For those hits this function can return None to skip them, or fill in the UUID as title if desired.
        """
        try:
            return CollectionNode(
                node_id=uuid.UUID(hit["nodeRef"]["id"]),
                title=hit["properties"]["cm:title"],
                children=[],
                parent_id=uuid.UUID(hit["parentRef"]["id"]),
            )
        except KeyError as e:
            node_id = hit["nodeRef"]["id"]
            logger.warning(f"Collection node {node_id} will be skipped. Missing attribute: {e} ")
            return None

    # gather all (valid) nodes in a dictionary by their id.
    nodes = {node.node_id: node for hit in response.hits if (node := try_node(hit)) is not None}

    # build up tree
    def recurse(node: CollectionNode):
        node.children = [child for child in nodes.values() if child.parent_id == node.node_id]
        for child in node.children:
            nodes.pop(child.node_id)
            recurse(child)

    recurse(root)  # actually initiate the recursion :)

    if len(nodes) != 0:
        logger.warning(f"Not all nodes could be arranged in the tree. Left over: {nodes}")

    return root
