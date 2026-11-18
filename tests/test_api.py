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


def test_folium_map_endpoint_returns_html_for_available_trip() -> None:
    from pathsnap.backend.main import app

    with TestClient(app) as client:
        trips = client.get("/api/trips")
        assert trips.status_code == 200
        trip_id = trips.json()[0]
        response = client.get(f"/api/trips/{trip_id}/map")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "<html" in response.text.lower()
    assert "GPS observations" in response.text
    assert "Predicted route" in response.text
    assert "Reference route" not in response.text
