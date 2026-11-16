"""ATLAS Go server on a real PostgreSQL: registration, sign-in, bank accounts, payments, ledger, payouts."""
import hashlib
import hmac
import threading
import uuid

import psycopg
import pytest

from atlas_go import payments as pay
from server import security
from server.db import Database
from conftest import ADMIN, CLOSED, GOOD, NO_FUNDS, PEPPER, Harness, admin, sibling

IBAN_DIGITS = '93115212345678'


def error(response):
    return response.json()['error']['code']


# ---------------------------------------------------------------------------- registration and sign-in
def test_register_each_role_and_read_it_back(server):
    for role in ('passenger', 'driver', 'seller'):
        user = server.register(role)
        me = server.call('GET', '/v1/me', user['token']).json()
        assert me['account'] == dict(id=user['id'], role=role, name='Aoife Rider', email=user['email']) and me['bank'] is None
    assert [r['n'] for r in server.sql('SELECT count(*) AS n FROM accounts')] == [3]
    assert server.sql('SELECT plate, seats, verified FROM driver_profiles') == [dict(plate='241-C-1234', seats=4, verified=False)]
    assert server.sql('SELECT price_cents FROM dishes') == [dict(price_cents=850)]
    row = server.sql("SELECT * FROM accounts WHERE role = 'passenger'")[0]
    assert row['phone'] == '+353851112233' and row['password_iterations'] == 1000
    assert len(bytes(row['password_salt'])) == 16 and len(bytes(row['password_hash'])) == 32
    assert bytes(row['password_hash']) == hashlib.pbkdf2_hmac('sha256', b'ride2026x', bytes(row['password_salt']), 1000)


@pytest.mark.parametrize('change,field', [
    (dict(email='not-an-email'), None), (dict(password='short1'), None), (dict(password='lettersonly'), None),
    (dict(phone='12'), None), (dict(name='A'), None), (dict(role='admin'), None),
    (dict(is_admin=True), 'is_admin'), (dict(id=str(uuid.uuid4())), 'id'), (dict(name=None), 'name'),
    (dict(role='driver'), None),                                   # driver details missing
    (dict(role='driver', driver=dict(vehicle='Car X', plate='XYZ', licence='A12345', seats=4)), None),
    (dict(role='driver', driver=dict(vehicle='Car X', plate='241-C-1', licence='A12345', seats='4')), 'driver.seats'),
    (dict(role='seller', kitchen=dict(name='Bake', cuisine='Bakery', registration='FBO-1', place=1, prep=2)), None),
    (dict(role='seller', kitchen=dict(name='Bake', cuisine='Bakery', registration='FBO-1', place=9, prep=10)), None),
])
def test_registration_rejects_bad_or_unexpected_input(server, change, field):
    body = dict(role='passenger', name='Aoife Rider', email='a@atlas.ie', phone='0851112233', password='ride2026x')
    body.update(change)
    response = server.call('POST', '/v1/accounts', **body)
    assert response.status_code == 422 and error(response) == 'invalid'
    if field:
        assert response.json()['error']['field'] == field
    assert str(change.get('password', '')) not in response.text or not change.get('password')
    assert server.sql('SELECT count(*) AS n FROM accounts')[0]['n'] == 0


def test_duplicate_email_and_kitchen_name(server):
    server.register(email='same@atlas.ie')
    body = dict(role='passenger', name='Brian Rider', email='SAME@atlas.ie', phone='0851112233', password='ride2026x')
    response = server.call('POST', '/v1/accounts', **body)
    assert response.status_code == 409 and error(response) == 'email_taken'
    seller = server.register('seller')
    kitchen = dict(name=f'lee side bakery {server.n}', cuisine='Bakery', registration='FBO-9', place=1, prep=10)
    response = server.call('POST', '/v1/accounts', **dict(body, role='seller', email='s2@atlas.ie', kitchen=kitchen))
    assert response.status_code == 409 and error(response) == 'kitchen_taken'
    assert server.sql('SELECT count(*) AS n FROM accounts')[0]['n'] == 2 and seller['id']


