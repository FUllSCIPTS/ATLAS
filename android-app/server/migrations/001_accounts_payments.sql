-- ATLAS Go server, migration 001: accounts, sessions, bank accounts, payments, ledger, payouts.
-- PostgreSQL 14 or newer. Applied once by server/db.py inside one transaction.
-- Money is INTEGER euro cents everywhere; times are TIMESTAMPTZ supplied by the application clock.

CREATE TABLE accounts (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role                TEXT NOT NULL CHECK (role IN ('passenger', 'driver', 'seller')),
    name                TEXT NOT NULL CHECK (char_length(name) BETWEEN 2 AND 40),
    email               TEXT NOT NULL UNIQUE CHECK (email = lower(email) AND char_length(email) <= 80),
    phone               TEXT NOT NULL CHECK (phone = '' OR phone ~ '^\+[1-9][0-9]{7,14}$'),
    password_salt       BYTEA NOT NULL,
    password_hash       BYTEA NOT NULL,
    password_iterations INTEGER NOT NULL CHECK (password_iterations >= 1000),
    created_at          TIMESTAMPTZ NOT NULL,
    deleted_at          TIMESTAMPTZ
);

CREATE TABLE driver_profiles (
    account_id UUID PRIMARY KEY REFERENCES accounts (id),
    vehicle    TEXT NOT NULL,
    plate      TEXT NOT NULL,
    licence    TEXT NOT NULL,
    seats      SMALLINT NOT NULL CHECK (seats BETWEEN 1 AND 8),
    verified   BOOLEAN NOT NULL DEFAULT FALSE           -- set by an operator after checking documents
);

CREATE TABLE kitchens (
    id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    owner_id     UUID NOT NULL UNIQUE REFERENCES accounts (id),
    name         TEXT NOT NULL,
    cuisine      TEXT NOT NULL,
    registration TEXT NOT NULL,
    place        SMALLINT NOT NULL CHECK (place BETWEEN 0 AND 3),
    prep_minutes SMALLINT NOT NULL CHECK (prep_minutes BETWEEN 5 AND 90),
    open         BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE UNIQUE INDEX kitchens_name ON kitchens (lower(name));

CREATE TABLE dishes (
    kitchen_id  BIGINT NOT NULL REFERENCES kitchens (id),
    dish_id     TEXT NOT NULL,                          -- the phone's id, e.g. k3-1
    name        TEXT NOT NULL,
    detail      TEXT NOT NULL,
    price_cents INTEGER NOT NULL CHECK (price_cents BETWEEN 50 AND 20000),
    archived    BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (kitchen_id, dish_id)
);

-- Session tokens are random 256-bit values; only their SHA-256 is stored.
CREATE TABLE sessions (
    token_hash BYTEA PRIMARY KEY,
    account_id UUID NOT NULL REFERENCES accounts (id),
    created_at TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ
);
CREATE INDEX sessions_account ON sessions (account_id);

CREATE TABLE login_failures (
    email        TEXT PRIMARY KEY,
    failures     INTEGER NOT NULL,
    locked_until TIMESTAMPTZ
);

-- The IBAN itself is not stored. The bank provider keeps it and returns a token; we keep what a
-- receipt shows (holder, country, last four) and a keyed fingerprint for duplicate detection.
CREATE TABLE bank_accounts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id      UUID NOT NULL REFERENCES accounts (id),
    purpose         TEXT NOT NULL CHECK (purpose IN ('debit', 'payout')),
    holder          TEXT NOT NULL,
    country         CHAR(2) NOT NULL,
    last4           CHAR(4) NOT NULL,
    fingerprint     BYTEA NOT NULL,                     -- HMAC-SHA256(server pepper, IBAN)
    provider_token  TEXT NOT NULL,
    mandate_id      TEXT,
    mandate_version TEXT,
    created_at      TIMESTAMPTZ NOT NULL,
    revoked_at      TIMESTAMPTZ,
    CHECK ((purpose = 'debit') = (mandate_id IS NOT NULL))
);
CREATE UNIQUE INDEX bank_accounts_active ON bank_accounts (account_id) WHERE revoked_at IS NULL;

