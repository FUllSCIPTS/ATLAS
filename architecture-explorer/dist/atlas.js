const groups = {
  client: { label: "Client apps", caption: "Mobile clients", color: "#7ed8ef", x: 19 },
  service: { label: "FastAPI services", caption: "Request handling", color: "#c2f77a", x: 242 },
  data: { label: "Data & streaming", caption: "Storage and events", color: "#ffc983", x: 465 },
  ml: { label: "Intelligence", caption: "Prediction and learning", color: "#c4aeff", x: 688 },
};

const components = {
  passenger: {
    title: "Passenger app", tech: "Mobile client", group: "client", icon: "user", y: 104, file: "passenger",
    summary: "Requests a ride and shows the passenger its live status from pickup to completion.",
    inputs: "Pickup, destination and passenger account session",
    outputs: "Trip request, cancellation and status subscription",
    notes: "Send an idempotency key on booking retries. Reconnect with a trip snapshot before resuming live updates.",
  },
  driver: {
    title: "Driver app", tech: "Mobile client", group: "client", icon: "car", y: 274, file: "driver",
    summary: "Reports availability and location, receives ride offers, and records driver decisions and trip milestones.",
    inputs: "Authenticated offers, device location and driver actions",
    outputs: "Location samples, availability and offer decisions",
    notes: "Buffer telemetry briefly on disconnect. Deduplicate retried offer decisions by offer ID.",
  },
  gateway: {
    title: "API Gateway", tech: "FastAPI · REST / WebSocket", group: "service", icon: "gateway", y: 65, file: "gateway",
    summary: "Authenticates both apps, validates their requests and relays authorized trip or offer updates to connected clients.",
    inputs: "Mobile requests and Kafka status events",
    outputs: "Authenticated service requests and WebSocket updates",
    notes: "Keep routing and access checks here. Trip lifecycle rules belong to the Trip Service.",
  },
  trip: {
    title: "Trip Service", tech: "FastAPI · lifecycle", group: "service", icon: "route", y: 180, file: "trip",
    summary: "Owns the trip lifecycle. It validates state transitions, writes the trip and its outbox event together, and consumes assignment outcomes.",
    inputs: "Validated booking requests and assignment events",
    outputs: "Trip snapshots and lifecycle events via the outbox",
    notes: "Use request idempotency and versioned state transitions to handle retries and duplicate delivery.",
  },
  dispatch: {
    title: "Dispatch Service", tech: "FastAPI · matching", group: "service", icon: "target", y: 295, file: "dispatch",
    summary: "Finds eligible drivers and ranks them using model scores and an approved RL policy. It records offers and assignments.",
    inputs: "Trip requests, driver availability, model scores and approved policy",
    outputs: "Offers and assignment outcomes via the outbox",
    notes: "Keep eligibility and safety rules deterministic. Apply timeouts to scoring and fall back to a baseline ranker.",
  },
  postgres: {
    title: "PostgreSQL", tech: "Trips · drivers · outbox", group: "data", icon: "database", y: 65, file: "migrations",
    summary: "Stores trips, driver availability, offer and assignment records, plus an outbox for reliable event publication.",
    inputs: "Transactional writes from Trip and Dispatch services",
    outputs: "Consistent reads and committed events for the outbox relay",
    notes: "Scope data ownership by service. Commit a state change and its outbox row in the same transaction.",
  },
  kafka: {
    title: "Kafka", tech: "Durable event topics", group: "data", icon: "kafka", y: 180, file: "events",
    summary: "Carries ride events from producers to independent consumers for dispatch, status updates and model learning.",
    inputs: "Outbox events from trip and dispatch transactions",
    outputs: "Keyed event streams for gateway, services and feature workers",
    notes: "Order lifecycle events within a trip key. Consumers handle duplicates and track lag independently.",
  },
  stream: {
    title: "Feature Worker", tech: "Python · Kafka consumer", group: "data", icon: "activity", y: 295, file: "features",
    summary: "Turns raw trip and driver events into time-windowed features and joins eventual outcomes to the decisions that produced them.",
    inputs: "Location, trip, dispatch and outcome events",
    outputs: "Demand histories, scoring features and RL experience records",
    notes: "Use event time, handle late data and keep only the fields needed for each learning task.",
  },
  lstm: {
    title: "LSTM Predictor", tech: "Demand forecasting", group: "ml", icon: "trend", y: 65, file: "lstm",
    summary: "Predicts near-term ride demand by zone from recent event windows and contextual features.",
    inputs: "Time-ordered zone demand and availability features",
    outputs: "Versioned forecasts cached by zone and time window",
    notes: "Dispatch reads the most recent forecast and falls back to a historical baseline when it becomes stale.",
  },
  discrete: {
    title: "Discrete ML Models", tech: "Acceptance · anomaly scores", group: "ml", icon: "layers", y: 151, file: "discrete",
    summary: "Independent task-specific models score driver acceptance likelihood and flag unusual telemetry for review.",
    inputs: "Candidate-level and driver telemetry features",
    outputs: "Acceptance probabilities and anomaly flags",
    notes: "Acceptance scores can rank eligible offers. Route anomaly flags to review and keep thresholds versioned.",
  },
  rl: {
    title: "RL Agent", tech: "Continuous learning", group: "ml", icon: "brain", y: 237, file: "rl",
    summary: "Learns dispatch preferences from recorded decisions and delayed outcomes such as pickup time, cancellations and driver idle time.",
    inputs: "State, action, reward, next state and deployed policy version",
    outputs: "Candidate policies for replay evaluation and shadow testing",
    notes: "Train on a rolling schedule. Gate candidate promotion with evaluation and guardrails, and keep rollback to the last approved policy.",
  },
  registry: {
    title: "Policy Registry", tech: "Versioned policy artifacts", group: "ml", icon: "archive", y: 323, file: "registry",
    summary: "Tracks candidate and approved policies, evaluation results and the active policy version used by dispatch.",
    inputs: "Candidate artifact, evaluation evidence and promotion decision",
    outputs: "Approved policy, manifest and rollback target",
    notes: "Pin the policy version per dispatch decision so later outcomes can be attributed to the policy that produced them.",
  },
};

