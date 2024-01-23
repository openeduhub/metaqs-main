from unittest import mock

from starlette.testclient import TestClient

from app.api.collections.quality_matrix import QualityMatrix
from app.main import api

client = TestClient(api())


def test_404():
    response = client.get("/collections")
    assert response.status_code == 404
    assert response.json() == {"errors": ["Not Found"]}


def test_get_quality():
    with mock.patch("app.api.api.quality_matrix", lambda collection, mode: QualityMatrix(rows=[], columns=[])):
        with mock.patch("app.api.api.tree", lambda x: None):
            node_id = "4940d5da-9b21-4ec0-8824-d16e0409e629"
            response = client.get(f"/collections/{node_id}/quality-matrix/collection")
            assert response.status_code == 200
