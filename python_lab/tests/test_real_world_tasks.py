"""Part II, real-world testing tasks RT01-RT10: reference solutions against ATLAS Go 1.5.0.

    python -m pytest -q python_lab/tests/test_real_world_tasks.py

Each test names the task and the testing technique it practises. They test the app's real code
(android-app/atlas_go). RT07, RT09 and RT10 also run against the real server when
ATLAS_TEST_DATABASE_URL names a PostgreSQL server.
"""
import json
import sys
import threading
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_payment_flows import needs_postgres, pf       # noqa: E402  (also puts android-app on the path)

pay, backend, LocalStore, T0, GOOD, NO_FUNDS = pf.pay, pf.backend, pf.LocalStore, pf.T0, pf.GOOD, pf.NO_FUNDS


@pytest.fixture
def phone(tmp_path):
    """A passenger with a linked bank account, on a phone with no server."""
    store = LocalStore(tmp_path / 'state.json')
    store.register('passenger', 'Aoife Rider', 'aoife@atlas.ie', '0851112233', 'ride2026x')
    store.link_bank('ride2026x', 'Aoife Rider', GOOD, True, now=T0)
    return store


# RT01 - equivalence classes and boundary values: the IBAN field ------------------------------------
@pytest.mark.parametrize('iban,valid', [
    ('IE29 AIBK 9311 5212 3456 78', True),      # valid class, with the spaces people type
    ('ie29aibk93115212345678', True),           # lower case is normalised
    ('NO93 8601 1117 947', True),               # shortest SEPA IBAN (15)
    ('MT84 MALT 0110 0001 2345 MTLC AST0 01S', True),   # longest (31)
    ('IE29 AIBK 9311 5212 3456 7', False),      # one character short (boundary - 1)
    ('IE29 AIBK 9311 5212 3456 789', False),    # one too many (boundary + 1)
    ('IE28 AIBK 9311 5212 3456 78', False),     # wrong check digits
    ('US29 AIBK 9311 5212 3456 78', False),     # outside SEPA
    ('IE29 AIBK 9311 5212 3456 7!', False),     # illegal character
    ('', False),
])
def test_rt01_iban_classes_and_boundaries(iban, valid):
    if valid:
        assert pay.clean_iban(iban).isalnum()
    else:
        with pytest.raises(ValueError):
            pay.clean_iban(iban)


# RT02 - decision table + property: the fee split ----------------------------------------------------
@pytest.mark.parametrize('kind,amount,fee', [
    ('ride', 860, 129), ('ride', 3, 0), ('ride', 4, 1),           # 15 %: 0.45 rounds down, 0.60 rounds up
    ('ride', 10, 2),                                               # exactly half a cent (1.5) rounds up
    ('shared', 980, 147), ('food', 1100, 335), ('food', 255, 251), # delivery fee + 10 % of the food
])
def test_rt02_split_decision_table(kind, amount, fee):
    assert pay.split(kind, amount) == dict(payee_net=amount - fee, platform_fee=fee)


def test_rt02_split_property_no_cent_is_lost_or_created():
    hypothesis = pytest.importorskip('hypothesis')
    st = hypothesis.strategies

    @hypothesis.given(st.sampled_from(('ride', 'shared')), st.integers(1, 5_000_000))
    def rides(kind, amount):
        parts = pay.split(kind, amount)
        assert parts['payee_net'] + parts['platform_fee'] == amount and 0 <= parts['platform_fee'] <= amount
        assert pay.split(kind, amount + 1)['platform_fee'] >= parts['platform_fee']      # metamorphic: never decreasing

    @hypothesis.given(st.integers(pay.DELIVERY_FEE + 1, 5_000_000))
    def food(amount):
        parts = pay.split('food', amount)
        assert parts['payee_net'] + parts['platform_fee'] == amount and parts['platform_fee'] >= pay.DELIVERY_FEE

    rides()
    food()


# RT03 - state-transition testing: every pair of states ----------------------------------------------
@pytest.mark.parametrize('start', pay.STATUSES)
@pytest.mark.parametrize('target', pay.STATUSES)
def test_rt03_transition_matrix(phone, start, target):
    phone.book(0, 1, now=T0, pay_by_bank=True)
    payment = dict(phone.payment(phone.ride['payment']))
    path = {'authorised': [], 'captured': ['captured'], 'voided': ['voided'], 'refunded': ['captured', 'refunded'], 'declined': None}[start]
    if path is None:
        payment['status'] = 'declined'                    # a declined payment is never stored by the phone; build one
    for step in path or []:
        pay.move(payment, step, T0, payee='fleet')
    legal = target in pay.TRANSITIONS[start]
    if legal:
        pay.move(payment, target, T0, payee='fleet')
        assert payment['status'] == target
    else:
        with pytest.raises(ValueError, match='cannot become'):
            pay.move(payment, target, T0, payee='fleet')
        assert payment['status'] == start                 # a refused transition changes nothing


