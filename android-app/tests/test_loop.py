"""Layer 1 live loop (1.4.0): LSTM predicts demand -> RL agent acts -> outcomes recorded -> both models
periodically updated and validated."""
import datetime as dt
import json
import pytest
from atlas_go import learned
from atlas_go import loop as L
from atlas_go import lstm_weights as LW

START = dt.datetime(2026, 10, 19, 0)


def running(hours=0, start=START, path=None):
    lp = L.Loop(path)
    lp.warm_up(L.hour_index(start))
    for _ in range(hours):
        lp.step()
    return lp


def test_pure_python_lstm_matches_the_trained_numpy_model():
    y = L.head(L.lstm_hidden(LW.REF_X), LW.V, LW.C)
    assert max(abs(a - b) for a, b in zip(y, LW.REF_Y)) < 1e-4


def test_city_feed_is_deterministic_and_calendar_aware():
    t = dt.datetime(2026, 11, 4, 10)
    assert L.demand(t) == L.demand(t)
    assert L.ordinary(t) == learned.BASE_DEMAND[0][10]
    jazz, plain = L.demand(dt.datetime(2026, 10, 24, 22)), L.demand(dt.datetime(2026, 10, 17, 22))
    assert jazz > 1.6 * plain
    cal = L.calendar(dt.datetime(2026, 10, 24, 22))
    assert len(cal) == 30 and cal[4 + LW.TAGS.index('jazz') - 1] == 1.0


def test_forecast_needs_the_experience_window():
    lp = L.Loop()
    with pytest.raises(LookupError):
        lp.forecast(L.hour_index(START))
    lp.warm_up(L.hour_index(START))
    fc = lp.forecast(L.hour_index(START))
    assert len(fc['ratios']) == LW.HZ and len(fc['hidden']) == LW.NH and 0 <= fc['level'] <= len(LW.BUCKETS)


def test_each_hour_forecast_then_act_then_record():
    lp = running()
    i = L.hour_index(START)
    fc = lp.forecast(i)                                   # issued before the hour's demand is known
    key = L._key(L.hour_time(i), fc['level'])
    expected_boost = LW.BOOSTS[lp.choose(key)]
    row = lp.step()
    assert row['i'] == i and row['f'] == [round(x, 4) for x in fc['ratios']] and row['key'] == key
    assert row['boost'] == expected_boost and row['by'] == 'LSTM + agent'
    assert key.endswith(f"|{fc['level']}")                # the agent's state includes the LSTM's forecast level
    assert row['d'] == round(L.demand(L.hour_time(i)), 2)
    assert row['un'] + (row['d'] - row['un']) == pytest.approx(row['d'])


def test_lstm_level_changes_the_agents_decision():
    lp = L.Loop()
    t = dt.datetime(2026, 10, 24, 21)
    actions = {lp.choose(L._key(t, lv)) for lv in range(len(LW.BUCKETS) + 1)}
    assert len(actions) > 1


def test_online_learning_goes_to_the_challenger_until_validated():
    lp = running(5)
    assert lp.state['challenger']['Q'] and not lp.state['agent']['Q']
    lp = running(24)                                      # passes 23:00 -> nightly update
    assert len(lp.state['updates']) == 1 and lp.state['challenger']['Q'] == {}
    assert lp.state['updates'][0]['agent']['accepted'] in (True, False)


def test_agent_validation_rejects_a_worse_challenger():
    lp = running(23 + 24 * 2)
    champion = dict(lp.state['agent']['Q'])
    lp.state['challenger'] = dict(Q={r['key']: [-1e6] * 5 + [0.0] for r in lp.state['log'] if r.get('key')}, NQ={})
    report = lp.daily_update(lp.state['cursor'])
    assert report['agent']['accepted'] is False and report['agent']['challenger'] > report['agent']['champion']
    assert lp.state['agent']['Q'] == champion


def test_lstm_validation_keeps_the_better_head():
    lp = running(24 * 5)
    lstm = [u['lstm'] for u in lp.state['updates'] if u['lstm']]
    assert lstm
    for u in lstm:
        assert u['accepted'] == (u['after'] <= u['before'] * .99)
    assert lp.state['lstm']['n'] == 1 + sum(u['accepted'] for u in lstm)


def test_the_loop_beats_the_calendar_agent_over_four_simulated_periods():
    loop_cost = cal_cost = none_cost = 0.0
    for start, days in ((dt.datetime(2026, 10, 19), 9), (dt.datetime(2027, 3, 14), 7),
                        (dt.datetime(2026, 12, 20), 14), (dt.datetime(2027, 2, 1), 14)):
        lp = running(days * 24, start)
        for r in (r for r in lp.state['log'] if r['f'] is not None):
            t = L.hour_time(r['i'])
            g = L.tag(t)
            b12 = learned.BOOST.get(f"{g}|{L.weektype(t) if g == 'ordinary' else 0}|{t.hour}", 0.0)
            loop_cost += r['cost']
            cal_cost += L._cost(r['d'], r['ty'] * 1.03, b12)[2]
            none_cost += L._cost(r['d'], r['ty'] * 1.03, 0.0)[2]
    assert loop_cost < cal_cost < none_cost


def test_training_metrics_exported_with_the_model():
    m = LW.METRICS
    assert m['supply']['cost_lstm_agent'] < m['supply']['cost_calendar_agent'] < m['supply']['cost_no_boost']
    assert m['h1']['mape'] < .15 and m['h1']['surge_recall'] > .7


def test_advance_to_catches_up_and_restarts_after_gaps_or_clock_changes(tmp_path):
    lp = L.Loop(tmp_path / 'loop.json')
    assert lp.advance_to(START) == 0 and lp.state['cursor'] == L.hour_index(START) - 1      # warm-up
    assert lp.advance_to(START + dt.timedelta(hours=10)) == 10
    assert lp.advance_to(START + dt.timedelta(hours=10)) == 0
    assert lp.advance_to(START + dt.timedelta(days=10)) == 0                                # long gap: warm-up
    assert lp.state['cursor'] == L.hour_index(START + dt.timedelta(days=10)) - 1
    lp.advance_to(START)                                                                    # clock moved back
    assert lp.state['cursor'] == L.hour_index(START) - 1


def test_persistence_and_damaged_files(tmp_path):
    path = tmp_path / 'loop.json'
    lp = running(30, path=path)
    lp.save()
    again = L.Loop(path)
    assert again.state['hours'] == 30 and again.state['log'] == lp.state['log']
    data = json.loads(path.read_text())
    data['lstm']['V'][0][0] = 'x'
    path.write_text(json.dumps(data))
    fresh = L.Loop(path)
    assert fresh.state['hours'] == 0 and path.with_suffix('.invalid.json').exists()
    fresh.reset()
    assert not path.exists() and not path.with_suffix('.invalid.json').exists()


def test_log_is_bounded():
    lp = running(L.LOG_HOURS + 30)
    assert len(lp.state['log']) == L.LOG_HOURS


def test_now_view_for_the_app():
    lp = running(30)
    view = lp.now(L.hour_time(lp.state['cursor'] + 1))
    assert 0.0 <= view['surge'] <= 1.0 and view['boost'] in LW.BOOSTS and len(view['forecast']['requests']) == 6
    assert view['lstm'].startswith(LW.LSTM_VERSION) and view['agent'].startswith(LW.AGENT_VERSION)


def test_loop_self_test():
    results = L.self_test()
    assert len(results) == 2 and all(ok for _, ok, _ in results), results
