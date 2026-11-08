"""Integration tests: browser assets -> FastAPI HTTP -> SQLite persistence.

Run: pytest -q web_lab/tests
Uses a temporary SQLite database and synthetic records.
"""
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from fastapi.testclient import TestClient

from web_lab.app import create_app, fare_cents


@pytest.fixture()
def client():
    with TemporaryDirectory() as directory:
        with TestClient(create_app(Path(directory) / "rides.sqlite3")) as api:
            yield api


def sample(key="demo-key-123456", **values):
    record = {"passenger": "Student", "pickup": "UCC", "destination": "Station",
              "distance_km": 4.5, "request_key": key}
    record.update(values)
    return record


def test_html_and_static_assets(client):
    assert client.get("/").status_code == 200
    assert "<form" in client.get("/").text
    assert client.get("/static/app.js").status_code == 200
    assert "fetch(" in client.get("/static/app.js").text
    assert client.get("/static/style.css").status_code == 200
    assert "grid-template-columns" in client.get("/static/style.css").text


def test_openapi_schema_and_health(client):
    assert client.get("/api/health").json()["status"] == "ok"
    schema = client.get("/openapi.json").json()
    assert "/api/rides" in schema["paths"]
    assert "RideCreate" in schema["components"]["schemas"]


def test_create_get_list_and_persistence(client):
    result = client.post("/api/rides", json=sample())
    assert result.status_code == 201, result.text
    created = result.json()
    assert created["fare_cents"] == 925
    assert created["status"] == "requested"
    assert client.get("/api/rides/" + created["id"]).json()["id"] == created["id"]
    assert len(client.get("/api/rides").json()) == 1
    assert len(client.get("/api/rides?status=requested").json()) == 1


def test_idempotency_and_conflicting_payload(client):
    first = client.post("/api/rides", json=sample()).json()
    again = client.post("/api/rides", json=sample()).json()
    assert first["id"] == again["id"]
    conflict = client.post("/api/rides", json={**sample(), "pickup": "Airport"})
    assert conflict.status_code == 409
    assert len(client.get("/api/rides").json()) == 1


def test_422_validation_and_sql_injection_resistance(client):
    for values in (
        sample(distance_km=-5),
        sample(pickup=" "),
        sample(destination="UCC"),
        sample(passenger=""),
    ):
        assert client.post("/api/rides", json=values).status_code == 422
    attack = sample(key="injection-safe-123", pickup="x'); DROP TABLE rides; --")
    assert client.post("/api/rides", json=attack).status_code == 201
    assert len(client.get("/api/rides").json()) == 1
    assert client.get("/api/rides?status=evil").status_code == 422


def test_state_machine_and_delete(client):
    rid = client.post("/api/rides", json=sample()).json()["id"]
    assert client.patch(f"/api/rides/{rid}", json={"status": "completed"}).status_code == 409
    assert client.patch(f"/api/rides/{rid}", json={"status": "assigned"}).status_code == 200
    assert client.delete(f"/api/rides/{rid}").status_code == 409
    assert client.patch(f"/api/rides/{rid}", json={"status": "completed"}).status_code == 200
    assert client.patch(f"/api/rides/{rid}", json={"status": "requested"}).status_code == 409
    assert client.get(f"/api/rides/{rid}").json()["status"] == "completed"


def test_cancel_and_delete(client):
    rid = client.post("/api/rides", json=sample()).json()["id"]
    assert client.patch(f"/api/rides/{rid}", json={"status": "cancelled"}).status_code == 200
    assert client.delete(f"/api/rides/{rid}").status_code == 204
    assert client.get(f"/api/rides/{rid}").status_code == 404


def test_fare_boundaries():
    assert fare_cents(1) == 400
    assert fare_cents(4.5) == 925
