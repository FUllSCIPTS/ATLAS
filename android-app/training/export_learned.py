"""Export what the simulated agents learned into atlas_go/learned.py (pure Python constants).

Run from android-app/:  python training/export_learned.py
Needs numpy (development only). The Android app itself never imports numpy or these scripts.

Sources
  rl_sim.py   - ride-dispatch policy (REINFORCE) and food courier timing (Q-learning)
  city_sim.py - two simulated years of Cork demand (2025-2026) with Ireland's public holidays,
                and the supply agent that learned when to add drivers
All demand here is synthetic. The exported tables are small enough to review by eye.
"""
import datetime as dt
import pprint
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rl_sim  # noqa: E402
import city_sim as cs  # noqa: E402

OUT = HERE.parent / 'atlas_go' / 'learned.py'


def holiday_kind(d, h):
    """A finer label than the agent's state, used only for the surge profiles."""
    tag = cs.event_tag(d, h)
    if tag == 'bank_hol':
        name = cs.HOL[d]
        return {"St Stephen's Day": 'stephens', "New Year's Day": 'new_year'}.get(name, 'bank_hol')
    return tag


def weektype(d):
    return 0 if d.weekday() < 4 else d.weekday() - 3   # Mon-Thu, Fri, Sat, Sun


def main():
    # ---- ride dispatch + courier timing
    w, *_ = rl_sim.train_ride()
    _, food_policy, *_ = rl_sim.train_food()

    # ---- two years of city demand and the supply agent
    D = cs.demand_series()
    TY = cs.typical(D)
    S = TY * 1.03
    cs.run_rl(D, S)
    Q = cs.run_rl.Q

    # Base requests/hour on an ordinary day in the second (most recent) year
    base = {}
    for wt in range(4):
        for h in range(24):
            vals = [TY[i] for i, t in enumerate(cs.T) if t.year == 2026 and weektype(t.date()) == wt and t.hour == h]
            base.setdefault(wt, []).append(round(float(np.mean(vals)), 1))

    # Learned surge ratio (demand / ordinary same weekday-hour) per calendar kind and hour
    acc = {}
    for i, t in enumerate(cs.T):
        k = holiday_kind(t.date(), t.hour)
        if k in ('ordinary', 'storm', 'match'):
            continue  # storms and matches are not knowable from the calendar alone
        acc.setdefault(k, {}).setdefault(t.hour, []).append(D[i] / TY[i])
    ratio = {k: [round(float(np.mean(v[h])), 2) if h in v else 1.0 for h in range(24)] for k, v in sorted(acc.items())}

    # Agent's learned boost (extra share of drivers) per state; keep only non-zero entries
    boost = {}
    for key, q in Q.items():
        if len(key) != 3:
            continue
        tag, wt, h = key
        if tag in ('storm', 'match'):
            continue
        b = float(cs.BOOSTS[int(np.argmax(q))])
        if b > 0:
            boost[f'{tag}|{wt}|{h}'] = b

    header = (
        '"""Learned constants exported from the ATLAS simulations by training/export_learned.py.\n\n'
        'Do not edit by hand. Everything here was learned from synthetic data: a ride-dispatch policy,\n'
        'a courier-timing table, and two simulated years of Cork demand over Ireland\'s 2025-2026\n'
        'public holidays. No real trips, riders or drivers are involved.\n"""\n\n')
    body = (
        f'POLICY_VERSION = \'v1.4\'\n'
        f'TRAINING_EPISODES = {30000}\n\n'
        '# Ride dispatch: softmax policy over driver features\n'
        '# [closer ETA (-eta/5), will accept (0-1), keep last driver in surging zone (-surge*last), avoid surging zone (-surge)]\n'
        f'RIDE_WEIGHTS = {[round(float(x), 3) for x in w]}\n\n'
        '# Food: kitchen slack (prep estimate - courier travel, whole minutes) -> minutes to wait before dispatch\n'
        f'COURIER_DELAY = {pprint.pformat({int(k): int(v) for k, v in food_policy.items()}, width=100)}\n\n'
        '# Ordinary-day requests per hour in the simulated city, by weekday type (0 Mon-Thu, 1 Fri, 2 Sat, 3 Sun)\n'
        f'BASE_DEMAND = {pprint.pformat(base, width=110)}\n\n'
        '# Learned demand ratio against an ordinary same weekday, per calendar kind and hour (0-23)\n'
        f'SURGE_RATIO = {pprint.pformat(ratio, width=110)}\n\n'
        '# Supply agent: extra share of drivers it learned to add, keyed "tag|weekday type|hour" (absent = 0)\n'
        f'BOOST = {pprint.pformat(boost, width=110)}\n')
    OUT.write_text(header + body, encoding='utf-8')
    print('wrote', OUT, len(boost), 'boost entries,', len(ratio), 'surge profiles')


if __name__ == '__main__':
    main()
