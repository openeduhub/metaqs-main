from unittest import mock

from starlette.testclient import TestClient

from app.main import fastapi_app

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
