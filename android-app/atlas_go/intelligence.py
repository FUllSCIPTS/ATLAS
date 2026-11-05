"""ATLAS intelligence for the offline app: what the reinforcement-learning agents learned, in pure Python.

Four pieces, all running on the device without network access or numpy:
  * Irish public-holiday calendar and Cork events (computed for any year)
  * Surge outlook - hourly demand learned from two simulated years, plus the hours the supply
    agent learned to add drivers
  * Ride dispatch policy - ranks candidate drivers and explains the choice
  * Courier timing - when to send the courier so they arrive as the food is ready
  * Learning lab - a sandbox that retrains a dispatch policy from scratch on the device; its
    candidates are never used for dispatch (approval happens offline, as in the reference design)

All numbers come from synthetic simulations (see training/). They are illustrative, not
measurements of real riders, drivers, kitchens or traffic.
"""
from __future__ import annotations

import datetime as dt
import math
import random
from dataclasses import dataclass

from . import learned as L

# --------------------------------------------------------------------------- calendar

def easter_sunday(year: int) -> dt.date:
    """Gregorian Easter (anonymous algorithm)."""
    a, b, c = year % 19, year // 100, year % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l_ = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l_) // 451
    month = (h + l_ - 7 * m + 114) // 31
    day = ((h + l_ - 7 * m + 114) % 31) + 1
    return dt.date(year, month, day)


def first_monday(year: int, month: int) -> dt.date:
    d = dt.date(year, month, 1)
    return d + dt.timedelta(days=(7 - d.weekday()) % 7)


def last_monday(year: int, month: int) -> dt.date:
    d = dt.date(year + (month == 12), month % 12 + 1, 1) - dt.timedelta(days=1)
    return d - dt.timedelta(days=d.weekday())


def public_holidays(year: int) -> dict[dt.date, str]:
    """Ireland's public holidays. St Brigid's Day (from 2023) is 1 February when that is a Friday,
    otherwise the first Monday in February. Substitute days for weekend holidays are not modelled."""
    days = {
        dt.date(year, 1, 1): "New Year's Day",
        dt.date(year, 3, 17): "St Patrick's Day",
        easter_sunday(year) + dt.timedelta(days=1): 'Easter Monday',
        first_monday(year, 5): 'May Bank Holiday',
        first_monday(year, 6): 'June Bank Holiday',
        first_monday(year, 8): 'August Bank Holiday',
        last_monday(year, 10): 'October Bank Holiday',
        dt.date(year, 12, 25): 'Christmas Day',
        dt.date(year, 12, 26): "St Stephen's Day",
    }
    if year >= 2023:
        feb1 = dt.date(year, 2, 1)
        days[feb1 if feb1.weekday() == 4 else first_monday(year, 2)] = "St Brigid's Day"
    return days


def jazz_weekend(year: int) -> set[dt.date]:
    """Cork Jazz Festival runs over the October bank holiday weekend (Friday to Sunday)."""
    monday = last_monday(year, 10)
    return {monday - dt.timedelta(days=k) for k in (1, 2, 3)}


KIND_TITLES = {
    'paddys': "St Patrick's Day", 'xmas_eve': 'Christmas Eve', 'xmas': 'Christmas Day', 'stephens': "St Stephen's Day",
    'new_year': "New Year's Day", 'nye': "New Year's Eve", 'jazz': 'Cork Jazz weekend', 'halloween': 'Halloween',
    'bh_sunday': 'Bank holiday Sunday', 'xmas_shop': 'Christmas shopping Saturday', 'bank_hol': 'Bank holiday',
}


def event_kind(day: dt.date, hour: int) -> str:
    """Calendar context for one hour. Mirrors the agent's state in training/city_sim.py."""
    holidays = public_holidays(day.year)
    name = holidays.get(day)
    if (day.month == 12 and day.day == 31 and hour >= 20) or (day.month == 1 and day.day == 1 and hour <= 3):
        return 'nye'
    if name == "St Patrick's Day":
        return 'paddys'
    if day.month == 12 and day.day == 24:
        return 'xmas_eve'
    if name == 'Christmas Day':
        return 'xmas'
    if day in jazz_weekend(day.year):
        return 'jazz'
    if day.month == 10 and day.day == 31:
        return 'halloween'
    if name:
        return {"St Stephen's Day": 'stephens', "New Year's Day": 'new_year'}.get(name, 'bank_hol')
    tomorrow = day + dt.timedelta(days=1)
    if day.weekday() == 6 and tomorrow in public_holidays(tomorrow.year):
        return 'bh_sunday'
    if day.month == 12 and day.day <= 23 and day.weekday() == 5:
        return 'xmas_shop'
    return 'ordinary'


