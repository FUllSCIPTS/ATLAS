# ATLAS ride-hailing starter

This repository directory runs a small ride-hailing system. It includes two browser apps, three FastAPI services, durable ride events, a separate model server, and a continuous policy training job. The public GitHub Pages site explains the architecture. Run the app locally or on a controlled server to use the ride APIs.

[Open the build guide](https://fullscipts.github.io/ATLAS/build.html) · [Machine-readable build specification](https://fullscipts.github.io/ATLAS/build-spec.json)

## Handover and UML blueprint

[Start with the final handover and runbook](docs/FINAL_HANDOVER.md). It collects the runtime settings, API contracts, model artifacts, replay checks and verification status.

The blueprint maps the folder hierarchy, every application class and method, module functions, callbacks, the database model, and the ride and ML flows. It includes source links and a regenerable JSON inventory for coding agents. [Read the UML blueprint](docs/UML_BLUEPRINT.md) · [Machine-readable inventory](docs/uml-blueprint.json)

## Start with PostgreSQL and Kafka

Prerequisites are Git and Docker with the Compose plugin. All model training and inference run on CPU. Run these commands from the repository checkout:

```bash
cd architecture-explorer/starter
docker compose up -d --build
docker compose exec -T gateway python -m tests.smoke
docker compose exec -T gateway python -m tests.policy
docker compose exec -T -e KAFKA_BOOTSTRAP=kafka:9092 gateway python -m tests.replay
```

Compose starts PostgreSQL and a single Kafka broker, creates `atlas.ride.v1`, applies the initial schema and trains the seeded models. The model server must report healthy before the event worker starts. Open `http://127.0.0.1:8000/passenger` and `http://127.0.0.1:8000/driver` in separate tabs. The demo keys are `rider-demo`, `driver-a-demo`, and `driver-b-demo`. If the offer does not appear under Driver A, try Driver B. To stop the stack, run `docker compose down`. Persistent volumes retain ride data and model artifacts.

Use `docker compose logs initialize models events` if the smoke test cannot find an offer or trained model. The API returns `202` for booking and acceptance because the event worker advances the trip asynchronously.

## Start locally without Docker

Use Python 3.12 on Linux or macOS with Bash. CPU wheel availability can vary by platform. The following installation commands use the PyTorch CPU package index.

```bash
cd architecture-explorer/starter
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install --index-url https://download.pytorch.org/whl/cpu torch==2.7.1
bash scripts/local.sh
```

From a second terminal in `starter/` with the virtual environment activated, run `python -m tests.smoke`. The local script uses SQLite and feeds committed outbox rows directly to the same event handlers. It starts the gateway on port 8000, Trips on 8001, Dispatch on 8002, and model serving on 8003. Compose uses PostgreSQL and Kafka for transport. Both modes use the same trip transitions, inference API and training code.

## Runtime files

| Path | Runtime responsibility |
| --- | --- |
| `apps/passenger/index.html` | Book a ride and poll status |
| `apps/driver/index.html` | Set availability, poll offers and submit trip milestones |
| `apps/shared/client.js` and `demo.css` | Browser UI actions and styling |
| `services/gateway.py` | Same-origin pages, role authentication and API routing |
| `services/trips.py` | Idempotent booking, passenger status and driver milestones |
| `services/dispatch.py` | Driver availability, offers and atomic acceptance |
| `infra/schema.sql` and `packages/db.py` | Schema, migrations, DB selection and transactional outbox |
| `packages/config.py` | Local paths, roles and shared runtime configuration |
| `packages/ride-event.schema.json` | Kafka envelope and payload contract |
| `workers/events.py` | Relay, deduplicated event application, demand features and RL experience |
| `ml/forecast.py` and `ml/discrete.py` | LSTM, logistic regression and Isolation Forest training |
| `ml/train.py`, `ml/serve.py`, `ml/registry.py` | Training job, inference API and atomic version pointers |
| `ml/rl.py` | Batch Q-learning, held-out gate, approval and rollback |
| `scripts/initialize.sh` and `scripts/local.sh` | Bootstrap and local process launcher |
| `Dockerfile`, `compose.yaml`, `requirements.txt` | Container deployment and dependency versions |
| `tests/smoke.py`, `tests/policy.py`, and `tests/replay.py` | End-to-end ride, model, policy approval, rollback and duplicate event checks |

## API and data contracts

All public demo endpoints except browser pages and `/healthz` require an `Authorization: Bearer <demo-key>` header. The gateway supplies internal identity headers to the private ride services. API input errors return `422`. An invalid key returns `401`, an unauthorized trip or offer returns `404`, and an invalid transition or reused booking key with a different body returns `409`.

| Method and path | Payload or result |
| --- | --- |
| `POST /v1/rider/trips` | Send `Idempotency-Key` and JSON `pickup`, `destination`, `zone`. Returns `202` with a trip ID and status. |
| `GET /v1/rider/trips/{id}` | Returns an authorized trip snapshot. |
| `PUT /v1/driver/availability` | Send `online` boolean, `distance_km` and `speed_kph`. |
| `GET /v1/driver/offers` | Returns active offers for the driver, including ML audit fields. |
| `POST /v1/driver/offers/{id}/accept` | Accepts the driver's offer and reserves availability. Returns `202`. |
| `POST /v1/driver/trips/{id}/milestones` | Send `status` as `picked_up` or `completed`. |
| `POST /internal/v1/score` | Send a zone and candidate driver list. Returns forecast, acceptance scores, anomaly flags, strategy and model/policy versions. Private model service only. |

The supported zones are `cork-centre` and `cork-north`. Trip state advances through `requested`, `assigned`, `picked_up`, and `completed`. Booking writes the trip and `trip.requested` in one transaction. The worker publishes to `atlas.ride.v1` using the trip ID as the Kafka key, and records each consumed event ID in the inbox before acknowledging the offset. A broker acknowledgement and the outbox status update can be separated by a crash, so duplicate delivery is expected and safe. The demo runs one event worker and one partition.

The starter makes one offer per trip. If no driver is available, the trip stays requested. An implementation intended for public ride service needs offer expiry, re-matching, cancellation, and durable recovery for pending trips.

## Train, serve and learn

Initial startup fits the three supervised or unsupervised models on seeded synthetic data. The LSTM reads 12 five-minute booking counts and predicts the next count. When live bucket files exist, inference uses those counts. Logistic regression estimates offer acceptance from distance and speed. Isolation Forest flags unusual values for review. Dispatch records the actual model version and falls back to nearest eligible driver if scoring is unavailable.

To retrain the demonstration models with Compose, run `docker compose exec -T models python -m ml.train`. In local mode, run `python -m ml.train`. Model binaries and the metric manifest are written to a versioned directory before the active manifest is replaced. Keep artifact directories writable only by trusted training jobs. Pickle-based model artifacts must come from that trusted pipeline.

For each completed ride, the worker logs one terminal sample with the original demand bucket, strategy, policy version, and reward. The demonstration reward is `max(-1, 1 - elapsed_seconds/600)`. This is a one-decision RL episode. Action 0 ranks by distance and action 1 ranks by predicted acceptance. The watcher checks for new completed rides every minute and starts training after 80 outcomes. It writes a candidate without activating it.

```bash
# Train a candidate on the synthetic fixture and copy the printed version.
docker compose exec -T models python -m ml.rl train --demo
# Review the holdout support and mean reward before running approval.
docker compose exec -T models python -m ml.rl approve CANDIDATE_VERSION --allow-demo
# Opt in to the approved strategy for this isolated demo.
ATLAS_POLICY_ENABLED=1 docker compose up -d events
# Restore nearest-driver selection.
docker compose exec -T models python -m ml.rl rollback
```

For a candidate based on recorded rides, use `python -m ml.rl train` and approve without `--allow-demo`. Approval requires at least eight held-out outcomes for the baseline and the candidate action per bucket and rejects reward below baseline. Logged outcomes are observational. Public deployment of a policy needs representative data, explicit approval, shadow evaluation and monitored rollback. Synthetic metrics describe the fixture.

## Completion checklist for a coding agent

1. Clone the branch and run the starter unmodified. Record the smoke test output for PostgreSQL and Kafka before making changes.
2. Keep request IDs, event schema, trip ownership, conditional transitions, and transactional outbox semantics stable.
3. Add production identity and authorization, GPS and routing, ride cancellation and reassignment, notification transport, and payment in separate tested increments. Define market-specific privacy and retention before collecting real rider data.
4. Replace the synthetic datasets with consented, validated data. Measure chronological holdout error, calibration, anomaly precision and operational impact. Keep the nearest-driver fallback.
5. Add concurrency and replay tests, tenant isolation, metrics and alerts, backups, and restore drills. Use an isolated staging deployment before exposing the application to real users.
6. Prove readiness with the smoke test, `tests.replay` against the configured broker, model version evidence, policy evaluation, and deployment runbook. List each remaining gap.

The starter is a development implementation with demo identities, seeded telemetry and one logical data store. Its build guide and contracts give a coding agent the inputs and verification steps for extending it.
