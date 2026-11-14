"""Shared rides (1.3.0): a rider is already in the car. The new rider waits for the driver,
boards, and is dropped only after the earlier rider has been dropped."""
import json
import pytest
from atlas_go import geo
from atlas_go.store import LocalStore

T0 = 1_800_000_000.0


def shared(tmp_path, offer='pool-1', party=1, now=T0):
    s = LocalStore(tmp_path / 'state.json')
    pickup, destination = {'pool-1': (0, 1), 'pool-2': (0, 1), 'pool-3': (1, 3), 'pool-4': (2, 0)}[offer]
    s.book(pickup, destination, offer_id=offer, party=party, now=now)
    return s


@pytest.mark.parametrize('offer', ['pool-1', 'pool-2', 'pool-3', 'pool-4'])
def test_every_carpool_has_a_rider_on_board_who_gets_out_on_your_route(tmp_path, offer):
    s = shared(tmp_path, offer)
    ride = s.ride
    co = ride['co']
    assert geo.has_co_rider(ride) and geo.last_stage(ride) == 3
    assert co['name'] and not co['dropped'] and co['point'] == list(geo.ZONE_COORDS[co['drop']])
    assert ride['live']['start'] == list(geo.ZONE_COORDS[co['boarded']])
    # The earlier rider's stop lies between your pickup and your destination.
    pickup, dest = geo.PLACE_COORDS[ride['pickup']], geo.PLACE_COORDS[ride['destination']]
    detour = geo.haversine_km(pickup, co['point']) + geo.haversine_km(co['point'], dest)
    assert detour < 1.6 * geo.haversine_km(pickup, dest) + 1.0


def test_stop_order_previous_rider_dropped_before_new_rider(tmp_path):
    s = shared(tmp_path)
    seen = []
    while s.ride:
        seen.append((s.ride['stage'], s.ride['co']['dropped']))
        s.advance_ride(now=T0 + len(seen))
    assert seen == [(0, False), (1, False), (2, False), (3, True)]
    done = s.history[-1]
    assert done['status'] == 'Completed' and done['co']['dropped'] and done['stage'] == 3


def test_new_rider_cannot_be_dropped_while_earlier_rider_is_on_board(tmp_path):
    s = shared(tmp_path)
    s.advance_ride(now=T0 + 1)
    s.advance_ride(now=T0 + 2)
    s.ride['stage'] = 3                 # jump past the drop without dropping the earlier rider
    with pytest.raises(ValueError, match='dropped first'):
        s.advance_ride(now=T0 + 3)
    assert s.ride is not None and not s.history


def test_tampered_file_with_wrong_drop_order_is_rejected(tmp_path):
    s = shared(tmp_path)
    data = json.loads(s.path.read_text())
    data['ride']['stage'] = 3                       # last leg, but the earlier rider never got out
    s.path.write_text(json.dumps(data))
    restored = LocalStore(s.path)
    assert restored.ride is None and s.path.with_suffix('.invalid.json').exists()


def test_solo_ride_cannot_have_a_fourth_stage(tmp_path):
    s = LocalStore(tmp_path / 'state.json')
    s.book(0, 1, now=T0)
    data = json.loads(s.path.read_text())
    data['ride']['stage'] = 3
    s.path.write_text(json.dumps(data))
    assert LocalStore(s.path).ride is None


@pytest.mark.parametrize('stage', [0, 1, 2, 3])
def test_restart_mid_shared_journey_keeps_stage_and_drop_order(tmp_path, stage):
    s = shared(tmp_path)
    for k in range(stage):
        s.advance_ride(now=T0 + k)
    restored = LocalStore(s.path)
    assert restored.ride['stage'] == stage and restored.ride['co']['dropped'] == (stage == 3)


def test_seats_released_on_arrival_and_on_cancel(tmp_path):
    s = shared(tmp_path, party=2)
    assert s.offers[0].seats == 1
    for k in range(4):
        s.advance_ride(now=T0 + k)
    assert s.ride is None and s.offers[0].seats == 3
    s.book(0, 1, offer_id='pool-1', party=1, now=T0)
    s.advance_ride(now=T0 + 1)
    s.advance_ride(now=T0 + 2)
    s.advance_ride(now=T0 + 3)
    s.advance_ride(cancel=True)
    assert s.offers[0].seats == 3 and s.history[-1]['status'] == 'Cancelled' and s.history[-1]['co']['dropped']


