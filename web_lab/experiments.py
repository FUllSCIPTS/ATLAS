"""Web Technology laboratory: 20 experiments, W01-W20.

Every number comes from running the real teaching app (web_lab/app.py) - through
FastAPI's in-process TestClient, through a live Uvicorn server on 127.0.0.1, or
through a real Chromium browser driven by Playwright. Nothing is simulated.

    python -m web_lab.experiments --list
    python -m web_lab.experiments --all                 # -> web_lab/results (CSV, JSON, PNG)
    python -m web_lab.experiments --experiment 1
    python -m web_lab.experiments --all --no-browser    # skip W05, W06, W19

Browser experiments need:  python -m pip install playwright && python -m playwright install chromium
"""
from __future__ import annotations

import argparse
import asyncio
import concurrent.futures
import contextlib
import csv
import json
import re
import socket
import sqlite3
import statistics
import tempfile
import threading
import time
from html.parser import HTMLParser
from pathlib import Path

from fastapi.testclient import TestClient

from web_lab.app import ROOT, SCHEMA, create_app

OUT_DEFAULT = Path("web_lab/results")


class BrowserUnavailable(RuntimeError):
    pass


# ============================================================================ helpers
def payload(i, **extra):
    data = {"passenger": f"Student {i}", "pickup": "UCC", "destination": "Kent Station",
            "distance_km": float(i % 20 + 1), "request_key": f"lab-key-{i:08}"}
    data.update(extra)
    return data


@contextlib.contextmanager
def app_client():
    with tempfile.TemporaryDirectory() as d:
        with TestClient(create_app(Path(d) / "lab.sqlite3")) as client:
            yield client


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@contextlib.contextmanager
def live_server():
    """Run the app in a real Uvicorn server on 127.0.0.1 in a background thread."""
    import uvicorn
    with tempfile.TemporaryDirectory() as d:
        port = free_port()
        config = uvicorn.Config(create_app(Path(d) / "live.sqlite3"), host="127.0.0.1", port=port,
                                log_level="warning", lifespan="on")
        server = uvicorn.Server(config)
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()
        for _ in range(200):
            if server.started:
                break
            time.sleep(0.02)
        try:
            yield f"http://127.0.0.1:{port}"
        finally:
            server.should_exit = True
            thread.join(timeout=5)


def in_thread(fn, *args):
    """Run fn in a fresh thread (Playwright's sync API refuses to run inside Jupyter's event loop)."""
    with concurrent.futures.ThreadPoolExecutor(1) as pool:
        return pool.submit(fn, *args).result()


