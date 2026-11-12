"""Reference solution for the ten app-building tasks (T01-T10).

Instructors: this file proves every acceptance test can pass
(`python python_lab/app_tasks/grade.py --check`). Students: try the task in
starter.py first - read TICKETS.md, run the grader, then compare.
"""
from __future__ import annotations

import csv
import hashlib
import hmac
import io
import json
import math
import re
import secrets
import sqlite3
import sys
import threading
import urllib.parse
import time
from collections import deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app_integration as ai  # noqa: E402
from app_integration import (Button, Conflict, Forbidden, NotFound, RawBody, TooManyRequests,  # noqa: E402
                             Unauthorized, ValidationError)

STATUSES = ("requested", "assigned", "completed", "cancelled")


# =============================================================================
# T01 - Delete a cancelled ride
# =============================================================================
def install_t01(app):
    db, service, screen = app.db, app.service, app.screen

    def delete(m, q, b, h):
        ride_id = int(m[1])
        with db.transaction():
            ride = service.get_ride(ride_id)                       # 404 if missing
            if ride["status"] != "cancelled":
                raise Conflict(f"only cancelled rides can be deleted (ride {ride_id} is {ride['status']})")
            db.execute("DELETE FROM audit WHERE ride_id = ?", (ride_id,))   # children first (FOREIGN KEY)
            db.execute("DELETE FROM rides WHERE id = ?", (ride_id,))
        service._invalidate()
        return 204, None

    app.server.add_route("DELETE", r"/api/rides/(\d+)", delete)

    def on_delete(ride_id):
        screen._handler(f"delete ride {ride_id}")
        resp = screen.client.request("DELETE", f"/api/rides/{ride_id}")
        if resp.status == 204:
            screen.table = [r for r in screen.table if r["id"] != ride_id]
            screen.banner = f"Deleted ride {ride_id}"
        else:
            screen._show_error(resp)
        return resp

    screen.delete_button = Button("Delete", on_delete, app.trace)


# =============================================================================
# T02 - Available-drivers dropdown
# =============================================================================
def install_t02(app):
    db, screen = app.db, app.screen

    def available(m, q, b, h):
        rows = db.query("SELECT id, name FROM drivers WHERE online = 1 AND busy = 0 ORDER BY name, id")
        return 200, rows

    app.server.add_route("GET", r"/api/drivers/available", available)
    screen.driver_options = []
    screen.selected_driver = None

    def on_available():
        screen._handler("load available drivers")
        resp = screen.client.get("/api/drivers/available")
        if resp.ok:
            screen.driver_options = [(d["id"], d["name"]) for d in resp.body]
            ids = [d for d, _ in screen.driver_options]
            if screen.selected_driver not in ids:
                screen.selected_driver = ids[0] if ids else None
        else:
            screen._show_error(resp)
        return resp

    def on_assign_selected(ride_id):
        screen._handler(f"assign selected driver to ride {ride_id}")
        if screen.selected_driver is None:
            screen.banner = "No drivers available"
            return None
        resp = screen.client.post(f"/api/rides/{ride_id}/assign", {"driver_id": screen.selected_driver})
        if resp.ok:
            screen._upsert(resp.body)
            screen.banner = ""
            on_available()                                     # that driver is busy now
        else:
            screen._show_error(resp)
        return resp

    screen.available_button = Button("Available drivers", on_available, app.trace)
    screen.assign_selected_button = Button("Assign selected", on_assign_selected, app.trace)


# =============================================================================
# T03 - Accounts, login and sessions
# =============================================================================
PBKDF2_ITERATIONS = 120_000
SESSION_SECONDS = 3600
USERNAME_RE = re.compile(r"[A-Za-z0-9_]{3,20}")

