# Web Technology lab: full-stack concept and practice

**New to web development?** Start with [Part I — Beginner foundations](../docs/WEB_TECHNOLOGY.md#part-i--beginner-foundations-start-here-before-practical-development), which teaches 12 step-by-step basics before the advanced full-stack material: Internet/Web, URLs and DNS, HTML, CSS, JavaScript, forms, DOM, JSON, HTTP, API and SQL. Work through three examples before running the integrated labs.

[Standalone teaching guide](../docs/WEB_TECHNOLOGY.md) · [Google Colab experiments](https://colab.research.google.com/github/FUllSCIPTS/ATLAS/blob/main/web_lab/Web_Technology_Colab_Labs.ipynb) · [UML blueprint](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/docs/UML_BLUEPRINT.md)

**Local-only synthetic teaching application:** HTML form → CSS responsive view → JS fetch → FastAPI → parameterized SQLite → JSON response and DOM refresh. It has no authentication and must not be exposed on a public network or populated with real passenger data.

## Files

| File | Purpose |
|---|---|
| static/index.html | HTML form, accessible labels and ride cards |
| static/style.css | CSS Grid and mobile layout |
| static/app.js | Browser DOM, fetch and JSON |
| app.py | FastAPI CRUD, validation, idempotency and SQLite |
| tests/test_integration.py | Tests for HTTP status, SQL, validation and state |
| experiments.py | W01–W12 real tests with CSV/JSON/PNG |
| Web_Technology_Colab_Labs.ipynb | Colab notebook for all experiments |

## Start the website

```bash
python -m pip install -r web_lab/requirements.txt
python -m uvicorn web_lab.app:app --host 127.0.0.1 --port 8000 --reload
```

Open http://127.0.0.1:8000 and http://127.0.0.1:8000/docs; create a synthetic ride and inspect the browser Network panel. Stop Uvicorn when done. The SQLite demo DB defaults to web_lab/data/demo.sqlite3.

## Run automated tests and 12 experiments

```bash
python -m pytest -q web_lab/tests
python -m web_lab.experiments --all --output web_lab/results
python -m web_lab.experiments --experiment 12
```

Each experiment exports its real observations to CSV, JSON and PNG. W12 times FastAPI TestClient GET requests and reports median/stdev milliseconds. Other charts report status codes, counts or bytes—not performance. This is an educational program, not an external network benchmark.

## Google Colab

Open the linked notebook, select Runtime → Run all. The notebook clones the repository, installs the lab dependencies, runs integration tests, invokes W01–W12 in-process and exports an archive. Colab is for API/SQL testing; use localhost Uvicorn for the actual browser interface.

## Practice questions

Which HTML name controls FormData? What makes CSS responsive? Why must JS test response.ok? Which FastAPI model validates a POST? Why use SQLite placeholders? What do 201, 404, 409 and 422 mean? How does an idempotency key prevent duplicate inserts? Why is the demo prohibited from public deployment?

## Security warning

Do not use this demo for real rides, payments or identities. Add independent authentication, authorization, HTTPS, rate limiting, backups, migrations, concurrency protections and audit controls before considering a public application.
