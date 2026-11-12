"""T01 - Delete a cancelled ride (8 points). See TICKETS.md#t01."""
import pytest
from conftest import book


@pytest.fixture
def app(make_app, impl):
    app = make_app(drivers=2, rides=3)
    impl.install_t01(app)
    return app


def cancelled_ride(app):
    ride = book(app).body
    assert app.client.post(f"/api/rides/{ride['id']}/cancel").status == 200      # writes an audit row
    return ride["id"]


def test_ac1_delete_cancelled_ride_returns_204_and_removes_row_and_audit(app):
    ride_id = cancelled_ride(app)
    assert app.db.count("audit", f"ride_id = {ride_id}") == 1
    resp = app.client.request("DELETE", f"/api/rides/{ride_id}")
    assert resp.status == 204 and resp.body is None
    assert app.db.count("rides", f"id = {ride_id}") == 0
    assert app.db.count("audit", f"ride_id = {ride_id}") == 0
    assert app.client.get(f"/api/rides/{ride_id}").status == 404


def test_ac2_missing_ride_is_404(app):
    assert app.client.request("DELETE", "/api/rides/9999").status == 404


@pytest.mark.parametrize("status", ["requested", "assigned", "completed"])
def test_ac3_only_cancelled_rides_can_be_deleted(app, status):
    ride_id = book(app).body["id"]
    if status != "requested":
        app.client.post(f"/api/rides/{ride_id}/assign", {"driver_id": 1})
    if status == "completed":
        app.client.post(f"/api/rides/{ride_id}/complete")
    assert app.service.get_ride(ride_id)["status"] == status
    resp = app.client.request("DELETE", f"/api/rides/{ride_id}")
    assert resp.status == 409 and "cancelled" in resp.body["error"]
    assert app.service.get_ride(ride_id)["status"] == status           # unchanged


def test_ac4_second_delete_is_404(app):
    ride_id = cancelled_ride(app)
    assert app.client.request("DELETE", f"/api/rides/{ride_id}").status == 204
    assert app.client.request("DELETE", f"/api/rides/{ride_id}").status == 404


def test_ac5_screen_removes_row_only_after_204(app):
    s = app.screen
    ride_id = cancelled_ride(app)
    s.load_button.click()
    assert any(r["id"] == ride_id for r in s.table)
    resp = s.delete_button.click(ride_id)
    assert resp.status == 204 and all(r["id"] != ride_id for r in s.table)
    assert s.banner == f"Deleted ride {ride_id}"


def test_ac6_screen_keeps_row_and_explains_409(app):
    s = app.screen
    s.load_button.click()
    keep = s.table[0]["id"]                                             # a requested ride
    resp = s.delete_button.click(keep)
    assert resp.status == 409 and any(r["id"] == keep for r in s.table)
    assert s.banner.startswith("Not saved") and "cancelled" in s.banner


def test_ac7_delete_is_atomic_and_never_500(app):
    ride_id = cancelled_ride(app)
    app.db.execute("INSERT INTO audit (ride_id, action) VALUES (?, 'note')", (ride_id,))   # several children
    assert app.client.request("DELETE", f"/api/rides/{ride_id}").status == 204
    assert not [e for e in app.server.log if e[0] == "ERROR"]
