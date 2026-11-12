"""T07 - Schema migration and ratings (12 points). See TICKETS.md#t07."""
import sqlite3
import threading

import pytest


@pytest.fixture
def app(make_app, impl):
    app = make_app(drivers=2, rides=4)
    impl.install_t07(app)
    return app


def complete(app, ride_id, driver_id=1):
    assert app.client.post(f"/api/rides/{ride_id}/assign", {"driver_id": driver_id}).status == 200
    assert app.client.post(f"/api/rides/{ride_id}/complete").status == 200


def user_version(app):
    return app.db.conn.execute("PRAGMA user_version").fetchone()[0]


def test_ac1_migration_runs_once_and_records_version(make_app, impl):
    app = make_app(drivers=1, rides=3)
    before = app.db.query("SELECT id, passenger, fare_cents FROM rides ORDER BY id")
    assert impl.migrate(app.db) == len(impl.MIGRATIONS) >= 1
    assert user_version(app) == len(impl.MIGRATIONS)
    assert impl.migrate(app.db) == 0                                    # idempotent
    assert app.db.query("SELECT id, passenger, fare_cents FROM rides ORDER BY id") == before
    assert "rating" in [c[1] for c in app.db.conn.execute("PRAGMA table_info(rides)")]


def test_ac2_failed_migration_rolls_back_and_keeps_version(make_app, impl):
    app = make_app(drivers=1)
    steps = ["ALTER TABLE drivers ADD COLUMN phone TEXT", "THIS IS NOT SQL"]
    with pytest.raises(sqlite3.Error):
        impl.migrate(app.db, steps)
    assert user_version(app) == 1
    assert impl.migrate(app.db, steps[:1]) == 0


def test_ac3_database_rejects_out_of_range_ratings(app):
    with pytest.raises(sqlite3.IntegrityError):
        app.db.conn.execute("UPDATE rides SET rating = 9 WHERE id = 1")


def test_ac4_rate_a_completed_ride(app):
    complete(app, 1)
    resp = app.client.post("/api/rides/1/rate", {"stars": 4})
    assert resp.status == 200 and resp.body["rating"] == 4


@pytest.mark.parametrize("stars", [0, 6, 4.5, "5", True, None])
def test_ac5_stars_must_be_an_integer_from_1_to_5(app, stars):
    complete(app, 1)
    resp = app.client.post("/api/rides/1/rate", {"stars": stars})
    assert resp.status == 422 and resp.body["field"] == "stars"


def test_ac6_rating_rules_404_and_409(app):
    assert app.client.post("/api/rides/99/rate", {"stars": 5}).status == 404
    resp = app.client.post("/api/rides/2/rate", {"stars": 5})          # still requested
    assert resp.status == 409 and "completed" in resp.body["error"]
    complete(app, 1)
    assert app.client.post("/api/rides/1/rate", {"stars": 5}).status == 200
    resp = app.client.post("/api/rides/1/rate", {"stars": 1})
    assert resp.status == 409 and "already" in resp.body["error"]
    assert app.service.get_ride(1)["rating"] == 5


def test_ac7_concurrent_ratings_only_one_wins(app):
    complete(app, 1)
    statuses, lock = [], threading.Lock()

    def worker(stars):
        s = app.client.post("/api/rides/1/rate", {"stars": stars}).status
        with lock:
            statuses.append(s)

    threads = [threading.Thread(target=worker, args=(1 + i % 5,)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(statuses) == [200] + [409] * 7


def test_ac8_driver_average_rating(app):
    resp = app.client.get("/api/drivers/1/rating")
    assert resp.body == {"driver_id": 1, "average": None, "count": 0}
    for ride_id, stars in ((1, 5), (2, 4), (3, 4)):
        complete(app, ride_id)
        app.client.post(f"/api/rides/{ride_id}/rate", {"stars": stars})
    assert app.client.get("/api/drivers/1/rating").body == {"driver_id": 1, "average": 4.33, "count": 3}
    assert app.client.get("/api/drivers/42/rating").status == 404
