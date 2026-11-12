"""T02 - Available-drivers dropdown (8 points). See TICKETS.md#t02."""
import pytest
from conftest import book


@pytest.fixture
def app(make_app, impl):
    app = make_app(drivers=5, rides=3, offline=(1,))     # driver 2 (Oisin) offline
    impl.install_t02(app)
    return app


def test_ac1_lists_only_online_and_free_drivers_sorted_by_name(app):
    app.client.post("/api/rides/1/assign", {"driver_id": 3})            # Padraig busy
    resp = app.client.get("/api/drivers/available")
    assert resp.status == 200
    assert resp.body == [{"id": 1, "name": "Niamh"}, {"id": 4, "name": "Roisin"}, {"id": 5, "name": "Sean"}]


def test_ac2_uses_exactly_one_select(app):
    mark = len(app.db.statements)
    app.client.get("/api/drivers/available")
    assert app.db.selects_since(mark) == 1


def test_ac3_driver_returns_after_completing_ride(app):
    app.client.post("/api/rides/1/assign", {"driver_id": 1})
    assert 1 not in [d["id"] for d in app.client.get("/api/drivers/available").body]
    app.client.post("/api/rides/1/complete")
    assert 1 in [d["id"] for d in app.client.get("/api/drivers/available").body]


def test_ac4_screen_fills_dropdown_and_preselects_first(app):
    s = app.screen
    s.available_button.click()
    assert s.driver_options == [(1, "Niamh"), (3, "Padraig"), (4, "Roisin"), (5, "Sean")]
    assert s.selected_driver == 1


def test_ac5_assign_selected_uses_choice_and_refreshes_dropdown(app):
    s = app.screen
    s.available_button.click()
    s.selected_driver = 4
    resp = s.assign_selected_button.click(2)
    assert resp.status == 200 and app.service.get_ride(2)["driver_id"] == 4
    assert 4 not in [d for d, _ in s.driver_options]                   # refreshed after assigning
    assert s.selected_driver in [d for d, _ in s.driver_options]


def test_ac6_no_drivers_means_no_request(app):
    s = app.screen
    for ride_id, driver in zip((1, 2, 3), (1, 3, 4)):
        app.client.post(f"/api/rides/{ride_id}/assign", {"driver_id": driver})
    ride = book(app).body["id"]
    app.client.post(f"/api/rides/{ride}/assign", {"driver_id": 5})
    s.available_button.click()
    assert s.driver_options == [] and s.selected_driver is None
    before = app.client.requests
    assert s.assign_selected_button.click(book(app).body["id"]) is None
    assert app.client.requests == before + 1                            # only the book() above
    assert s.banner == "No drivers available"
