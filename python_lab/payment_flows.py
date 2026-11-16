"""Part III, labs A13-A18: registration, bank payments and payouts on the real ATLAS Go 1.5.0 code.

Each lab drives the app's own modules (android-app/atlas_go: LocalStore, payments, backend) and a
server through the same HTTP client the phone uses.

    python python_lab/payment_flows.py --all          # every lab
    python python_lab/payment_flows.py --lab 17       # one lab
    python -m pytest -q python_lab/tests/test_payment_flows.py

Two back ends, chosen automatically:
  * the REAL ATLAS Go server (android-app/server, FastAPI + PostgreSQL) when ATLAS_TEST_DATABASE_URL
    names a PostgreSQL server and fastapi + psycopg are installed, for example
        ATLAS_TEST_DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5432/postgres
  * otherwise DeskServer, a small in-memory stand-in defined below. It follows the same contract for
    the calls these labs make, and tests/test_payment_flows.py checks it against the real server.
Nothing here contacts a bank: both use the sandbox rules in atlas_go/payments.py.
"""
from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
import tempfile
import threading
import uuid
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'android-app'))

from atlas_go import accounts as acc              # noqa: E402
from atlas_go import backend                      # noqa: E402
from atlas_go import payments as pay              # noqa: E402
from atlas_go.domain import DISHES                # noqa: E402
from atlas_go.store import LocalStore             # noqa: E402

T0 = 1_780_000_000.0                               # a fixed clock, so every run prints the same thing
GOOD, NO_FUNDS, CLOSED = (pay.SANDBOX_IBANS[k] for k in ('approved', 'insufficient_funds', 'account_closed'))
URL = 'https://atlas.lab.example'                  # never resolved: requests go to an in-process session


# ---------------------------------------------------------------------------- the stand-in server
class Reply:
    def __init__(self, status: int, data: dict | None = None, headers: dict | None = None):
        self.status_code, self._data, self.headers = status, data or {}, headers or {}
        self.content = json.dumps(self._data).encode()

    def json(self):
        return self._data


def problem(status: int, code: str, message: str) -> Reply:
    return Reply(status, dict(error=dict(code=code, message=message)))


