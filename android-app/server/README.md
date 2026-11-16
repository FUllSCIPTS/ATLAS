# ATLAS Go server — accounts, bank payments and payouts in PostgreSQL (1.5.0)

The back end for the ATLAS Go Android app: **registration and sign-in** for passengers, drivers and food sellers, **bank accounts** (SEPA Direct Debit mandates for passengers, payout accounts for drivers and sellers), **bank payments** with a server-side price check, a **double-entry ledger**, and **payouts**. FastAPI + psycopg 3 on **PostgreSQL 14 or newer** (tested on 16).

[App](../README.md) · [What the phone sends](../docs/PRIVACY.md) · [Security teaching guide](../../docs/INFORMATION_SECURITY.md#14-bank-payments-and-the-postgresql-back-end---implemented-sandbox-bank) · [UML: accounts, payments and the ledger](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/docs/UML_BLUEPRINT.md#atlas-go-15-bank-payments-and-the-postgresql-server)

> **Sandbox bank.** IBANs are validated for real (country, length, mod-97 check digits) but no bank is contacted and **no money moves**. `server/bank.py` defines the three calls a licensed payment provider must implement (`tokenise`, `debit`, `credit`); `SandboxBank` is the only implementation here. Rides and food orders themselves stay on the phone: the server is the system of record for **accounts, bank details, payments and payouts**.

## Run it

**With Docker** (from `android-app/server/`):

```bash
cp .env.example .env          # put two long random values in it (the file says how)
docker compose up -d --build
curl http://127.0.0.1:8080/healthz        # {"status":"ok","schema":1}
```

**Without Docker** (from `android-app/`, Python 3.12+, an existing PostgreSQL):

```bash
python -m pip install -r server/requirements.txt
createdb -E UTF8 -T template0 atlas
export DATABASE_URL=postgresql://USER:PASSWORD@127.0.0.1:5432/atlas
export ATLAS_BANK_PEPPER=$(python -c "import secrets; print(secrets.token_hex(32))")
python -m uvicorn --factory server.app:from_env --host 127.0.0.1 --port 8080
```

The first start applies `migrations/001_accounts_payments.sql`. In the app open **You → Bank & payments → ATLAS server**, enter the address and your password, and tap **Connect this account**. The app accepts `https://` addresses, and plain `http://` only for `localhost`, `127.0.0.1` and `10.0.2.2` (the host machine seen from an Android emulator) — a phone on another machine needs TLS in front of the server.

| Variable | Meaning | Default |
|---|---|---|
| `DATABASE_URL` | `postgresql://…` connection string | required |
| `ATLAS_BANK_PEPPER` | at least 16 random bytes in hex; keys the IBAN fingerprint. Keep it outside the database and its backups | required |
| `ATLAS_PBKDF2_ITERATIONS` | PBKDF2-HMAC-SHA256 work factor for new and upgraded password hashes | `600000` |
| `ATLAS_SESSION_HOURS` | lifetime of a session token | `720` |
| `ATLAS_MIGRATE` | `1` applies pending migrations at start; `0` when the API runs as the limited role | `1` |

**Least privilege.** Run the migrations as the database owner, then `psql "$OWNER_URL" -v app_password="'…'" -f server/roles.sql` and start the API with `DATABASE_URL=postgresql://atlas_app:…` and `ATLAS_MIGRATE=0`. `atlas_app` can read and write rows but cannot change the schema, cannot update or delete ledger, payout or audit rows, and cannot disable the triggers.

## API

Every route except registration, sign-in and `/healthz` needs `Authorization: Bearer <token>`. Errors are `{"error": {"code", "message", "field"?}}`.

| Method and path | Who | What it does |
|---|---|---|
| `POST /v1/accounts` | anyone | Register a passenger, driver (vehicle, plate, SPSV licence, seats) or seller (kitchen and dishes). `201` with the account and a session token; `409 email_taken` |
| `POST /v1/sessions` | anyone | Sign in. One `401` for unknown email and wrong password; five failures lock the email for 60 s (`429` + `Retry-After`) |
| `DELETE /v1/sessions/current` | signed in | Sign out: revoke this token |
| `GET /v1/me` | signed in | Account and linked bank account (holder, country, last four) |
| `DELETE /v1/accounts/me` | signed in + password | Erase the person; keep the money rows under an anonymous id. `409 balance_due` while a balance is owed |
| `PUT /v1/me/bank` | signed in + password | Link or replace the bank account. Passengers must send `consent: true` (the Direct Debit mandate) |
| `DELETE /v1/me/bank` | signed in + password | Revoke the bank account |
| `PUT /v1/seller/kitchen` | seller | Upload the kitchen and menu, so the server can price food itself |
| `POST /v1/payments` + `Idempotency-Key` | passenger | Pay for a ride, a shared ride or a food order. The body describes the **booking**; the server computes the amount. `201` captured, `200` replay, `402` declined, `409 already_paid` / `key_reused` / `no_mandate` |
| `GET /v1/payments`, `GET /v1/payments/{id}` | payer or payee | Own payments only; anyone else gets `404` |
| `GET /v1/me/balance` | driver, seller | Earned, paid out and available, from the ledger |
| `POST /v1/payouts` + `Idempotency-Key` | driver, seller + password | Pay the balance (or `amount_cents`) to the linked account. `409 insufficient_balance` / `too_small` / `no_bank` |
| `GET /v1/payouts` | driver, seller | Own payouts |

A payment body: `{"kind": "ride", "reference": "R-…", "details": {"pickup": 0, "destination": 1, "comfort": false, "multiplier": 1.0}, "payee_account": "<driver id>"}` (or `"house_payee": "fleet"` for a simulated driver; `"kind": "shared"` with `{"offer", "party"}`; `"kind": "food"` with `{"items": {"dish": quantity}}` and a seller's account or `kitchen-0…2`). There is no amount field: sending one is a `422`.

## Data model

```mermaid
erDiagram
    ACCOUNTS ||--o| DRIVER_PROFILES : "driver"
    ACCOUNTS ||--o| KITCHENS : "seller owns"
    KITCHENS ||--o{ DISHES : lists
    ACCOUNTS ||--o{ SESSIONS : "signed in as"
    ACCOUNTS ||--o{ BANK_ACCOUNTS : "one active"
    ACCOUNTS ||--o{ PAYMENTS : "pays / is paid"
    ACCOUNTS ||--o{ PAYOUTS : receives
    PAYMENTS ||--o{ LEDGER_ENTRIES : "3 lines when captured"
    PAYOUTS ||--o{ LEDGER_ENTRIES : "2 lines when paid"
    ACCOUNTS { uuid id PK
        text role
        text email UK
        bytea password_hash
        int password_iterations }
    SESSIONS { bytea token_hash PK
        timestamptz expires_at
        timestamptz revoked_at }
    BANK_ACCOUNTS { text purpose "debit or payout"
        char last4
        bytea fingerprint "HMAC of the IBAN"
        text provider_token
        text mandate_id }
    PAYMENTS { int amount_cents
        int payee_net_cents
        int platform_fee_cents
        text status
        text idempotency_key }
    PAYOUTS { int amount_cents
        text status }
    LEDGER_ENTRIES { text txn
        text account
        int debit_cents
        int credit_cents }
```

Also `login_failures` (lockout), `outbox` (events written in the same transaction as the change) and `audit_log` (who did what; no passwords, tokens, emails or IBANs).

A captured ride of €8.60 to a registered driver, then that driver's payout:

| txn | account | debit | credit |
|---|---|---|---|
| payment | `bank:clearing` | 860 | |
| payment | `payable:<driver>` | | 731 |
| payment | `revenue:commission` | | 129 |
| payout | `payable:<driver>` | 731 | |
| payout | `bank:clearing` | | 731 |

## What protects the money

| Risk | Control | Where |
|---|---|---|
| Client sends a lower amount, or another account's id | No amount field exists; `payments.quote` recomputes it from the booking; the payer is the session's account; unknown fields are rejected | `app.py` `Strict`, `Service.pay` |
| Reply lost, phone retries | `Idempotency-Key` unique per payer; a repeat returns the first answer; a different body under the same key is `409` | `UNIQUE (payer_id, idempotency_key)` |
| The same booking paid twice | partial unique index on `(payer_id, reference)` for non-declined payments | migration 001 |
| Two payouts race for one balance | `SELECT … FOR UPDATE` on the account row before the balance is read | `Service.payout` |
| Ledger edited after the fact | append-only triggers (no `UPDATE`, `DELETE`, `TRUNCATE`); the API role has no such privilege either | migration 001, `roles.sql` |
| Unbalanced entry | deferred constraint trigger: every transaction's debits must equal its credits at `COMMIT` | `ledger_txn_balanced` |
| Stolen session token | bank changes, payouts and deletion ask for the password again, with the sign-in lockout | `Service.step_up` |
| Database copied | passwords are PBKDF2 hashes (600,000 iterations, upgraded at sign-in); tokens are SHA-256; the IBAN is not stored, only an HMAC fingerprint keyed outside the database | `security.py` |
| SQL injection | every value is a bound parameter; no SQL is built from input | `db.py`, all queries |
| Reading someone else's payment | ownership is part of the `WHERE`; a foreign id is a `404` | `Service.payment` |

## Tests

```bash
cd android-app
python -m pip install -r server/requirements-dev.txt
ATLAS_TEST_DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5432/postgres python -m pytest server/tests
```

59 tests on a real PostgreSQL (each in its own database cloned from a migrated template): registration and validation for the three roles, uniform sign-in failures and lockout, hashed and expiring sessions, hash upgrade, SQL-injection strings, bank linking with step-up, server-side pricing, payee and role checks, idempotent replays, six concurrent requests with one key, declines, the ledger triggers, the least-privilege role, payouts including a four-way race, erasure, a scan of every table for passwords, tokens and IBANs, and the phone's `LocalStore` and `backend.py` syncing to a live server over HTTP. `scripts/connected-acceptance.py` drives the real Kivy screens against a running server. The [server workflow](../../.github/workflows/atlas-server.yml) runs all of this on every push.

## Before real money

- **A licensed payment provider.** Implement `BankProvider` for a PSD2 provider (SEPA Direct Debit or open-banking payment initiation), with strong customer authentication at mandate set-up, webhooks for late failures and refunds (a direct debit can be returned for 8 weeks), and reconciliation of `bank:clearing` against the provider's settlement files. With a real provider, insert the payment as *pending*, commit, then call the provider with the same idempotency key — never hold a database transaction open across a network call.
- **TLS and a gateway.** Terminate HTTPS in front of the API, add per-IP rate limits and request logging there.
- **Identity checks.** SPSV licences, vehicle registrations and food-business numbers are still format-checked only (`driver_profiles.verified` is always `false`); email and phone are not verified.
- **Operations.** Connection pooling, backups with restore drills, monitoring of `outbox` and `audit_log`, key rotation for the pepper, and a data-retention schedule for the money rows.
