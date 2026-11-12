"""T03 - Accounts, login and sessions (15 points). See TICKETS.md#t03."""
import hashlib

import pytest

PASSWORD = "correct horse battery"


@pytest.fixture
def app(make_app, impl, clock):
    app = make_app(drivers=1)
    impl.install_t03(app, clock=clock)
    return app


def register(app, username="aoife", password=PASSWORD, **extra):
    return app.client.post("/api/register", {"username": username, "password": password, **extra})


def login(app, username="aoife", password=PASSWORD):
    return app.client.post("/api/login", {"username": username, "password": password})


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def test_ac1_register_creates_passenger_and_ignores_role_in_body(app):
    resp = register(app, role="dispatcher")
    assert resp.status == 201
    assert resp.body["username"] == "aoife" and resp.body["role"] == "passenger"
    assert set(resp.body) == {"id", "username", "role"}                 # never echo secrets


@pytest.mark.parametrize("username, password, field", [
    ("ab", PASSWORD, "username"), ("a" * 21, PASSWORD, "username"), ("bad name", PASSWORD, "username"),
    ("x'; DROP TABLE users;--", PASSWORD, "username"), ("aoife", "short", "password"),
    ("longusername", "LongUserName", "password"), (None, PASSWORD, "username"), ("aoife", 1234567890, "password"),
])
def test_ac2_validation_errors_name_the_field(app, username, password, field):
    resp = app.client.post("/api/register", {"username": username, "password": password})
    assert resp.status == 422 and resp.body["field"] == field


def test_ac3_duplicate_username_is_409_case_insensitive(app):
    assert register(app).status == 201
    assert register(app, username="AOIFE").status == 409
    assert app.db.count("users") == 1


def test_ac4_passwords_are_salted_pbkdf2_hashes(app, impl):
    register(app, "aoife"); register(app, "brian")
    rows = app.db.query("SELECT * FROM users ORDER BY id")
    for row in rows:
        assert all(PASSWORD not in str(v) for v in row.values())
    assert rows[0]["salt"] != rows[1]["salt"] and len(rows[0]["salt"]) >= 16
    assert impl.PBKDF2_ITERATIONS >= 100_000
    expected = hashlib.pbkdf2_hmac("sha256", PASSWORD.encode(), rows[0]["salt"], impl.PBKDF2_ITERATIONS)
    assert rows[0]["pw_hash"] == expected


def test_ac5_login_returns_token_and_me_returns_user(app):
    register(app)
    resp = login(app)
    assert resp.status == 200 and resp.body["expires_in"] == 3600 and len(resp.body["token"]) >= 32
    me = app.client.get("/api/me", headers=bearer(resp.body["token"]))
    assert me.status == 200 and me.body["username"] == "aoife" and me.body["role"] == "passenger"


def test_ac6_failed_logins_look_identical(app):
    register(app)
    wrong = login(app, password="wrong password!!")
    unknown = login(app, username="nobody")
    injection = login(app, username="' OR '1'='1' --")
    assert wrong.status == unknown.status == injection.status == 401
    assert wrong.body == unknown.body == injection.body == {"error": "invalid username or password"}


def test_ac7_tokens_are_random_and_stored_hashed(app):
    register(app)
    t1, t2 = login(app).body["token"], login(app).body["token"]
    assert t1 != t2
    stored = [r["token_hash"] for r in app.db.query("SELECT token_hash FROM sessions")]
    assert len(stored) == 2 and t1 not in stored and hashlib.sha256(t1.encode()).hexdigest() in stored


@pytest.mark.parametrize("header", [None, "Bearer", "Bearer ", "Basic abc", "Bearer not-a-real-token", "bearer x"])
def test_ac8_me_rejects_missing_or_bad_tokens_with_401(app, header):
    resp = app.client.get("/api/me", headers={"Authorization": header} if header else {})
    assert resp.status == 401 and resp.headers.get("WWW-Authenticate") == "Bearer"


def test_ac9_sessions_expire_after_one_hour(app, clock):
    register(app)
    token = login(app).body["token"]
    clock.advance(3599)
    assert app.client.get("/api/me", headers=bearer(token)).status == 200
    clock.advance(2)
    assert app.client.get("/api/me", headers=bearer(token)).status == 401


def test_ac10_logout_revokes_only_that_token(app):
    register(app)
    t1, t2 = login(app).body["token"], login(app).body["token"]
    assert app.client.post("/api/logout", headers=bearer(t1)).status == 204
    assert app.client.get("/api/me", headers=bearer(t1)).status == 401
    assert app.client.get("/api/me", headers=bearer(t2)).status == 200


def test_ac11_create_user_helper_can_make_a_dispatcher(app, impl):
    user = impl.create_user(app, "dispatch1", PASSWORD, role="dispatcher")
    assert user["role"] == "dispatcher"
    token = login(app, "dispatch1").body["token"]
    assert app.client.get("/api/me", headers=bearer(token)).body["role"] == "dispatcher"


def test_ac12_screen_sign_in_and_out(app):
    register(app)
    s = app.screen
    assert s.login_button.click("aoife", "nope nope nope").status == 401
    assert s.banner == "Invalid username or password" and "Authorization" not in app.client.default_headers
    assert s.login_button.click("aoife", PASSWORD).status == 200
    assert s.banner == "Signed in as aoife" and s.user["username"] == "aoife"
    assert app.client.get("/api/me").status == 200                       # header sent automatically
    s.logout_button.click()
    assert "Authorization" not in app.client.default_headers and s.user is None
    assert app.db.count("sessions") == 0
