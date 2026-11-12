"""Building real apps: 12 integration-flow labs (A01-A12).

Part I (experiments.py) teaches the language one idea at a time. Real applications
are different: one button click crosses five layers before any data comes back.

    UI button -> event handler -> HTTP client -> HTTP route -> service -> SQLite
                                                                          |
    screen updated  <- JSON response <-  status code  <-  rows  <---------+

This module builds that whole stack with the standard library only - no frameworks to
install - so every hop can be observed:

* ``Database``     sqlite3 with CHECK / FOREIGN KEY / UNIQUE constraints and transactions
* ``RideService``  business rules: validation, pricing, idempotency, state changes, cache
* ``ApiServer``    a JSON REST API on http.server (runs in a background thread)
* ``ApiClient``    urllib requests with timeouts and a retry policy
* ``RideScreen``   a headless screen: form fields, buttons, a table and an error banner

Each lab clicks buttons on the screen, lets the request travel to the database and back,
asserts what must be true, and charts what was observed.

    python python_lab/app_integration.py                  # self-tests, then usage
    python python_lab/app_integration.py --list
    python python_lab/app_integration.py --all            # A01-A12 -> python_lab/results_app
    python python_lab/app_integration.py --experiment 4
    python python_lab/app_integration.py --serve          # the same API + a clickable page

Course guide: docs/PYTHON_PROGRAMMING.md (Part III). Tests: python_lab/tests/.
Only the standard library and matplotlib are needed. All data is synthetic.
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import re
import socket
import sqlite3
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from collections import deque
from concurrent.futures import Future, ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

SEED = 2026
PLACES = ["UCC", "Kent Station", "Cork Airport", "English Market", "Blackrock Castle",
          "Douglas", "Ballincollig", "Mahon Point"]
PASSENGERS = ["Aoife", "Brian", "Ciara", "Darragh", "Eimear", "Fionn", "Grainne", "Hugh",
              "Isolde", "Jack", "Keelin", "Liam"]
DRIVER_NAMES = ["Niamh", "Oisin", "Padraig", "Roisin", "Sean", "Tadhg", "Una", "Cormac",
                "Saoirse", "Ronan", "Orla", "Declan", "Maeve", "Cillian", "Aisling", "Eoin"]


def fare_cents(km: float) -> int:
    """Same tariff as Part I: 350 cents flag fall + 170 cents per km."""
    return 350 + round(170 * km)


# =============================================================================
# Trace: who handled the click, in which order
# =============================================================================
LAYERS = ["UI button", "event handler", "HTTP client", "HTTP route", "service", "database"]


class Trace:
    """Thread-safe log of hops. The server thread writes to the same trace as the UI."""

    def __init__(self):
        self.hops: list[tuple[float, str, str]] = []
        self.enabled = True
        self._lock = threading.Lock()

    def hop(self, layer: str, what: str):
        assert layer in LAYERS, layer
        if self.enabled:
            with self._lock:
                self.hops.append((time.perf_counter(), layer, what))

    def clear(self):
        with self._lock:
            self.hops.clear()

    def lines(self):
        if not self.hops:
            return []
        t0 = self.hops[0][0]
        return [f"{(t - t0) * 1000:7.2f} ms  {layer:<13} {what}" for t, layer, what in self.hops]


# =============================================================================
# Layer 6: the database
# =============================================================================
SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE drivers (
    id      INTEGER PRIMARY KEY,
    name    TEXT    NOT NULL UNIQUE,
    online  INTEGER NOT NULL DEFAULT 1 CHECK (online IN (0, 1)),
    busy    INTEGER NOT NULL DEFAULT 0 CHECK (busy IN (0, 1))
);
CREATE TABLE rides (
    id          INTEGER PRIMARY KEY,
    passenger   TEXT    NOT NULL CHECK (length(passenger) BETWEEN 1 AND 40),
    pickup      TEXT    NOT NULL,
    destination TEXT    NOT NULL,
    distance_km REAL    NOT NULL CHECK (typeof(distance_km) IN ('real', 'integer')
                                        AND distance_km > 0 AND distance_km <= 100),
    fare_cents  INTEGER NOT NULL CHECK (fare_cents > 0),
    status      TEXT    NOT NULL DEFAULT 'requested'
                        CHECK (status IN ('requested', 'assigned', 'completed', 'cancelled')),
    driver_id   INTEGER REFERENCES drivers(id),
    version     INTEGER NOT NULL DEFAULT 1,
    request_key TEXT UNIQUE,
    CHECK (pickup <> destination)
);
CREATE TABLE audit (
    id      INTEGER PRIMARY KEY,
    ride_id INTEGER NOT NULL REFERENCES rides(id),
    action  TEXT    NOT NULL
);
CREATE INDEX rides_status ON rides(status);
"""


def _describe_sql(sql: str) -> str:
    words = sql.split()
    verb = words[0].upper()
    table = ""
    for key in ("FROM", "INTO", "UPDATE"):
        upper = [w.upper() for w in words]
        if key in upper and upper.index(key) + 1 < len(words):
            table = words[upper.index(key) + 1] if key != "UPDATE" else words[1]
            break
    if verb == "SELECT" and "COUNT(" in sql.upper():
        verb = "SELECT COUNT(*)"
    return f"{verb} {table}".strip()


class Database:
    """One shared SQLite connection guarded by a re-entrant lock.

    ``statements`` records every SQL statement SQLite actually ran (via
    ``set_trace_callback``), so labs can count queries per button click.
    """

    def __init__(self, trace: Trace | None = None, path: str = ":memory:"):
        self.trace = trace or Trace()
        self.conn = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
        self.conn.row_factory = sqlite3.Row
        self.lock = threading.RLock()
        self.statements: list[str] = []
        self.conn.executescript(SCHEMA)
        self.conn.set_trace_callback(lambda sql: self.statements.append(" ".join(sql.split())))

    def query(self, sql: str, params=()) -> list[dict]:
        with self.lock:
            self.trace.hop("database", _describe_sql(sql))
            return [dict(r) for r in self.conn.execute(sql, params).fetchall()]

    def execute(self, sql: str, params=()) -> sqlite3.Cursor:
        with self.lock:
            self.trace.hop("database", _describe_sql(sql))
            return self.conn.execute(sql, params)

    @contextmanager
    def transaction(self):
        """BEGIN ... COMMIT, or ROLLBACK if anything inside raises."""
        with self.lock:
            self.conn.execute("BEGIN IMMEDIATE")
            try:
                yield
            except BaseException:
                self.conn.execute("ROLLBACK")
                raise
            else:
                self.conn.execute("COMMIT")

    def count(self, table: str, where: str = "1") -> int:
        with self.lock:
            return self.conn.execute(f"SELECT COUNT(*) FROM {table} WHERE {where}").fetchone()[0]

    def selects_since(self, mark: int, contains: str = "") -> int:
        return sum(1 for s in self.statements[mark:] if s.upper().startswith("SELECT") and contains in s)

    def close(self):
        self.conn.close()


# =============================================================================
# Layer 5: the service (business rules)
# =============================================================================
class AppError(Exception):
    status = 500
    headers: dict = {}

    def payload(self):
        return {"error": str(self)}


class ValidationError(AppError):
    status = 422

    def __init__(self, field_name: str, message: str):
        super().__init__(message)
        self.field = field_name

    def payload(self):
        return {"error": str(self), "field": self.field}


class NotFound(AppError):
    status = 404


class Conflict(AppError):
    status = 409


class Unauthorized(AppError):
    """401: no valid credentials. The response carries WWW-Authenticate: Bearer."""
    status = 401
    headers = {"WWW-Authenticate": "Bearer"}


class Forbidden(AppError):
    """403: authenticated, but this role may not do this."""
    status = 403


class TooManyRequests(AppError):
    """429 with a Retry-After header (whole seconds)."""
    status = 429

    def __init__(self, message: str, retry_after: int):
        super().__init__(message)
        self.retry_after = max(1, int(retry_after))
        self.headers = {"Retry-After": str(self.retry_after)}

    def payload(self):
        return {"error": str(self), "retry_after": self.retry_after}


@dataclass
class RawBody:
    """A non-JSON response body (CSV, plain text, a file download)."""
    data: str | bytes
    content_type: str = "text/plain; charset=utf-8"


@dataclass
class Request:
    """What before_request hooks see. `state` is where a hook can leave data (e.g. the user)."""
    method: str
    path: str
    query: dict
    headers: object
    body: object
    client: str
    state: dict = field(default_factory=dict)


