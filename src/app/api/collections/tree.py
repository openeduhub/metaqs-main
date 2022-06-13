from uuid import UUID

from aiohttp import ClientSession
from elasticsearch_dsl.response import Response
from glom import Coalesce, Iter, glom

from app.api.collections.models import (
    Collection,
    CollectionAttribute,
    CollectionTreeNode,
)
from app.api.collections.vocabs import tree_from_vocabs
from app.core.config import ELASTIC_TOTAL_SIZE
from app.elastic.dsl import qbool, qterm
from app.elastic.elastic import add_base_match_filters
from app.elastic.search import Search


def build_portal_tree(
    collections: list, root_noderef_id: UUID
) -> list[CollectionTreeNode]:
    lut = {str(root_noderef_id): []}

    for collection in collections:
        if collection.title:
            portal_node = CollectionTreeNode(
                noderef_id=collection.noderef_id,
                title=collection.title,
                children=[],
            )

            try:
                lut[str(collection.parent_id)].append(portal_node)
            except KeyError:
                lut[str(collection.parent_id)] = [portal_node]

            lut[str(collection.noderef_id)] = portal_node.children

    return lut.get(str(root_noderef_id), [])


def tree_query(node_id: UUID) -> Search:
    s = add_base_match_filters(
        Search().query(qbool(filter=qterm(qfield="path", value=node_id)))
    )
    s = s.source(
        ["nodeRef.id", "properties.cm:title", "collections.path", "parentRef.id"]
    ).sort("fullpath")[:ELASTIC_TOTAL_SIZE]
    return s


def hits_to_collection(hits: Response) -> list[Collection]:
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
            "node_id": Coalesce(CollectionAttribute.NODE_ID.path, default=None),
        }
        parsed_entry = glom(entry, spec)
        if parsed_entry["title"] is not None:
            collections.append(
                Collection(
                    noderef_id=parsed_entry["node_id"],
                    title=parsed_entry["title"],
                    children=[],
                    parent_id=parsed_entry["parent_id"],
                )
            )
    return collections


def tree_from_elastic(node_id: UUID):
    response: Response = tree_query(node_id).execute()

    if response.success():
        collection = hits_to_collection(response)
        return build_portal_tree(collection, node_id)


async def collection_tree(node_id: UUID, use_vocabs: bool = False):
    if use_vocabs:
        async with ClientSession() as session:
            return await tree_from_vocabs(session, node_id)
    return tree_from_elastic(node_id)
