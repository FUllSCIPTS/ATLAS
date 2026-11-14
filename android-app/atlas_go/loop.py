"""Layer 1 live loop (1.4.0): LSTM predicts demand -> RL supply agent acts -> outcomes recorded ->
both models are updated and validated, on the phone, in pure Python.

1.2/1.3 used what the LSTM and the supply agent had learned as fixed tables (intelligence.py and
learned.py, which stay unchanged). 1.4 adds a running loop on top of those tables:

  Forecast  A compact LSTM (24 hours in, 16 hidden units, 6 hours out; trained by training/export_lstm.py
            on the 1.2 agent's experience log) runs every hour on the last 24 hours of served trips,
            unserved requests, boosts and the calendar, and forecasts demand for the next 1-6 hours.
  Act       The supply agent chooses how many extra drivers to add for the coming hour. Its state is the
            calendar context (tag, weekday type, hour) *and the LSTM's forecast level*.
  Record    The city reveals the hour's demand. Served trips, unserved requests, idle drivers, the
            forecast and the LSTM's hidden state are written to an experience log (14 days kept).
  Update    Once a day (at midnight in city time) two challengers are trained from the log:
              * LSTM: the output layer is refitted by SGD on the logged hidden states and the demand
                that followed (the recurrent weights are retrained offline with training/export_lstm.py);
              * agent: the Q-table that learned online, hour by hour, with hindsight from the log.
  Validate  Each challenger replaces the champion only if it does better on held-out recent data
            (LSTM: weighted forecast error on the last 24 hours; agent: cost of its decisions replayed
            over the last 7 days). Otherwise the champion stays and the rejection is logged.

The "city" is a simulation (the demand model of training/city_sim.py, made deterministic per hour). In a
live deployment the same loop would read real completed and unserved requests from the operator back end.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import os
import random
from pathlib import Path

from . import intelligence as ai
from . import learned
from . import lstm_weights as LW

EPOCH = dt.datetime(2025, 1, 1)
LOG_HOURS = 14 * 24          # experience kept on the phone
WARMUP = LW.L_IN             # hours simulated before the first forecast
REPLAY_HOURS = 7 * 24        # agent validation window
HOLDOUT = 24                 # LSTM validation window
MAX_CATCH_UP = 72            # hours processed on one tick; a longer gap restarts from a warm-up
UPDATES_KEPT = 30
TAG_MAP = {'stephens': 'bank_hol', 'new_year': 'bank_hol'}

# Ordinary hourly demand shape by day type (city_sim.WEEKDAY, FRIDAY, SATURDAY, SUNDAY)
WEEKDAY = (20, 12, 8, 6, 8, 25, 90, 260, 400, 300, 210, 220, 280, 250, 220, 240, 300, 380, 330, 240, 200, 170, 120, 60)
SATURDAY = (200, 220, 160, 80, 30, 15, 20, 40, 80, 140, 200, 260, 300, 310, 300, 290, 280, 270, 260, 280, 330, 380, 420, 380)
SUNDAY = (300, 260, 190, 90, 30, 12, 12, 25, 50, 90, 150, 200, 230, 230, 220, 210, 200, 200, 190, 170, 150, 120, 80, 40)
FRIDAY = WEEKDAY[:19] + (260, 300, 360, 420, 400)


def hour_index(t: dt.datetime) -> int:
    return int((t.replace(minute=0, second=0, microsecond=0, tzinfo=None) - EPOCH).total_seconds() // 3600)


def hour_time(i: int) -> dt.datetime:
    return EPOCH + dt.timedelta(hours=i)


# --------------------------------------------------------------------------- the simulated city

def tag(t: dt.datetime) -> str:
    """Calendar context in the LSTM's vocabulary (Layer 1's event_kind, with the same merges as training)."""
    kind = ai.event_kind(t.date(), t.hour)
    return TAG_MAP.get(kind, kind)


def weektype(t: dt.datetime) -> int:
    return 0 if t.weekday() < 4 else t.weekday() - 3


def ordinary(t: dt.datetime) -> float:
    """Ordinary demand for this weekday type and hour (what the fleet plans for), from Layer 1."""
    return float(learned.BASE_DEMAND[weektype(t)][t.hour])


def _rng(*parts) -> random.Random:
    return random.Random('|'.join(str(p) for p in parts))


def in_term(d: dt.date) -> bool:
    return dt.date(d.year, 1, 19) <= d <= dt.date(d.year, 5, 8) or dt.date(d.year, 9, 15) <= d <= dt.date(d.year, 12, 12)


def demand(t: dt.datetime) -> float:
    """Requests in one hour of the simulated city: the demand model of training/city_sim.py, with the same
    calendar effects, a deterministic rainy-day draw per date and ±8 % noise per hour."""
    d, h, wd = t.date(), t.hour, t.weekday()
    base = (WEEKDAY if wd < 4 else FRIDAY if wd == 4 else SATURDAY if wd == 5 else SUNDAY)[h]
    k = ai.event_kind(d, h)
    m = 1.0
    if in_term(d) and wd < 5 and 7 <= h <= 18:
        m *= 1.18
    if d.month in (6, 7, 8):
        m *= 1.06
    if _rng('rain', d.isoformat()).random() < .45:
        m *= 1.12
    if k in ('bank_hol', 'new_year', 'stephens'):
        base = SUNDAY[h] * .95
    if k == 'bh_sunday' and h >= 20:
        m *= 1.55
    if k == 'paddys':
        base = SUNDAY[h]
        m *= 2.6 if 10 <= h <= 14 else 2.0 if (h >= 18 or h <= 1) else 1.0
    if k == 'xmas_eve' and 13 <= h <= 20:
        m *= 1.9
    if k == 'xmas':
        m *= .25
    if k == 'stephens' and 18 <= h <= 23:
        m *= 1.6
    if k == 'nye':
        m *= 3.2 if (h >= 23 or h <= 2) else 1.6
    if k == 'jazz' and (h >= 19 or h <= 2):
        m *= 2.1
    if k == 'halloween' and h >= 18:
        m *= 1.7
    if k == 'xmas_shop' and 11 <= h <= 18:
        m *= 1.4
    growth = 1.0 + .08 * min(1.0, max(0.0, hour_index(t) / (24 * 730)))
    return base * m * growth * _rng('noise', hour_index(t)).lognormvariate(0, .08)


def calendar(t: dt.datetime) -> list[float]:
    """30 calendar inputs: hour and weekday on the unit circle and the event tag, now and 3 hours ahead."""
    out = []
    for u in (t, t + dt.timedelta(hours=3)):
        g = tag(u)
        out += [math.sin(2 * math.pi * u.hour / 24), math.cos(2 * math.pi * u.hour / 24),
                math.sin(2 * math.pi * u.weekday() / 7), math.cos(2 * math.pi * u.weekday() / 7)]
        out += [1.0 if g == x else 0.0 for x in LW.TAGS[1:]]
    return out


# --------------------------------------------------------------------------- the LSTM in pure Python

def _sig(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x)) if x >= 0 else math.exp(x) / (1.0 + math.exp(x))


def lstm_hidden(X: list[list[float]], W=LW.W, B=LW.B) -> list[float]:
    """Final hidden state after reading the window X (L_IN rows of inputs)."""
    nh = LW.NH
    h = [0.0] * nh
    c = [0.0] * nh
    for x in X:
        g = list(B)
        for zi, row in zip(list(x) + h, W):
            if zi:
                g = [gj + zi * wj for gj, wj in zip(g, row)]
        c = [_sig(g[nh + j]) * c[j] + _sig(g[j]) * math.tanh(g[3 * nh + j]) for j in range(nh)]
        h = [_sig(g[2 * nh + j]) * math.tanh(c[j]) for j in range(nh)]
    return h


def head(hidden: list[float], V, C) -> list[float]:
    return [C[k] + sum(hv * V[j][k] for j, hv in enumerate(hidden)) for k in range(LW.HZ)]


def level(ratio: float) -> int:
    return sum(ratio >= b for b in LW.BUCKETS)


# --------------------------------------------------------------------------- the loop

def _cost(dem: float, sup: float, boost: float) -> tuple[float, float, float]:
    unserved = max(0.0, dem - sup * (1 + boost))
    idle = min(max(0.0, sup * (1 + boost) - dem), sup * boost)
    return unserved, idle, unserved + LW.IDLE_COST * idle


def _key(t: dt.datetime, lv: int) -> str:
    g = tag(t)
    return f"{g}|{weektype(t) if g == 'ordinary' else 0}|{t.hour}|{lv}"


def fresh_state() -> dict:
    return dict(version=1, lstm=dict(name=LW.LSTM_VERSION, n=1, V=[list(r) for r in LW.V], C=list(LW.C)),
                agent=dict(name=LW.AGENT_VERSION, n=1, Q={}, NQ={}), challenger=dict(Q={}, NQ={}),
                log=[], cursor=None, updates=[], hours=0)


class Loop:
    """The running loop. Persisted to loop.json next to state.json; damaged files start fresh."""

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else None
        self.state = fresh_state()
        if self.path and self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding='utf-8'))
                self._validate(data)
                self.state = data
            except (ValueError, TypeError, KeyError, AttributeError):
                self.path.replace(self.path.with_suffix('.invalid.json'))

    # ---------------------------------------------------------------- persistence
    @staticmethod
    def _validate(data: dict) -> None:
        if not isinstance(data, dict) or data.get('version') != 1:
            raise ValueError('Unknown loop file.')
        lstm = data['lstm']
        if len(lstm['V']) != LW.NH or any(len(r) != LW.HZ for r in lstm['V']) or len(lstm['C']) != LW.HZ:
            raise ValueError('Invalid LSTM head.')
        if not all(isinstance(x, (int, float)) and math.isfinite(x) for r in lstm['V'] for x in r):
            raise ValueError('Invalid LSTM head values.')
        for part in (data['agent'], data['challenger']):
            if not isinstance(part['Q'], dict) or any(len(v) != len(LW.BOOSTS) for v in part['Q'].values()):
                raise ValueError('Invalid agent table.')
        if not isinstance(data['log'], list) or len(data['log']) > LOG_HOURS:
            raise ValueError('Invalid experience log.')
        for row in data['log']:
            if type(row.get('i')) is not int or len(row.get('x', [])) != 5 or len(row.get('h', [])) != LW.NH:
                raise ValueError('Invalid experience row.')
        if data['cursor'] is not None and type(data['cursor']) is not int:
            raise ValueError('Invalid cursor.')

    def save(self) -> None:
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix('.tmp')
        with tmp.open('w', encoding='utf-8') as stream:
            json.dump(self.state, stream, separators=(',', ':'))
            stream.flush()
            os.fsync(stream.fileno())
        tmp.replace(self.path)

    def reset(self) -> None:
        self.state = fresh_state()
        if self.path:
            self.path.unlink(missing_ok=True)
            self.path.with_suffix('.invalid.json').unlink(missing_ok=True)

    # ---------------------------------------------------------------- models
    def q(self, key: str, table: str = 'agent') -> list[float]:
        """Q-values for a state: learned online on this phone, else the exported table, else the
        (forecast level, hour) back-off table."""
        part = self.state[table]
        if key in part['Q']:
            return part['Q'][key]
        if table == 'challenger' and key in self.state['agent']['Q']:
            return self.state['agent']['Q'][key]
        if key in LW.Q:
            return LW.Q[key]
        lv, hour = int(key.rsplit('|', 1)[1]), int(key.split('|')[2])
        return LW.QB[lv][hour]

    def counts(self, key: str, table: str = 'challenger') -> int:
        part = self.state[table]
        return part['NQ'].get(key, self.state['agent']['NQ'].get(key, LW.NQ.get(key, 0)))

    def choose(self, key: str, table: str = 'agent') -> int:
        q = self.q(key, table)
        return max(range(len(q)), key=lambda a: (q[a], -a))

    def forecast(self, i: int) -> dict:
        """Forecast issued at the end of hour i-1 for hours i..i+5, from the logged window."""
        rows = self.window(i)
        X = [r['x'] + calendar(hour_time(r['i'])) for r in rows]
        hidden = lstm_hidden(X)
        lstm = self.state['lstm']
        ratios = [max(0.05, r) for r in head(hidden, lstm['V'], lstm['C'])]
        hours = [hour_time(i + k) for k in range(LW.HZ)]
        return dict(hidden=hidden, ratios=ratios, hours=hours,
                    requests=[r * ordinary(t) for r, t in zip(ratios, hours)], level=level(ratios[0]))

    # ---------------------------------------------------------------- experience
    def rows(self) -> dict:
        return {r['i']: r for r in self.state['log']}

    def window(self, i: int) -> list[dict]:
        by = self.rows()
        rows = [by.get(k) for k in range(i - LW.L_IN, i)]
        if any(r is None for r in rows):
            raise LookupError('The experience log does not cover the last 24 hours.')
        return rows

    def _record(self, i: int, boost: float, dem: float, fc: dict | None, decided_by: str) -> dict:
        t = hour_time(i)
        ty, ty_next = ordinary(t), ordinary(t + dt.timedelta(hours=1))
        sup = ty * 1.03
        unserved, idle, cost = _cost(dem, sup, boost)
        served = dem - unserved
        row = dict(i=i, x=[served / ty, unserved / ty, boost, ty / LW.SCALE, ty_next / LW.SCALE],
                   d=round(dem, 2), ty=round(ty, 2), boost=boost, un=round(unserved, 2), idle=round(idle, 2),
                   cost=round(cost, 2), by=decided_by,
                   f=[round(x, 4) for x in fc['ratios']] if fc else None,
                   h=[round(x, 6) for x in fc['hidden']] if fc else [0.0] * LW.NH,
                   lv=fc['level'] if fc else None)
        self.state['log'] = [r for r in self.state['log'] if r['i'] != i] + [row]
        self.state['log'].sort(key=lambda r: r['i'])
        del self.state['log'][:-LOG_HOURS]
        return row

    def warm_up(self, i: int) -> None:
        """Fill the 24 hours before hour i with the 1.2 calendar agent (the behaviour the LSTM was trained on)."""
        self.state['log'] = []
        for k in range(i - WARMUP, i):
            t = hour_time(k)
            g = tag(t)
            boost = learned.BOOST.get(f"{g}|{weektype(t) if g == 'ordinary' else 0}|{t.hour}", 0.0)
            self._record(k, boost, demand(t), None, 'warm-up')
        self.state['cursor'] = i - 1

    def step(self) -> dict:
        """One city hour: forecast -> act -> record -> learn online; daily update and validation at midnight."""
        i = self.state['cursor'] + 1
        t = hour_time(i)
        fc = self.forecast(i)
        key = _key(t, fc['level'])
        a = self.choose(key)
        dem = demand(t)
        row = self._record(i, LW.BOOSTS[a], dem, fc, 'LSTM + agent')
        row['key'] = key
        # online hindsight update of the challenger: every action's outcome is known from the logged demand
        sup = row['ty'] * 1.03
        target = [-_cost(dem, sup, b)[2] for b in LW.BOOSTS]
        ch = self.state['challenger']
        n = self.counts(key) + 1
        q = self.q(key, 'challenger')
        lr = max(.05, 1.0 / n)
        ch['Q'][key] = [round(qa + lr * (ta - qa), 3) for qa, ta in zip(q, target)]
        ch['NQ'][key] = n
        self.state['cursor'] = i
        self.state['hours'] += 1
        if t.hour == 23:
            self.daily_update(i)
        return row

    def advance_to(self, now: dt.datetime, limit: int = MAX_CATCH_UP) -> int:
        """Process every completed city hour up to now. Returns how many hours were processed."""
        target = hour_index(now) - 1
        cursor = self.state['cursor']
        if cursor is None or target < cursor - LW.L_IN or target - cursor > limit or not self.state['log']:
            self.warm_up(target + 1)
            return 0
        if target <= cursor:
            if target < cursor:                        # clock moved back (e.g. a pinned test clock)
                self.warm_up(target + 1)
            return 0
        done = 0
        while self.state['cursor'] < target:
            self.step()
            done += 1
        return done

    # ---------------------------------------------------------------- update and validation
    def _samples(self, until: int):
        """(hidden state, target ratios, weights) for forecasts whose six hours have all happened."""
        by = self.rows()
        out = []
        for r in self.state['log']:
            if r['f'] is None or r['i'] + LW.HZ - 1 > until:
                continue
            nxt = [by.get(r['i'] + k) for k in range(LW.HZ)]
            if any(x is None for x in nxt):
                continue
            ys = [min(5.0, x['d'] / x['ty']) for x in nxt]
            ws = [4.0 if y > 1.35 else 1.0 for y in ys]
            out.append((r['i'], r['h'], ys, ws))
        return out

    @staticmethod
    def _head_error(samples, V, C) -> float:
        err = tot = 0.0
        for _, hidden, ys, ws in samples:
            pred = head(hidden, V, C)
            for p, y, w in zip(pred, ys, ws):
                err += w * abs(p - y)
                tot += w
        return err / tot if tot else float('inf')

    def daily_update(self, i: int) -> dict:
        samples = self._samples(i)
        report = dict(t=hour_time(i).isoformat(), lstm=None, agent=None)
        lstm = self.state['lstm']
        if len(samples) >= HOLDOUT + 24:
            train, hold = samples[:-HOLDOUT], samples[-HOLDOUT:]
            V = [list(r) for r in lstm['V']]
            C = list(lstm['C'])
            lr = .02
            for _ in range(8):                         # SGD on the output layer, surge hours weighted
                for _, hidden, ys, ws in train:
                    pred = head(hidden, V, C)
                    for k in range(LW.HZ):
                        g = max(-1.0, min(1.0, ws[k] * (pred[k] - ys[k]))) * lr / LW.HZ
                        C[k] -= g
                        for j, hv in enumerate(hidden):
                            V[j][k] -= g * hv
            before, after = self._head_error(hold, lstm['V'], lstm['C']), self._head_error(hold, V, C)
            ok = all(math.isfinite(x) for r in V for x in r) and after <= before * .99
            if ok:
                lstm.update(V=[[round(x, 6) for x in r] for r in V], C=[round(x, 6) for x in C], n=lstm['n'] + 1)
            report['lstm'] = dict(accepted=ok, before=round(before, 4), after=round(after, 4), samples=len(train))
        # agent: replay the last 7 days with champion and challenger decisions, using the logged demand
        by = [r for r in self.state['log'] if r.get('key') and r['i'] > i - REPLAY_HOURS]
        if len(by) >= 24:
            def replay(table):
                return sum(_cost(r['d'], r['ty'] * 1.03, LW.BOOSTS[self.choose(r['key'], table)])[2] for r in by)
            champ, chall = replay('agent'), replay('challenger')
            ok = chall <= champ
            agent = self.state['agent']
            if ok:                                     # keep the refined values; a new version only if better
                agent['Q'].update(self.state['challenger']['Q'])
                agent['NQ'].update(self.state['challenger']['NQ'])
                agent['n'] += chall < champ - 1e-9
            self.state['challenger'] = dict(Q={}, NQ={})
            report['agent'] = dict(accepted=ok, improved=chall < champ - 1e-9, champion=round(champ, 1),
                                   challenger=round(chall, 1), hours=len(by))
        self.state['updates'] = (self.state['updates'] + [report])[-UPDATES_KEPT:]
        return report

    # ---------------------------------------------------------------- what the app shows
    def now(self, now: dt.datetime) -> dict:
        """Forecast for the current hour onward and the agent's decision for this hour."""
        i = hour_index(now)
        fc = self.forecast(i)
        t = hour_time(i)
        a = self.choose(_key(t, fc['level']))
        last = [r for r in self.state['log'] if r['f'] is not None][-24:]
        mape = (sum(abs(r['f'][0] * r['ty'] - r['d']) / r['d'] for r in last) / len(last)) if last else None
        return dict(forecast=fc, boost=LW.BOOSTS[a], ratio=fc['ratios'][0],
                    surge=max(0.0, min(1.0, (fc['ratios'][0] - 1.0) / 1.5)), mape_24h=mape,
                    lstm=f"{self.state['lstm']['name']}.{self.state['lstm']['n'] - 1}",
                    agent=f"{self.state['agent']['name']}.{self.state['agent']['n'] - 1}",
                    hours=self.state['hours'], updates=self.state['updates'][-3:])


def self_test() -> list[tuple[str, bool, str]]:
    """The loop's own checks (Intelligence screen and unit tests)."""
    results = []

    def run(name, fn):
        try:
            ok, detail = fn()
        except Exception as error:
            ok, detail = False, f'{type(error).__name__}: {error}'
        results.append((name, bool(ok), detail))

    def parity():
        y = head(lstm_hidden(LW.REF_X), LW.V, LW.C)
        gap = max(abs(a - b) for a, b in zip(y, LW.REF_Y))
        return gap < 1e-4, f'pure Python vs training forecast: max gap {gap:.1e}'

    def closed_loop():
        loop = Loop()
        start = dt.datetime(2026, 10, 22, 0)
        loop.warm_up(hour_index(start))
        for _ in range(48):
            loop.step()
        rows = [r for r in loop.state['log'] if r['f'] is not None]
        ok = len(rows) == 48 and len(loop.state['updates']) == 2 and all(r['key'] for r in rows)
        return ok, f"48 hours: forecast > act > record; {len(loop.state['updates'])} daily updates validated"

    run('Live LSTM (on this phone)', parity)
    run('LSTM > RL > outcomes > update', closed_loop)
    return results
