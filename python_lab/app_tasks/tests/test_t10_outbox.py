"""T10 - Transactional outbox and a delivery worker (9 points). See TICKETS.md#t10."""
import json

import pytest
from conftest import book


@pytest.fixture
def app(make_app, impl):
    app = make_app(drivers=2)
    impl.install_t10(app)
    return app


def outbox(app):
    return app.db.query("SELECT * FROM outbox ORDER BY id")


def test_ac1_every_write_records_an_event(app):
    ride = book(app).body["id"]
    app.client.post(f"/api/rides/{ride}/assign", {"driver_id": 1})
    app.client.post(f"/api/rides/{ride}/complete")
    other = book(app, passenger="Brian").body["id"]
    app.client.post(f"/api/rides/{other}/cancel")
    assert [(e["event"], e["ride_id"], e["status"]) for e in outbox(app)] == [
        ("ride.created", ride, "pending"), ("ride.assigned", ride, "pending"), ("ride.completed", ride, "pending"),
        ("ride.created", other, "pending"), ("ride.cancelled", other, "pending")]


def test_ac2_payload_is_json_snapshot_of_the_ride(app):
    ride = book(app).body
    payload = json.loads(outbox(app)[0]["payload"])
    assert payload == {"id": ride["id"], "status": "requested", "passenger": "Aoife",
                       "fare_cents": ride["fare_cents"], "driver_id": None}


def test_ac3_event_is_written_in_the_same_transaction(app):
    def explode(db, event, ride):
        raise RuntimeError("later hook fails")

    app.service.write_hooks.append(explode)
    assert book(app).status == 500
    assert app.db.count("rides") == 0 and outbox(app) == []           # both rolled back
    app.service.write_hooks.remove(explode)
    ride = book(app).body["id"]
    app.service.crash_assign_ids = {ride}
    assert app.client.post(f"/api/rides/{ride}/assign", {"driver_id": 1}).status == 500
    assert [e["event"] for e in outbox(app)] == ["ride.created"]       # no ride.assigned


def test_ac4_worker_delivers_in_order_exactly_once(app, impl):
    for name in ("A1", "B2", "C3"):
        book(app, passenger=name)
    sent = []
    assert impl.deliver_outbox(app, sent.append) == {"delivered": 3, "failed": 0, "dead": 0}
    assert [e["payload"]["passenger"] for e in sent] == ["A1", "B2", "C3"]
    assert [e["id"] for e in sent] == [r["id"] for r in outbox(app)]
    assert set(sent[0]) == {"id", "event", "ride_id", "payload"}
    assert impl.deliver_outbox(app, sent.append) == {"delivered": 0, "failed": 0, "dead": 0}
    assert len(sent) == 3 and all(r["status"] == "delivered" for r in outbox(app))


def test_ac5_failures_are_retried_later_and_recorded(app, impl):
    book(app); book(app, passenger="Brian")
    calls = []

    def flaky(event):
        calls.append(event["id"])
        if event["payload"]["passenger"] == "Brian" and calls.count(event["id"]) == 1:
            raise ConnectionError("webhook timed out")

    assert impl.deliver_outbox(app, flaky) == {"delivered": 1, "failed": 1, "dead": 0}
    row = outbox(app)[1]
    assert row["status"] == "pending" and row["attempts"] == 1 and "timed out" in row["last_error"]
    assert impl.deliver_outbox(app, flaky) == {"delivered": 1, "failed": 0, "dead": 0}
    assert [r["status"] for r in outbox(app)] == ["delivered", "delivered"]


def test_ac6_gives_up_after_max_attempts(app, impl):
    book(app)

    def down(event):
        raise ConnectionError("down")

    results = [impl.deliver_outbox(app, down, max_attempts=3) for _ in range(4)]
    assert results[:3] == [{"delivered": 0, "failed": 1, "dead": 0}] * 2 + [{"delivered": 0, "failed": 0, "dead": 1}]
    assert results[3] == {"delivered": 0, "failed": 0, "dead": 0}
    assert outbox(app)[0]["status"] == "dead" and outbox(app)[0]["attempts"] == 3


def test_ac7_installing_twice_does_not_duplicate_events(app, impl):
    impl.install_t10(app)                                               # e.g. a second app start-up
    book(app)
    assert app.db.count("outbox") == 1