def browser_session(fn):
    """Call fn(page, base_url) with a Chromium page pointed at a live server."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise BrowserUnavailable("pip install playwright && python -m playwright install chromium") from exc

    def run():
        with live_server() as base, sync_playwright() as p:
            try:
                browser = p.chromium.launch()
            except Exception as exc:                       # browser binary missing
                raise BrowserUnavailable(f"Chromium not installed: {exc}") from exc
            try:
                return fn(browser, base)
            finally:
                browser.close()

    return in_thread(run)


def result(n, rows, labels, xlabel, ylabel, kind="line", notes="", log=False, extra=None):
    return {"number": n, "title": TITLES[n], "rows": rows, "labels": labels, "xlabel": xlabel,
            "ylabel": ylabel, "kind": kind, "notes": notes, "log": log, "extra": extra or {}}


# ============================================================================ W01 HTTP anatomy
def w01():
    """Send a hand-written HTTP/1.1 request over a raw TCP socket and read the raw response."""
    rows, raw_example = [], ""
    with live_server() as base:
        host, port = base.split("//")[1].split(":")
        for path in ("/", "/static/style.css", "/static/app.js", "/api/health", "/api/rides", "/openapi.json"):
            request = f"GET {path} HTTP/1.1\r\nHost: {host}:{port}\r\nConnection: close\r\n\r\n"
            with socket.create_connection((host, int(port))) as s:
                s.sendall(request.encode())
                chunks = []
                while chunk := s.recv(65536):
                    chunks.append(chunk)
            raw = b"".join(chunks)
            head, _, body = raw.partition(b"\r\n\r\n")
            status = int(head.split(b" ")[1])
            assert status == 200, (path, head[:80])
            if path == "/api/health":
                raw_example = request + raw.decode()
            rows.append((path, len(head) + 4, len(body)))
    return result(1, rows, ["header bytes", "body bytes"], "resource (GET over a raw socket)", "bytes",
                  kind="bar", notes="The raw exchange for /api/health is in extra.raw_http.",
                  extra={"raw_http": raw_example})


# ============================================================================ W02 status codes
def w02():
    with app_client() as c:
        rid = c.post("/api/rides", json=payload(1)).json()["id"]
        cases = [
            ("GET /", lambda: c.get("/")),
            ("POST /api/rides (new)", lambda: c.post("/api/rides", json=payload(2))),
            ("POST same key again", lambda: c.post("/api/rides", json=payload(2))),
            ("DELETE cancelled ride", lambda: (c.patch(f"/api/rides/{rid}", json={"status": "cancelled"}),
                                               c.delete(f"/api/rides/{rid}"))[1]),
            ("GET with matching ETag", lambda: c.get("/api/rides", headers={"If-None-Match": c.get("/api/rides").headers["ETag"]})),
            ("GET /api/rides/unknown", lambda: c.get("/api/rides/unknown")),
            ("DELETE /api/rides", lambda: c.delete("/api/rides")),
            ("POST same key, new details", lambda: c.post("/api/rides", json=payload(2, pickup="Airport"))),
            ("POST distance -1", lambda: c.post("/api/rides", json=payload(3, distance_km=-1))),
            ("GET ?limit=999", lambda: c.get("/api/rides?limit=999")),
        ]
        rows = [(label, fn().status_code) for label, fn in cases]
    return result(2, rows, ["status code"], "request", "HTTP status", kind="bar",
                  notes="2xx success, 3xx redirect/not modified, 4xx client error, 5xx server error.")


# ============================================================================ W03 HTML -> DOM
class _DomStats(HTMLParser):
    VOID = {"meta", "link", "input", "br", "img", "hr", "source", "option"}

    def __init__(self):
        super().__init__()
        self.depth = self.max_depth = 0
        self.tags, self.ids, self.labels_for, self.controls = {}, set(), set(), []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tags[tag] = self.tags.get(tag, 0) + 1
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "label" and "for" in a:
            self.labels_for.add(a["for"])
        if tag in ("input", "select", "textarea") and a.get("type") != "hidden":
            self.controls.append((a.get("id"), a.get("aria-label")))
        if tag not in self.VOID:
            self.depth += 1
            self.max_depth = max(self.max_depth, self.depth)

    def handle_endtag(self, tag):
        if tag not in self.VOID:
            self.depth -= 1


def w03():
    with app_client() as c:
        html = c.get("/").text
    p = _DomStats()
    p.feed(html)
    unlabeled = [cid for cid, aria in p.controls if cid not in p.labels_for and not aria]
    assert not unlabeled, unlabeled
    rows = sorted(p.tags.items(), key=lambda kv: -kv[1])
    return result(3, rows, ["elements"], "HTML tag", "count in index.html", kind="bar",
                  notes=f"{sum(p.tags.values())} elements, nesting depth {p.max_depth}; "
                        f"all {len(p.controls)} form controls have a <label for> (accessibility check passed).")


# ============================================================================ W04 CSS specificity
def specificity(selector):
    """(ids, classes/attributes/pseudo-classes, elements/pseudo-elements) for a simple selector list item."""
    inner = re.findall(r":not\(([^)]*)\)", selector)
    s = re.sub(r":not\([^)]*\)", " ", selector)                  # :not() itself counts nothing; its argument does
    s = re.sub(r"::?(before|after|first-line|first-letter)", " PE ", s)
    ids = len(re.findall(r"#[\w-]+", s))
    classes = len(re.findall(r"\.[\w-]+", s)) + len(re.findall(r"\[[^\]]+\]", s)) \
        + len(re.findall(r":[\w-]+(\([^)]*\))?", s))
    s2 = re.sub(r"#[\w-]+|\.[\w-]+|\[[^\]]+\]|:[\w-]+(\([^)]*\))?", " ", s)
    elements = len(re.findall(r"\b[a-z][\w-]*\b", s2.replace("PE", "pe"))) if s2.strip() not in ("*", "") else 0
    for pseudo in inner:
        sub = specificity(pseudo)
        ids, classes, elements = ids + sub[0], classes + sub[1], elements + sub[2]
    return ids, classes, elements


def w04():
    css = (ROOT / "static" / "style.css").read_text()
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"@media[^{]+\{", "", css)
    selectors = []
    for block in re.findall(r"([^{}]+)\{", css):
        for sel in block.split(","):
            sel = sel.strip()
            if sel and not sel.startswith("@") and sel not in selectors:
                selectors.append(sel)
    scored = [(sel, *specificity(sel)) for sel in selectors]
    scored.sort(key=lambda r: (r[1], r[2], r[3]), reverse=True)
    rows = [(sel, 100 * a + 10 * b + c) for sel, a, b, c in scored[:16]]
    assert specificity("#message") == (1, 0, 0) and specificity(".ride strong") == (0, 1, 1)
    assert specificity('.ride[data-status="completed"]') == (0, 2, 0)
    assert specificity("input:invalid:not(:placeholder-shown)") == (0, 2, 1)
    assert specificity("*::before") == (0, 0, 1) and specificity(":root") == (0, 1, 0)
    return result(4, rows, ["specificity (ids*100 + classes*10 + elements)"], "selector in style.css",
                  "specificity score", kind="bar",
                  notes="Higher specificity wins; equal specificity -> the later rule wins.",
                  extra={"all": scored})


# ============================================================================ W05 responsive layout (browser)
def w05(output):
    def run(browser, base):
        rows, shots = [], {}
        page = browser.new_page()
        for width in (320, 480, 640, 768, 800, 801, 1024, 1280, 1440):
            page.set_viewport_size({"width": width, "height": 900})
            page.goto(base + "/")
            page.wait_for_selector("#stats tr, #count:not(:empty)", timeout=5000)
            columns = page.evaluate("getComputedStyle(document.querySelector('.layout'))"
                                    ".gridTemplateColumns.split(' ').length")
            panel = page.evaluate("document.querySelector('.panel').getBoundingClientRect().width")
            rows.append((width, columns, round(panel)))
            if width in (480, 1280):
                path = Path(output) / f"W05_viewport_{width}.png"
                page.screenshot(path=str(path), full_page=True)
                shots[width] = path.name
        return rows, shots

    rows, shots = browser_session(run)
    assert [r[1] for r in rows if r[0] <= 800] == [1] * sum(r[0] <= 800 for r in rows)
    assert all(r[1] == 2 for r in rows if r[0] > 800)
    return result(5, [(w, c, p) for w, c, p in rows], ["grid columns", "first panel width px"], "viewport width px",
                  "value", notes="@media (max-width: 800px) switches 2 columns -> 1. Screenshots: " + ", ".join(shots.values()),
                  extra={"screenshots": shots})


# ============================================================================ W06 XSS (browser)
XSS = '<img src=x onerror="window.__xss = (window.__xss || 0) + 1">'


def w06(output):
    def run(browser, base):
        page = browser.new_page()
        page.goto(base + "/")
        page.wait_for_selector("#count:not(:empty)")
        page.fill("#passenger", XSS)
        page.click("button[type=submit]")
        page.wait_for_selector(".ride")
        card_text = page.inner_text(".ride p")
        via_text = page.evaluate("window.__xss || 0")
        # The anti-pattern on the same page: innerHTML. The app's Content-Security-Policy
        # forbids inline event handlers, so the browser blocks the payload anyway.
        page.evaluate("s => { const d = document.createElement('div'); document.body.append(d); d.innerHTML = s; }", XSS)
        page.wait_for_timeout(300)
        via_html_csp = page.evaluate("window.__xss || 0")
        page.screenshot(path=str(Path(output) / "W06_xss_safe_card.png"))
        # The same anti-pattern on a page WITHOUT a CSP: the script runs.
        bare = browser.new_page()
        bare.set_content("<div id=d></div>")
        bare.evaluate("s => { document.getElementById('d').innerHTML = s; }", XSS)
        bare.wait_for_timeout(300)
        via_html_no_csp = bare.evaluate("window.__xss || 0")
        return card_text, via_text, via_html_csp, via_html_no_csp

    text, safe, html_csp, html_bare = browser_session(run)
    assert XSS in text and safe == 0 and html_csp == 0 and html_bare >= 1
    rows = [("textContent (what app.js does)", safe),
            ("innerHTML, page has CSP", html_csp),
            ("innerHTML, page without CSP", min(html_bare, 1))]
    return result(6, rows, ["injected script ran (1 = yes)"], "how the passenger name was inserted", "ran?",
                  kind="bar", notes="Safe DOM APIs are the first defence; the Content-Security-Policy header "
                                    "is a second one that blocks inline handlers even if a bug uses innerHTML.")


# ============================================================================ W07 validation errors
def w07():
    bad_inputs = {
        "passenger": [None, "", "   ", "x" * 71, 42],
        "pickup": [None, "", "x" * 121],
        "destination": [None, "UCC"],
        "distance_km": [None, 0, -1, 201, "far"],
        "request_key": [None, "short", "k" * 101],
    }
    rows = []
    with app_client() as c:
        for field, values in bad_inputs.items():
            rejected = 0
            for v in values:
                data = payload(1)
                if v is None:
                    data.pop(field)
                else:
                    data[field] = v
                r = c.post("/api/rides", json=data)
                rejected += r.status_code == 422
            rows.append((field, len(values), rejected))
        assert c.get("/api/rides").headers["X-Total-Count"] == "0"
        sample_error = c.post("/api/rides", json=payload(1, distance_km=-1)).json()
    return result(7, rows, ["invalid payloads sent", "rejected with 422"], "field", "requests", kind="bar",
                  notes="No invalid payload reached the database (row count 0).", extra={"sample_422": sample_error})


# ============================================================================ W08 state machine
STATES = ["requested", "assigned", "completed", "cancelled"]


def w08():
    rows = []
    with app_client() as c:
        ava = next(d["id"] for d in c.get("/api/drivers").json() if d["name"] == "Ava")
        path_to = {"requested": [], "assigned": ["assigned"], "completed": ["assigned", "completed"],
                   "cancelled": ["cancelled"]}
        for i, start in enumerate(STATES):
            cells = []
            for j, target in enumerate(STATES):
                rid = c.post("/api/rides", json=payload(100 * i + j)).json()["id"]
                for step in path_to[start]:
                    body = {"status": step, "driver_id": ava} if step == "assigned" else {"status": step}
                    assert c.patch(f"/api/rides/{rid}", json=body).status_code == 200
                body = {"status": target, "driver_id": ava} if target == "assigned" else {"status": target}
                cells.append(c.patch(f"/api/rides/{rid}", json=body).status_code)
            rows.append((f"from {start}", *cells))
    return result(8, rows, [f"to {s}" for s in STATES], "requested new state", "current state", kind="heatmap",
                  notes="200 = legal transition, 409 = refused by the server's state machine.")


# ============================================================================ W09 concurrency and idempotency
def w09():
    import httpx
    rows = []
    with live_server() as base:
        for k in (1, 2, 4, 8, 16):
            def fire(key):
                with httpx.Client(base_url=base, timeout=10) as h:
                    return h.post("/api/rides", json=payload(k, request_key=key)).status_code

            with concurrent.futures.ThreadPoolExecutor(k) as pool:
                same = list(pool.map(fire, [f"same-key-{k:04}"] * k))
            with concurrent.futures.ThreadPoolExecutor(k) as pool:
                distinct = list(pool.map(fire, [f"uniq-{k:04}-{i:04}" for i in range(k)]))
            assert same.count(201) == 1 and distinct.count(201) == k
            rows.append((k, same.count(201), distinct.count(201)))
    return result(9, rows, ["rows created: same idempotency key", "rows created: distinct keys"],
                  "simultaneous HTTP requests", "rows created",
                  notes="UNIQUE(request_key) + a check-then-insert inside one transaction: one row, however many retries.")


# ============================================================================ W10 SQL injection
def w10():
    db = sqlite3.connect(":memory:")
    db.executescript(SCHEMA)
    db.execute("INSERT INTO drivers(name, zone, rating, online) VALUES('Ava','Mardyke',4.9,1)")
    for i, status in enumerate(["requested", "completed", "completed", "cancelled"]):
        db.execute("INSERT INTO rides(id,passenger,pickup,destination,distance_km,fare_cents,status,request_key) "
                   "VALUES(?,?,?,?,?,?,?,?)", (f"r{i}", f"P{i}", "UCC", "Kent", 2, 550, status, f"key-{i:06}"))
    attacks = {"normal: 'completed'": "completed",
               "always-true: x' OR '1'='1": "x' OR '1'='1",
               "comment: completed' --": "completed' --",
               "union: x' UNION SELECT name,zone,... --": "x' UNION SELECT name, zone, rating, online, id, id, id, id, id, id FROM drivers --"}
    rows = []
    for label, text in attacks.items():
        unsafe_sql = f"SELECT * FROM rides WHERE status = '{text}'"          # NEVER do this
        try:
            unsafe = len(db.execute(unsafe_sql).fetchall())
        except sqlite3.Error:
            unsafe = -1
        safe = len(db.execute("SELECT * FROM rides WHERE status = ?", (text,)).fetchall())
        rows.append((label, unsafe, safe))
    assert rows[0][1:] == (2, 2) and rows[1][1] == 4 and rows[1][2] == 0
    return result(10, rows, ["rows returned: string concatenation", "rows returned: ? parameter"],
                  "value typed into a 'status' filter", "rows", kind="bar",
                  notes="Concatenation lets the input rewrite the query (all rows, or rows from another table); "
                        "a bound parameter is always just data.")


# ============================================================================ W11 indexes
def w11():
    rows, plans = [], {}
    for n in (1_000, 10_000, 50_000, 200_000):
        db = sqlite3.connect(":memory:")
        db.executescript(SCHEMA.replace("CREATE INDEX IF NOT EXISTS idx_rides_status ON rides(status);", ""))
        states = ["requested", "assigned", "completed", "cancelled"]
        db.executemany("INSERT INTO rides(id,passenger,pickup,destination,distance_km,fare_cents,status,request_key) "
                       "VALUES(?,?,?,?,?,?,?,?)",
                       ((f"r{i}", "P", "A", "B", 1, 400, "requested" if i % 500 == 0 else states[1 + i % 3],
                         f"key-{i:09}") for i in range(n)))

        def timed():
            samples = []
            for _ in range(7):
                t = time.perf_counter()
                db.execute("SELECT COUNT(*) FROM rides WHERE status = 'requested'").fetchone()
                samples.append((time.perf_counter() - t) * 1000)
            return statistics.median(samples)

        plan_before = " ".join(r[-1] for r in db.execute("EXPLAIN QUERY PLAN SELECT * FROM rides WHERE status='requested'"))
        without = timed()
        db.execute("CREATE INDEX idx_rides_status ON rides(status)")
        plan_after = " ".join(r[-1] for r in db.execute("EXPLAIN QUERY PLAN SELECT * FROM rides WHERE status='requested'"))
        with_index = timed()
        plans = {"without index": plan_before, "with index": plan_after}
        rows.append((n, without, with_index))
    assert "SCAN" in plans["without index"] and "USING INDEX" in plans["with index"]
    return result(11, rows, ["no index (full scan)", "with index on status"], "rows in table",
                  "median ms per query (log scale)", log=True, notes=f"Query plans: {plans}", extra={"plans": plans})


# ============================================================================ W12 transactions
def w12():
    """Move a ride's fare from 'pending' to 'paid' in two UPDATEs; crash between them in half the trials."""
    def trial(use_transaction, crash):
        db = sqlite3.connect(":memory:", isolation_level=None)      # autocommit unless we BEGIN
        db.execute("CREATE TABLE ledger(account TEXT PRIMARY KEY, cents INTEGER NOT NULL)")
        db.executemany("INSERT INTO ledger VALUES(?,?)", [("pending", 1000), ("paid", 0)])
        try:
            if use_transaction:
                db.execute("BEGIN")
            db.execute("UPDATE ledger SET cents = cents - 550 WHERE account = 'pending'")
            if crash:
                raise RuntimeError("power cut between the two updates")
            db.execute("UPDATE ledger SET cents = cents + 550 WHERE account = 'paid'")
            if use_transaction:
                db.execute("COMMIT")
        except RuntimeError:
            if use_transaction:
                db.execute("ROLLBACK")
        total = db.execute("SELECT SUM(cents) FROM ledger").fetchone()[0]
        return total == 1000

    rows = []
    for use in (False, True):
        consistent = sum(trial(use, crash=(i % 2 == 0)) for i in range(100))
        rows.append(("autocommit (no transaction)" if not use else "BEGIN ... COMMIT / ROLLBACK", consistent, 100 - consistent))
    assert rows[1][1] == 100 and rows[0][2] == 50
    return result(12, rows, ["consistent ledgers", "money lost"], "how the two UPDATEs ran", "out of 100 trials",
                  kind="bar", notes="Atomicity: with a transaction a failure undoes the first UPDATE.")


