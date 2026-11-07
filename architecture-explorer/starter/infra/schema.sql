CREATE TABLE IF NOT EXISTS trips (
    id TEXT PRIMARY KEY, rider_id TEXT NOT NULL, request_key TEXT NOT NULL,
    pickup TEXT NOT NULL, destination TEXT NOT NULL, zone TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('requested','assigned','picked_up','completed')),
    driver_id TEXT, created_at BIGINT NOT NULL, UNIQUE (rider_id, request_key)
);
CREATE TABLE IF NOT EXISTS drivers (
    id TEXT PRIMARY KEY, online INTEGER NOT NULL, distance_km REAL NOT NULL,
    speed_kph REAL NOT NULL, active_trip TEXT REFERENCES trips(id)
);
CREATE TABLE IF NOT EXISTS offers (
    trip_id TEXT PRIMARY KEY REFERENCES trips(id), driver_id TEXT NOT NULL REFERENCES drivers(id),
    state TEXT NOT NULL CHECK (state IN ('offered','accepted')),
    action INTEGER NOT NULL, bucket INTEGER NOT NULL, policy_version TEXT NOT NULL,
    model_version TEXT NOT NULL, forecast REAL, acceptance REAL, anomaly_flag INTEGER
);
CREATE TABLE IF NOT EXISTS outbox (
    seq __SEQUENCE__, event_id TEXT NOT NULL UNIQUE,
    trip_id TEXT NOT NULL REFERENCES trips(id), event_type TEXT NOT NULL,
    occurred_at BIGINT NOT NULL, body TEXT NOT NULL, sent INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS pending_outbox ON outbox (sent, seq);
CREATE TABLE IF NOT EXISTS inbox (event_id TEXT PRIMARY KEY);
CREATE TABLE IF NOT EXISTS experience (
    trip_id TEXT PRIMARY KEY REFERENCES trips(id), state INTEGER NOT NULL,
    action INTEGER NOT NULL, reward REAL NOT NULL, policy_version TEXT NOT NULL,
    occurred_at BIGINT NOT NULL
);
