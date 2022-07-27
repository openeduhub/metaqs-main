import asyncio
import uuid
from unittest import mock

from starlette.testclient import TestClient

from src.app.crud.collection import material_counts_by_descendant, get_many
from src.app.main import fastapi_app
from src.app.models.collection import CollectionAttribute

client = TestClient(fastapi_app)


def test_404():
    response = client.get("/collections")
    assert response.status_code == 404
    assert response.json() == {"errors": ["Not Found"]}


def test_get_portals():
    with mock.patch("app.api.v1.realtime.collections.crud_collection.get_portals") as get_portals:
        get_portals.return_value = 0
        response = client.get("/real-time/collections")
    assert response.status_code == 200
    assert response.json() == 0


async def test_material_counts_by_descendant():
    dummy_uuid = uuid.uuid4()
    try:
        result = material_counts_by_descendant(dummy_uuid)
    except:
        pass

    await get_many(dummy_uuid, source_fields={CollectionAttribute.NODEREF_ID,
                                              CollectionAttribute.PATH,
                                              CollectionAttribute.TITLE, })
    assert False


if __name__ == '__main__':
    asyncio.run(test_material_counts_by_descendant())
