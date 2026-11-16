"""HTTP API of the ATLAS Go server: registration and sign-in for passengers, drivers and food sellers,
bank accounts, bank payments, a double-entry ledger and payouts, stored in PostgreSQL.

Run (from android-app/):
    DATABASE_URL=postgresql://atlas_app:...@db/atlas ATLAS_BANK_PEPPER=<32+ random bytes, hex> \\
        python -m uvicorn --factory server.app:from_env --host 0.0.0.0 --port 8080

The validation and money rules are imported from the phone app (atlas_go.accounts, atlas_go.payments),
so the phone and the server cannot disagree. The server never trusts an amount, a role or an account
id sent by the client: amounts are recomputed from the booking, the role comes from the session, and
every row is filtered by the signed-in account.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import logging
import math
import os
import re
import uuid

import psycopg
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from psycopg.types.json import Jsonb
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt

from atlas_go import accounts as acc
from atlas_go import payments as pay
from atlas_go.domain import DISHES

from . import security
from .bank import BankProvider, SandboxBank
from .db import Database

log = logging.getLogger('atlas.server')
MAX_BODY = 64 * 1024
KEY = re.compile(r'^[A-Za-z0-9._:-]{8,80}$')
DISH_ID = re.compile(r'^k\d{1,6}-\d{1,3}$')
UTC = dt.timezone.utc


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str, field: str | None = None, headers: dict | None = None):
        super().__init__(message)
        self.status, self.code, self.message, self.field, self.headers = status, code, message, field, headers or {}

    def response(self) -> JSONResponse:
        error = dict(code=self.code, message=self.message)
        if self.field:
            error['field'] = self.field
        return JSONResponse(dict(error=error), status_code=self.status, headers=self.headers)


def invalid(error: ValueError, field: str | None = None) -> ApiError:
    return ApiError(422, 'invalid', str(error), field)


# ---------------------------------------------------------------------------- request bodies
class Strict(BaseModel):
    """Unknown fields are an error (a client cannot smuggle role=..., amount=... or id=...)."""
    model_config = ConfigDict(extra='forbid', str_max_length=200)


class DriverIn(Strict):
    vehicle: str
    plate: str
    licence: str
    seats: StrictInt


class DishIn(Strict):
    id: str
    name: str
    detail: str
    price: StrictInt
    archived: StrictBool = False


class KitchenIn(Strict):
    name: str
    cuisine: str
    registration: str
    place: StrictInt
    prep: StrictInt
    open: StrictBool = True
    dishes: list[DishIn] = Field(default_factory=list, max_length=30)


class RegisterIn(Strict):
    role: str
    name: str
    email: str
    phone: str
    password: str
    driver: DriverIn | None = None
    kitchen: KitchenIn | None = None


class LoginIn(Strict):
    email: str
    password: str


class PasswordIn(Strict):
    password: str


class BankIn(Strict):
    password: str
    holder: str
    iban: str
    consent: StrictBool = False


class PaymentIn(Strict):
    kind: str
    reference: str = Field(min_length=3, max_length=60)
    details: dict
    payee_account: str | None = None
    house_payee: str | None = None


class PayoutIn(Strict):
    password: str
    amount_cents: StrictInt | None = None


# ---------------------------------------------------------------------------- the service
class Service:
    """Business rules. Every method that takes db runs inside the caller's SQL transaction."""

    def __init__(self, database: Database, pepper: bytes, iterations: int = security.DEFAULT_ITERATIONS,
                 session_hours: int = 720, bank: BankProvider | None = None, clock=None):
        if len(pepper) < 16:
            raise ValueError('ATLAS_BANK_PEPPER must be at least 16 random bytes.')
        if iterations < 1000:
            raise ValueError('PBKDF2 iterations are too low.')
        self.database, self.pepper, self.iterations = database, pepper, iterations
        self.session_hours, self.bank = session_hours, bank or SandboxBank()
        self.clock = clock or (lambda: dt.datetime.now(UTC))

    # ---- helpers
    def audit(self, db, account_id, action: str, **detail) -> None:
        db.execute('INSERT INTO audit_log (at, account_id, action, detail) VALUES (%s, %s, %s, %s)',
                   (self.clock(), account_id, action, Jsonb(detail)))

    def emit(self, db, event_type: str, **body) -> None:
        db.execute('INSERT INTO outbox (event_type, body, created_at) VALUES (%s, %s, %s)',
                   (event_type, Jsonb(body), self.clock()))

    @staticmethod
    def account_view(row: dict) -> dict:
        return dict(id=str(row['id']), role=row['role'], name=row['name'], email=row['email'])

    @staticmethod
    def bank_view(row: dict | None) -> dict | None:
        if row is None:
            return None
        return dict(holder=row['holder'], country=row['country'], last4=row['last4'], purpose=row['purpose'],
                    masked=f"{row['country']}•• •••• {row['last4']}", mandate_id=row['mandate_id'])

    def active_bank(self, db, account_id) -> dict | None:
        return db.execute('SELECT * FROM bank_accounts WHERE account_id = %s AND revoked_at IS NULL',
                          (account_id,)).fetchone()

    # ---- lockout (shared by sign-in and password step-up)
    def check_lock(self, db, email: str) -> None:
        row = db.execute('SELECT locked_until FROM login_failures WHERE email = %s', (email,)).fetchone()
        now = self.clock()
        if row and row['locked_until'] and row['locked_until'] > now:
            seconds = max(1, math.ceil((row['locked_until'] - now).total_seconds()))
            raise ApiError(429, 'locked', f'Too many attempts. Try again in {seconds} seconds.',
                           headers={'Retry-After': str(seconds)})

    def record_failure(self, email: str) -> None:
        """Committed in its own transaction: the request that failed is about to be refused."""
        now = self.clock()
        with self.database.transaction() as db:
            db.execute(
                'INSERT INTO login_failures (email, failures, locked_until) VALUES (%s, 1, NULL) '
                'ON CONFLICT (email) DO UPDATE SET '
                ' failures = CASE WHEN login_failures.failures + 1 >= %s THEN 0 ELSE login_failures.failures + 1 END,'
                ' locked_until = CASE WHEN login_failures.failures + 1 >= %s THEN %s ELSE NULL END',
                (email, acc.MAX_FAILED_LOGINS, acc.MAX_FAILED_LOGINS, now + dt.timedelta(seconds=acc.LOCKOUT_SECONDS)))
            self.audit(db, None, 'login.failed', email_hash=hashlib.sha256(email.encode()).hexdigest()[:16])

    def step_up(self, account: dict, password: str) -> None:
        """Re-check the password for money settings, with the same lockout as sign-in. A stolen
        session token alone cannot change the bank account or trigger a payout."""
        with self.database.transaction() as db:
            self.check_lock(db, account['email'])
        if not security.verify_password(password, account, self.iterations):
            self.record_failure(account['email'])
            raise ApiError(403, 'wrong_password', 'Password is not correct.', 'password')
        with self.database.transaction() as db:
            db.execute('DELETE FROM login_failures WHERE email = %s', (account['email'],))

    # ---- accounts and sessions
    def open_session(self, db, account_id) -> tuple[str, int]:
        token, digest = security.new_token()
        now = self.clock()
        db.execute('INSERT INTO sessions (token_hash, account_id, created_at, expires_at) VALUES (%s, %s, %s, %s)',
                   (digest, account_id, now, now + dt.timedelta(hours=self.session_hours)))
        return token, self.session_hours * 3600

    def authenticate(self, db, request: Request) -> dict:
        scheme, _, token = request.headers.get('authorization', '').partition(' ')
        if scheme.lower() != 'bearer' or not token.strip():
            raise ApiError(401, 'unauthenticated', 'Sign in first.', headers={'WWW-Authenticate': 'Bearer'})
        row = db.execute(
            'SELECT a.*, s.token_hash FROM sessions s JOIN accounts a ON a.id = s.account_id '
            'WHERE s.token_hash = %s AND s.revoked_at IS NULL AND s.expires_at > %s AND a.deleted_at IS NULL',
            (security.token_hash(token.strip()), self.clock())).fetchone()
        if row is None:
            raise ApiError(401, 'unauthenticated', 'Your session has ended. Sign in again.',
                           headers={'WWW-Authenticate': 'Bearer'})
        return row

    @staticmethod
    def require(account: dict, *roles: str) -> None:
        if account['role'] not in roles:
            raise ApiError(403, 'forbidden', 'Your account type cannot do this.')

    def register(self, body: RegisterIn) -> dict:
        try:
            if body.role not in acc.ROLES:
                raise ValueError('Choose passenger, driver or food seller.')
            name, email, phone = acc.clean_name(body.name), acc.clean_email(body.email), acc.clean_phone(body.phone)
            acc.check_password(body.password)
            driver = kitchen = None
            if body.role == 'driver':
                if body.driver is None:
                    raise ValueError('Driver details are required.')
                driver = (acc.clean_name(body.driver.vehicle, 'Vehicle', 3, 40), acc.clean_plate(body.driver.plate),
                          acc.clean_licence(body.driver.licence), acc.parse_int(body.driver.seats, 'Seats', 1, 8))
            if body.role == 'seller':
                if body.kitchen is None:
                    raise ValueError('Kitchen details are required.')
                kitchen = self.clean_kitchen(body.kitchen)
        except ValueError as error:
            raise invalid(error) from None
        salt, digest, iterations = security.hash_password(body.password, self.iterations)
        try:
            with self.database.transaction() as db:
                account = db.execute(
                    'INSERT INTO accounts (role, name, email, phone, password_salt, password_hash, password_iterations,'
                    ' created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING *',
                    (body.role, name, email, phone, salt, digest, iterations, self.clock())).fetchone()
                if driver:
                    db.execute('INSERT INTO driver_profiles (account_id, vehicle, plate, licence, seats) '
                               'VALUES (%s, %s, %s, %s, %s)', (account['id'], *driver))
                if kitchen:
                    self.save_kitchen(db, account['id'], kitchen)
                token, expires = self.open_session(db, account['id'])
                self.audit(db, account['id'], 'account.registered', role=body.role)
                self.emit(db, 'account.registered', account=str(account['id']), role=body.role)
        except psycopg.errors.UniqueViolation as error:
            if 'kitchens' in str(error):
                raise ApiError(409, 'kitchen_taken', 'A kitchen with this name already exists.', 'kitchen') from None
            raise ApiError(409, 'email_taken', 'An account with this email already exists. Sign in instead.',
                           'email') from None
        return dict(account=self.account_view(account), token=token, expires_in=expires)

    def login(self, body: LoginIn) -> dict:
        email = (body.email or '').strip().lower()[:80]
        shaped = bool(acc.EMAIL.match(email))        # anything else cannot be an account: never sent to SQL
        account = None
        if shaped:
            with self.database.transaction() as db:
                self.check_lock(db, email)
                account = db.execute('SELECT * FROM accounts WHERE email = %s AND deleted_at IS NULL', (email,)).fetchone()
        if not security.verify_password(body.password, account, self.iterations):
            if shaped:
                self.record_failure(email)
            # One message for "no such account" and "wrong password": no account enumeration.
            raise ApiError(401, 'bad_credentials', 'Email or password is not correct.')
        with self.database.transaction() as db:
            db.execute('DELETE FROM login_failures WHERE email = %s', (email,))
            if account['password_iterations'] < self.iterations:
                # Upgrade an older, cheaper hash now that we hold the password (hash agility).
                salt, digest, iterations = security.hash_password(body.password, self.iterations)
                db.execute('UPDATE accounts SET password_salt = %s, password_hash = %s, password_iterations = %s '
                           'WHERE id = %s', (salt, digest, iterations, account['id']))
            token, expires = self.open_session(db, account['id'])
            self.audit(db, account['id'], 'login.ok')
        return dict(account=self.account_view(account), token=token, expires_in=expires)

    def delete_account(self, account: dict, password: str) -> None:
        self.step_up(account, password)
        with self.database.transaction() as db:
            db.execute('SELECT id FROM accounts WHERE id = %s FOR UPDATE', (account['id'],))
            if self.balance(db, account['id'])['balance_cents'] > 0:
                raise ApiError(409, 'balance_due', 'Pay out your balance to your bank account first.')
            now, tomb = self.clock(), security.hash_password(uuid.uuid4().hex, 1000)
            # Erase the person; keep the money rows (accounting law) under the now-anonymous id.
            db.execute("UPDATE accounts SET name = 'Deleted user', email = %s, phone = '', password_salt = %s, "
                       'password_hash = %s, password_iterations = %s, deleted_at = %s WHERE id = %s',
                       (f"deleted-{account['id']}@deleted.invalid", tomb[0], tomb[1], tomb[2], now, account['id']))
            db.execute('UPDATE sessions SET revoked_at = %s WHERE account_id = %s AND revoked_at IS NULL',
                       (now, account['id']))
            db.execute("UPDATE bank_accounts SET revoked_at = COALESCE(revoked_at, %s), holder = 'Deleted user', "
                       "provider_token = 'revoked' WHERE account_id = %s", (now, account['id']))
            db.execute("UPDATE driver_profiles SET vehicle = 'removed', plate = 'removed', licence = 'removed' "
                       'WHERE account_id = %s', (account['id'],))
            db.execute("UPDATE kitchens SET open = FALSE, registration = 'REMOVED' WHERE owner_id = %s", (account['id'],))
            self.audit(db, account['id'], 'account.deleted')

    # ---- kitchens (so the server can price a seller's food itself)
    @staticmethod
    def clean_kitchen(body: KitchenIn) -> dict:
        dishes = []
        for dish in body.dishes:
            if not DISH_ID.match(dish.id):
                raise ValueError('Invalid dish id.')
            if not 50 <= dish.price <= 20000:
                raise ValueError('Price must be between €0.50 and €200.00.')
            dishes.append((dish.id, acc.clean_name(dish.name, 'Dish name', 2, 40),
                           acc.clean_name(dish.detail, 'Description', 3, 60), dish.price, dish.archived))
        if len({d[0] for d in dishes}) != len(dishes):
            raise ValueError('Duplicate dish id.')
        return dict(name=acc.clean_name(body.name, 'Kitchen name', 2, 40), cuisine=acc.clean_name(body.cuisine, 'Cuisine', 3, 40),
                    registration=acc.clean_business(body.registration), place=acc.parse_int(body.place, 'Place', 0, 3),
                    prep=acc.parse_int(body.prep, 'Preparation time', 5, 90), open=body.open, dishes=dishes)

    @staticmethod
    def save_kitchen(db, owner_id, kitchen: dict) -> int:
        row = db.execute(
            'INSERT INTO kitchens (owner_id, name, cuisine, registration, place, prep_minutes, open) '
            'VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (owner_id) DO UPDATE SET name = EXCLUDED.name, '
            'cuisine = EXCLUDED.cuisine, registration = EXCLUDED.registration, place = EXCLUDED.place, '
            'prep_minutes = EXCLUDED.prep_minutes, open = EXCLUDED.open RETURNING id',
            (owner_id, kitchen['name'], kitchen['cuisine'], kitchen['registration'], kitchen['place'],
             kitchen['prep'], kitchen['open'])).fetchone()
        for dish in kitchen['dishes']:
            db.execute('INSERT INTO dishes (kitchen_id, dish_id, name, detail, price_cents, archived) '
                       'VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (kitchen_id, dish_id) DO UPDATE SET '
                       'name = EXCLUDED.name, detail = EXCLUDED.detail, price_cents = EXCLUDED.price_cents, '
                       'archived = EXCLUDED.archived', (row['id'], *dish))
        return row['id']

    # ---- bank account
    def link_bank(self, account: dict, body: BankIn) -> dict:
        self.step_up(account, body.password)
        now = self.clock()
        try:
            record = pay.bank_record(account['role'], body.holder, body.iban, body.consent, now.timestamp())
        except ValueError as error:
            raise invalid(error) from None
        iban = pay.clean_iban(body.iban)
        provider = self.bank.tokenise(iban, record['holder'], record['purpose'])     # the IBAN stops here
        with self.database.transaction() as db:
            db.execute('UPDATE bank_accounts SET revoked_at = %s WHERE account_id = %s AND revoked_at IS NULL',
                       (now, account['id']))
            row = db.execute(
                'INSERT INTO bank_accounts (account_id, purpose, holder, country, last4, fingerprint, provider_token,'
                ' mandate_id, mandate_version, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING *',
                (account['id'], record['purpose'], record['holder'], record['country'], record['last4'],
                 security.fingerprint(self.pepper, iban), provider['token'], provider['mandate_id'],
                 pay.MANDATE_VERSION if provider['mandate_id'] else None, now)).fetchone()
            self.audit(db, account['id'], 'bank.linked', purpose=record['purpose'], country=record['country'],
                       last4=record['last4'], mandate=provider['mandate_id'])
        return self.bank_view(row)

    def unlink_bank(self, account: dict, password: str) -> None:
        self.step_up(account, password)
        with self.database.transaction() as db:
            changed = db.execute('UPDATE bank_accounts SET revoked_at = %s WHERE account_id = %s AND revoked_at IS NULL',
                                 (self.clock(), account['id'])).rowcount
            if not changed:
                raise ApiError(404, 'no_bank', 'No bank account is linked.')
            self.audit(db, account['id'], 'bank.unlinked')

    # ---- payments
    @staticmethod
    def payment_view(row: dict, me) -> dict:
        payer = row['payer_id'] == me
        view = dict(id=str(row['id']), kind=row['kind'], reference=row['reference'], status=row['status'],
                    amount_cents=row['amount_cents'], payee_net_cents=row['payee_net_cents'],
                    platform_fee_cents=row['platform_fee_cents'], role='payer' if payer else 'payee',
                    created_at=row['created_at'].isoformat())
        if payer:                                   # the payee never sees the payer's bank details
            view.update(last4=row['last4'], decline_reason=row['decline_reason'])
        return view

    def replay(self, row: dict, request_hash: bytes, me) -> Response:
        """Answer a repeated Idempotency-Key with the first result; refuse a different request under it."""
        if bytes(row['request_hash']) != request_hash:
            raise ApiError(409, 'key_reused', 'This Idempotency-Key was used for a different request.')
        if row['status'] == 'declined':
            return ApiError(402, row['decline_reason'], pay.DECLINES[row['decline_reason']]).response()
        return JSONResponse(dict(payment=self.payment_view(row, me)), status_code=200,
                            headers={'Idempotent-Replay': 'true'})

    def resolve_payee(self, db, body: PaymentIn) -> tuple:
        """-> (payee account id or None, house payee or None, seller menu or None). The client names the
        payee; the server checks that such a driver or kitchen exists and has the right role."""
        if (body.payee_account is None) == (body.house_payee is None):
            raise ApiError(422, 'invalid', 'Name exactly one payee.', 'payee_account')
        if body.house_payee is not None:
            expected = ('fleet',) if body.kind in ('ride', 'shared') else ('kitchen-0', 'kitchen-1', 'kitchen-2')
            if body.house_payee not in expected:
                raise ApiError(422, 'invalid', 'Unknown payee for this kind of payment.', 'house_payee')
            if body.kind == 'food':
                kitchen = int(body.house_payee[-1])
                items = body.details.get('items') if isinstance(body.details.get('items'), dict) else {}
                if any(d not in DISHES or DISHES[d].restaurant != kitchen for d in items):
                    raise ApiError(422, 'invalid', 'A dish in this order is not from that kitchen.', 'details')
            return None, body.house_payee, None
        try:
            payee_id = uuid.UUID(body.payee_account)
        except ValueError:
            raise ApiError(422, 'invalid', 'Invalid payee account.', 'payee_account') from None
        payee = db.execute('SELECT id, role FROM accounts WHERE id = %s AND deleted_at IS NULL', (payee_id,)).fetchone()
        wanted = {'ride': 'driver', 'food': 'seller'}.get(body.kind)
        if payee is None or payee['role'] != wanted:
            raise ApiError(422, 'invalid', 'The payee is not a registered driver or kitchen for this payment.',
                           'payee_account')
        menu = None
        if body.kind == 'food':
            rows = db.execute('SELECT d.dish_id, d.price_cents FROM dishes d JOIN kitchens k ON k.id = d.kitchen_id '
                              'WHERE k.owner_id = %s', (payee_id,)).fetchall()
            menu = {r['dish_id']: r['price_cents'] for r in rows}
        return payee_id, None, menu

    def pay(self, account: dict, body: PaymentIn, key: str | None) -> Response:
        self.require(account, 'passenger')
        if not key or not KEY.match(key):
            raise ApiError(400, 'key_required', 'Send an Idempotency-Key header (8 to 80 letters, digits, . _ : -).')
        me = account['id']
        request_hash = hashlib.sha256(json.dumps(body.model_dump(), sort_keys=True, separators=(',', ':'))
                                      .encode('utf-8')).digest()
        try:
            with self.database.transaction() as db:
                seen = db.execute('SELECT * FROM payments WHERE payer_id = %s AND idempotency_key = %s',
                                  (me, key)).fetchone()
                if seen:
                    return self.replay(seen, request_hash, me)
                bank = self.active_bank(db, me)
                if bank is None or bank['purpose'] != 'debit':
                    raise ApiError(409, 'no_mandate', 'Link a bank account with a Direct Debit mandate first.')
                payee_id, house, menu = self.resolve_payee(db, body)
                try:
                    amount = pay.quote(body.kind, body.details, menu)      # the server's own price
                    parts = pay.split(body.kind, amount)
                except ValueError as error:
                    raise invalid(error, 'details') from None
                outcome = self.bank.debit(bank['provider_token'], bank['last4'], amount, body.reference)
                declined = outcome != 'approved'
                row = db.execute(
                    'INSERT INTO payments (payer_id, payee_id, house_payee, kind, reference, amount_cents, '
                    'payee_net_cents, platform_fee_cents, status, decline_reason, last4, idempotency_key, request_hash,'
                    ' created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) '
                    'ON CONFLICT (payer_id, idempotency_key) DO NOTHING RETURNING *',
                    (me, payee_id, house, body.kind, body.reference, amount, parts['payee_net'], parts['platform_fee'],
                     'declined' if declined else 'captured', outcome if declined else None, bank['last4'], key,
                     request_hash, self.clock())).fetchone()
                if row is None:      # the same key arrived twice at once; the other request won the insert
                    seen = db.execute('SELECT * FROM payments WHERE payer_id = %s AND idempotency_key = %s',
                                      (me, key)).fetchone()
                    return self.replay(seen, request_hash, me)
                if declined:
                    self.audit(db, me, 'payment.declined', payment=str(row['id']), reason=outcome, amount=amount)
                    return ApiError(402, outcome, pay.DECLINES[outcome]).response()      # the row is committed
                record = dict(id=str(row['id']), status='captured', amount=amount, payee=str(payee_id or house), **parts)
                self.post(db, pay.entries([record]))
                self.audit(db, me, 'payment.captured', payment=str(row['id']), amount=amount, kind=body.kind)
                self.emit(db, 'payment.captured', payment=str(row['id']), amount_cents=amount,
                          payee=str(payee_id or house), reference=body.reference)
                return JSONResponse(dict(payment=self.payment_view(row, me)), status_code=201)
        except psycopg.errors.UniqueViolation:
            raise ApiError(409, 'already_paid', 'This booking has already been paid.') from None

    def post(self, db, lines) -> None:
        """Write ledger lines. The deferred constraint trigger refuses the COMMIT if they do not balance."""
        now = self.clock()
        for txn, account, debit, credit in lines:
            db.execute('INSERT INTO ledger_entries (txn, account, debit_cents, credit_cents, created_at) '
                       'VALUES (%s, %s, %s, %s, %s)', (txn, account, debit, credit, now))

    def payments(self, db, me) -> list[dict]:
        rows = db.execute('SELECT * FROM payments WHERE payer_id = %s OR payee_id = %s ORDER BY created_at DESC, id '
                          'LIMIT 50', (me, me)).fetchall()
        return [self.payment_view(r, me) for r in rows]

    def payment(self, db, me, payment_id: str) -> dict:
        try:
            wanted = uuid.UUID(payment_id)
        except ValueError:
            raise ApiError(404, 'not_found', 'Payment not found.') from None
        # Ownership is part of the WHERE clause: someone else's payment is indistinguishable from none.
        row = db.execute('SELECT * FROM payments WHERE id = %s AND (payer_id = %s OR payee_id = %s)',
                         (wanted, me, me)).fetchone()
        if row is None:
            raise ApiError(404, 'not_found', 'Payment not found.')
        return self.payment_view(row, me)

    # ---- balance and payouts
    def balance(self, db, me) -> dict:
        row = db.execute('SELECT COALESCE(SUM(credit_cents), 0) AS earned, '
                         'COALESCE(SUM(credit_cents) - SUM(debit_cents), 0) AS balance '
                         'FROM ledger_entries WHERE account = %s', (pay.payable(str(me)),)).fetchone()
        paid = db.execute("SELECT COALESCE(SUM(amount_cents), 0) AS paid FROM payouts WHERE account_id = %s "
                          "AND status = 'paid'", (me,)).fetchone()['paid']
        return dict(balance_cents=int(row['balance']), earned_cents=int(row['earned']), paid_out_cents=int(paid))

    @staticmethod
    def payout_view(row: dict) -> dict:
        return dict(id=str(row['id']), amount_cents=row['amount_cents'], status=row['status'], last4=row['last4'],
                    created_at=row['created_at'].isoformat())

    def payout(self, account: dict, body: PayoutIn, key: str | None) -> Response:
        self.require(account, 'driver', 'seller')
        if not key or not KEY.match(key):
            raise ApiError(400, 'key_required', 'Send an Idempotency-Key header (8 to 80 letters, digits, . _ : -).')
        self.step_up(account, body.password)
        me = account['id']
        with self.database.transaction() as db:
            # Row lock: two payouts for one account run one after the other, so the balance check
            # and the debit cannot interleave (no double spend).
            db.execute('SELECT id FROM accounts WHERE id = %s FOR UPDATE', (me,))
            seen = db.execute('SELECT * FROM payouts WHERE account_id = %s AND idempotency_key = %s', (me, key)).fetchone()
            if seen:
                return JSONResponse(dict(payout=self.payout_view(seen)), status_code=200,
                                    headers={'Idempotent-Replay': 'true'})
            bank = self.active_bank(db, me)
            if bank is None or bank['purpose'] != 'payout':
                raise ApiError(409, 'no_bank', 'Link the bank account you want to be paid to first.')
            available = self.balance(db, me)['balance_cents']
            amount = available if body.amount_cents is None else body.amount_cents
            if amount < pay.MIN_PAYOUT:
                raise ApiError(409, 'too_small', 'You need at least €1.00 to pay out.')
            if amount > available:
                raise ApiError(409, 'insufficient_balance', 'Your balance on the server is lower than this payout.')
            outcome = self.bank.credit(bank['provider_token'], bank['last4'], amount, key)
            status = 'paid' if outcome == 'approved' else 'failed'
            row = db.execute('INSERT INTO payouts (account_id, amount_cents, status, last4, idempotency_key, created_at) '
                             'VALUES (%s, %s, %s, %s, %s, %s) RETURNING *',
                             (me, amount, status, bank['last4'], key, self.clock())).fetchone()
            if status == 'paid':
                self.post(db, pay.entries([], [dict(id=str(row['id']), account=str(me), amount=amount, status='paid')]))
                self.emit(db, 'payout.paid', payout=str(row['id']), account=str(me), amount_cents=amount)
            self.audit(db, me, 'payout.' + status, payout=str(row['id']), amount=amount)
            return JSONResponse(dict(payout=self.payout_view(row)), status_code=201)

    def payouts(self, db, me) -> list[dict]:
        rows = db.execute('SELECT * FROM payouts WHERE account_id = %s ORDER BY created_at DESC, id LIMIT 50',
                          (me,)).fetchall()
        return [self.payout_view(r) for r in rows]


