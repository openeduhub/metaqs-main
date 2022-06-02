from __future__ import annotations

from uuid import UUID

from aiohttp import ClientSession
from fastapi import Path
from pydantic import BaseModel

PORTAL_ROOT_ID = "5e40e372-735c-4b17-bbf7-e827a5702b57"

PORTALS = {
    # "Physik": {"value": "unknown"},
    "Mathematik": {"value": "bd8be6d5-0fbe-4534-a4b3-773154ba6abc"},
    "Biologie": {"value": "15fce411-54d9-467f-8f35-61ea374a298d"},
    "Chemie": {"value": "4940d5da-9b21-4ec0-8824-d16e0409e629"},
    "Deutsch": {"value": "69f9ff64-93da-4d68-b849-ebdf9fbdcc77"},
    "DaZ": {"value": "26a336bf-51c8-4b91-9a6c-f1cf67fd4ae4"},
    "Englisch": {"value": "15dbd166-fd31-4e01-aabd-524cfa4d2783"},
    "Informatik": {"value": "742d8c87-e5a3-4658-86f9-419c2cea6574"},
    "Kunst": {"value": "6a3f5881-cce0-4e8d-b123-26392b3f1c19"},
    "Religion": {"value": "66c667bc-8777-4c57-b476-35f54ce9ff5d"},
    "Geschichte": {"value": "324f24e3-6687-4e89-b8dd-2bd0e20ff733"},
    "Medienbildung": {"value": "eef047a3-58ba-419c-ab7d-3d0cfd04bb4e"},
    "Politische Bildung": {"value": "ffd298b5-3a04-4d13-9d26-ddd5d3b5cedc"},
    "Sport": {"value": "ea776a48-b3f4-446c-b871-19f84b31d280"},
    "Darstellendes Spiel": {"value": "7998f334-9311-491e-9a58-72baf2a7efd2"},
    "Spanisch": {"value": "11bdb8a0-a9f5-4028-becc-cbf8e328dd4b"},
    "Tuerkisch": {"value": "26105802-9039-4add-bf21-07a0f89f6e70"},
    "Nachhaltigkeit": {"value": "d0ed50e6-a49f-4566-8f3b-c545cdf75067"},
    "OER": {"value": "a87c092d-e3b5-43ef-81db-757ab1967646"},
    "Zeitgemaesse Bildung": {"value": "a3291cd2-5fe4-444e-9b7b-65807d9b0024"},
    "Wirtschaft": {"value": "f0109e16-a8fc-48b5-9461-369571fd59f2"},
    "Geografie": {"value": "f1049950-bdda-45f5-9c73-38b51ea66c74"},
    "Paedagogik": {"value": "7e2a3536-8441-4328-8ee6-ab0068bb13f8"},
    "Franzoesisch": {"value": "86b990ef-0955-45ad-bdae-ec2623cf0e1a"},
    "Musik": {"value": "2eda0065-f69b-46c8-ae09-d258c8226a5e"},
    "Philosophie": {"value": "9d364fd0-4374-40b4-a153-3c722b9cda35"},
}


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
    response: list[PortalTreeNode] = []
    for collection in data:
        response.append(
            PortalTreeNode(
                noderef_id=collection["id"].split("/")[-1],
                title=collection["prefLabel"]["de"],
                children=collection_to_model(collection["narrower"])
                if "narrower" in collection
                else [],
            )
        )
    return response


async def parsed_tree(session: ClientSession, node_id: UUID):
    oeh_topic_route = "oeh-topics" if str(node_id) == PORTAL_ROOT_ID else "oehTopics"
    url = f"https://vocabs.openeduhub.de/w3id.org/openeduhub/vocabs/{oeh_topic_route}/{node_id}.json"
    response = await session.get(url=url)
    if response.status == 200:
        data = await response.json()
        if str(node_id) == PORTAL_ROOT_ID:
            collections = data["hasTopConcept"]
        else:
            collections = data["narrower"]
        return collection_to_model(collections)


# TODO: Include parent/current node
async def collection_tree(node_id: UUID):
    async with ClientSession() as session:
        return await parsed_tree(session, node_id)