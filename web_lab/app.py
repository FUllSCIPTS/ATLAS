"""ATLAS Web Technology teaching application: browser -> FastAPI -> SQLite.

Run (from the repository root):
    python -m pip install -r web_lab/requirements.txt
    python -m uvicorn web_lab.app:app --reload
    open http://127.0.0.1:8000        (the page)   and   /docs   (the API)

Everything is synthetic and local: no accounts, payments, maps or real rides.
It deliberately has NO authentication, so never expose it on a public network.

What each part demonstrates (see docs/WEB_TECHNOLOGY.md):
* static/index.html, style.css, app.js  - HTML forms, CSS grid, DOM + fetch
* RideCreate / RideUpdate / DriverCreate - Pydantic validation -> HTTP 422
* /api/rides            - REST collection: GET (filter, paginate, ETag), POST (idempotency key)
* /api/rides/{id}       - item: GET (JOIN with drivers), PATCH (state machine), DELETE
* /api/drivers          - second table with a FOREIGN KEY from rides.driver_id
* /api/stats            - GROUP BY aggregation
* middleware            - security headers, Server-Timing, CORS for one dev origin
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
from contextlib import asynccontextmanager, contextmanager
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, StringConstraints, model_validator

ROOT = Path(__file__).resolve().parent
DEFAULT_DB = ROOT / "data" / "demo.sqlite3"
STATES = ("requested", "assigned", "completed", "cancelled")
TRANSITIONS = {"requested": {"assigned", "cancelled"}, "assigned": {"completed", "cancelled"},
               "completed": set(), "cancelled": set()}
SEED_DRIVERS = [("Ava", "Mardyke", 4.9, 1), ("Sam", "Grand Parade", 4.7, 1),
                ("Eoin", "Kent Station", 4.6, 1), ("Orla", "Douglas", 4.8, 0)]
SECURITY_HEADERS = {
    "Content-Security-Policy": "default-src 'self'; img-src 'self' data:; object-src 'none'; frame-ancestors 'none'",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
}
DEV_ORIGINS = [o for o in os.getenv("WEB_LAB_ORIGINS", "http://localhost:5173").split(",") if o]

Text70 = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=70)]
Text120 = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]


# ----------------------------------------------------------------------------- schemas
class RideCreate(BaseModel):
    passenger: Text70
    pickup: Text120
    destination: Text120
    distance_km: float = Field(gt=0, le=200)
    request_key: str = Field(min_length=8, max_length=100)

    @model_validator(mode="after")
    def different_places(self):
        if self.pickup.casefold() == self.destination.casefold():
            raise ValueError("pickup and destination must differ")
        return self


class RideUpdate(BaseModel):
    status: Literal["requested", "assigned", "completed", "cancelled"]
    driver_id: int | None = None


class DriverCreate(BaseModel):
    name: Text70
    zone: Text70
    rating: float = Field(ge=1, le=5)
    online: bool = True


def fare_cents(distance_km: float) -> int:
    """Demo pricing only: EUR 2.50 + EUR 1.50 per km, rounded half-up to whole cents."""
    d = Decimal(str(distance_km))
    return int((Decimal("250") + d * Decimal("150")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


# ----------------------------------------------------------------------------- database
SCHEMA = """
CREATE TABLE IF NOT EXISTS drivers(
  id      INTEGER PRIMARY KEY AUTOINCREMENT,
  name    TEXT NOT NULL UNIQUE,
  zone    TEXT NOT NULL,
  rating  REAL NOT NULL CHECK(rating BETWEEN 1 AND 5),
  online  INTEGER NOT NULL CHECK(online IN (0, 1))
);
CREATE TABLE IF NOT EXISTS rides(
  id          TEXT PRIMARY KEY,
  passenger   TEXT NOT NULL,
  pickup      TEXT NOT NULL,
  destination TEXT NOT NULL,
  distance_km REAL NOT NULL CHECK(distance_km > 0 AND distance_km <= 200),
  fare_cents  INTEGER NOT NULL CHECK(fare_cents >= 0),
  status      TEXT NOT NULL CHECK(status IN ('requested','assigned','completed','cancelled')),
  request_key TEXT NOT NULL UNIQUE,
  driver_id   INTEGER REFERENCES drivers(id) ON DELETE RESTRICT,
  created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE INDEX IF NOT EXISTS idx_rides_status ON rides(status);
CREATE INDEX IF NOT EXISTS idx_rides_driver ON rides(driver_id);
"""

RIDE_SELECT = """SELECT r.*, d.name AS driver_name
                 FROM rides r LEFT JOIN drivers d ON d.id = r.driver_id"""


@contextmanager
def connection(path: Path):
    """One connection per request; commit on success, roll back on any error."""
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
    path.parent.mkdir(parents=True, exist_ok=True)
    with connection(path) as db:
        db.execute("PRAGMA journal_mode=WAL")
        db.executescript(SCHEMA)
        if db.execute("SELECT COUNT(*) FROM drivers").fetchone()[0] == 0:
            db.executemany("INSERT INTO drivers(name, zone, rating, online) VALUES(?,?,?,?)", SEED_DRIVERS)


def as_dict(row):
    return dict(row) if row is not None else None


def etag_for(body: bytes) -> str:
    return '"' + hashlib.sha256(body).hexdigest()[:20] + '"'


# ----------------------------------------------------------------------------- application
def create_app(db_path: str | Path | None = None) -> FastAPI:
    path = Path(db_path or os.getenv("WEB_LAB_DB", str(DEFAULT_DB)))

    @asynccontextmanager
    async def lifespan(_app):
        initialize(path)                     # runs at server start-up, not at import time
        yield

    api = FastAPI(title="ATLAS Web Technology teaching API", version="2.0", lifespan=lifespan,
                  description="Synthetic ride and driver CRUD service for teaching. "
                              "No authentication: run on localhost only.")
    api.state.db_path = path
    api.add_middleware(CORSMiddleware, allow_origins=DEV_ORIGINS, allow_methods=["GET", "POST", "PATCH", "DELETE"],
                       allow_headers=["Content-Type", "If-None-Match"], expose_headers=["ETag", "X-Total-Count"])

    @api.middleware("http")
    async def headers_and_timing(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        for name, value in SECURITY_HEADERS.items():
            response.headers.setdefault(name, value)
        response.headers["Server-Timing"] = f"app;dur={(time.perf_counter() - start) * 1000:.2f}"
        return response

    api.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")

    @api.get("/", include_in_schema=False)
    def home():
        return FileResponse(ROOT / "static" / "index.html")

    @api.get("/api/health")
    def health():
        return {"status": "ok", "database": "sqlite", "demo": True}

    # ------------------------------------------------------------------ drivers
    @api.get("/api/drivers")
    def list_drivers(online: bool | None = None):
        sql, args = "SELECT * FROM drivers", ()
        if online is not None:
            sql, args = sql + " WHERE online = ?", (int(online),)
        with connection(path) as db:
            return [as_dict(r) for r in db.execute(sql + " ORDER BY name", args)]

    @api.post("/api/drivers", status_code=201)
    def create_driver(payload: DriverCreate):
        with connection(path) as db:
            try:
                cur = db.execute("INSERT INTO drivers(name, zone, rating, online) VALUES(?,?,?,?)",
                                 (payload.name, payload.zone, payload.rating, int(payload.online)))
            except sqlite3.IntegrityError as exc:
                raise HTTPException(409, "A driver with this name already exists") from exc
            return as_dict(db.execute("SELECT * FROM drivers WHERE id=?", (cur.lastrowid,)).fetchone())

    # ------------------------------------------------------------------ rides
    @api.get("/api/rides")
    def list_rides(request: Request, response: Response,
                   status: Literal["requested", "assigned", "completed", "cancelled"] | None = None,
                   limit: int = Query(default=50, ge=1, le=200), offset: int = Query(default=0, ge=0)):
        where, args = ("WHERE r.status = ?", (status,)) if status else ("", ())
        with connection(path) as db:
            total = db.execute(f"SELECT COUNT(*) FROM rides r {where}", args).fetchone()[0]
            rows = db.execute(f"{RIDE_SELECT} {where} ORDER BY r.rowid DESC LIMIT ? OFFSET ?",
                              (*args, limit, offset)).fetchall()
        data = [as_dict(r) for r in rows]
        body = json.dumps(data, separators=(",", ":")).encode()
        tag = etag_for(body + f"|{total}".encode())
        headers = {"ETag": tag, "X-Total-Count": str(total), "Cache-Control": "no-cache"}
        if request.headers.get("if-none-match") == tag:
            return Response(status_code=304, headers=headers)
        return Response(content=body, media_type="application/json", headers=headers)

    @api.get("/api/rides/{ride_id}")
    def get_ride(ride_id: str):
        with connection(path) as db:
            ride = db.execute(f"{RIDE_SELECT} WHERE r.id = ?", (ride_id,)).fetchone()
        if ride is None:
            raise HTTPException(404, "Ride not found")
        return as_dict(ride)

    @api.post("/api/rides", status_code=201)
    def create_ride(payload: RideCreate, response: Response):
        values = payload.model_dump()
        with connection(path) as db:
            existing = db.execute("SELECT * FROM rides WHERE request_key = ?", (values["request_key"],)).fetchone()
            if existing is not None:
                same = all(existing[k] == values[k] for k in ("passenger", "pickup", "destination", "distance_km"))
                if not same:
                    raise HTTPException(409, "Idempotency key was already used with different details")
                response.status_code = 200            # a replay: nothing new was created
                return as_dict(db.execute(f"{RIDE_SELECT} WHERE r.id = ?", (existing["id"],)).fetchone())
            ride_id = str(uuid4())
            try:
                db.execute("""INSERT INTO rides(id, passenger, pickup, destination, distance_km, fare_cents,
                              status, request_key) VALUES(?,?,?,?,?,?,'requested',?)""",
                           (ride_id, values["passenger"], values["pickup"], values["destination"],
                            values["distance_km"], fare_cents(values["distance_km"]), values["request_key"]))
            except sqlite3.IntegrityError as exc:       # a concurrent request won the race for this key
                raise HTTPException(409, "Request conflicts with an existing ride") from exc
            return as_dict(db.execute(f"{RIDE_SELECT} WHERE r.id = ?", (ride_id,)).fetchone())

    @api.patch("/api/rides/{ride_id}")
    def update_ride(ride_id: str, payload: RideUpdate):
        with connection(path) as db:
            current = db.execute("SELECT * FROM rides WHERE id = ?", (ride_id,)).fetchone()
            if current is None:
                raise HTTPException(404, "Ride not found")
            if payload.status not in TRANSITIONS[current["status"]]:
                raise HTTPException(409, f"Cannot move a {current['status']} ride to {payload.status}")
            driver_id = current["driver_id"]
            if payload.status == "assigned":
                if payload.driver_id is None:
                    raise HTTPException(422, "driver_id is required to assign a ride")
                driver = db.execute("SELECT * FROM drivers WHERE id = ?", (payload.driver_id,)).fetchone()
                if driver is None:
                    raise HTTPException(404, "Driver not found")
                if not driver["online"]:
                    raise HTTPException(409, "Driver is offline")
                driver_id = payload.driver_id
            db.execute("UPDATE rides SET status = ?, driver_id = ? WHERE id = ?", (payload.status, driver_id, ride_id))
            return as_dict(db.execute(f"{RIDE_SELECT} WHERE r.id = ?", (ride_id,)).fetchone())

    @api.delete("/api/rides/{ride_id}", status_code=204)
    def delete_ride(ride_id: str):
        with connection(path) as db:
            current = db.execute("SELECT status FROM rides WHERE id = ?", (ride_id,)).fetchone()
            if current is None:
                raise HTTPException(404, "Ride not found")
            if current["status"] not in ("requested", "cancelled"):
                raise HTTPException(409, "Only requested or cancelled demo rides can be deleted")
            db.execute("DELETE FROM rides WHERE id = ?", (ride_id,))
        return Response(status_code=204)

    @api.get("/api/stats")
    def stats():
        with connection(path) as db:
            by_status = db.execute("""SELECT status, COUNT(*) AS rides, COALESCE(SUM(fare_cents), 0) AS fare_cents
                                      FROM rides GROUP BY status ORDER BY status""").fetchall()
            by_driver = db.execute("""SELECT d.name, COUNT(r.id) AS rides
                                      FROM drivers d LEFT JOIN rides r ON r.driver_id = d.id
                                      GROUP BY d.id HAVING COUNT(r.id) > 0 ORDER BY rides DESC, d.name""").fetchall()
        return {"by_status": [as_dict(r) for r in by_status], "by_driver": [as_dict(r) for r in by_driver]}

    return api


app = create_app()
