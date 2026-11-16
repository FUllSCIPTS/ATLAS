"""Fixtures for the server tests. They need a real PostgreSQL (the schema uses triggers, partial
indexes, row locks and JSONB), named by ATLAS_TEST_DATABASE_URL, for example

    ATLAS_TEST_DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5432/postgres python -m pytest server/tests

The role must be allowed to CREATE DATABASE: every test runs in its own database, cloned from a
migrated template, so tests cannot see each other's rows and can run in any order.
"""
import datetime as dt
import os
import sys
import uuid
from pathlib import Path

import psycopg
import pytest

ROOT = Path(__file__).resolve().parents[2]                    # android-app/
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests'))                       # reuse the app tests' helpers

from fastapi.testclient import TestClient                     # noqa: E402
from atlas_go import payments as pay                          # noqa: E402
from server.app import create_app                             # noqa: E402
from server.db import Database                                # noqa: E402

ADMIN = os.environ.get('ATLAS_TEST_DATABASE_URL', '')
PEPPER = bytes(range(32))
GOOD, NO_FUNDS, CLOSED = (pay.SANDBOX_IBANS[k] for k in ('approved', 'insufficient_funds', 'account_closed'))


def pytest_collection_modifyitems(config, items):
    if not ADMIN:
        skip = pytest.mark.skip(reason='set ATLAS_TEST_DATABASE_URL to a PostgreSQL server to run the server tests')
        for item in items:
            item.add_marker(skip)


def sibling(dsn: str, name: str, user: str | None = None, password: str | None = None) -> str:
    """The same server, another database (and optionally another role)."""
    info = psycopg.conninfo.conninfo_to_dict(dsn)
    info['dbname'] = name
    if user:
        info['user'], info['password'] = user, password
    auth = info.get('user', '') + (':' + info['password'] if info.get('password') else '')
    return f"postgresql://{auth}@{info.get('host', '127.0.0.1')}:{info.get('port', 5432)}/{name}"


def admin(sql: str, *params) -> None:
    with psycopg.connect(ADMIN, autocommit=True) as connection:
        connection.execute(sql, params or None)


@pytest.fixture(scope='session')
def template():
    name = f'atlas_tpl_{uuid.uuid4().hex[:10]}'
    admin(f"CREATE DATABASE {name} ENCODING 'UTF8' TEMPLATE template0")
    assert Database(sibling(ADMIN, name)).migrate() == 1
    yield name
    admin(f'DROP DATABASE IF EXISTS {name} WITH (FORCE)')


class Clock:
    """A clock the test moves by hand, so lockouts and session expiry need no sleeping."""

    def __init__(self):
        self.now = dt.datetime(2026, 11, 16, 12, 0, tzinfo=dt.timezone.utc)

    def __call__(self):
        return self.now

    def advance(self, **delta):
        self.now += dt.timedelta(**delta)


class Harness:
    def __init__(self, dsn, clock, **options):
        self.dsn, self.clock = dsn, clock
        self.app = create_app(dsn, pepper=PEPPER, iterations=1000, clock=clock, **options)
        self.client = TestClient(self.app, raise_server_exceptions=False)
        self.n = 0

    def sql(self, query, *params):
        with psycopg.connect(self.dsn, row_factory=psycopg.rows.dict_row) as connection:
            cursor = connection.execute(query, params or None)
            return cursor.fetchall() if cursor.description else []

    def call(self, method, path, token=None, key=None, **body):
        headers = {}
        if token:
            headers['Authorization'] = 'Bearer ' + token
        if key:
            headers['Idempotency-Key'] = key
        return self.client.request(method, path, json=body or None, headers=headers)

    def register(self, role='passenger', email=None, password='ride2026x', **extra):
        self.n += 1
        body = dict(role=role, name='Aoife Rider', email=email or f'{role}{self.n}@atlas.ie', phone='085 111 2233',
                    password=password)
        if role == 'driver':
            body['driver'] = dict(vehicle='Toyota Corolla', plate='241-C-1234', licence='A12345', seats=4)
        if role == 'seller':
            body['kitchen'] = dict(name=f'Lee Side Bakery {self.n}', cuisine='Bakery', registration='FBO-1234', place=1,
                                   prep=10, dishes=[dict(id='k3-1', name='Sourdough toastie', detail='Cheddar and onion',
                                                         price=850)])
        body.update(extra)
        response = self.call('POST', '/v1/accounts', **body)
        assert response.status_code == 201, response.text
        data = response.json()
        return dict(id=data['account']['id'], token=data['token'], email=body['email'], password=password)

    def passenger(self, iban=GOOD, **extra):
        user = self.register('passenger', **extra)
        if iban:
            response = self.call('PUT', '/v1/me/bank', user['token'], password=user['password'], holder='Aoife Rider',
                                 iban=iban, consent=True)
            assert response.status_code == 200, response.text
        return user

    def payee(self, role='driver', iban=GOOD):
        user = self.register(role, password='drive2026')
        if iban:
            response = self.call('PUT', '/v1/me/bank', user['token'], password='drive2026', holder='Siobhan Driver', iban=iban)
            assert response.status_code == 200, response.text
        return user

    def ride(self, payer, key=None, payee=None, reference=None, **details):
        self.n += 1
        body = dict(kind='ride', reference=reference or f'R-{self.n}', details=dict(dict(pickup=0, destination=1), **details))
        body.update(dict(payee_account=payee['id']) if payee else dict(house_payee='fleet'))
        return self.call('POST', '/v1/payments', payer['token'], key or f'P-key-{self.n:04d}', **body)


@pytest.fixture
def server(template):
    name = f'atlas_t_{uuid.uuid4().hex[:12]}'
    admin(f'CREATE DATABASE {name} TEMPLATE {template}')
    harness = Harness(sibling(ADMIN, name), Clock(), migrate=False)
    harness.database_name = name
    yield harness
    harness.client.close()
    admin(f'DROP DATABASE IF EXISTS {name} WITH (FORCE)')
