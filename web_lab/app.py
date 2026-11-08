"""Standalone ATLAS-inspired Web Technology lab.

Run: uvicorn web_lab.app:app --reload
Open: http://127.0.0.1:8000
All records are synthetic. No real rides, payments, accounts or map routing.
"""
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent
DEFAULT_DB = ROOT / "data" / "demo.sqlite3"
STATES = ("requested", "assigned", "completed", "cancelled")


class RideCreate(BaseModel):
    passenger: str = Field(min_length=1, max_length=70)
    pickup: str = Field(min_length=1, max_length=120)
    destination: str = Field(min_length=1, max_length=120)
    distance_km: float = Field(gt=0, le=200)
    request_key: str = Field(min_length=8, max_length=100)


class RideUpdate(BaseModel):
    status: str


def fare_cents(distance_km: float) -> int:
    """Demo pricing only: €2.50 + €1.50/km; exact decimal rounding to cents."""
    d = Decimal(str(distance_km))
    return int((Decimal("250") + d * Decimal("150")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


@contextmanager
def connection(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(path), timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    try:
        yield db
        db.commit()
    except BaseException:
        db.rollback()
        raise
    finally:
        db.close()


def initialize(path: Path):
    with connection(path) as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS rides(
              id TEXT PRIMARY KEY,
              passenger TEXT NOT NULL,
              pickup TEXT NOT NULL,
              destination TEXT NOT NULL,
              distance_km REAL NOT NULL CHECK(distance_km>0 AND distance_km<=200),
              fare_cents INTEGER NOT NULL CHECK(fare_cents>=0),
              status TEXT NOT NULL CHECK(status IN ('requested','assigned','completed','cancelled')),
              request_key TEXT NOT NULL UNIQUE
            );
            CREATE INDEX IF NOT EXISTS idx_rides_status ON rides(status);
        """)


def as_dict(row):
    return dict(row) if row is not None else None


def create_app(db_path: str | Path | None = None) -> FastAPI:
    path = Path(db_path or os.getenv("WEB_LAB_DB", str(DEFAULT_DB)))
    initialize(path)
    api = FastAPI(title="ATLAS Web Technology teaching API", version="1.0",
                  description="Synthetic ride CRUD learning service. No authentication or real bookings.")
    api.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")

    @api.get("/", include_in_schema=False)
    def home():
        return FileResponse(ROOT / "static" / "index.html")

    @api.get("/api/health")
    def health():
        return {"status": "ok", "database": "sqlite", "demo": True}

    @api.get("/api/rides")
    def list_rides(status: str | None = Query(default=None)):
        if status is not None and status not in STATES:
            raise HTTPException(422, "Invalid status filter")
        with connection(path) as db:
            if status is None:
                rows = db.execute("SELECT * FROM rides ORDER BY rowid DESC").fetchall()
            else:
                rows = db.execute("SELECT * FROM rides WHERE status=? ORDER BY rowid DESC", (status,)).fetchall()
        return [as_dict(r) for r in rows]

    @api.get("/api/rides/{ride_id}")
    def get_ride(ride_id: str):
        with connection(path) as db:
            ride = db.execute("SELECT * FROM rides WHERE id=?", (ride_id,)).fetchone()
        if not ride:
            raise HTTPException(404, "Ride not found")
        return as_dict(ride)

    @api.post("/api/rides", status_code=201)
    def create_ride(payload: RideCreate):
        values = payload.model_dump()
        if not values["passenger"].strip() or not values["pickup"].strip() or not values["destination"].strip():
            raise HTTPException(422, "Fields cannot be blank")
        if values["pickup"].strip().casefold() == values["destination"].strip().casefold():
            raise HTTPException(422, "Pickup and destination must differ")
        with connection(path) as db:
            existing = db.execute("SELECT * FROM rides WHERE request_key=?", (values["request_key"],)).fetchone()
            if existing is not None:
                same = all(existing[k] == values[k] for k in ("passenger", "pickup", "destination", "distance_km"))
                if not same:
                    raise HTTPException(409, "Idempotency key was already used with different details")
                return as_dict(existing)
            ride_id = str(uuid4())
            try:
                db.execute("""INSERT INTO rides(id, passenger, pickup, destination, distance_km, fare_cents,
                              status, request_key) VALUES(?,?,?,?,?,?,?,?)""",
                           (ride_id, values["passenger"], values["pickup"], values["destination"],
                            values["distance_km"], fare_cents(values["distance_km"]), "requested",
                            values["request_key"]))
            except sqlite3.IntegrityError as exc:
                raise HTTPException(409, "Request conflicts with an existing ride") from exc
            saved = db.execute("SELECT * FROM rides WHERE id=?", (ride_id,)).fetchone()
        return as_dict(saved)

    @api.patch("/api/rides/{ride_id}")
    def update_ride(ride_id: str, payload: RideUpdate):
        next_state = payload.status
        allowed = {"requested": {"assigned", "cancelled"}, "assigned": {"completed", "cancelled"},
                   "completed": set(), "cancelled": set()}
        with connection(path) as db:
            current = db.execute("SELECT * FROM rides WHERE id=?", (ride_id,)).fetchone()
            if current is None:
                raise HTTPException(404, "Ride not found")
            if next_state not in STATES:
                raise HTTPException(422, "Invalid ride status")
            if next_state not in allowed[current["status"]]:
                raise HTTPException(409, "Invalid ride transition")
            db.execute("UPDATE rides SET status=? WHERE id=?", (next_state, ride_id))
            updated = db.execute("SELECT * FROM rides WHERE id=?", (ride_id,)).fetchone()
        return as_dict(updated)

    @api.delete("/api/rides/{ride_id}", status_code=204)
    def delete_ride(ride_id: str):
        with connection(path) as db:
            current = db.execute("SELECT status FROM rides WHERE id=?", (ride_id,)).fetchone()
            if current is None:
                raise HTTPException(404, "Ride not found")
            if current["status"] not in ("requested", "cancelled"):
                raise HTTPException(409, "Only requested or cancelled demo rides can be deleted")
            db.execute("DELETE FROM rides WHERE id=?", (ride_id,))

    return api


app = create_app()
