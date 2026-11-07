"""Store rules for registered passengers, drivers and food sellers on one device."""
import json
import pytest
from atlas_go import geo
from atlas_go.store import LocalStore

T0 = 1_800_000_000.0


def driver(store, email='d@atlas.ie', base=0, online=True):
    store.register('driver', 'Siobhan Driver', email, '087 123 4567', 'drive2026', vehicle='Toyota Corolla',
                   plate='241-C-1234', licence='A12345', seats='4', base=base)
    if online:
        store.set_online(True)
    return store.user


def seller(store, email='s@atlas.ie', prep='10'):
    store.register('seller', 'Cathal Baker', email, '086 765 4321', 'bread2026', kitchen='Lee Side Bakery',
                   cuisine='Bakery', registration='FBO-1234', place=1, prep=prep)
    return store.user


def passenger(store, email='p@atlas.ie'):
    store.register('passenger', 'Aoife Rider', email, '085 111 2233', 'ride2026x')
    return store.user


def test_register_login_logout_and_lockout(tmp_path):
    s = LocalStore(tmp_path / 'state.json')
    user = passenger(s)
    assert s.session == user['id'] and s.role == 'passenger'
    raw = (tmp_path / 'state.json').read_text()
    assert 'ride2026x' not in raw and user['hash'] in raw
    with pytest.raises(ValueError, match='already exists'):
        passenger(s, 'P@ATLAS.IE')
    s.logout()
    assert s.user is None and not s.signed_in
    for _ in range(5):
        with pytest.raises(ValueError, match='not correct'):
            s.login('p@atlas.ie', 'nope12345', now=T0)
    with pytest.raises(ValueError, match='Too many attempts'):
        s.login('p@atlas.ie', 'ride2026x', now=T0 + 1)
    assert s.login('P@atlas.ie', 'ride2026x', now=T0 + 61)['id'] == user['id']
    assert LocalStore(tmp_path / 'state.json').session == user['id']


def test_role_specific_validation(tmp_path):
    s = LocalStore(tmp_path / 'state.json')
    with pytest.raises(ValueError, match='Irish registration'):
        s.register('driver', 'Siobhan', 'd@atlas.ie', '0871234567', 'drive2026', vehicle='Car X', plate='XYZ',
                   licence='A12345')
    with pytest.raises(ValueError, match='Preparation'):
        s.register('seller', 'Cathal', 's@atlas.ie', '0871234567', 'bread2026', kitchen='Bake', cuisine='Bakery',
                   registration='FBO-1', prep='2')
    with pytest.raises(ValueError, match='already exists'):
        s.register('seller', 'Cathal', 's@atlas.ie', '0871234567', 'bread2026', kitchen='Marina Pizza',
                   cuisine='Pizza', registration='FBO-1')
    assert not s.accounts and not s.kitchens and s.session is None


def test_registered_driver_ride_lifecycle(tmp_path):
    s = LocalStore(tmp_path / 'state.json')
    d = driver(s)
    s.logout()
    assert s.online_drivers()[0]['id'] == d['id']
    p = passenger(s)
    s.book(0, 1, driver='Siobhan · registered driver', why='closest', driver_id=d['id'],
           start=geo.PLACE_COORDS[0], now=T0)
    assert s.ride['pending'] and s.ride['passenger'] == p['id'] and not s.online_drivers()
    with pytest.raises(ValueError, match='not accepted'):
        s.advance_ride()
    assert not s.tick(T0 + 999)  # registered drivers are never auto-advanced
    s.logout()
    s.login('d@atlas.ie', 'drive2026')
    assert s.driver_job() is s.ride
    s.driver_respond(True, now=T0 + 5)
    assert not s.ride['pending'] and s.user['driver']['accepted'] == 1
    for _ in range(3):
        s.driver_advance(now=T0 + 10)
    assert s.ride is None and s.user['driver']['earnings'] == 860 and s.user['driver']['trips'] == 1
    assert s.my_history()[0]['driver_id'] == d['id']
    assert LocalStore(tmp_path / 'state.json').account(d['id'])['driver']['earnings'] == 860


def test_driver_decline_hands_over(tmp_path):
    s = LocalStore(tmp_path / 'state.json')
    d = driver(s)
    s.logout()
    passenger(s)
    s.book(0, 1, driver='Siobhan · registered driver', driver_id=d['id'], start=geo.PLACE_COORDS[0], now=T0)
    s.logout()
    s.login('d@atlas.ie', 'drive2026')
    with pytest.raises(ValueError):
        s.driver_respond(False)
    s.driver_respond(False, fallback=dict(driver='Morgan · ATLAS demo driver', why='next best',
                                          start=geo.ZONE_COORDS['Western Road']), now=T0)
    assert s.ride['driver_id'] is None and s.ride['declined'] == [d['id']] and not s.ride['pending']
    assert s.user['driver']['offered'] == 1 and s.user['driver']['accepted'] == 0
    assert s.driver_job() is None


def test_only_passengers_book_and_order(tmp_path):
    s = LocalStore(tmp_path / 'state.json')
    driver(s)
    with pytest.raises(ValueError, match='passenger'):
        s.book(0, 1)
    with pytest.raises(ValueError):
        s.checkout(0)


def test_live_simulated_ride_advances_with_time(tmp_path):
    s = LocalStore(tmp_path / 'state.json')
    s.continue_as_guest()
    s.book(0, 1, start=geo.ZONE_COORDS['Western Road'], now=T0)
    start, pickup, dest = geo.ride_legs(s.ride)
    assert not s.tick(T0 + 1)
    assert s.tick(T0 + geo.leg_seconds(start, pickup) + .1) and s.ride['stage'] == 1
    t1 = s.ride['live']['t']
    assert s.tick(t1 + geo.BOARD_SECONDS + .1) and s.ride['stage'] == 2
    t2 = s.ride['live']['t']
    assert s.tick(t2 + geo.leg_seconds(pickup, dest) + .1) and s.ride is None
    assert s.history[-1]['status'] == 'Completed' and s.my_history() == s.history


