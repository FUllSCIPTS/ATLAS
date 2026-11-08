# Web Technology lab — a full-stack teaching app, 28 tests and 20 experiments

[Course guide (23 lessons)](../docs/WEB_TECHNOLOGY.md) · [Open the experiments in Google Colab](https://colab.research.google.com/github/FUllSCIPTS/ATLAS/blob/main/web_lab/Web_Technology_Colab_Labs.ipynb) · [ATLAS UML blueprint](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/docs/UML_BLUEPRINT.md)

**New to the Web?** Start with [Lesson 1 of the guide](../docs/WEB_TECHNOLOGY.md#lesson-1--the-internet-and-the-web-clients-servers-ip-tcp-and-ports); every lesson points to the exact file and function in this folder that demonstrates it.

A local, synthetic ride-booking site: **HTML form → CSS grid → JavaScript `fetch` → FastAPI → SQLite (two tables, foreign key) → JSON → safe DOM update**. It has no authentication and must never be exposed on a public network or filled with real personal data.

## Files

| File | What to study in it |
|---|---|
| `static/index.html` | semantic structure, a labelled form with `datalist`, a captioned table, ARIA live regions |
| `static/style.css` | custom properties, `border-box`, grid layout, Flexbox rows, focus styles, a media query |
| `static/app.js` | `FormData` → JSON, `fetch` with `response.ok` checks, 422 error formatting, `Promise.all`, pagination, `textContent`-only rendering |
| `app.py` | Pydantic models, REST routes, state machine, idempotency keys, ETag/304, pagination headers, JOIN and GROUP BY, CORS, security headers, lifespan start-up |
| `tests/test_integration.py` | 28 tests: static files, headers, OpenAPI, CRUD, pagination, ETags, validation, idempotency (incl. concurrent), injection, state machine, drivers, foreign key, stats, 405/404, CORS |
| `experiments.py` | W01–W20, each writing CSV, JSON and PNG |
| `Web_Technology_Colab_Labs.ipynb` | the experiments with concept recaps and editable demos |

## API

| Method and path | Purpose | Success | Errors |
|---|---|---|---|
| `GET /api/health` | liveness | 200 | — |
| `GET /api/rides?status=&limit=&offset=` | list, newest first, with `X-Total-Count` and `ETag` | 200 / 304 | 422 |
| `GET /api/rides/{id}` | one ride, with the driver's name (LEFT JOIN) | 200 | 404 |
| `POST /api/rides` | create (body `passenger, pickup, destination, distance_km, request_key`) | 201 (200 on replay) | 409, 422 |
| `PATCH /api/rides/{id}` | change state (`status`, plus `driver_id` to assign) | 200 | 404, 409, 422 |
| `DELETE /api/rides/{id}` | delete a requested or cancelled ride | 204 | 404, 409 |
| `GET /api/drivers?online=` | list drivers (4 seeded, one offline) | 200 | 422 |
| `POST /api/drivers` | add a driver | 201 | 409 duplicate, 422 |
| `GET /api/stats` | rides and fares by status; rides per driver | 200 | — |

Interactive documentation is generated at **`/docs`**.

## Run it

~~~bash
python -m pip install -r web_lab/requirements.txt
python -m uvicorn web_lab.app:app --host 127.0.0.1 --port 8000 --reload
~~~

Open http://127.0.0.1:8000 and http://127.0.0.1:8000/docs with DevTools → Network open. The database file `web_lab/data/demo.sqlite3` is created when the server starts (not when the module is imported); delete it to start again. Settings: `WEB_LAB_DB` (database path) and `WEB_LAB_ORIGINS` (comma-separated CORS origins, default `http://localhost:5173`).

## Tests and experiments

~~~bash
python -m pytest -q web_lab/tests                        # 28 tests, each on a fresh temporary database
python -m pip install playwright && python -m playwright install chromium   # once, for W05, W06, W19
python -m web_lab.experiments --list
python -m web_lab.experiments --all                      # W01-W20 -> web_lab/results (≈ 30 s)
python -m web_lab.experiments --all --no-browser         # without Chromium
python -m web_lab.experiments --experiment 6
~~~

| ID | Experiment | Runs against |
|---|---|---|
| W01 | HTTP message anatomy (hand-written request over a raw socket) | live server |
| W02 | Ten status codes from real requests | TestClient |
| W03 | HTML tree: element counts, depth, label check | `html.parser` |
| W04 | CSS specificity of every selector | `style.css` |
| W05 | Responsive grid at nine viewport widths (+ screenshots) | Chromium |
| W06 | XSS: `textContent` vs `innerHTML`, with and without CSP | Chromium |
| W07 | 422 validation by field | TestClient |
| W08 | 4 × 4 state-transition matrix | TestClient |
| W09 | Concurrent identical POSTs → one row | live server |
| W10 | SQL injection: concatenation vs parameters | SQLite |
| W11 | Index vs full scan up to 200 000 rows; query plans | SQLite |
| W12 | Transactions: lost money with vs without BEGIN/COMMIT | SQLite |
| W13 | JOIN + GROUP BY; foreign-key violation | TestClient + SQLite |
| W14 | Pagination: bytes and time vs page size | TestClient |
| W15 | ETag / 304 sequence | TestClient |
| W16 | CORS preflight and security-header matrix | TestClient |
| W17 | Latency (median, p95) as the table grows | TestClient |
| W18 | Throughput and latency vs concurrent clients | live server |
| W19 | End-to-end UI flow in a browser (+ screenshots) | Chromium |
| W20 | `asyncio` sequential vs `gather` | Python event loop |

Only W11, W14, W17, W18, W19 and W20 report times, which depend on the machine; the rest report counts, status codes or sizes.

## Google Colab

Open the notebook and choose **Runtime → Run all**. It clones the repository, installs the requirements, installs a headless Chromium (one minute), runs the 28 tests, then W01–W20 with a concept recap and an editable demo before each, and zips the results. Colab cannot show the site in a browser tab; run Uvicorn on your own computer for that.

## Practice questions

Which attribute names a field in `FormData`? Why must JavaScript check `response.ok`? Where are the three places a rule such as "distance between 0 and 200 km" is enforced, and which one is a convenience? What do 201, 204, 304, 404, 405, 409 and 422 mean in this API? How does a `request_key` make POST safe to retry, and what stops two simultaneous retries both inserting? Why does `textContent` prevent XSS, and what does the CSP add? What does `LEFT JOIN` return for a ride with no driver? When does an index stop helping?

## Security warning

There is no login, no authorisation and no rate limiting. Do not deploy this app, do not enter real names or addresses, and see Lessons 19–20 for what a real service needs.

## Audit notes

Rebuilt in November 2026. Previously: importing `app.py` created `web_lab/data/demo.sqlite3` as a side effect; the PATCH status was validated by hand and undocumented in OpenAPI; there was one table and no JOIN, foreign key, pagination, caching, CORS or security headers; six of twelve experiment charts plotted constant values with labels "result A/result B"; and there were no browser or live-server experiments. All addressed above.