def test_live_positions_follow_the_stop_order(tmp_path):
    s = shared(tmp_path)
    ride = s.ride
    start, pickup, dest = geo.ride_legs(ride)
    drop = geo.co_drop_point(ride)
    assert geo.ride_position(ride, T0)[0] == pytest.approx(start)
    assert 'Ciara is on board' in geo.ride_eta_text(ride, T0)
    s.advance_ride(now=T0)
    s.advance_ride(now=T0)          # stage 2: from your pickup to the earlier rider's stop
    pos, f = geo.ride_position(s.ride, T0 + geo.leg_seconds(pickup, drop) / 2)
    assert f == pytest.approx(.5, abs=.01)
    assert geo.haversine_km(pos, pickup) == pytest.approx(geo.haversine_km(pos, drop), rel=.05)
    assert geo.ride_eta_text(s.ride, T0).startswith('Dropping Ciara at Grand Parade first')
    s.advance_ride(now=T0)          # stage 3: a short stop while Ciara gets out, then on to you
    assert geo.ride_position(s.ride, T0 + 1)[0] == pytest.approx(drop)
    end, f = geo.ride_position(s.ride, T0 + geo.BOARD_SECONDS / 2 + geo.leg_seconds(drop, dest) + 1)
    assert f == 1.0 and end == pytest.approx(dest)
    assert 'to your destination' in geo.ride_eta_text(s.ride, T0)


def test_time_lapse_runs_all_four_stages_without_skipping_the_drop(tmp_path):
    s = shared(tmp_path)
    t, order = T0, []
    for _ in range(400):
        t += 1.0
        if s.tick(now=t) and s.ride:
            order.append((s.ride['stage'], s.ride['co']['dropped']))
        if not s.ride:
            break
    assert s.ride is None and s.history[-1]['status'] == 'Completed'
    assert order == [(1, False), (2, False), (3, True)]


def test_legacy_shared_ride_from_1_2_0_still_has_three_stages(tmp_path):
    path = tmp_path / 'state.json'
    path.write_text(json.dumps(dict(cart={}, history=[], order=None, ui={}, seats={'pool-1': 2},
                                    ride=dict(id='R-1', pickup=0, destination=1, shared=True, party=1, offer='pool-1',
                                              driver='Alex · Electric hatchback', fare=490, stage=1,
                                              passenger=None, driver_id=None, pending=False,
                                              live=dict(start=[51.8895, -8.4981], t=T0)))))
    s = LocalStore(path)
    assert s.ride and not geo.has_co_rider(s.ride) and geo.last_stage(s.ride) == 2
    s.advance_ride(now=T0 + 1)
    s.advance_ride(now=T0 + 2)
    assert s.ride is None and s.history[-1]['status'] == 'Completed' and s.offers[0].seats == 3


def test_map_refits_after_layout_gives_the_real_size():
    """Ride maps are created at Kivy's default 100 x 100 and laid out later; the fit must follow."""
    import os
    if not os.environ.get('DISPLAY'):
        pytest.skip('needs a display (Kivy creates a window); run under xvfb-run')
    os.environ.setdefault('KIVY_NO_ARGS', '1')
    os.environ.setdefault('KIVY_NO_CONSOLELOG', '1')
    pytest.importorskip('kivy')
    from atlas_go.livemap import LiveMap

    class NoTiles:
        listeners, offline = [], True

        def get(self, *_a, **_k):
            return None

    m = LiveMap(tile_loader=NoTiles(), interactive=False)
    points = [geo.ZONE_COORDS['Bishopstown'], geo.PLACE_COORDS[0], geo.PLACE_COORDS[1]]
    m.fit(points)
    small = m.zoom
    m.size = (900, 520)                   # real size after layout
    assert m.zoom > small
    m.zoom_by(-1)                          # the user zooms: no more automatic refits
    zoom = m.zoom
    m.size = (300, 200)
    assert m.zoom == zoom
