from __future__ import annotations

from uuid import UUID

from aiohttp import ClientSession
from fastapi import Path
from pydantic import BaseModel

from app.core.constants import PORTAL_ROOT_ID, PORTALS


def portal_id_with_root_param(
    *,
    node_id: UUID = Path(
        ...,
        examples={
            "Alle Fachportale": {"value": PORTAL_ROOT_ID},
            **PORTALS,
        },
    ),
) -> UUID:
    return node_id


class PortalTreeNode(BaseModel):
    noderef_id: UUID
    title: str
    children: list[PortalTreeNode]


def collection_to_model(data: list[dict]) -> list[PortalTreeNode]:
    return [
        PortalTreeNode(
            noderef_id=collection["id"].split("/")[-1],
            title=collection["prefLabel"]["de"],
            children=collection_to_model(collection["narrower"])
            if "narrower" in collection
            else [],
        )
        for collection in data
    ]


async def parsed_tree(session: ClientSession, node_id: UUID):
    oeh_topic_route = "oeh-topics" if str(node_id) == PORTAL_ROOT_ID else "oehTopics"
    url = f"https://vocabs.openeduhub.de/w3id.org/openeduhub/vocabs/{oeh_topic_route}/{node_id}.json"
    response = await session.get(url=url)
    if response.status == 200:
        data = await response.json()
        keyword = "hasTopConcept" if str(node_id) == PORTAL_ROOT_ID else "narrower"
        return collection_to_model(data[keyword])


# TODO: Include parent/current node
async def collection_tree(node_id: UUID):
    async with ClientSession() as session:
        return await parsed_tree(session, node_id)