def _escape_like(text: str) -> str:
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class RideService:
    """Everything the API is allowed to do to the database.

    Teaching switches (set by the labs, never by HTTP clients):
      atomic_assign       True: assignment runs in one transaction
      crash_assign_ids    ride ids for which assignment crashes half-way
      stats_cache         'none' | 'no-invalidation' | 'invalidate-on-write'
    """

    def __init__(self, db: Database, trace: Trace):
        self.db, self.trace = db, trace
        self.atomic_assign = True
        self.crash_assign_ids: set[int] = set()
        self.stats_cache = "none"
        self._cached_stats = None
        self.write_hooks: list = []     # f(db, event, ride) - runs INSIDE the write's transaction

    def _emit(self, event: str, ride_id: int):
        for hook in self.write_hooks:
            hook(self.db, event, self.get_ride(ride_id))

    # ---- validation -------------------------------------------------------
    def validate_booking(self, body) -> dict:
        if not isinstance(body, dict):
            raise ValidationError("body", "a JSON object is required")
        passenger = body.get("passenger")
        if not isinstance(passenger, str) or not passenger.strip():
            raise ValidationError("passenger", "passenger name is required")
        if len(passenger.strip()) > 40:
            raise ValidationError("passenger", "at most 40 characters")
        for name in ("pickup", "destination"):
            if body.get(name) not in PLACES:
                raise ValidationError(name, f"unknown place {body.get(name)!r}")
        if body["pickup"] == body["destination"]:
            raise ValidationError("destination", "destination must differ from pickup")
        km = body.get("distance_km")
        if isinstance(km, bool) or not isinstance(km, (int, float)):
            raise ValidationError("distance_km", "a number is required")
        if not 0 < km <= 100:
            raise ValidationError("distance_km", "must be greater than 0 and at most 100")
        driver_id = body.get("driver_id")              # optional; existence is left to the FOREIGN KEY
        if driver_id is not None and (isinstance(driver_id, bool) or not isinstance(driver_id, int)):
            raise ValidationError("driver_id", "an integer is required")
        return {"passenger": passenger.strip(), "pickup": body["pickup"], "destination": body["destination"],
                "distance_km": float(km), "driver_id": driver_id}

    # ---- rides ------------------------------------------------------------
    def create_ride(self, body, request_key: str | None = None) -> tuple[dict, bool]:
        """Returns (ride, created). A repeated request_key returns the first ride (created=False)."""
        self.trace.hop("service", "validate, price, insert")
        data = self.validate_booking(body)
        with self.db.transaction():
            if request_key:
                existing = self.db.query("SELECT * FROM rides WHERE request_key = ?", (request_key,))
                if existing:
                    return existing[0], False
            try:
                cur = self.db.execute(
                    "INSERT INTO rides (passenger, pickup, destination, distance_km, fare_cents, status, "
                    "driver_id, request_key) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (data["passenger"], data["pickup"], data["destination"], data["distance_km"],
                     fare_cents(data["distance_km"]), "assigned" if data["driver_id"] else "requested",
                     data["driver_id"], request_key))
            except sqlite3.IntegrityError as exc:
                raise Conflict(f"the database rejected the ride ({exc})") from None
            ride = self.db.query("SELECT * FROM rides WHERE id = ?", (cur.lastrowid,))[0]
            self._emit("ride.created", ride["id"])
        self._invalidate()
        return ride, True

    def list_rides(self, limit=10, offset=0, q="", before_id=None) -> tuple[list[dict], int]:
        self.trace.hop("service", "list rides")
        where, params = [], []
        if q:
            pattern = f"%{_escape_like(q)}%"
            where.append("(destination LIKE ? ESCAPE '\\' OR passenger LIKE ? ESCAPE '\\')")
            params += [pattern, pattern]
        total_sql = "SELECT COUNT(*) AS n FROM rides" + (" WHERE " + " AND ".join(where) if where else "")
        total = self.db.query(total_sql, params)[0]["n"]
        if before_id is not None:                      # keyset pagination
            where.append("id < ?")
            params.append(before_id)
        sql = "SELECT * FROM rides" + (" WHERE " + " AND ".join(where) if where else "")
        rows = self.db.query(sql + " ORDER BY id DESC LIMIT ? OFFSET ?", (*params, limit, offset))
        return rows, total

    def get_ride(self, ride_id: int) -> dict:
        rows = self.db.query("SELECT * FROM rides WHERE id = ?", (ride_id,))
        if not rows:
            raise NotFound(f"ride {ride_id} does not exist")
        return rows[0]

    def update_ride(self, ride_id: int, body) -> dict:
        """PATCH. With "version" in the body the update only succeeds if nobody saved in between."""
        self.trace.hop("service", "update ride")
        if not isinstance(body, dict):
            raise ValidationError("body", "a JSON object is required")
        changes = {}
        if "passenger" in body:
            p = body["passenger"]
            if not isinstance(p, str) or not 1 <= len(p.strip()) <= 40:
                raise ValidationError("passenger", "1 to 40 characters")
            changes["passenger"] = p.strip()
        if "destination" in body:
            if body["destination"] not in PLACES:
                raise ValidationError("destination", "unknown place")
            changes["destination"] = body["destination"]
        if not changes:
            raise ValidationError("body", "nothing to change")
        version = body.get("version")
        with self.db.transaction():
            current = self.get_ride(ride_id)
            if changes.get("destination", current["destination"]) == current["pickup"]:
                raise ValidationError("destination", "destination must differ from pickup")
            assignments = ", ".join(f"{k} = ?" for k in changes)
            sql = f"UPDATE rides SET {assignments}, version = version + 1 WHERE id = ?"
            params = [*changes.values(), ride_id]
            if version is not None:
                sql += " AND version = ?"
                params.append(version)
            if self.db.execute(sql, params).rowcount == 0:
                raise Conflict(f"ride {ride_id} was changed by someone else (you had version {version}, "
                               f"it is now {current['version']})")
            ride = self.get_ride(ride_id)
        return ride

    def assign(self, ride_id: int, driver_id) -> dict:
        """Three writes that must happen together: ride, driver, audit log."""
        self.trace.hop("service", "assign driver")
        if isinstance(driver_id, bool) or not isinstance(driver_id, int):
            raise ValidationError("driver_id", "an integer is required")

        def steps():
            ride = self.get_ride(ride_id)
            if ride["status"] != "requested":
                raise Conflict(f"ride {ride_id} is {ride['status']}, not requested")
            drivers = self.db.query("SELECT * FROM drivers WHERE id = ?", (driver_id,))
            if not drivers:
                raise NotFound(f"driver {driver_id} does not exist")
            if drivers[0]["busy"] or not drivers[0]["online"]:
                raise Conflict(f"driver {driver_id} is not available")
            self.db.execute("UPDATE rides SET status = 'assigned', driver_id = ?, version = version + 1 "
                            "WHERE id = ?", (driver_id, ride_id))
            if ride_id in self.crash_assign_ids:
                raise RuntimeError("simulated crash after the ride row was updated")
            self.db.execute("UPDATE drivers SET busy = 1 WHERE id = ?", (driver_id,))
            self.db.execute("INSERT INTO audit (ride_id, action) VALUES (?, ?)",
                            (ride_id, f"assigned driver {driver_id}"))
            self._emit("ride.assigned", ride_id)

        if self.atomic_assign:
            with self.db.transaction():
                steps()
        else:
            with self.db.lock:                         # still one thread at a time, but no rollback
                steps()
        self._invalidate()
        return self.get_ride(ride_id)

    def finish(self, ride_id: int, action: str) -> dict:
        """complete: assigned -> completed (driver freed);  cancel: requested -> cancelled."""
        self.trace.hop("service", action)
        allowed = {"complete": ("assigned", "completed"), "cancel": ("requested", "cancelled")}
        before, after = allowed[action]
        with self.db.transaction():
            ride = self.get_ride(ride_id)
            if ride["status"] != before:
                raise Conflict(f"cannot {action} a ride that is {ride['status']}")
            self.db.execute("UPDATE rides SET status = ?, version = version + 1 WHERE id = ?", (after, ride_id))
            if ride["driver_id"]:
                self.db.execute("UPDATE drivers SET busy = 0 WHERE id = ?", (ride["driver_id"],))
            self.db.execute("INSERT INTO audit (ride_id, action) VALUES (?, ?)", (ride_id, after))
            self._emit(f"ride.{after}", ride_id)
        self._invalidate()
        return self.get_ride(ride_id)

    def rides_with_drivers(self, strategy="join") -> list[dict]:
        self.trace.hop("service", f"rides with drivers ({strategy})")
        if strategy == "join":
            return self.db.query("SELECT r.id, r.passenger, d.name AS driver FROM rides r "
                                 "LEFT JOIN drivers d ON d.id = r.driver_id ORDER BY r.id")
        if strategy == "n_plus_1":                      # the classic ORM trap: one query per row
            out = []
            for ride in self.db.query("SELECT id, passenger, driver_id FROM rides ORDER BY id"):
                name = None
                if ride["driver_id"] is not None:
                    name = self.db.query("SELECT name FROM drivers WHERE id = ?", (ride["driver_id"],))[0]["name"]
                out.append({"id": ride["id"], "passenger": ride["passenger"], "driver": name})
            return out
        raise ValidationError("strategy", "join or n_plus_1")

    def drivers(self, online=None) -> list[dict]:
        if online is None:
            return self.db.query("SELECT * FROM drivers ORDER BY id")
        return self.db.query("SELECT * FROM drivers WHERE online = ? ORDER BY id", (int(online),))

    # ---- stats with an optional cache ------------------------------------
    def stats(self) -> dict:
        self.trace.hop("service", f"stats (cache: {self.stats_cache})")
        if self.stats_cache != "none" and self._cached_stats is not None:
            return {**self._cached_stats, "cached": True}
        rows = self.db.query("SELECT status, COUNT(*) AS rides, COALESCE(SUM(fare_cents), 0) AS fares "
                             "FROM rides GROUP BY status ORDER BY status")
        result = {"by_status": rows, "total_rides": sum(r["rides"] for r in rows), "cached": False}
        if self.stats_cache != "none":
            self._cached_stats = result
        return result

    def _invalidate(self):
        if self.stats_cache == "invalidate-on-write":
            self._cached_stats = None

    # ---- seeding (bypasses the trace) -------------------------------------
    def seed(self, drivers=4, rides=0, assigned=False, offline=(), rng_seed=SEED):
        rng = random.Random(rng_seed)
        was = self.trace.enabled
        self.trace.enabled = False
        try:
            with self.db.transaction():
                for i in range(drivers):
                    name = DRIVER_NAMES[i % len(DRIVER_NAMES)] + ("" if i < len(DRIVER_NAMES) else f" {i}")
                    self.db.execute("INSERT INTO drivers (name, online) VALUES (?, ?)",
                                    (name, 0 if i in offline else 1))
                for i in range(rides):
                    pickup, destination = rng.sample(PLACES, 2)
                    km = round(rng.uniform(1, 15), 1)
                    driver = (i % drivers) + 1 if assigned and drivers else None
                    self.db.execute(
                        "INSERT INTO rides (passenger, pickup, destination, distance_km, fare_cents, status, "
                        "driver_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (PASSENGERS[i % len(PASSENGERS)], pickup, destination, km, fare_cents(km),
                         "assigned" if driver else "requested", driver))
        finally:
            self.trace.enabled = was