# ============================================================================ W13 joins and foreign keys
def w13():
    with app_client() as c:
        drivers = {d["name"]: d["id"] for d in c.get("/api/drivers?online=true").json()}
        plan = {"Ava": 5, "Sam": 3, "Eoin": 1}
        i = 0
        for name, k in plan.items():
            for _ in range(k):
                i += 1
                rid = c.post("/api/rides", json=payload(i)).json()["id"]
                c.patch(f"/api/rides/{rid}", json={"status": "assigned", "driver_id": drivers[name]})
        c.post("/api/rides", json=payload(99))                         # unassigned: LEFT JOIN gives NULL
        stats = c.get("/api/stats").json()
        joined = c.get("/api/rides?limit=1").json()[0]
        db = sqlite3.connect(c.app.state.db_path)
        db.execute("PRAGMA foreign_keys=ON")
        try:
            db.execute("UPDATE rides SET driver_id = 999 WHERE driver_id IS NULL")
            fk = "accepted (BUG)"
        except sqlite3.IntegrityError as e:
            fk = f"rejected: {e}"
        db.close()
    rows = [(r["name"], r["rides"]) for r in stats["by_driver"]]
    assert rows == [("Ava", 5), ("Sam", 3), ("Eoin", 1)] and joined["driver_name"] is None
    return result(13, rows, ["assigned rides (JOIN + GROUP BY)"], "driver", "rides", kind="bar",
                  notes=f"Unassigned ride has driver_name NULL (LEFT JOIN). Pointing a ride at driver 999: {fk}.")


