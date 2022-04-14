from aiohttp.test_utils import TestClient

from app.main import fastapi_app

client = TestClient(fastapi_app)


def test_get_portals():
    response = client.get("/collections")
    assert response.status_code == 200
    assert response.json() == {"fruit": "apple"}