def test_login_uniform_failures_lockout_and_unlock(server):
    user = server.register(email='p@atlas.ie')
    wrong = server.call('POST', '/v1/sessions', email='p@atlas.ie', password='nope12345')
    unknown = server.call('POST', '/v1/sessions', email='nobody@atlas.ie', password='nope12345')
    assert wrong.status_code == unknown.status_code == 401 and wrong.json() == unknown.json()
    for _ in range(4):
        assert server.call('POST', '/v1/sessions', email='P@atlas.ie ', password='nope12345').status_code == 401
    locked = server.call('POST', '/v1/sessions', email='p@atlas.ie', password=user['password'])
    assert locked.status_code == 429 and error(locked) == 'locked' and 0 < int(locked.headers['Retry-After']) <= 60
    server.clock.advance(seconds=61)
    ok = server.call('POST', '/v1/sessions', email='p@atlas.ie', password=user['password'])
    assert ok.status_code == 201 and ok.json()['account']['id'] == user['id']
    assert server.sql('SELECT count(*) AS n FROM login_failures')[0]['n'] == 1      # only the unknown email's single failure
    assert [r['action'] for r in server.sql("SELECT action FROM audit_log WHERE action LIKE 'login%%' ORDER BY id")] \
        == ['login.failed'] * 6 + ['login.ok']


def test_sessions_are_hashed_expire_and_can_be_revoked(server):
    user = server.register()
    stored = server.sql('SELECT token_hash FROM sessions')[0]['token_hash']
    assert bytes(stored) == hashlib.sha256(user['token'].encode()).digest()
    for bad in (None, 'x' * 43, user['token'] + 'x', user['token'].swapcase()):
        response = server.call('GET', '/v1/me', bad)
        assert response.status_code == 401 and response.headers['WWW-Authenticate'] == 'Bearer'
    basic = server.client.get('/v1/me', headers={'Authorization': 'Basic ' + user['token']})
    assert basic.status_code == 401
    second = server.call('POST', '/v1/sessions', email=user['email'], password=user['password']).json()['token']
    assert server.call('DELETE', '/v1/sessions/current', second).status_code == 204
    assert server.call('GET', '/v1/me', second).status_code == 401           # revoked
    assert server.call('GET', '/v1/me', user['token']).status_code == 200    # the other session lives on
    server.clock.advance(hours=720, seconds=1)
    assert server.call('GET', '/v1/me', user['token']).status_code == 401    # expired


def test_cheaper_hash_is_upgraded_at_sign_in(server):
    user = server.register()
    stronger = Harness(server.dsn, server.clock, migrate=False)
    stronger.app.state.service.iterations = 3000
    assert stronger.call('POST', '/v1/sessions', email=user['email'], password=user['password']).status_code == 201
    assert server.sql('SELECT password_iterations AS i FROM accounts')[0]['i'] == 3000
    assert stronger.call('POST', '/v1/sessions', email=user['email'], password=user['password']).status_code == 201
    stronger.client.close()


@pytest.mark.parametrize('email', ["' OR '1'='1", "a@atlas.ie'; DROP TABLE accounts; --", 'a@atlas.ie" OR ""="', '%', '\x00'])
def test_sql_injection_strings_are_just_data(server, email):
    server.register(email='a@atlas.ie')
    assert server.call('POST', '/v1/sessions', email=email, password="' OR '1'='1").status_code in (401, 422)
    assert server.call('POST', '/v1/accounts', role='passenger', name="Robert'); DROP TABLE accounts;--", email=email,
                       phone='0851112233', password='ride2026x').status_code == 422
    assert server.sql('SELECT count(*) AS n FROM accounts')[0]['n'] == 1


