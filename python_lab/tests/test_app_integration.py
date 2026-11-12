"""Integration tests for python_lab/app_integration.py.

Each test starts the whole stack (SQLite + service + HTTP server + client + screen) on a
random local port, clicks buttons, and checks both what the screen shows and what the
database holds.

    python -m pytest -q python_lab/tests
"""
import importlib.util
import sys
from collections import deque
from pathlib import Path

import pytest

_path = Path(__file__).resolve().parents[1] / "app_integration.py"
_spec = importlib.util.spec_from_file_location("app_integration", _path)
ai = importlib.util.module_from_spec(_spec)
sys.modules["app_integration"] = ai
_spec.loader.exec_module(ai)

GOOD = {"passenger": "Aoife", "pickup": "UCC", "destination": "Cork Airport", "distance_km": 5.8}


@pytest.fixture
def app():
    with ai.App(drivers=3, rides=5) as running:
        yield running


def book(app, **form):
    app.screen.form.update({"passenger": "Aoife", "pickup": "UCC", "destination": "Cork Airport", "km": "5.8",
                            **form})
    future = app.screen.book_button.click()
    return future.result() if future else None


# ---- button -> API -> database -> screen ---------------------------------------
def test_load_button_shows_database_rows(app):
    resp = app.screen.load_button.click()
    assert resp.status == 200 and resp.headers["X-Total-Count"] == "5"
    db_ids = [r["id"] for r in app.db.query("SELECT id FROM rides ORDER BY id DESC")]
    assert [r["id"] for r in app.screen.table] == db_ids


def test_click_trace_reaches_database_and_returns(app):
    app.trace.clear()
    app.screen.load_button.click()
    layers = [layer for _, layer, _ in app.trace.hops]
    assert layers[0] == "UI button" and "database" in layers and layers[-1] == "event handler"


def test_book_inserts_one_row_and_renders_it(app):
    resp = book(app, passenger="Brian")
    assert resp.status == 201 and resp.body["fare_cents"] == ai.fare_cents(5.8)
    stored = app.service.get_ride(resp.body["id"])
    assert stored["passenger"] == "Brian" and app.screen.table[0]["id"] == stored["id"]
    assert app.screen.form["passenger"] == "" and app.screen.banner.startswith("Booked")


def test_form_errors_send_no_request(app):
    before = app.client.requests
    assert book(app, passenger="  ", km="ten") is None
    assert app.client.requests == before and "passenger" in app.screen.banner
    assert app.db.count("rides") == 5


@pytest.mark.parametrize("change, field", [
    ({"passenger": "X" * 41}, "passenger"), ({"distance_km": 0}, "distance_km"),
    ({"distance_km": True}, "distance_km"), ({"destination": "UCC"}, "destination"),
    ({"pickup": "Atlantis"}, "pickup"),
])
def test_api_rejects_bad_bookings_with_field(app, change, field):
    resp = app.client.post("/api/rides", {**GOOD, **change})
    assert resp.status == 422 and resp.body["field"] == field
    assert app.db.count("rides") == 5


def test_missing_driver_is_caught_by_foreign_key(app):
    resp = app.client.post("/api/rides", {**GOOD, "driver_id": 999})
    assert resp.status == 409 and "FOREIGN KEY" in resp.body["error"]


def test_malformed_json_and_unknown_routes(app):
    import urllib.error
    import urllib.request
    req = urllib.request.Request(app.server.url + "/api/rides", data=b"{not json", method="POST",
                                 headers={"Content-Type": "application/json"})
    with pytest.raises(urllib.error.HTTPError) as err:
        app.client._opener.open(req, timeout=3)
    assert err.value.code == 422
    assert app.client.get("/api/nope").status == 404
    assert app.client.request("DELETE", "/api/stats").status == 405
    assert app.client.get("/api/rides?limit=0").status == 422


