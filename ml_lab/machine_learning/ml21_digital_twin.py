#!/usr/bin/env python3
"""ML 21 - Digital twin: mirror, foresee, rehearse and guard (ATLAS Go Layer 2).

ATLAS link: ATLAS Go 1.3 adds a digital twin of Cork (android-app/atlas_go/twin.py) that sits on top of
the learned models. It MIRRORS the city (every driver, the active car and courier, with a fidelity
score), FORESEES the next 30 minutes from Layer 1's demand outlook, lets Agent 1 (dispatch) and Agent 2
(pricing and repositioning) REHEARSE decisions in simulation before they are sent, and lets Agent 3,
the Guardian, block unsafe decisions and fall back to Layer 1. This experiment measures each step:
  1. foresight: the twin's 30-minute demand ratio against what the simulated city then does;
  2. rehearsal: how many rollouts Agent 1 needs before its choice is stable;
  3. planning: Agent 2's price and moves through St Patrick's Day;
  4. guarding: 3,000 injected faults - how many the Guardian catches, and false alarms on good decisions.
Applies to: factories, power grids, logistics, hospitals - any system you can simulate before acting.
Exercise: make the twin rehearse 30 minutes with a stale mirror (positions 5 minutes old) - how much
worse are Agent 1's choices?
"""
import datetime as dt
import random

import numpy as np

from common import note, run, show, table
from atlas_go import intelligence as ai
from atlas_go import loop as live
from atlas_go import twin
from atlas_go.domain import PLACES


def foresight():
    rows = []
    for name, start in (('ordinary week', dt.datetime(2026, 11, 2)), ('Jazz weekend', dt.datetime(2026, 10, 22)),
                        ("St Patrick's week", dt.datetime(2027, 3, 14))):
        err_twin, err_persist, err_one = [], [], []
        for h in range(7 * 24):
            t = start + dt.timedelta(hours=h)
            actual = np.mean([live.demand(t + dt.timedelta(minutes=m)) / live.ordinary(t + dt.timedelta(minutes=m))
                              for m in (0, 30)])
            err_twin.append(abs(twin.ratio_30(t) - actual))
            prev = t - dt.timedelta(hours=1)
            err_persist.append(abs(live.demand(prev) / live.ordinary(prev) - actual))
            err_one.append(abs(1.0 - actual))
        rows.append((name, f'{np.mean(err_one):.3f}', f'{np.mean(err_persist):.3f}', f'{np.mean(err_twin):.3f}'))
    table(['week (hourly checks)', '"always ordinary"', 'last hour again', 'twin foresight'], rows)
    note('Mean absolute error of the demand ratio for the next 30 minutes. The twin reads the calendar-aware')
    note('outlook from Layer 1, so it sees a festival or a holiday coming; "last hour again" only reacts.')


def rehearsal():
    when = dt.datetime(2027, 3, 17, 13, 0)
    rows = []
    for pickup in range(4):
        ranked = ai.rank(pickup)
        top = [c for c, _ in ranked[:3]]
        r = twin.ratio_30(when)
        ref_rng = random.Random(1)
        reference = min(top, key=lambda c: twin.rehearse(c, r, ref_rng, 5000))
        agree = []
        for n in (5, 20, 50, 200):
            hits = 0
            for seed in range(40):
                rng = random.Random(seed)
                pick = min(top, key=lambda c: twin.rehearse(c, r, rng, n))
                hits += pick == reference
            agree.append(f'{hits / 40:.0%}')
        rows.append((PLACES[pickup], reference.name, *agree))
    table(['pickup (St Patrick\'s 13:00)', 'best of top 3', '5 runs', '20 runs', '50 runs', '200 runs'], rows)
    note('Share of 40 independent rehearsals that agree with a 5,000-run reference. The app uses 200 runs:')
    note('enough for a stable choice and still a few milliseconds on a phone.')


def planning():
    day = dt.datetime(2027, 3, 17)
    rows = []
    for h in (8, 10, 12, 13, 15, 18, 20, 22):
        t = day.replace(hour=h)
        plan = twin.agent2(1, t)
        keep = plan['plans'][0]['wait']
        rows.append((f'{h:02d}:00', f"{plan['ratio']:.2f}", plan['choice']['name'], f"x{plan['multiplier']:.1f}",
                     f'{keep:.1f}', f"{plan['choice']['wait']:.1f}"))
    table(['City Centre', 'demand ratio', 'Agent 2 plan', 'price', 'wait if no change', 'wait with plan'], rows)
    note('Three plans are rehearsed every five minutes; a change is made only if it saves more than its cost')
    note('(price jumps and empty kilometres). Prices never exceed x2.0.')


def guarding():
    rng = random.Random(7)
    caught = total = false_alarm = good = 0
    for k in range(3000):
        t = dt.datetime(2026, 11, 4, 0) + dt.timedelta(hours=rng.randrange(24 * 400))
        pickup = rng.randrange(4)
        d = twin.agent1(pickup, t)
        p = twin.agent2(pickup, t)
        good += 2
        false_alarm += (not twin.check_dispatch(d)[0]) + (not twin.check_price(p['multiplier'], p['expected'])[0])
        kind = k % 3
        if kind == 0:                                          # a wild price
            m = rng.choice([rng.uniform(2.05, 6.0), rng.uniform(0.0, 0.95), float('nan')])
            ok = twin.check_price(m, p['expected'])[0]
        elif kind == 1:                                        # a driver Layer 1 would never send
            outsider = [c for c, _ in ai.rank(pickup)][-1]
            ok = twin.check_dispatch(dict(d, choice=outsider))[0]
        else:                                                  # no answer in time
            ok = twin.check_dispatch(dict(d, elapsed_ms=twin.DECISION_BUDGET_MS * rng.uniform(1.01, 20)))[0]
        total += 1
        caught += not ok
    show('injected faults caught', f'{caught} of {total} ({caught / total:.1%})')
    show('false alarms on normal decisions', f'{false_alarm} of {good}')
    passed, n = twin.retest_pricing()
    show('re-test before hand-back', f'{n} of {twin.RETEST_ROLLOUTS} rollouts pass -> {"hand back" if passed else "keep Layer 1"}')
    note('A runtime shield does not optimise anything: it checks hard limits and what the twin expects, and')
    note('falls back to the tested Layer 1 decision. The guarantee is narrow and testable - as measured here.')


def main():
    foresight()
    rehearsal()
    planning()
    guarding()


if __name__ == '__main__':
    run(main, __doc__)
