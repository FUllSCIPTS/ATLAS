"""T04 - Protect the API with roles (12 points). Needs T03. See TICKETS.md#t04."""
import pytest
from conftest import GOOD_RIDE

PASSWORD = "correct horse battery"


@pytest.fixture
def app(make_app, impl, clock):
    app = make_app(drivers=2, rides=2)
    impl.install_t03(app, clock=clock)
    impl.install_t04(app)
    impl.create_user(app, "dispatch1", PASSWORD, role="dispatcher")
    impl.create_user(app, "aoife", PASSWORD)
    return app


def token(app, username):
    resp = app.client.post("/api/login", {"username": username, "password": PASSWORD})
    assert resp.status == 200, resp.body
    return {"Authorization": f"Bearer {resp.body['token']}"}


PROTECTED = [("GET", "/api/rides"), ("GET", "/api/rides/1"), ("POST", "/api/rides"), ("GET", "/api/drivers"),
             ("GET", "/api/stats"), ("POST", "/api/rides/1/assign"), ("POST", "/api/rides/1/cancel"),
             ("GET", "/api/me"), ("PATCH", "/api/rides/1")]


@pytest.mark.parametrize("method, path", PROTECTED)
def test_ac1_protected_routes_need_a_token(app, method, path):
    resp = app.client.request(method, path, {"driver_id": 1} if method != "GET" else None)
    assert resp.status == 401 and resp.headers.get("WWW-Authenticate") == "Bearer"


@pytest.mark.parametrize("method, path", [("GET", "/api/health"), ("GET", "/")])
def test_ac2_public_routes_stay_open(app, method, path):
    assert app.client.request(method, path).status == 200
    assert app.client.post("/api/register", {"username": "newbie", "password": PASSWORD}).status == 201


@pytest.mark.parametrize("method, path, body", [
    ("POST", "/api/rides/1/assign", {"driver_id": 1}), ("POST", "/api/rides/1/complete", None),
    ("GET", "/api/stats", None)])
def test_ac3_passengers_get_403_on_dispatcher_routes(app, method, path, body):
    before = app.db.query("SELECT status, driver_id FROM rides ORDER BY id")
    resp = app.client.request(method, path, body, headers=token(app, "aoife"))
    assert resp.status == 403
    assert app.db.query("SELECT status, driver_id FROM rides ORDER BY id") == before


def test_ac4_dispatchers_can_assign_and_complete(app):
    h = token(app, "dispatch1")
    assert app.client.post("/api/rides/1/assign", {"driver_id": 1}, headers=h).status == 200
    assert app.client.post("/api/rides/1/complete", headers=h).status == 200
    assert app.client.get("/api/stats", headers=h).status == 200


def test_ac5_passengers_always_book_in_their_own_name(app):
    resp = app.client.post("/api/rides", {**GOOD_RIDE, "passenger": "Somebody Else"}, headers=token(app, "aoife"))
    assert resp.status == 201 and resp.body["passenger"] == "aoife"
    resp = app.client.post("/api/rides", {**GOOD_RIDE, "passenger": "Walk-in"}, headers=token(app, "dispatch1"))
    assert resp.body["passenger"] == "Walk-in"                          # dispatchers book for others


def test_ac6_logged_out_token_is_rejected(app):
    h = token(app, "aoife")
    assert app.client.post("/api/logout", headers=h).status == 204
    assert app.client.get("/api/rides", headers=h).status == 401


def test_ac7_role_is_checked_on_every_request(app):
    h = token(app, "dispatch1")
    assert app.client.get("/api/stats", headers=h).status == 200
    app.db.execute("UPDATE users SET role = 'passenger' WHERE username = 'dispatch1'")   # demoted
    assert app.client.get("/api/stats", headers=h).status == 403


def test_ac8_screen_shows_sign_in_and_permission_messages(app):
    s = app.screen
    s.load_button.click()
    assert s.banner == "Please sign in."
    s.login_button.click("aoife", PASSWORD)
    assert s.assign_button.click(1, 1).status == 403
    assert s.banner == "You are not allowed to do that."
