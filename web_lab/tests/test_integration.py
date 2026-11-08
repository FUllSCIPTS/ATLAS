"""Integration tests: browser assets -> FastAPI -> SQLite.

Run from the repository root:  python -m pytest -q web_lab/tests
Each test gets its own temporary SQLite database; all data is synthetic.
"""
import sqlite3
import threading
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from fastapi.testclient import TestClient

from web_lab.app import SECURITY_HEADERS, create_app, fare_cents


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


def driver_id(client, name="Ava"):
    return next(d["id"] for d in client.get("/api/drivers").json() if d["name"] == name)


# ---------------------------------------------------------------- static front end
def test_html_css_js_are_served(client):
    page = client.get("/")
    assert page.status_code == 200 and page.headers["content-type"].startswith("text/html")
    assert '<form id="booking"' in page.text and 'for="pickup"' in page.text
    js = client.get("/static/app.js")
    assert "fetch(" in js.text and "innerHTML" not in js.text.replace("NOT innerHTML", "")
    css = client.get("/static/style.css")
    assert "grid-template-columns" in css.text and "@media" in css.text


def test_importing_the_module_creates_no_database():
    with TemporaryDirectory() as directory:
        path = Path(directory) / "never.sqlite3"
        create_app(path)
        assert not path.exists()                       # created only when the server starts
        with TestClient(create_app(path)):
            assert path.exists()


def test_security_headers_on_every_response(client):
    for url in ("/", "/api/health", "/api/rides", "/static/style.css"):
        response = client.get(url)
        for name in SECURITY_HEADERS:
            assert name in response.headers, (url, name)
        assert response.headers["Server-Timing"].startswith("app;dur=")


def test_openapi_documents_the_contract(client):
    schema = client.get("/openapi.json").json()
    assert {"/api/rides", "/api/rides/{ride_id}", "/api/drivers", "/api/stats"} <= set(schema["paths"])
    status_enum = schema["components"]["schemas"]["RideUpdate"]["properties"]["status"]["enum"]
    assert status_enum == ["requested", "assigned", "completed", "cancelled"]


# ---------------------------------------------------------------- create, read, list
def test_create_get_and_list(client):
    created = client.post("/api/rides", json=sample())
    assert created.status_code == 201, created.text
    ride = created.json()
    assert ride["fare_cents"] == 925 and ride["status"] == "requested" and ride["driver_name"] is None
    assert client.get("/api/rides/" + ride["id"]).json()["id"] == ride["id"]
    listing = client.get("/api/rides")
    assert len(listing.json()) == 1 and listing.headers["X-Total-Count"] == "1"
    assert len(client.get("/api/rides?status=requested").json()) == 1
    assert client.get("/api/rides?status=evil").status_code == 422


def test_pagination(client):
    for i in range(7):
        client.post("/api/rides", json=sample(key=f"page-key-{i:04}", distance_km=i + 1))
    page1 = client.get("/api/rides?limit=3&offset=0")
    page3 = client.get("/api/rides?limit=3&offset=6")
    assert len(page1.json()) == 3 and len(page3.json()) == 1 and page1.headers["X-Total-Count"] == "7"
    newest_first = [r["distance_km"] for r in page1.json()]
    assert newest_first == [7, 6, 5]
    assert client.get("/api/rides?limit=0").status_code == 422
    assert client.get("/api/rides?limit=500").status_code == 422


def test_etag_conditional_get(client):
    first = client.get("/api/rides")
    tag = first.headers["ETag"]
    again = client.get("/api/rides", headers={"If-None-Match": tag})
    assert again.status_code == 304 and again.content == b""
    client.post("/api/rides", json=sample())
    changed = client.get("/api/rides", headers={"If-None-Match": tag})
    assert changed.status_code == 200 and changed.headers["ETag"] != tag


# ---------------------------------------------------------------- validation
@pytest.mark.parametrize("bad, field", [
    (sample(distance_km=-5), "distance_km"),
    (sample(distance_km=0), "distance_km"),
    (sample(distance_km="far"), "distance_km"),
    (sample(pickup="   "), "pickup"),
    (sample(passenger=""), "passenger"),
    (sample(request_key="short"), "request_key"),
    ({k: v for k, v in sample().items() if k != "destination"}, "destination"),
])
def test_422_names_the_bad_field(client, bad, field):
    response = client.post("/api/rides", json=bad)
    assert response.status_code == 422
    assert any(field in err["loc"] for err in response.json()["detail"])


def test_same_pickup_and_destination_rejected(client):
    response = client.post("/api/rides", json=sample(destination=" ucc "))
    assert response.status_code == 422 and "differ" in response.text


def test_whitespace_is_stripped(client):
    ride = client.post("/api/rides", json=sample(passenger="  Student  ")).json()
    assert ride["passenger"] == "Student"


# ---------------------------------------------------------------- idempotency
def test_idempotent_retry_and_conflict(client):
    first = client.post("/api/rides", json=sample())
    again = client.post("/api/rides", json=sample())
    assert (first.status_code, again.status_code) == (201, 200)
    assert first.json()["id"] == again.json()["id"]
    conflict = client.post("/api/rides", json={**sample(), "pickup": "Airport"})
    assert conflict.status_code == 409
    assert client.get("/api/rides").headers["X-Total-Count"] == "1"


