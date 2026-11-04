const groups = {
  client: { label: "Client apps", caption: "Mobile clients", color: "#7ed8ef", x: 19 },
  service: { label: "FastAPI services", caption: "Request handling", color: "#c2f77a", x: 242 },
  data: { label: "Data & streaming", caption: "Storage and events", color: "#ffc983", x: 465 },
  ml: { label: "Intelligence", caption: "Prediction and learning", color: "#c4aeff", x: 688 },
};

const components = {
  passenger: {
    title: "Passenger app", tech: "Browser · REST polling", group: "client", icon: "user", y: 104, file: "passenger",
    summary: "A browser app that creates a trip with an idempotency key and polls the trip until pickup and completion.",
    inputs: "Demo rider key, pickup, destination and zone",
    outputs: "POST /v1/rider/trips and GET /v1/rider/trips/{id}",
    notes: "Open /passenger on port 8000. The starter uses text locations and two Cork zones.",
  },
  driver: {
    title: "Driver app", tech: "Browser · REST polling", group: "client", icon: "car", y: 274, file: "driver",
    summary: "A browser app that sends availability, polls offers and accepts or completes assigned rides.",
    inputs: "Demo driver key, distance and speed",
    outputs: "Availability, offer acceptance, pickup and completion",
    notes: "Open /driver on port 8000. Driver A and Driver B are seeded as separate identities.",
  },
  gateway: {
    title: "API Gateway", tech: "FastAPI · REST gateway", group: "service", icon: "gateway", y: 65, file: "gateway",
    summary: "Serves both browser apps, checks bearer keys and forwards only supported routes to internal APIs.",
    inputs: "Same-origin browser requests with a demo bearer key",
    outputs: "Role-checked internal HTTP requests and poll responses",
    notes: "Only port 8000 is published. Replace development keys with identity-provider sessions before exposing the application.",
  },
  trip: {
    title: "Trip Service", tech: "FastAPI · lifecycle", group: "service", icon: "route", y: 180, file: "trip",
    summary: "Persists each booking, owns the trip state machine and creates outbox events in the same transaction.",
    inputs: "Idempotent bookings, assignment events and driver milestones",
    outputs: "requested → assigned → picked_up → completed",
    notes: "Use the unique rider/key constraint and conditional updates to reject invalid transitions and duplicate side effects.",
  },
  dispatch: {
    title: "Dispatch Service", tech: "FastAPI · matching", group: "service", icon: "target", y: 295, file: "dispatch",
    summary: "Tracks driver availability and offers. The event worker scores candidates and records an offer on its behalf.",
    inputs: "Driver telemetry, trip requests and model score response",
    outputs: "Authorized offers, acceptance and assignment events",
    notes: "Reserve a driver with an atomic update. Use nearest eligible driver when model serving is unavailable.",
  },
  postgres: {
    title: "PostgreSQL", tech: "Trips · offers · outbox", group: "data", icon: "database", y: 65, file: "migrations",
    summary: "Stores trips, driver state, offers, the outbox, consumer deduplication and RL experiences.",
    inputs: "FastAPI and worker transactions",
    outputs: "Stored ride state and committed events",
    notes: "Docker Compose uses PostgreSQL. The quick local run uses SQLite with the same state machine.",
  },
  kafka: {
    title: "Kafka", tech: "Topic · atlas.ride.v1", group: "data", icon: "kafka", y: 180, file: "events",
    summary: "Carries versioned ride events keyed by trip ID. The demo worker handles dispatch, assignment and features.",
    inputs: "Acknowledged outbox publications",
    outputs: "trip.requested, dispatch.assignment.confirmed and trip.completed",
    notes: "The starter uses one partition and at-least-once delivery. The worker records event IDs before committing offsets.",
  },
  stream: {
    title: "Feature Worker", tech: "Python · event worker", group: "data", icon: "activity", y: 295, file: "features",
    summary: "Consumes ride events, writes 12 five-minute demand buckets by zone and joins completed trips to their dispatch decisions.",
    inputs: "Kafka or local outbox events",
    outputs: "demand.json and terminal RL experiences",
    notes: "One worker runs the relay and consumers in the starter. Replay is safe through the inbox and unique trip keys.",
  },
  lstm: {
    title: "LSTM Predictor", tech: "PyTorch · CPU LSTM", group: "ml", icon: "trend", y: 65, file: "lstm",
    summary: "Trains a PyTorch LSTM and forecasts the next five-minute ride count for a zone.",
    inputs: "12 ordered demand counts for the zone",
    outputs: "Forecast count, demand bucket and model version",
    notes: "The included trainer uses a seeded synthetic time series and reports holdout MAE. Inference reads live event buckets when available.",
  },
  discrete: {
    title: "Discrete ML Models", tech: "scikit-learn · two models", group: "ml", icon: "layers", y: 151, file: "discrete",
    summary: "Trains logistic regression for offer acceptance and Isolation Forest for unusual candidate telemetry.",
    inputs: "Distance in km and speed in km/h",
    outputs: "Acceptance probability and anomaly flag per candidate",
    notes: "Dispatch uses acceptance scores when the approved strategy calls for them. Anomaly flags are recorded for review.",
  },
  rl: {
    title: "RL Agent", tech: "Q-learning · batch trainer", group: "ml", icon: "brain", y: 237, file: "rl",
    summary: "Learns one dispatch strategy per demand bucket from completed trips or a synthetic demo fixture.",
    inputs: "Demand bucket, strategy, terminal reward and policy version",
    outputs: "Versioned candidates after at least 80 recorded outcomes",
    notes: "The trainer runs every minute. Only the explicit approval command can activate a candidate.",
  },
  registry: {
    title: "Policy Registry", tech: "Versioned model artifacts", group: "ml", icon: "archive", y: 323, file: "registry",
    summary: "Stores trained models, their metrics and versioned policy candidates. An atomic pointer identifies the active policy.",
    inputs: "Model checkpoint, holdout results and explicit approval",
    outputs: "Active model version, approved policy and baseline rollback",
    notes: "Approval checks minimum holdout support and reward against nearest-driver baseline. Only load artifacts from trusted training jobs.",
  },
};