# ---------------------------------------------------------------------------- bank accounts
def test_linking_a_bank_account_needs_password_consent_and_a_real_iban(server):
    user = server.register()
    link = lambda **change: server.call('PUT', '/v1/me/bank', user['token'], **dict(
        dict(password=user['password'], holder='Aoife Rider', iban=GOOD, consent=True), **change))
    assert link(password='wrong-pass1').status_code == 403
    assert link(consent=False).status_code == 422
    assert link(iban=GOOD[:-1] + '9').status_code == 422
    assert link(iban='US29AIBK93115212345678').status_code == 422
    assert link(holder='12345').status_code == 422
    assert link(consent='yes').status_code == 422
    assert server.sql('SELECT count(*) AS n FROM bank_accounts')[0]['n'] == 0
    bank = link().json()['bank']
    assert bank['last4'] == '5678' and bank['purpose'] == 'debit' and bank['mandate_id'].startswith('M-')
    assert IBAN_DIGITS not in str(bank)
    row = server.sql('SELECT * FROM bank_accounts')[0]
    assert bytes(row['fingerprint']) == hmac.new(PEPPER, GOOD.encode(), hashlib.sha256).digest()
    assert bytes(row['fingerprint']) != hashlib.sha256(GOOD.encode()).digest()       # keyed, not a plain hash
    assert row['provider_token'].startswith('sbx_') and row['mandate_version'] == pay.MANDATE_VERSION
    assert server.call('GET', '/v1/me', user['token']).json()['bank']['mandate_id'] == bank['mandate_id']
    link(iban='DE89 3704 0044 0532 0130 00')                                       # replace: the old one is revoked
    rows = server.sql('SELECT last4, revoked_at IS NULL AS active FROM bank_accounts ORDER BY created_at, last4 DESC')
    assert sorted((r['last4'], r['active']) for r in rows) == [('3000', True), ('5678', False)]
    assert server.call('DELETE', '/v1/me/bank', user['token'], password='nope12345').status_code == 403
    assert server.call('DELETE', '/v1/me/bank', user['token'], password=user['password']).status_code == 204
    assert server.call('DELETE', '/v1/me/bank', user['token'], password=user['password']).status_code == 404
    assert server.call('GET', '/v1/me', user['token']).json()['bank'] is None


def test_payout_accounts_have_no_mandate_and_step_up_locks_out(server):
    driver = server.payee('driver')
    assert server.sql('SELECT purpose, mandate_id FROM bank_accounts') == [dict(purpose='payout', mandate_id=None)]
    for _ in range(5):
        response = server.call('PUT', '/v1/me/bank', driver['token'], password='guess12345', holder='X Y', iban=GOOD)
        assert response.status_code == 403 and error(response) == 'wrong_password'
    locked = server.call('PUT', '/v1/me/bank', driver['token'], password='drive2026', holder='X Y', iban=GOOD)
    assert locked.status_code == 429                    # a stolen token cannot brute-force the password
    server.clock.advance(seconds=61)
    assert server.call('PUT', '/v1/me/bank', driver['token'], password='drive2026', holder='X Y', iban=GOOD).status_code == 200


# ---------------------------------------------------------------------------- payments
def test_ride_payment_is_priced_by_the_server_and_posted_to_the_ledger(server):
    rider = server.passenger()
    response = server.ride(rider)
    assert response.status_code == 201
    payment = response.json()['payment']
    assert (payment['amount_cents'], payment['payee_net_cents'], payment['platform_fee_cents']) == (860, 731, 129)
    assert payment['status'] == 'captured' and payment['role'] == 'payer' and payment['last4'] == '5678'
    lines = server.sql('SELECT txn, account, debit_cents, credit_cents FROM ledger_entries ORDER BY id')
    assert [(l['account'], l['debit_cents'], l['credit_cents']) for l in lines] == [
        ('bank:clearing', 860, 0), ('payable:fleet', 0, 731), ('revenue:commission', 0, 129)]
    assert {l['txn'] for l in lines} == {payment['id']}
    event = server.sql('SELECT event_type, body FROM outbox ORDER BY id DESC LIMIT 1')[0]
    assert event['event_type'] == 'payment.captured' and event['body']['amount_cents'] == 860
    assert server.sql("SELECT count(*) AS n FROM audit_log WHERE action = 'payment.captured'")[0]['n'] == 1
    busy = server.ride(rider, comfort=True, multiplier=1.4).json()['payment']
    assert busy['amount_cents'] == 1570


@pytest.mark.parametrize('extra', [dict(amount_cents=1), dict(payee_net_cents=860), dict(status='refunded'),
                                   dict(payer_id=str(uuid.uuid4()))])
def test_client_cannot_send_amounts_status_or_payer(server, extra):
    rider = server.passenger()
    response = server.call('POST', '/v1/payments', rider['token'], 'P-key-0001', kind='ride', reference='R-1',
                           details=dict(pickup=0, destination=1), house_payee='fleet', **extra)
    assert response.status_code == 422 and server.sql('SELECT count(*) AS n FROM payments')[0]['n'] == 0