# ============================================================================ W14 pagination
def w14():
    rows = []
    with app_client() as c:
        for i in range(400):
            c.post("/api/rides", json=payload(i))
        for limit in (10, 25, 50, 100, 200):
            samples, size = [], 0
            for _ in range(7):
                t = time.perf_counter()
                r = c.get(f"/api/rides?limit={limit}")
                samples.append((time.perf_counter() - t) * 1000)
                size = len(r.content)
            assert r.headers["X-Total-Count"] == "400" and len(r.json()) == limit
            rows.append((limit, size / 1024, statistics.median(samples)))
    return result(14, rows, ["response KiB", "median ms"], "page size (limit)", "KiB / ms",
                  notes="X-Total-Count tells the client how many pages exist; bytes grow linearly with page size.")


# ============================================================================ W15 caching with ETags
def w15():
    rows = []
    with app_client() as c:
        for i in range(50):
            c.post("/api/rides", json=payload(i))
        r1 = c.get("/api/rides")
        tag = r1.headers["ETag"]
        r2 = c.get("/api/rides", headers={"If-None-Match": tag})
        r3 = c.get("/api/rides", headers={"If-None-Match": tag})
        c.post("/api/rides", json=payload(999))
        r4 = c.get("/api/rides", headers={"If-None-Match": tag})
        r5 = c.get("/api/rides", headers={"If-None-Match": r4.headers["ETag"]})
        for label, r in (("1 first GET", r1), ("2 revalidate", r2), ("3 revalidate", r3),
                         ("4 after a POST", r4), ("5 revalidate", r5)):
            rows.append((f"{label} -> {r.status_code}", len(r.content)))
    assert [int(r[0].split()[-1]) for r in rows] == [200, 304, 304, 200, 304]
    return result(15, rows, ["body bytes transferred"], "request sequence", "bytes", kind="bar",
                  notes="304 Not Modified sends headers only; the ETag changes when the data changes.")


