import os
import time
from uuid import uuid4

import httpx

from packages.config import KEYS
from packages.db import database

gateway = os.getenv("ATLAS_GATEWAY_URL", "http://127.0.0.1:8000")
models = os.getenv("ATLAS_MODEL_URL", "http://127.0.0.1:8003")
client = httpx.Client(timeout=5, trust_env=False)
driver_keys = {driver: key for driver, key in KEYS.items() if driver.startswith("driver-")}


def until(check, label, timeout=45):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            if result := check():
                return result
        except httpx.TransportError:
            pass
        time.sleep(.2)
    raise AssertionError(f"Timed out waiting for {label}")


def api(method, path, actor="rider-a", *, expected=200, key=None, body=None):
    headers = {"Authorization": f"Bearer {KEYS[actor]}"}
    if key:
        headers["Idempotency-Key"] = key
    response = client.request(method, gateway + path, headers=headers, json=body, timeout=5)
    assert response.status_code == expected, (path, response.status_code, response.text)
    return response.json()


def check():
    until(lambda: client.get(gateway + "/healthz", timeout=3).is_success, "gateway")
    until(lambda: client.get(models + "/healthz", timeout=3).is_success, "scorer")
    assert client.get(gateway + "/passenger").is_success and client.get(gateway + "/driver").is_success
    assert client.get(gateway + "/v1/driver/offers").status_code == 401
    request_key = str(uuid4())
    booking = {"pickup": "UCC Main Gate", "destination": "Kent Station", "zone": "cork-centre"}
    trip = api("POST", "/v1/rider/trips", expected=202, body=booking, key=request_key)
    trip_id = trip["id"]
    assert api("POST", "/v1/rider/trips", expected=202, body=booking, key=request_key)["id"] == trip_id
    api("POST", "/v1/rider/trips", expected=409, body={**booking, "destination": "Douglas"}, key=request_key)

    def offer_for_trip():
        for actor in driver_keys:
            for row in api("GET", "/v1/driver/offers", actor):
                if row["trip_id"] == trip_id:
                    return actor, row

    actor, offer = until(offer_for_trip, "driver offer")
    other = next(driver for driver in driver_keys if driver != actor)
    accept = f"/v1/driver/offers/{trip_id}/accept"
    api("POST", accept, other, expected=404)
    assert offer["model_version"] != "fallback" and 0 <= offer["acceptance"] <= 1
    assert offer["forecast"] >= 0 and offer["anomaly_flag"] in (0, 1)
    api("POST", accept, actor, expected=202)
    api("POST", accept, actor, expected=202)
    status = f"/v1/rider/trips/{trip_id}"
    until(lambda: api("GET", status)["status"] == "assigned", "assignment")
    milestone = f"/v1/driver/trips/{trip_id}/milestones"
    api("POST", milestone, actor, expected=409, body={"status": "completed"})
    assert api("POST", milestone, actor, body={"status": "picked_up"})["status"] == "picked_up"
    assert api("POST", milestone, actor, body={"status": "completed"})["status"] == "completed"
    assert api("GET", status)["status"] == "completed"

    def learned():
        with database() as db:
            return db.run("SELECT * FROM experience WHERE trip_id=?", trip_id).fetchone()

    logged = until(learned, "one learning experience")
    assert logged["policy_version"] == offer["policy_version"]
    assert -1 <= logged["reward"] <= 1
    with database() as db:
        rows = db.run("SELECT event_type, COUNT(*) AS count FROM outbox WHERE trip_id=? GROUP BY event_type", trip_id).fetchall()
    assert {row["event_type"]: row["count"] for row in rows} == {
        "trip.requested": 1, "dispatch.offer.created": 1, "dispatch.assignment.confirmed": 1,
        "trip.assigned": 1, "trip.picked_up": 1, "trip.completed": 1,
    }
    print(f"PASS trip {trip_id}, trained models {offer['model_version']}, policy {logged['policy_version']}, reward {logged['reward']:.3f}")


if __name__ == "__main__":
    check()
