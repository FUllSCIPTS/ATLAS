"""Pre-booked rides and SOS (1.6.0): pickup-time rules, seat holds, dispatch through the ordinary
booking path, missed and failed bookings, the trusted contact, SOS records and their integrity."""
import datetime as dt
import json
import pytest
from atlas_go import payments as pay
from atlas_go import safety
from atlas_go.domain import PLACES, fare
from atlas_go.store import LocalStore
from test_roles import T0, driver, passenger, seller

HOUR = 3600
GOOD, NO_FUNDS = pay.SANDBOX_IBANS['approved'], pay.SANDBOX_IBANS['insufficient_funds']


def store(tmp_path):
    return LocalStore(tmp_path / 'state.json')


def offer(s, offer_id):
    return next(o for o in s.offers if o.id == offer_id)


def matching_offer(s, party=1):
    return next((o, a, b) for o in s.offers for a in range(4) for b in range(4) if a != b and o.matches(a, b, party))


# ---------------------------------------------------------------------------- pure rules
@pytest.mark.parametrize('ahead,ok', [(0, False), (14 * 60, False), (15 * 60, True), (HOUR, True),
                                      (7 * 24 * HOUR, True), (7 * 24 * HOUR + 1, False), (-HOUR, False)])
def test_pickup_time_window(ahead, ok):
    if ok:
        assert safety.check_when(T0 + ahead, T0) == int(T0 + ahead)
    else:
        with pytest.raises(ValueError):
            safety.check_when(T0 + ahead, T0)


@pytest.mark.parametrize('bad', [None, '18:00', True, [T0]])
def test_pickup_time_must_be_a_number(bad):
    with pytest.raises(ValueError, match='Choose a pickup time'):
        safety.check_when(bad, T0)


@pytest.mark.parametrize('clock', ['2026-11-17 09:00', '2026-11-17 17:50', '2026-11-17 23:59', '2026-12-31 23:30'])
def test_every_offered_time_is_bookable(clock):
    now = dt.datetime.strptime(clock, '%Y-%m-%d %H:%M')
    options = safety.when_options(now)
    assert len(options) >= 4 and len({label for label, _ in options}) == len(options)
    for _, at in options:
        safety.check_when(at.timestamp(), now.timestamp())


def test_emergency_links():
    assert safety.dial_uri() == 'tel:112'
    with pytest.raises(ValueError):
        safety.dial_uri('112;wait')
    uri = safety.sms_uri('+353871234567', 'SOS & help? yes\n#1')
    assert uri.startswith('sms:+353871234567?body=') and '&' not in uri and ' ' not in uri and '#' not in uri and '\n' not in uri
    with pytest.raises(ValueError):
        safety.sms_uri('0871234567', 'x')
    assert safety.map_link((51.89852, -8.47561)) == 'https://www.openstreetmap.org/?mlat=51.89852&mlon=-8.47561#map=17/51.89852/-8.47561'
    assert safety.open_uri('tel:112') is False          # no Android here: nothing is opened


# ---------------------------------------------------------------------------- pre-booking
def test_prebook_needs_a_passenger_account(tmp_path):
    s = store(tmp_path)
    with pytest.raises(ValueError, match='Create an account'):
        s.prebook(0, 1, T0 + HOUR, now=T0)
    driver(s)
    with pytest.raises(ValueError, match='as a passenger'):
        s.prebook(0, 1, T0 + HOUR, now=T0)
    assert s.prebooks == []


def test_solo_prebook_fixes_the_ordinary_fare_and_survives_restart(tmp_path):
    s = store(tmp_path)
    passenger(s)
    p = s.prebook(0, 2, T0 + 2 * HOUR, comfort=True, now=T0)
    assert p['fare'] == fare(0, 2, True) and p['status'] == 'scheduled' and p['offer'] is None and p['party'] == 1
    assert s.ride is None and s.payments == []                     # nothing is charged or dispatched yet
    again = store(tmp_path)
    assert again.my_prebooks() == [p]