# RT04 - test doubles: a stub bank and a spy bank ----------------------------------------------------
def test_rt04_stub_bank_declines_and_spy_bank_sees_the_fare(phone, monkeypatch):
    calls = []

    def spy(last4, amount):
        calls.append((last4, amount))
        return 'approved'

    monkeypatch.setattr(pay, 'sandbox_outcome', spy)
    phone.book(0, 1, now=T0)                               # demo checkout: the bank must not be asked
    phone.advance_ride(cancel=True, now=T0)
    assert calls == []
    phone.book(0, 1, comfort=True, now=T0, pay_by_bank=True)
    assert calls == [('5678', phone.ride['fare'])]         # asked once, for exactly the fare
    phone.advance_ride(cancel=True, now=T0)
    monkeypatch.setattr(pay, 'sandbox_outcome', lambda last4, amount: 'limit_exceeded')      # stub: a canned answer
    with pytest.raises(ValueError, match='€500'):
        phone.book(0, 1, now=T0, pay_by_bank=True)
    assert phone.ride is None and len(phone.payments) == 1


# RT05 - integration test with a real file: pay, restart, compare ------------------------------------
def test_rt05_payment_survives_a_restart(phone):
    phone.book(0, 1, offer_id='pool-1', party=2, now=T0, pay_by_bank=True)
    for _ in range(4):
        phone.advance_ride(now=T0)
    restarted = LocalStore(phone.path)                     # a new object reading the same file = the app restarted
    assert restarted.payments == phone.payments and restarted.history == phone.history
    assert restarted.user['bank'] == phone.user['bank'] and restarted.offers[0].seats == 3
    assert pay.balanced(pay.entries(restarted.payments)) and not (phone.path.parent / 'state.invalid.json').exists()


# RT06 - security tests: what an attacker with the file can and cannot do ----------------------------
def test_rt06_bank_secrets_and_tampering(phone):
    phone.book(0, 1, now=T0, pay_by_bank=True)
    for _ in range(3):
        phone.advance_ride(now=T0)
    raw = phone.path.read_text(encoding='utf-8')
    assert GOOD not in raw and GOOD[4:] not in raw and 'ride2026x' not in raw          # no IBAN, no password on disk
    for attack in ('wrong-pass1', '', None, "' OR '1'='1"):
        with pytest.raises(ValueError, match='Password is not correct'):
            phone.unlink_bank(attack)
    data = json.loads(raw)
    data['payments'][0]['platform_fee'] = 0                # "the platform takes nothing": the split no longer adds up
    phone.path.write_text(json.dumps(data), encoding='utf-8')
    reopened = LocalStore(phone.path)
    assert reopened.accounts == [] and (phone.path.parent / 'state.invalid.json').exists()


# RT07 - contract test: what the client puts on the wire ---------------------------------------------
class Recorder:
    def __init__(self, inner):
        self.inner, self.seen = inner, []

    def request(self, method, url, **kwargs):
        self.seen.append((method, url, kwargs))
        return self.inner.request(method, url, **kwargs)


def check_contract(server):
    wire = Recorder(server)
    client = backend.Backend(pf.URL, session=wire)
    with pf.a_phone() as store:
        pf.join(store, client, 'passenger', 'Aoife Rider', 'aoife@atlas.ie', 'ride2026x')
        pf.link(store, client, 'ride2026x', 'Aoife Rider', GOOD, True)
        payment = pf.ride(store)
        assert backend.sync(store, client) == dict(sent=1, failed=0, waiting=0)
    method, url, sent = next(s for s in wire.seen if s[1].endswith('/v1/payments'))
    assert method == 'POST' and sent['headers']['Idempotency-Key'] == payment['id'] and sent['allow_redirects'] is False
    assert sent['headers']['Authorization'].startswith('Bearer ') and sent['timeout'] == backend.TIMEOUT
    assert set(sent['json']) == {'kind', 'reference', 'details', 'payee_account', 'house_payee'}       # no amount, no payer
    assert all('password' not in (s[2].get('json') or {}) for s in wire.seen if '/v1/payments' in s[1])
    assert all(s[1].startswith('https://') for s in wire.seen)


def test_rt07_client_contract_on_the_stand_in():
    check_contract(pf.DeskServer())