class DeskServer:
    """In-memory stand-in for the ATLAS Go server: same routes, same status codes and the same
    payments.quote / payments.split rules, with dictionaries instead of PostgreSQL. A teaching double,
    not a second product: it has no lockout, no expiry and no persistence."""
    name = 'in-memory stand-in (DeskServer)'

    def __init__(self):
        self.accounts, self.tokens, self.banks, self.menus = {}, {}, {}, {}
        self.payments, self.by_key, self.payouts, self.lines = [], {}, {}, []
        self.lock = threading.Lock()

    def request(self, method, url, json=None, headers=None, timeout=None, allow_redirects=None):
        path, body, headers = urlsplit(url).path, json or {}, headers or {}
        token = headers.get('Authorization', '')[7:]
        me = self.accounts.get(self.tokens.get(token))
        key = headers.get('Idempotency-Key')
        with self.lock:                            # one request at a time, like a row lock
            if (method, path) == ('POST', '/v1/accounts'):
                return self.register(body)
            if (method, path) == ('POST', '/v1/sessions'):
                found = next((a for a in self.accounts.values() if a['email'] == body.get('email', '').lower()), None)
                if not found or not acc.verify_password(body.get('password', ''), found['password']):
                    return problem(401, 'bad_credentials', 'Email or password is not correct.')
                return self.session(found, 201)
            if me is None:
                return problem(401, 'unauthenticated', 'Sign in first.')
            if (method, path) == ('PUT', '/v1/me/bank'):
                return self.link_bank(me, body)
            if (method, path) == ('PUT', '/v1/seller/kitchen'):
                self.menus[me['id']] = {d['id']: d['price'] for d in body.get('dishes', [])}
                return Reply(200, dict(kitchen=dict(dishes=len(body.get('dishes', [])))))
            if (method, path) == ('POST', '/v1/payments'):
                return self.pay(me, body, key)
            if (method, path) == ('GET', '/v1/payments'):
                return Reply(200, dict(payments=[p for p in self.payments if me['id'] in (p['payer'], p['payee'])]))
            if (method, path) == ('GET', '/v1/me/balance'):
                return Reply(200, self.balance(me['id']))
            if (method, path) == ('POST', '/v1/payouts'):
                return self.payout(me, body, key)
        return problem(404, 'not_found', 'Not found.')

    def session(self, account, status):
        token = secrets.token_urlsafe(16)
        self.tokens[token] = account['id']
        return Reply(status, dict(account={k: account[k] for k in ('id', 'role', 'name', 'email')}, token=token))

    def register(self, body):
        try:
            email = acc.clean_email(body.get('email', ''))
            acc.clean_name(body.get('name', '')), acc.clean_phone(body.get('phone', ''))
            acc.check_password(body.get('password', ''))
            if body.get('role') not in acc.ROLES or set(body) - {'role', 'name', 'email', 'phone', 'password', 'driver', 'kitchen'}:
                raise ValueError('Unknown role or field.')
        except ValueError as error:
            return problem(422, 'invalid', str(error))
        if any(a['email'] == email for a in self.accounts.values()):
            return problem(409, 'email_taken', 'An account with this email already exists. Sign in instead.')
        account = dict(id=str(uuid.uuid4()), role=body['role'], name=body['name'], email=email,
                       password=acc.hash_password(body['password'], iterations=1000))
        self.accounts[account['id']] = account
        if body.get('kitchen'):
            self.menus[account['id']] = {d['id']: d['price'] for d in body['kitchen'].get('dishes', [])}
        return self.session(account, 201)

    def link_bank(self, me, body):
        if not acc.verify_password(body.get('password', ''), me['password']):
            return problem(403, 'wrong_password', 'Password is not correct.')
        try:
            record = pay.bank_record(me['role'], body.get('holder', ''), body.get('iban', ''), body.get('consent', False), T0)
        except ValueError as error:
            return problem(422, 'invalid', str(error))
        self.banks[me['id']] = record                    # like the real server: no IBAN in the record
        return Reply(200, dict(bank=dict(last4=record['last4'], purpose=record['purpose'],
                                         mandate_id=record.get('mandate', {}).get('id'))))

    def pay(self, me, body, key):
        if me['role'] != 'passenger':
            return problem(403, 'forbidden', 'Your account type cannot do this.')
        if set(body) - {'kind', 'reference', 'details', 'payee_account', 'house_payee'}:
            return problem(422, 'invalid', 'Check the request: Extra inputs are not permitted.')
        fingerprint = json.dumps(body, sort_keys=True)
        if (me['id'], key) in self.by_key:               # the same key again: the first answer, nothing new
            first = self.by_key[(me['id'], key)]
            if first['fingerprint'] != fingerprint:
                return problem(409, 'key_reused', 'This Idempotency-Key was used for a different request.')
            return Reply(200, dict(payment=first['payment']), {'Idempotent-Replay': 'true'})
        bank = self.banks.get(me['id'])
        if not bank or bank['purpose'] != 'debit':
            return problem(409, 'no_mandate', 'Link a bank account with a Direct Debit mandate first.')
        payee, house = body.get('payee_account'), body.get('house_payee')
        try:
            if (payee is None) == (house is None):
                raise ValueError('Name exactly one payee.')
            if payee is not None and self.accounts.get(payee, {}).get('role') != {'ride': 'driver', 'food': 'seller'}.get(body.get('kind')):
                raise ValueError('The payee is not a registered driver or kitchen for this payment.')
            items = (body.get('details') or {}).get('items') or {}
            if house and body.get('kind') == 'food' and any(d not in DISHES or DISHES[d].restaurant != int(house[-1]) for d in items):
                raise ValueError('A dish in this order is not from that kitchen.')
            amount = pay.quote(body.get('kind'), body.get('details'), self.menus.get(payee) if payee else None)
            parts = pay.split(body['kind'], amount)
        except (ValueError, KeyError, TypeError) as error:
            return problem(422, 'invalid', str(error))
        if any(p['payer'] == me['id'] and p['reference'] == body['reference'] for p in self.payments):
            return problem(409, 'already_paid', 'This booking has already been paid.')
        outcome = pay.sandbox_outcome(bank['last4'], amount)
        if outcome != 'approved':
            return problem(402, outcome, pay.DECLINES[outcome])
        payment = dict(id=str(uuid.uuid4()), kind=body['kind'], reference=body['reference'], status='captured',
                       amount_cents=amount, payee_net_cents=parts['payee_net'], platform_fee_cents=parts['platform_fee'],
                       payer=me['id'], payee=payee or house)
        self.payments.append(payment)
        self.by_key[(me['id'], key)] = dict(fingerprint=fingerprint, payment=payment)
        self.lines += pay.entries([dict(id=payment['id'], status='captured', amount=amount, payee=payee or house, **parts)])
        return Reply(201, dict(payment=payment))

    def balance(self, account_id):
        earned = sum(c for _t, a, _d, c in self.lines if a == pay.payable(account_id))
        return dict(balance_cents=pay.balance(self.lines, pay.payable(account_id)), earned_cents=earned,
                    paid_out_cents=sum(o['amount_cents'] for o in self.payouts.values() if o['account'] == account_id))

    def payout(self, me, body, key):
        if me['role'] not in ('driver', 'seller'):
            return problem(403, 'forbidden', 'Your account type cannot do this.')
        if not acc.verify_password(body.get('password', ''), me['password']):
            return problem(403, 'wrong_password', 'Password is not correct.')
        if (me['id'], key) in self.payouts:
            return Reply(200, dict(payout=self.payouts[(me['id'], key)]), {'Idempotent-Replay': 'true'})
        if me['id'] not in self.banks:
            return problem(409, 'no_bank', 'Link the bank account you want to be paid to first.')
        available = self.balance(me['id'])['balance_cents']
        amount = available if body.get('amount_cents') is None else body['amount_cents']
        if amount < pay.MIN_PAYOUT:
            return problem(409, 'too_small', 'You need at least €1.00 to pay out.')
        if amount > available:
            return problem(409, 'insufficient_balance', 'Your balance on the server is lower than this payout.')
        payout = dict(id=str(uuid.uuid4()), account=me['id'], amount_cents=amount, status='paid', last4=self.banks[me['id']]['last4'])
        self.payouts[(me['id'], key)] = payout
        self.lines += pay.entries([], [dict(id=payout['id'], account=me['id'], amount=amount, status='paid')])
        return Reply(201, dict(payout=payout))

    def count(self, what: str) -> int:
        return len(self.payments) if what == 'payments' else len(self.lines)


