from uuid import UUID

from aiohttp import ClientSession
from elasticsearch_dsl.response import Response
from glom import Coalesce, Iter

from app.api.collections.models import CollectionNode
from app.api.collections.utils import hits_to_object
from app.api.collections.vocabs import tree_from_vocabs
from app.core.config import ELASTIC_TOTAL_SIZE
from app.elastic.dsl import qbool, qterm
from app.elastic.search import Search
from app.models import CollectionAttribute


def build_portal_tree(collections: list, root_noderef_id: UUID) -> list[CollectionNode]:
    tree_hierarchy = {str(root_noderef_id): []}

    for collection in collections:
        if collection.title:
            tree_hierarchy.update(build_hierarchy(collection, tree_hierarchy))

    return tree_hierarchy[str(root_noderef_id)]


def build_hierarchy(
    collection, tree_hierarchy: dict[str, list[CollectionNode]]
) -> dict[str, list[CollectionNode]]:
    portal_node = CollectionNode(
        noderef_id=collection.noderef_id,
        title=collection.title,
        children=[],
    )

    if str(collection.parent_id) not in tree_hierarchy.keys():
        tree_hierarchy.update({str(collection.parent_id): []})

    tree_hierarchy[str(collection.parent_id)].append(portal_node)
    tree_hierarchy[str(collection.noderef_id)] = portal_node.children
    return tree_hierarchy


def tree_search(node_id: UUID) -> Search:
    s = Search().base_filters().query(qbool(filter=qterm(qfield="path", value=node_id)))
    s = s.source(
        ["nodeRef.id", "properties.cm:title", "collections.path", "parentRef.id"]
    ).sort("fullpath")[:ELASTIC_TOTAL_SIZE]
    return s


collection_spec = {
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
    "children": Coalesce("", default=[]),
}


def tree_from_elastic(node_id: UUID) -> list[CollectionNode]:
    response: Response = tree_search(node_id).execute()

    if response.success():
        collection = hits_to_object(response, collection_spec, CollectionNode)
        return build_portal_tree(collection, node_id)


async def collection_tree(
    node_id: UUID, use_vocabs: bool = False
) -> list[CollectionNode]:
    if use_vocabs:
        async with ClientSession() as session:
            return await tree_from_vocabs(session, node_id)
    return tree_from_elastic(node_id)