# ---- idempotency, pagination, concurrency ----------------------------------------
def test_double_click_creates_one_ride(app):
    app.server.faults["/api/rides"] = deque(["delay:0.1", "delay:0.1"])
    app.screen.form.update(passenger="Zoe Double")
    app.screen.book_button.click()
    assert app.screen.book_button.click() is None          # disabled while in flight
    app.screen.wait()
    assert app.db.count("rides", "passenger = 'Zoe Double'") == 1


def test_idempotency_key_replays_first_ride(app):
    headers = {"Idempotency-Key": "abc123"}
    first = app.client.post("/api/rides", GOOD, headers=headers)
    second = app.client.post("/api/rides", GOOD, headers=headers)
    assert (first.status, second.status) == (201, 200) and first.body["id"] == second.body["id"]
    assert second.headers["Idempotent-Replay"] == "true"


def test_keyset_pagination_never_repeats_rows():
    with ai.App(drivers=1, rides=25, page_size=10, pagination="keyset") as app:
        app.screen.load_button.click()
        app.client.post("/api/rides", GOOD)                  # inserted between pages
        while app.screen.more_button.enabled:
            app.screen.more_button.click()
        ids = [r["id"] for r in app.screen.table]
        assert len(ids) == len(set(ids)) == 25


def test_version_check_prevents_lost_update(app):
    alice, bob = app.screen, ai.RideScreen(app.client, app.trace)
    alice.open_button.click(1)
    bob.open_button.click(1)
    alice.editing["passenger"] = "Alice edit"
    assert alice.save_button.click().status == 200
    bob.editing["passenger"] = "Bob edit"
    assert bob.save_button.click().status == 409
    assert app.service.get_ride(1)["passenger"] == "Alice edit"
    bob.close()


# ---- transactions, queries, cache, errors ----------------------------------------
def test_crash_inside_transaction_rolls_back(app):
    app.service.crash_assign_ids = {2}
    assert app.screen.assign_button.click(2, 1).status == 500
    assert app.service.get_ride(2)["status"] == "requested"
    assert app.db.count("drivers", "busy = 1") == 0 and app.db.count("audit") == 0
    assert "Reference" in app.screen.banner and "Traceback" not in app.screen.banner


def test_busy_driver_cannot_be_assigned_twice(app):
    assert app.screen.assign_button.click(1, 1).status == 200
    assert app.screen.assign_button.click(2, 1).status == 409


def test_join_uses_one_query_and_matches_n_plus_1():
    with ai.App(drivers=3, rides=12, assigned=True) as app:
        mark = len(app.db.statements)
        joined = app.client.get("/api/rides-with-drivers?strategy=join").body
        assert app.db.selects_since(mark) == 1
        assert joined == app.client.get("/api/rides-with-drivers?strategy=n_plus_1").body


def test_stats_cache_is_invalidated_by_a_booking(app):
    app.service.stats_cache = "invalidate-on-write"
    app.screen.stats_button.click()
    book(app, passenger="Darragh")
    app.screen.stats_button.click()
    assert app.screen.stats["total_rides"] == 6 and app.screen.stats["cached"] is False


def test_search_escapes_like_wildcards(app):
    assert app.screen.search_button.click("%").body["total"] == 0
    assert app.screen.search_button.click("Aoife").body["total"] >= 1


def test_retry_policy_retries_503_but_not_500(app):
    app.server.faults["/api/stats"] = deque([503, 503])
    assert app.screen.refresh_button.click().attempts == 3
    app.server.faults["/api/stats"] = deque([500])
    resp = app.screen.refresh_button.click()
    assert resp.status == 500 and resp.attempts == 1


def test_server_down_shows_friendly_message():
    with ai.App(drivers=1, base_url=f"http://127.0.0.1:{ai.unused_port()}", retries=1) as app:
        out = app.screen.refresh_button.click()
        assert isinstance(out, ai.NetworkError) and out.attempts == 2
        assert app.screen.banner.startswith("Cannot reach the server")


@pytest.mark.parametrize("number", sorted(ai.LABS))
def test_every_lab_runs(number):
    res = ai.experiment(number)
    assert res["rows"] and all(len(r) == len(res["labels"]) + 1 for r in res["rows"])
