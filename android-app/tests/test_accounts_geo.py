import datetime as dt
import math
import pytest
from atlas_go import accounts as acc
from atlas_go import geo
from atlas_go import intelligence as ai


def test_password_hash_roundtrip_and_salt():
    a, b = acc.hash_password('drive2026'), acc.hash_password('drive2026')
    assert a['salt'] != b['salt'] and a['hash'] != b['hash']
    assert a['iterations'] == acc.PBKDF2_ITERATIONS
    assert acc.verify_password('drive2026', a)
    assert not acc.verify_password('drive2027', a)
    assert not acc.verify_password('x', {'salt': 'zz'})


@pytest.mark.parametrize('raw,clean', [('087 123 4567', '+353871234567'), ('+353 (86) 765-4321', '+353867654321'),
                                       ('0044 20 7946 0958', '+442079460958')])
def test_phone_normalisation(raw, clean):
    assert acc.clean_phone(raw) == clean


@pytest.mark.parametrize('bad', ['', '123', '+0123456789', 'phone'])
def test_phone_rejected(bad):
    with pytest.raises(ValueError):
        acc.clean_phone(bad)


def test_email_password_plate_licence_business():
    assert acc.clean_email('  Name@Example.IE ') == 'name@example.ie'
    for bad in ('name', 'a@b', 'a b@c.ie', '@c.ie'):
        with pytest.raises(ValueError):
            acc.clean_email(bad)
    for bad in ('short1', 'lettersonly', '12345678'):
        with pytest.raises(ValueError):
            acc.check_password(bad)
    assert acc.check_password('ride2026x') == 'ride2026x'
    assert acc.clean_plate('241 c 1234') == '241-C-1234'
    assert acc.clean_plate('12-d-5678') == '12-D-5678'
    for bad in ('ABC123', '2411-C-1', '241-CCC-1'):
        with pytest.raises(ValueError):
            acc.clean_plate(bad)
    assert acc.clean_licence('a 12345') == 'A12345'
    assert acc.clean_business('fbo-12345') == 'FBO-12345'
    with pytest.raises(ValueError):
        acc.clean_licence('a1')


@pytest.mark.parametrize('raw,cents', [('8.50', 850), ('€3,60', 360), ('12', 1200), ('0.5', 50), ('200', 20000)])
def test_price_parsing(raw, cents):
    assert acc.parse_price(raw) == cents


@pytest.mark.parametrize('bad', ['', 'abc', '0.49', '200.01', '8.505', '-2'])
def test_price_rejected(bad):
    with pytest.raises(ValueError):
        acc.parse_price(bad)


def test_names_and_public_view():
    assert acc.clean_name('  Aoife   Murphy ') == 'Aoife Murphy'
    with pytest.raises(ValueError):
        acc.clean_name('A')
    record = dict(id='U-1', name='A', **acc.hash_password('abc12345'))
    assert set(acc.public_view(record)) == {'id', 'name'}


def test_haversine_and_eta():
    ucc, airport = geo.PLACE_COORDS[0], geo.PLACE_COORDS[3]
    km = geo.haversine_km(ucc, airport)
    assert 5.0 < km < 5.6
    assert geo.haversine_km(ucc, ucc) == 0
    assert geo.eta_minutes(ucc, airport) == round(km / geo.SPEED_KMH * 60)
    assert geo.eta_minutes(ucc, ucc) == 1
    assert geo.nearest_place((51.9010, -8.4590))[0] == 2