// Paths share the same coordinate system as the component cards.
const links = [
  { id: "request", from: "passenger", to: "gateway", kind: "sync", label: "POST /v1/rider/trips", path: "M207 128H222V86H242" },
  { id: "telemetry", from: "driver", to: "gateway", kind: "sync", label: "Driver telemetry and offer decisions", path: "M207 290H231V108H242" },
  { id: "trip-request", from: "gateway", to: "trip", kind: "sync", label: "Authenticated booking request", path: "M303 121V180" },
  { id: "driver-state", from: "gateway", to: "dispatch", kind: "sync", label: "Driver availability, offer polls and acceptance", path: "M242 116H220V329H242" },
  { id: "trip-store", from: "trip", to: "postgres", kind: "sync", label: "Trip and outbox transaction", path: "M430 196H445V87H465" },
  { id: "outbox", from: "postgres", to: "kafka", kind: "event", label: "Outbox relay publishes committed events", path: "M563 121V180" },
  { id: "queue", from: "kafka", to: "dispatch", kind: "event", label: "trip.requested", path: "M465 218H455V315H430" },
  { id: "assignment-store", from: "dispatch", to: "postgres", kind: "sync", label: "Offer or assignment + outbox transaction", path: "M430 304H437V106H465" },
  { id: "assignment", from: "kafka", to: "trip", kind: "event", label: "dispatch.assignment.confirmed", path: "M465 206H430" },
  { id: "trip-poll", from: "trip", to: "gateway", kind: "sync", label: "Authorized trip snapshot", path: "M353 180V121" },
  { id: "offer-poll", from: "dispatch", to: "gateway", kind: "sync", label: "Authorized offers and assignment state", path: "M242 311H237V76H242" },
  { id: "milestone", from: "gateway", to: "trip", kind: "sync", label: "Driver pickup or completion", path: "M384 121V180" },
  { id: "passenger-read", from: "gateway", to: "passenger", kind: "sync", label: "GET /v1/rider/trips/{id} response", path: "M242 99H227V145H207" },
  { id: "driver-read", from: "gateway", to: "driver", kind: "sync", label: "GET /v1/driver/offers response", path: "M242 78H214V314H207" },
  { id: "event-window", from: "kafka", to: "stream", kind: "event", label: "Keyed ride and outcome streams", path: "M563 236V295" },
  { id: "demand-features", from: "stream", to: "lstm", kind: "learn", label: "Time-windowed zone features", path: "M653 306H660V90H688" },
  { id: "scoring-features", from: "dispatch", to: "discrete", kind: "learn", label: "Candidate and telemetry features", path: "M430 334H448V386H670V197H688" },
  { id: "experience", from: "stream", to: "rl", kind: "learn", label: "Logged state, action and delayed reward", path: "M653 328H676V260H688" },
  { id: "forecast", from: "lstm", to: "dispatch", kind: "learn", label: "Zone demand forecast read by dispatch", path: "M736 65V53H433V279H392V295" },
  { id: "scores", from: "discrete", to: "dispatch", kind: "learn", label: "Candidate acceptance scores", path: "M876 177H882V373H376V351" },
  { id: "candidate", from: "rl", to: "registry", kind: "learn", label: "Evaluated policy candidate", path: "M788 293V323" },
  { id: "approved", from: "registry", to: "dispatch", kind: "learn", label: "Approved policy, pinned by version", path: "M740 379V394H319V351" },
];