# ---------------------------------------------------------------------------- the real server, in process
class RealServer:
    """The real FastAPI app on a fresh PostgreSQL database, reached without a network port."""
    name = 'ATLAS Go server on PostgreSQL'

    def __init__(self, admin_dsn: str):
        import psycopg
        from fastapi.testclient import TestClient
        from server.app import create_app
        self.psycopg, self.admin, self.database = psycopg, admin_dsn, f'atlas_lab_{uuid.uuid4().hex[:12]}'
        with psycopg.connect(admin_dsn, autocommit=True) as db:
            db.execute(f"CREATE DATABASE {self.database} ENCODING 'UTF8' TEMPLATE template0")
        info = psycopg.conninfo.conninfo_to_dict(admin_dsn)
        auth = info.get('user', '') + (':' + info['password'] if info.get('password') else '')
        self.dsn = f"postgresql://{auth}@{info.get('host', '127.0.0.1')}:{info.get('port', 5432)}/{self.database}"
        self.client = TestClient(create_app(self.dsn, pepper=bytes(range(32)), iterations=1000))

    def request(self, method, url, json=None, headers=None, timeout=None, allow_redirects=None):
        return self.client.request(method, urlsplit(url).path, json=json, headers=headers)

    def sql(self, query: str, *params):
        with self.psycopg.connect(self.dsn) as db:
            cursor = db.execute(query, params or None)
            return cursor.fetchall() if cursor.description else []

    def count(self, what: str) -> int:
        return self.sql(f"SELECT count(*) FROM {'payments' if what == 'payments' else 'ledger_entries'}")[0][0]

    def close(self):
        self.client.close()
        with self.psycopg.connect(self.admin, autocommit=True) as db:
            db.execute(f'DROP DATABASE IF EXISTS {self.database} WITH (FORCE)')


