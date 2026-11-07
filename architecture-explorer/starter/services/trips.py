import time
from typing import Annotated, Literal
from uuid import UUID, uuid4

from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, Field

from packages.config import internal_actor
from packages.db import database, emit

app = FastAPI(title="ATLAS Trip API")


class Booking(BaseModel):
    pickup: str = Field(min_length=1, max_length=120, pattern=r"\S")
    destination: str = Field(min_length=1, max_length=120, pattern=r"\S")
    zone: Literal["cork-centre", "cork-north"]


class Milestone(BaseModel):
    status: Literal["picked_up", "completed"]


@app.get("/healthz")
def health():
    with database() as db:
        db.run("SELECT 1")
    return {"status": "ok"}


@app.post("/v1/rider/trips", status_code=202)
def book(request: Request, payload: Booking, idempotency_key: Annotated[str, Header(min_length=1, max_length=128)]):
    rider = internal_actor(request, "rider")
    trip_id = str(uuid4())
    with database() as db:
        created = db.run(
            "INSERT INTO trips VALUES (?, ?, ?, ?, ?, ?, 'requested', NULL, ?) ON CONFLICT DO NOTHING",
            trip_id, rider, idempotency_key, payload.pickup, payload.destination, payload.zone, int(time.time()),
        ).rowcount
        trip = db.run("SELECT * FROM trips WHERE rider_id=? AND request_key=?", rider, idempotency_key).fetchone()
        if any(trip[name] != value for name, value in payload.model_dump().items()):
            raise HTTPException(409, "Idempotency key already used with another booking")
        if created:
            emit(db, trip_id, "trip.requested", zone=payload.zone)
    return public_trip(trip)


def public_trip(row):
    return {key: row[key] for key in ("id", "pickup", "destination", "zone", "status", "driver_id")}


@app.get("/v1/rider/trips/{trip_id}")
def status(request: Request, trip_id: UUID):
    rider = internal_actor(request, "rider")
    with database() as db:
        trip = db.run("SELECT * FROM trips WHERE id=? AND rider_id=?", str(trip_id), rider).fetchone()
    if trip is None:
        raise HTTPException(404, "Trip not found")
    return public_trip(trip)


@app.post("/v1/driver/trips/{trip_id}/milestones")
def milestone(request: Request, trip_id: UUID, payload: Milestone):
    driver = internal_actor(request, "driver")
    identifier = str(trip_id)
    before = "assigned" if payload.status == "picked_up" else "picked_up"
    with database() as db:
        changed = db.run("UPDATE trips SET status=? WHERE id=? AND driver_id=? AND status=?",
                         payload.status, identifier, driver, before).rowcount
        trip = db.run("SELECT * FROM trips WHERE id=? AND driver_id=?", identifier, driver).fetchone()
        if trip is None:
            raise HTTPException(404, "Trip not found")
        if not changed and trip["status"] != payload.status:
            raise HTTPException(409, "Invalid trip transition")
        if changed:
            if payload.status == "completed":
                db.run("UPDATE drivers SET active_trip=NULL WHERE id=? AND active_trip=?", driver, identifier)
            emit(db, identifier, "trip." + payload.status, elapsed_s=max(0, int(time.time()) - trip["created_at"]))
    return public_trip(trip)