def test_prebook_limits(tmp_path):
    s = store(tmp_path)
    passenger(s)
    with pytest.raises(ValueError, match='different'):
        s.prebook(1, 1, T0 + HOUR, now=T0)
    with pytest.raises(ValueError, match='15 minutes'):
        s.prebook(0, 1, T0 + 60, now=T0)
    with pytest.raises(ValueError, match='Link a bank account'):
        s.prebook(0, 1, T0 + HOUR, pay_by_bank=True, now=T0)
    s.prebook(0, 1, T0 + HOUR, now=T0)
    with pytest.raises(ValueError, match='within 30 minutes'):
        s.prebook(0, 1, T0 + HOUR + 600, now=T0)
    for n in (1, 2):
        s.prebook(0, 1, T0 + (n + 1) * HOUR, now=T0)
    with pytest.raises(ValueError, match='three pre-booked rides'):
        s.prebook(0, 1, T0 + 5 * HOUR, now=T0)
    assert [p['when'] for p in s.my_prebooks()] == [int(T0 + (n + 1) * HOUR) for n in range(3)]


def test_shared_prebook_holds_seats_and_cancel_releases_them(tmp_path):
    s = store(tmp_path)
    passenger(s)
    o, a, b = matching_offer(s, 2)
    free = o.seats
    p = s.prebook(a, b, T0 + HOUR, offer_id=o.id, party=2, comfort=True, now=T0)
    assert p['fare'] == o.price * 2 and p['comfort'] is False and offer(s, o.id).seats == free - 2
    assert offer(store(tmp_path), o.id).seats == free - 2          # the hold is saved
    with pytest.raises(ValueError, match='does not match'):
        s.prebook(b, a, T0 + 3 * HOUR, offer_id=o.id, now=T0)
    s.cancel_prebook(p['id'])
    assert offer(s, o.id).seats == free and s.my_prebooks() == []
    assert s.my_prebooks(upcoming=False)[0]['status'] == 'cancelled'
    with pytest.raises(ValueError, match='no longer scheduled'):
        s.cancel_prebook(p['id'])
    assert offer(s, o.id).seats == free                            # not released twice


def test_only_the_owner_can_cancel(tmp_path):
    s = store(tmp_path)
    passenger(s)
    p = s.prebook(0, 1, T0 + HOUR, now=T0)
    s.logout()
    passenger(s, 'other@atlas.ie')
    assert s.my_prebooks() == []
    with pytest.raises(ValueError, match='no longer scheduled'):
        s.cancel_prebook(p['id'])
    with pytest.raises(ValueError, match='no longer scheduled'):
        s.dispatch_prebook(p['id'], now=T0 + HOUR)
    assert s.prebooks[0]['status'] == 'scheduled'


def test_dispatch_happens_ten_minutes_before_pickup(tmp_path):
    s = store(tmp_path)
    passenger(s)
    p = s.prebook(0, 2, T0 + HOUR, now=T0)
    assert s.due_prebook(T0 + HOUR - 601) is None
    assert s.due_prebook(T0 + HOUR - 600)['id'] == p['id']
    assert s.dispatch_prebook(p['id'], now=T0 + HOUR - 600, driver='Test driver', why='nearest', multiplier=1.0) is True
    assert s.ride['prebook'] == p['id'] and s.ride['fare'] == p['fare'] and s.ride['driver'] == 'Test driver'
    assert s.prebooks[0]['status'] == 'dispatched' and s.prebooks[0]['ride'] == s.ride['id']
    assert s.due_prebook(T0 + HOUR) is None and s.my_prebooks() == []
    LocalStore(tmp_path / 'state.json')                             # the saved file is valid


def test_dispatch_waits_for_an_active_ride_to_finish(tmp_path):
    s = store(tmp_path)
    passenger(s)
    p = s.prebook(0, 2, T0 + HOUR, now=T0)
    s.book(1, 3, now=T0 + HOUR - 900)
    assert s.due_prebook(T0 + HOUR) is None
    with pytest.raises(ValueError, match='active ride first'):
        s.dispatch_prebook(p['id'], now=T0 + HOUR)
    s.advance_ride(cancel=True, now=T0 + HOUR)
    assert s.due_prebook(T0 + HOUR)['id'] == p['id']