class Lossy:
    """A network that delivers the request and then loses the reply, `lose` times."""

    def __init__(self, inner, lose: int):
        self.inner, self.lose, self.sent = inner, lose, 0

    def request(self, method, url, **kwargs):
        reply = self.inner.request(method, url, **kwargs)
        if method == 'POST':
            self.sent += 1
            if self.lose > 0:
                self.lose -= 1
                raise ConnectionError('reply lost on the way back')
        return reply


@contextmanager
def a_server(force_stand_in: bool = False):
    dsn = os.environ.get('ATLAS_TEST_DATABASE_URL', '')
    real = None
    if dsn and not force_stand_in:
        try:
            real = RealServer(dsn)
        except ImportError:                          # fastapi or psycopg not installed
            real = None
    try:
        yield real or DeskServer()
    finally:
        if real:
            real.close()


# ---------------------------------------------------------------------------- helpers
@contextmanager
def a_phone():
    with tempfile.TemporaryDirectory() as folder:
        store = LocalStore(Path(folder) / 'state.json')
        store.set_server(URL)
        yield store


def join(store, client, role, name, email, password, **profile):
    """Register on the phone, then connect the account to the server (as the app does)."""
    store.logout()
    store.register(role, name, email, '085 111 2233', password, **profile)
    reply = client.connect(store.user, password, store.kitchen_of(store.user))
    store.connect(reply['account']['id'], reply['token'])
    return store.user


def link(store, client, password, holder, iban, consent=False):
    """Server first, then the phone: the order the app uses for a connected account."""
    bank = client.link_bank(store.user['server']['token'], password, holder, iban, consent)
    return store.link_bank(password, holder, iban, consent, now=T0, mandate_id=bank.get('mandate_id'))


def ride(store, driver_id=None):
    """Book a ride by bank and take it to 'completed', which captures the payment."""
    passenger = store.session
    store.book(0, 1, driver='Siobhan' if driver_id else None, driver_id=driver_id, now=T0, pay_by_bank=True)
    payment = store.payment(store.ride['payment'])
    if driver_id:
        store.session = driver_id
        store.driver_respond(True, now=T0)
        for _ in range(3):
            store.driver_advance(now=T0)
        store.session = passenger
    else:
        for _ in range(3):
            store.advance_ride(now=T0)
    return payment


def attempt(action) -> str:
    try:
        action()
        return 'accepted'
    except backend.ServerError as error:
        return f'{error.status} {error.code}'
    except ValueError as error:
        return 'refused: ' + str(error)[:58]


def table(title: str, rows: list[tuple]) -> None:
    print(f'\n{title}')
    widths = [max(len(str(r[i])) for r in rows) for i in range(len(rows[0]))]
    for n, r in enumerate(rows):
        print('  ' + '  '.join(str(c).ljust(w) for c, w in zip(r, widths)))
        if n == 0:
            print('  ' + '  '.join('-' * w for w in widths))


