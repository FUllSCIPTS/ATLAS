"""Layer 2 (1.3.0): digital twin, Agents 1-3 and the Guardian, on top of an unchanged Layer 1."""
import datetime as dt
import hashlib
import json
import random
from pathlib import Path
import pytest
from atlas_go import intelligence as ai
from atlas_go import twin
from atlas_go.store import LocalStore

PKG = Path(__file__).resolve().parents[1] / 'atlas_go'
ORDINARY = dt.datetime(2026, 11, 4, 10, 0)
BUSY = dt.datetime(2027, 3, 17, 13, 0)


def test_layer1_source_is_byte_identical_to_1_2_0():
    """Layer 2 must not touch the learned models: these hashes are the 1.2.0 files."""
    expected = {'intelligence.py': '1c3729b0ca6c86ea5258db90a2a90fbc4cc3be2205d51da3ebe890493beb17d8',
                'learned.py': '92221cbe0b713bf7ce522433f71f7ea0867287279500e7afb877ea792b90a846'}
    for name, digest in expected.items():
        assert hashlib.sha256((PKG / name).read_bytes()).hexdigest() == digest, name


def test_layer2_does_not_change_layer1_answers(tmp_path):
    before = [[(c.name, round(p, 12)) for c, p in ai.rank(k)] for k in range(4)]
    s = LocalStore(tmp_path / 'state.json')
    for k in range(4):
        twin.decide_ride(s, k, BUSY)
        twin.agent2(k, BUSY)
    twin.fault_drill(s, 0, BUSY)
    after = [[(c.name, round(p, 12)) for c, p in ai.rank(k)] for k in range(4)]
    assert before == after and ai.self_test(dt.date(2026, 11, 4)) and all(ok for _, ok, _ in ai.self_test(dt.date(2026, 11, 4)))


def test_foresee_reads_layer1_outlook():
    assert twin.ratio_30(ORDINARY) == pytest.approx(1.0)
    assert twin.ratio_30(BUSY) > 2.0
    rows = twin.foresee(BUSY)
    assert [r['place'] for r in rows] == [0, 1, 2, 3] and all(r['free'] >= 1 for r in rows)
    assert rows[1]['pressure'] > rows[3]['pressure']
    assert twin.extra_requests(ORDINARY, 1) == 0 and twin.extra_requests(BUSY, 1) > 20
    # the horizon crosses midnight into the next day without error
    assert twin.ratio_30(dt.datetime(2026, 12, 31, 23, 45)) > 1.0


def test_agent1_chooses_among_layer1_top_three_and_is_deterministic():
    for k in range(4):
        a, b = twin.agent1(k, BUSY), twin.agent1(k, BUSY)
        assert a['choice'] in a['top'] and len(a['rollouts']) == twin.TOP_K
        assert [(c.name, w) for c, w in a['rollouts']] == [(c.name, w) for c, w in b['rollouts']]
        assert a['top'] == [c for c, _ in ai.rank(k)[:3]]
        assert a['elapsed_ms'] < twin.DECISION_BUDGET_MS
    d = twin.agent1(0, ORDINARY)
    assert d['choice'].name == d['layer1'].name == 'Morgan'
    waits = dict((c.name, w) for c, w in d['rollouts'])
    assert waits['Ava'] > 5 * waits['Morgan']        # taking the last car at Mardyke costs the next riders


def test_agent1_overrides_layer1_when_the_twin_sees_the_next_30_minutes():
    close = ai.Candidate('Near', 'Mardyke', 1, .95, .9, True)     # last free car in a zone about to surge
    other = ai.Candidate('Far', 'Douglas', 3, .95, .0, False)
    rng = random.Random(1)
    assert twin.rehearse(close, 3.0, rng) > twin.rehearse(other, 3.0, rng)


def test_agent2_prices_are_capped_and_stable():
    assert all(twin.agent2(k, ORDINARY)['multiplier'] == 1.0 for k in range(4))
    busy = twin.agent2(1, BUSY)
    assert 1.0 < busy['multiplier'] <= twin.PRICE_CAP and busy['move'] and busy['move']['dst'] == 1
    assert len(busy['plans']) == 3 and busy['choice'] in busy['plans']
    for r in [x / 10 for x in range(1, 500)]:
        m = twin.surge_only(r)
        assert 1.0 <= m <= twin.PRICE_CAP and twin.check_price(m, twin.expected_multiplier(r))[0]
        assert abs(twin.surge_only(r + .1) - m) <= twin.MAX_STEP


def test_driver_and_kitchen_hints():
    assert twin.driver_hint(0, ORDINARY)['action'] == 'none'
    hint = twin.driver_hint(0, BUSY)
    assert hint['action'] == 'move' and hint['place'] == 1 and 'capped' in hint['text']
    assert twin.driver_hint(1, BUSY)['action'] == 'stay'
    text = twin.kitchen_hint(ai.courier_plan(0, prep=10))
    assert 'twin ETA' in text and 'ready when the courier walks in' in text


@pytest.mark.parametrize('multiplier,ok', [(1.0, True), (1.4, True), (2.0, True), (4.0, False), (0.8, False),
                                           (2.01, False), (float('nan'), False), ('1.2', False)])
def test_guardian_price_limits(multiplier, ok):
    assert twin.check_price(multiplier, 1.6)[0] is ok


