import uuid
from unittest import mock

import pytest
from starlette.testclient import TestClient

from app.main import api

client = TestClient(api())


def test_404():
    response = client.get("/collections")
    assert response.status_code == 404
    assert response.json() == {"errors": ["Not Found"]}


def test_get_quality():
    with mock.patch("app.api.api.source_quality") as mocked_source:
        with mock.patch("app.api.api.collection_quality"):
            mocked_source.return_value = [], {}

            response = client.get("/quality")
            assert response.status_code == 422

            with pytest.raises(ValueError):
                client.get("/quality", params={"node_id": ""})

            response = client.get("/quality", params={"node_id": str(uuid.uuid4())})
            assert response.status_code == 422

            response = client.get(
                "/quality", params={"node_id": "4940d5da-9b21-4ec0-8824-d16e0409e629"}
            )
            assert response.status_code == 200
