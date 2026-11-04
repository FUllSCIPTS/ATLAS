import json
import os
import time

import httpx

from ml.registry import write_json
from packages.config import CONSUMER_GROUP, DATA, TOPIC
from packages.db import database, emit, envelope

MODEL_URL = os.getenv("ATLAS_MODEL_URL", "http://127.0.0.1:8003")
BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP")
USE_POLICY = os.getenv("ATLAS_POLICY_ENABLED", "0") == "1"
BUCKET_SECONDS = 300


def choose(candidates, zone):
    scores = {}
    details = {"bucket": 0, "action": 0, "policy_version": "baseline", "model_version": "fallback", "forecast": None}
    try:
        response = httpx.post(MODEL_URL + "/internal/v1/score", timeout=3, trust_env=False,
                              json={"zone": zone, "drivers": [dict(row) for row in candidates]})
        response.raise_for_status()
        result = response.json()
        scores = {row["driver_id"]: row for row in result["drivers"]}
        details.update({key: result[key] for key in ("bucket", "model_version", "forecast")})
        if USE_POLICY:
            details.update({key: result[key] for key in ("action", "policy_version")})
    except (httpx.HTTPError, ValueError, KeyError, TypeError) as error:
        print(f"Scorer fallback: {type(error).__name__}", flush=True)
        scores.clear()
    if details["action"] == 1:
        driver = min(candidates, key=lambda d: (-scores.get(d["driver_id"], {}).get("acceptance", 0),
                                               d["distance_km"], d["driver_id"]))
    else:
        driver = min(candidates, key=lambda d: (d["distance_km"], d["driver_id"]))
    chosen = scores.get(driver["driver_id"], {})
    return driver["driver_id"], details, chosen


def apply(event):
    trip_id = event["trip_id"]
    kind = event["type"]
    body = event["data"]
    if event["schema_version"] != 1:
        raise ValueError("Unexpected event schema version")
    with database() as db:
        inserted = db.run("INSERT INTO inbox VALUES (?) ON CONFLICT DO NOTHING", event["event_id"]).rowcount
        if not inserted:
            return
        if kind == "trip.requested":
            candidates = db.run("SELECT id AS driver_id, distance_km, speed_kph FROM drivers "
                                "WHERE online=1 AND active_trip IS NULL ORDER BY distance_km, id LIMIT 20").fetchall()
            if candidates:
                driver, details, chosen = choose(candidates, body["zone"])
                offered = db.run("INSERT INTO offers VALUES (?, ?, 'offered', ?, ?, ?, ?, ?, ?, ?) "
                                 "ON CONFLICT DO NOTHING", trip_id, driver, details["action"], details["bucket"],
                                 details["policy_version"], details["model_version"], details["forecast"],
                                 chosen.get("acceptance"),
                                 int(chosen["anomaly_flag"]) if "anomaly_flag" in chosen else None).rowcount
                if offered:
                    emit(db, trip_id, "dispatch.offer.created", driver_id=driver)
        elif kind == "dispatch.assignment.confirmed":
            assigned = db.run("UPDATE trips SET status='assigned', driver_id=? WHERE id=? AND status='requested'",
                              body["driver_id"], trip_id).rowcount
            if assigned:
                emit(db, trip_id, "trip.assigned", driver_id=body["driver_id"])
        elif kind == "trip.completed":
            offer = db.run("SELECT bucket, action, policy_version FROM offers WHERE trip_id=?", trip_id).fetchone()
            if offer:
                reward = max(-1.0, 1.0 - body["elapsed_s"] / 600.0)
                db.run("INSERT INTO experience VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT DO NOTHING",
                       trip_id, offer["bucket"], offer["action"], reward, offer["policy_version"], event["occurred_at"])


def update_features():
    current_bucket = int(time.time()) // BUCKET_SECONDS
    counts = {"cork-centre": [0] * 12, "cork-north": [0] * 12}
    with database() as db:
        rows = db.run("SELECT o.occurred_at, t.zone FROM outbox o JOIN inbox i ON o.event_id=i.event_id "
                      "JOIN trips t ON o.trip_id=t.id WHERE o.event_type='trip.requested' AND o.occurred_at>=?",
                      (current_bucket - 11) * BUCKET_SECONDS).fetchall()
    for row in rows:
        index = row["occurred_at"] // BUCKET_SECONDS - current_bucket + 11
        if 0 <= index < 12:
            counts[row["zone"]][index] += 1
    write_json(DATA / "demand.json", counts)


def next_event():
    with database() as db:
        row = db.run("SELECT * FROM outbox WHERE sent=0 ORDER BY seq LIMIT 1").fetchone()
        return envelope(row) if row else None


def mark_sent(event):
    with database() as db:
        db.run("UPDATE outbox SET sent=1 WHERE event_id=?", event["event_id"])


def local_tick():
    if event := next_event():
        apply(event)
        if event["type"] == "trip.requested":
            update_features()
        mark_sent(event)
        return True
    return False


def kafka_loop():
    from confluent_kafka import Consumer, Producer
    producer = Producer({"bootstrap.servers": BOOTSTRAP, "enable.idempotence": True, "message.timeout.ms": 8000})
    consumer = Consumer({"bootstrap.servers": BOOTSTRAP, "group.id": CONSUMER_GROUP,
                         "auto.offset.reset": "earliest", "enable.auto.commit": False})
    consumer.subscribe([TOPIC])
    try:
        while True:
            if event := next_event():
                delivery = []
                producer.produce(TOPIC, key=event["trip_id"], value=json.dumps(event),
                                 on_delivery=lambda error, _: delivery.append(error))
                producer.flush(10)
                if delivery != [None]:
                    raise RuntimeError(f"Kafka publish failed for {event['event_id']}")
                mark_sent(event)
            message = consumer.poll(.25)
            if message is not None:
                if message.error():
                    raise RuntimeError(str(message.error()))
                event = json.loads(message.value())
                apply(event)
                if event["type"] == "trip.requested":
                    update_features()
                consumer.commit(message=message, asynchronous=False)
    finally:
        consumer.close()


if __name__ == "__main__":
    print("ATLAS event worker ready", flush=True)
    if BOOTSTRAP:
        kafka_loop()
    else:
        while True:
            if not local_tick():
                time.sleep(.15)
