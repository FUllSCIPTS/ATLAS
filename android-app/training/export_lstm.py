"""Train the on-device LSTM forecaster and the forecast-aware supply agent, and export them for ATLAS Go 1.4.

Run from android-app/:  python training/export_lstm.py
Needs numpy (development only). Writes atlas_go/lstm_weights.py (pure Python constants).

What it does, on the two simulated years of Cork demand in city_sim.py:
  1. The 1.2 supply agent runs the city and logs its experience (served trips, unserved requests, boosts).
  2. A compact LSTM (24 hours in, 16 hidden units, 1-6 hours out) learns demand from that experience log
     plus the calendar - "model B" of city_sim.py, small enough to run in pure Python on a phone.
  3. A new supply agent learns, with hindsight Q-updates over the logged demand, how many extra drivers to
     add for each (LSTM forecast level, hour). Its state is the LSTM's forecast: LSTM predicts -> RL acts.
  4. Both are evaluated on the held-out last quarter (Jul-Dec 2026) against the 1.2 calendar agent.
On the phone (atlas_go/loop.py) the loop continues: outcomes are recorded every hour and both models are
updated and validated (champion / challenger) once a day.
"""
import json
import pprint
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import city_sim as cs  # noqa: E402

OUT = HERE.parent / 'atlas_go' / 'lstm_weights.py'
L_IN, NH, HZ, SCALE = 24, 16, 6, 400.0
BUCKETS = (1.05, 1.15, 1.3, 1.5, 1.8, 2.2, 3.0)   # LSTM forecast / ordinary demand -> 8 levels
IDLE_COST = 0.25


def bucket(ratio: float) -> int:
    return sum(ratio >= b for b in BUCKETS)


def windows(F, target, idxs, L):
    X = np.stack([F[i - L + 1:i + 1] for i in idxs])
    Y = np.stack([target[i + 1:i + 1 + HZ] for i in idxs])
    return X, Y


def train(F, target, surge_w, idx, epochs=40, seed=3):
    model = cs.LSTM(F.shape[1], NH, HZ, seed)
    r = np.random.default_rng(seed)
    for ep in range(epochs):
        r.shuffle(idx)
        tot = 0.0
        for b in range(0, len(idx), 128):
            ids = idx[b:b + 128]
            X, Y = windows(F, target, ids, L_IN)
            W_ = np.stack([surge_w[i + 1:i + 1 + HZ] for i in ids])
            tot += model.step(X, Y, W_, 4e-3 if ep < 25 else 1e-3)
        print(f'  epoch {ep} loss {tot / (len(idx) / 128):.4f}', flush=True)
    return model


def predict(model, F, idxs):
    out = []
    for b in range(0, len(idxs), 512):
        X = np.stack([F[i - L_IN + 1:i + 1] for i in idxs[b:b + 512]])
        out.append(model.forward(X)[0])
    return np.concatenate(out)


