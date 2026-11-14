"""ATLAS Go Layer 2 (1.3.0): a digital twin of Cork and three agents that work on top of Layer 1.

Layer 1 is the 1.2.0 intelligence in intelligence.py and learned.py (LSTM-style surge outlook,
REINFORCE dispatch policy, acceptance model, supply agent, Q-learning courier timing). Layer 2
never changes it: it only *reads* Layer 1's forecast, ranking and cost model, rehearses
decisions in a small simulation of the next 30 minutes, and lets the Guardian check every
decision before it reaches a screen. If Layer 2 is switched off, or the Guardian blocks a
decision, the app uses Layer 1's answer exactly as 1.2.0 did.

  Mirror     what the twin knows now: every driver, the active car and courier, with a fidelity score
  Foresee    demand for the next 30 minutes per pickup place, from Layer 1's hourly outlook
  Agent 1    dispatch: rehearses Layer 1's top three drivers in the twin, picks the lowest total wait
  Agent 2    pricing and repositioning: rehearses three plans per place, capped surge (x2.0)
  Agent 3    Guardian: hard limits, a time budget, fallback to Layer 1, re-test before hand-back

Pure Python, deterministic for a given place and five-minute window, no network and no numpy.
All numbers come from simulation; they are illustrative, not measurements of real riders.
"""
from __future__ import annotations

import datetime as dt
import math
import random
import time

from . import geo
from . import intelligence as ai
from .domain import PLACES

VERSION = 'twin-1.0'
HORIZON_MIN = 30          # the twin plays the next 30 minutes
ROLLOUTS = 200            # rehearsals per decision
RETEST_ROLLOUTS = 500     # rehearsals before a blocked agent gets control back
PRICE_CAP = 2.0           # Guardian: never more than double the base fare
MAX_STEP = 0.5            # Guardian: never more than +0.5 above what the twin expects
DECISION_BUDGET_MS = 250  # Guardian: a decision that takes longer is replaced by Layer 1's
TOP_K = 3                 # Agent 1 chooses among Layer 1's three best drivers
LOG_LIMIT = 60

# Share of Cork's ride requests that start near each saved place (illustrative)
PLACE_SHARE = (0.30, 0.40, 0.20, 0.10)
CAR_CAPACITY_PER_30 = 2.2  # rides one free car can serve in 30 minutes
REFERENCE_HOURLY = 260.0   # city requests/hour the usual fleet is sized for; load scales with Layer 1's ratio

AGENTS = (
    ('twin', 'Digital twin', 'Mirrors drivers, rides and couriers · foresees 30 min'),
    ('dispatch', 'Agent 1 · Dispatch', "Rehearses Layer 1's top 3 drivers, sends the best"),
    ('pricing', 'Agent 2 · Pricing + moves', 'Capped surge (×2.0) and driver hints per area'),
    ('guardian', 'Agent 3 · Guardian', 'Checks every decision · falls back to Layer 1'),
)


def default_state() -> dict:
    return dict(enabled=True, status=dict(dispatch='active', pricing='active'), log=[], checks=0, blocks=0)


def valid_state(state) -> bool:
    if not isinstance(state, dict) or type(state.get('enabled')) is not bool:
        return False
    status = state.get('status')
    if not isinstance(status, dict) or set(status) != {'dispatch', 'pricing'} or \
            any(v not in ('active', 'retesting') for v in status.values()):
        return False
    if any(type(state.get(k)) is not int or state[k] < 0 for k in ('checks', 'blocks')):
        return False
    log = state.get('log')
    if not isinstance(log, list) or len(log) > LOG_LIMIT:
        return False
    for entry in log:
        if not isinstance(entry, dict) or type(entry.get('t')) not in (int, float):
            return False
        if not all(isinstance(entry.get(k), str) for k in ('agent', 'decision', 'result')):
            return False
        if entry['result'] not in ('passed', 'blocked', 'fallback', 'retested', 'handed back', 'info'):
            return False
    return True