# =============================================================================
# Layer 4: the HTTP API (standard library http.server)
# =============================================================================
def _int_param(query: dict, name: str, default, lo, hi):
    if name not in query:
        return default
    try:
        value = int(query[name][0])
    except ValueError:
        raise ValidationError(name, "an integer is required") from None
    if not lo <= value <= hi:
        raise ValidationError(name, f"must be between {lo} and {hi}")
    return value


class ApiServer:
    """JSON API on 127.0.0.1 with a random free port, served from a background thread.

    ``faults`` lets a lab make a path misbehave:  faults['/api/stats'] = deque([503, 503])
    or deque(['delay:0.4']) - each request to that path pops one entry.
    """

    def __init__(self, service: RideService, trace: Trace):
        self.service, self.trace = service, trace
        self.faults: dict[str, deque] = {}
        self.log: list[tuple[str, str, int]] = []
        self.before_request: list = []          # f(request) -> None, or raise AppError to refuse
        self._local = threading.local()
        self.routes = [
            ("GET", r"/api/health", lambda m, q, b, h: (200, {"ok": True})),
            ("GET", r"/api/rides", self._list_rides),
            ("POST", r"/api/rides", self._create_ride),
            ("GET", r"/api/rides/(\d+)", lambda m, q, b, h: (200, service.get_ride(int(m[1])))),
            ("PATCH", r"/api/rides/(\d+)", lambda m, q, b, h: (200, service.update_ride(int(m[1]), b))),
            ("POST", r"/api/rides/(\d+)/assign",
             lambda m, q, b, h: (200, service.assign(int(m[1]), (b or {}).get("driver_id")))),
            ("POST", r"/api/rides/(\d+)/(complete|cancel)",
             lambda m, q, b, h: (200, service.finish(int(m[1]), m[2]))),
            ("GET", r"/api/drivers", self._drivers),
            ("GET", r"/api/rides-with-drivers",
             lambda m, q, b, h: (200, service.rides_with_drivers(q.get("strategy", ["join"])[0]))),
            ("GET", r"/api/stats", lambda m, q, b, h: (200, service.stats())),
            ("GET", r"/", lambda m, q, b, h: (200, DEMO_PAGE)),
        ]
        server = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *args):          # keep notebook output clean
                pass

            def do_GET(self):
                server._dispatch(self, "GET")

            def do_POST(self):
                server._dispatch(self, "POST")

            def do_PATCH(self):
                server._dispatch(self, "PATCH")

            def do_DELETE(self):
                server._dispatch(self, "DELETE")

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.httpd.daemon_threads = True
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}"
        self._thread = threading.Thread(target=self.httpd.serve_forever, kwargs={"poll_interval": 0.02},
                                        daemon=True)

    def start(self):
        self._thread.start()
        return self

    def add_route(self, method: str, pattern: str, fn):
        """fn(match, query, body, headers) -> (status, payload[, extra_headers]).

        payload may be a dict/list (JSON), a RawBody, or None (with status 204).
        Added routes are checked before the built-in ones."""
        self.routes.insert(0, (method, pattern, fn))

    def current_request(self) -> Request:
        """The Request being handled on this thread (set before before_request hooks run)."""
        return self._local.request

    def stop(self):
        self.httpd.shutdown()
        self.httpd.server_close()

    # ---- route handlers ---------------------------------------------------
    def _list_rides(self, m, q, b, h):
        limit = _int_param(q, "limit", 10, 1, 100)
        offset = _int_param(q, "offset", 0, 0, 10**9)
        before = _int_param(q, "before_id", None, 1, 10**12)
        rows, total = self.service.list_rides(limit, offset, q.get("q", [""])[0][:60], before)
        return 200, {"items": rows, "total": total}, {"X-Total-Count": str(total)}

    def _create_ride(self, m, q, b, h):
        ride, created = self.service.create_ride(b, h.get("Idempotency-Key"))
        return (201 if created else 200), ride, {"Idempotent-Replay": "false" if created else "true"}

    def _drivers(self, m, q, b, h):
        online = q.get("online", [None])[0]
        if online not in (None, "true", "false"):
            raise ValidationError("online", "true or false")
        return 200, self.service.drivers(None if online is None else online == "true")

    # ---- the request pipeline --------------------------------------------
    def _dispatch(self, req: BaseHTTPRequestHandler, method: str):
        parsed = urllib.parse.urlsplit(req.path)
        path, query = parsed.path, urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
        self.trace.hop("HTTP route", f"{method} {path} received")
        extra = {}
        try:
            length = int(req.headers.get("Content-Length") or 0)
            raw = req.rfile.read(length) if length else b""
            fault = self.faults.get(path)
            if fault:
                item = fault.popleft()
                if isinstance(item, str) and item.startswith("delay:"):
                    time.sleep(float(item.split(":")[1]))
                else:
                    raise _Fault(int(item))
            try:
                body = json.loads(raw) if raw else None
            except json.JSONDecodeError:
                raise ValidationError("body", "malformed JSON") from None
            request = Request(method, path, query, req.headers, body, req.client_address[0])
            self._local.request = request
            for hook in self.before_request:
                hook(request)
            matched_path = False
            for route_method, pattern, fn in self.routes:
                match = re.fullmatch(pattern, path)
                if match:
                    matched_path = True
                    if route_method == method:
                        out = fn(match, query, body, req.headers)
                        status, payload = out[0], out[1]
                        extra = out[2] if len(out) > 2 else {}
                        break
            else:
                if matched_path:
                    status, payload = 405, {"error": f"{method} is not allowed on {path}"}
                else:
                    status, payload = 404, {"error": f"no route for {path}"}
        except _Fault as fault_exc:
            status, payload = fault_exc.status, {"error": f"injected fault {fault_exc.status}"}
            if status == 500:
                payload["ref"] = uuid.uuid4().hex[:8]
        except AppError as exc:
            status, payload = exc.status, exc.payload()
            extra = dict(exc.headers)
        except Exception as exc:                        # a bug: log it, never leak internals
            ref = uuid.uuid4().hex[:8]
            status, payload = 500, {"error": "internal server error", "ref": ref}
            self.log.append(("ERROR", f"{ref}: {exc!r}", 500))
        self.log.append((method, req.path, status))
        self.trace.hop("HTTP route", f"respond {status}")
        if status == 204 or payload is None:
            data, ctype = b"", None
        elif isinstance(payload, RawBody):
            data = payload.data.encode() if isinstance(payload.data, str) else payload.data
            ctype = payload.content_type
        elif isinstance(payload, str):
            data, ctype = payload.encode(), "text/html; charset=utf-8"
        else:
            data, ctype = json.dumps(payload).encode(), "application/json"
        try:
            req.send_response(status)
            if ctype:
                req.send_header("Content-Type", ctype)
            req.send_header("Content-Length", str(len(data)))
            req.send_header("X-Content-Type-Options", "nosniff")
            for k, v in extra.items():
                req.send_header(k, v)
            req.end_headers()
            req.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):  # the client gave up (timeout lab)
            pass


class _Fault(Exception):
    def __init__(self, status):
        self.status = status


# =============================================================================
# Layer 3: the HTTP client
# =============================================================================
RETRYABLE = {502, 503, 504}


class NetworkError(Exception):
    def __init__(self, message, attempts):
        super().__init__(message)
        self.attempts = attempts


@dataclass
class Response:
    status: int
    body: object
    headers: dict = field(default_factory=dict)
    attempts: int = 1

    @property
    def ok(self):
        return 200 <= self.status < 300


