"""Tests for python_lab/feature_flow.py (Part III, lab A19: adding SOS to an existing app).

    python -m pytest -q python_lab/tests/test_feature_flow.py

Two groups: the new feature at each layer, and regression tests proving the old behaviour did not move.
"""
import importlib.util
import sqlite3
import sys
import threading
from pathlib import Path

import pytest

_path = Path(__file__).resolve().parents[1] / 'feature_flow.py'
_spec = importlib.util.spec_from_file_location('feature_flow', _path)
ff = importlib.util.module_from_spec(_spec)
sys.modules['feature_flow'] = ff
_spec.loader.exec_module(ff)
ai = ff.ai

POINT = {'lat': 51.9, 'lon': -8.47, 'source': 'device'}


@pytest.fixture
def app():
    with ff.SosApp(drivers=3, rides=4) as running:
        yield running


def raise_sos(app, ride_id=1, **body):
    ride = app.service.get_ride(ride_id)
    return app.client.post(f'/api/rides/{ride_id}/sos', {'passenger': ride['passenger'], **POINT, **body})


# ---- database --------------------------------------------------------------------------------
def test_migration_is_repeatable_and_keeps_existing_rows():
    db = ai.Database()
    ai.RideService(db, ai.Trace()).seed(3, 4, True)
    before = ff.rows_of(db, 'rides'), ff.rows_of(db, 'drivers')
    ff.migrate(db)
    ff.migrate(db)
    assert (ff.rows_of(db, 'rides'), ff.rows_of(db, 'drivers')) == before and ff.rows_of(db, 'sos') == []


@pytest.mark.parametrize('values', [(91, 0, 'route', 'active', None), (0, 181, 'route', 'active', None),
                                    (0, 0, 'gps', 'active', None), (0, 0, 'route', 'resolved', None),
                                    (0, 0, 'route', 'active', 5.0), (0, 0, 'route', 'paused', None)])
def test_database_checks_refuse_impossible_rows(values):
    db = ai.Database()
    ai.RideService(db, ai.Trace()).seed(2, 1, True)
    ff.migrate(db)
    with pytest.raises(sqlite3.IntegrityError):
        db.execute('INSERT INTO sos (ride_id, passenger, lat, lon, source, status, resolved_at, raised_at) '
                   "VALUES (1, 'x', ?, ?, ?, ?, ?, 0)", (*values[:4], values[4]))


def test_unique_index_allows_a_new_sos_after_the_old_one_ended():
    db = ai.Database()
    ai.RideService(db, ai.Trace()).seed(2, 1, True)
    ff.migrate(db)
    add = "INSERT INTO sos (ride_id, passenger, lat, lon, source, raised_at) VALUES (1, 'x', 1, 1, 'route', 0)"
    db.execute(add)
    with pytest.raises(sqlite3.IntegrityError):
        db.execute(add)
    db.execute("UPDATE sos SET status = 'resolved', resolved_at = 1")
    db.execute(add)
    assert db.count('sos') == 2


# ---- service and API -------------------------------------------------------------------------
def test_first_request_creates_and_repeat_returns_the_same_record(app):
    first, again = raise_sos(app), raise_sos(app)
    assert (first.status, again.status) == (201, 200)
    assert again.body['id'] == first.body['id'] and again.headers['Idempotent-Replay'] == 'true'
    assert app.db.count('sos') == 1 and app.db.count('audit', "action = 'sos'") == 1


def test_only_a_ride_in_progress_can_raise_an_sos(app):
    queued = app.service.create_ride({'passenger': 'Brian', 'pickup': 'UCC', 'destination': 'Kent Station', 'distance_km': 3})[0]
    resp = app.client.post(f"/api/rides/{queued['id']}/sos", {'passenger': 'Brian', **POINT})
    assert resp.status == 409 and '112' in resp.body['error'] and app.db.count('sos') == 0
    app.service.finish(1, 'complete')
    assert raise_sos(app, 1).status == 409                       # finished rides cannot either


def test_only_the_ride_passenger_can_raise_or_end_it(app):
    assert raise_sos(app, passenger='Somebody Else').status == 403
    assert app.client.post('/api/rides/1/sos', POINT).status == 403          # no name at all
    made = raise_sos(app)
    for name in ('Somebody Else', None, 7):
        assert app.client.post(f"/api/sos/{made.body['id']}/resolve", {'passenger': name}).status == 403
    assert app.db.query('SELECT status FROM sos')[0]['status'] == 'active'


@pytest.mark.parametrize('change', [{'lat': 91}, {'lat': '51.9'}, {'lat': True}, {'lat': None}, {'lon': -181},
                                    {'source': 'gps'}])
