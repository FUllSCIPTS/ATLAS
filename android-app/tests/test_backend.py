"""backend.py without a server: address rules, error mapping and the outbox, with a fake HTTP session."""
import pytest
from atlas_go import backend, payments as pay
from atlas_go.store import LocalStore
from test_roles import T0, passenger


@pytest.mark.parametrize('url,cleaned', [
    ('', ''), ('  ', ''), ('https://atlas.example.ie/', 'https://atlas.example.ie'),
    ('https://api.atlas.example.ie:8443/go', 'https://api.atlas.example.ie:8443/go'),
    ('http://localhost:8080', 'http://localhost:8080'), ('http://127.0.0.1:8080/', 'http://127.0.0.1:8080'),
    ('http://10.0.2.2:8080', 'http://10.0.2.2:8080'),
])
def test_server_address_is_normalised(url, cleaned):
    assert backend.clean_url(url) == cleaned


@pytest.mark.parametrize('url', ['http://atlas.example.ie', 'ftp://atlas.example.ie', 'atlas.example.ie', 'https://',
                                 'https://user:secret@atlas.example.ie', 'https://atlas.example.ie/?token=1',
                                 'https://atlas.example.ie/#x', 'http://localhost.evil.example', 'javascript:alert(1)',
                                 'https://exa mple.ie'])
def test_unsafe_server_addresses_are_refused(url):
    with pytest.raises(ValueError):
        backend.clean_url(url)


class Reply:
    def __init__(self, status, data=None, content=b'{}'):
        self.status_code, self._data, self.content = status, data, content

    def json(self):
        if self._data is None:
            raise ValueError('not json')
        return self._data


class Session:
    """Records every request and answers from a script."""

    def __init__(self, *script):
        self.script, self.sent = list(script), []

    def request(self, method, url, json=None, headers=None, timeout=None, allow_redirects=None):
        self.sent.append(dict(method=method, url=url, json=json, headers=headers, timeout=timeout,
                              allow_redirects=allow_redirects))
        answer = self.script.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer


def test_calls_carry_the_token_and_key_and_never_follow_redirects():
    session = Session(Reply(201, dict(payment=dict(id='srv-1'))))
    client = backend.Backend('https://atlas.example.ie/', session=session)
    payment = dict(id='P-1', kind='ride', ref='R-1', details=dict(pickup=0, destination=1), payee='fleet', amount=860)
    assert client.push_payment('tok', payment, None) == dict(id='srv-1')
    sent = session.sent[0]
    assert sent['url'] == 'https://atlas.example.ie/v1/payments' and sent['allow_redirects'] is False and sent['timeout'] == backend.TIMEOUT
    assert sent['headers'] == {'Accept': 'application/json', 'Authorization': 'Bearer tok', 'Idempotency-Key': 'P-1'}
    assert sent['json'] == dict(kind='ride', reference='R-1', details=dict(pickup=0, destination=1), payee_account=None,
                                house_payee='fleet')
    assert 'amount' not in str(sent['json'])                      # the phone's amount is never sent: the server prices it


@pytest.mark.parametrize('answer,status,retry', [
    (ConnectionError('refused'), 0, True), (TimeoutError('slow'), 0, True), (Reply(503), 503, True), (Reply(429), 429, True),
    (Reply(402, dict(error=dict(code='insufficient_funds', message='No funds.'))), 402, False),
    (Reply(500, None, b'<html>'), 500, False), (Reply(401, []), 401, False),
])
def test_failures_become_server_errors(answer, status, retry):
    client = backend.Backend('https://atlas.example.ie', session=Session(answer))
    with pytest.raises(backend.ServerError) as caught:
        client.balance('tok')
    assert caught.value.status == status and caught.value.retryable is retry and isinstance(caught.value, ValueError)
    assert 'Traceback' not in str(caught.value) and str(caught.value)


def test_backend_needs_an_address():
    with pytest.raises(ValueError, match='No ATLAS server'):
        backend.Backend('')


def captured(tmp_path, n=3):
    s = LocalStore(tmp_path / 'state.json')
    s.set_server('https://atlas.example.ie')
    passenger(s)
    s.link_bank('ride2026x', 'Aoife Rider', pay.SANDBOX_IBANS['approved'], True, now=T0)
    for _ in range(n):
        s.book(0, 1, now=T0, pay_by_bank=True)
        for _ in range(3):
            s.advance_ride(now=T0)
    return s


def test_outbox_waits_for_a_connected_account_and_keeps_order(tmp_path):
    s = captured(tmp_path)
    assert s.unsynced() == [] and backend.outbox(s) == []          # not connected: nothing leaves the phone
    s.connect('srv-account', 'tok')
    jobs = backend.outbox(s)
    assert [j['id'] for j in jobs] == [p['id'] for p in s.payments] and all(j['token'] == 'tok' and j['payee'] is None for j in jobs)
    ok = lambda i: Reply(201, dict(payment=dict(id=f'srv-{i}')))
    session = Session(ok(1), ConnectionError('offline'))
    results = backend.deliver(backend.Backend(s.server_url, session=session), jobs)
    assert results == [dict(id=s.payments[0]['id'], server='srv-1', error=None)] and len(session.sent) == 2
    assert backend.apply(s, results) == dict(sent=1, failed=0, waiting=2)
    refusal = Reply(422, dict(error=dict(code='invalid', message='Prices are capped at twice the base fare.')))
    session = Session(refusal, ok(3))
    client = backend.Backend(s.server_url, session=session)
    assert backend.sync(s, client) == dict(sent=1, failed=1, waiting=0)       # a refusal does not block the next one
    assert [p['synced'] for p in s.payments] == [True, False, True] and 'capped' in s.payments[1]['error']
    assert [x['headers']['Idempotency-Key'] for x in session.sent] == [s.payments[1]['id'], s.payments[2]['id']]
    s.disconnect()
    assert s.unsynced() == [] and 'server' not in LocalStore(tmp_path / 'state.json').user


def test_server_address_must_be_valid_to_be_saved(tmp_path):
    s = LocalStore(tmp_path / 'state.json')
    with pytest.raises(ValueError, match='https'):
        s.set_server('http://atlas.example.ie')
    s.set_server('https://atlas.example.ie/')
    assert LocalStore(tmp_path / 'state.json').server_url == 'https://atlas.example.ie'
    passenger(s)
    with pytest.raises(ValueError, match='did not return'):
        s.connect('', 'tok')