def test_mercator_roundtrip_and_tiles():
    for point in (geo.CORK, (0.0, 0.0), (60.0, -170.0)):
        x, y = geo.world_px(*point, 13)
        lat, lon = geo.from_world_px(x, y, 13)
        assert math.isclose(lat, point[0], abs_tol=1e-9) and math.isclose(lon, point[1], abs_tol=1e-9)
    # Same tile as the OSM wiki formula: Cork city centre is tile 13/3903/2709
    lat, lon = geo.PLACE_COORDS[1]
    n = 2 ** 13
    expected = (int((lon + 180) / 360 * n), int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n))
    x, y = geo.world_px(lat, lon, 13)
    assert (int(x // 256), int(y // 256)) == expected == (3903, 2709)
    tiles = geo.tile_range(geo.CORK, 13, 600, 400)
    assert expected in tiles and 6 <= len(tiles) <= 12
    center, zoom = geo.fit_zoom(geo.PLACE_COORDS, 600, 600)
    assert 11 <= zoom <= 13 and geo.valid_point(center)


def test_live_ride_positions_follow_time():
    ride = dict(pickup=0, destination=1, stage=0, live=dict(start=[51.9000, -8.4800], t=1000.0))
    start, pickup, dest = geo.ride_legs(ride)
    leg = geo.leg_seconds(start, pickup)
    assert geo.ride_position(ride, 1000.0) == (start, 0.0)
    mid, f = geo.ride_position(ride, 1000.0 + leg / 2)
    assert math.isclose(f, .5) and geo.haversine_km(mid, start) < geo.haversine_km(start, pickup)
    assert geo.ride_position(ride, 1000.0 + leg * 3)[1] == 1.0
    assert 'arrives' in geo.ride_eta_text(ride, 1000.0)
    ride['pending'] = True
    assert geo.ride_position(ride, 5000.0) == (start, 0.0)


def test_live_order_positions():
    order = dict(address=0, stage=0, live=dict(kitchen=list(geo.KITCHEN_COORDS[0]), t=0.0))
    assert geo.order_position(order, 10, 12)[0] is None
    order['stage'] = 1
    pos, f = geo.order_position(order, 0, 12)
    assert pos == geo.KITCHEN_COORDS[0] and f == 0
    order['stage'] = 2
    assert geo.order_position(order, 100, 12) == (geo.PLACE_COORDS[0], 1.0)


def test_registered_driver_candidate_and_dispatch():
    account = dict(id='U-9', name='Siobhan Driver', driver=dict(vehicle='Corolla', offered=0, accepted=0))
    c = ai.registered_candidate(account, geo.PLACE_COORDS[0], geo.PLACE_COORDS[0], 0.0, False)
    assert c.eta == 1 and c.accept == .9 and c.account == 'U-9'
    chosen, why = ai.choose(0, extra=[c])
    assert chosen.account == 'U-9' and 'nearest' in why
    chosen, _ = ai.choose(0, extra=[c], exclude=['U-9'])
    assert chosen.name == 'Morgan'
    far = ai.registered_candidate(account, geo.PLACE_COORDS[3], geo.PLACE_COORDS[0], 0.0, False)
    assert ai.choose(0, extra=[far])[0].name == 'Morgan'


def test_acceptance_model_and_surge_level():
    assert ai.acceptance(0, 0) == .9
    assert ai.acceptance(20, 20) > ai.acceptance(0, 0) > ai.acceptance(20, 5)
    assert ai.surge_level(dt.date(2026, 11, 4), 3) == 0.0
    paddy = max(ai.surge_level(dt.date(2026, 3, 17), h) for h in range(24))
    assert 0.5 < paddy <= 1.0


def test_courier_plan_for_seller_prep_times():
    assert ai.courier_plan(0) == ai.courier_plan(0, prep=12)
    for prep in (5, 10, 25, 45, 90):
        plan = ai.courier_plan(5, prep=prep)
        assert plan['courier_wait'] <= max(3, plan['naive_wait']) and plan['dispatch_after'] >= 0
        assert plan['arrive'] == plan['dispatch_after'] + plan['travel']


def test_every_bundled_model_passes_self_test():
    results = ai.self_test(dt.date(2026, 11, 7))
    assert [name for name, _, _ in results] == [name for name, _ in ai.MODELS]
    assert all(ok for _, ok, _ in results), results