// Paths share the same coordinate system as the component cards.
const links = [
  { id: "request", from: "passenger", to: "gateway", kind: "sync", label: "POST /v1/trips", path: "M207 128H222V86H242" },
  { id: "telemetry", from: "driver", to: "gateway", kind: "sync", label: "Driver telemetry and offer decisions", path: "M207 290H231V108H242" },
  { id: "trip-request", from: "gateway", to: "trip", kind: "sync", label: "Authenticated booking request", path: "M303 121V180" },
  { id: "driver-state", from: "gateway", to: "dispatch", kind: "sync", label: "Availability, location and accept / decline", path: "M242 116H220V329H242" },
  { id: "trip-store", from: "trip", to: "postgres", kind: "sync", label: "Trip and outbox transaction", path: "M430 196H445V87H465" },
  { id: "outbox", from: "postgres", to: "kafka", kind: "event", label: "Outbox relay publishes committed events", path: "M563 121V180" },
  { id: "queue", from: "kafka", to: "dispatch", kind: "event", label: "trip.requested.v1", path: "M465 218H455V315H430" },
  { id: "assignment-store", from: "dispatch", to: "postgres", kind: "sync", label: "Offer or assignment + outbox transaction", path: "M430 304H437V106H465" },
  { id: "assignment", from: "kafka", to: "trip", kind: "event", label: "trip.assignment_confirmed.v1", path: "M465 206H430" },
  { id: "updates", from: "kafka", to: "gateway", kind: "event", label: "Offer and trip status topics", path: "M501 180V150H353V121" },
  { id: "passenger-ws", from: "gateway", to: "passenger", kind: "sync", label: "WebSocket trip status", path: "M242 99H227V145H207" },
  { id: "driver-ws", from: "gateway", to: "driver", kind: "sync", label: "WebSocket offer or assignment", path: "M242 78H214V314H207" },
  { id: "event-window", from: "kafka", to: "stream", kind: "event", label: "Keyed ride and outcome streams", path: "M563 236V295" },
  { id: "demand-features", from: "stream", to: "lstm", kind: "learn", label: "Time-windowed zone features", path: "M653 306H660V90H688" },
  { id: "scoring-features", from: "stream", to: "discrete", kind: "learn", label: "Candidate and telemetry features", path: "M653 317H668V176H688" },
  { id: "experience", from: "stream", to: "rl", kind: "learn", label: "Logged state, action and delayed reward", path: "M653 328H676V260H688" },
  { id: "forecast", from: "lstm", to: "dispatch", kind: "learn", label: "Zone demand forecast read by dispatch", path: "M736 65V53H433V279H392V295" },
  { id: "scores", from: "discrete", to: "dispatch", kind: "learn", label: "Candidate acceptance scores", path: "M876 177H882V373H376V351" },
  { id: "candidate", from: "rl", to: "registry", kind: "learn", label: "Evaluated policy candidate", path: "M788 293V323" },
  { id: "approved", from: "registry", to: "dispatch", kind: "learn", label: "Approved policy, pinned by version", path: "M740 379V394H319V351" },
];

