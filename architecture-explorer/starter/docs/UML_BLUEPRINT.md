# ATLAS ride-hailing UML blueprint

Use this blueprint to reproduce or extend the runnable ATLAS starter on the `architecture-explorer` branch. It covers the passenger and driver apps, FastAPI services, event worker, database, ML training and serving, policy training, and verification scripts.

[Runnable starter](../README.md) · [Machine-readable symbol inventory](uml-blueprint.json) · [Build specification](../../dist/build-spec.json) · [Kafka event contract](../packages/ride-event.schema.json)

## Start from the implementation

Clone the branch and run the unmodified starter before changing contracts or behavior.

```bash
git clone --branch architecture-explorer --single-branch https://github.com/FUllSCIPTS/ATLAS.git
cd ATLAS/architecture-explorer/starter
docker compose up -d --build
docker compose exec -T gateway python -m tests.smoke
docker compose exec -T gateway python -m tests.policy
```

The [local SQLite quickstart](../README.md#start-locally-without-docker) runs the same business handlers without a broker. The full Compose run is the acceptance check for the PostgreSQL and Kafka deployment.

## Folder hierarchy

All checked-in files in `architecture-explorer/starter/`. Runtime data, model artifacts and virtual environments are generated outside the source inventory.

<!-- BEGIN GENERATED TREE -->

```text
starter/
├── apps/
│   ├── driver/
│   │   └── index.html
│   ├── passenger/
│   │   └── index.html
│   └── shared/
│       ├── client.js
│       └── demo.css
├── docs/
│   ├── UML_BLUEPRINT.md
│   └── uml-blueprint.json
├── infra/
│   └── schema.sql
├── ml/
│   ├── discrete.py
│   ├── forecast.py
│   ├── registry.py
│   ├── rl.py
│   ├── serve.py
│   └── train.py
├── packages/
│   ├── config.py
│   ├── db.py
│   └── ride-event.schema.json
├── scripts/
│   ├── generate_blueprint.py
│   ├── initialize.sh
│   └── local.sh
├── services/
│   ├── dispatch.py
│   ├── gateway.py
│   └── trips.py
├── tests/
│   ├── policy.py
│   └── smoke.py
├── workers/
│   └── events.py
├── .dockerignore
├── .gitignore
├── Dockerfile
├── README.md
├── compose.yaml
└── requirements.txt
```

<!-- END GENERATED TREE -->

## Component and deployment boundaries

Only the gateway is published on the host loopback interface in the starter. The trip, dispatch and model APIs run on the internal network. The same event worker performs outbox relay and event consumption in this demo.

```mermaid
flowchart TD
    B["Passenger and driver browsers"] --> G["Gateway · host port 8000"]
    G --> T["Trip API"]
    G --> D["Dispatch API"]
    T --> P["PostgreSQL"]
    D --> P
    E["Event worker"] --> P
    E --> K["Kafka · atlas.ride.v1"]
    K --> E
    E --> M["Model serving API"]
    E --> A["Feature and artifact volume"]
    M --> A
    R["RL watcher"] --> P
    R --> A
    I["Initialize schema and models"] --> P
    I --> A
```

| Owner | Responsibility | Code |
| --- | --- | --- |
| Gateway | Serve browser pages, verify demo bearer keys, forward only allowlisted routes, attach internal identity | [services/gateway.py](../services/gateway.py) |
| Trip API | Create and read rider trips, validate driver milestones, update trip state | [services/trips.py](../services/trips.py) |
| Dispatch API | Track availability and offers, reserve a driver atomically on acceptance | [services/dispatch.py](../services/dispatch.py) |
| Event worker | Publish acknowledged outbox events, deduplicate consumption, create offers, apply assignment and collect learning features | [workers/events.py](../workers/events.py) |
| Model API | Load versioned artifacts and score candidates with demand, acceptance, anomaly and policy signals | [ml/serve.py](../ml/serve.py) |
| RL watcher | Train candidates from completed rides. Review and approval run as separate commands. | [ml/rl.py](../ml/rl.py) |

## Class diagrams

The diagrams show classes declared by the starter. Inherited library methods are supplied by their base classes. Full type annotations, defaults, decorators and source lines are in the [generated symbol catalog](#generated-symbol-catalog).

### Booking and dispatch types

```mermaid
classDiagram
    class BaseModel
    class Booking {
        +str pickup
        +str destination
        +Literal zone
    }
    class Milestone {
        +Literal status
    }
    class Telemetry {
        +bool online
        +float distance_km
        +float speed_kph
    }
    BaseModel <|-- Booking
    BaseModel <|-- Milestone
    BaseModel <|-- Telemetry
```

### Scoring types and LSTM

```mermaid
classDiagram
    class BaseModel
    class Candidate {
        +str driver_id
        +float distance_km
        +float speed_kph
    }
    class ScoringRequest {
        +Literal zone
        +list~Candidate~ drivers
    }
    class TorchModule
    class DemandLSTM {
        +LSTM recurrent
        +Linear output
        +__init__()
        +forward(values)
    }
    BaseModel <|-- Candidate
    BaseModel <|-- ScoringRequest
    ScoringRequest "1" *-- "1..20" Candidate : contains
    TorchModule <|-- DemandLSTM
```

### Database adapter

```mermaid
classDiagram
    class DB {
        +connection
        +__init__(connection)
        +run(query, *args)
    }
    class DBAPIConnection
    DB --> DBAPIConnection : wraps
```

`TorchModule` and `DBAPIConnection` represent external dependencies. The connection is either `sqlite3.Connection` or a Psycopg connection. The starter's service modules use functions and route decorators. Their signatures appear in the catalog.

## Persistence model

Cardinalities and key markers reflect the actual database constraints in [infra/schema.sql](../infra/schema.sql). `trips.driver_id` is a nullable text field. The assignment handler supplies its value.

```mermaid
erDiagram
    TRIPS ||--o| OFFERS : has
    DRIVERS ||--o{ OFFERS : receives
    TRIPS o|--o{ DRIVERS : "referenced by active_trip"
    TRIPS ||--o{ OUTBOX : emits
    TRIPS ||--o| EXPERIENCE : produces
    TRIPS {
        text id PK
        text rider_id
        text request_key
        text pickup
        text destination
        text zone
        text status
        text driver_id
        bigint created_at
    }
    DRIVERS {
        text id PK
        integer online
        real distance_km
        real speed_kph
        text active_trip FK
    }
    OFFERS {
        text trip_id PK, FK
        text driver_id FK
        text state
        integer action
        integer bucket
        text policy_version
        text model_version
        real forecast
        real acceptance
        integer anomaly_flag
    }
    OUTBOX {
        bigint seq PK
        text event_id UK
        text trip_id FK
        text event_type
        bigint occurred_at
        text body
        integer sent
    }
    INBOX {
        text event_id PK
    }
    EXPERIENCE {
        text trip_id PK, FK
        integer state
        integer action
        real reward
        text policy_version
        bigint occurred_at
    }
```

The compound unique key `trips(rider_id, request_key)` makes booking retries idempotent. The inbox primary key prevents duplicate event side effects. One offer and one learning record are stored per trip. The `pending_outbox(sent, seq)` index supports the relay.

## Trip state machine

```mermaid
stateDiagram-v2
    [*] --> requested : Idempotent booking
    requested --> assigned : Assignment confirmation consumed
    assigned --> picked_up : Assigned driver submits pickup
    picked_up --> completed : Assigned driver submits completion
    completed --> [*]
```

| Transition or action | Durable effect |
| --- | --- |
| Create booking | Insert trip and `trip.requested` outbox row in one transaction. Same key and body returns the existing trip. Different body with the same key yields `409`. |
| Create offer | Score online, unreserved drivers. Insert one offer and `dispatch.offer.created`. |
| Accept offer | Check driver ownership and availability. Update the offer, reserve the driver, and insert `dispatch.assignment.confirmed` in one transaction. |
| Apply assignment | Conditionally move `requested` to `assigned` and emit `trip.assigned`. |
| Pick up | Check driver and prior state. Move `assigned` to `picked_up` and emit `trip.picked_up`. |
| Complete | Move `picked_up` to `completed`, release the driver's reservation, and emit `trip.completed`. |
| Process completion | Join the offer's original state, action and policy version to the terminal reward. Insert one experience row. |

## Sequence diagrams

### Passenger booking

```mermaid
sequenceDiagram
    participant Passenger
    participant Gateway
    participant Trip
    participant Store
    Passenger->>Gateway: POST booking and idempotency key
    Gateway->>Trip: Forward authorized rider request
    Trip->>Store: Commit trip and trip.requested outbox row
    Store-->>Trip: Created or existing trip
    Trip-->>Gateway: 202 and trip snapshot
    Gateway-->>Passenger: 202 and trip ID
    Passenger->>Gateway: Poll trip status
```

### Event delivery and offer creation

```mermaid
sequenceDiagram
    participant Store
    participant Worker
    participant Kafka
    participant Models
    Worker->>Store: Read first unsent outbox row
    Worker->>Kafka: Publish event with trip ID key
    Kafka-->>Worker: Broker acknowledgement
    Worker->>Store: Mark event sent
    Kafka->>Worker: Deliver trip.requested
    Worker->>Store: Deduplicate event and read eligible drivers
    Worker->>Models: POST candidate list and zone
    Models-->>Worker: Forecast, scores, flags and versions
    Worker->>Store: Commit offer, inbox key and new outbox row
    Worker->>Kafka: Commit consumer offset
```

If a relay crashes after the broker acknowledgement and before marking the event sent, the next attempt can publish the same event again. The inbox deduplication is in the same transaction as the event's database effects. The SQLite profile drives these handlers directly from the outbox.

### Driver acceptance and completion

```mermaid
sequenceDiagram
    participant Driver
    participant Gateway
    participant Dispatch
    participant Worker
    participant Trip
    Driver->>Gateway: Poll offers and accept an offer
    Gateway->>Dispatch: Forward authenticated driver actions
    Dispatch-->>Gateway: 202 after reservation and outbox commit
    Dispatch-->>Worker: Assignment event via outbox and Kafka
    Worker-->>Trip: Apply assignment to shared trip storage
    Driver->>Gateway: Submit pickup and completion
    Gateway->>Trip: Forward driver milestone requests
    Trip-->>Worker: Completion event via outbox and Kafka
```

The worker applies assignment in the shared database. The diagram's dashed message to Trip represents that logical ownership boundary. There is no worker-to-Trip HTTP request.

### Training, serving and approval

```mermaid
flowchart TD
    S["Seeded training data"] --> T["Train LSTM, acceptance and anomaly models"]
    T --> M["Versioned model files and manifest"]
    M --> I["Model serving API"]
    E["Committed ride events"] --> F["Demand buckets and terminal experiences"]
    F --> I
    F --> Q["Batch Q-learning candidate"]
    Q --> G{"Explicit approval and holdout checks"}
    G -->|Pass| P["Atomic active-policy pointer"]
    P --> I
    G -->|Reject| B["Keep current policy"]
```

The LSTM reads 12 five-minute counts. Logistic regression and Isolation Forest read distance and speed. The RL state is forecast bucket `0` below 8 or `1` at least 8. Action `0` ranks by distance and action `1` ranks by acceptance probability. The policy watcher creates candidates after at least 80 completed outcomes. Training does not activate candidates. Inference uses an approved strategy only when `ATLAS_POLICY_ENABLED=1`. Rollback restores the nearest-driver baseline.

## Rebuild checklist

1. Run the [starter smoke and policy checks](../README.md#start-with-postgresql-and-kafka) against the existing code. Use the request paths and payloads in the [API contract](../README.md#api-and-data-contracts) as the compatibility baseline.
2. Implement changes through existing boundaries. Preserve rider and driver ownership, transactional state and outbox writes, deduplication, the state machine, model versions and explicit policy approval.
3. Test one complete ride, a booking retry with the same key, a forbidden offer acceptance, an invalid state transition, model outputs and one terminal experience. Run a real Kafka replay test before claiming deployment readiness.
4. Treat GPS, routing, offer expiry and re-matching, cancellations, payments, production identity and representative training data as separately scoped extensions.
5. Regenerate the blueprint after changing code. Commit the updated generated sections and JSON with the source changes.

From `starter/`, use Python 3.12 and Node.js with npm. The generator uses the Python standard library and the pinned Acorn parser for JavaScript.

```bash
python scripts/generate_blueprint.py
python scripts/generate_blueprint.py --check
```

The JSON includes relative paths, source hashes, imports, class bases, attributes, method signatures, module functions, nested functions, callbacks, decorators and source lines. It inventories the starter's runtime and verification code. The documentation generator and the separate GitHub Pages UI are outside the application symbol catalog.

## Generated symbol catalog

<!-- BEGIN GENERATED CATALOG -->

### `apps/shared/client.js`

[Open source](../apps/shared/client.js)

| Kind | Signature | Decorators | Source |
| --- | --- | --- | --- |
| Function | `async request(path, method = "GET", data, idempotencyKey)` | — | [L8](../apps/shared/client.js#L8) |
| Function | `async refresh()` | — | [L20](../apps/shared/client.js#L20) |
| Function | `refresh.<callback: offers.map>(offer)` | — | [L31](../apps/shared/client.js#L31) |
| Function | `async refresh.<callback: offers.map>.button.onclick()` | — | [L43](../apps/shared/client.js#L43) |
| Function | `async <callback: document.getElementById("booking")?.addEventListener, "submit">(event)` | — | [L59](../apps/shared/client.js#L59) |
| Function | `async <callback: document.getElementById("telemetry")?.addEventListener, "submit">(event)` | — | [L72](../apps/shared/client.js#L72) |

### `ml/discrete.py`

[Open source](../ml/discrete.py)

| Kind | Signature | Decorators | Source |
| --- | --- | --- | --- |
| Function | `train(directory)` | — | [L8](../ml/discrete.py#L8) |

### `ml/forecast.py`

[Open source](../ml/forecast.py)

**Class `DemandLSTM`** · bases `nn.Module` · [L9](../ml/forecast.py#L9)

- Instance attribute `self.recurrent = nn.LSTM(1, 12, batch_first=True)`
- Instance attribute `self.output = nn.Linear(12, 1)`

| Kind | Signature | Decorators | Source |
| --- | --- | --- | --- |
| Function | `train(directory)` | — | [L20](../ml/forecast.py#L20) |
| Function | `load(directory)` | — | [L44](../ml/forecast.py#L44) |
| Function | `predict(model, counts)` | — | [L51](../ml/forecast.py#L51) |
| Method | `DemandLSTM.__init__(self)` | — | [L10](../ml/forecast.py#L10) |
| Method | `DemandLSTM.forward(self, values)` | — | [L15](../ml/forecast.py#L15) |

### `ml/registry.py`

[Open source](../ml/registry.py)

| Kind | Signature | Decorators | Source |
| --- | --- | --- | --- |
| Function | `read_json(path, default=None)` | — | [L10](../ml/registry.py#L10) |
| Function | `write_json(path, value)` | — | [L17](../ml/registry.py#L17) |

### `ml/rl.py`

[Open source](../ml/rl.py)

| Kind | Signature | Decorators | Source |
| --- | --- | --- | --- |
| Function | `current_policy()` | — | [L15](../ml/rl.py#L15) |
| Function | `fixture()` | — | [L19](../ml/rl.py#L19) |
| Function | `experiences()` | — | [L25](../ml/rl.py#L25) |
| Function | `fit(samples, source)` | — | [L32](../ml/rl.py#L32) |
| Function | `fit.<lambda@39:40>(action)` | — | [L39](../ml/rl.py#L39) |
| Function | `approve(version, allow_demo=False)` | — | [L51](../ml/rl.py#L51) |
| Function | `watch(seconds)` | — | [L70](../ml/rl.py#L70) |
| Function | `main()` | — | [L81](../ml/rl.py#L81) |

### `ml/serve.py`

[Open source](../ml/serve.py)

**Class `Candidate`** · bases `BaseModel` · [L16](../ml/serve.py#L16)

- Declared field `driver_id: str`
- Declared field `distance_km: float = Field(ge=0, le=50)`
- Declared field `speed_kph: float = Field(ge=0, le=250)`

This class uses inherited methods.

**Class `ScoringRequest`** · bases `BaseModel` · [L22](../ml/serve.py#L22)

- Declared field `zone: Literal['cork-centre', 'cork-north']`
- Declared field `drivers: list[Candidate] = Field(min_length=1, max_length=20)`

This class uses inherited methods.

| Kind | Signature | Decorators | Source |
| --- | --- | --- | --- |
| Function | `models(version)` | `lru_cache(maxsize=2)` | [L28](../ml/serve.py#L28) |
| Function | `active()` | — | [L33](../ml/serve.py#L33) |
| Function | `health()` | `app.get('/healthz')` | [L41](../ml/serve.py#L41) |
| Function | `score(payload: ScoringRequest)` | `app.post('/internal/v1/score')` | [L48](../ml/serve.py#L48) |

### `ml/train.py`

[Open source](../ml/train.py)

| Kind | Signature | Decorators | Source |
| --- | --- | --- | --- |
| Function | `train()` | — | [L8](../ml/train.py#L8) |

### `packages/config.py`

[Open source](../packages/config.py)

| Kind | Signature | Decorators | Source |
| --- | --- | --- | --- |
| Function | `equal(left, right)` | — | [L19](../packages/config.py#L19) |
| Function | `internal_actor(request: Request, role: str) -> str` | — | [L23](../packages/config.py#L23) |

### `packages/db.py`

[Open source](../packages/db.py)

**Class `DB`** · bases none · [L14](../packages/db.py#L14)

- Instance attribute `self.connection = connection`

| Kind | Signature | Decorators | Source |
| --- | --- | --- | --- |
| Function | `database()` | `contextmanager` | [L23](../packages/db.py#L23) |
| Function | `migrate()` | — | [L45](../packages/db.py#L45) |
| Function | `emit(db, trip_id, event_type, **body)` | — | [L57](../packages/db.py#L57) |
| Function | `envelope(row)` | — | [L62](../packages/db.py#L62) |
| Method | `DB.__init__(self, connection)` | — | [L15](../packages/db.py#L15) |
| Method | `DB.run(self, query, *args)` | — | [L18](../packages/db.py#L18) |

### `scripts/initialize.sh`

[Open source](../scripts/initialize.sh)

Entrypoint script with no declared functions.

### `scripts/local.sh`

[Open source](../scripts/local.sh)

| Kind | Signature | Decorators | Source |
| --- | --- | --- | --- |
| Function | `start()` | — | [L13](../scripts/local.sh#L13) |
| Function | `cleanup()` | — | [L17](../scripts/local.sh#L17) |

### `services/dispatch.py`

[Open source](../services/dispatch.py)

**Class `Telemetry`** · bases `BaseModel` · [L12](../services/dispatch.py#L12)

- Declared field `online: bool`
- Declared field `distance_km: float = Field(ge=0, le=50)`
- Declared field `speed_kph: float = Field(ge=0, le=250)`

This class uses inherited methods.

| Kind | Signature | Decorators | Source |
| --- | --- | --- | --- |
| Function | `health()` | `app.get('/healthz')` | [L19](../services/dispatch.py#L19) |
| Function | `availability(request: Request, payload: Telemetry)` | `app.put('/v1/driver/availability')` | [L26](../services/dispatch.py#L26) |
| Function | `offers(request: Request)` | `app.get('/v1/driver/offers')` | [L35](../services/dispatch.py#L35) |
| Function | `accept(request: Request, trip_id: UUID)` | `app.post('/v1/driver/offers/{trip_id}/accept', status_code=202)` | [L47](../services/dispatch.py#L47) |

### `services/gateway.py`

[Open source](../services/gateway.py)

| Kind | Signature | Decorators | Source |
| --- | --- | --- | --- |
| Function | `health()` | `app.get('/healthz')` | [L26](../services/gateway.py#L26) |
| Function | `passenger()` | `app.get('/')`, `app.get('/passenger')` | [L37](../services/gateway.py#L37) |
| Function | `driver()` | `app.get('/driver')` | [L42](../services/gateway.py#L42) |
| Function | `async proxy(request: Request, role: str, path: str)` | `app.api_route('/v1/{role}/{path:path}', methods=['GET', 'POST', 'PUT'])` | [L47](../services/gateway.py#L47) |

### `services/trips.py`

[Open source](../services/trips.py)

**Class `Booking`** · bases `BaseModel` · [L14](../services/trips.py#L14)

- Declared field `pickup: str = Field(min_length=1, max_length=120, pattern='\\S')`
- Declared field `destination: str = Field(min_length=1, max_length=120, pattern='\\S')`
- Declared field `zone: Literal['cork-centre', 'cork-north']`

This class uses inherited methods.

**Class `Milestone`** · bases `BaseModel` · [L20](../services/trips.py#L20)

- Declared field `status: Literal['picked_up', 'completed']`

This class uses inherited methods.

| Kind | Signature | Decorators | Source |
| --- | --- | --- | --- |
| Function | `health()` | `app.get('/healthz')` | [L25](../services/trips.py#L25) |
| Function | `book(request: Request, payload: Booking, idempotency_key: Annotated[str, Header(min_length=1, max_length=128)])` | `app.post('/v1/rider/trips', status_code=202)` | [L32](../services/trips.py#L32) |
| Function | `public_trip(row)` | — | [L48](../services/trips.py#L48) |
| Function | `status(request: Request, trip_id: UUID)` | `app.get('/v1/rider/trips/{trip_id}')` | [L53](../services/trips.py#L53) |
| Function | `milestone(request: Request, trip_id: UUID, payload: Milestone)` | `app.post('/v1/driver/trips/{trip_id}/milestones')` | [L63](../services/trips.py#L63) |

### `tests/policy.py`

[Open source](../tests/policy.py)

| Kind | Signature | Decorators | Source |
| --- | --- | --- | --- |
| Function | `reject(action, expected)` | — | [L9](../tests/policy.py#L9) |
| Function | `<lambda@21:12>()` | — | [L21](../tests/policy.py#L21) |
| Function | `<lambda@28:12>()` | — | [L28](../tests/policy.py#L28) |

### `tests/smoke.py`

[Open source](../tests/smoke.py)

| Kind | Signature | Decorators | Source |
| --- | --- | --- | --- |
| Function | `until(check, label, timeout=45)` | — | [L16](../tests/smoke.py#L16) |
| Function | `api(method, path, actor='rider-a', *, expected=200, key=None, body=None)` | — | [L28](../tests/smoke.py#L28) |
| Function | `check()` | — | [L37](../tests/smoke.py#L37) |
| Function | `check.<lambda@38:11>()` | — | [L38](../tests/smoke.py#L38) |
| Function | `check.<lambda@39:11>()` | — | [L39](../tests/smoke.py#L39) |
| Function | `check.offer_for_trip()` | — | [L49](../tests/smoke.py#L49) |
| Function | `check.<lambda@64:11>()` | — | [L64](../tests/smoke.py#L64) |
| Function | `check.learned()` | — | [L71](../tests/smoke.py#L71) |

### `workers/events.py`

[Open source](../workers/events.py)

| Kind | Signature | Decorators | Source |
| --- | --- | --- | --- |
| Function | `choose(candidates, zone)` | — | [L17](../workers/events.py#L17) |
| Function | `choose.<lambda@33:38>(d)` | — | [L33](../workers/events.py#L33) |
| Function | `choose.<lambda@36:38>(d)` | — | [L36](../workers/events.py#L36) |
| Function | `apply(event)` | — | [L41](../workers/events.py#L41) |
| Function | `update_features()` | — | [L76](../workers/events.py#L76) |
| Function | `next_event()` | — | [L90](../workers/events.py#L90) |
| Function | `mark_sent(event)` | — | [L96](../workers/events.py#L96) |
| Function | `local_tick()` | — | [L101](../workers/events.py#L101) |
| Function | `kafka_loop()` | — | [L111](../workers/events.py#L111) |
| Function | `kafka_loop.<lambda@122:46>(error, _)` | — | [L122](../workers/events.py#L122) |

<!-- END GENERATED CATALOG -->
