import uuid

from aiohttp import ClientSession

from app.api.collections.tree import CollectionNode
from app.core.constants import COLLECTION_ROOT_ID


async def tree_from_vocabs(
    session: ClientSession, node_id: uuid.UUID
) -> list[CollectionNode]:
    url = f"https://vocabs.openeduhub.de/w3id.org/openeduhub/vocabs/oeh-topics/{node_id}.json"
    response = await session.get(url=url)
    if response.status == 200:
        data = await response.json()
        keyword = "hasTopConcept" if str(node_id) == COLLECTION_ROOT_ID else "narrower"
        return collection_to_model(data[keyword])


def collection_to_model(data: list[dict]) -> list[CollectionNode]:
    return [
        CollectionNode(
            node_id=collection["id"].split("/")[-1],
            title=collection["prefLabel"]["de"],
            children=collection_to_model(collection["narrower"])
            if "narrower" in collection
            else [],
        )
        for collection in data
    ]
