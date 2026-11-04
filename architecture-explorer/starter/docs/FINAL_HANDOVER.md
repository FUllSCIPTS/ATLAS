# ATLAS final handover

This is the entry point for taking over the ride-hailing starter and the public architecture explorer. Use the Git branch as the implementation source, the executable tests as the acceptance criteria, and the UML and JSON inventory to navigate the code.

[UML blueprint](UML_BLUEPRINT.md) · [Generated inventory](uml-blueprint.json) · [Starter README](../README.md) · [Public build guide](https://fullscipts.github.io/ATLAS/build.html)

## What is delivered

| Item | Where it runs | Entry point |
| --- | --- | --- |
| Interactive architecture map and build guide | Public GitHub Pages from the `gh-pages` branch | [ATLAS Explorer](https://fullscipts.github.io/ATLAS/) |
| Self-hosted copy of the same explorer | Loopback Node HTTP process, optionally supervised by systemd | [server.mjs](../../server.mjs) and [systemd unit](../../deploy/atlas-explorer.service) |
| Passenger and driver apps, APIs and learning stack | Local Python profile or Docker Compose | [starter README](../README.md) |
| Source-derived catalog and verification | Python 3.12 and Node.js with npm | [generate_blueprint.py](../scripts/generate_blueprint.py) |

The public site serves documentation and an interactive architecture map. The runnable backend starts separately. The current application is a development starter with demo identities, two example zones, one offer per ride and synthetic initial model training data. Production identity, routing, payments, cancellation, re-matching and policy rollout require separate implementation and validation.

## Start, verify and stop

From a new checkout:

```bash
git clone --branch architecture-explorer --single-branch https://github.com/FUllSCIPTS/ATLAS.git
cd ATLAS/architecture-explorer/starter
docker compose config --quiet
docker compose up -d --build
docker compose exec -T gateway python -m tests.smoke
docker compose exec -T gateway python -m tests.policy
docker compose exec -T -e KAFKA_BOOTSTRAP=kafka:9092 gateway python -m tests.replay
docker compose down
```

For the SQLite profile, follow the [local setup](../README.md#start-locally-without-docker), leave the launcher running and execute `python -m tests.replay` and `python -m tests.policy` in a second terminal. Replay starts with a fresh completed ride. In Kafka mode the test waits until the worker group's committed offset advances past the replay, then compares the trip, experience, inbox and outbox counts. In SQLite mode it calls the same event handler directly.

For a manual run, open `http://127.0.0.1:8000/passenger` and `http://127.0.0.1:8000/driver` in separate tabs. Book with `rider-demo`. Check `driver-a-demo` and `driver-b-demo` for the offer, then accept, pick up and complete it. The passenger tab should show those states in order.

For the static explorer only, run `node server.mjs` from `architecture-explorer/` and open `http://127.0.0.1:8080/`. Its health route is `GET /healthz` and it serves only the assets in the code's allowlist. On GitHub Pages, copy the contents of `architecture-explorer/dist/` to the root of `gh-pages`, retaining `.nojekyll` and relative asset URLs.

## Runtime settings

The Compose profile includes only local-development credentials. Keep the gateway on loopback for the demo. In a real deployment use external authentication, TLS, restricted networks and separately managed secrets.

| Variable | Default in the local profile | Purpose |
| --- | --- | --- |
| `ATLAS_DATA` | `starter/.data` | SQLite file, feature data and model artifacts. Compose uses `/data`. |
| `DATABASE_URL` | Unset | A nonempty PostgreSQL connection string selects Psycopg. The SQLite launcher clears this variable. |
| `KAFKA_BOOTSTRAP` | Unset | Broker addresses select Kafka relay and consumption. The SQLite launcher clears it. Compose uses `kafka:9092` for the worker. |
| `ATLAS_INTERNAL_TOKEN` | `local-internal-only` | Shared internal gateway credential for Trip and Dispatch. |
| `ATLAS_RIDER_KEY` | `rider-demo` | Demo bearer key for `rider-a`. |
| `ATLAS_DRIVER_A_KEY` | `driver-a-demo` | Demo bearer key for `driver-a`. |
| `ATLAS_DRIVER_B_KEY` | `driver-b-demo` | Demo bearer key for `driver-b`. |
| `ATLAS_TRIP_URL` | `http://127.0.0.1:8001` | Internal Trip API origin for the gateway. |
| `ATLAS_DISPATCH_URL` | `http://127.0.0.1:8002` | Internal Dispatch API origin for the gateway. |
| `ATLAS_MODEL_URL` | `http://127.0.0.1:8003` | Model API origin for the worker and smoke/replay tests. |
| `ATLAS_GATEWAY_URL` | `http://127.0.0.1:8000` | Gateway origin for the smoke/replay tests. |
| `ATLAS_POLICY_ENABLED` | `0` | Use the approved policy in the worker only when set to `1`. |
| `PYTHON` | `python` | Interpreter for `scripts/initialize.sh` and `scripts/local.sh`. |
| `PORT` | `8080` | Node static explorer only. The Python gateway uses port 8000. |

Compose publishes only gateway port 8000 to the host loopback. The services use the Compose network. The broker topic is `atlas.ride.v1`, keyed by trip ID, and the worker consumer group is `atlas-ride-workers-v1`.

## HTTP and Kafka contracts

The two browser clients use the same-origin gateway. Gateway routes under `/v1/` require `Authorization: Bearer <demo-key>`. The gateway passes `X-Atlas-Actor` and `X-Atlas-Internal` to the internal ride service. `{trip_id}` is a UUID.

| Request | Successful response |
| --- | --- |
| `POST /v1/rider/trips` with `Idempotency-Key` and `pickup`, `destination`, `zone` | `202` and trip snapshot |
| `GET /v1/rider/trips/{trip_id}` | `200` and trip snapshot owned by the rider |
| `PUT /v1/driver/availability` with `online`, `distance_km`, `speed_kph` | `200` and those fields plus `driver_id` |
| `GET /v1/driver/offers` | `200` and array of the driver's active offers |
| `POST /v1/driver/offers/{trip_id}/accept` | `202` and `{"trip_id": "...", "state": "accepted"}` |
| `POST /v1/driver/trips/{trip_id}/milestones` with `{"status": "picked_up"}` or `{"status": "completed"}` | `200` and trip snapshot for the assigned driver |
| `POST /internal/v1/score` on the private Model API with `zone` and 1–20 `drivers` | `200` and the scorer response described below |

A trip snapshot contains `id`, `pickup`, `destination`, `zone`, `status` and `driver_id`. The last field is null until assignment. Zones are `cork-centre` and `cork-north`. Driver telemetry uses distance in km and speed in km/h. An offer contains `trip_id`, `state`, `status`, `pickup`, `destination`, `model_version`, `policy_version`, `forecast`, `acceptance` and `anomaly_flag`. The three ML values can be null on fallback. Stored anomaly flags are integers. The scorer response contains `model_version`, `forecast`, `bucket`, `action`, `policy_version` and `drivers`. Each result in `drivers` has `driver_id`, `acceptance` and a Boolean `anomaly_flag`. Input driver rows contain `driver_id`, `distance_km` and `speed_kph`.

The gateway returns `401` for invalid demo authentication, `404` for an unknown route, `413` for a body over 8,192 bytes, and `503` if a ride service is unreachable. Trip and Dispatch return `403` for invalid internal credentials or role, `404` for an inaccessible record, `409` for a conflict, and `422` for an invalid typed request. The Model API returns `503` when its active manifest is missing. Gateway `/healthz` checks the Trip and Dispatch APIs. Check the model health and a full smoke test for the learning path.

The [event schema](../packages/ride-event.schema.json) defines the v1 Kafka envelope and every payload. State changes and outbox rows share a transaction. The relay waits for broker acknowledgement before marking a row sent. The consumer commits after applying the event, with an inbox key to guard against replay. [Database schema](../infra/schema.sql)

## Models, data and rollback

| Path relative to `ATLAS_DATA` | Meaning |
| --- | --- |
| `rides.sqlite` | Local profile database. The Compose profile uses PostgreSQL instead. |
| `demand.json` | Twelve ordered five-minute booking counts per zone, written by the event worker. |
| `models/<version>/demand.pt` | PyTorch LSTM weights. |
| `models/<version>/acceptance.joblib` and `anomaly.joblib` | Logistic regression and Isolation Forest artifacts. Load from trusted training only. |
| `models/<version>/manifest.json` | Version, training-data label, seed window and holdout metrics. |
| `models/active-models.json` | Active model manifest, switched after the trained files are ready. |
| `models/policies/<version>.json` | RL candidate with action mapping and holdout evidence. |
| `models/active-policy.json` | The approved policy or the baseline pointer. |

Initial training and retraining commands are in the [ML runbook](../README.md#train-serve-and-learn). The RL watcher trains after sufficient recorded outcomes, but candidate creation and approval are separate steps. `python -m ml.rl rollback` restores the baseline policy. For an application rollback, stop the running services, select the previous verified Git commit, preserve a backup of data and artifacts, then verify compatibility before restarting.

Inspect `docker compose logs initialize models events` when the model service or offers fail to appear. Check the broker, topic and committed offsets if the replay test times out. Check that both seeded drivers are available if a trip stays requested.

## Verification record

| Check | Handover status |
| --- | --- |
| Full file tree, class/method inventory, source hashes and regenerate check | Checked against the Git checkout |
| UML diagram syntax and public documentation links | Checked |
| Booking through completion, model outputs, approval and rollback | Passed in the SQLite profile |
| Duplicate completed-event replay | Passed in the SQLite profile and through a Kafka-protocol mock broker |
| PostgreSQL driver and replay persistence | Checked against PGlite using the PostgreSQL protocol during starter verification |
| Complete Docker Compose run with the PostgreSQL and Apache Kafka containers | Run the acceptance commands above on a Docker host before treating that deployment as verified |

## First task for the next coding agent

Read the UML blueprint and JSON inventory, clone `architecture-explorer`, and run the acceptance commands before modifying source. Keep the API, event and model contracts compatible unless the task explicitly changes them. After code changes, run `python scripts/generate_blueprint.py` and then repeat it with `--check`. Report the commit, run profile, tests executed and any gaps that still affect the requested deployment.
