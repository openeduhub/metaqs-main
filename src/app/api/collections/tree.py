from __future__ import (  # Needed for recursive type annotation, can be dropped with Python>3.10
    annotations,
)

from itertools import chain
from uuid import UUID

from aiohttp import ClientSession
from elasticsearch_dsl.response import Response
from glom import Coalesce, Iter, glom
from pydantic import BaseModel

from app.api.quality_matrix.quality_matrix import add_base_match_filters
from app.core.config import ELASTIC_TOTAL_SIZE
from app.core.constants import COLLECTION_ROOT_ID
from app.elastic.dsl import qbool, qterm
from app.elastic.fields import Field, FieldType
from app.elastic.search import Search
from app.models import ElasticResourceAttribute


class CollectionTreeNode(BaseModel):
    noderef_id: UUID
    title: str
    children: list[CollectionTreeNode]


def collection_to_model(data: list[dict]) -> list[CollectionTreeNode]:
    return [
        CollectionTreeNode(
            noderef_id=collection["id"].split("/")[-1],
            title=collection["prefLabel"]["de"],
            children=collection_to_model(collection["narrower"])
            if "narrower" in collection
            else [],
        )
        for collection in data
    ]


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


async def parsed_tree(session: ClientSession, node_id: UUID):
    url = f"https://vocabs.openeduhub.de/w3id.org/openeduhub/vocabs/oehTopics/{node_id}.json"
    response = await session.get(url=url)
    if response.status == 200:
        data = await response.json()
        keyword = "hasTopConcept" if str(node_id) == COLLECTION_ROOT_ID else "narrower"
        return collection_to_model(data[keyword])


def tree_query(node_id: UUID) -> Search:
    s = add_base_match_filters(
        Search().query(qbool(filter=qterm(qfield="path", value=node_id)))
    )
    s = s.source(
        ["nodeRef.id", "properties.cm:title", "collections.path", "parentRef.id"]
    ).sort("fullpath")[:ELASTIC_TOTAL_SIZE]
    return s


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


def hits_to_collection(hits: list) -> list[Collection]:
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


def parse_tree(node_id: UUID):
    response: Response = tree_query(node_id).execute()

    if response.success():
        collection = hits_to_collection(response)
        return build_portal_tree(collection, node_id)


# TODO: Include parent/current node
async def collection_tree(node_id: UUID, use_vocabs: bool = False):
    if use_vocabs:
        async with ClientSession() as session:
            return await parsed_tree(session, node_id)
    return parse_tree(node_id)
