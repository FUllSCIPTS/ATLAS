#!/usr/bin/env python3
"""ML 24 - LSTM + RL as one loop: forecast -> act -> record outcomes -> update and validate both models.

ATLAS link: ATLAS Go 1.4 runs this loop on the phone (android-app/atlas_go/loop.py). Every city hour a
compact LSTM (24 hours in, 16 hidden units, 6 hours out; trained by training/export_lstm.py on the
supply agent's experience log) forecasts demand; the RL supply agent chooses how many extra drivers to
add from the calendar AND the LSTM's forecast level; the real outcome is logged; each night the LSTM's
output layer and the agent's Q-table are retrained and kept only if they beat the current models on
held-out recent hours (champion / challenger). This experiment measures:
  1. the loop against the 1.2 calendar-only agent and against no extra drivers, on four periods;
  2. an ablation: the same loop with learning switched off (frozen models);
  3. forecast error by horizon (1-6 hours) from the loop's own log;
  4. validation at work: a deliberately bad challenger is rejected and the champion is kept.
Applies to: demand planning, energy dispatch, inventory - any forecast-then-decide system that must keep
learning without breaking.
Exercise: accept every challenger without validation for four weeks and plot the cost - what goes wrong?
"""
import datetime as dt

import numpy as np

from common import note, run, show, table
from atlas_go import learned
from atlas_go import loop as live
from atlas_go import lstm_weights as LW

PERIODS = (('Jazz weekend', dt.datetime(2026, 10, 19), 9), ("St Patrick's week", dt.datetime(2027, 3, 14), 7),
           ('Christmas fortnight', dt.datetime(2026, 12, 20), 14), ('February fortnight', dt.datetime(2027, 2, 1), 14))


def run_loop(start, days, learn=True):
    lp = live.Loop()
    if not learn:
        lp.daily_update = lambda i: {}                      # champion never replaced
    lp.warm_up(live.hour_index(start))
    for _ in range(days * 24):
        lp.step()
    return lp


def calendar_boost(t):
    g = live.tag(t)
    return learned.BOOST.get(f"{g}|{live.weektype(t) if g == 'ordinary' else 0}|{t.hour}", 0.0)


def main():
    rows = []
    totals = np.zeros(3)
    for name, start, days in PERIODS:
        lp = run_loop(start, days)
        logged = [r for r in lp.state['log'] if r['f'] is not None]
        c_loop = sum(r['cost'] for r in logged)
        c_cal = sum(live._cost(r['d'], r['ty'] * 1.03, calendar_boost(live.hour_time(r['i'])))[2] for r in logged)
        c_none = sum(live._cost(r['d'], r['ty'] * 1.03, 0.0)[2] for r in logged)
        totals += (c_none, c_cal, c_loop)
        rows.append((name, f'{c_none:.0f}', f'{c_cal:.0f}', f'{c_loop:.0f}'))
    rows.append(('all four', *[f'{x:.0f}' for x in totals]))
    table(['period', 'no extra drivers', '1.2 calendar agent', 'LSTM + RL loop'], rows)
    show('loop vs 1.2 calendar agent', f'{(totals[2] / totals[1] - 1) * 100:+.1f} % cost')
    note('Cost = unserved requests + 0.25 x idle extra drivers. The forecast-aware agent beats the calendar')
    note('agent overall, though not in every period (the calendar table knows St Patrick\'s Day very well).')

    rows = []
    for name, start in (('Jan-Feb 2027', dt.datetime(2027, 1, 4)), ('May-Jun 2027', dt.datetime(2027, 5, 3)),
                        ('Sep-Oct 2027', dt.datetime(2027, 9, 6))):
        on, off = run_loop(start, 56), run_loop(start, 56, learn=False)
        c_on = sum(r['cost'] for r in on.state['log'] if r['f'] is not None)       # the last 14 days
        c_off = sum(r['cost'] for r in off.state['log'] if r['f'] is not None)
        rows.append((name, f'{c_off:.0f}', f'{c_on:.0f}', f'{(c_on / c_off - 1) * 100:+.1f} %',
                     f"lstm v{on.state['lstm']['n'] - 1} · agent v{on.state['agent']['n'] - 1}"))
    table(['8 weeks, cost in the last 2 weeks', 'learning off (frozen)', 'learning on', 'change', 'versions reached'], rows)
    note('Over one or two weeks nightly learning changes little; over eight weeks, beyond the training years,')
    note('the validated updates keep the models current and the cost falls against the frozen models.')

    lp = run_loop(dt.datetime(2026, 10, 1), 28)
    by = lp.rows()
    errs = [[] for _ in range(LW.HZ)]
    for r in lp.state['log']:
        if r['f'] is None:
            continue
        for k in range(LW.HZ):
            nxt = by.get(r['i'] + k)
            if nxt:
                errs[k].append(abs(r['f'][k] * nxt['ty'] - nxt['d']) / nxt['d'])
    table(['horizon (hours ahead)'] + [str(k + 1) for k in range(LW.HZ)],
          [('mean absolute % error', *[f'{100 * np.mean(e):.1f}' for e in errs])])
    accepted = sum(1 for u in lp.state['updates'] if (u['lstm'] or {}).get('accepted'))
    tried = sum(1 for u in lp.state['updates'] if u['lstm'])
    improved = sum(1 for u in lp.state['updates'] if (u['agent'] or {}).get('improved'))
    show('nightly LSTM refits kept (28 days)', f'{accepted} of {tried}')
    show('nightly agent updates that improved the replay', f'{improved} of {len(lp.state["updates"])}')

    champion = dict(lp.state['agent']['Q'])
    lp.state['challenger'] = dict(Q={r['key']: [-1e6] * 5 + [0.0] for r in lp.state['log'] if r.get('key')}, NQ={})
    report = lp.daily_update(lp.state['cursor'])
    show('bad challenger (always +150 % drivers)',
         f"replay cost {report['agent']['challenger']:.0f} vs champion {report['agent']['champion']:.0f} -> "
         f"{'accepted' if report['agent']['accepted'] else 'rejected'}")
    show('champion unchanged', lp.state['agent']['Q'] == champion)
    note('Validation is what makes continuous learning safe: a challenger that would have cost more on the')
    note('last seven days is never deployed, and the log records why.')


if __name__ == '__main__':
    run(main, __doc__)