def main():
    D = cs.demand_series()
    TY = cs.typical(D)
    S = TY * 1.03
    boost12, un_rl, un_base, idle12 = cs.run_rl(D, S)
    served = np.minimum(D, S * (1 + boost12))
    cal = np.concatenate([cs.calendar_feats(0), cs.calendar_feats(3)], 1)
    # Inputs relative to the ordinary demand the fleet plans for; the LSTM predicts demand / ordinary.
    ty_next = np.roll(TY, -1)
    F = np.concatenate([np.stack([served / TY, un_rl / TY, boost12, TY / SCALE, ty_next / SCALE], 1), cal], 1)
    surge = D > 1.35 * TY
    surge_w = 1 + 3 * surge.astype(float)
    split = int(cs.HOURS * 0.75)
    train_idx = np.arange(L_IN, split - HZ)
    test_idx = np.arange(split, cs.HOURS - HZ)
    print(f'LSTM {F.shape[1]} inputs, {NH} hidden, {L_IN} h in, {HZ} h out')
    model = train(F, np.minimum(D / TY, 5.0), surge_w, train_idx.copy())   # tiny night hours can reach 40x

    all_idx = np.arange(L_IN, cs.HOURS - HZ)
    P = predict(model, F, all_idx) * np.stack([TY[all_idx + k] for k in range(1, HZ + 1)], 1)
    pred1 = np.full(cs.HOURS, np.nan)
    pred1[all_idx + 1] = P[:, 0]                     # forecast of hour t+1, issued at hour t

    # ---- forecast-aware supply agent. State: calendar context the 1.2 agent used (tag, weekday type, hour)
    # plus the LSTM's forecast level for the coming hour; a (level, hour) table backs off for unseen states.
    def ckey(i):
        t = cs.T[i]
        tag = cs.event_tag(t.date(), t.hour)
        tag = 'ordinary' if tag in ('storm', 'match') else tag      # not knowable in advance on the phone
        wt = 0 if t.weekday() < 4 else t.weekday() - 3
        return f"{tag}|{wt if tag == 'ordinary' else 0}|{t.hour}"
    Qf, Nf = {}, {}
    Qb = np.zeros((len(BUCKETS) + 1, 24, len(cs.BOOSTS)))
    Nb = np.zeros((len(BUCKETS) + 1, 24))
    def cost_all(i):
        sup = S[i] * (1 + cs.BOOSTS)
        return np.maximum(0, D[i] - sup) + IDLE_COST * np.minimum(np.maximum(0, sup - D[i]), S[i] * cs.BOOSTS)
    for i in range(L_IN + 1, split):                 # learn on the training period only
        if np.isnan(pred1[i]):
            continue
        lv = bucket(pred1[i] / TY[i])
        k = f'{ckey(i)}|{lv}'
        Qf.setdefault(k, np.zeros(len(cs.BOOSTS))); Nf[k] = Nf.get(k, 0) + 1
        Qf[k] += (1.0 / Nf[k]) * (-cost_all(i) - Qf[k])   # hindsight: every action's outcome is in the log
        s_ = (lv, cs.T[i].hour)
        Nb[s_] += 1
        Qb[s_] += (1.0 / Nb[s_]) * (-cost_all(i) - Qb[s_])
    def act(i):
        lv = bucket(pred1[i] / TY[i])
        k = f'{ckey(i)}|{lv}'
        return int(np.argmax(Qf[k])) if k in Qf else int(np.argmax(Qb[lv, cs.T[i].hour]))

    # ---- held-out evaluation (Jul-Dec 2026)
    res = {}
    test_hours = [i for i in range(split, cs.HOURS) if not np.isnan(pred1[i])]
    c12 = sum(cost_all(i)[int(np.where(cs.BOOSTS == boost12[i])[0][0])] for i in test_hours)
    c14 = sum(cost_all(i)[act(i)] for i in test_hours)
    c0 = sum(cost_all(i)[0] for i in test_hours)
    un12 = sum(max(0, D[i] - S[i] * (1 + boost12[i])) for i in test_hours)
    un14 = sum(max(0, D[i] - S[i] * (1 + cs.BOOSTS[act(i)])) for i in test_hours)
    res['supply'] = dict(cost_no_boost=round(float(c0)), cost_calendar_agent=round(float(c12)),
                         cost_lstm_agent=round(float(c14)), unserved_calendar_agent=round(float(un12)),
                         unserved_lstm_agent=round(float(un14)), hours=len(test_hours))
    Pt = predict(model, F, test_idx) * np.stack([TY[test_idx + k] for k in range(1, HZ + 1)], 1)
    for hz in (1, 3, 6):
        tgt = D[test_idx + hz]
        ty = TY[test_idx + hz]
        sg = tgt > 1.35 * ty
        ps = Pt[:, hz - 1] > 1.35 * ty
        res[f'h{hz}'] = dict(mape=round(float(np.mean(np.abs(Pt[:, hz - 1] - tgt) / tgt)), 3),
                             surge_recall=round(float((sg & ps).sum() / max(1, sg.sum())), 3),
                             surge_precision=round(float((sg & ps).sum() / max(1, ps.sum())), 3))
    print(json.dumps(res, indent=1))

    # a reference window for the parity test: 24 h of features ending 2026-10-24 21:00 (Jazz Saturday)
    ref_end = cs.T.index(cs.dt.datetime(2026, 10, 24, 21))
    ref_x = F[ref_end - L_IN + 1:ref_end + 1]
    ref_y = model.forward(ref_x[None])[0][0]

    r = lambda a: np.round(a, 6).tolist()
    W, b, V, c = model.params
    body = (
        '"""On-device LSTM forecaster and forecast-aware supply agent, exported by training/export_lstm.py.\n\n'
        'Do not edit by hand. Learned from two simulated years of Cork demand (training/city_sim.py), using the\n'
        "1.2 supply agent's experience log (served trips, unserved requests, boosts) as LSTM input. Synthetic data only.\n"
        '"""\n\n'
        f"LSTM_VERSION = 'lstm-1.0'\nAGENT_VERSION = 'supply-1.0'\n"
        f'L_IN, NH, HZ, SCALE = {L_IN}, {NH}, {HZ}, {SCALE}\n'
        f'BUCKETS = {BUCKETS}\nBOOSTS = {cs.BOOSTS.tolist()}\nIDLE_COST = {IDLE_COST}\n'
        f'TAGS = {cs.TAGS}\n\n'
        '# LSTM: gates [input, forget, output, cell] = [x_t, h_{t-1}] @ W + b; forecast = h_L @ V + c\n'
        '# Inputs per hour: served/ordinary, unserved/ordinary, boost, ordinary/SCALE, next ordinary/SCALE, 30 calendar\n'
        '# features (hour, weekday, 11 event tags; now and 3 h ahead). Output: demand/ordinary for the next 1-6 hours.\n'
        f'W = {r(W)}\nB = {r(b)}\nV = {r(V)}\nC = {r(c)}\n\n'
        '# Supply agent Q-values (negative expected cost per boost), keyed "tag|weekday type|hour|forecast level",\n'
        '# with visit counts; QB/NB back off to [forecast level][hour] for unseen calendar states\n'
        f'Q = {pprint.pformat({k: np.round(v, 2).tolist() for k, v in sorted(Qf.items())}, width=120, compact=True)}\n'
        f'NQ = {pprint.pformat(dict(sorted(Nf.items())), width=120, compact=True)}\n'
        f'QB = {pprint.pformat(np.round(Qb, 2).tolist(), width=120, compact=True)}\n'
        f'NB = {Nb.astype(int).tolist()}\n\n'
        '# Held-out evaluation, Jul-Dec 2026 (simulation)\n'
        f'METRICS = {pprint.pformat(res, width=110)}\n\n'
        '# Parity check: one input window and the numpy forecast for it\n'
        f'REF_X = {r(ref_x)}\nREF_Y = {r(ref_y)}\n')
    OUT.write_text(body, encoding='utf-8')
    print('wrote', OUT)


if __name__ == '__main__':
    main()