# ============================================================================ W16 CORS and security headers
def w16():
    with app_client() as c:
        checks = {
            "GET /": c.get("/"),
            "GET /api/rides": c.get("/api/rides"),
            "preflight from http://localhost:5173": c.options("/api/rides", headers={
                "Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"}),
            "preflight from https://evil.example": c.options("/api/rides", headers={
                "Origin": "https://evil.example", "Access-Control-Request-Method": "POST"}),
        }
    headers = ["content-security-policy", "x-content-type-options", "x-frame-options",
               "referrer-policy", "access-control-allow-origin"]
    rows = [(label, *[int(h in r.headers) for h in headers]) for label, r in checks.items()]
    assert rows[2][-1] == 1 and rows[3][-1] == 0
    return result(16, rows, headers, "response header", "request", kind="heatmap",
                  notes="1 = header present. Only the allowed development origin receives Access-Control-Allow-Origin.")


# ============================================================================ W17 latency vs rows
def w17():
    rows = []
    with app_client() as c:
        stored = 0
        for target in (0, 100, 400, 1600):
            while stored < target:
                c.post("/api/rides", json=payload(stored))
                stored += 1
            samples = []
            for _ in range(25):
                t = time.perf_counter()
                assert c.get("/api/rides?limit=50").status_code == 200
                samples.append((time.perf_counter() - t) * 1000)
            samples.sort()
            rows.append((stored, statistics.median(samples), samples[int(0.95 * (len(samples) - 1))]))
    return result(17, rows, ["median ms", "95th percentile ms"], "rows stored", "ms per GET /api/rides?limit=50",
                  notes="In-process TestClient: measures the application and SQLite, not a network.")


