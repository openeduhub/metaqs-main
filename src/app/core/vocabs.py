import uuid

from aiohttp import ClientSession

from app.api.collections.tree import Tree
from app.core.constants import COLLECTION_TOPIC_PORTALS_ROOT_NODE_ID


async def tree_from_vocabs(session: ClientSession, node_id: uuid.UUID) -> list[Tree]:
    url = f"https://vocabs.openeduhub.de/w3id.org/openeduhub/vocabs/oeh-topics/{node_id}.json"
    response = await session.get(url=url)
    if response.status == 200:
        data = await response.json()
        keyword = "hasTopConcept" if str(node_id) == COLLECTION_TOPIC_PORTALS_ROOT_NODE_ID else "narrower"
        return collection_to_model(data[keyword])


def collection_to_model(data: list[dict], level=0) -> list[Tree]:
    return [
        Tree(
            node_id=collection["id"].split("/")[-1],
            title=collection["prefLabel"]["de"],
            level=level,
            children=collection_to_model(collection["narrower"], level=level + 1) if "narrower" in collection else [],
        )
        for collection in data
    ]
