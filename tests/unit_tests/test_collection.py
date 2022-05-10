from starlette.testclient import TestClient

from app.main import fastapi_app

client = TestClient(fastapi_app)


def test_404():
    response = client.get("/collections")
    assert response.status_code == 404
    assert response.json() == {"errors": ["Not Found"]}