def test_bad_positions_are_rejected_before_the_database(app, change):
    app.db.statements.clear()
    resp = raise_sos(app, **change)
    assert resp.status == 422 and resp.body['field'] in ('lat', 'lon', 'source')
    assert not any('INSERT' in s and 'sos' in s for s in app.db.statements)


def test_unknown_ride_and_malformed_body(app):
    assert app.client.post('/api/rides/999/sos', {'passenger': 'x', **POINT}).status == 404
    assert app.client.post('/api/rides/1/sos', [1, 2]).status == 422
    assert app.client.get('/api/sos/999').status == 404


def test_ending_twice_is_a_conflict_and_a_new_sos_can_follow(app):
    made = raise_sos(app).body
    ok = app.client.post(f"/api/sos/{made['id']}/resolve", {'passenger': made['passenger']})
    assert ok.status == 200 and ok.body['status'] == 'resolved' and ok.body['resolved_at'] is not None
    assert app.client.post(f"/api/sos/{made['id']}/resolve", {'passenger': made['passenger']}).status == 409
    assert raise_sos(app).status == 201 and app.db.count('sos') == 2
    assert app.db.count('audit', "action = 'sos-ended'") == 1


def test_four_simultaneous_taps_make_one_row(app):
    gate, answers = threading.Barrier(4), []

    def tap():
        gate.wait()
        answers.append(raise_sos(app, 2).status)
    threads = [threading.Thread(target=tap) for _ in range(4)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert sorted(answers) == [200, 200, 200, 201] and app.db.count('sos', 'ride_id = 2') == 1


def test_a_service_bug_is_a_500_with_a_reference_not_a_stack_trace(app):
    app.db.execute('DROP INDEX sos_one_active')
    app.db.execute('DROP TABLE sos')                              # the migration "was never run"
    resp = raise_sos(app)
    assert resp.status == 500 and resp.body['ref'] and 'sqlite' not in str(resp.body).lower() and 'sos' not in str(resp.body)


# ---- front end -------------------------------------------------------------------------------
def test_first_tap_only_asks(app):
    ride = app.service.get_ride(1)
    assert app.screen.sos_button.click(ride) is None
    assert app.client.requests == 0 and 'confirm' in app.screen.banner and app.db.count('sos') == 0


def test_second_tap_sends_and_the_screen_does_not_overpromise(app):
    ride = app.service.get_ride(1)
    app.screen.sos_button.click(ride)
    resp = app.screen.sos_button.click(ride)
    assert resp.status == 201 and app.screen.sos['id'] == resp.body['id']
    assert '112' in app.screen.banner and 'alerts nobody' in app.screen.banner
    assert app.screen.sos_button.enabled                          # usable again after the response


def test_screen_shows_the_server_reason_when_refused(app):
    ride = dict(app.service.get_ride(1), passenger='Somebody Else')
    app.screen.sos_button.click(ride)
    app.screen.sos_button.click(ride)
    assert app.screen.banner == 'You are not allowed to do that.' and app.screen.sos is None


def test_i_am_safe_ends_it(app):
    ride = app.service.get_ride(1)
    app.screen.sos_button.click(ride)
    app.screen.sos_button.click(ride)
    app.screen.resolve_button.click(ride)
    assert app.screen.sos is None and app.screen.banner == 'SOS ended.'
    assert app.db.query('SELECT status FROM sos')[0]['status'] == 'resolved'


# ---- regression: the old features did not move -----------------------------------------------
def test_booking_listing_and_assignment_behave_as_before(app):
    app.screen.form.update(passenger='Aoife', pickup='UCC', destination='Cork Airport', km='5.8')
    booked = app.screen.book_button.click().result()
    assert booked.status == 201 and booked.body['fare_cents'] == ai.fare_cents(5.8)
    page = app.client.get('/api/rides?limit=3')
    assert page.status == 200 and page.headers['X-Total-Count'] == '5' and len(page.body['items']) == 3
    assert app.client.get('/api/rides/1').body['status'] == 'assigned'
    assert app.client.post('/api/rides/1/complete').status == 200


def test_a_plain_app_without_the_feature_has_no_sos_routes():
    with ai.App(drivers=2, rides=1, assigned=True) as plain:
        assert plain.client.post('/api/rides/1/sos', {}).status == 404


def test_the_lab_runs_and_its_internal_assertions_hold(capsys):
    out = ff.lab19()
    assert 'Traceback' not in capsys.readouterr().out
    assert out['statuses'] == [409, 403, 422, 422, 404, 201, 200, 403, 200, 409]
    assert out['race'] == [200, 200, 200, 201]
    assert out['phone'] == ['refused', 'active', 'same record', 'refused', 'resolved']