# ---------------------------------------------------------------------------- A13
def lab13(force_stand_in: bool = False) -> dict:
    """A13 - Registration: form -> validation -> hash -> phone file -> POST /v1/accounts -> server row -> token."""
    with a_server(force_stand_in) as server, a_phone() as store:
        client = backend.Backend(URL, session=server)
        rows = [('input', 'phone (LocalStore.register)', 'server (POST /v1/accounts)')]
        cases = [('valid passenger', dict(email='aoife@atlas.ie')), ('email without @', dict(email='aoife.atlas.ie')),
                 ('password "password"', dict(password='password')), ('name "A"', dict(name='A')),
                 ('unknown role "admin"', dict(role='admin'))]
        for label, change in cases:
            form = dict(dict(role='passenger', name='Aoife Rider', email='x@atlas.ie', phone='0851112233', password='ride2026x'), **change)
            on_phone = attempt(lambda: (store.logout(), store.register(form['role'], form['name'], form['email'], form['phone'], form['password'])))
            on_server = attempt(lambda: client.call('POST', '/v1/accounts', dict(form, email='srv-' + form['email'])))
            rows.append((label, on_phone, on_server))
        table('A13  The same form, checked on the phone and again on the server', rows)
        user = store.account(store.session) or store.accounts[0]
        stored = sorted(k for k in user if k in ('salt', 'hash', 'iterations', 'password'))
        store.session = user['id']
        reply = client.connect(user, 'ride2026x')
        store.connect(reply['account']['id'], reply['token'])
        second = client.connect(user, 'ride2026x')                       # the email exists: this is a sign-in
        takeover = attempt(lambda: client.connect(dict(user), 'someone-else-1'))
        print(f"\n  phone record keeps {stored}; the password itself is not saved")
        print(f"  connect -> server account {reply['account']['id'][:8]}…, a session token of {len(reply['token'])} characters")
        print(f"  connect again -> same account: {second['account']['id'] == reply['account']['id']}, new token: {second['token'] != reply['token']}")
        print(f"  same email, wrong password -> {takeover}")
        assert rows[1][1] == rows[1][2] == 'accepted' and all(r[1] != 'accepted' and r[2] != 'accepted' for r in rows[2:])
        assert stored == ['hash', 'iterations', 'salt'] and takeover.startswith('401')
        return dict(server=server.name, rows=rows, same_account=second['account']['id'] == reply['account']['id'])


# ---------------------------------------------------------------------------- A14
def lab14(force_stand_in: bool = False) -> dict:
    """A14 - Linking a bank account: IBAN check digits, the mandate, and the password asked again."""
    with a_server(force_stand_in) as server, a_phone() as store:
        client = backend.Backend(URL, session=server)
        user = join(store, client, 'passenger', 'Aoife Rider', 'aoife@atlas.ie', 'ride2026x')
        token = user['server']['token']
        cases = [('one digit mistyped', 'ride2026x', GOOD[:-1] + '9', True), ('two digits swapped', 'ride2026x', GOOD[:8] + GOOD[9] + GOOD[8] + GOOD[10:], True),
                 ('not a SEPA country', 'ride2026x', 'US29AIBK93115212345678', True), ('mandate not ticked', 'ride2026x', GOOD, False),
                 ('wrong password', 'guess12345', GOOD, True), ('all correct', 'ride2026x', GOOD, True)]
        rows = [('attempt', 'phone', 'server')]
        for label, password, iban, consent in cases[:-1]:
            rows.append((label, attempt(lambda: store.link_bank(password, 'Aoife Rider', iban, consent, now=T0)),
                         attempt(lambda: client.link_bank(token, password, 'Aoife Rider', iban, consent))))
        bank = link(store, client, 'ride2026x', 'Aoife Rider', GOOD, True)
        rows.append(('all correct', 'accepted', 'accepted'))
        table('A14  Who refuses a bad bank link?', rows)
        on_disk = store.path.read_text(encoding='utf-8')
        print(f"\n  saved on the phone: {bank['masked']}, holder {bank['holder']}, mandate {bank['mandate']['id']}")
        print(f"  full IBAN in state.json: {GOOD in on_disk or GOOD[4:] in on_disk}")
        database = None
        if isinstance(server, RealServer):
            stored = server.sql('SELECT holder, country, last4, purpose, mandate_id IS NOT NULL FROM bank_accounts')
            dump = str(server.sql('SELECT * FROM bank_accounts')) + str(server.sql('SELECT * FROM audit_log'))
            try:
                server.sql("UPDATE bank_accounts SET mandate_id = NULL")       # a debit account must have a mandate
                database = 'accepted'
            except server.psycopg.errors.CheckViolation:
                database = 'CHECK constraint refused it'
            print(f"  PostgreSQL row: {stored[0]}; IBAN anywhere in bank_accounts or audit_log: {GOOD[4:] in dump}")
            print(f"  third layer - removing the mandate with raw SQL: {database}")
            assert GOOD[4:] not in dump and database.startswith('CHECK')
        assert all(r[1] != 'accepted' and r[2] != 'accepted' for r in rows[1:-1]) and GOOD[4:] not in on_disk
        return dict(server=server.name, rows=rows, database=database)