def agent_tag(kind: str) -> str:
    return 'bank_hol' if kind in ('stephens', 'new_year') else kind


def weektype(day: dt.date) -> int:
    return 0 if day.weekday() < 4 else day.weekday() - 3


# --------------------------------------------------------------------------- surge outlook

SURGE_FACTOR = 1.35      # demand at least 35 % above an ordinary same weekday-hour ...
SURGE_FLOOR = 60         # ... and at least 60 extra requests/hour


@dataclass(frozen=True)
class Hour:
    hour: int
    kind: str
    ordinary: float
    expected: float
    boost: float

    @property
    def ratio(self) -> float:
        return self.expected / self.ordinary if self.ordinary else 1.0

    @property
    def surge(self) -> bool:
        return self.expected >= SURGE_FACTOR * self.ordinary and self.expected - self.ordinary >= SURGE_FLOOR


def outlook(day: dt.date) -> list[Hour]:
    wt = weektype(day)
    hours = []
    for h in range(24):
        kind = event_kind(day, h)
        ordinary = L.BASE_DEMAND[wt][h]
        ratio = L.SURGE_RATIO.get(kind, [1.0] * 24)[h] if kind != 'ordinary' else 1.0
        tag = agent_tag(kind)
        boost = L.BOOST.get(f'{tag}|{wt if tag == "ordinary" else 0}|{h}', 0.0)
        hours.append(Hour(h, kind, ordinary, ordinary * ratio, boost))
    return hours


def windows(flags: list[bool]) -> list[tuple[int, int]]:
    """Contiguous runs of True as (start hour, end hour exclusive)."""
    runs, start = [], None
    for h, flag in enumerate(flags + [False]):
        if flag and start is None:
            start = h
        elif not flag and start is not None:
            runs.append((start, h))
            start = None
    return runs


def clock(h: int) -> str:
    return f'{h % 24:02d}:00'


def span(run: tuple[int, int]) -> str:
    return f'{clock(run[0])}–{clock(run[1])}'


def ratio_text(r: float) -> str:
    return f'{r:.1f}× usual' if r >= 3 else f'+{round((r - 1) * 100)}%'


def day_title(day: dt.date) -> str:
    kinds = [k for k in dict.fromkeys(event_kind(day, h) for h in range(24)) if k != 'ordinary']
    name = public_holidays(day.year).get(day)
    titles = []
    for k in kinds:
        if k == 'bank_hol' and name:
            titles.append(name)
        elif k == 'nye' and day.month == 1:
            continue  # the small hours of 1 January belong to New Year's Eve's story
        else:
            titles.append(KIND_TITLES[k])
    return ' · '.join(titles) if titles else 'An ordinary ' + day.strftime('%A')


def day_summary(day: dt.date) -> dict:
    hours = outlook(day)
    surge_runs = windows([h.surge for h in hours])
    boost_runs = windows([h.boost > 0 for h in hours])
    busiest = max(hours, key=lambda h: h.expected)
    peak = max((h for h in hours if h.surge), key=lambda h: h.expected, default=None)
    total = sum(h.expected for h in hours)
    ordinary_total = sum(h.ordinary for h in hours)
    if peak:
        text = (f'Surge {", ".join(span(r) for r in surge_runs)} · peak about {round(peak.expected)} requests/hour '
                f'at {clock(peak.hour)} (usually {round(peak.ordinary)})')
    elif total < 0.6 * ordinary_total:
        text = f'Quiet day: about {round(100 * total / ordinary_total)}% of a usual {day.strftime("%A")}'
    else:
        text = f'No surge expected · busiest around {clock(busiest.hour)}'
    if boost_runs:
        top = max(h.boost for h in hours)
        weight = {r: sum(hours[h].boost for h in range(*r)) for r in boost_runs}
        shown = sorted(sorted(boost_runs, key=lambda r: -weight[r])[:3])
        agent = f'ATLAS adds up to {round(top * 100)}% more drivers, {", ".join(span(r) for r in shown)}'
    else:
        agent = 'ATLAS keeps the normal fleet'
    return dict(title=day_title(day), surge=bool(surge_runs), text=text, agent=agent, hours=hours,
                total=round(total), ordinary_total=round(ordinary_total))


def upcoming(today: dt.date, days: int = 120, limit: int = 6) -> list[dict]:
    """Next calendar days the agent has learned to treat differently."""
    found = []
    for k in range(1, days + 1):
        day = today + dt.timedelta(days=k)
        if all(event_kind(day, h) == 'ordinary' for h in range(24)):
            continue
        summary = day_summary(day)
        summary['date'] = day
        found.append(summary)
        if len(found) >= limit:
            break
    return found


