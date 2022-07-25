import uuid

from aiohttp import ClientSession
from elasticsearch_dsl.response import Response
from glom import Coalesce, Iter

from app.api.collections.models import CollectionNode
from app.api.collections.utils import map_elastic_response_to_model
from app.api.collections.vocabs import tree_from_vocabs
from app.core.config import ELASTIC_TOTAL_SIZE
from app.core.models import ElasticResourceAttribute
from app.elastic.dsl import qbool, qterm
from app.elastic.search import Search


def build_portal_tree(collections: list, root_id: uuid.UUID) -> list[CollectionNode]:
    tree_hierarchy = {str(root_id): []}

    for collection in collections:
        if collection.title:
            tree_hierarchy.update(build_hierarchy(collection, tree_hierarchy))

    return tree_hierarchy[str(root_id)]


def build_hierarchy(
    collection, tree_hierarchy: dict[str, list[CollectionNode]]
) -> dict[str, list[CollectionNode]]:
    portal_node = CollectionNode(
        node_id=collection.node_id,
        title=collection.title,
        children=[],
    )

    if str(collection.parent_id) not in tree_hierarchy.keys():
        tree_hierarchy.update({str(collection.parent_id): []})

    tree_hierarchy[str(collection.parent_id)].append(portal_node)
    tree_hierarchy[str(collection.node_id)] = portal_node.children
    return tree_hierarchy


def tree_search(node_id: uuid.UUID) -> Search:
    s = Search().base_filters().query(qbool(filter=qterm(qfield="path", value=node_id)))
    s = s.source(
        [
            ElasticResourceAttribute.NODE_ID.path,
            ElasticResourceAttribute.COLLECTION_TITLE.path,
            ElasticResourceAttribute.COLLECTION_PATH.path,
            ElasticResourceAttribute.PARENT_ID.path,
        ]
    ).sort("fullpath")[:ELASTIC_TOTAL_SIZE]
    return s


collection_spec = {
    "title": Coalesce(ElasticResourceAttribute.COLLECTION_TITLE.path, default=None),
    "keywords": (
        Coalesce(ElasticResourceAttribute.KEYWORDS.path, default=[]),
        Iter().all(),
    ),
    "description": Coalesce(
        ElasticResourceAttribute.COLLECTION_DESCRIPTION.path, default=None
    ),
    "path": (
        Coalesce(ElasticResourceAttribute.PATH.path, default=[]),
        Iter().all(),
    ),
    "parent_id": Coalesce(ElasticResourceAttribute.PARENT_ID.path, default=None),
    "node_id": Coalesce(ElasticResourceAttribute.NODE_ID.path, default=None),
    "children": Coalesce("", default=[]),
}


def tree_from_elastic(node_id: uuid.UUID) -> list[CollectionNode]:
    response: Response = tree_search(node_id).execute()

    if response.success():
        collection = map_elastic_response_to_model(
            response, collection_spec, CollectionNode
        )
        return build_portal_tree(collection, node_id)


async def collection_tree(
    node_id: uuid.UUID, use_vocabs: bool = False
) -> list[CollectionNode]:
    if use_vocabs:
        async with ClientSession() as session:
            return await tree_from_vocabs(session, node_id)
    return tree_from_elastic(node_id)
