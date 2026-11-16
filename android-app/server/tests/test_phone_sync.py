"""The phone app against the real server over HTTP: LocalStore + backend.py -> uvicorn -> PostgreSQL."""
import socket
import threading
import time

import pytest
import uvicorn

from atlas_go import backend, payments as pay
from atlas_go.store import LocalStore
from test_roles import T0, driver, passenger, seller
from conftest import GOOD


@pytest.fixture
def live(server):
    """The test's app served on a real local port, as the phone would reach it."""
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        port = probe.getsockname()[1]
    web = uvicorn.Server(uvicorn.Config(server.app, host='127.0.0.1', port=port, log_level='warning'))
    thread = threading.Thread(target=web.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 10
    while not web.started and time.monotonic() < deadline:
        time.sleep(0.02)
    assert web.started
    server.url = f'http://127.0.0.1:{port}'
    yield server
    web.should_exit = True
    thread.join(timeout=10)


def connect(store, client, password):
    reply = client.connect(store.user, password, store.kitchen_of(store.user))
    store.connect(reply['account']['id'], reply['token'])
    return reply['account']['id']


def test_phone_payments_reach_postgresql_exactly_once(live, tmp_path):
    s = LocalStore(tmp_path / 'state.json')
    s.set_server(live.url)
    client = backend.Backend(s.server_url)

    d = driver(s)
    driver_sid = connect(s, client, 'drive2026')
    s.logout()
    sel = seller(s)
    dish = s.add_dish('Sourdough toastie', 'Cheddar and onion', '8.50')
    seller_sid = connect(s, client, 'bread2026')
    s.logout()
    p = passenger(s)
    connect(s, client, 'ride2026x')
    # Connected accounts link the bank on the server first; the phone keeps the mandate id it returns.
    bank = client.link_bank(p['server']['token'], 'ride2026x', 'Aoife Rider', GOOD, True)
    s.link_bank('ride2026x', 'Aoife Rider', GOOD, True, now=T0, mandate_id=bank['mandate_id'])
    assert p['bank']['mandate']['id'] == bank['mandate_id']

    # A ride with the registered driver, an order from the seller, and a shared ride with the house fleet.
    s.book(0, 1, driver='Siobhan', driver_id=d['id'], now=T0, pay_by_bank=True)
    s.update_cart('add', dish)
    s.checkout(1, now=T0, pay_by_bank=True)
    assert s.unsynced() == []                                   # nothing is sent before it is captured
    s.logout(); s.login('d@atlas.ie', 'drive2026', now=T0)
    s.driver_respond(True, now=T0)
    for _ in range(3):
        s.driver_advance(now=T0)
    s.logout(); s.login('s@atlas.ie', 'bread2026', now=T0)
    s.seller_accept(now=T0); s.seller_ready(now=T0); s.advance_order(now=T0); s.advance_order(now=T0)
    s.logout(); s.login('p@atlas.ie', 'ride2026x', now=T0)
    s.book(0, 1, offer_id='pool-1', party=2, now=T0, pay_by_bank=True)
    for _ in range(4):
        s.advance_ride(now=T0)
    assert len(s.unsynced()) == 3 and [j['type'] for j in backend.outbox(s)] == ['kitchen', 'payment', 'payment', 'payment']

    assert backend.sync(s, client) == dict(sent=3, failed=0, waiting=0)
    assert all(q['synced'] and q['server'] for q in s.payments) and s.unsynced() == []
    rows = live.sql('SELECT reference, amount_cents, payee_net_cents, platform_fee_cents, idempotency_key FROM payments ORDER BY created_at, reference')
    assert sorted((r['idempotency_key'], r['amount_cents'], r['payee_net_cents']) for r in rows) == \
        sorted((q['id'], q['amount'], q['payee_net']) for q in s.payments)
    # The phone's ledger and PostgreSQL's ledger agree account by account.
    phone = pay.entries(s.payments)
    for local, remote in ((pay.payable(d['id']), pay.payable(driver_sid)), (pay.payable(sel['id']), pay.payable(seller_sid)),
                          (pay.payable('fleet'), pay.payable('fleet')), (pay.REVENUE, pay.REVENUE), (pay.CLEARING, pay.CLEARING)):
        on_server = live.sql('SELECT COALESCE(SUM(credit_cents) - SUM(debit_cents), 0) AS b FROM ledger_entries WHERE account = %s', remote)
        assert on_server[0]['b'] == pay.balance(phone, local), remote
    assert LocalStore(tmp_path / 'state.json').payments == s.payments

    # A lost reply: the phone does not know the server has the payments and sends all three again.
    for q in s.payments:
        q['synced'] = False
    assert backend.sync(s, client)['sent'] == 3
    assert live.sql('SELECT count(*) AS n FROM payments')[0]['n'] == 3 and live.sql('SELECT count(*) AS n FROM ledger_entries')[0]['n'] == 9

    # Payout, server first (as the app does), then recorded on the phone under the same id.
    s.logout(); s.login('d@atlas.ie', 'drive2026', now=T0)
    token = d['server']['token']
    client.link_bank(token, 'drive2026', 'Siobhan Driver', GOOD, False)
    s.link_bank('drive2026', 'Siobhan Driver', GOOD, now=T0)
    with pytest.raises(backend.ServerError, match='Password is not correct') as refused:
        client.payout(token, 'wrong-pass1', 'O-1763294400000000001', 731)
    assert refused.value.status == 403 and not refused.value.retryable
    remote = client.payout(token, 'drive2026', 'O-1763294400000000001', s.wallet()['balance'])
    local = s.request_payout('drive2026', now=T0, payout_id='O-1763294400000000001')
    s.mark_synced(local['id'], remote['id'])
    assert remote['amount_cents'] == local['amount'] == 731 and s.payouts[0]['synced']
    assert client.balance(token) == dict(balance_cents=0, earned_cents=731, paid_out_cents=731)
    assert s.wallet()['balance'] == 0
    client.logout(token)
    with pytest.raises(backend.ServerError) as ended:
        client.balance(token)
    assert ended.value.status == 401


def test_offline_phone_keeps_working_and_syncs_later(live, tmp_path):
    s = LocalStore(tmp_path / 'state.json')
    s.set_server(live.url)
    client = backend.Backend(s.server_url)
    p = passenger(s)
    connect(s, client, 'ride2026x')
    bank = client.link_bank(p['server']['token'], 'ride2026x', 'Aoife Rider', GOOD, True)
    s.link_bank('ride2026x', 'Aoife Rider', GOOD, True, now=T0, mandate_id=bank['mandate_id'])
    s.book(0, 1, now=T0, pay_by_bank=True)
    for _ in range(3):
        s.advance_ride(now=T0)
    down = backend.Backend('http://127.0.0.1:9', timeout=0.5)                   # nothing listens on the discard port
    assert backend.sync(s, down) == dict(sent=0, failed=0, waiting=1)
    assert not s.payments[0]['synced'] and 'error' not in s.payments[0]
    assert backend.sync(s, client) == dict(sent=1, failed=0, waiting=0)
    # The server refuses what it cannot verify: the phone says a ride cost 4x; the server's own price cap says no.
    s.book(0, 1, now=T0, pay_by_bank=True)
    for _ in range(3):
        s.advance_ride(now=T0)
    s.payments[1]['details']['multiplier'] = 4.0
    assert backend.sync(s, client) == dict(sent=0, failed=1, waiting=0)
    assert 'capped' in s.payments[1]['error'] and not s.payments[1]['synced']
    assert live.sql('SELECT count(*) AS n FROM payments')[0]['n'] == 1


def test_connect_signs_in_when_the_email_is_already_registered(live, tmp_path):
    client = backend.Backend(live.url)
    first = LocalStore(tmp_path / 'phone1.json')
    passenger(first)
    one = client.connect(first.user, 'ride2026x')
    second = LocalStore(tmp_path / 'phone2.json')                  # the same person on a second phone
    passenger(second)
    two = client.connect(second.user, 'ride2026x')
    assert one['account']['id'] == two['account']['id'] and one['token'] != two['token']
    third = LocalStore(tmp_path / 'phone3.json')
    third.register('passenger', 'Someone Else', 'p@atlas.ie', '085 111 2233', 'other2026x')
    with pytest.raises(backend.ServerError, match='not correct'):
        client.connect(third.user, 'other2026x')                   # same email, different password: no takeover