# ---------------------------------------------------------------------------- A15
def lab15(force_stand_in: bool = False) -> dict:
    """A15 - One payment's life on the phone: authorised, then captured or voided; a decline books nothing."""
    with a_phone() as store:
        store.server_url = ''
        store.register('passenger', 'Aoife Rider', 'aoife@atlas.ie', '0851112233', 'ride2026x')
        store.link_bank('ride2026x', 'Aoife Rider', GOOD, True, now=T0)
        rows = [('step', 'ride', 'payment', 'ledger lines', 'seats left in pool-1')]
        seats = lambda: store.offers[0].seats
        snap = lambda step, p: rows.append((step, 'active' if store.ride else 'none', p['status'] if p else '-', len(pay.entries(store.payments)), seats()))
        store.book(0, 1, now=T0, pay_by_bank=True)
        first = store.payment(store.ride['payment'])
        snap('book a ride by bank', first)
        store.advance_ride(cancel=True, now=T0)
        snap('cancel it', first)
        store.book(0, 1, offer_id='pool-1', party=2, now=T0, pay_by_bank=True)
        second = store.payment(store.ride['payment'])
        snap('book 2 shared seats', second)
        for _ in range(4):
            store.advance_ride(now=T0)
        snap('ride completed', second)
        store.link_bank('ride2026x', 'Aoife Rider', NO_FUNDS, True, now=T0)
        declined = attempt(lambda: store.book(0, 1, offer_id='pool-1', party=1, now=T0, pay_by_bank=True))
        snap('book with an empty account', None)
        table('A15  Booking and payment move together', rows)
        lines = pay.entries(store.payments)
        table('  ledger after one captured payment of ' + f"€{second['amount'] / 100:.2f}", [('account', 'debit', 'credit')] + [(a, d or '', c or '') for _t, a, d, c in lines])
        illegal = attempt(lambda: pay.move(second, 'voided', T0))
        print(f"\n  declined booking -> {declined}")
        print(f"  void a captured payment -> {illegal}")
        assert [r[2] for r in rows[1:]] == ['authorised', 'voided', 'authorised', 'captured', '-'] and pay.balanced(lines)
        assert rows[-1][4] == rows[-2][4] and store.ride is None and len(store.payments) == 2
        return dict(rows=rows, lines=lines)