const scenarios = {
  booking: {
    title: "Book a ride", icon: "route", description: "Follow a booking request through the outbox to the first driver offer.",
    steps: [
      ["request", "Passenger submits the pickup and destination with an idempotency key."],
      ["trip-request", "The gateway authenticates the request and sends it to the Trip Service."],
      ["trip-store", "The Trip Service commits the pending trip and trip.requested.v1 outbox record together."],
      ["outbox", "The outbox relay publishes the committed trip request to Kafka."],
      ["queue", "Dispatch consumes the request, ranks eligible drivers and selects a candidate to offer."],
      ["assignment-store", "Dispatch persists the offer and a dispatch.offer_created.v1 outbox record."],
      ["outbox", "The relay publishes the offer event."],
      ["updates", "The gateway consumes the offer event and identifies the authorized driver session."],
      ["driver-ws", "The connected driver receives the offer. Acceptance follows the Driver updates flow."],
    ],
  },
  driver: {
    title: "Driver updates", icon: "car", description: "See how a driver's offer acceptance becomes a passenger status update.",
    steps: [
      ["telemetry", "The driver accepts an offer. Location pings use the same app-to-gateway route."],
      ["driver-state", "The gateway forwards the accepted offer ID to Dispatch."],
      ["assignment-store", "Dispatch confirms the offer is still active and atomically records the assignment and event."],
      ["outbox", "The relay publishes trip.assignment_confirmed.v1, keyed by trip ID."],
      ["assignment", "The Trip Service consumes the assignment event and moves the trip to Assigned."],
      ["trip-store", "It persists the new trip state and a trip.status_changed.v1 outbox record."],
      ["outbox", "The relay publishes the trip status change."],
      ["updates", "The gateway receives the status change and checks passenger authorization."],
      ["passenger-ws", "The passenger sees the assigned driver in the trip view."],
    ],
  },
  learning: {
    title: "Learning loop", icon: "brain", description: "See how completed trips feed forecasting, scoring and policy updates.",
    steps: [
      ["event-window", "Kafka supplies trip outcomes and dispatch decisions to the feature worker."],
      ["demand-features", "Time-windowed demand features feed the LSTM predictor."],
      ["forecast", "Dispatch uses the latest zone-level demand forecast as a ranking signal."],
      ["scoring-features", "The feature worker refreshes inputs for the task-specific models."],
      ["scores", "Dispatch reads acceptance scores for its eligible candidates."],
      ["experience", "The worker joins decisions to delayed rewards and feeds the RL training job."],
      ["candidate", "Replay evaluation and shadow testing precede policy approval."],
      ["approved", "Dispatch loads the approved policy version, and future decisions generate new experience."],
    ],
  },
};