const scenarios = {
  "booking": {
    "title": "Book a ride",
    "icon": "route",
    "steps": [
      [
        "request",
        "The passenger sends a pickup, destination, zone and an idempotency key."
      ],
      [
        "trip-request",
        "The gateway validates the rider key and forwards the booking to Trip Service."
      ],
      [
        "trip-store",
        "The service inserts the requested trip and its trip.requested outbox row in one transaction."
      ],
      [
        "outbox",
        "The worker publishes the committed event to atlas.ride.v1, keyed by trip ID."
      ],
      [
        "queue",
        "The worker handles trip.requested for Dispatch and scores eligible drivers via the model service."
      ],
      [
        "assignment-store",
        "Dispatch records the offer, prediction metadata and dispatch.offer.created."
      ],
      [
        "offer-poll",
        "On the next driver poll, Dispatch returns the offer scoped to that driver."
      ],
      [
        "driver-read",
        "The driver app displays the route and enables the Accept button."
      ]
    ]
  },
  "driver": {
    "title": "Driver updates",
    "icon": "car",
    "steps": [
      [
        "telemetry",
        "The selected driver posts the accepted offer ID through the gateway."
      ],
      [
        "driver-state",
        "Dispatch verifies ownership and confirms that the driver is available."
      ],
      [
        "assignment-store",
        "Dispatch reserves the driver and inserts dispatch.assignment.confirmed atomically."
      ],
      [
        "outbox",
        "The event worker publishes the assignment event to Kafka."
      ],
      [
        "assignment",
        "The assignment handler updates the trip to assigned and emits trip.assigned."
      ],
      [
        "trip-poll",
        "A passenger status poll returns the committed trip snapshot."
      ],
      [
        "passenger-read",
        "The passenger sees the assigned driver and can follow pickup and completion."
      ],
      [
        "milestone",
        "The driver app sends picked_up and completed. Trip Service verifies the assigned driver and transition."
      ],
      [
        "trip-store",
        "Completion frees the driver and inserts trip.completed for the learning loop."
      ]
    ]
  },
  "learning": {
    "title": "Learning loop",
    "icon": "brain",
    "steps": [
      [
        "event-window",
        "The event worker uses trip.requested counts and completed-trip outcomes."
      ],
      [
        "demand-features",
        "The worker writes twelve five-minute counts per zone to demand.json."
      ],
      [
        "forecast",
        "The internal scorer runs the trained LSTM and maps predicted demand to a low or high bucket."
      ],
      [
        "scoring-features",
        "Scoring uses current candidate distance and speed alongside the forecast."
      ],
      [
        "scores",
        "The internal API returns acceptance probabilities, anomaly flags and the model version."
      ],
      [
        "experience",
        "Completion logs one terminal reward with the original strategy and policy version."
      ],
      [
        "candidate",
        "Batch Q-learning writes a candidate. An explicit approval command checks held-out support and reward."
      ],
      [
        "approved",
        "Dispatch uses the approved strategy when policy inference is enabled and falls back to nearest-driver selection."
      ]
    ]
  }
};