# ---------------------------------------------------------------------------- A16
def lab16(force_stand_in: bool = False) -> dict:
    """A16 - The server sets the price: the phone sends the booking, never the amount."""
    with a_server(force_stand_in) as server, a_phone() as store:
        client = backend.Backend(URL, session=server)
        user = join(store, client, 'passenger', 'Aoife Rider', 'aoife@atlas.ie', 'ride2026x')
        link(store, client, 'ride2026x', 'Aoife Rider', GOOD, True)
        token = user['server']['token']
        honest = ride(store)
        body = dict(kind='ride', reference='R-lab', details=dict(pickup=0, destination=1, comfort=False, multiplier=1.0), house_payee='fleet')
        send = lambda key, **change: attempt(lambda: client.call('POST', '/v1/payments', dict(body, **change), token=token, key=key))
        rows = [('what the client sends', 'server answer'),
                ('the booking, as the app does', attempt(lambda: backend.sync(store, client))),
                ('an extra field amount_cents = 1', send('K-amount-0001', amount_cents=1)),
                ('multiplier 0.1 (a 90 % discount)', send('K-cheap-00001', details=dict(body['details'], multiplier=0.1))),
                ('multiplier 4.0 (above the x2 cap)', send('K-surge-00001', details=dict(body['details'], multiplier=4.0))),
                ('pickup = destination', send('K-route-00001', details=dict(body['details'], destination=0))),
                ('food: a dish from another kitchen', send('K-food-000001', kind='food', details=dict(items={'pizza': 1}), house_payee='kitchen-0')),
                ('food: quantity -3', send('K-food-000002', kind='food', details=dict(items={'bowl': -3}), house_payee='kitchen-0')),
                ('a second payment for the same booking', send('K-twice-00001', reference=honest['ref']))]
        table('A16  Trying to pay less (or charge more)', rows)
        mine = client.call('GET', '/v1/payments', token=token)['payments']
        print(f"\n  on the server: {len(mine)} payment, amount {mine[0]['amount_cents']} cents - the server's own price for that route")
        assert rows[1][1] == 'accepted' and [r[1][:3] for r in rows[2:]] == ['422'] * 6 + ['409'] and len(mine) == 1
        assert mine[0]['amount_cents'] == pay.quote('ride', honest['details']) == honest['amount']
        return dict(server=server.name, rows=rows)


# ---------------------------------------------------------------------------- A17
def lab17(force_stand_in: bool = False) -> dict:
    """A17 - Offline outbox and exactly-once: replies are lost, the phone retries, nobody is charged twice."""
    with a_server(force_stand_in) as server, a_phone() as store:
        user = join(store, backend.Backend(URL, session=server), 'passenger', 'Aoife Rider', 'aoife@atlas.ie', 'ride2026x')
        link(store, backend.Backend(URL, session=server), 'ride2026x', 'Aoife Rider', GOOD, True)
        for _ in range(5):
            ride(store)
        rows = [('sync', 'network', 'requests sent', 'phone marks sent', 'payments on server')]
        down = backend.Backend('http://127.0.0.1:9', timeout=0.3)             # nothing listens there
        result = backend.sync(store, down)
        rows.append((1, 'offline', 0, result['sent'], server.count('payments')))
        lossy = Lossy(server, lose=1)
        result = backend.sync(store, backend.Backend(URL, session=lossy))
        rows.append((2, 'first reply lost', lossy.sent, result['sent'], server.count('payments')))
        lossy = Lossy(server, lose=0)
        result = backend.sync(store, backend.Backend(URL, session=lossy))
        rows.append((3, 'healthy', lossy.sent, result['sent'], server.count('payments')))
        lossy = Lossy(server, lose=0)
        for payment in store.payments:                                         # a restored backup: the phone forgot it synced
            payment['synced'] = False
        result = backend.sync(store, backend.Backend(URL, session=lossy))
        rows.append((4, 'phone forgot; resends all', lossy.sent, result['sent'], server.count('payments')))
        table('A17  At-least-once delivery + idempotency key = exactly-once effect', rows)
        print(f"\n  each request carried Idempotency-Key = the phone's payment id, e.g. {store.payments[0]['id']}")
        print(f"  ledger lines on the server: {server.count('ledger')} (3 per payment)")
        assert [r[4] for r in rows[1:]] == [0, 1, 5, 5] and server.count('ledger') == 15 and rows[4][2] == 5
        assert all(p['synced'] for p in store.payments) and user['server']
        return dict(server=server.name, rows=rows)