# ============================================================================ W18 throughput vs concurrency
def w18():
    import httpx
    rows = []
    with live_server() as base:
        with httpx.Client(base_url=base) as h:
            for i in range(100):
                h.post("/api/rides", json=payload(i))
        for clients in (1, 2, 4, 8, 16):
            per_client = 40

            def work(_):
                with httpx.Client(base_url=base, timeout=10) as h:
                    times = []
                    for _ in range(per_client):
                        t = time.perf_counter()
                        assert h.get("/api/rides?limit=20").status_code == 200
                        times.append((time.perf_counter() - t) * 1000)
                    return times

            start = time.perf_counter()
            with concurrent.futures.ThreadPoolExecutor(clients) as pool:
                all_times = [t for ts in pool.map(work, range(clients)) for t in ts]
            elapsed = time.perf_counter() - start
            rows.append((clients, clients * per_client / elapsed, statistics.median(all_times)))
    return result(18, rows, ["requests per second", "median latency ms"], "concurrent HTTP clients",
                  "req/s  |  ms", notes="Real HTTP over 127.0.0.1 to one Uvicorn worker: throughput levels off "
                                       "while latency rises once the worker is saturated.")


# ============================================================================ W19 browser end-to-end
def w19(output):
    def run(browser, base):
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        steps = []

        def step(name, action, selector, state="visible"):
            # wait_for_selector is used instead of wait_for_function: the app's CSP forbids eval().
            t = time.perf_counter()
            action()
            page.wait_for_selector(selector, state=state, timeout=5000)
            steps.append((name, (time.perf_counter() - t) * 1000))
            page.screenshot(path=str(Path(output) / f"W19_{len(steps)}_{name.replace(' ', '_')}.png"))

        step("open page", lambda: page.goto(base + "/"), "#count:not(:empty)")
        step("book ride", lambda: page.click("button[type=submit]"), ".ride[data-status=requested]")
        step("assign driver", lambda: page.click(".ride button:text('Assign')"), ".ride[data-status=assigned]")
        step("complete ride", lambda: page.click(".ride button:text('Complete')"), ".ride[data-status=completed]")
        page.fill("#pickup", "Grand Parade")
        step("book second", lambda: page.click("button[type=submit]"), ".ride[data-status=requested]")
        step("delete it", lambda: page.click(".ride[data-status=requested] button:text('Delete')"),
             ".ride[data-status=requested]", state="detached")
        assert page.locator(".ride").count() == 1
        stats = page.inner_text("#stats")
        return steps, stats

    steps, stats = browser_session(run)
    assert "completed" in stats
    return result(19, steps, ["ms from click to updated DOM"], "user step in Chromium", "ms", kind="bar",
                  notes="Each step = click -> fetch -> FastAPI -> SQLite -> JSON -> DOM update. Screenshots W19_*.png.")