@pytest.mark.parametrize('details', [dict(pickup=0, destination=0), dict(pickup=0, destination=9), dict(pickup='0', destination=1),
                                     dict(pickup=0, destination=1, multiplier=4.0), dict(pickup=0, destination=1, multiplier=0.1),
                                     dict(pickup=0, destination=1, comfort='yes'), dict()])
def test_invalid_bookings_are_not_charged(server, details):
    rider = server.passenger()
    response = server.call('POST', '/v1/payments', rider['token'], 'P-key-0001', kind='ride', reference='R-1',
                           details=details, house_payee='fleet')
    assert response.status_code == 422 and server.sql('SELECT count(*) AS n FROM ledger_entries')[0]['n'] == 0


def test_driver_is_credited_and_each_party_sees_only_its_own_side(server):
    rider, driver, stranger = server.passenger(), server.payee('driver'), server.passenger()
    payment = server.ride(rider, payee=driver).json()['payment']
    assert server.call('GET', '/v1/me/balance', driver['token']).json() == dict(balance_cents=731, earned_cents=731, paid_out_cents=0)
    assert server.call('GET', '/v1/me/balance', rider['token']).status_code == 403
    seen = server.call('GET', '/v1/payments', driver['token']).json()['payments']
    assert len(seen) == 1 and seen[0]['role'] == 'payee' and 'last4' not in seen[0] and seen[0]['payee_net_cents'] == 731
    assert server.call('GET', f"/v1/payments/{payment['id']}", rider['token']).json()['payment']['last4'] == '5678'
    # Insecure direct object reference: another passenger asks for this payment by id.
    assert server.call('GET', f"/v1/payments/{payment['id']}", stranger['token']).status_code == 404
    assert server.call('GET', '/v1/payments', stranger['token']).json() == dict(payments=[])
    assert server.call('GET', '/v1/payments/not-a-uuid', rider['token']).status_code == 404
    assert server.call('GET', f'/v1/payments/{uuid.uuid4()}', rider['token']).status_code == 404


def test_payee_must_exist_and_have_the_right_role(server):
    rider, driver, seller = server.passenger(), server.payee('driver'), server.payee('seller')
    pay_to = lambda kind, **body: server.call('POST', '/v1/payments', rider['token'], f'P-{uuid.uuid4().hex}', kind=kind,
                                              reference=f'X-{uuid.uuid4().hex[:6]}', **body)
    ride, food = dict(pickup=0, destination=1), dict(items={'k3-1': 1})
    assert pay_to('ride', details=ride, payee_account=seller['id']).status_code == 422
    assert pay_to('ride', details=ride, payee_account=rider['id']).status_code == 422          # pay yourself
    assert pay_to('ride', details=ride, payee_account=str(uuid.uuid4())).status_code == 422
    assert pay_to('ride', details=ride, payee_account='1; DROP TABLE payments').status_code == 422
    assert pay_to('ride', details=ride).status_code == 422                                     # no payee
    assert pay_to('ride', details=ride, payee_account=driver['id'], house_payee='fleet').status_code == 422
    assert pay_to('ride', details=ride, house_payee='kitchen-0').status_code == 422
    assert pay_to('shared', details=dict(offer='pool-1', party=1), payee_account=driver['id']).status_code == 422
    assert pay_to('food', details=food, payee_account=driver['id']).status_code == 422
    assert pay_to('tip', details=ride, house_payee='fleet').status_code == 422
    assert server.sql('SELECT count(*) AS n FROM payments')[0]['n'] == 0
    assert pay_to('shared', details=dict(offer='pool-1', party=2), house_payee='fleet').json()['payment']['amount_cents'] == 980
    assert pay_to('food', details=food, payee_account=seller['id']).json()['payment']['amount_cents'] == 1100


def test_only_passengers_with_a_mandate_can_pay(server):
    driver, no_bank = server.payee('driver'), server.passenger(iban=None)
    assert server.ride(driver).status_code == 403
    response = server.ride(no_bank)
    assert response.status_code == 409 and error(response) == 'no_mandate'
    assert server.call('POST', '/v1/payments', None, 'P-key-0001', kind='ride', reference='R-1',
                       details=dict(pickup=0, destination=1), house_payee='fleet').status_code == 401