const folders = [
  { name: "apps", summary: "Passenger and driver clients", children: [
    { id: "passenger", name: "passenger/", detail: "Booking screens, trip status, authenticated API client and live ride subscriptions.", example: ["src/screens/book_ride", "src/screens/trip_status", "src/api/trips", "src/realtime/trip_feed"] },
    { id: "driver", name: "driver/", detail: "Driver availability, telemetry collection, offer UI and trip actions.", example: ["src/screens/driver_home", "src/screens/offers", "src/telemetry/location", "src/api/dispatch"] },
  ] },
  { name: "services", summary: "HTTP and WebSocket entry points", children: [
    { id: "gateway", name: "gateway/", detail: "Auth dependencies, REST routes, Kafka status consumer and WebSocket sessions.", example: ["app/main.py", "app/auth.py", "app/routes.py", "app/websockets.py"] },
    { id: "trip", name: "trips/", detail: "Trip state machine, booking routes, persistence and assignment-event consumer.", example: ["app/api.py", "app/domain/lifecycle.py", "app/repository.py", "app/consumers/assignment.py"] },
    { id: "dispatch", name: "dispatch/", detail: "Candidate selection, driver endpoints, offer state and model integration.", example: ["app/api.py", "app/ranking.py", "app/offer_service.py", "app/policy_client.py"] },
  ] },
  { name: "workers", summary: "Background consumers and outbox relay", children: [
    { id: "outbox", name: "outbox/", detail: "Read committed outbox rows, publish to Kafka, then record successful publication.", example: ["relay.py", "publisher.py", "tests/test_retry.py"], component: "kafka" },
    { id: "features", name: "features/", detail: "Consume ride events, aggregate windows and join outcomes to recorded decisions.", example: ["consumer.py", "windows.py", "experience.py"], component: "stream" },
  ] },
  { name: "ml", summary: "Prediction, scoring and reinforcement learning", children: [
    { id: "lstm", name: "lstm/", detail: "Train and serve a per-zone demand predictor from time-windowed features.", example: ["dataset.py", "train.py", "predict.py", "tests/test_windows.py"] },
    { id: "discrete", name: "discrete/", detail: "Independent acceptance and anomaly models with separately versioned training and thresholds.", example: ["acceptance/train.py", "acceptance/score.py", "anomaly/train.py", "anomaly/score.py"] },
    { id: "rl", name: "rl/", detail: "Build experience batches, train candidate policies and replay decisions with guardrail metrics.", example: ["experience.py", "train.py", "evaluate.py", "shadow.py"] },
    { id: "registry", name: "registry/", detail: "Policy manifests, evaluation evidence, promotion and rollback tooling.", example: ["manifest.py", "promote.py", "rollback.py"] },
  ] },
  { name: "packages", summary: "Shared contracts", children: [
    { id: "events", name: "event_contracts/", detail: "Versioned schemas and examples shared by Kafka producers and consumers.", example: ["trip_requested.v1.json", "trip_assignment_confirmed.v1.json", "trip_status_changed.v1.json"], component: "kafka" },
  ] },
  { name: "infra", summary: "Local and hosted runtime configuration", children: [
    { id: "migrations", name: "postgres/", detail: "Schema migrations for trips, drivers, offers, assignments and the transactional outbox.", example: ["alembic.ini", "migrations/versions/001_core.py", "migrations/versions/002_outbox.py"], component: "postgres" },
    { id: "local", name: "compose/", detail: "Start APIs, Kafka, PostgreSQL and worker processes for local integration tests.", example: ["compose.yaml", "seed/demo_trips.json"] },
    { id: "deploy", name: "deploy/", detail: "Define API and worker deployments, internal services and managed data endpoints.", example: ["api-services.yaml", "workers.yaml", "network-policy.yaml"] },
  ] },
  { name: "tests", summary: "Cross-service verification", children: [
    { id: "e2e", name: "integration/", detail: "Exercise booking, driver acceptance and event replay across process boundaries.", example: ["test_booking_flow.py", "test_driver_acceptance.py", "test_event_replay.py"] },
  ] },
];

const zones = [
  { title: "Mobile devices", sub: "Public clients", icon: "user", group: "client", nodes: ["passenger", "driver"], boundary: "HTTPS / WSS to the gateway. Use short-lived sessions and reconnect after connectivity loss." },
  { title: "API runtime", sub: "Public ingress · private services", icon: "cloud", group: "service", nodes: ["gateway", "trip", "dispatch"], boundary: "Expose the gateway over TLS. Scale API replicas separately and keep service endpoints internal." },
  { title: "Data plane", sub: "Private network", icon: "database", group: "data", nodes: ["postgres", "kafka", "stream"], boundary: "Keep the database and Kafka on private endpoints. Run the outbox relay beside consumers with its own credentials." },
  { title: "ML runtime", sub: "Internal inference · background jobs", icon: "brain", group: "ml", nodes: ["lstm", "discrete", "rl", "registry"], boundary: "Serve predictions internally. Run training separately and load only approved, versioned policies in dispatch." },
];