def test_shared_dispatch_reuses_the_held_seats(tmp_path):
    s = store(tmp_path)
    passenger(s)
    o, a, b = matching_offer(s, 2)
    free = o.seats
    p = s.prebook(a, b, T0 + HOUR, offer_id=o.id, party=2, now=T0)
    assert s.dispatch_prebook(p['id'], now=T0 + HOUR - 300) is True
    assert s.ride['shared'] and s.ride['offer'] == o.id and s.ride['party'] == 2 and s.ride['fare'] == o.price * 2
    assert offer(s, o.id).seats == free - 2                         # held once, not twice
    s.advance_ride(cancel=True, now=T0 + HOUR)
    assert offer(s, o.id).seats == free


def test_bank_is_asked_at_dispatch_and_a_decline_charges_nothing(tmp_path):
    s = store(tmp_path)
    passenger(s)
    s.link_bank('ride2026x', 'Aoife Rider', GOOD, consent=True, now=T0)
    o, a, b = matching_offer(s)
    free = o.seats
    ok = s.prebook(a, b, T0 + HOUR, offer_id=o.id, pay_by_bank=True, now=T0)
    assert s.payments == []                                         # no authorisation while it waits
    s.link_bank('ride2026x', 'Aoife Rider', NO_FUNDS, consent=True, now=T0 + 60)
    assert s.dispatch_prebook(ok['id'], now=T0 + HOUR - 300) is False
    failed = s.my_prebooks(upcoming=False)[0]
    assert failed['status'] == 'failed' and failed['reason'] and s.ride is None
    assert offer(s, o.id).seats == free and not any(p['status'] in ('authorised', 'captured') for p in s.payments)
    s.link_bank('ride2026x', 'Aoife Rider', GOOD, consent=True, now=T0 + 120)
    second = s.prebook(0, 2, T0 + 3 * HOUR, pay_by_bank=True, now=T0)
    assert s.dispatch_prebook(second['id'], now=T0 + 3 * HOUR - 60) is True
    payment = next(p for p in s.payments if p['id'] == s.ride['payment'])
    assert payment['status'] == 'authorised' and payment['amount'] == second['fare']
    LocalStore(tmp_path / 'state.json')


def test_missed_prebook_releases_seats(tmp_path):
    s = store(tmp_path)
    passenger(s)
    o, a, b = matching_offer(s)
    free = o.seats
    p = s.prebook(a, b, T0 + HOUR, offer_id=o.id, now=T0)
    s.logout()
    assert s.tick(T0 + HOUR + safety.GRACE) is False and s.prebooks[0]['status'] == 'scheduled'
    assert s.tick(T0 + HOUR + safety.GRACE + 1) is True
    assert s.prebooks[0]['status'] == 'missed' and s.prebooks[0]['id'] == p['id'] and offer(s, o.id).seats == free
    assert s.tick(T0 + HOUR + safety.GRACE + 2) is False


def test_delete_account_removes_prebooks_contact_and_sos(tmp_path):
    s = store(tmp_path)
    passenger(s)
    o, a, b = matching_offer(s)
    free = o.seats
    s.prebook(a, b, T0 + HOUR, offer_id=o.id, now=T0)
    s.set_trusted('Niamh Murphy', '087 123 4567')
    s.book(0, 2, now=T0)
    s.raise_sos(now=T0 + 5)
    s.advance_ride(cancel=True, now=T0 + 10)
    s.delete_account('ride2026x')
    raw = (tmp_path / 'state.json').read_text()
    assert s.prebooks == [] and s.sos == [] and offer(s, o.id).seats == free
    assert 'Niamh' not in raw and '+353871234567' not in raw
    LocalStore(tmp_path / 'state.json')


def test_finished_prebooks_are_trimmed(tmp_path):
    s = store(tmp_path)
    passenger(s)
    for n in range(safety.KEEP_FINISHED + 4):
        p = s.prebook(0, 1, T0 + (n + 1) * HOUR, now=T0)
        s.cancel_prebook(p['id'])
    assert len(s.prebooks) == safety.KEEP_FINISHED
    assert min(p['when'] for p in s.prebooks) == int(T0 + 5 * HOUR)      # the oldest four went


