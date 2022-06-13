from __future__ import (  # Needed for recursive type annotation, can be dropped with Python>3.10
    annotations,
)

from uuid import UUID

from aiohttp import ClientSession
from pydantic import BaseModel

from app.core.constants import COLLECTION_ROOT_ID


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


async def parsed_tree(session: ClientSession, node_id: UUID):
    url = f"https://vocabs.openeduhub.de/w3id.org/openeduhub/vocabs/oehTopics/{node_id}.json"
    response = await session.get(url=url)
    if response.status == 200:
        data = await response.json()
        keyword = "hasTopConcept" if str(node_id) == COLLECTION_ROOT_ID else "narrower"
        return collection_to_model(data[keyword])


# TODO: Include parent/current node
async def collection_tree(node_id: UUID):
    async with ClientSession() as session:
        return await parsed_tree(session, node_id)
