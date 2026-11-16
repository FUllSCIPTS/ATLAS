"""Client for the ATLAS Go server (server/, FastAPI + PostgreSQL) — 1.5.0.

The phone stays usable offline: accounts, rides and payments are written to state.json first.
When an account is connected, this module registers it on the server, links its bank account
there, and copies captured payments and payouts into PostgreSQL. Every write that can be retried
carries an Idempotency-Key (the phone's own payment or payout id), so a lost reply never charges
or pays twice. Calls block: run them off Kivy's main thread (AtlasGoApp.remote).
"""
from __future__ import annotations

import re
from urllib.parse import urlsplit

TIMEOUT = 6.0
LOCAL_HOSTS = ('localhost', '127.0.0.1', '10.0.2.2')       # 10.0.2.2 = the host machine, from an Android emulator


def clean_url(value: str) -> str:
    """'' (this phone only) or an https:// base URL. Plain http is accepted for a local test server only:
    a password or an IBAN must never cross a network unencrypted."""
    value = (value or '').strip().rstrip('/')
    if not value:
        return ''
    parts = urlsplit(value)
    if parts.username or parts.password or parts.query or parts.fragment or not parts.hostname:
        raise ValueError('Enter the server address only, for example https://atlas.example.ie.')
    if parts.scheme == 'http' and parts.hostname in LOCAL_HOSTS:
        return value
    if parts.scheme != 'https':
        raise ValueError('The server address must start with https://.')
    if not re.fullmatch(r'[A-Za-z0-9.-]+', parts.hostname):
        raise ValueError('Enter a valid server address.')
    return value


class ServerError(ValueError):
    """A refusal from the server (status 4xx/5xx) or no answer at all (status 0)."""

    def __init__(self, message: str, status: int = 0, code: str = 'network'):
        super().__init__(message)
        self.status, self.code = status, code

    @property
    def retryable(self) -> bool:
        return self.status in (0, 429, 502, 503, 504)


class Backend:
    def __init__(self, url: str, session=None, timeout: float = TIMEOUT):
        self.url = clean_url(url)
        if not self.url:
            raise ValueError('No ATLAS server is set.')
        self.session, self.timeout = session, timeout

    def call(self, method: str, path: str, body: dict | None = None, token: str | None = None,
             key: str | None = None) -> dict:
        if self.session is None:
            import requests                      # bundled with the APK; imported late, off the UI thread
            self.session = requests.Session()
        headers = {'Accept': 'application/json'}
        if token:
            headers['Authorization'] = 'Bearer ' + token
        if key:
            headers['Idempotency-Key'] = key
        try:
            response = self.session.request(method, self.url + path, json=body, headers=headers,
                                            timeout=self.timeout, allow_redirects=False)
        except Exception as error:               # DNS, TLS, refused, timeout: all mean "try again later"
            raise ServerError('Could not reach the ATLAS server. Your data is safe on this phone; '
                              'try again when you are online.') from error
        try:
            data = response.json() if response.content else {}
        except ValueError:
            data = {}
        if response.status_code >= 400:
            problem = data.get('error', {}) if isinstance(data, dict) else {}
            raise ServerError(problem.get('message') or f'The server refused the request ({response.status_code}).',
                              response.status_code, problem.get('code', 'error'))
        return data if isinstance(data, dict) else {}

    # ---- accounts and sessions
    def register(self, account: dict, password: str, kitchen: dict | None = None) -> dict:
        body = dict(role=account['role'], name=account['name'], email=account['email'], phone=account['phone'],
                    password=password)
        if account['role'] == 'driver':
            body['driver'] = {k: account['driver'][k] for k in ('vehicle', 'plate', 'licence', 'seats')}
        if account['role'] == 'seller' and kitchen:
            body['kitchen'] = kitchen_body(kitchen)
        return self.call('POST', '/v1/accounts', body)

    def login(self, email: str, password: str) -> dict:
        return self.call('POST', '/v1/sessions', dict(email=email, password=password))

    def connect(self, account: dict, password: str, kitchen: dict | None = None) -> dict:
        """Create the server account, or sign in if this email is already registered there."""
        try:
            return self.register(account, password, kitchen)
        except ServerError as error:
            if error.status != 409:
                raise
        return self.login(account['email'], password)

    def logout(self, token: str) -> None:
        self.call('DELETE', '/v1/sessions/current', token=token)

    # ---- bank account
    def link_bank(self, token: str, password: str, holder: str, iban: str, consent: bool) -> dict:
        return self.call('PUT', '/v1/me/bank', dict(password=password, holder=holder, iban=iban, consent=consent),
                         token=token)['bank']

    def unlink_bank(self, token: str, password: str) -> None:
        self.call('DELETE', '/v1/me/bank', dict(password=password), token=token)

    # ---- kitchens, payments, payouts
    def push_kitchen(self, token: str, kitchen: dict) -> None:
        self.call('PUT', '/v1/seller/kitchen', kitchen_body(kitchen), token=token)

    def push_payment(self, token: str, payment: dict, payee_account: str | None) -> dict:
        body = dict(kind=payment['kind'], reference=payment['ref'], details=payment['details'],
                    payee_account=payee_account,
                    house_payee=payment['payee'] if payee_account is None else None)
        return self.call('POST', '/v1/payments', body, token=token, key=payment['id'])['payment']

    def balance(self, token: str) -> dict:
        return self.call('GET', '/v1/me/balance', token=token)

    def payout(self, token: str, password: str, key: str, amount: int) -> dict:
        return self.call('POST', '/v1/payouts', dict(password=password, amount_cents=amount), token=token,
                         key=key)['payout']


