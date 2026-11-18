from pathlib import Path

import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient


def test_health_endpoint() -> None:
    from pathsnap.backend.main import app
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_predict_schema_rejects_invalid_trip_id() -> None:
    from pathsnap.backend.main import app
    with TestClient(app) as client:
        response = client.post("/api/predict", json={"trip_id": "../../route"})
    assert response.status_code == 422