# ---------------------------------------------------------------------------- trusted contact
def test_trusted_contact_rules(tmp_path):
    s = store(tmp_path)
    with pytest.raises(ValueError, match='Create an account'):
        s.set_trusted('Niamh Murphy', '087 123 4567')
    passenger(s)
    assert s.set_trusted(' Niamh   Murphy ', '087 123 4567') == dict(name='Niamh Murphy', phone='+353871234567')
    for name, phone in (('N', '087 123 4567'), ('Niamh Murphy', '12'), ('Niamh Murphy', ''), ('', '087 123 4567')):
        with pytest.raises(ValueError):
            s.set_trusted(name, phone)
    assert store(tmp_path).user['trusted']['phone'] == '+353871234567'
    assert s.set_trusted('', '') is None and 'trusted' not in s.user


# ---------------------------------------------------------------------------- SOS
def test_sos_needs_a_ride(tmp_path):
    s = store(tmp_path)
    passenger(s)
    with pytest.raises(ValueError, match='call 112'):
        s.raise_sos(now=T0)
    assert s.sos == []


def test_passenger_sos_records_time_place_and_ride(tmp_path):
    s = store(tmp_path)
    user = passenger(s)
    s.book(0, 2, now=T0)
    e = s.raise_sos(now=T0 + 30, point=(51.9001234, -8.4701234))
    assert e['account'] == user['id'] and e['role'] == 'passenger' and e['ride'] == s.ride['id'] and e['at'] == int(T0 + 30)
    assert e['point'] == [51.90012, -8.47012] and e['source'] == 'device' and e['status'] == 'active' and e['shared'] is False
    assert s.raise_sos(now=T0 + 40) is e and len(s.sos) == 1          # one SOS per ride
    assert store(tmp_path).active_sos()['id'] == e['id']             # it survives a restart


def test_sos_without_location_uses_the_route_position(tmp_path):
    s = store(tmp_path)
    passenger(s)
    s.book(0, 2, now=T0)
    for bad in (None, (999, 0), ('a', 'b')):
        s.sos.clear()
        e = s.raise_sos(now=T0 + 30, point=bad)
        assert e['source'] == 'route' and 51 < e['point'][0] < 53 and -9.5 < e['point'][1] < -7.5


def test_guest_can_raise_and_end_an_sos(tmp_path):
    s = store(tmp_path)
    s.book(0, 2, now=T0)
    e = s.raise_sos(now=T0 + 5)
    assert e['account'] is None and e['role'] == 'passenger'
    s.resolve_sos(e['id'], now=T0 + 60)
    assert s.sos[0]['status'] == 'resolved' and s.sos[0]['resolved'] == int(T0 + 60) and s.active_sos() is None


def test_ending_an_sos_needs_the_account_password(tmp_path):
    s = store(tmp_path)
    passenger(s)
    s.book(0, 2, now=T0)
    e = s.raise_sos(now=T0 + 5)
    for wrong in ('', 'nope12345'):
        with pytest.raises(ValueError, match='not correct'):
            s.resolve_sos(e['id'], wrong)
    assert s.active_sos()['id'] == e['id']
    s.mark_sos_shared(e['id'])
    s.resolve_sos(e['id'], 'ride2026x', now=T0 + 90)
    assert s.active_sos() is None and s.my_sos()[0]['shared'] is True
    with pytest.raises(ValueError, match='already ended'):
        s.resolve_sos(e['id'], 'ride2026x')
    s.advance_ride(cancel=True, now=T0 + 100)
    s.book(0, 2, now=T0 + 200)
    assert s.raise_sos(now=T0 + 210)['id'] != e['id']                # a new ride can raise a new one


def test_driver_sos_and_privacy_between_accounts(tmp_path):
    s = store(tmp_path)
    d = driver(s)
    s.logout()
    passenger(s)
    s.book(0, 2, driver='Siobhan Driver · registered driver', driver_id=d['id'], now=T0)
    mine = s.raise_sos(now=T0 + 5)
    s.logout()
    s.login('d@atlas.ie', 'drive2026', now=T0 + 6)
    assert s.active_sos() is None and s.my_sos() == []               # the driver cannot see the passenger's SOS
    with pytest.raises(ValueError, match='not found'):
        s.resolve_sos(mine['id'], 'drive2026')
    theirs = s.raise_sos(now=T0 + 10)
    assert theirs['role'] == 'driver' and theirs['account'] == d['id'] and theirs['id'] != mine['id']
    assert len(s.sos) == 2