class ApiClient:
    def __init__(self, base_url: str, trace: Trace, timeout: float = 3.0):
        self.base_url, self.trace, self.timeout = base_url, trace, timeout
        self.requests = 0
        self.default_headers: dict = {}             # e.g. {"Authorization": "Bearer ..."} after login
        self._lock = threading.Lock()
        self._opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))  # localhost: no proxy

    def request(self, method, path, body=None, headers=None, timeout=None) -> Response:
        self.trace.hop("HTTP client", f"{method} {path}")
        with self._lock:
            self.requests += 1
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base_url + path, data=data, method=method,
                                     headers={"Content-Type": "application/json", **self.default_headers,
                                              **(headers or {})})
        try:
            with self._opener.open(req, timeout=timeout or self.timeout) as resp:
                status, raw, hdrs = resp.status, resp.read(), dict(resp.headers)
        except urllib.error.HTTPError as err:          # 4xx/5xx still carry a JSON body
            status, raw, hdrs = err.code, err.read(), dict(err.headers)
        ctype = hdrs.get("Content-Type", "")
        if not raw:
            payload = None
        elif ctype.startswith("application/json"):
            payload = json.loads(raw)
        else:
            payload = raw.decode()
        self.trace.hop("HTTP client", f"{status} received")
        return Response(status, payload, hdrs)

    def get(self, path, **kw):
        return self.request("GET", path, **kw)

    def post(self, path, body=None, **kw):
        return self.request("POST", path, body, **kw)

    def patch(self, path, body=None, **kw):
        return self.request("PATCH", path, body, **kw)

    def request_with_retry(self, method, path, body=None, headers=None, retries=3, timeout=None,
                           backoff=0.02) -> Response:
        """Retry only what may succeed next time: 502/503/504, timeouts, refused connections.

        4xx means the request itself is wrong and 500 means a bug - retrying will not help.
        Only safe for GET, or for POST with an Idempotency-Key.
        """
        for attempt in range(1, retries + 2):
            try:
                resp = self.request(method, path, body, headers, timeout)
            except (urllib.error.URLError, TimeoutError, ConnectionError, socket.timeout) as exc:
                if attempt > retries:
                    raise NetworkError(str(getattr(exc, "reason", exc)), attempt) from None
                time.sleep(backoff * 2 ** (attempt - 1))
                continue
            if resp.status in RETRYABLE and attempt <= retries:
                time.sleep(backoff * 2 ** (attempt - 1))
                continue
            resp.attempts = attempt
            return resp
        raise AssertionError("unreachable")


# =============================================================================
# Layers 1-2: a headless screen with buttons and event handlers
# =============================================================================
class Button:
    def __init__(self, label: str, handler, trace: Trace):
        self.label, self.handler, self.trace = label, handler, trace
        self.enabled = True
        self.clicks = self.ignored = 0

    def click(self, *args):
        self.clicks += 1
        if not self.enabled:                           # a disabled button does nothing
            self.ignored += 1
            return None
        self.trace.hop("UI button", f"click '{self.label}'")
        return self.handler(*args)


def client_side_errors(form: dict) -> list[str]:
    """Quick checks a form can do before sending anything. Not the authority - the server is."""
    errors = []
    if not str(form.get("passenger", "")).strip():
        errors.append("passenger: please enter a name")
    try:
        float(form.get("km", ""))
    except (TypeError, ValueError):
        errors.append("km: please enter a number")
    for name in ("pickup", "destination"):              # these are drop-down lists in the UI
        if form.get(name) not in PLACES:
            errors.append(f"{name}: choose a place from the list")
    return errors


def user_message(resp: Response | None, error: Exception | None = None) -> str:
    """What a person sees for each kind of failure. Never show tracebacks or SQL."""
    if error is not None:
        return "Cannot reach the server - check your connection and try again."
    if resp.ok:
        return ""
    body = resp.body if isinstance(resp.body, dict) else {}
    if resp.status == 422:
        return f"Please check {body.get('field', 'the form')}: {body.get('error', '')}"
    if resp.status == 404:
        return "Not found - it may have been deleted."
    if resp.status == 409:
        return f"Not saved: {body.get('error', 'conflict')}"
    if resp.status == 401:
        return "Please sign in."
    if resp.status == 403:
        return "You are not allowed to do that."
    if resp.status == 429:
        wait = resp.headers.get("Retry-After") or body.get("retry_after") or "a few"
        return f"Too many requests - try again in {wait} s."
    if resp.status >= 500:
        ref = body.get("ref")
        return "Something went wrong on our side." + (f" Reference {ref}." if ref else "") + " Please try later."
    return f"Request failed ({resp.status})."


class RideScreen:
    """The 'front end'. Each button's handler reads the form, calls the API and redraws.

    'Book' behaves like fetch(): it returns immediately with a Future while the request is in
    flight, so a second click can arrive before the first response - exactly as in a browser.
    """

    def __init__(self, client: ApiClient, trace: Trace, page_size=10, pagination="keyset",
                 disable_while_sending=True, send_request_key=True, use_versions=True, retries=3):
        self.client, self.trace = client, trace
        self.page_size, self.pagination = page_size, pagination
        self.disable_while_sending, self.send_request_key = disable_while_sending, send_request_key
        self.use_versions, self.retries = use_versions, retries
        self.form = {"passenger": "", "pickup": "UCC", "destination": "Cork Airport", "km": "5.8"}
        self.table: list[dict] = []
        self.drivers: list[dict] = []
        self.stats: dict | None = None
        self.editing: dict | None = None
        self.total: int | None = None
        self.banner = ""
        self._form_key: str | None = None
        self._pending: list[Future] = []
        self._ui_lock = threading.Lock()                # stands in for "back on the UI thread"
        self._pool = ThreadPoolExecutor(max_workers=4)
        b = lambda label, fn: Button(label, fn, trace)
        self.load_button = b("Load rides", self._on_load)
        self.more_button = b("Load more", self._on_more)
        self.book_button = b("Book", self._on_book)
        self.search_button = b("Search", self._on_search)
        self.open_button = b("Open", self._on_open)
        self.save_button = b("Save", self._on_save)
        self.assign_button = b("Assign", self._on_assign)
        self.complete_button = b("Complete", lambda rid: self._on_finish(rid, "complete"))
        self.cancel_button = b("Cancel ride", lambda rid: self._on_finish(rid, "cancel"))
        self.drivers_button = b("Drivers", self._on_drivers)
        self.joined_button = b("Rides + drivers", self._on_joined)
        self.stats_button = b("Stats", self._on_stats)
        self.refresh_button = b("Refresh", self._on_refresh)

    # ---- helpers -----------------------------------------------------------
    def _handler(self, what):
        self.trace.hop("event handler", what)

    def _show_error(self, resp=None, error=None):
        self.banner = user_message(resp, error)
        self.trace.hop("event handler", f"show banner: {self.banner}" if self.banner else "render")

    def _upsert(self, ride: dict, front=True):
        for i, row in enumerate(self.table):
            if row["id"] == ride["id"]:
                self.table[i] = ride
                return
        self.table.insert(0, ride) if front else self.table.append(ride)

    def wait(self):
        """Wait for every in-flight request (tests and labs call this; a UI would not block)."""
        while self._pending:
            self._pending.pop().result()

    def close(self):
        self.wait()
        self._pool.shutdown(wait=True)

    # ---- handlers ---------------------------------------------------------
    def _on_load(self):
        self._handler("read page size, build URL")
        resp = self.client.get(f"/api/rides?limit={self.page_size}")
        if not resp.ok:
            return self._show_error(resp)
        self.table = list(resp.body["items"])
        self.total = int(resp.headers["X-Total-Count"])
        self.more_button.enabled = len(resp.body["items"]) == self.page_size
        self.banner = ""
        self.trace.hop("event handler", f"render {len(self.table)} rows")
        return resp

    def _on_more(self):
        self._handler(f"next page ({self.pagination})")
        if self.pagination == "offset":
            url = f"/api/rides?limit={self.page_size}&offset={len(self.table)}"
        else:
            url = f"/api/rides?limit={self.page_size}&before_id={self.table[-1]['id']}"
        resp = self.client.get(url)
        if not resp.ok:
            return self._show_error(resp)
        self.table.extend(resp.body["items"])          # append as received - duplicates show up
        self.total = int(resp.headers["X-Total-Count"])
        self.more_button.enabled = len(resp.body["items"]) == self.page_size
        return resp

    def _on_book(self):
        self._handler("read form, client-side checks")
        errors = client_side_errors(self.form)
        if errors:
            self.banner = "; ".join(errors)
            self.trace.hop("event handler", "show banner (no request sent)")
            return None
        body = {"passenger": self.form["passenger"], "pickup": self.form["pickup"],
                "destination": self.form["destination"], "distance_km": float(self.form["km"])}
        if self.form.get("driver_id") is not None:
            body["driver_id"] = self.form["driver_id"]
        if self._form_key is None:                     # one key per filled-in form, reused on retry
            self._form_key = uuid.uuid4().hex
        headers = {"Idempotency-Key": self._form_key} if self.send_request_key else {}
        if self.disable_while_sending:
            self.book_button.enabled = False
        future = self._pool.submit(self._send_booking, body, headers)
        self._pending.append(future)
        return future

    def _send_booking(self, body, headers):
        try:
            resp = self.client.post("/api/rides", body, headers=headers)
        except Exception as exc:
            with self._ui_lock:
                self._show_error(error=exc)
            raise
        finally:
            self.book_button.enabled = True
        with self._ui_lock:
            if resp.ok:
                self._upsert(resp.body)
                self.form.update(passenger="")
                self.form.pop("driver_id", None)
                self._form_key = None
                self.banner = f"Booked ride {resp.body['id']} - fare EUR {resp.body['fare_cents'] / 100:.2f}"
                self.trace.hop("event handler", "render new row, clear form")
            else:
                self._show_error(resp)
        return resp

    def _on_search(self, text: str):
        self._handler(f"search {text!r}")
        resp = self.client.get("/api/rides?" + urllib.parse.urlencode({"q": text, "limit": 100}))
        if not resp.ok:
            return self._show_error(resp)
        self.table = list(resp.body["items"])
        self.total = resp.body["total"]
        return resp

    def _on_open(self, ride_id: int):
        self._handler(f"open ride {ride_id}")
        resp = self.client.get(f"/api/rides/{ride_id}")
        if not resp.ok:
            return self._show_error(resp)
        self.editing = dict(resp.body)                 # the copy the user edits
        return resp

    def _on_save(self):
        self._handler("send the edited record")
        body = {"passenger": self.editing["passenger"], "destination": self.editing["destination"]}
        if self.use_versions:
            body["version"] = self.editing["version"]
        resp = self.client.patch(f"/api/rides/{self.editing['id']}", body)
        if resp.ok:
            self.editing = dict(resp.body)
            self._upsert(resp.body)
            self.banner = "Saved"
        else:
            self._show_error(resp)
        return resp

    def _on_assign(self, ride_id: int, driver_id: int):
        self._handler(f"assign driver {driver_id} to ride {ride_id}")
        resp = self.client.post(f"/api/rides/{ride_id}/assign", {"driver_id": driver_id})
        if resp.ok:
            self._upsert(resp.body)
            self.banner = ""
        else:
            self._show_error(resp)
        return resp

    def _on_finish(self, ride_id: int, action: str):
        self._handler(f"{action} ride {ride_id}")
        resp = self.client.post(f"/api/rides/{ride_id}/{action}")
        if resp.ok:
            self._upsert(resp.body)
        else:
            self._show_error(resp)
        return resp

    def _on_drivers(self):
        self._handler("load drivers")
        resp = self.client.get("/api/drivers")
        if resp.ok:
            self.drivers = resp.body
        return resp

    def _on_joined(self, strategy="join"):
        self._handler(f"rides with driver names ({strategy})")
        resp = self.client.get(f"/api/rides-with-drivers?strategy={strategy}")
        if resp.ok:
            self.table = resp.body
        return resp

    def _on_stats(self):
        self._handler("refresh stats")
        resp = self.client.get("/api/stats")
        if resp.ok:
            self.stats = resp.body
        return resp

    def _on_refresh(self, path="/api/stats"):
        """A GET that uses the retry policy and turns every failure into a readable message."""
        self._handler(f"refresh {path} (retry policy)")
        try:
            resp = self.client.request_with_retry("GET", path, retries=self.retries, timeout=0.25)
        except NetworkError as exc:
            self._show_error(error=exc)
            return exc
        if resp.ok:
            self.stats, self.banner = resp.body, ""
        else:
            self._show_error(resp)
        return resp

    # ---- what the person sees ------------------------------------------------
    def render(self, rows=8) -> str:
        lines = [f"[banner] {self.banner}" if self.banner else "[banner] -"]
        lines.append(f"{'id':>4}  {'passenger':<10} {'from':<16} {'to':<16} {'fare':>7}  status")
        for r in self.table[:rows]:
            if "pickup" in r:
                lines.append(f"{r['id']:>4}  {r['passenger']:<10} {r['pickup']:<16} {r['destination']:<16} "
                             f"{r['fare_cents'] / 100:>7.2f}  {r['status']}")
            else:
                lines.append(f"{r['id']:>4}  {r['passenger']:<10} driver: {r.get('driver')}")
        if len(self.table) > rows:
            lines.append(f"... {len(self.table) - rows} more")
        return "\n".join(lines)