# ============================================================================ W20 async / event loop
def w20():
    async def fake_io(ms):
        await asyncio.sleep(ms / 1000)                 # stands for a network or database wait
        return ms

    async def sequential(n):
        for _ in range(n):
            await fake_io(50)

    async def concurrent_(n):
        await asyncio.gather(*(fake_io(50) for _ in range(n)))

    def timed(coro_fn, n):
        def run():
            t = time.perf_counter()
            asyncio.run(coro_fn(n))
            return (time.perf_counter() - t) * 1000
        return in_thread(run)                          # works inside Jupyter's running loop too

    rows = [(n, timed(sequential, n), timed(concurrent_, n)) for n in (1, 2, 4, 8, 16)]
    assert rows[-1][1] > 4 * rows[-1][2]
    return result(20, rows, ["await one after another", "asyncio.gather (concurrent)"], "number of 50 ms waits",
                  "total ms", notes="The same idea as Promise.all in JavaScript: waiting overlaps, CPU work does not.")


TITLES = {
    1: "HTTP message anatomy over a raw TCP socket",
    2: "Status codes returned by the API",
    3: "HTML document as a tree: elements and label check",
    4: "CSS selector specificity in style.css",
    5: "Responsive layout measured in Chromium",
    6: "XSS: textContent vs innerHTML in a real browser",
    7: "Server-side validation: 422 by field",
    8: "Ride state machine: every transition",
    9: "Concurrent retries and idempotency keys",
    10: "SQL injection: concatenation vs parameters",
    11: "Database index vs full table scan",
    12: "Transactions: atomic two-step update",
    13: "JOIN, GROUP BY and a foreign key",
    14: "Pagination: page size vs bytes and time",
    15: "HTTP caching with ETag and 304",
    16: "CORS preflight and security headers",
    17: "API latency as the table grows",
    18: "Throughput vs concurrent clients (live server)",
    19: "Browser end-to-end flow (Playwright)",
    20: "Async waits: sequential vs gather",
}
RUNNERS = {1: w01, 2: w02, 3: w03, 4: w04, 5: w05, 6: w06, 7: w07, 8: w08, 9: w09, 10: w10,
           11: w11, 12: w12, 13: w13, 14: w14, 15: w15, 16: w16, 17: w17, 18: w18, 19: w19, 20: w20}