CREATE TABLE payments (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payer_id           UUID NOT NULL REFERENCES accounts (id),
    payee_id           UUID REFERENCES accounts (id),
    house_payee        TEXT CHECK (house_payee IN ('fleet', 'kitchen-0', 'kitchen-1', 'kitchen-2')),
    kind               TEXT NOT NULL CHECK (kind IN ('ride', 'shared', 'food')),
    reference          TEXT NOT NULL,
    amount_cents       INTEGER NOT NULL CHECK (amount_cents > 0),
    payee_net_cents    INTEGER NOT NULL CHECK (payee_net_cents >= 0),
    platform_fee_cents INTEGER NOT NULL CHECK (platform_fee_cents >= 0),
    status             TEXT NOT NULL CHECK (status IN ('captured', 'declined', 'refunded')),
    decline_reason     TEXT,
    last4              CHAR(4) NOT NULL,
    idempotency_key    TEXT NOT NULL,
    request_hash       BYTEA NOT NULL,
    created_at         TIMESTAMPTZ NOT NULL,
    CHECK (payee_net_cents + platform_fee_cents = amount_cents),
    CHECK ((payee_id IS NULL) <> (house_payee IS NULL)),
    CHECK ((status = 'declined') = (decline_reason IS NOT NULL)),
    UNIQUE (payer_id, idempotency_key)
);
-- One booking is paid at most once (a declined attempt may be followed by a successful one).
CREATE UNIQUE INDEX payments_reference_paid ON payments (payer_id, reference) WHERE status <> 'declined';
CREATE INDEX payments_payee ON payments (payee_id);

CREATE TABLE payouts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id      UUID NOT NULL REFERENCES accounts (id),
    amount_cents    INTEGER NOT NULL CHECK (amount_cents >= 100),
    status          TEXT NOT NULL CHECK (status IN ('paid', 'failed')),
    last4           CHAR(4) NOT NULL,
    idempotency_key TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL,
    UNIQUE (account_id, idempotency_key)
);

-- Double-entry ledger from the platform's books. Each row is one side of a transaction.
CREATE TABLE ledger_entries (
    id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    txn          TEXT NOT NULL,                          -- payment id, payment id || ':refund', or payout id
    account      TEXT NOT NULL,                          -- bank:clearing, revenue:commission, payable:<account>
    debit_cents  INTEGER NOT NULL CHECK (debit_cents >= 0),
    credit_cents INTEGER NOT NULL CHECK (credit_cents >= 0),
    created_at   TIMESTAMPTZ NOT NULL,
    CHECK ((debit_cents > 0) <> (credit_cents > 0))
);
CREATE INDEX ledger_account ON ledger_entries (account);
CREATE INDEX ledger_txn ON ledger_entries (txn);

-- Invariant 1: the ledger is append-only. Corrections are new entries, never edits.
CREATE FUNCTION ledger_append_only() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'ledger_entries is append-only' USING ERRCODE = 'integrity_constraint_violation';
END $$;
CREATE TRIGGER ledger_no_change BEFORE UPDATE OR DELETE ON ledger_entries
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
CREATE TRIGGER ledger_no_truncate BEFORE TRUNCATE ON ledger_entries
    FOR EACH STATEMENT EXECUTE FUNCTION ledger_append_only();

-- Invariant 2: every transaction's debits equal its credits, checked when the SQL transaction commits.
CREATE FUNCTION ledger_txn_balanced() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    off BIGINT;
BEGIN
    SELECT COALESCE(SUM(debit_cents), 0) - COALESCE(SUM(credit_cents), 0) INTO off
      FROM ledger_entries WHERE txn = NEW.txn;
    IF off <> 0 THEN
        RAISE EXCEPTION 'ledger transaction % does not balance (off by % cents)', NEW.txn, off
            USING ERRCODE = 'check_violation';
    END IF;
    RETURN NULL;
END $$;
CREATE CONSTRAINT TRIGGER ledger_balanced AFTER INSERT ON ledger_entries
    DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION ledger_txn_balanced();

-- Transactional outbox: events are written in the same transaction as the change they describe.
CREATE TABLE outbox (
    id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_type   TEXT NOT NULL,
    body         JSONB NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL,
    published_at TIMESTAMPTZ
);

-- Who did what, when. Never contains passwords, tokens or IBANs.
CREATE TABLE audit_log (
    id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    at         TIMESTAMPTZ NOT NULL,
    account_id UUID,
    action     TEXT NOT NULL,
    detail     JSONB NOT NULL DEFAULT '{}'
);
CREATE INDEX audit_account ON audit_log (account_id, at);