def test_concurrent_retries_create_one_row(client):
    codes = []

    def post():
        codes.append(client.post("/api/rides", json=sample()).status_code)

    threads = [threading.Thread(target=post) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert codes.count(201) == 1 and set(codes) <= {200, 201, 409}
    assert client.get("/api/rides").headers["X-Total-Count"] == "1"


# ---------------------------------------------------------------- SQL safety
def test_sql_injection_text_is_stored_as_data(client):
    attack = sample(key="injection-safe-123", pickup="x'); DROP TABLE rides; --")
    assert client.post("/api/rides", json=attack).status_code == 201
    rides = client.get("/api/rides").json()
    assert rides[0]["pickup"] == "x'); DROP TABLE rides; --"


# ---------------------------------------------------------------- state machine, drivers, joins
def test_full_lifecycle_with_driver_join(client):
    rid = client.post("/api/rides", json=sample()).json()["id"]
    ava = driver_id(client, "Ava")
    assert client.patch(f"/api/rides/{rid}", json={"status": "completed"}).status_code == 409
    assert client.patch(f"/api/rides/{rid}", json={"status": "assigned"}).status_code == 422   # no driver
    assigned = client.patch(f"/api/rides/{rid}", json={"status": "assigned", "driver_id": ava})
    assert assigned.status_code == 200 and assigned.json()["driver_name"] == "Ava"
    assert client.delete(f"/api/rides/{rid}").status_code == 409
    assert client.patch(f"/api/rides/{rid}", json={"status": "completed"}).status_code == 200
    assert client.patch(f"/api/rides/{rid}", json={"status": "requested"}).status_code == 409
    assert client.get(f"/api/rides/{rid}").json()["status"] == "completed"
    assert client.patch(f"/api/rides/{rid}", json={"status": "flying"}).status_code == 422


def test_assign_rejects_missing_or_offline_driver(client):
    rid = client.post("/api/rides", json=sample()).json()["id"]
    assert client.patch(f"/api/rides/{rid}", json={"status": "assigned", "driver_id": 999}).status_code == 404
    orla = driver_id(client, "Orla")                                   # seeded offline
    assert client.patch(f"/api/rides/{rid}", json={"status": "assigned", "driver_id": orla}).status_code == 409


def test_cancel_and_delete(client):
    rid = client.post("/api/rides", json=sample()).json()["id"]
    assert client.patch(f"/api/rides/{rid}", json={"status": "cancelled"}).status_code == 200
    deleted = client.delete(f"/api/rides/{rid}")
    assert deleted.status_code == 204 and deleted.content == b""
    assert client.get(f"/api/rides/{rid}").status_code == 404
    assert client.delete(f"/api/rides/{rid}").status_code == 404


def test_drivers_crud_and_unique_name(client):
    assert len(client.get("/api/drivers").json()) == 4
    assert {d["name"] for d in client.get("/api/drivers?online=false").json()} == {"Orla"}
    created = client.post("/api/drivers", json={"name": "Niamh", "zone": "City Centre", "rating": 4.8})
    assert created.status_code == 201 and created.json()["online"] == 1
    assert client.post("/api/drivers", json={"name": "Niamh", "zone": "X", "rating": 4}).status_code == 409
    assert client.post("/api/drivers", json={"name": "Bad", "zone": "X", "rating": 6}).status_code == 422


def test_foreign_key_is_enforced_by_sqlite(client):
    path = client.app.state.db_path
    db = sqlite3.connect(path)
    db.execute("PRAGMA foreign_keys=ON")
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("""INSERT INTO rides(id, passenger, pickup, destination, distance_km, fare_cents,
                      status, request_key, driver_id) VALUES('x','p','a','b',1,400,'assigned','fk-test-key',999)""")
    db.close()


def test_stats_group_by(client):
    ava = driver_id(client, "Ava")
    for i in range(3):
        rid = client.post("/api/rides", json=sample(key=f"stats-key-{i:03}")).json()["id"]
        if i < 2:
            client.patch(f"/api/rides/{rid}", json={"status": "assigned", "driver_id": ava})
    stats = client.get("/api/stats").json()
    assert {s["status"]: s["rides"] for s in stats["by_status"]} == {"assigned": 2, "requested": 1}
    assert stats["by_driver"] == [{"name": "Ava", "rides": 2}]


# ---------------------------------------------------------------- HTTP semantics
def test_method_not_allowed_and_not_found(client):
    assert client.delete("/api/rides").status_code == 405
    assert client.get("/api/nothing-here").status_code == 404


def test_cors_preflight(client):
    allowed = client.options("/api/rides", headers={"Origin": "http://localhost:5173",
                                                    "Access-Control-Request-Method": "POST"})
    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:5173"
    blocked = client.options("/api/rides", headers={"Origin": "https://evil.example",
                                                    "Access-Control-Request-Method": "POST"})
    assert blocked.status_code == 400 and "access-control-allow-origin" not in blocked.headers


def test_fare_rounding():
    assert fare_cents(1) == 400 and fare_cents(4.5) == 925 and fare_cents(0.1) == 265