ACCOUNT_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id       INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
    salt     BLOB NOT NULL,
    pw_hash  BLOB NOT NULL,
    role     TEXT NOT NULL DEFAULT 'passenger' CHECK (role IN ('passenger', 'dispatcher'))
);
CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id),
    expires_at REAL NOT NULL
);
"""


def _hash_password(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_user(app, username: str, password: str, role: str = "passenger") -> dict:
    """Server-side helper (also used by the tests to create a dispatcher)."""
    if not isinstance(username, str) or not USERNAME_RE.fullmatch(username):
        raise ValidationError("username", "3-20 letters, digits or _")
    if not isinstance(password, str) or len(password) < 10:
        raise ValidationError("password", "at least 10 characters")
    if password.lower() == username.lower():
        raise ValidationError("password", "must differ from the username")
    salt = secrets.token_bytes(16)
    try:
        with app.db.transaction():
            cur = app.db.execute("INSERT INTO users (username, salt, pw_hash, role) VALUES (?, ?, ?, ?)",
                                 (username, salt, _hash_password(password, salt), role))
    except sqlite3.IntegrityError:
        raise Conflict("that username is taken") from None
    return {"id": cur.lastrowid, "username": username, "role": role}


def current_user(app, headers) -> dict:
    """The user for an 'Authorization: Bearer <token>' header, or raise Unauthorized."""
    value = headers.get("Authorization") or ""
    scheme, _, token = value.partition(" ")
    if scheme != "Bearer" or not token.strip():
        raise Unauthorized("sign in first")
    rows = app.db.query("SELECT u.id, u.username, u.role, s.expires_at FROM sessions s "
                        "JOIN users u ON u.id = s.user_id WHERE s.token_hash = ?", (_token_hash(token.strip()),))
    if not rows or rows[0]["expires_at"] <= app.auth_clock():
        raise Unauthorized("session expired or invalid")
    return {k: rows[0][k] for k in ("id", "username", "role")}


def install_t03(app, clock=time.time):
    db, screen = app.db, app.screen
    app.auth_clock = clock
    with db.lock:
        db.conn.executescript(ACCOUNT_SCHEMA)

    def register(m, q, b, h):
        b = b if isinstance(b, dict) else {}
        user = create_user(app, b.get("username"), b.get("password"))      # role is never taken from the body
        return 201, user

    def login(m, q, b, h):
        b = b if isinstance(b, dict) else {}
        username, password = b.get("username"), b.get("password")
        rows = []
        if isinstance(username, str) and isinstance(password, str):
            rows = db.query("SELECT id, salt, pw_hash FROM users WHERE username = ?", (username,))
        dummy_salt = b"\0" * 16
        candidate = _hash_password(password if isinstance(password, str) else "", rows[0]["salt"] if rows else dummy_salt)
        if not rows or not hmac.compare_digest(candidate, rows[0]["pw_hash"]):
            raise Unauthorized("invalid username or password")             # same message either way
        token = secrets.token_urlsafe(32)
        with db.transaction():
            db.execute("INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (?, ?, ?)",
                       (_token_hash(token), rows[0]["id"], clock() + SESSION_SECONDS))
        return 200, {"token": token, "expires_in": SESSION_SECONDS}

    def me(m, q, b, h):
        return 200, current_user(app, h)

    def logout(m, q, b, h):
        current_user(app, h)
        token = h.get("Authorization").partition(" ")[2].strip()
        with db.transaction():
            db.execute("DELETE FROM sessions WHERE token_hash = ?", (_token_hash(token),))
        return 204, None

    app.server.add_route("POST", r"/api/register", register)
    app.server.add_route("POST", r"/api/login", login)
    app.server.add_route("GET", r"/api/me", me)
    app.server.add_route("POST", r"/api/logout", logout)
    screen.user = None

    def on_login(username, password):
        screen._handler("sign in")
        resp = screen.client.post("/api/login", {"username": username, "password": password})
        if resp.ok:
            screen.client.default_headers["Authorization"] = f"Bearer {resp.body['token']}"
            screen.user = screen.client.get("/api/me").body
            screen.banner = f"Signed in as {screen.user['username']}"
        else:
            screen.banner = "Invalid username or password" if resp.status == 401 else ai.user_message(resp)
        return resp

    def on_logout():
        screen._handler("sign out")
        resp = screen.client.post("/api/logout")
        screen.client.default_headers.pop("Authorization", None)
        screen.user = None
        screen.banner = "Signed out"
        return resp

    screen.login_button = Button("Sign in", on_login, app.trace)
    screen.logout_button = Button("Sign out", on_logout, app.trace)


# =============================================================================
# T04 - Protect the API with roles
# =============================================================================
PUBLIC = {("GET", "/"), ("GET", "/api/health"), ("POST", "/api/register"), ("POST", "/api/login")}
DISPATCHER_ONLY = [("POST", r"/api/rides/\d+/(assign|complete)"), ("GET", r"/api/stats"),
                   ("DELETE", r"/api/rides/\d+")]


def install_t04(app):
    def guard(request):
        if (request.method, request.path) in PUBLIC:
            return
        user = current_user(app, request.headers)                 # 401 - role read fresh from the DB
        request.state["user"] = user
        for method, pattern in DISPATCHER_ONLY:
            if request.method == method and re.fullmatch(pattern, request.path) and user["role"] != "dispatcher":
                raise Forbidden("dispatchers only")
        if (request.method, request.path) == ("POST", "/api/rides") and user["role"] == "passenger" \
                and isinstance(request.body, dict):
            request.body["passenger"] = user["username"]           # passengers book in their own name

    app.server.before_request.append(guard)


# =============================================================================
# T05 - Rate-limit bookings
# =============================================================================
def install_t05(app, limit=5, window=60.0, clock=time.monotonic):
    hits: dict[str, deque] = {}
    lock = threading.Lock()

    def limiter(request):
        if (request.method, request.path) != ("POST", "/api/rides"):
            return
        auth = request.headers.get("Authorization") or ""
        key = "token:" + auth if auth.startswith("Bearer ") else "ip:" + request.client
        with lock:
            now = clock()
            q = hits.setdefault(key, deque())
            while q and q[0] <= now - window:
                q.popleft()
            if len(q) >= limit:
                raise TooManyRequests("too many bookings", math.ceil(q[0] + window - now))
            q.append(now)

    app.server.before_request.append(limiter)


# =============================================================================
# T06 - CSV export
# =============================================================================
CSV_COLUMNS = ["id", "passenger", "pickup", "destination", "distance_km", "fare_eur", "status", "driver"]


def _csv_safe(value) -> str:
    text = "" if value is None else str(value)
    return "'" + text if text[:1] in ("=", "+", "-", "@", "\t", "\r") else text


def install_t06(app):
    db, screen = app.db, app.screen

    def export(m, q, b, h):
        status = q.get("status", [None])[0]
        if status is not None and status not in STATUSES:
            raise ValidationError("status", f"one of {', '.join(STATUSES)}")
        sql = ("SELECT r.id, r.passenger, r.pickup, r.destination, r.distance_km, r.fare_cents, r.status, "
               "d.name AS driver FROM rides r LEFT JOIN drivers d ON d.id = r.driver_id")
        rows = db.query(sql + (" WHERE r.status = ?" if status else "") + " ORDER BY r.id", (status,) if status else ())
        out = io.StringIO()
        writer = csv.writer(out, lineterminator="\r\n")
        writer.writerow(CSV_COLUMNS)
        for r in rows:
            writer.writerow([r["id"], _csv_safe(r["passenger"]), _csv_safe(r["pickup"]), _csv_safe(r["destination"]),
                             f"{r['distance_km']:g}", f"{r['fare_cents'] / 100:.2f}", r["status"],
                             _csv_safe(r["driver"])])
        return 200, RawBody(out.getvalue(), "text/csv; charset=utf-8"), \
            {"Content-Disposition": 'attachment; filename="rides.csv"'}

    app.server.add_route("GET", r"/api/rides/export\.csv", export)
    screen.download = None

    def on_export(status=None):
        screen._handler("export CSV")
        resp = screen.client.get("/api/rides/export.csv" + (f"?status={status}" if status else ""))
        if resp.ok:
            match = re.search(r'filename="([^"]+)"', resp.headers.get("Content-Disposition", ""))
            screen.download = (match[1] if match else "download.csv", resp.body)
        else:
            screen._show_error(resp)
        return resp

    screen.export_button = Button("Export CSV", on_export, app.trace)


# =============================================================================
# T07 - Schema migration and ratings
# =============================================================================
MIGRATIONS = [
    "ALTER TABLE rides ADD COLUMN rating INTEGER CHECK (rating BETWEEN 1 AND 5)",
]


def migrate(db, migrations=None) -> int:
    """Apply migrations[user_version:], each in its own transaction. Returns how many ran."""
    migrations = MIGRATIONS if migrations is None else migrations
    applied = 0
    with db.lock:
        version = db.conn.execute("PRAGMA user_version").fetchone()[0]
        for number, sql in enumerate(migrations[version:], start=version + 1):
            with db.transaction():
                db.conn.execute(sql)
                db.conn.execute(f"PRAGMA user_version = {int(number)}")
            applied += 1
    return applied


def install_t07(app):
    db, service = app.db, app.service
    migrate(db)

    def rate(m, q, b, h):
        ride_id = int(m[1])
        stars = (b or {}).get("stars") if isinstance(b, dict) else None
        if isinstance(stars, bool) or not isinstance(stars, int) or not 1 <= stars <= 5:
            raise ValidationError("stars", "an integer from 1 to 5")
        with db.transaction():
            changed = db.execute("UPDATE rides SET rating = ?, version = version + 1 "
                                 "WHERE id = ? AND status = 'completed' AND rating IS NULL", (stars, ride_id)).rowcount
            if not changed:
                ride = service.get_ride(ride_id)                   # 404 if missing
                if ride["status"] != "completed":
                    raise Conflict("only completed rides can be rated")
                raise Conflict("this ride has already been rated")
        return 200, service.get_ride(ride_id)

    def driver_rating(m, q, b, h):
        driver_id = int(m[1])
        if not db.query("SELECT 1 FROM drivers WHERE id = ?", (driver_id,)):
            raise NotFound(f"driver {driver_id} does not exist")
        row = db.query("SELECT AVG(rating) AS avg, COUNT(rating) AS n FROM rides WHERE driver_id = ?", (driver_id,))[0]
        return 200, {"driver_id": driver_id, "average": None if row["avg"] is None else round(row["avg"], 2),
                     "count": row["n"]}

    app.server.add_route("POST", r"/api/rides/(\d+)/rate", rate)
    app.server.add_route("GET", r"/api/drivers/(\d+)/rating", driver_rating)


# =============================================================================
# T08 - Ignore out-of-order search responses
# =============================================================================
def install_t08(app):
    screen = app.screen
    screen.search_seq = 0
    screen.stale_responses_ignored = 0
    screen.search_status = ""
    seq_lock = threading.Lock()

    def fetch(seq, text):
        resp = screen.client.get("/api/rides?" + urllib.parse.urlencode({"q": text, "limit": 100}))
        with screen._ui_lock:
            if seq != screen.search_seq:                       # a newer search was started
                screen.stale_responses_ignored += 1
                return resp
            if resp.ok:
                screen.table = list(resp.body["items"])
                screen.search_status = f"{resp.body['total']} results"
                screen.banner = ""
            else:
                screen.search_status = ""
                screen._show_error(resp)
        return resp

    def on_live_search(text):
        screen._handler(f"live search {text!r}")
        with seq_lock:
            screen.search_seq += 1
            seq = screen.search_seq
        screen.search_status = "Searching..."
        future = screen._pool.submit(fetch, seq, text)
        screen._pending.append(future)
        return future

    screen.live_search_button = Button("Live search", on_live_search, app.trace)


# =============================================================================
# T09 - Sorting and filtering without SQL injection
# =============================================================================
SORT_COLUMNS = {"id": "id", "fare_cents": "fare_cents", "distance_km": "distance_km", "passenger": "passenger"}


def _int_arg(q, name, default, lo, hi):
    if name not in q:
        return default
    try:
        value = int(q[name][0])
    except ValueError:
        raise ValidationError(name, "an integer is required") from None
    if not lo <= value <= hi:
        raise ValidationError(name, f"between {lo} and {hi}")
    return value


def install_t09(app):
    db = app.db

    def query(m, q, b, h):
        sort = q.get("sort", ["id"])[0]
        if sort not in SORT_COLUMNS:
            raise ValidationError("sort", f"one of {', '.join(SORT_COLUMNS)}")
        order = q.get("order", ["asc"])[0]
        if order not in ("asc", "desc"):
            raise ValidationError("order", "asc or desc")
        where, params = [], []
        if "status" in q:
            statuses = q["status"][0].split(",")
            if not statuses or any(s not in STATUSES for s in statuses):
                raise ValidationError("status", f"comma-separated values from {', '.join(STATUSES)}")
            where.append(f"status IN ({', '.join('?' * len(statuses))})")
            params += statuses
        lo = _int_arg(q, "min_fare", None, 0, 10**7)
        hi = _int_arg(q, "max_fare", None, 0, 10**7)
        if lo is not None and hi is not None and lo > hi:
            raise ValidationError("min_fare", "must not exceed max_fare")
        if lo is not None:
            where.append("fare_cents >= ?"); params.append(lo)
        if hi is not None:
            where.append("fare_cents <= ?"); params.append(hi)
        limit = _int_arg(q, "limit", 20, 1, 100)
        clause = (" WHERE " + " AND ".join(where)) if where else ""
        total = db.query("SELECT COUNT(*) AS n FROM rides" + clause, params)[0]["n"]
        direction = "DESC" if order == "desc" else "ASC"
        rows = db.query(f"SELECT * FROM rides{clause} ORDER BY {SORT_COLUMNS[sort]} {direction}, id {direction} "
                        "LIMIT ?", (*params, limit))
        return 200, {"items": rows, "total": total}

    app.server.add_route("GET", r"/api/rides/query", query)


# =============================================================================
# T10 - Transactional outbox and a delivery worker
# =============================================================================
OUTBOX_SCHEMA = """
CREATE TABLE IF NOT EXISTS outbox (
    id         INTEGER PRIMARY KEY,
    event      TEXT    NOT NULL,
    ride_id    INTEGER NOT NULL,
    payload    TEXT    NOT NULL,
    status     TEXT    NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'delivered', 'dead')),
    attempts   INTEGER NOT NULL DEFAULT 0,
    last_error TEXT
);
"""


def install_t10(app):
    if getattr(app, "outbox_installed", False):        # idempotent: never register the hook twice
        return
    app.outbox_installed = True
    with app.db.lock:
        app.db.conn.executescript(OUTBOX_SCHEMA)

    def record(db, event, ride):                       # runs inside the write's own transaction
        payload = {k: ride[k] for k in ("id", "status", "passenger", "fare_cents", "driver_id")}
        db.execute("INSERT INTO outbox (event, ride_id, payload) VALUES (?, ?, ?)",
                   (event, ride["id"], json.dumps(payload)))

    app.service.write_hooks.append(record)


def deliver_outbox(app, send, max_attempts=5) -> dict:
    """Send every pending event in id order. Returns {'delivered', 'failed', 'dead'} counts."""
    db = app.db
    counts = {"delivered": 0, "failed": 0, "dead": 0}
    for row in db.query("SELECT * FROM outbox WHERE status = 'pending' ORDER BY id"):
        event = {"id": row["id"], "event": row["event"], "ride_id": row["ride_id"],
                 "payload": json.loads(row["payload"])}
        try:
            send(event)
        except Exception as exc:
            attempts = row["attempts"] + 1
            status = "dead" if attempts >= max_attempts else "pending"
            with db.transaction():
                db.execute("UPDATE outbox SET attempts = ?, last_error = ?, status = ? WHERE id = ?",
                           (attempts, repr(exc)[:200], status, row["id"]))
            counts["dead" if status == "dead" else "failed"] += 1
        else:
            with db.transaction():
                db.execute("UPDATE outbox SET status = 'delivered', attempts = attempts + 1 WHERE id = ?", (row["id"],))
            counts["delivered"] += 1
    return counts
