"""Tests for python_lab/payment_flows.py (Part III, labs A13-A18).

    python -m pytest -q python_lab/tests/test_payment_flows.py

Every lab runs on the in-memory stand-in. When ATLAS_TEST_DATABASE_URL names a PostgreSQL server (and
fastapi + psycopg are installed) each lab also runs on the real ATLAS Go server, and the two results
must be identical: that is the contract test that keeps the stand-in honest.
"""
import importlib.util
import os
import sys
from pathlib import Path

import pytest

_path = Path(__file__).resolve().parents[1] / 'payment_flows.py'
_spec = importlib.util.spec_from_file_location('payment_flows', _path)
pf = importlib.util.module_from_spec(_spec)
sys.modules['payment_flows'] = pf
_spec.loader.exec_module(pf)

REAL = bool(os.environ.get('ATLAS_TEST_DATABASE_URL')) and importlib.util.find_spec('fastapi') and importlib.util.find_spec('psycopg')
needs_postgres = pytest.mark.skipif(not REAL, reason='set ATLAS_TEST_DATABASE_URL (and install fastapi, psycopg) for the real server')


@pytest.mark.parametrize('number', sorted(pf.LABS))
def test_lab_runs_on_the_stand_in(number, capsys):
    result = pf.LABS[number](True)
    assert result and 'Traceback' not in capsys.readouterr().out
    assert result.get('server', pf.DeskServer.name) == pf.DeskServer.name


@needs_postgres
@pytest.mark.parametrize('number', [13, 14, 16, 17, 18])
def test_stand_in_and_real_server_give_the_same_answers(number):
    fake, real = pf.LABS[number](True), pf.LABS[number](False)
    assert real['server'] == pf.RealServer.name
    assert fake['rows'] == real['rows']
    if number == 18:
        assert fake['answers'] == real['answers'] == ['409 insufficient_balance'] * 3 + ['accepted']
    if number == 14:
        assert real['database'] == 'CHECK constraint refused it' and fake['database'] is None


def test_registration_is_checked_on_both_sides():
    rows = pf.lab13(True)['rows']
    assert [r[1] == 'accepted' for r in rows[1:]] == [True, False, False, False, False]
    assert [r[2] for r in rows[1:]] == ['accepted'] + ['422 invalid'] * 4


def test_payment_lifecycle_table():
    result = pf.lab15()
    assert [(r[1], r[2]) for r in result['rows'][1:]] == [('active', 'authorised'), ('none', 'voided'), ('active', 'authorised'),
                                                          ('none', 'captured'), ('none', '-')]
    assert [(a, d, c) for _t, a, d, c in result['lines']] == [('bank:clearing', 980, 0), ('payable:fleet', 0, 833),
                                                             ('revenue:commission', 0, 147)]


def test_every_attempt_to_change_the_price_is_refused():
    rows = pf.lab16(True)['rows']
    assert rows[1][1] == 'accepted' and all(r[1].startswith(('422', '409')) for r in rows[2:]) and len(rows) == 9


def test_lost_replies_never_charge_twice():
    rows = pf.lab17(True)['rows']
    assert [r[4] for r in rows[1:]] == [0, 1, 5, 5] and [r[3] for r in rows[1:]] == [0, 0, 5, 5]


def test_cli_runs_one_lab_and_all(capsys):
    assert pf.main(['--lab', '15']) == 0
    assert '1 lab(s) ran' in capsys.readouterr().out
    assert pf.main(['--all', '--stand-in']) == 0
    assert '6 lab(s) ran' in capsys.readouterr().out


def test_desk_server_refuses_what_the_real_server_refuses():
    desk = pf.DeskServer()
    client = pf.backend.Backend(pf.URL, session=desk)
    assert pf.attempt(lambda: client.balance('no-such-token')) == '401 unauthenticated'
    assert pf.attempt(lambda: client.call('GET', '/v1/unknown')) == '401 unauthenticated'
    with pf.a_phone() as store:
        user = pf.join(store, client, 'passenger', 'Aoife Rider', 'aoife@atlas.ie', 'ride2026x')
        token = user['server']['token']
        body = dict(kind='ride', reference='R-1', details=dict(pickup=0, destination=1), house_payee='fleet')
        assert pf.attempt(lambda: client.call('POST', '/v1/payments', body, token=token, key='K-00000001')) == '409 no_mandate'
        assert pf.attempt(lambda: client.payout(token, 'ride2026x', 'O-00000001', 100)) == '403 forbidden'
        pf.link(store, client, 'ride2026x', 'Aoife Rider', pf.NO_FUNDS, True)
        assert pf.attempt(lambda: client.call('POST', '/v1/payments', body, token=token, key='K-00000002')) == '402 insufficient_funds'
        pf.link(store, client, 'ride2026x', 'Aoife Rider', pf.GOOD, True)
        assert pf.attempt(lambda: client.call('POST', '/v1/payments', body, token=token, key='K-00000003')) == 'accepted'
        assert pf.attempt(lambda: client.call('POST', '/v1/payments', dict(body, reference='R-2'), token=token, key='K-00000003')) == '409 key_reused'
        assert pf.attempt(lambda: client.call('POST', '/v1/payments', dict(body, payee_account=user['server']['id'], house_payee=None),
                                              token=token, key='K-00000004')) == '422 invalid'