# =============================================================================
# The whole application in one object
# =============================================================================
class App:
    """Database + service + API server + client + screen, wired together and running.

        with App(drivers=4, rides=3) as app:
            app.screen.load_button.click()
            print(app.screen.render())
    """

    def __init__(self, drivers=4, rides=0, assigned=False, offline=(), timeout=3.0, base_url=None, **screen_options):
        self.trace = Trace()
        self.db = Database(self.trace)
        self.service = RideService(self.db, self.trace)
        self.service.seed(drivers, rides, assigned, offline)
        self.server = ApiServer(self.service, self.trace).start()
        self.client = ApiClient(base_url or self.server.url, self.trace, timeout)
        self.screen = RideScreen(self.client, self.trace, **screen_options)

    def close(self):
        self.screen.close()
        self.server.stop()
        self.db.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def unused_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


# =============================================================================
# Labs
# =============================================================================
def result(number, title, kind, labels, rows, xlabel, ylabel, notes="", log=False, xticks=None,
           yticks=None, extra=None):
    return {"number": number, "title": title, "kind": kind, "labels": list(labels), "rows": rows,
            "xlabel": xlabel, "ylabel": ylabel, "notes": notes, "log": log, "xticks": xticks,
            "yticks": yticks, "extra": extra or {}}


# ----------------------------------------------------------------------------- A01
def lab_01():
    """One click, traced through every layer and back."""
    with App(drivers=4, rides=3) as app:
        app.trace.clear()
        resp = app.screen.load_button.click()
        hops = list(app.trace.hops)
        lines = app.trace.lines()
        assert resp.status == 200 and len(app.screen.table) == 3
        layers = [LAYERS.index(layer) for _, layer, _ in hops]
        assert layers[0] == 0 and max(layers) == LAYERS.index("database")
        assert layers[-1] == LAYERS.index("event handler")            # back up to the screen
        elapsed = (hops[-1][0] - hops[0][0]) * 1000
    rows = [(i + 1, layer) for i, layer in enumerate(layers)]
    return result(1, "One 'Load rides' click travels down to SQLite and back", "line", ["layer reached"], rows,
                  "hop number", "layer", yticks=LAYERS,
                  notes=f"{len(hops)} hops in {elapsed:.1f} ms (machine-dependent). The route runs two SELECTs "
                        "(COUNT for the total, then the page) before the response climbs back to the screen.",
                  extra={"trace": lines})


# ----------------------------------------------------------------------------- A02
def lab_02():
    """Book button: form -> POST -> INSERT -> 201 -> new row on screen."""
    attempts = [
        ("Aoife", "UCC", "Cork Airport", "5.8"),
        ("", "UCC", "Douglas", "4"),                      # stopped by the form, no request
        ("Brian", "Kent Station", "English Market", "1.2"),
        ("Ciara", "Douglas", "Douglas", "3"),              # passes the form, server says 422
        ("Darragh", "Mahon Point", "Blackrock Castle", "2.5"),
        ("Eimear", "Ballincollig", "UCC", "ten"),          # stopped by the form
        ("Fionn", "UCC", "Kent Station", "2.2"),
    ]
    rows, outcomes = [], []
    with App(drivers=4) as app:
        s = app.screen
        for i, (name, a, b, km) in enumerate(attempts, 1):
            s.form.update(passenger=name, pickup=a, destination=b, km=km)
            future = s.book_button.click()
            resp = future.result() if future else None
            outcomes.append(f"click {i}: " + (f"HTTP {resp.status}" if resp else "no request") + f" - {s.banner}")
            rows.append((i, app.db.count("rides"), len(s.table), app.client.requests))
        assert app.db.count("rides") == len(s.table) == 4
        assert app.client.requests == 5
        assert {r["id"] for r in s.table} == {r["id"] for r in app.db.query("SELECT id FROM rides")}
    return result(2, "Book button: rows in the database, rows on screen, requests sent", "line",
                  ["rows in database", "rows on screen", "HTTP requests sent"], rows, "click on 'Book'", "count",
                  notes="Clicks 2 and 6 never leave the browser (form checks). Click 4 reaches the server and is "
                        "rejected with 422, so nothing is inserted. The screen always matches the database.",
                  extra={"outcomes": outcomes})


# ----------------------------------------------------------------------------- A03
BAD_BOOKINGS = [
    ("valid booking", {}),
    ("empty passenger", {"passenger": ""}),
    ("passenger of 60 chars", {"passenger": "X" * 60}),
    ("km = 'abc'", {"distance_km": "abc"}),
    ("km = -3", {"distance_km": -3}),
    ("km = 500", {"distance_km": 500}),
    ("pickup = destination", {"destination": "UCC"}),
    ("unknown place", {"destination": "Atlantis"}),
    ("driver_id 999 (missing)", {"driver_id": 999}),
]


