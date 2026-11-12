"""T05 - Rate-limit bookings (10 points). See TICKETS.md#t05."""
import threading

import pytest
from conftest import GOOD_RIDE, book


@pytest.fixture
def app(make_app, impl, clock):
    app = make_app(drivers=1)
    impl.install_t05(app, limit=5, window=60.0, clock=clock)
    return app


def test_ac1_sixth_booking_in_a_minute_gets_429_with_retry_after(app):
    assert [book(app).status for _ in range(5)] == [201] * 5
    resp = book(app)
    assert resp.status == 429 and resp.headers["Retry-After"] == "60" and resp.body["retry_after"] == 60
    assert app.db.count("rides") == 5


def test_ac2_retry_after_counts_down_and_window_slides(app, clock):
    for _ in range(5):
        book(app); clock.advance(10)                      # bookings at t = 0, 10, 20, 30, 40
    clock.advance(5)                                      # t = 55
    assert book(app).headers["Retry-After"] == "5"       # oldest (t=0) leaves the window at t=60
    clock.advance(5)                                      # t = 60
    assert book(app).status == 201
    assert book(app).status == 429                       # the t=10 booking is still inside


def test_ac3_each_client_has_its_own_limit(app):
    for _ in range(5):
        book(app)
    other = {"Authorization": "Bearer someone-else"}
    assert app.client.post("/api/rides", GOOD_RIDE, headers=other).status == 201
    assert book(app).status == 429


def test_ac4_only_post_rides_is_limited(app):
    for _ in range(6):
        book(app)
    assert all(app.client.get("/api/rides").status == 200 for _ in range(10))
    assert app.client.post("/api/rides/1/cancel").status == 200


def test_ac5_invalid_attempts_count_but_refused_ones_do_not(app, clock):
    for _ in range(5):
        assert book(app, distance_km=-1).status == 422     # attempts count, even invalid ones
    assert book(app).status == 429
    clock.advance(30)
    for _ in range(3):
        assert book(app).status == 429                     # refusals do not extend the window
    clock.advance(30)
    assert book(app).status == 201


def test_ac6_limit_holds_under_concurrency(app):
    results, lock = [], threading.Lock()

    def worker():
        status = book(app).status
        with lock:
            results.append(status)

    threads = [threading.Thread(target=worker) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert results.count(201) == 5 and results.count(429) == 15
    assert app.db.count("rides") == 5


def test_ac7_screen_tells_the_user_how_long_to_wait(app, clock):
    s = app.screen
    s.form.update(passenger="Aoife", pickup="UCC", destination="Douglas", km="3")
    for i in range(6):
        s.form["passenger"] = f"P{i}"
        resp = s.book_button.click().result()
    assert resp.status == 429 and s.banner == "Too many requests - try again in 60 s."
