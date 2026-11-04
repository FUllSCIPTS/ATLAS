"""Re-deliver a completed ride event and check that the worker applies it once."""

import json
import os
import time

from packages.config import CONSUMER_GROUP, TOPIC
from packages.db import database, envelope
from tests.smoke import check
from workers.events import apply


def completed_event(trip_id):
    with database() as db:
        row = db.run("SELECT * FROM outbox WHERE trip_id=? AND event_type='trip.completed'", trip_id).fetchone()
        assert row is not None, trip_id
        return envelope(row)


def snapshot(trip_id, event_id):
    with database() as db:
        trip = db.run("SELECT * FROM trips WHERE id=?", trip_id).fetchone()
        experience = db.run("SELECT * FROM experience WHERE trip_id=?", trip_id).fetchone()
        outbox_count = db.run("SELECT COUNT(*) AS count FROM outbox WHERE trip_id=?", trip_id).fetchone()["count"]
        inbox_count = db.run("SELECT COUNT(*) AS count FROM inbox WHERE event_id=?", event_id).fetchone()["count"]
    assert trip is not None and trip["status"] == "completed"
    assert experience is not None and inbox_count == 1
    return dict(trip), dict(experience), outbox_count, inbox_count


def replay_over_kafka(event, bootstrap):
    from confluent_kafka import Consumer, Producer, TopicPartition

    config = {"bootstrap.servers": bootstrap}
    producer = Producer({**config, "message.timeout.ms": 10000})
    delivery = []
    producer.produce(TOPIC, key=event["trip_id"], value=json.dumps(event),
                     on_delivery=lambda error, message: delivery.append((error, message)))
    assert producer.flush(12) == 0 and len(delivery) == 1, "No replay acknowledgement"
    error, message = delivery[0]
    assert error is None, error
    partition = TopicPartition(message.topic(), message.partition())

    # Query committed offsets without subscribing or joining the active consumer group.
    consumer = Consumer({**config, "group.id": CONSUMER_GROUP, "enable.auto.commit": False})
    try:
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            offset = consumer.committed([partition], timeout=5)[0]
            if offset.error is None and offset.offset > message.offset():
                return
            time.sleep(.25)
        raise AssertionError(f"{CONSUMER_GROUP} did not acknowledge the replay at offset {message.offset()}")
    finally:
        consumer.close()


def main():
    trip_id = check()
    event = completed_event(trip_id)
    before = snapshot(trip_id, event["event_id"])
    if bootstrap := os.getenv("KAFKA_BOOTSTRAP"):
        replay_over_kafka(event, bootstrap)
        transport = "Kafka with consumer offset confirmation"
    else:
        apply(event)
        transport = "local event handler"
    assert snapshot(trip_id, event["event_id"]) == before, "Replay changed durable state"
    print(f"PASS replay through {transport}. Trip, experience, inbox and outbox are unchanged.")


if __name__ == "__main__":
    main()