def lab_03():
    """Which layer stops each bad input: the form, the API, or the database constraint?"""
    base = {"passenger": "Aoife", "pickup": "UCC", "destination": "Cork Airport", "distance_km": 5.8}
    rows = []
    with App(drivers=2) as app:
        for label, change in BAD_BOOKINGS:
            body = {**base, **change}
            form = {"passenger": body["passenger"], "pickup": body["pickup"],
                    "destination": body["destination"], "km": str(body["distance_km"])}
            ui = int(bool(client_side_errors(form)))
            api = int(app.client.post("/api/rides", body).status >= 400)            # bypass the form
            db = 0                                                                  # bypass the API too
            km = body["distance_km"]
            fare = fare_cents(km) if isinstance(km, (int, float)) else 350
            with app.db.lock:
                app.db.conn.execute("BEGIN")
                try:
                    app.db.conn.execute(
                        "INSERT INTO rides (passenger, pickup, destination, distance_km, fare_cents, driver_id) "
                        "VALUES (?, ?, ?, ?, ?, ?)",
                        (body["passenger"], body["pickup"], body["destination"], km, fare, body.get("driver_id")))
                except sqlite3.IntegrityError:
                    db = 1
                finally:
                    app.db.conn.execute("ROLLBACK")
            rows.append((label, ui, api, db))
        assert rows[0][1:] == (0, 0, 0)
        assert all(r[2] == 1 for r in rows[1:])                      # the API is the authority
        assert app.db.count("rides") == 1                            # only the valid booking was stored
    return result(3, "Defence in depth: which layer rejects each input (1 = rejected)", "heatmap",
                  ["form (client)", "API (4xx)", "DB constraint"], rows, "layer", "input",
                  notes="The form catches typos early but can be bypassed (curl, scripts). The API rejects every "
                        "bad input. The DB constraints are the last line: they cannot know the list of places, "
                        "and the missing driver is only caught by the FOREIGN KEY (the API turns it into 409).")


# ----------------------------------------------------------------------------- A04
def keystrokes(text: str, pauses: dict[int, int], gap_ms=110):
    """(time_ms, text so far) for each key press; pauses[i] adds a pause before key i."""
    t, out = 0, []
    for i in range(1, len(text) + 1):
        t += gap_ms + pauses.get(i - 1, 0)
        out.append((t, text[:i]))
    return out


def debounced(events, delay_ms):
    """Texts that would fire: a search runs only after `delay_ms` with no new key press."""
    fired = []
    for i, (t, text) in enumerate(events):
        if i == len(events) - 1 or events[i + 1][0] - t >= delay_ms:
            fired.append(text)
    return fired


def lab_04():
    """Search box: every keystroke vs debounce vs a Search button."""
    events = keystrokes("airport", pauses={3: 500})        # "air" ... pause ... "port"
    strategies = {
        "search on every key": [text for _, text in events],
        "debounce 300 ms": debounced(events, 300),
        "debounce 800 ms": debounced(events, 800),
        "Search button": [events[-1][1]],
    }
    rows, finals = [], {}
    with App(drivers=2, rides=60) as app:
        for name, texts in strategies.items():
            before_req, before_sql = app.client.requests, len(app.db.statements)
            sent_rows = 0
            for text in texts:
                resp = app.screen.search_button.click(text)
                sent_rows += len(resp.body["items"])
            finals[name] = [r["id"] for r in app.screen.table]
            rows.append((name, app.client.requests - before_req, app.db.selects_since(before_sql), sent_rows))
        wildcard = app.screen.search_button.click("%").body["total"]
        assert wildcard == 0                                   # '%' is escaped, not a wildcard
    assert len({tuple(v) for v in finals.values()}) == 1         # every strategy ends on the same results
    return result(4, "Search-as-you-type: requests, SQL queries and rows sent for 'airport'", "bar",
                  ["HTTP requests", "SQL SELECTs", "rows sent to the screen"], rows, "strategy", "count",
                  notes=f"All strategies end with the same {len(finals['Search button'])} rides on screen. "
                        "Debouncing waits for a pause in typing; the user paused once after 'air'. "
                        "The query uses LIKE ? with escaped % and _, so searching '%' finds nothing.")


# ----------------------------------------------------------------------------- A05
def lab_05():
    """Double-clicking 'Book': disabled button, idempotency key, both, neither."""
    configs = [("no protection", False, False), ("idempotency key only", False, True),
               ("disable button only", True, False), ("both", True, True)]
    rows = []
    for name, disable, key in configs:
        with App(drivers=2, disable_while_sending=disable, send_request_key=key) as app:
            app.server.faults["/api/rides"] = deque(["delay:0.15", "delay:0.15"])  # slow network
            app.screen.form.update(passenger="Aoife", pickup="UCC", destination="Cork Airport", km="5.8")
            app.screen.book_button.click()
            app.screen.book_button.click()                 # second click 0 ms later, first still in flight
            app.screen.wait()
            rows.append((name, app.client.requests, app.db.count("rides"), len(app.screen.table)))
    assert rows[0][2] == 2 and all(r[2] == 1 for r in rows[1:])
    return result(5, "Double click on 'Book' while the first request is still in flight", "bar",
                  ["requests sent", "rides in database", "rows on screen"], rows, "protection", "count",
                  notes="Disabling the button stops the second request in the browser; the idempotency key "
                        "makes the server return the first ride (200, Idempotent-Replay: true) for a repeat. "
                        "Use both: the key also protects automatic retries and other clients.")


# ----------------------------------------------------------------------------- A06
def lab_06():
    """'Load more' with offset vs keyset pagination while someone else books a ride."""
    series = {}
    for mode in ("offset", "keyset"):
        with App(drivers=2, rides=47, pagination=mode, page_size=10) as app:
            s = app.screen
            s.load_button.click()
            points = [(len(s.table), len(s.table) - len({r["id"] for r in s.table}))]
            clicks = 1
            while s.more_button.enabled:
                if clicks == 2:                              # another user books between clicks
                    app.client.post("/api/rides", {"passenger": "Newcomer", "pickup": "UCC",
                                                   "destination": "Douglas", "distance_km": 4})
                s.more_button.click()
                clicks += 1
                points.append((len(s.table), len(s.table) - len({r["id"] for r in s.table})))
            series[mode] = points
            ignored_before = s.more_button.ignored
            s.more_button.click()                            # disabled at the end: no request
            assert s.more_button.ignored == ignored_before + 1
    n = max(len(v) for v in series.values())
    pad = lambda pts, i: pts[min(i, len(pts) - 1)]
    rows = [(i + 1, pad(series["offset"], i)[0], pad(series["offset"], i)[1],
             pad(series["keyset"], i)[0], pad(series["keyset"], i)[1]) for i in range(n)]
    assert series["offset"][-1][1] >= 1 and series["keyset"][-1][1] == 0
    return result(6, "'Load more' (page size 10) while a new ride is inserted after click 2", "line",
                  ["offset: rows shown", "offset: duplicate rows", "keyset: rows shown", "keyset: duplicate rows"],
                  rows, "click (1 = Load rides, then Load more)", "rows",
                  notes="OFFSET counts positions: the new ride pushes every row down one place, so the next page "
                        "repeats a row. Keyset pagination (WHERE id < last_id_seen) cannot repeat. The button is "
                        "disabled when a page comes back short.")


# ----------------------------------------------------------------------------- A07
def lab_07():
    """Two people edit the same ride: last write wins vs version check (optimistic locking)."""
    rows, story = [], []
    for name, versions in (("last write wins", False), ("version check", True)):
        with App(drivers=2, rides=1, use_versions=versions) as app:
            ride_id = app.db.query("SELECT id FROM rides")[0]["id"]
            alice = app.screen
            bob = RideScreen(app.client, app.trace, use_versions=versions)   # a second screen, same server
            alice.open_button.click(ride_id)
            bob.open_button.click(ride_id)
            new_dest = next(p for p in PLACES if p not in (alice.editing["pickup"], alice.editing["destination"]))
            alice.editing["destination"] = new_dest          # Alice changes the destination
            bob.editing["passenger"] = "Bob's guest"         # Bob, at the same time, renames the passenger
            accepted = conflicts = 0
            for screen in (alice, bob):
                resp = screen.save_button.click()
                accepted += resp.ok
                conflicts += resp.status == 409
            if bob.banner.startswith("Not saved"):           # Bob reloads, re-applies his edit, saves again
                story.append(f"{name}: Bob saw '{bob.banner}'")
                bob.open_button.click(ride_id)
                bob.editing["passenger"] = "Bob's guest"
                accepted += bob.save_button.click().ok
            final = app.service.get_ride(ride_id)
            lost = int(final["destination"] != new_dest) + int(final["passenger"] != "Bob's guest")
            story.append(f"{name}: final destination={final['destination']}, passenger={final['passenger']}, "
                         f"version={final['version']}")
            rows.append((name, accepted, conflicts, lost))
            bob.close()
    assert rows[0][3] == 1 and rows[1][3] == 0 and rows[1][2] == 1
    return result(7, "Concurrent edits of one ride", "bar", ["saves accepted", "409 conflicts shown", "lost updates"],
                  rows, "strategy", "count",
                  notes="Without a version, Bob's save sends the old destination and silently erases Alice's "
                        "change. With 'UPDATE ... WHERE id = ? AND version = ?' Bob gets 409, reloads and keeps "
                        "both edits.", extra={"story": story})