# ---------------------------------------------------------------------------- A18
def lab18(force_stand_in: bool = False) -> dict:
    """A18 - Paying the driver out, a race for one balance, and reconciling the phone with the server."""
    with a_server(force_stand_in) as server, a_phone() as store:
        client = backend.Backend(URL, session=server)
        driver = join(store, client, 'driver', 'Siobhan Driver', 'siobhan@atlas.ie', 'drive2026', vehicle='Toyota Corolla',
                      plate='241-C-1234', licence='A12345', seats=4)
        link(store, client, 'drive2026', 'Siobhan Driver', GOOD)
        store.set_online(True)
        rider = join(store, client, 'passenger', 'Aoife Rider', 'aoife@atlas.ie', 'ride2026x')
        link(store, client, 'ride2026x', 'Aoife Rider', GOOD, True)
        for _ in range(2):
            ride(store, driver['id'])
        backend.sync(store, client)
        token = driver['server']['token']
        before = client.balance(token)
        answers, gate = [], threading.Barrier(4)

        def withdraw(i):
            gate.wait()
            answers.append(attempt(lambda: client.payout(token, 'drive2026', f'O-race-{i:06d}', before['balance_cents'])))

        threads = [threading.Thread(target=withdraw, args=(i,)) for i in range(4)]
        [t.start() for t in threads]
        [t.join() for t in threads]
        after = client.balance(token)
        table('A18  Four payouts of the whole balance, started together', [('result', 'count')] + sorted((a, answers.count(a)) for a in set(answers)))
        print(f"\n  server balance {before['balance_cents']} -> {after['balance_cents']} cents; paid out {after['paid_out_cents']} (never more than was earned)")
        # The phone records the payout it was told about, then both sides are compared.
        store.session = driver['id']
        local = store.request_payout('drive2026', now=T0, payout_id='O-race-winner')
        store.mark_synced(local['id'])
        phone = pay.wallet(driver['id'], store.payments, store.payouts)
        rows = [('figure', 'phone', 'server', 'match'),
                ('driver earned', phone['earned'], after['earned_cents'], phone['earned'] == after['earned_cents']),
                ('driver paid out', phone['paid_out'], after['paid_out_cents'], phone['paid_out'] == after['paid_out_cents']),
                ('driver balance', phone['balance'], after['balance_cents'], phone['balance'] == after['balance_cents'])]
        store.session = rider['id']
        extra = ride(store, driver['id'])                                      # captured on the phone, not yet synced
        late = pay.wallet(driver['id'], store.payments, store.payouts)
        rows.append(('after one unsynced ride', late['balance'], client.balance(token)['balance_cents'], False))
        table('  Reconciliation: do the two ledgers agree?', rows)
        print(f"  the difference is exactly the unsynced payment's net amount: {extra['payee_net']} cents -> sync, then compare again")
        backend.sync(store, client)
        assert answers.count('accepted') == 1 and len(answers) == 4 and after['balance_cents'] == 0
        assert all(r[3] for r in rows[1:4]) and client.balance(token)['balance_cents'] == late['balance'] == extra['payee_net']
        return dict(server=server.name, answers=sorted(answers), rows=rows)


LABS = {13: lab13, 14: lab14, 15: lab15, 16: lab16, 17: lab17, 18: lab18}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--all', action='store_true', help='run labs A13-A18')
    parser.add_argument('--lab', type=int, choices=sorted(LABS), help='run one lab')
    parser.add_argument('--stand-in', action='store_true', help='use DeskServer even if PostgreSQL is available')
    args = parser.parse_args(argv)
    chosen = sorted(LABS) if args.all or not args.lab else [args.lab]
    for number in chosen:
        print(f"\n{'=' * 96}\n{LABS[number].__doc__}")
        result = LABS[number](args.stand_in)
        if result.get('server'):
            print(f"  [back end: {result['server']}]")
    print(f"\n{len(chosen)} lab(s) ran and their internal assertions passed.")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