def test_seller_menu_order_and_courier(tmp_path):
    s = LocalStore(tmp_path / 'state.json')
    seller(s)
    kitchen = s.kitchen_of(s.user)
    assert kitchen['id'] == 3 and kitchen['owner'] == s.session
    assert 3 not in [k.id for k in s.catalog.listed()]  # no dishes yet
    toastie = s.add_dish('Sourdough toastie', 'Cheddar and onion', '8.50')
    coffee = s.add_dish('Flat white', 'Double shot', '3.60')
    with pytest.raises(ValueError, match='already'):
        s.add_dish('flat white', 'again', '3')
    s.archive_dish(coffee)
    assert [d.id for d in s.catalog.menu(3)] == [toastie]
    s.logout()
    passenger(s)
    with pytest.raises(ValueError, match='no longer'):
        s.update_cart('add', coffee)
    s.update_cart('add', toastie)
    s.checkout(1, courier=dict(prep=10, dispatch_after=5), now=T0)
    assert s.order['pending'] and s.order['restaurant'] == 3
    assert not s.tick(T0 + 999)
    with pytest.raises(ValueError, match='not accepted'):
        s.advance_order()
    s.logout()
    s.login('s@atlas.ie', 'bread2026')
    s.seller_accept(now=T0)
    assert not s.tick(T0 + 999)  # cooking stage waits for the seller
    s.seller_ready(now=T0 + 60)
    assert s.order['stage'] == 1
    kitchen_pt, home = tuple(s.order['live']['kitchen']), geo.PLACE_COORDS[1]
    assert s.tick(T0 + 60.1 + geo.leg_seconds(kitchen_pt, home)) and s.order['stage'] == 2
    assert s.tick(T0 + 1000) and s.order is None
    assert s.kitchen_of(s.user)['sales'] == 850 and s.kitchen_of(s.user)['orders'] == 1
    assert len(s.my_history()) == 1


def test_closed_kitchen_and_prep_update(tmp_path):
    s = LocalStore(tmp_path / 'state.json')
    seller(s)
    dish = s.add_dish('Scone', 'Butter and jam', '3')
    s.update_kitchen(open_=False, prep='25')
    assert s.catalog.kitchens[3].prep == 25 and not s.catalog.listed()[3:]
    s.logout()
    s.continue_as_guest()
    with pytest.raises(ValueError, match='closed'):
        s.update_cart('add', dish)


def test_delete_account_keeps_anonymised_history(tmp_path):
    s = LocalStore(tmp_path / 'state.json')
    p = passenger(s)
    s.book(0, 1, now=T0)
    with pytest.raises(ValueError, match='active ride'):
        s.delete_account('ride2026x')
    s.advance_ride(cancel=True)
    with pytest.raises(ValueError, match='Password'):
        s.delete_account('wrong')
    s.delete_account('ride2026x')
    assert s.account(p['id']) is None and s.session is None
    assert s.history[0]['passenger'] == 'deleted'
    assert p['email'] not in (tmp_path / 'state.json').read_text()


def test_deleted_seller_closes_kitchen(tmp_path):
    s = LocalStore(tmp_path / 'state.json')
    seller(s)
    s.add_dish('Scone', 'Butter and jam', '3')
    s.delete_account('bread2026')
    assert s.kitchens[0]['open'] is False and s.kitchens[0]['owner'] == 'deleted'
    assert not [k for k in s.catalog.listed() if k.id == 3]
    assert LocalStore(tmp_path / 'state.json').kitchens[0]['open'] is False


@pytest.mark.parametrize('damage', [
    lambda d: d['accounts'][0].update(role='admin'),
    lambda d: d['accounts'][0].pop('hash'),
    lambda d: d['accounts'].append(dict(d['accounts'][0])),
    lambda d: d.update(session='U-missing'),
    lambda d: d['accounts'][0]['driver'].update(accepted=5),
    lambda d: d['accounts'][0]['driver'].update(location=[200, 0]),
    lambda d: d['kitchens'][0].update(id=1),
    lambda d: d['kitchens'][0]['dishes'][0].update(price=-1),
    lambda d: d['kitchens'][0]['dishes'][0].update(id='k9-1'),
])
def test_damaged_role_state_is_quarantined(tmp_path, damage):
    path = tmp_path / 'state.json'
    s = LocalStore(path)
    driver(s, online=False)
    s.logout()
    seller(s)
    s.add_dish('Scone', 'Butter and jam', '3')
    data = json.loads(path.read_text())
    data['accounts'].sort(key=lambda a: a['role'])  # driver first
    damage(data)
    path.write_text(json.dumps(data))
    restored = LocalStore(path)
    assert not restored.accounts and path.with_suffix('.invalid.json').exists()


def test_v110_state_loads_unchanged(tmp_path):
    path = tmp_path / 'state.json'
    path.write_text(json.dumps(dict(cart={'bowl': 1}, history=[dict(id='R-1', pickup=0, destination=1, shared=False,
                    party=1, offer=None, driver='Morgan', fare=860, stage=2, status='Completed', why='x')],
                    ride=None, order=None, seats={'pool-1': 2}, ui={'screen': 'food', 'outlook_day': 3})))
    s = LocalStore(path)
    assert s.cart.items == {'bowl': 1} and s.offers[0].seats == 2 and len(s.history) == 1
    assert s.ui['screen'] == 'food' and not s.signed_in
    s.continue_as_guest()
    assert s.my_history() == s.history