# ----------------------------------------------------------------------------- A08
def lab_08():
    """'Assign' writes three rows; a crash half-way with and without a transaction."""
    rows = {}
    for mode, atomic in (("no transaction", False), ("transaction", True)):
        with App(drivers=12, rides=12) as app:
            app.service.atomic_assign = atomic
            app.service.crash_assign_ids = {3, 6, 9, 12}
            statuses = [app.screen.assign_button.click(i, i).status for i in range(1, 13)]
            db = app.db
            inconsistent = db.query(
                "SELECT COUNT(*) AS n FROM rides r JOIN drivers d ON d.id = r.driver_id "
                "WHERE r.status = 'assigned' AND (d.busy = 0 OR NOT EXISTS "
                "(SELECT 1 FROM audit a WHERE a.ride_id = r.id))")[0]["n"]
            rows[mode] = [db.count("rides", "status = 'assigned'"), db.count("drivers", "busy = 1"),
                          db.count("audit"), inconsistent, statuses.count(500)]
            if atomic:
                assert inconsistent == 0
            assert app.screen.banner.startswith("Something went wrong")
    metrics = ["rides marked assigned", "drivers marked busy", "audit rows", "inconsistent rides", "HTTP 500 shown"]
    table = [(m, rows["no transaction"][i], rows["transaction"][i]) for i, m in enumerate(metrics)]
    assert rows["no transaction"][3] == 4
    return result(8, "12 'Assign' clicks, 4 crash after the first write", "bar", ["no transaction", "transaction"],
                  table, "metric", "count",
                  notes="Without a transaction the 4 crashed rides stay 'assigned' to drivers who are still free "
                        "and have no audit entry. With BEGIN ... COMMIT the crash triggers ROLLBACK: the ride stays "
                        "'requested' and the user can simply try again.")


# ----------------------------------------------------------------------------- A09
def lab_09():
    """'Rides + drivers' button: N+1 queries vs one JOIN as the table grows."""
    rows = []
    for n in (5, 10, 20, 40, 80):
        with App(drivers=8, rides=n, assigned=True) as app:
            counts, results = [], []
            for strategy in ("n_plus_1", "join"):
                mark = len(app.db.statements)
                resp = app.screen.joined_button.click(strategy)
                counts.append(app.db.selects_since(mark))
                results.append(resp.body)
            assert results[0] == results[1]                # same answer, different cost
            rows.append((n, *counts))
    assert all(r[1] == r[0] + 1 and r[2] == 1 for r in rows)
    return result(9, "SQL SELECTs run for one click on 'Rides + drivers'", "line",
                  ["one query per row (N+1)", "LEFT JOIN"], rows, "rides in the table", "SELECT statements",
                  notes="Counted with sqlite3's set_trace_callback. N+1 is easy to write by accident (a loop that "
                        "looks up each ride's driver) and grows with the data; the JOIN stays at one query.")


# ----------------------------------------------------------------------------- A10
def lab_10():
    """'Stats' button with no cache, a cache that is never invalidated, and invalidate-on-write."""
    rows = []
    for mode in ("none", "no-invalidation", "invalidate-on-write"):
        with App(drivers=4, rides=10) as app:
            app.service.stats_cache = mode
            mark, stale = len(app.db.statements), 0
            for click in range(1, 11):
                if click in (4, 8):                             # someone books between refreshes
                    app.screen.form.update(passenger=f"P{click}", pickup="UCC", destination="Douglas", km="3")
                    app.screen.book_button.click().result()
                app.screen.stats_button.click()
                stale += app.screen.stats["total_rides"] != app.db.count("rides")
            rows.append((mode, app.db.selects_since(mark, "GROUP BY status"), stale))
    assert rows[0] == ("none", 10, 0) and rows[1][2] > 0 and rows[2][2] == 0 and rows[2][1] == 3
    return result(10, "10 clicks on 'Stats' with 2 bookings in between", "bar",
                  ["aggregate queries on the database", "stale screens shown"], rows, "cache strategy", "count",
                  notes="A cache that is never invalidated is fast and wrong. Clearing it on every write keeps the "
                        "screen correct and still saves 7 of 10 queries here.")


# ----------------------------------------------------------------------------- A11
def lab_11():
    """What the user sees when things go wrong, and which failures are retried."""
    cases = [
        ("200 OK", "/api/stats", None),
        ("404 wrong URL", "/api/statistics", None),
        ("422 bad parameter", "/api/rides?limit=0", None),
        ("500 server bug", "/api/stats", [500] * 5),
        ("503 twice, then OK", "/api/stats", [503, 503]),
        ("timeout once, then OK", "/api/stats", ["delay:0.6"]),
        ("server down", "/api/stats", "down"),
    ]
    rows, messages = [], []
    for label, path, fault in cases:
        down_url = f"http://127.0.0.1:{unused_port()}" if fault == "down" else None
        with App(drivers=2, rides=3, base_url=down_url, retries=3) as app:
            if fault and fault != "down":
                app.server.faults[urllib.parse.urlsplit(path).path] = deque(fault)
            out = app.screen.refresh_button.click(path)
            attempts = out.attempts
            ok = int(isinstance(out, Response) and out.ok)
            messages.append(f"{label}: {app.screen.banner or 'data shown'}")
            rows.append((label, attempts, ok))
    expected = {"200 OK": (1, 1), "404 wrong URL": (1, 0), "422 bad parameter": (1, 0), "500 server bug": (1, 0),
                "503 twice, then OK": (3, 1), "timeout once, then OK": (2, 1), "server down": (4, 0)}
    assert {r[0]: r[1:] for r in rows} == expected
    return result(11, "Retry policy: attempts made and outcome for each failure", "bar",
                  ["HTTP attempts", "succeeded (1 = data shown)"], rows, "what went wrong", "count",
                  notes="Retry only transient failures (503, timeouts, refused connections) with back-off; never "
                        "4xx (the request is wrong) or 500 (a bug). Every failure becomes a plain sentence - "
                        "never a stack trace.", extra={"messages": messages})


# ----------------------------------------------------------------------------- A12
def lab_12():
    """A complete user journey, checking after each step that the screen matches the database."""
    steps = []
    with App(drivers=3, rides=2) as app:
        s, db = app.screen, app.db

        def check(name):
            s.wait()
            for row in s.table:                            # every row on screen equals the DB row
                stored = app.service.get_ride(row["id"]) if "pickup" in row else None
                assert stored is None or (stored["status"], stored["driver_id"]) == (row["status"], row["driver_id"]), name
            steps.append((name, db.count("rides"), db.count("rides", "status = 'requested'"),
                          db.count("drivers", "busy = 1"), db.count("audit"), app.client.requests))

        s.drivers_button.click(); s.load_button.click(); check("open app")
        s.form.update(passenger="Aoife", pickup="UCC", destination="Cork Airport", km="5.8")
        aoife = s.book_button.click().result().body["id"]; check("book Aoife")
        s.form.update(passenger="Brian", pickup="Kent Station", destination="Douglas", km="4.1")
        brian = s.book_button.click().result().body["id"]; check("book Brian")
        driver = next(d["id"] for d in s.drivers if d["online"] and not d["busy"])
        assert s.assign_button.click(aoife, driver).status == 200; check("assign driver")
        assert s.assign_button.click(brian, driver).status == 409; check("driver busy (409)")
        assert s.complete_button.click(aoife).status == 200; check("complete Aoife")
        assert s.cancel_button.click(brian).status == 200; check("cancel Brian")
        assert s.cancel_button.click(brian).status == 409; check("cancel again (409)")
        s.stats_button.click(); s.load_button.click(); check("refresh")
        assert s.stats["total_rides"] == db.count("rides") == 4
    rows = [(i + 1, *v[1:]) for i, v in enumerate(steps)]
    return result(12, "End-to-end journey: database state after each user action", "line",
                  ["rides", "rides waiting", "busy drivers", "audit rows", "HTTP requests (cumulative)"], rows,
                  "step", "count", xticks=[v[0] for v in steps],
                  notes="After every step the lab asserts that each ride on screen has the same status and driver "
                        "as its row in SQLite. Rejected actions (409) change nothing.")


LABS = {i: globals()[f"lab_{i:02}"] for i in range(1, 13)}
TITLES = {
    1: "Tracing one click through every layer", 2: "Form -> POST -> INSERT -> screen",
    3: "Validation in the form, the API and the database", 4: "Search-as-you-type and debouncing",
    5: "Double submit: disabled button and idempotency keys", 6: "Load more: offset vs keyset pagination",
    7: "Concurrent edits and optimistic locking", 8: "Transactions across three tables",
    9: "The N+1 query problem", 10: "Caching and invalidation",
    11: "Errors, timeouts and retries", 12: "An end-to-end user journey",
}


def experiment(number):
    if number not in LABS:
        raise ValueError(f"Unknown lab: {number}")
    return LABS[number]()