# ---------------------------------------------------------------------------- HTTP wiring
def create_app(dsn: str, *, pepper: bytes, iterations: int = security.DEFAULT_ITERATIONS, session_hours: int = 720,
               bank: BankProvider | None = None, clock=None, migrate: bool = True) -> FastAPI:
    database = Database(dsn)
    if migrate:
        database.migrate()
    service = Service(database, pepper, iterations, session_hours, bank, clock)
    app = FastAPI(title='ATLAS Go server', version='1.5.0')
    app.state.service = service

    @app.middleware('http')
    async def guard(request: Request, call_next):
        length = request.headers.get('content-length', '0')
        if not length.isdigit() or int(length) > MAX_BODY:
            return ApiError(413, 'too_large', 'Request body is too large.').response()
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'          # tokens and balances must not be cached
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response

    @app.exception_handler(ApiError)
    async def api_error(_request, error: ApiError):
        return error.response()

    @app.exception_handler(RequestValidationError)
    async def bad_request(_request, error: RequestValidationError):
        first = error.errors()[0]
        field = '.'.join(str(part) for part in first.get('loc', ())[1:]) or None
        # The message names the field and the rule, never the value that was sent.
        return ApiError(422, 'invalid', f"Check the request: {first.get('msg', 'invalid value')}.", field).response()

    @app.exception_handler(psycopg.DataError)
    async def bad_data(_request, _error):
        # Text PostgreSQL cannot store (for example a NUL byte) is the client's mistake, not a crash.
        return ApiError(422, 'invalid', 'Check the request: unsupported characters.').response()

    @app.exception_handler(Exception)
    async def crash(_request, error: Exception):
        reference = uuid.uuid4().hex[:12]
        log.exception('unhandled error %s', reference, exc_info=error)
        return ApiError(500, 'server', f'Something went wrong. Reference {reference}.').response()

    def signed_in(request: Request) -> dict:
        with database.transaction() as db:
            return service.authenticate(db, request)

    @app.get('/healthz')
    def health():
        with database.transaction() as db:
            version = db.execute('SELECT COALESCE(MAX(version), 0) AS v FROM schema_version').fetchone()['v']
        return dict(status='ok', schema=version)

    @app.post('/v1/accounts', status_code=201)
    def register(body: RegisterIn):
        return service.register(body)

    @app.post('/v1/sessions', status_code=201)
    def login(body: LoginIn):
        return service.login(body)

    @app.delete('/v1/sessions/current', status_code=204)
    def logout(request: Request):
        account = signed_in(request)
        with database.transaction() as db:
            db.execute('UPDATE sessions SET revoked_at = %s WHERE token_hash = %s', (service.clock(), account['token_hash']))
            service.audit(db, account['id'], 'logout')
        return Response(status_code=204)

    @app.get('/v1/me')
    def me(request: Request):
        account = signed_in(request)
        with database.transaction() as db:
            return dict(account=service.account_view(account), bank=service.bank_view(service.active_bank(db, account['id'])))

    @app.delete('/v1/accounts/me', status_code=204)
    def delete_me(request: Request, body: PasswordIn):
        service.delete_account(signed_in(request), body.password)
        return Response(status_code=204)

    @app.put('/v1/me/bank')
    def link_bank(request: Request, body: BankIn):
        return dict(bank=service.link_bank(signed_in(request), body))

    @app.delete('/v1/me/bank', status_code=204)
    def unlink_bank(request: Request, body: PasswordIn):
        service.unlink_bank(signed_in(request), body.password)
        return Response(status_code=204)

    @app.put('/v1/seller/kitchen')
    def put_kitchen(request: Request, body: KitchenIn):
        account = signed_in(request)
        service.require(account, 'seller')
        try:
            kitchen = service.clean_kitchen(body)
        except ValueError as error:
            raise invalid(error) from None
        try:
            with database.transaction() as db:
                kitchen_id = service.save_kitchen(db, account['id'], kitchen)
        except psycopg.errors.UniqueViolation:
            raise ApiError(409, 'kitchen_taken', 'A kitchen with this name already exists.', 'name') from None
        return dict(kitchen=dict(id=kitchen_id, dishes=len(kitchen['dishes'])))

    @app.post('/v1/payments')
    def create_payment(request: Request, body: PaymentIn):
        return service.pay(signed_in(request), body, request.headers.get('idempotency-key'))

    @app.get('/v1/payments')
    def list_payments(request: Request):
        account = signed_in(request)
        with database.transaction() as db:
            return dict(payments=service.payments(db, account['id']))

    @app.get('/v1/payments/{payment_id}')
    def get_payment(request: Request, payment_id: str):
        account = signed_in(request)
        with database.transaction() as db:
            return dict(payment=service.payment(db, account['id'], payment_id))

    @app.get('/v1/me/balance')
    def balance(request: Request):
        account = signed_in(request)
        service.require(account, 'driver', 'seller')
        with database.transaction() as db:
            return service.balance(db, account['id'])

    @app.post('/v1/payouts')
    def create_payout(request: Request, body: PayoutIn):
        return service.payout(signed_in(request), body, request.headers.get('idempotency-key'))

    @app.get('/v1/payouts')
    def list_payouts(request: Request):
        account = signed_in(request)
        service.require(account, 'driver', 'seller')
        with database.transaction() as db:
            return dict(payouts=service.payouts(db, account['id']))

    return app


def from_env() -> FastAPI:
    """uvicorn --factory server.app:from_env. Refuses to start without its two secrets."""
    dsn, pepper = os.environ.get('DATABASE_URL', ''), os.environ.get('ATLAS_BANK_PEPPER', '')
    if not re.fullmatch(r'(?:[0-9a-fA-F]{2}){16,}', pepper):
        raise RuntimeError('Set ATLAS_BANK_PEPPER to at least 16 random bytes in hex (python -c "import secrets; '
                           'print(secrets.token_hex(32))").')
    return create_app(dsn, pepper=bytes.fromhex(pepper),
                      iterations=int(os.environ.get('ATLAS_PBKDF2_ITERATIONS', security.DEFAULT_ITERATIONS)),
                      session_hours=int(os.environ.get('ATLAS_SESSION_HOURS', '720')),
                      migrate=os.environ.get('ATLAS_MIGRATE', '1') == '1')