@needs_postgres
def test_rt07_client_contract_on_the_real_server():
    with pf.a_server() as server:
        check_contract(server)


# RT08 - reliability: any number of lost replies -----------------------------------------------------
@pytest.mark.parametrize('lost', [0, 1, 2, 5, 9])
def test_rt08_retries_until_done_and_charges_once(lost):
    server = pf.DeskServer()
    network = pf.Lossy(server, lose=lost)
    client = backend.Backend(pf.URL, session=network)
    with pf.a_phone() as store:
        setup = backend.Backend(pf.URL, session=server)
        pf.join(store, setup, 'passenger', 'Aoife Rider', 'aoife@atlas.ie', 'ride2026x')
        pf.link(store, setup, 'ride2026x', 'Aoife Rider', GOOD, True)
        for _ in range(3):
            pf.ride(store)
        rounds = 0
        while store.unsynced():
            backend.sync(store, client)
            rounds += 1
            assert rounds <= lost + 1, 'each round must make progress or hit one lost reply'
        assert server.count('payments') == 3 and network.sent == 3 + lost and rounds == lost + 1
        assert sum(d for _t, _a, d, _c in server.lines) == sum(c for _t, _a, _d, c in server.lines) == 3 * 860


# RT09 - concurrency: a race for one balance ---------------------------------------------------------
def race(server, threads=8):
    client = backend.Backend(pf.URL, session=server)
    with pf.a_phone() as store:
        driver = pf.join(store, client, 'driver', 'Siobhan Driver', 'siobhan@atlas.ie', 'drive2026', vehicle='Toyota Corolla',
                         plate='241-C-1234', licence='A12345', seats=4)
        pf.link(store, client, 'drive2026', 'Siobhan Driver', GOOD)
        store.set_online(True)
        pf.join(store, client, 'passenger', 'Aoife Rider', 'aoife@atlas.ie', 'ride2026x')
        pf.link(store, client, 'ride2026x', 'Aoife Rider', GOOD, True)
        pf.ride(store, driver['id'])
        backend.sync(store, client)
        token, answers, gate = driver['server']['token'], [], threading.Barrier(threads)

        def withdraw(i):
            gate.wait()
            answers.append(pf.attempt(lambda: client.payout(token, 'drive2026', f'O-rt09-{i:05d}', 400)))    # 2 x 400 > 731

        workers = [threading.Thread(target=withdraw, args=(i,)) for i in range(threads)]
        [w.start() for w in workers]
        [w.join() for w in workers]
        return answers, client.balance(token)


def test_rt09_payout_race_on_the_stand_in():
    answers, balance = race(pf.DeskServer())
    assert answers.count('accepted') == 1 and balance == dict(balance_cents=331, earned_cents=731, paid_out_cents=400)


@needs_postgres
def test_rt09_payout_race_on_postgresql():
    with pf.a_server() as server:
        answers, balance = race(server)
    assert answers.count('accepted') == 1 and answers.count('409 insufficient_balance') == 7
    assert balance == dict(balance_cents=331, earned_cents=731, paid_out_cents=400)


# RT10 - regression tests written from three defect reports of 1.5.0 ---------------------------------
def test_rt10_defect_3_payment_amount_must_match_the_booking(phone):
    """Defect: a saved file whose payment amount differed from the ride's fare was accepted."""
    phone.book(0, 1, now=T0, pay_by_bank=True)
    for _ in range(3):
        phone.advance_ride(now=T0)
    data = json.loads(phone.path.read_text(encoding='utf-8'))
    data['payments'][0].update(amount=86000, payee_net=85871)       # still adds up: 85871 + 129 = 86000
    phone.path.write_text(json.dumps(data), encoding='utf-8')
    assert LocalStore(phone.path).payments == []                    # quarantined, not trusted


@needs_postgres
def test_rt10_defects_1_and_2_on_the_server():
    """Defect 1: a NUL byte in the sign-in email caused a 500. Defect 2: Retry-After said 61 s for a 60 s lock."""
    with pf.a_server() as server:
        nul = server.request('POST', pf.URL + '/v1/sessions', json=dict(email='a\x00@atlas.ie', password='x'))
        assert nul.status_code == 401
        for _ in range(5):
            server.request('POST', pf.URL + '/v1/sessions', json=dict(email='a@atlas.ie', password='wrong-pass1'))
        locked = server.request('POST', pf.URL + '/v1/sessions', json=dict(email='a@atlas.ie', password='wrong-pass1'))
        assert locked.status_code == 429 and 1 <= int(locked.headers['Retry-After']) <= 60
