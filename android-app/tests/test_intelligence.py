import datetime as dt
import json
import pytest
from atlas_go import intelligence as ai
from atlas_go import learned
from atlas_go.store import LocalStore

D = dt.date


@pytest.mark.parametrize('year,expected', [
    (2025, {D(2025, 1, 1), D(2025, 2, 3), D(2025, 3, 17), D(2025, 4, 21), D(2025, 5, 5), D(2025, 6, 2),
            D(2025, 8, 4), D(2025, 10, 27), D(2025, 12, 25), D(2025, 12, 26)}),
    (2026, {D(2026, 1, 1), D(2026, 2, 2), D(2026, 3, 17), D(2026, 4, 6), D(2026, 5, 4), D(2026, 6, 1),
            D(2026, 8, 3), D(2026, 10, 26), D(2026, 12, 25), D(2026, 12, 26)}),
])
def test_irish_public_holidays(year, expected):
    assert set(ai.public_holidays(year)) == expected


def test_st_brigids_day_friday_rule_and_easter():
    assert D(2030, 2, 1) in ai.public_holidays(2030)          # 1 February 2030 is a Friday
    assert ai.easter_sunday(2027) == D(2027, 3, 28)
    assert ai.jazz_weekend(2026) == {D(2026, 10, 23), D(2026, 10, 24), D(2026, 10, 25)}


@pytest.mark.parametrize('day,hour,kind', [
    (D(2026, 3, 17), 13, 'paddys'), (D(2026, 12, 24), 15, 'xmas_eve'), (D(2026, 12, 31), 23, 'nye'),
    (D(2027, 1, 1), 2, 'nye'), (D(2027, 1, 1), 12, 'new_year'), (D(2026, 10, 24), 21, 'jazz'),
    (D(2026, 10, 31), 20, 'halloween'), (D(2026, 5, 3), 21, 'bh_sunday'), (D(2026, 12, 5), 14, 'xmas_shop'),
    (D(2026, 12, 26), 20, 'stephens'), (D(2026, 11, 5), 8, 'ordinary'),
])
def test_calendar_context(day, hour, kind):
    assert ai.event_kind(day, hour) == kind


def test_surge_outlook_learned_from_holidays():
    paddys = ai.day_summary(D(2026, 3, 17))
    assert paddys['surge'] and paddys['title'] == "St Patrick's Day"
    assert any(h.surge for h in paddys['hours'][10:15])
    assert any(h.boost > 0 for h in paddys['hours'][10:15])        # agent pre-positions drivers
    eve = ai.day_summary(D(2026, 12, 24))
    assert eve['surge'] and all(h.surge for h in eve['hours'][13:21])
    ordinary = ai.day_summary(D(2026, 11, 5))
    assert not ordinary['surge'] and ordinary['title'] == 'An ordinary Thursday'
    christmas = ai.day_summary(D(2026, 12, 25))
    assert christmas['text'].startswith('Quiet day') and christmas['total'] < christmas['ordinary_total'] / 2


def test_upcoming_events_are_ordered_and_named():
    events = ai.upcoming(D(2026, 12, 20), limit=4)
    assert [e['date'] for e in events] == sorted(e['date'] for e in events)
    assert [e['title'] for e in events][:2] == ['Christmas Eve', 'Christmas Day']


def test_dispatch_policy_matches_video_scenario():
    chosen, why = ai.choose(0)          # UCC Campus
    assert chosen.name == 'Morgan'
    assert 'Ava' in why and 'Mardyke' in why and 'surge' in why
    probabilities = [p for _, p in ai.rank(0)]
    assert abs(sum(probabilities) - 1) < 1e-9 and probabilities == sorted(probabilities, reverse=True)


@pytest.mark.parametrize('pickup,name', [(1, 'Sam'), (2, 'Eoin'), (3, 'Conor')])
def test_dispatch_policy_other_pickups(pickup, name):
    chosen, why = ai.choose(pickup)
    assert chosen.name == name and why


def test_courier_timing_avoids_counter_wait():
    for restaurant in range(3):
        plan = ai.courier_plan(restaurant)
        assert plan['courier_wait'] <= 2 < plan['naive_wait']
        assert plan['arrive'] == plan['dispatch_after'] + plan['travel']
    assert ai.courier_plan(0)['dispatch_after'] == 7


def test_learning_lab_beats_nearest_driver_rule():
    lab = ai.LearningLab(test_size=120)
    start = lab.curve[0][1]
    lab.train(learned.TRAINING_EPISODES)
    result = lab.result()
    assert lab.done and result['episodes'] == learned.TRAINING_EPISODES
    assert result['candidate'] < result['nearest'] < start
    assert abs(result['candidate'] - result['approved']) < 0.5
    assert [e for e, _ in lab.curve] == sorted(e for e, _ in lab.curve)
    lab.reset()
    assert lab.episodes == 0 and lab.w == [0.0] * 4


def test_dispatch_explanation_and_courier_plan_persist(tmp_path):
    store = LocalStore(tmp_path / 'state.json')
    chosen, why = ai.choose(0)
    store.book(0, 1, driver=f'{chosen.name} · ATLAS demo driver', why=why)
    store.cart.add('bowl')
    store.checkout(1, ai.courier_plan(0))
    restored = LocalStore(store.path)
    assert restored.ride['driver'].startswith('Morgan') and restored.ride['why'] == why
    assert restored.order['courier']['dispatch_after'] == 7


def test_shared_ride_keeps_offer_driver(tmp_path):
    store = LocalStore(tmp_path / 'state.json')
    store.book(0, 1, offer_id='pool-1', driver='Ignored', why='Ignored')
    assert store.ride['driver'].startswith('Alex') and 'why' not in store.ride


@pytest.mark.parametrize('field,value', [('why', 7), ('courier', {'dispatch_after': 'soon'})])
def test_damaged_learning_fields_are_recovered(tmp_path, field, value):
    path = tmp_path / 'state.json'
    store = LocalStore(path)
    if field == 'why':
        store.book(0, 1)
        store.ride['why'] = value
    else:
        store.cart.add('bowl')
        store.checkout(0)
        store.order['courier'] = value
    store.save()
    restored = LocalStore(path)
    assert restored.ride is None and restored.order is None and path.with_suffix('.invalid.json').exists()


def test_outlook_day_ui_bounds(tmp_path):
    store = LocalStore(tmp_path / 'state.json')
    store.ui = {'screen': 'intelligence', 'outlook_day': 3}
    store.save()
    assert LocalStore(store.path).ui == {'screen': 'intelligence', 'outlook_day': 3}
    store.ui = {'outlook_day': 9999}
    store.save()
    assert LocalStore(store.path).ui == {}


def test_learned_constants_are_plain_python():
    assert len(learned.RIDE_WEIGHTS) == 4 and all(isinstance(w, float) for w in learned.RIDE_WEIGHTS)
    json.dumps([learned.COURIER_DELAY, learned.BASE_DEMAND, learned.SURGE_RATIO, learned.BOOST])