# --------------------------------------------------------------------------- ride dispatch

@dataclass(frozen=True)
class Candidate:
    name: str
    zone: str
    eta: int          # minutes to pickup
    accept: float     # predicted probability of accepting the offer (discrete model)
    surge: float      # forecast surge in the driver's current zone, next 10 minutes (0-1)
    last: bool        # last free driver in that zone

    def features(self) -> list[float]:
        return [-self.eta / 5.0, self.accept, -(self.surge * self.last), -self.surge]


# Illustrative candidates near each saved pickup place (index matches domain.PLACES).
DRIVER_POOLS = (
    (Candidate('Ava', 'Mardyke', 2, .81, .85, True), Candidate('Morgan', 'Western Road', 3, .94, .10, False),
     Candidate('Niamh', 'City Centre', 6, .88, .30, False), Candidate('Ciarán', 'Douglas', 8, .97, .05, False)),
    (Candidate('Dara', 'Oliver Plunkett St', 1, .35, .20, False), Candidate('Sam', 'Grand Parade', 3, .92, .15, False),
     Candidate('Rory', 'MacCurtain St', 4, .90, .60, True), Candidate('Leah', 'South Mall', 5, .95, .10, False)),
    (Candidate('Eoin', 'Kent Station', 2, .90, .25, False), Candidate('Aoife', 'Lower Glanmire Rd', 4, .93, .10, False),
     Candidate('Tadhg', 'Montenotte', 6, .96, .05, False), Candidate('Sinéad', 'Blackpool', 7, .89, .40, True)),
    (Candidate('Conor', 'Airport rank', 1, .97, .00, False), Candidate('Fiona', 'Ballygarvan', 5, .95, .05, False),
     Candidate('Paddy', 'Frankfield', 7, .90, .10, False), Candidate('Orla', 'Douglas', 9, .96, .15, False)),
)


def score(c: Candidate, weights=L.RIDE_WEIGHTS) -> float:
    return sum(w * f for w, f in zip(weights, c.features()))


def rank(pickup: int, weights=L.RIDE_WEIGHTS) -> list[tuple[Candidate, float]]:
    """Candidates with their policy probability, best first. Dispatch takes the top one."""
    pool = DRIVER_POOLS[pickup]
    scores = [score(c, weights) for c in pool]
    top = max(scores)
    exps = [math.exp(s - top) for s in scores]
    total = sum(exps)
    return sorted(((c, e / total) for c, e in zip(pool, exps)), key=lambda x: -x[1])


def choose(pickup: int) -> tuple[Candidate, str]:
    ranked = rank(pickup)
    chosen = ranked[0][0]
    nearest = min(DRIVER_POOLS[pickup], key=lambda c: c.eta)
    return chosen, explain(chosen, nearest)


def explain(chosen: Candidate, nearest: Candidate, weights=L.RIDE_WEIGHTS) -> str:
    if chosen == nearest:
        return (f'{chosen.name} is the nearest driver ({chosen.eta} min), likely to accept '
                f'({round(chosen.accept * 100)}%), and no busy area loses its last car.')
    diffs = [w * (a - b) for w, a, b in zip(weights, chosen.features(), nearest.features())]
    reasons = []
    order = sorted(range(4), key=lambda i: -diffs[i])
    for i in order:
        if diffs[i] <= 0.2:
            continue
        if i == 2:
            reasons.append(f'{nearest.name} is the last free driver at {nearest.zone}, where a surge is forecast '
                           f'({round(nearest.surge * 100)}%)')
        elif i == 1:
            reasons.append(f'{chosen.name} is far more likely to accept ({round(chosen.accept * 100)}% vs '
                           f'{round(nearest.accept * 100)}%)')
        elif i == 3:
            reasons.append(f'it avoids pulling a car from busier {nearest.zone}')
    if not reasons:
        reasons.append('the overall score is higher')
    return (f'{chosen.name} is {chosen.eta - nearest.eta} min further than {nearest.name}, but '
            + ' and '.join(reasons[:2]) + '.')


# --------------------------------------------------------------------------- courier timing

PREP_MINUTES = (12, 15, 18)   # kitchen estimates per restaurant (illustrative)
COURIER_TRAVEL = 4            # minutes from the courier to the kitchen


def courier_plan(restaurant: int) -> dict:
    prep = PREP_MINUTES[restaurant]
    slack = max(min(L.COURIER_DELAY), min(max(L.COURIER_DELAY), round(prep - COURIER_TRAVEL)))
    wait = L.COURIER_DELAY[slack]
    arrive = wait + COURIER_TRAVEL
    return dict(prep=prep, travel=COURIER_TRAVEL, dispatch_after=wait, arrive=arrive,
                courier_wait=max(0, prep - arrive), naive_wait=max(0, prep - COURIER_TRAVEL))