def entry(agent: str, decision: str, result: str, detail: str = '', now: float | None = None) -> dict:
    return dict(t=round(time.time() if now is None else now, 3), agent=agent, decision=decision,
                result=result, detail=detail)


# --------------------------------------------------------------------------- clock and forecast

def window(now_dt: dt.datetime) -> int:
    """Five-minute window index: Agent 2 decides once per window, so prices are stable within it."""
    return now_dt.hour * 12 + now_dt.minute // 5


def _ratio(day: dt.date, hour: int) -> float:
    """Layer 1's forecast for one hour, as demand / ordinary demand (read-only use of the outlook)."""
    day = day + dt.timedelta(days=hour // 24)
    return ai.outlook(day)[hour % 24].ratio


def _expected(day: dt.date, hour: int) -> tuple[float, float]:
    day = day + dt.timedelta(days=hour // 24)
    h = ai.outlook(day)[hour % 24]
    return h.expected, h.ordinary


def extra_requests(now_dt: dt.datetime, place: int) -> int:
    """Requests above an ordinary same weekday and time near one place in the next 30 minutes,
    straight from Layer 1's hourly outlook (expected minus ordinary)."""
    day, hour, minute = now_dt.date(), now_dt.hour, now_dt.minute
    extra = 0.0
    for step in range(6):
        expected, ordinary = _expected(day, hour + (minute + step * 5) // 60)
        extra += (expected - ordinary) / 12            # five minutes of an hourly rate
    return max(0, round(extra * PLACE_SHARE[place]))


def ratio_30(now_dt: dt.datetime) -> float:
    """Average demand ratio over the next 30 minutes, blending this hour and the next one."""
    day, hour, minute = now_dt.date(), now_dt.hour, now_dt.minute
    total = 0.0
    for step in range(6):                       # every 5 minutes across the horizon
        m = minute + step * 5
        total += _ratio(day, hour + m // 60)
    return total / 6


def foresee(now_dt: dt.datetime, extra_supply=None) -> list[dict]:
    """Next 30 minutes for each pickup place: expected requests, free cars and pressure."""
    extra_supply = extra_supply or {}
    r = ratio_30(now_dt)
    rows = []
    for p, name in enumerate(PLACES):
        # The fleet follows the usual daily pattern, so the load an area feels grows with Layer 1's
        # demand ratio (expected / ordinary for that weekday and hour), not with the raw hourly count.
        demand = REFERENCE_HOURLY * r * PLACE_SHARE[p] * HORIZON_MIN / 60 / 12
        pool = ai.DRIVER_POOLS[p]
        free = sum(1 for c in pool if not (c.last and c.surge >= .5)) + extra_supply.get(p, 0)
        rows.append(dict(place=p, name=name, ratio=round(r, 3), demand=round(demand, 2), free=free,
                         pressure=round(demand / max(1e-9, free * CAR_CAPACITY_PER_30), 3)))
    return rows


# --------------------------------------------------------------------------- mirror

def mirror(store, now: float) -> dict:
    """What the twin holds right now and how well it knows it (fidelity 0-1).

    Simulated drivers report every second (known = 1). Registered drivers count fully when their
    phone shared a location, at 0.6 when only their starting area is known. The active car and
    courier are positioned from their live journey."""
    entities, weight = [], 0.0
    seen = set()
    for p, pool in enumerate(ai.DRIVER_POOLS):
        for k, c in enumerate(pool):
            if c.name in seen:
                continue
            seen.add(c.name)
            entities.append(dict(kind='driver', name=c.name, point=geo.zone_drift(c.zone, now, p * 1.7 + k)))
            weight += 1.0
    for account in store.online_drivers():
        known = bool(account['driver'].get('location'))
        entities.append(dict(kind='registered', name=account['name'].split()[0], point=store.driver_position(account)))
        weight += 1.0 if known else 0.6
    if store.ride:
        entities.append(dict(kind='ride', name=store.ride['driver'].split(' · ')[0],
                             point=geo.ride_position(store.ride, now)[0]))
        weight += 1.0
    if store.order and store.order.get('live'):
        pos, _ = geo.order_position(store.order, now, store.kitchen_prep(store.order['restaurant']))
        if pos is not None:
            entities.append(dict(kind='courier', name='Courier', point=pos))
            weight += 1.0
    fidelity = weight / len(entities) if entities else 1.0
    return dict(entities=entities, count=len(entities), fidelity=round(fidelity, 2),
                drivers=sum(e['kind'] in ('driver', 'registered') for e in entities))


# --------------------------------------------------------------------------- Agent 1: dispatch

def _seed(*parts) -> int:
    text = '|'.join(str(p) for p in parts)
    return sum((i + 1) * ord(ch) for i, ch in enumerate(text)) % 2_147_483_647


def rehearse(candidate: ai.Candidate, ratio: float, rng: random.Random, rollouts: int = ROLLOUTS) -> float:
    """Average total rider waiting (minutes) over the next 30 minutes if this driver is sent.

    The rider's own pickup follows Layer 1's waiting model (accept or decline, then re-offer).
    The twin adds what Layer 1 cannot see past ten minutes: riders who will ask for a car in the
    driver's area during the next 30 minutes, and wait longer if this was its last free car."""
    total = 0.0
    for _ in range(rollouts):
        accepted = rng.random() < candidate.accept
        wait = candidate.eta if accepted else candidate.eta + 1.5 + rng.uniform(2.0, 5.0)
        if wait > 8.0 and rng.random() < .45:
            wait += 10.0                               # cancellation, as in Layer 1's cost model
        expected = candidate.surge * 5.0 * ratio       # requests in that area within 30 minutes
        arrivals = _poisson(rng, expected)
        if candidate.last:
            wait += sum(rng.uniform(6.0, 14.0) for _ in range(arrivals))   # no car left: wait for one to return
        else:
            wait += arrivals * candidate.surge * 0.6                     # one car fewer in a busy area
        total += wait
    return total / rollouts


def _poisson(rng: random.Random, lam: float) -> int:
    if lam <= 0:
        return 0
    limit, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= limit:
            return k
        k += 1


def agent1(pickup: int, now_dt: dt.datetime, extra=(), exclude=()) -> dict:
    """Agent 1 decision for one request. Starts from Layer 1's ranking (untouched) and its top three."""
    started = time.perf_counter()
    ranked = ai.rank(pickup, extra=extra, exclude=exclude)
    layer1 = ranked[0][0]
    top = [c for c, _ in ranked[:TOP_K]]
    r = ratio_30(now_dt)
    rng = random.Random(_seed('dispatch', pickup, window(now_dt), now_dt.date().isoformat()))
    rollouts = [(c, round(rehearse(c, r, rng), 2)) for c in top]
    choice = min(rollouts, key=lambda x: (x[1], top.index(x[0])))[0]
    nearest = min((c for c, _ in ranked), key=lambda c: (c.eta, -c.accept))
    return dict(choice=choice, layer1=layer1, top=top, rollouts=rollouts, ratio=r,
                why=ai.explain(choice, nearest), elapsed_ms=(time.perf_counter() - started) * 1000)


def twin_reason(decision: dict) -> str:
    waits = ' · '.join(f'{c.name} {w:.1f} min' for c, w in decision['rollouts'])
    same = decision['choice'] == decision['layer1']
    lead = (f"Rehearsed in the city twin ({ROLLOUTS} runs, next {HORIZON_MIN} min): " + waits + '. ')
    if same:
        return lead + f"{decision['choice'].name} keeps the total wait lowest, as Layer 1 chose."
    return lead + (f"{decision['choice'].name} keeps the total wait lowest, so Agent 1 sends them instead of "
                   f"{decision['layer1'].name}.")


# --------------------------------------------------------------------------- Agent 2: pricing and moves

def _wait(demand: float, free: float, multiplier: float) -> float:
    """Average wait (minutes) in an area for 30 minutes of demand served by free cars."""
    effective = demand * multiplier ** -0.7             # some riders choose to wait or walk at a higher price
    load = effective / max(.5, free * CAR_CAPACITY_PER_30)
    return 3.0 + 6.0 * max(0.0, load - .55) ** 1.4


def surge_only(ratio: float) -> float:
    return round(min(PRICE_CAP, max(1.0, 1 + .4 * (ratio - 1))), 1)


def small_surge(ratio: float) -> float:
    return round(min(PRICE_CAP, max(1.0, 1 + .2 * (ratio - 1))), 1)


def expected_multiplier(ratio: float) -> float:
    """What the twin expects a sensible price to be; the Guardian compares against it."""
    return surge_only(ratio)


def agent2(place: int, now_dt: dt.datetime, extra_supply=None) -> dict:
    """Agent 2: rehearse three plans for one area and keep the one with the lowest wait plus price jump."""
    started = time.perf_counter()
    rows = foresee(now_dt, extra_supply)
    row = rows[place]
    donor = min((x for x in rows if x['place'] != place), key=lambda x: x['pressure'])
    movable = max(0, min(3, donor['free'] - 2))
    plans = []
    for name, m, moved in (('Keep prices, no moves', 1.0, 0),
                           ('Surge only', surge_only(row['ratio']), 0),
                           ('Small surge + move idle cars', small_surge(row['ratio']), movable)):
        wait = _wait(row['demand'], row['free'] + moved, m)
        plans.append(dict(name=name, multiplier=m, moved=moved, wait=round(wait, 2),
                          score=round(wait + 1.5 * (m - 1.0) + .1 * moved, 3)))
    best = min(plans, key=lambda p: p['score'])
    if plans[0]['score'] - best['score'] < .3:          # not worth changing anything
        best = plans[0]
    move = None
    if best['moved']:
        move = dict(cars=best['moved'], src=donor['place'], dst=place)
    return dict(place=place, ratio=row['ratio'], demand=row['demand'], free=row['free'], plans=plans,
                choice=best, multiplier=best['multiplier'], move=move,
                expected=expected_multiplier(row['ratio']), elapsed_ms=(time.perf_counter() - started) * 1000)


def driver_hint(base: int, now_dt: dt.datetime) -> dict:
    """Repositioning hint for a driver whose starting area is base: stay, or move where the twin sees pressure."""
    rows = foresee(now_dt)
    busiest = max(rows, key=lambda x: x['pressure'])
    here = rows[base]
    plan = agent2(busiest['place'], now_dt)
    extra = extra_requests(now_dt, busiest['place'])
    if busiest['place'] != base and plan['move'] and busiest['pressure'] > here['pressure'] + .15:
        return dict(action='move', place=busiest['place'], extra=extra,
                    text=f"Move towards {busiest['name']}. The twin expects about {extra} more requests than usual "
                         f"there in the next 30 minutes (×{plan['multiplier']:.1f}, capped).")
    if here['ratio'] >= 1.2:
        return dict(action='stay', place=base, extra=extra_requests(now_dt, base),
                    text=f"Stay near {here['name']}. Demand there is {ai.ratio_text(here['ratio'])} for the next "
                         f"30 minutes.")
    return dict(action='none', place=base, extra=0,
                text=f"No move needed: demand around {here['name']} is normal for the next 30 minutes.")


def kitchen_hint(plan: dict) -> str:
    """Seller hint from Layer 1's courier plan: when the courier arrives and when to start cooking."""
    start = max(0, plan['arrive'] - plan['prep'])
    when = 'Start cooking as soon as you accept' if start == 0 else f'You can start cooking {start} min after accepting'
    return (f"Courier arrives about {plan['arrive']} min after you accept (twin ETA). Food needs {plan['prep']} min. "
            f"{when}, so it is ready when the courier walks in.")


# --------------------------------------------------------------------------- Agent 3: Guardian

def check_dispatch(decision: dict, exclude=(), online_ids=None) -> tuple[bool, str]:
    choice = decision['choice']
    if decision['elapsed_ms'] > DECISION_BUDGET_MS:
        return False, f"no answer within {DECISION_BUDGET_MS} ms"
    if choice not in decision['top']:
        return False, "driver is not in Layer 1's top three"
    if choice.account and choice.account in exclude:
        return False, 'driver already declined this ride'
    if choice.account and online_ids is not None and choice.account not in online_ids:
        return False, 'driver is no longer online'
    if choice.eta > decision['layer1'].eta + 8:
        return False, f'pickup {choice.eta} min is far beyond Layer 1’s {decision["layer1"].eta} min'
    return True, 'within limits'


def check_price(multiplier, expected: float, elapsed_ms: float = 0.0) -> tuple[bool, str]:
    if type(multiplier) not in (int, float) or math.isnan(multiplier):
        return False, 'no valid price'
    if elapsed_ms > DECISION_BUDGET_MS:
        return False, f"no answer within {DECISION_BUDGET_MS} ms"
    if multiplier < 1.0:
        return False, 'below the base fare'
    if multiplier > PRICE_CAP:
        return False, f'×{multiplier:.1f} is above the ×{PRICE_CAP:.1f} cap'
    if multiplier > expected + MAX_STEP:
        return False, f'×{multiplier:.1f} jumps more than {MAX_STEP} above the twin’s ×{expected:.1f}'
    return True, 'within limits'


def retest_pricing(seed: int = 7, rollouts: int = RETEST_ROLLOUTS) -> tuple[bool, int]:
    """Before Agent 2 gets control back, replay it on random demand in the twin: every price must pass
    the Guardian and neighbouring demand levels must not jump the price by more than MAX_STEP."""
    rng = random.Random(seed)
    passed = 0
    for _ in range(rollouts):
        r = rng.uniform(.3, 4.5)
        m, m2 = surge_only(r), surge_only(r + .25)
        ok = check_price(m, expected_multiplier(r))[0] and check_price(small_surge(r), expected_multiplier(r))[0]
        ok = ok and abs(m2 - m) <= MAX_STEP and 1.0 <= m <= PRICE_CAP
        passed += ok
    return passed == rollouts, passed


# --------------------------------------------------------------------------- one call per screen action

def decide_ride(store, pickup: int, now_dt: dt.datetime, extra=(), exclude=(), enabled: bool = True) -> dict:
    """Driver and price for a solo ride. Returns Layer 1's answer when Layer 2 is off or blocked.

    Result: choice (Candidate), why (text), multiplier, twin (dict saved with the ride or None), log (entries)."""
    layer1, why1 = ai.choose(pickup, extra=extra, exclude=exclude)
    if not enabled:
        return dict(choice=layer1, why=why1, multiplier=1.0, twin=None, log=[], layer=1)
    now = time.time()
    log = []
    status = store.twin['status']
    choice, why, twin_info = layer1, why1, None
    if status['dispatch'] == 'active':
        decision = agent1(pickup, now_dt, extra=extra, exclude=exclude)
        online = {a['id'] for a in store.online_drivers()}
        ok, reason = check_dispatch(decision, exclude=exclude, online_ids=online)
        if ok:
            choice, why = decision['choice'], decision['why']
            twin_info = dict(agent='Agent 1', rollouts=[[c.name, w] for c, w in decision['rollouts']],
                             layer1=decision['layer1'].name, reason=twin_reason(decision))
            log.append(entry('Agent 1', f'match {choice.name} at {PLACES[pickup]}', 'passed', reason, now))
        else:
            log.append(entry('Agent 1', f"match {decision['choice'].name} at {PLACES[pickup]}", 'blocked', reason, now))
            log.append(entry('Guardian', f'Layer 1 sends {layer1.name}', 'fallback', 'dispatch fallback', now))
    multiplier = 1.0
    if status['pricing'] == 'active':
        plan = agent2(pickup, now_dt)
        ok, reason = check_price(plan['multiplier'], plan['expected'], plan['elapsed_ms'])
        if ok:
            multiplier = plan['multiplier']
            log.append(entry('Agent 2', f"{PLACES[pickup]} ×{multiplier:.1f}", 'passed',
                             plan['choice']['name'], now))
        else:
            log.append(entry('Agent 2', f"{PLACES[pickup]} ×{plan['multiplier']:.1f}", 'blocked', reason, now))
            log.append(entry('Guardian', 'Layer 1 base price ×1.0', 'fallback', 'price fallback', now))
        twin_info = dict(twin_info or {}, multiplier=multiplier, plan=plan['choice']['name'])
    return dict(choice=choice, why=why, multiplier=multiplier, twin=twin_info, log=log, layer=2)


def fault_drill(store, place: int, now_dt: dt.datetime) -> list[dict]:
    """Inject a faulty Agent 2 price (×4.0) in the twin and let the Guardian handle it end to end:
    block, fall back to Layer 1's base price, re-test Agent 2 with 500 rollouts, hand control back."""
    now = time.time()
    plan = agent2(place, now_dt)
    faulty = 4.0
    ok, reason = check_price(faulty, plan['expected'])
    log = [entry('Agent 2', f'{PLACES[place]} ×{faulty:.1f} (injected fault)', 'passed' if ok else 'blocked', reason, now)]
    if ok:      # never expected; reported rather than hidden
        return log
    log.append(entry('Guardian', 'Layer 1 base price ×1.0 while Agent 2 is re-tested', 'fallback',
                     'riders keep being served', now))
    passed, count = retest_pricing(seed=_seed('retest', window(now_dt)))
    log.append(entry('Guardian', f're-test Agent 2 in the twin · {count}/{RETEST_ROLLOUTS} rollouts',
                     'retested' if passed else 'blocked', 'passed' if passed else 'failed', now))
    if passed:
        log.append(entry('Guardian', 'control handed back to Agent 2', 'handed back', '', now))
    return log


def self_test(now_dt: dt.datetime | None = None) -> list[tuple[str, bool, str]]:
    """Layer 2 on known inputs. Shown in the Twin tab (Check Layer 2) and run by the unit tests."""
    now_dt = now_dt or dt.datetime(2026, 11, 4, 10, 0)
    results = []

    def run(name, fn):
        try:
            ok, detail = fn()
        except Exception as error:  # report, never crash the screen
            ok, detail = False, f'{type(error).__name__}: {error}'
        results.append((name, bool(ok), detail))

    def foresight():
        quiet = ratio_30(dt.datetime(2026, 11, 4, 10, 0))
        paddy = ratio_30(dt.datetime(2027, 3, 17, 13, 0))
        return paddy > 1.5 > quiet > .5, f'ordinary Wednesday ×{quiet:.2f} · St Patrick’s afternoon ×{paddy:.2f}'

    def dispatch():
        d = agent1(0, now_dt)
        ok = d['choice'].name == ai.choose(0)[0].name == 'Morgan' and len(d['rollouts']) == TOP_K
        return ok and check_dispatch(d)[0], ' · '.join(f'{c.name} {w:.1f}' for c, w in d['rollouts']) + ' min'

    def pricing():
        quiet = agent2(1, dt.datetime(2026, 11, 4, 10, 0))['multiplier']
        busy = agent2(1, dt.datetime(2027, 3, 17, 13, 0))
        return quiet == 1.0 and 1.0 < busy['multiplier'] <= PRICE_CAP, \
            f"ordinary ×{quiet:.1f} · St Patrick’s ×{busy['multiplier']:.1f} ({busy['choice']['name'].lower()})"

    def guardian():
        blocked = not check_price(4.0, 1.4)[0] and not check_price(0.8, 1.0)[0]
        passed, count = retest_pricing()
        return blocked and passed, f'blocks ×4.0 and ×0.8 · re-test {count}/{RETEST_ROLLOUTS}'

    run('Digital twin · foresee 30 min', foresight)
    run('Agent 1 · dispatch', dispatch)
    run('Agent 2 · pricing + moves', pricing)
    run('Agent 3 · Guardian', guardian)
    return results