def test_other_roles_cannot_raise_an_sos_for_someone_elses_ride(tmp_path):
    s = store(tmp_path)
    passenger(s)
    s.book(0, 2, now=T0)
    s.logout()
    seller(s)
    with pytest.raises(ValueError, match='during a ride'):
        s.raise_sos(now=T0 + 5)


def test_sos_message_says_what_a_helper_needs():
    event = dict(id='S-1', account='a', ride='R-1', role='passenger', at=int(T0), point=[51.89852, -8.47561],
                 source='device', status='active', shared=False)
    ride = dict(pickup=0, destination=2, driver='Maeve · ATLAS demo driver')
    text = safety.sos_message(event, 'Aoife Rider', ride, PLACES)
    assert 'Aoife Rider' in text and PLACES[0] in text and PLACES[2] in text and 'Maeve' in text
    assert 'mlat=51.89852' in text and '112' in text and len(text) < 480
    assert 'An ATLAS Go user' in safety.sos_message(event, '', None, PLACES)
    assert 'Driving from' in safety.sos_message(dict(event, role='driver'), 'Siobhan', ride, PLACES)


# ---------------------------------------------------------------------------- integrity of the saved file
def tamper(tmp_path, change):
    path = tmp_path / 'state.json'
    data = json.loads(path.read_text())
    change(data)
    path.write_text(json.dumps(data))
    return LocalStore(path)


def prepared(tmp_path):
    s = store(tmp_path)
    passenger(s)
    o, a, b = matching_offer(s)
    s.prebook(a, b, T0 + HOUR, offer_id=o.id, now=T0)
    s.set_trusted('Niamh Murphy', '087 123 4567')
    s.book(0, 2, now=T0)
    s.raise_sos(now=T0 + 5)
    return s, o


@pytest.mark.parametrize('change', [
    lambda d: d['prebooks'][0].update(fare=0),
    lambda d: d['prebooks'][0].update(fare=1.5),
    lambda d: d['prebooks'][0].update(status='paid'),
    lambda d: d['prebooks'][0].update(destination=d['prebooks'][0]['pickup']),
    lambda d: d['prebooks'][0].update(account='nobody'),
    lambda d: d['prebooks'][0].update(offer='pool-9'),
    lambda d: d['prebooks'][0].update(party=5),
    lambda d: d['prebooks'].append(dict(d['prebooks'][0])),
    lambda d: d['seats'].update({d['prebooks'][0]['offer']: 99}),          # seats "held" but not taken
    lambda d: d.update(prebooks='none'),
    lambda d: d['sos'][0].update(point=[251.0, 0.0]),
    lambda d: d['sos'][0].update(status='resolved'),                        # resolved without a time
    lambda d: d['sos'][0].update(role='seller'),
    lambda d: d['sos'][0].update(shared='yes'),
    lambda d: d['sos'].append(dict(d['sos'][0])),
    lambda d: d['accounts'][0].update(trusted=dict(name='Niamh', phone='0871234567')),
    lambda d: d['accounts'][0].update(trusted='Niamh'),
    lambda d: d['ride'].update(prebook=7),
])
def test_tampered_prebook_or_sos_state_is_quarantined(tmp_path, change):
    prepared(tmp_path)
    s = tamper(tmp_path, change)
    assert s.prebooks == [] and s.sos == [] and s.accounts == []
    assert (tmp_path / 'state.invalid.json').exists()


def test_state_from_1_5_0_loads(tmp_path):
    s, _ = prepared(tmp_path)
    s.advance_ride(cancel=True, now=T0 + 10)
    old = tamper(tmp_path, lambda d: (d.pop('prebooks'), d.pop('sos'), d['accounts'][0].pop('trusted')))
    assert old.accounts and old.prebooks == [] and old.sos == [] and not (tmp_path / 'state.invalid.json').exists()