def courier_text(plan: dict) -> str:
    return (f"Kitchen needs about {plan['prep']} min. ATLAS sends the courier after {plan['dispatch_after']} min, "
            f"so they arrive as the food is ready: about {plan['courier_wait']} min at the counter instead of "
            f"{plan['naive_wait']}.")


# --------------------------------------------------------------------------- learning lab (sandbox)

def _candidates(r: random.Random) -> list[Candidate]:
    return [Candidate('', '', r.uniform(1.0, 9.0), r.uniform(.35, .98), r.uniform(0.0, 1.0) ** 1.5, r.uniform(0, 1) < .45)
            for _ in range(4)]


def expected_cost(c: Candidate) -> float:
    """Expected waiting-cost in minutes of offering this driver (same model as training/rl_sim.py)."""
    p_late = max(0.0, min(1.0, (c.eta + 1.5 + 5.0 - 8.0) / 3.0))
    pickup = c.accept * c.eta + (1 - c.accept) * (c.eta + 1.5 + 3.5)
    cancel = 0.45 * (c.accept * (c.eta > 8.0) + (1 - c.accept) * p_late)
    shortage = c.surge * c.last * 10.0
    return pickup + 10.0 * cancel + shortage


class LearningLab:
    """Retrains a ride-dispatch policy from zero on the device with REINFORCE.

    Sandbox only: the candidate is evaluated against the bundled approved policy and the
    nearest-driver rule, and is never used to dispatch a ride."""

    TOTAL = L.TRAINING_EPISODES

    def __init__(self, seed: int = 7, test_size: int = 300):
        self.seed = seed
        test = random.Random(seed + 1000)
        self.test = [_candidates(test) for _ in range(test_size)]
        self.nearest = self._eval(lambda cs: min(range(4), key=lambda i: cs[i].eta))
        self.approved = self._eval_policy(L.RIDE_WEIGHTS, greedy=True)
        self.reset()

    def reset(self) -> None:
        self.rng = random.Random(self.seed)
        self.w = [0.0, 0.0, 0.0, 0.0]
        self.base = -10.0
        self.episodes = 0
        self.curve = [(1, self._eval_policy(self.w, greedy=False))]
        self._next_check = 2

    @property
    def done(self) -> bool:
        return self.episodes >= self.TOTAL

    def _eval(self, pick) -> float:
        return sum(expected_cost(cs[pick(cs)]) for cs in self.test) / len(self.test)

    def _eval_policy(self, weights, greedy: bool) -> float:
        total = 0.0
        for cs in self.test:
            scores = [score(c, weights) for c in cs]
            if greedy:
                total += expected_cost(cs[max(range(4), key=lambda i: scores[i])])
            else:
                top = max(scores)
                ex = [math.exp(s - top) for s in scores]
                z = sum(ex)
                total += sum(e / z * expected_cost(c) for e, c in zip(ex, cs))
        return total / len(self.test)

    def train(self, episodes: int, lr: float = 0.004) -> None:
        r = self.rng
        for _ in range(min(episodes, self.TOTAL - self.episodes)):
            cs = _candidates(r)
            phi = [c.features() for c in cs]
            scores = [sum(w * f for w, f in zip(self.w, p)) for p in phi]
            top = max(scores)
            ex = [math.exp(s - top) for s in scores]
            z = sum(ex)
            probs = [e / z for e in ex]
            a = r.choices(range(4), weights=probs)[0]
            c = cs[a]
            accepted = r.random() < c.accept
            pickup = c.eta if accepted else c.eta + 1.5 + r.uniform(2.0, 5.0)
            cancel = pickup > 8.0 and r.random() < 0.45
            shortage = c.surge * c.last * r.uniform(6.0, 14.0)
            reward = -pickup - 10.0 * cancel - shortage
            mean_phi = [sum(p * f[k] for p, f in zip(probs, phi)) for k in range(4)]
            for k in range(4):
                self.w[k] += lr * (reward - self.base) * (phi[a][k] - mean_phi[k])
            self.base += 0.01 * (reward - self.base)
            self.episodes += 1
            if self.episodes >= self._next_check or self.episodes == self.TOTAL:
                self.curve.append((self.episodes, self._eval_policy(self.w, greedy=False)))
                self._next_check = max(self._next_check + 1, int(self._next_check * 1.35))

    def result(self) -> dict:
        return dict(episodes=self.episodes, candidate=self._eval_policy(self.w, greedy=True),
                    behaviour=self.curve[-1][1], nearest=self.nearest, approved=self.approved,
                    weights=[round(x, 2) for x in self.w])