def save_experiment(res, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    ident = f"app_{res['number']:02}"
    with (out / f"{ident}.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([res["xlabel"], *res["labels"]])
        w.writerows(res["rows"])
    (out / f"{ident}.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    fig, ax = plt.subplots(figsize=(10, 5.2))
    rows, labels = res["rows"], res["labels"]
    if res["kind"] == "line":
        step = res["number"] == 1
        for j, label in enumerate(labels):
            xs, ys = [r[0] for r in rows], [r[j + 1] for r in rows]
            if step:
                ax.step(xs, ys, where="mid", marker="o", label=label)
            else:
                ax.plot(xs, ys, marker="os^Dv"[j % 5], linestyle=["-", "--", ":", "-."][j % 4],
                        markersize=7 - j, label=label)
        if len(labels) > 1:
            ax.legend()
        if res["xticks"]:
            ax.set_xticks([r[0] for r in rows])
            ax.set_xticklabels(res["xticks"], rotation=25, ha="right")
    elif res["kind"] == "bar":
        width = 0.8 / len(labels)
        xs = range(len(rows))
        for j, label in enumerate(labels):
            bars = ax.bar([x + j * width for x in xs], [r[j + 1] for r in rows], width, label=label)
            ax.bar_label(bars, fontsize=7)
        ax.set_xticks([x + width * (len(labels) - 1) / 2 for x in xs])
        ax.set_xticklabels([str(r[0]) for r in rows], rotation=20, ha="right")
        if len(labels) > 1:
            ax.legend()
    else:
        grid = [list(r[1:]) for r in rows]
        ax.imshow(grid, cmap="Blues", aspect="auto", vmin=0, vmax=1.4)
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels)
        ax.set_yticks(range(len(rows)))
        ax.set_yticklabels([str(r[0]) for r in rows])
        for i, row in enumerate(grid):
            for j, v in enumerate(row):
                ax.text(j, i, "rejected" if v else "-", ha="center", va="center", fontsize=8,
                        color="white" if v else "black")
    if res.get("yticks"):
        ax.set_yticks(range(len(res["yticks"])))
        ax.set_yticklabels(res["yticks"])
        ax.invert_yaxis()
    if res["log"]:
        ax.set_yscale("log")
    elif res["kind"] != "heatmap" and not res.get("yticks"):
        from matplotlib.ticker import MaxNLocator
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        if res["kind"] == "line" and not res["xticks"]:
            ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_title(f"A{res['number']:02} - {res['title']}")
    ax.set_xlabel(res["xlabel"])
    ax.set_ylabel(res["ylabel"])
    ax.grid(alpha=.2)
    fig.tight_layout()
    fig.savefig(out / f"{ident}.png", dpi=150)
    plt.close(fig)
    return out / f"{ident}.png"


def self_test():
    assert len(LABS) == 12
    assert fare_cents(3) == 860
    assert client_side_errors({"passenger": "A", "pickup": "UCC", "destination": "Douglas", "km": "2"}) == []
    assert len(client_side_errors({"passenger": " ", "pickup": "X", "destination": "Douglas", "km": "x"})) == 3
    assert debounced([(0, "a"), (100, "ai"), (900, "air")], 300) == ["ai", "air"]
    assert _escape_like("50%_off") == "50\\%\\_off"
    for n in LABS:
        res = experiment(n)
        assert res["rows"] and all(len(r) == len(res["labels"]) + 1 for r in res["rows"]), n
    print("All 12 app-integration labs ran and their internal assertions passed.")


# =============================================================================
# A clickable page for --serve (same API; open it with DevTools -> Network)
# =============================================================================
DEMO_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>ATLAS Go desk - integration lab</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
 body{font:15px system-ui,sans-serif;max-width:900px;margin:2rem auto;padding:0 1rem;color:#1f2933}
 fieldset{border:1px solid #cbd2d9;border-radius:8px;margin-bottom:1rem} label{margin-right:.6rem}
 input,select,button{font:inherit;padding:.25rem .4rem} button{cursor:pointer}
 table{border-collapse:collapse;width:100%} td,th{border-bottom:1px solid #e4e7eb;padding:.3rem;text-align:left}
 #banner{min-height:1.4em;padding:.4rem;border-radius:6px} #banner.err{background:#fde8e8} #banner.ok{background:#e3f9e5}
 #log{font:12px ui-monospace,monospace;background:#f5f7fa;padding:.5rem;max-height:10rem;overflow:auto}
</style></head><body>
<h1>ATLAS Go desk</h1>
<p>Every button sends a request to the Python API, which reads or writes SQLite and returns JSON. Open DevTools &rarr; Network to watch.</p>
<fieldset><legend>Book a ride</legend>
 <label>Passenger <input id="passenger" maxlength="40"></label>
 <label>From <select id="pickup"></select></label> <label>To <select id="destination"></select></label>
 <label>km <input id="km" type="number" step="0.1" value="5.8" style="width:5rem"></label>
 <button id="book">Book</button></fieldset>
<p><button id="load">Load rides</button> <input id="q" placeholder="search (debounced)"> <button id="more">Load more</button> <button id="stats">Stats</button></p>
<div id="banner" role="status" aria-live="polite"></div>
<table><caption>Rides (newest first)</caption><thead><tr><th>id</th><th>passenger</th><th>from</th><th>to</th><th>fare</th><th>status</th><th></th></tr></thead><tbody id="rows"></tbody></table>
<h2>Request log</h2><div id="log"></div>
<script>
const PLACES = __PLACES__;
const $ = id => document.getElementById(id);
for (const p of PLACES) { $('pickup').add(new Option(p)); $('destination').add(new Option(p)); }
$('destination').value = 'Cork Airport';
let rides = [], formKey = null, timer = null;
function banner(text, ok) { $('banner').textContent = text; $('banner').className = text ? (ok ? 'ok' : 'err') : ''; }
function log(line) { const d = document.createElement('div'); d.textContent = line; $('log').prepend(d); }
async function api(method, path, body, headers = {}) {
  const t0 = performance.now();
  const r = await fetch(path, {method, headers: {'Content-Type': 'application/json', ...headers},
                               body: body ? JSON.stringify(body) : undefined});
  const data = await r.json();
  log(`${method} ${path} -> ${r.status} in ${(performance.now() - t0).toFixed(1)} ms`);
  return {r, data};
}
function message(r, data) {
  if (r.status === 422) return `Please check ${data.field}: ${data.error}`;
  if (r.status === 409) return `Not saved: ${data.error}`;
  if (r.status >= 500) return `Something went wrong on our side (reference ${data.ref || '-'})`;
  return data.error || `Request failed (${r.status})`;
}
function render() {
  const tbody = $('rows'); tbody.replaceChildren();
  for (const ride of rides) {
    const tr = tbody.insertRow();
    for (const v of [ride.id, ride.passenger, ride.pickup, ride.destination, (ride.fare_cents / 100).toFixed(2), ride.status])
      tr.insertCell().textContent = v;                      // textContent: never innerHTML with data
    const cell = tr.insertCell();
    if (ride.status === 'requested') { const b = document.createElement('button'); b.textContent = 'Cancel';
      b.onclick = async () => { const {r, data} = await api('POST', `/api/rides/${ride.id}/cancel`);
        if (r.ok) { Object.assign(ride, data); render(); } else banner(message(r, data)); }; cell.append(b); }
  }
}
$('load').onclick = async () => { const {r, data} = await api('GET', '/api/rides?limit=10');
  if (r.ok) { rides = data.items; render(); banner(`${data.total} rides in the database`, true); } };
$('more').onclick = async () => { if (!rides.length) return;
  const {data} = await api('GET', `/api/rides?limit=10&before_id=${rides[rides.length - 1].id}`);
  rides.push(...data.items); render(); };
$('q').oninput = () => { clearTimeout(timer); timer = setTimeout(async () => {
  const {data} = await api('GET', '/api/rides?limit=100&q=' + encodeURIComponent($('q').value));
  rides = data.items; render(); }, 300); };
$('stats').onclick = async () => { const {data} = await api('GET', '/api/stats');
  banner(data.by_status.map(s => `${s.status}: ${s.rides}`).join(' | ') || 'no rides', true); };
$('book').onclick = async () => {
  const body = {passenger: $('passenger').value, pickup: $('pickup').value,
                destination: $('destination').value, distance_km: Number($('km').value)};
  formKey ??= crypto.randomUUID();
  $('book').disabled = true;
  try { const {r, data} = await api('POST', '/api/rides', body, {'Idempotency-Key': formKey});
    if (r.ok) { rides.unshift(data); render(); formKey = null; $('passenger').value = '';
      banner(`Booked ride ${data.id} - fare EUR ${(data.fare_cents / 100).toFixed(2)}`, true); }
    else banner(message(r, data));
  } catch (e) { banner('Cannot reach the server - check your connection.'); }
  finally { $('book').disabled = false; }
};
</script></body></html>
""".replace("__PLACES__", json.dumps(PLACES))


def serve(port=8010):
    trace = Trace()
    trace.enabled = False
    db = Database(trace)
    service = RideService(db, trace)
    service.seed(drivers=4, rides=12)
    api = ApiServer(service, trace)
    api.httpd.server_close()
    api.httpd = ThreadingHTTPServer(("127.0.0.1", port), api.httpd.RequestHandlerClass)
    print(f"Open http://127.0.0.1:{port}  (local only, synthetic data; Ctrl+C to stop)")
    try:
        api.httpd.serve_forever()
    except KeyboardInterrupt:
        pass


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--experiment", type=int, choices=sorted(LABS))
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--serve", action="store_true", help="run the API and a clickable page on 127.0.0.1")
    parser.add_argument("--port", type=int, default=8010)
    parser.add_argument("--output", default="python_lab/results_app")
    args = parser.parse_args()
    if args.list:
        for n, t in TITLES.items():
            print(f"A{n:02}  {t}")
        return
    if args.serve:
        return serve(args.port)
    self_test()
    targets = list(LABS) if args.all else [args.experiment] if args.experiment else []
    for n in targets:
        res = experiment(n)
        save_experiment(res, args.output)
        print(f"A{n:02}: {res['title']} -> {args.output}")
    if not targets:
        parser.print_help()


if __name__ == "__main__":
    main()