def kitchen_body(kitchen: dict) -> dict:
    return dict(name=kitchen['name'], cuisine=kitchen['cuisine'], registration=kitchen['registration'],
                place=kitchen['place'], prep=kitchen['prep'], open=kitchen.get('open', True),
                dishes=[dict(id=d['id'], name=d['name'], detail=d['detail'], price=d['price'],
                             archived=bool(d.get('archived'))) for d in kitchen.get('dishes', [])])


def outbox(store) -> list[dict]:
    """What the server does not have yet, as plain jobs that can be sent from another thread:
    seller menus first (the server prices food from its own copy), then captured payments, oldest
    first. Reads the store; changes nothing."""
    jobs, pending = [], store.unsynced()
    for seller_id in sorted({p['payee'] for p in pending if p['kind'] == 'food' and
                             p['payee'] not in ('kitchen-0', 'kitchen-1', 'kitchen-2')}):
        seller = store.account(seller_id)
        kitchen = store.kitchen_of(seller)
        if kitchen:
            jobs.append(dict(type='kitchen', token=seller['server']['token'], kitchen=kitchen_body(kitchen)))
    for payment in pending:
        jobs.append(dict(type='payment', id=payment['id'], token=store.account(payment['payer'])['server']['token'],
                         payment=dict(payment), payee=store.server_payee(payment)[1]))
    return jobs


def deliver(backend: Backend, jobs: list[dict]) -> list[dict]:
    """Send the jobs in order (network only; no store access). Stops at the first failure that a
    retry could fix, so the order is kept; a refusal is recorded and the next job is tried."""
    results = []
    for job in jobs:
        try:
            if job['type'] == 'kitchen':
                backend.call('PUT', '/v1/seller/kitchen', job['kitchen'], token=job['token'])
            else:
                saved = backend.push_payment(job['token'], job['payment'], job['payee'])
                results.append(dict(id=job['id'], server=saved.get('id'), error=None))
        except ServerError as error:
            if error.retryable:
                break
            if job['type'] == 'payment':
                results.append(dict(id=job['id'], server=None, error=str(error)))
    return results


def apply(store, results: list[dict]) -> dict:
    """Record the server's answers in the store (call on the thread that owns the store)."""
    for r in results:
        store.mark_synced(r['id'], r['server'], r['error'])
    sent = sum(r['error'] is None for r in results)
    return dict(sent=sent, failed=len(results) - sent, waiting=len(store.unsynced()) - (len(results) - sent))


def sync(store, backend: Backend) -> dict:
    """outbox -> deliver -> apply in one call. Safe to call again after any failure: every payment
    carries its own id as the Idempotency-Key."""
    return apply(store, deliver(backend, outbox(store)))