const folders = [
  {
    "name": "apps",
    "children": [
      {
        "id": "passenger",
        "name": "passenger/",
        "detail": "Booking form and status polling in the passenger browser app.",
        "example": [
          "index.html"
        ]
      },
      {
        "id": "driver",
        "name": "driver/",
        "detail": "Availability, offer acceptance, pickup and completion in the driver browser app.",
        "example": [
          "index.html"
        ]
      },
      {
        "id": "shared",
        "name": "shared/",
        "detail": "Shared browser fetch client, role-specific actions and styles.",
        "example": [
          "client.js",
          "demo.css"
        ]
      }
    ]
  },
  {
    "name": "services",
    "children": [
      {
        "id": "gateway",
        "name": "gateway.py",
        "detail": "Public entry point, auth and an allowlist for forwarded requests.",
        "example": [
          "gateway.py"
        ]
      },
      {
        "id": "trip",
        "name": "trips.py",
        "detail": "Creates trips, returns status and validates milestones.",
        "example": [
          "trips.py"
        ]
      },
      {
        "id": "dispatch",
        "name": "dispatch.py",
        "detail": "Updates availability, returns offers and atomically accepts assignments.",
        "example": [
          "dispatch.py"
        ]
      }
    ]
  },
  {
    "name": "workers",
    "children": [
      {
        "id": "features",
        "name": "events.py",
        "detail": "Publishes committed outbox rows, applies Kafka events, derives demand buckets and records experiences.",
        "example": [
          "events.py"
        ],
        "component": "stream"
      }
    ]
  },
  {
    "name": "ml",
    "children": [
      {
        "id": "lstm",
        "name": "forecast.py",
        "detail": "Trains and runs the PyTorch LSTM.",
        "example": [
          "forecast.py",
          "train.py",
          "serve.py"
        ]
      },
      {
        "id": "discrete",
        "name": "discrete.py",
        "detail": "Trains and serves the acceptance and anomaly models.",
        "example": [
          "discrete.py",
          "train.py",
          "serve.py"
        ]
      },
      {
        "id": "rl",
        "name": "rl.py",
        "detail": "Builds candidates from completed trips, evaluates them, and approves or rolls back a policy.",
        "example": [
          "rl.py"
        ]
      },
      {
        "id": "registry",
        "name": "registry.py",
        "detail": "Writes manifests atomically and manages model artifact paths.",
        "example": [
          "registry.py"
        ]
      }
    ]
  },
  {
    "name": "packages",
    "children": [
      {
        "id": "events",
        "name": "Ride event contract",
        "detail": "Versioned Kafka envelope with payload shapes, emitted by the DB helpers.",
        "example": [
          "ride-event.schema.json",
          "db.py"
        ],
        "component": "kafka"
      },
      {
        "id": "config",
        "name": "Service configuration",
        "detail": "Environment, role validation and shared runtime paths.",
        "example": [
          "config.py",
          "db.py"
        ]
      }
    ]
  },
  {
    "name": "infra",
    "children": [
      {
        "id": "migrations",
        "name": "Database schema",
        "detail": "Tables for rides, drivers, offers, outbox, inbox and experience.",
        "example": [
          "schema.sql"
        ],
        "component": "postgres"
      }
    ]
  },
  {
    "name": "scripts",
    "children": [
      {
        "id": "local",
        "name": "Runtime scripts",
        "detail": "Bootstrap the database and models, or run the complete SQLite demo locally.",
        "example": [
          "initialize.sh",
          "local.sh"
        ]
      }
    ]
  },
  {
    "name": "tests",
    "children": [
      {
        "id": "e2e",
        "name": "End-to-end checks",
        "detail": "Exercises authorization, idempotency, offer, assignment, completion and model outputs.",
        "example": [
          "smoke.py",
          "policy.py"
        ]
      }
    ]
  },
  {
    "name": "starter",
    "root": true,
    "children": [
      {
        "id": "compose",
        "name": "Container deployment",
        "detail": "Image build, Compose wiring and exact dependency versions.",
        "example": [
          "Dockerfile",
          "compose.yaml",
          "requirements.txt"
        ]
      }
    ]
  }
];

const zones = [
  {
    "title": "Browser clients",
    "sub": "Passenger and driver",
    "icon": "user",
    "group": "client",
    "nodes": [
      "passenger",
      "driver"
    ],
    "boundary": "Open /passenger and /driver on port 8000. The demo polls REST endpoints with role-specific development keys."
  },
  {
    "title": "API runtime",
    "sub": "One exposed gateway",
    "icon": "cloud",
    "group": "service",
    "nodes": [
      "gateway",
      "trip",
      "dispatch"
    ],
    "boundary": "Compose publishes only the gateway to 127.0.0.1. Trips and Dispatch remain on the internal network."
  },
  {
    "title": "Data plane",
    "sub": "Private network",
    "icon": "database",
    "group": "data",
    "nodes": [
      "postgres",
      "kafka",
      "stream"
    ],
    "boundary": "PostgreSQL owns committed state. Kafka transports ride events. A single worker publishes outbox rows and processes events."
  },
  {
    "title": "ML runtime",
    "sub": "Internal inference and training",
    "icon": "brain",
    "group": "ml",
    "nodes": [
      "lstm",
      "discrete",
      "rl",
      "registry"
    ],
    "boundary": "A CPU training job writes model artifacts. The scorer serves them privately. The RL watcher creates candidates for review."
  }
];