BROWSER = {5, 6, 19}


def run(number, output=OUT_DEFAULT):
    if number not in RUNNERS:
        raise ValueError("Unknown experiment")
    Path(output).mkdir(parents=True, exist_ok=True)
    return RUNNERS[number](output) if number in BROWSER else RUNNERS[number]()


def draw(res, output=OUT_DEFAULT):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    stem = output / f"W{res['number']:02}"
    with stem.with_suffix(".csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([res["xlabel"], *res["labels"]])
        w.writerows(res["rows"])
    stem.with_suffix(".json").write_text(json.dumps(res, indent=2, default=str), encoding="utf-8")
    rows, labels = res["rows"], res["labels"]
    fig, ax = plt.subplots(figsize=(9.5, 5))
    if res["kind"] == "line":
        for j, label in enumerate(labels):
            ax.plot([r[0] for r in rows], [r[j + 1] for r in rows], marker="o", label=label)
        ax.legend()
    elif res["kind"] == "bar":
        width = 0.8 / len(labels)
        for j, label in enumerate(labels):
            bars = ax.bar([i + j * width for i in range(len(rows))], [r[j + 1] for r in rows], width, label=label)
            ax.bar_label(bars, fmt="%g", fontsize=8)
        ax.set_xticks([i + width * (len(labels) - 1) / 2 for i in range(len(rows))])
        ax.set_xticklabels([str(r[0]) for r in rows], rotation=25, ha="right", fontsize=8)
        if len(labels) > 1:
            ax.legend()
    else:
        grid = [list(r[1:]) for r in rows]
        ax.imshow(grid, cmap="RdYlGn_r" if res["number"] == 8 else "Greens", aspect="auto")
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=25, ha="right", fontsize=8)
        ax.set_yticks(range(len(rows)))
        ax.set_yticklabels([r[0] for r in rows], fontsize=8)
        for i, row in enumerate(grid):
            for j, v in enumerate(row):
                ax.text(j, i, str(v), ha="center", va="center", fontsize=10)
    if res["log"]:
        ax.set_yscale("log")
    ax.set_title(f"W{res['number']:02} - {res['title']}")
    ax.set_xlabel(res["xlabel"])
    ax.set_ylabel(res["ylabel"])
    ax.grid(alpha=.25)
    fig.tight_layout()
    fig.savefig(stem.with_suffix(".png"), dpi=140)
    plt.close(fig)
    return stem.with_suffix(".png")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--experiment", type=int, choices=range(1, 21))
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--no-browser", action="store_true", help="skip the Playwright experiments")
    parser.add_argument("--output", default=str(OUT_DEFAULT))
    args = parser.parse_args()
    if args.list:
        for n, t in TITLES.items():
            print(f"W{n:02}  {t}{'  [browser]' if n in BROWSER else ''}")
        return
    targets = list(TITLES) if args.all else [args.experiment] if args.experiment else []
    if not targets:
        parser.print_help()
    for n in targets:
        if n in BROWSER and args.no_browser:
            print(f"W{n:02}: skipped (--no-browser)")
            continue
        try:
            res = run(n, args.output)
        except BrowserUnavailable as exc:
            print(f"W{n:02}: skipped - browser unavailable ({exc})")
            continue
        draw(res, args.output)
        print(f"W{n:02}: {res['title']} -> {args.output}")


if __name__ == "__main__":
    main()