def test_idempotency_key_replays_the_first_answer(server):
    rider = server.passenger()
    first = server.ride(rider, key='P-1763294400000000001', reference='R-1')
    again = server.ride(rider, key='P-1763294400000000001', reference='R-1')
    assert first.status_code == 201 and again.status_code == 200 and again.headers['Idempotent-Replay'] == 'true'
    assert again.json() == first.json()
    different = server.ride(rider, key='P-1763294400000000001', reference='R-1', comfort=True)
    assert different.status_code == 409 and error(different) == 'key_reused'
    other_key = server.ride(rider, key='P-1763294400000000002', reference='R-1')
    assert other_key.status_code == 409 and error(other_key) == 'already_paid'
    for bad in (None, 'short', 'has space in it', 'x' * 81):
        response = server.call('POST', '/v1/payments', rider['token'], bad, kind='ride', reference='R-2',
                               details=dict(pickup=0, destination=1), house_payee='fleet')
        assert response.status_code == 400 and error(response) == 'key_required'
    assert server.sql('SELECT count(*) AS n FROM payments')[0]['n'] == 1
    assert server.sql('SELECT count(*) AS n FROM ledger_entries')[0]['n'] == 3


def test_same_key_sent_concurrently_charges_once(server):
    rider = server.passenger()
    statuses, gate = [], threading.Barrier(6)

    def send():
        gate.wait()
        statuses.append(server.ride(rider, key='P-concurrent-0001', reference='R-1').status_code)

    threads = [threading.Thread(target=send) for _ in range(6)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert sorted(statuses) == [200] * 5 + [201]
    assert server.sql('SELECT count(*) AS n FROM payments')[0]['n'] == 1
    assert server.sql('SELECT sum(debit_cents) AS d FROM ledger_entries')[0]['d'] == 860


@pytest.mark.parametrize('iban,code', [(NO_FUNDS, 'insufficient_funds'), (CLOSED, 'account_closed')])
def test_declined_payment_moves_nothing_and_can_be_retried_with_a_new_key(server, iban, code):
    rider = server.passenger(iban)
    declined = server.ride(rider, key='P-key-declined', reference='R-1')
    assert declined.status_code == 402 and error(declined) == code
    assert server.sql('SELECT status, decline_reason FROM payments') == [dict(status='declined', decline_reason=code)]
    assert server.sql('SELECT count(*) AS n FROM ledger_entries')[0]['n'] == 0
    replay = server.ride(rider, key='P-key-declined', reference='R-1')
    assert replay.status_code == 402 and replay.json() == declined.json()
    server.call('PUT', '/v1/me/bank', rider['token'], password=rider['password'], holder='Aoife Rider', iban=GOOD, consent=True)
    assert server.ride(rider, key='P-key-retry-1', reference='R-1').status_code == 201
    assert server.sql('SELECT count(*) AS n FROM ledger_entries')[0]['n'] == 3


def test_food_is_priced_from_the_servers_own_menu(server):
    rider, seller = server.passenger(), server.payee('seller')
    food = lambda key, **body: server.call('POST', '/v1/payments', rider['token'], key, kind='food', **body)
    built_in = food('P-food-0001', reference='F-1', details=dict(items={'bowl': 1, 'juice': 1}), house_payee='kitchen-0')
    assert built_in.json()['payment']['amount_cents'] == 1730
    assert food('P-food-0002', reference='F-2', details=dict(items={'pizza': 1}), house_payee='kitchen-0').status_code == 422
    assert food('P-food-0003', reference='F-3', details=dict(items={'bowl': 11}), house_payee='kitchen-0').status_code == 422
    assert food('P-food-0004', reference='F-4', details=dict(items={'bowl': 1}), payee_account=seller['id']).status_code == 422
    seller_food = food('P-food-0005', reference='F-5', details=dict(items={'k3-1': 2}), payee_account=seller['id'])
    assert seller_food.json()['payment'] | dict(id=0, created_at=0) == dict(
        id=0, kind='food', reference='F-5', status='captured', amount_cents=1950, payee_net_cents=1530,
        platform_fee_cents=420, role='payer', created_at=0, last4='5678', decline_reason=None)
    # The seller raises the price and adds a dish; the next order uses the new menu.
    menu = dict(name='Lee Side Bakery', cuisine='Bakery', registration='FBO-1234', place=1, prep=12, dishes=[
        dict(id='k3-1', name='Sourdough toastie', detail='Cheddar and onion', price=900),
        dict(id='k3-2', name='Flat white', detail='Double shot', price=360)])
    assert server.call('PUT', '/v1/seller/kitchen', seller['token'], **menu).json()['kitchen']['dishes'] == 2
    assert server.call('PUT', '/v1/seller/kitchen', rider['token'], **menu).status_code == 403
    assert server.call('PUT', '/v1/seller/kitchen', seller['token'], **dict(menu, dishes=[dict(menu['dishes'][0], price=1)])).status_code == 422
    assert server.call('PUT', '/v1/seller/kitchen', seller['token'], **dict(menu, dishes=[dict(menu['dishes'][0], id='../x')])).status_code == 422
    again = food('P-food-0006', reference='F-6', details=dict(items={'k3-1': 1, 'k3-2': 1}), payee_account=seller['id'])
    assert again.json()['payment']['amount_cents'] == 900 + 360 + 250
    assert server.call('GET', '/v1/me/balance', seller['token']).json()['balance_cents'] == 1530 + (1260 - 126)


# ---------------------------------------------------------------------------- ledger integrity in the database
def test_ledger_is_append_only_and_must_balance(server):
    server.ride(server.passenger())
    for statement in ('UPDATE ledger_entries SET credit_cents = credit_cents + 100000 WHERE credit_cents > 0',
                      "DELETE FROM ledger_entries WHERE account = 'revenue:commission'", 'TRUNCATE ledger_entries'):
        with pytest.raises(psycopg.errors.IntegrityConstraintViolation, match='append-only'):
            server.sql(statement)
    with pytest.raises(psycopg.errors.CheckViolation, match='does not balance'):
        server.sql("INSERT INTO ledger_entries (txn, account, debit_cents, credit_cents, created_at) "
                   "VALUES ('forged', 'payable:fleet', 0, 5000, now())")          # a credit from nowhere
    for debit, credit in ((5, 5), (0, 0), (-5, 0)):
        with pytest.raises(psycopg.errors.CheckViolation):
            server.sql("INSERT INTO ledger_entries (txn, account, debit_cents, credit_cents, created_at) "
                       "VALUES ('forged', 'x', %s, %s, now())", debit, credit)
    with pytest.raises(psycopg.errors.CheckViolation):
        server.sql('UPDATE payments SET payee_net_cents = amount_cents')            # net + fee must equal the amount
    totals = server.sql('SELECT sum(debit_cents) AS d, sum(credit_cents) AS c, count(*) AS n FROM ledger_entries')[0]
    assert totals == dict(d=860, c=860, n=3)


def test_api_runs_as_a_least_privilege_role(server):
    owner = sibling(ADMIN, server.database_name)
    with psycopg.connect(owner, autocommit=True) as connection:
        script = (sibling.__globals__['ROOT'] / 'server' / 'roles.sql').read_text().replace(":app_password", "'atlas-app-test'")
        connection.execute(script)
    app_dsn = sibling(ADMIN, server.database_name, 'atlas_app', 'atlas-app-test')
    limited = Harness(app_dsn, server.clock, migrate=False)
    rider, driver = limited.passenger(), limited.payee('driver')
    assert limited.ride(rider, payee=driver).status_code == 201
    assert limited.call('POST', '/v1/payouts', driver['token'], 'O-key-0001', password='drive2026').status_code == 201
    assert limited.call('DELETE', '/v1/accounts/me', driver['token'], password='drive2026').status_code == 204
    for statement in ('UPDATE ledger_entries SET credit_cents = 1', 'DELETE FROM ledger_entries', 'DELETE FROM payments',
                      'DELETE FROM audit_log', "UPDATE audit_log SET action = 'x'", 'UPDATE payouts SET amount_cents = 100',
                      'DROP TABLE accounts', 'ALTER TABLE ledger_entries DISABLE TRIGGER ledger_no_change',
                      'CREATE TABLE loot (x int)', 'DELETE FROM accounts'):
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            limited.sql(statement)
    limited.client.close()


def test_migrations_run_once_and_are_safe_to_repeat(server):
    database = Database(server.dsn)
    assert database.migrate() == 1 and database.migrate() == 1
    assert server.sql('SELECT version FROM schema_version') == [dict(version=1)]
    assert server.call('GET', '/healthz').json() == dict(status='ok', schema=1)
    with pytest.raises(ValueError):
        Database('sqlite:///rides.db')


# ---------------------------------------------------------------------------- payouts
def test_payout_needs_step_up_a_bank_account_and_a_balance(server):
    rider, driver = server.passenger(), server.payee('driver', iban=None)
    payout = lambda key='O-key-0001', **body: server.call('POST', '/v1/payouts', driver['token'], key,
                                                         **dict(dict(password='drive2026'), **body))
    assert server.call('POST', '/v1/payouts', rider['token'], 'O-key-0001', password=rider['password']).status_code == 403
    assert error(payout()) == 'no_bank'
    server.call('PUT', '/v1/me/bank', driver['token'], password='drive2026', holder='Siobhan Driver', iban=GOOD)
    assert error(payout()) == 'too_small'
    server.ride(rider, payee=driver)
    assert payout(password='wrong-pass1').status_code == 403
    assert error(payout(key=None)) == 'key_required'
    assert error(payout(amount_cents=732)) == 'insufficient_balance'
    assert error(payout(amount_cents=99)) == 'too_small'
    assert payout(amount_cents='731').status_code == 422
    paid = payout(amount_cents=500)
    assert paid.status_code == 201 and paid.json()['payout'] | dict(id=0, created_at=0) == dict(
        id=0, amount_cents=500, status='paid', last4='5678', created_at=0)
    replay = payout(amount_cents=500)
    assert replay.status_code == 200 and replay.json() == paid.json()
    rest = payout(key='O-key-0002')
    assert rest.json()['payout']['amount_cents'] == 231
    assert server.call('GET', '/v1/me/balance', driver['token']).json() == dict(balance_cents=0, earned_cents=731, paid_out_cents=731)
    assert [p['amount_cents'] for p in server.call('GET', '/v1/payouts', driver['token']).json()['payouts']] in ([231, 500], [500, 231])
    totals = server.sql('SELECT sum(debit_cents) AS d, sum(credit_cents) AS c FROM ledger_entries')[0]
    assert totals['d'] == totals['c'] == 860 + 731
    clearing = server.sql("SELECT sum(debit_cents) - sum(credit_cents) AS held FROM ledger_entries WHERE account = 'bank:clearing'")
    assert clearing[0]['held'] == 129                       # only the platform's commission is left


def test_two_payouts_at_once_cannot_spend_the_balance_twice(server):
    rider, driver = server.passenger(), server.payee('driver')
    server.ride(rider, payee=driver)
    statuses, gate = [], threading.Barrier(4)

    def withdraw(i):
        gate.wait()
        statuses.append(server.call('POST', '/v1/payouts', driver['token'], f'O-race-{i:04d}', password='drive2026').status_code)

    threads = [threading.Thread(target=withdraw, args=(i,)) for i in range(4)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert sorted(statuses) == [201, 409, 409, 409]
    assert server.sql("SELECT sum(amount_cents) AS paid FROM payouts WHERE status = 'paid'")[0]['paid'] == 731
    assert server.call('GET', '/v1/me/balance', driver['token']).json()['balance_cents'] == 0


def test_payout_to_a_closed_account_fails_and_keeps_the_balance(server):
    rider, seller = server.passenger(), server.payee('seller', iban=CLOSED)
    server.call('POST', '/v1/payments', rider['token'], 'P-food-0001', kind='food', reference='F-1',
                details=dict(items={'k3-1': 1}), payee_account=seller['id'])
    failed = server.call('POST', '/v1/payouts', seller['token'], 'O-key-0001', password='drive2026')
    assert failed.status_code == 201 and failed.json()['payout']['status'] == 'failed'
    assert server.call('GET', '/v1/me/balance', seller['token']).json()['balance_cents'] == 765
    assert server.sql("SELECT count(*) AS n FROM ledger_entries WHERE txn = %s", failed.json()['payout']['id'])[0]['n'] == 0


# ---------------------------------------------------------------------------- erasure, hygiene
def test_account_deletion_erases_the_person_and_keeps_the_books(server):
    rider, driver = server.passenger(), server.payee('driver')
    server.ride(rider, payee=driver)
    assert error(server.call('DELETE', '/v1/accounts/me', driver['token'], password='drive2026')) == 'balance_due'
    assert server.call('DELETE', '/v1/accounts/me', rider['token'], password='nope12345').status_code == 403
    server.call('POST', '/v1/payouts', driver['token'], 'O-key-0001', password='drive2026')
    for user, password in ((driver, 'drive2026'), (rider, rider['password'])):
        assert server.call('DELETE', '/v1/accounts/me', user['token'], password=password).status_code == 204
        assert server.call('GET', '/v1/me', user['token']).status_code == 401
        assert server.call('POST', '/v1/sessions', email=user['email'], password=password).status_code == 401
    rows = server.sql('SELECT name, email, phone, deleted_at IS NOT NULL AS gone FROM accounts')
    assert all(r['name'] == 'Deleted user' and r['email'].endswith('@deleted.invalid') and r['phone'] == '' and r['gone'] for r in rows)
    assert server.sql("SELECT count(*) AS n FROM bank_accounts WHERE revoked_at IS NULL OR holder <> 'Deleted user'")[0]['n'] == 0
    assert server.sql("SELECT plate FROM driver_profiles") == [dict(plate='removed')]
    assert server.sql('SELECT count(*) AS n FROM payments')[0]['n'] == 1 and server.sql('SELECT count(*) AS n FROM ledger_entries')[0]['n'] == 5
    server.register(email=rider['email'])                    # the email address is free again


def test_no_password_token_or_iban_is_stored_or_logged(server):
    rider, driver = server.passenger(), server.payee('driver')
    server.ride(rider, payee=driver)
    server.call('POST', '/v1/payouts', driver['token'], 'O-key-0001', password='drive2026')
    server.call('POST', '/v1/sessions', email=rider['email'], password='nope12345')
    dump = ''
    for table in ('accounts', 'driver_profiles', 'kitchens', 'dishes', 'sessions', 'login_failures', 'bank_accounts',
                  'payments', 'payouts', 'ledger_entries', 'outbox', 'audit_log'):
        dump += str(server.sql(f'SELECT * FROM {table}'))
    for secret in (rider['password'], 'drive2026', 'nope12345', rider['token'], driver['token'], GOOD, GOOD[4:], IBAN_DIGITS):
        assert secret not in dump
    assert rider['email'] not in str(server.sql('SELECT * FROM audit_log'))          # audit keeps ids, not emails


def test_http_hygiene(server):
    user = server.register()
    response = server.call('GET', '/v1/me', user['token'])
    assert response.headers['Cache-Control'] == 'no-store' and response.headers['X-Content-Type-Options'] == 'nosniff'
    big = server.client.post('/v1/sessions', content=b'{"email": "' + b'a' * 70_000 + b'"}', headers={'Content-Type': 'application/json'})
    assert big.status_code == 413
    assert server.client.post('/v1/sessions', content=b'{not json', headers={'Content-Type': 'application/json'}).status_code == 422
    assert server.client.post('/v1/sessions', content=b'[]', headers={'Content-Type': 'application/json'}).status_code == 422
    assert server.call('GET', '/v1/nothing').status_code == 404
    assert server.call('PATCH', '/v1/me', user['token']).status_code == 405
    server.app.state.service.clock = lambda: 1 / 0                                   # an unexpected crash
    crash = server.call('GET', '/v1/me', user['token'])
    assert crash.status_code == 500 and error(crash) == 'server' and 'ZeroDivision' not in crash.text and 'Traceback' not in crash.text


def test_configuration_is_checked(server, monkeypatch):
    from server import app as api
    with pytest.raises(ValueError, match='pepper|PEPPER'):
        api.Service(Database(server.dsn), b'short')
    with pytest.raises(ValueError, match='iterations'):
        api.Service(Database(server.dsn), PEPPER, iterations=10)
    assert security.DEFAULT_ITERATIONS == 600_000
    monkeypatch.setenv('DATABASE_URL', server.dsn)
    monkeypatch.delenv('ATLAS_BANK_PEPPER', raising=False)
    with pytest.raises(RuntimeError, match='ATLAS_BANK_PEPPER'):
        api.from_env()
    monkeypatch.setenv('ATLAS_BANK_PEPPER', 'ab' * 32)
    monkeypatch.setenv('ATLAS_PBKDF2_ITERATIONS', '1000')
    assert api.from_env().state.service.pepper == bytes.fromhex('ab' * 32)