def test_guardian_blocks_bad_dispatch_and_slow_answers():
    d = twin.agent1(0, ORDINARY)
    assert twin.check_dispatch(d)[0]
    outsider = ai.DRIVER_POOLS[0][3]                      # Ciarán: not in Layer 1's top three here
    assert outsider not in d['top']
    assert not twin.check_dispatch(dict(d, choice=outsider))[0]
    assert 'ms' in twin.check_dispatch(dict(d, elapsed_ms=twin.DECISION_BUDGET_MS + 1))[1]
    registered = ai.Candidate('Siobhan', 'Registered', 1, .9, 0, False, 'U-1')
    d2 = dict(d, choice=registered, top=[registered] + d['top'][:2])
    assert not twin.check_dispatch(d2, exclude=['U-1'])[0]
    assert not twin.check_dispatch(d2, online_ids=set())[0]
    assert not twin.check_price(1.2, 1.2, elapsed_ms=10_000)[0]


def test_retest_passes_and_fault_drill_hands_back(tmp_path):
    passed, count = twin.retest_pricing()
    assert passed and count == twin.RETEST_ROLLOUTS
    s = LocalStore(tmp_path / 'state.json')
    log = twin.fault_drill(s, 1, BUSY)
    assert [e['result'] for e in log] == ['blocked', 'fallback', 'retested', 'handed back']
    s.twin_record(log, status=dict(pricing='active'))
    restored = LocalStore(s.path)
    assert restored.twin['blocks'] == 1 and restored.twin['checks'] == 1 and len(restored.twin['log']) == 4


def test_decide_ride_with_layer2_on_off_and_with_a_blocked_agent(tmp_path):
    s = LocalStore(tmp_path / 'state.json')
    on = twin.decide_ride(s, 0, BUSY)
    assert on['layer'] == 2 and on['choice'].name == 'Morgan' and on['multiplier'] == 1.4
    assert [e['result'] for e in on['log']] == ['passed', 'passed'] and len(on['twin']['rollouts']) == 3
    off = twin.decide_ride(s, 0, BUSY, enabled=False)
    assert off['layer'] == 1 and off['multiplier'] == 1.0 and off['twin'] is None and not off['log']
    assert off['choice'] == ai.choose(0)[0] and off['why'] == ai.choose(0)[1]
    s.twin['status']['pricing'] = 'retesting'            # while re-tested, Layer 1's base price is used
    assert twin.decide_ride(s, 0, BUSY)['multiplier'] == 1.0


def test_booking_with_price_and_guardian_log_persists(tmp_path):
    s = LocalStore(tmp_path / 'state.json')
    d = twin.decide_ride(s, 0, BUSY)
    s.book(0, 1, driver='Morgan · ATLAS demo driver', why=d['why'], multiplier=d['multiplier'],
           twin=dict(d['twin'], layer=2), log=d['log'])
    assert s.ride['fare'] == 1200 and s.ride['surge'] == 1.4
    restored = LocalStore(s.path)
    assert restored.ride['twin']['layer1'] == 'Morgan' and restored.twin['checks'] == 2
    restored.advance_ride(cancel=True)
    with pytest.raises(ValueError, match='capped'):
        restored.book(0, 1, multiplier=2.5)
    assert restored.ride is None


def test_shared_rides_ignore_the_price_multiplier(tmp_path):
    s = LocalStore(tmp_path / 'state.json')
    s.book(0, 1, offer_id='pool-1', multiplier=1.4)
    assert s.ride['fare'] == 490 and 'surge' not in s.ride


def test_twin_state_validation_and_legacy_files(tmp_path):
    path = tmp_path / 'state.json'
    path.write_text(json.dumps(dict(cart={}, history=[], ride=None, order=None, ui={}, seats={})))
    assert LocalStore(path).twin == twin.default_state()                     # 1.2.0 file
    for bad in ({'enabled': 'yes'}, dict(twin.default_state(), status={'dispatch': 'gone', 'pricing': 'active'}),
                dict(twin.default_state(), log=[{'t': 1}]), dict(twin.default_state(), checks=-1)):
        path.write_text(json.dumps(dict(cart={'bowl': 1}, history=[], ride=None, order=None, ui={}, seats={}, twin=bad)))
        s = LocalStore(path)
        assert s.twin == twin.default_state() and s.cart.items == {'bowl': 1}     # only Layer 2 state is reset
    path.write_text(json.dumps(dict(cart={}, history=[dict(id='R-1', pickup=0, destination=1, shared=False, party=1,
                                                           offer=None, driver='M', fare=860, stage=2, surge=3.0)],
                                    ride=None, order=None, ui={}, seats={})))
    assert not LocalStore(path).history                                        # out-of-cap price is refused


def test_log_is_bounded_and_switch_is_logged(tmp_path):
    s = LocalStore(tmp_path / 'state.json')
    s.twin_record([twin.entry('Agent 1', f'x{k}', 'passed') for k in range(100)])
    assert len(s.twin['log']) == twin.LOG_LIMIT and s.twin['checks'] == 100
    s.set_layer2(False)
    assert not LocalStore(s.path).twin['enabled'] and s.twin['log'][-1]['result'] == 'info'
    with pytest.raises(ValueError):
        s.twin_record([], status=dict(pricing='broken'))


def test_mirror_fidelity(tmp_path):
    s = LocalStore(tmp_path / 'state.json')
    m = twin.mirror(s, 1_800_000_000.0)
    assert m['fidelity'] == 1.0 and m['drivers'] == 16
    s.register('driver', 'Siobhan Driver', 'd@atlas.ie', '087 123 4567', 'drive2026', vehicle='Toyota Corolla',
               plate='241-C-1234', licence='A12345', seats='4', base=0)
    s.set_online(True)
    m = twin.mirror(s, 1_800_000_000.0)
    assert m['drivers'] == 17 and 0.9 < m['fidelity'] < 1.0               # registered driver: area only
    s.update_location((51.8935, -8.4921))
    assert twin.mirror(s, 1_800_000_000.0)['fidelity'] == 1.0


def test_layer2_self_test_passes():
    results = twin.self_test()
    assert len(results) == 4 and all(ok for _, ok, _ in results), results
