from uuid import UUID

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from packages.config import internal_actor
from packages.db import database, emit

app = FastAPI(title="ATLAS Dispatch API")


class Telemetry(BaseModel):
    online: bool
    distance_km: float = Field(ge=0, le=50)
    speed_kph: float = Field(ge=0, le=250)


@app.get("/healthz")
def health():
    with database() as db:
        db.run("SELECT 1")
    return {"status": "ok"}


@app.put("/v1/driver/availability")
def availability(request: Request, payload: Telemetry):
    actor = internal_actor(request, "driver")
    with database() as db:
        db.run("UPDATE drivers SET online=?, distance_km=?, speed_kph=? WHERE id=?",
               int(payload.online), payload.distance_km, payload.speed_kph, actor)
    return {"driver_id": actor, **payload.model_dump()}


@app.get("/v1/driver/offers")
def offers(request: Request):
    actor = internal_actor(request, "driver")
    with database() as db:
        rows = db.run(
            "SELECT o.trip_id, o.state, t.status, t.pickup, t.destination, o.model_version, o.policy_version, o.forecast, o.acceptance, o.anomaly_flag FROM offers o JOIN trips t "
            "ON t.id=o.trip_id WHERE o.driver_id=? AND t.status!='completed' ORDER BY t.created_at DESC",
            actor,
        ).fetchall()
    return [dict(row) for row in rows]


@app.post("/v1/driver/offers/{trip_id}/accept", status_code=202)
def accept(request: Request, trip_id: UUID):
    actor = internal_actor(request, "driver")
    identifier = str(trip_id)
    with database() as db:
        offer = db.run("SELECT state FROM offers WHERE trip_id=? AND driver_id=?", identifier, actor).fetchone()
        if offer is None:
            raise HTTPException(404, "Offer not found")
        changed = db.run("UPDATE offers SET state='accepted' WHERE trip_id=? AND driver_id=? AND state='offered'",
                         identifier, actor).rowcount
        if changed:
            free = db.run("UPDATE drivers SET active_trip=? WHERE id=? AND online=1 AND active_trip IS NULL",
                          identifier, actor).rowcount
            if not free:
                raise HTTPException(409, "Driver unavailable")
            emit(db, identifier, "dispatch.assignment.confirmed", driver_id=actor)
    return {"trip_id": identifier, "state": "accepted"}
