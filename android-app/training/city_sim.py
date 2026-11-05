"""Two years of synthetic ride demand in Cork (2025-2026), an RL supply agent, and an LSTM surge forecaster.

Everything here is a toy model built for the ATLAS Go video. Calendar dates are Ireland's real public
holidays for 2025 and 2026; festival, match and storm days are illustrative.

Pipeline (mirrors the story told in the video):
  1. Demand  - hourly latent ride requests with daily/weekly rhythm, UCC term, rain, holidays and events.
  2. Supply  - a fleet schedule planned for an ordinary day of the same weekday and hour.
  3. RL      - every hour the agent picks how many extra drivers to pre-position (0..100 % boost).
               Reward = -(riders left unserved) - 0.25 * (extra drivers left idle).
               It logs every outcome, including the requests that went unserved.
  4. LSTM    - forecasts demand 1..6 hours ahead.  Model A sees only completed trips (censored at fleet
               capacity).  Model B also receives the RL agent's experience log (unserved requests,
               its boost decisions) and is trained on the uncensored demand that log reveals.
"""
import json
import datetime as dt
import numpy as np

rng = np.random.default_rng(2026)
START = dt.datetime(2025, 1, 1)
HOURS = 24 * 730
T = [START + dt.timedelta(hours=h) for h in range(HOURS)]

HOL = {  # Irish public holidays
    dt.date(2025, 1, 1): "New Year's Day", dt.date(2025, 2, 3): "St Brigid's Day", dt.date(2025, 3, 17): "St Patrick's Day",
    dt.date(2025, 4, 21): 'Easter Monday', dt.date(2025, 5, 5): 'May Bank Holiday', dt.date(2025, 6, 2): 'June Bank Holiday',
    dt.date(2025, 8, 4): 'August Bank Holiday', dt.date(2025, 10, 27): 'October Bank Holiday', dt.date(2025, 12, 25): 'Christmas Day',
    dt.date(2025, 12, 26): "St Stephen's Day",
    dt.date(2026, 1, 1): "New Year's Day", dt.date(2026, 2, 2): "St Brigid's Day", dt.date(2026, 3, 17): "St Patrick's Day",
    dt.date(2026, 4, 6): 'Easter Monday', dt.date(2026, 5, 4): 'May Bank Holiday', dt.date(2026, 6, 1): 'June Bank Holiday',
    dt.date(2026, 8, 3): 'August Bank Holiday', dt.date(2026, 10, 26): 'October Bank Holiday', dt.date(2026, 12, 25): 'Christmas Day',
    dt.date(2026, 12, 26): "St Stephen's Day",
}
JAZZ = {dt.date(2025, 10, d) for d in (24, 25, 26)} | {dt.date(2026, 10, d) for d in (23, 24, 25)}
MATCH = {dt.date(2025, 5, 18), dt.date(2025, 6, 8), dt.date(2025, 6, 22), dt.date(2025, 7, 6),
         dt.date(2026, 5, 17), dt.date(2026, 6, 7), dt.date(2026, 6, 21), dt.date(2026, 7, 5)}
STORM = {dt.date(2025, 2, 21), dt.date(2025, 11, 14), dt.date(2026, 2, 13), dt.date(2026, 11, 20)}
XMAS_SHOP = {d for y in (2025, 2026) for d in (dt.date(y, 12, k) for k in range(1, 24)) if d.weekday() == 5}
NYE = {dt.date(2025, 12, 31), dt.date(2026, 12, 31)}
EVE = {dt.date(2025, 12, 24), dt.date(2026, 12, 24)}
HALLOWEEN = {dt.date(2025, 10, 31), dt.date(2026, 10, 31)}


def in_term(d):
    return (dt.date(d.year, 1, 19) <= d <= dt.date(d.year, 5, 8)) or (dt.date(d.year, 9, 15) <= d <= dt.date(d.year, 12, 12))


WEEKDAY = np.array([20, 12, 8, 6, 8, 25, 90, 260, 400, 300, 210, 220, 280, 250, 220, 240, 300, 380, 330, 240, 200, 170, 120, 60], float)
SATURDAY = np.array([200, 220, 160, 80, 30, 15, 20, 40, 80, 140, 200, 260, 300, 310, 300, 290, 280, 270, 260, 280, 330, 380, 420, 380], float)
SUNDAY = np.array([300, 260, 190, 90, 30, 12, 12, 25, 50, 90, 150, 200, 230, 230, 220, 210, 200, 200, 190, 170, 150, 120, 80, 40], float)
FRIDAY = WEEKDAY.copy(); FRIDAY[19:] = [260, 300, 360, 420, 400]


def event_tag(d, h):
    """The calendar context the agent can see in advance (used as RL state and LSTM feature)."""
    if d in NYE and h >= 20 or (d.month == 1 and d.day == 1 and h <= 3):
        return 'nye'
    if d in HOL and HOL[d] == "St Patrick's Day":
        return 'paddys'
    if d in EVE:
        return 'xmas_eve'
    if d in HOL and HOL[d] == 'Christmas Day':
        return 'xmas'
    if d in JAZZ:
        return 'jazz'
    if d in MATCH:
        return 'match'
    if d in STORM:
        return 'storm'
    if d in HALLOWEEN:
        return 'halloween'
    if d in HOL:
        return 'bank_hol'
    nxt = d + dt.timedelta(days=1)
    if nxt in HOL and d.weekday() == 6:
        return 'bh_sunday'
    if d in XMAS_SHOP:
        return 'xmas_shop'
    return 'ordinary'


TAGS = ['ordinary', 'bank_hol', 'bh_sunday', 'paddys', 'xmas_eve', 'xmas', 'nye', 'jazz', 'match', 'storm', 'halloween', 'xmas_shop']


def demand_series():
    D = np.zeros(HOURS)
    rain = {START.date() + dt.timedelta(days=k): rng.uniform() < 0.45 for k in range(731)}
    for i, t in enumerate(T):
        d, h, wd = t.date(), t.hour, t.weekday()
        base = (WEEKDAY if wd < 4 else FRIDAY if wd == 4 else SATURDAY if wd == 5 else SUNDAY)[h]
        tag = event_tag(d, h)
        m = 1.0
        if in_term(d) and wd < 5 and 7 <= h <= 18:
            m *= 1.18
        if d.month in (6, 7, 8):
            m *= 1.06
        if rain[d]:
            m *= 1.12
        if tag in ('bank_hol',):
            base = SUNDAY[h] * 0.95
        if tag == 'bh_sunday' and h >= 20:
            m *= 1.55
        if tag == 'paddys':
            base = SUNDAY[h]
            if 10 <= h <= 14:
                m *= 2.6
            if h >= 18 or h <= 1:
                m *= 2.0
        if tag == 'xmas_eve' and 13 <= h <= 20:
            m *= 1.9
        if tag == 'xmas':
            m *= 0.25
        if d in HOL and HOL[d] == "St Stephen's Day" and 18 <= h <= 23:
            m *= 1.6
        if tag == 'nye':
            m *= 3.2 if (h >= 23 or h <= 2) else 1.6
        if tag == 'jazz' and (h >= 19 or h <= 2):
            m *= 2.1
        if tag == 'match':
            if 12 <= h <= 14:
                m *= 1.6
            if 17 <= h <= 19:
                m *= 2.7
        if tag == 'storm':
            m *= 1.7 if 7 <= h <= 20 else 1.2
        if tag == 'halloween' and h >= 18:
            m *= 1.7
        if tag == 'xmas_shop' and 11 <= h <= 18:
            m *= 1.4
        growth = 1.0 + 0.08 * (i / HOURS)
        D[i] = base * m * growth * rng.lognormal(0, 0.08)
    return D


def typical(D):
    """Median demand for the same weekday-hour on ordinary days of the same year (what the fleet plans for)."""
    ty = np.zeros(HOURS)
    keys = {}
    for i, t in enumerate(T):
        if event_tag(t.date(), t.hour) == 'ordinary':
            keys.setdefault((t.year, t.weekday(), t.hour), []).append(D[i])
    med = {k: np.median(v) for k, v in keys.items()}
    for i, t in enumerate(T):
        ty[i] = med[(t.year, t.weekday(), t.hour)]
    return ty


BOOSTS = np.array([0.0, 0.2, 0.4, 0.7, 1.0, 1.5])


def run_rl(D, S):
    """Tabular agent over (calendar tag, weekday-type, hour). Hindsight (full-information) updates are
    possible because the experience log records the uncensored demand of every hour."""
    Q = {}
    boost_hist, unserved_rl, unserved_base, idle = (np.zeros(HOURS) for _ in range(4))
    for i, t in enumerate(T):
        tag = event_tag(t.date(), t.hour)
        wt = 0 if t.weekday() < 4 else t.weekday() - 3
        key = (tag, wt if tag == 'ordinary' else 0, t.hour)
        q = Q.setdefault(key, np.zeros(len(BOOSTS)))
        n_seen = Q.setdefault(key + ('n',), np.zeros(1))
        a = int(np.argmax(q)) if n_seen[0] > 0 else 0
        sup = S[i] * (1 + BOOSTS[a])
        served = min(D[i], sup)
        unserved_rl[i] = D[i] - served
        idle[i] = max(0.0, sup - D[i]) if a > 0 else 0.0
        unserved_base[i] = max(0.0, D[i] - S[i])
        boost_hist[i] = BOOSTS[a]
        # hindsight update for every action from the logged demand
        r_all = -np.maximum(0, D[i] - S[i] * (1 + BOOSTS)) - 0.25 * np.minimum(np.maximum(0, S[i] * (1 + BOOSTS) - D[i]), S[i] * BOOSTS)
        lr = 1.0 / (n_seen[0] + 1) if tag != 'ordinary' else max(0.05, 1.0 / (n_seen[0] + 1))
        q += lr * (r_all - q)
        n_seen[0] += 1
    run_rl.Q = Q
    return boost_hist, unserved_rl, unserved_base, idle


# ------------------------------------------------------------------ numpy LSTM
def sigmoid(x):
    return 1 / (1 + np.exp(-x))


class LSTM:
    def __init__(self, nin, nh, nout, seed=0):
        r = np.random.default_rng(seed)
        s = 1 / np.sqrt(nin + nh)
        self.W = r.normal(0, s, (nin + nh, 4 * nh))
        self.b = np.zeros(4 * nh); self.b[nh:2 * nh] = 1.0
        self.V = r.normal(0, 1 / np.sqrt(nh), (nh, nout))
        self.c = np.zeros(nout)
        self.nh = nh
        self.params = [self.W, self.b, self.V, self.c]
        self.m = [np.zeros_like(p) for p in self.params]
        self.v = [np.zeros_like(p) for p in self.params]
        self.t = 0

    def forward(self, X):
        B, L, _ = X.shape
        nh = self.nh
        h = np.zeros((B, nh)); c = np.zeros((B, nh))
        cache = []
        for k in range(L):
            z = np.concatenate([X[:, k], h], 1)
            g = z @ self.W + self.b
            i_, f_, o_, u_ = sigmoid(g[:, :nh]), sigmoid(g[:, nh:2 * nh]), sigmoid(g[:, 2 * nh:3 * nh]), np.tanh(g[:, 3 * nh:])
            c_new = f_ * c + i_ * u_
            h_new = o_ * np.tanh(c_new)
            cache.append((z, i_, f_, o_, u_, c, c_new))
            h, c = h_new, c_new
        y = h @ self.V + self.c
        return y, (cache, h)

    def step(self, X, Y, wts, lr=3e-3):
        y, (cache, h) = self.forward(X)
        err = (y - Y) * wts
        loss = float((err * (y - Y)).mean())
        dy = 2 * err / err.size
        gV = h.T @ dy; gc = dy.sum(0)
        dh = dy @ self.V.T
        dc = np.zeros_like(dh)
        gW = np.zeros_like(self.W); gb = np.zeros_like(self.b)
        nh = self.nh
        for (z, i_, f_, o_, u_, c_prev, c_new) in reversed(cache):
            tc = np.tanh(c_new)
            do = dh * tc
            dc = dc + dh * o_ * (1 - tc ** 2)
            di = dc * u_; df = dc * c_prev; du = dc * i_
            dg = np.concatenate([di * i_ * (1 - i_), df * f_ * (1 - f_), do * o_ * (1 - o_), du * (1 - u_ ** 2)], 1)
            gW += z.T @ dg; gb += dg.sum(0)
            dz = dg @ self.W.T
            dh = dz[:, -nh:]
            dc = dc * f_
        grads = [gW, gb, gV, gc]
        self.t += 1
        for k, (p, g) in enumerate(zip(self.params, grads)):
            g = np.clip(g, -1, 1)
            self.m[k] = 0.9 * self.m[k] + 0.1 * g
            self.v[k] = 0.999 * self.v[k] + 0.001 * g * g
            mh = self.m[k] / (1 - 0.9 ** self.t); vh = self.v[k] / (1 - 0.999 ** self.t)
            p -= lr * mh / (np.sqrt(vh) + 1e-8)
        return loss


L_IN, HZ = 48, 6


def features(obs, extra, cal):
    return np.concatenate([obs[:, None], extra, cal], 1)


def calendar_feats(shift=0):
    F = []
    for i in range(HOURS):
        t = T[min(HOURS - 1, i + shift)]
        tag = event_tag(t.date(), t.hour)
        F.append([np.sin(2 * np.pi * t.hour / 24), np.cos(2 * np.pi * t.hour / 24),
                  np.sin(2 * np.pi * t.weekday() / 7), np.cos(2 * np.pi * t.weekday() / 7)] +
                 [1.0 if tag == g else 0.0 for g in TAGS[1:]])
    return np.array(F)


def make_windows(F, target, idxs):
    X = np.stack([F[i - L_IN + 1:i + 1] for i in idxs])
    Y = np.stack([target[i + 1:i + 1 + HZ] for i in idxs])
    return X, Y


def train_lstm(F, target, surge_w, train_idx, epochs=14, seed=0):
    model = LSTM(F.shape[1], 40, HZ, seed)
    r = np.random.default_rng(seed)
    for ep in range(epochs):
        r.shuffle(train_idx)
        tot = 0
        for b in range(0, len(train_idx), 128):
            ids = train_idx[b:b + 128]
            X, Y = make_windows(F, target, ids)
            W_ = np.stack([surge_w[i + 1:i + 1 + HZ] for i in ids])
            tot += model.step(X, Y, W_, 3e-3 if ep < 9 else 1e-3)
        print(f'  epoch {ep} loss {tot / (len(train_idx) / 128):.4f}', flush=True)
    return model


def predict(model, F, idxs):
    out = []
    for b in range(0, len(idxs), 512):
        X = np.stack([F[i - L_IN + 1:i + 1] for i in idxs[b:b + 512]])
        out.append(model.forward(X)[0])
    return np.concatenate(out)


if __name__ == '__main__':
    D = demand_series()
    TY = typical(D)
    S = TY * 1.03  # fleet planned for an ordinary day
    boost, un_rl, un_base, idle = run_rl(D, S)
    served = np.minimum(D, S * (1 + boost))

    SCALE = 400.0
    cal_now = calendar_feats(0)
    cal_ahead = calendar_feats(3)  # calendar is known in advance
    cal = np.concatenate([cal_now, cal_ahead], 1)
    zeros = np.zeros((HOURS, 2))
    rl_extra = np.stack([un_rl / SCALE, boost], 1)
    F_A = features(served / SCALE, zeros, cal)          # completed trips only
    F_B = features(served / SCALE, rl_extra, cal)       # + RL experience log
    surge = D > 1.35 * TY
    surge_w = 1 + 3 * surge.astype(float)

    split = int(HOURS * 0.75)  # train: 2025 + Jan-Jun 2026, test: Jul-Dec 2026
    train_idx = np.arange(L_IN, split - HZ)
    test_idx = np.arange(split, HOURS - HZ)
    print('model A (trips only)')
    mA = train_lstm(F_A, served / SCALE, surge_w, train_idx.copy(), seed=1)
    print('model B (with RL experience)')
    mB = train_lstm(F_B, D / SCALE, surge_w, train_idx.copy(), seed=1)
    pA = predict(mA, F_A, test_idx) * SCALE
    pB = predict(mB, F_B, test_idx) * SCALE

    np.savez('city_preds.npz', pA=pA, pB=pB, test_idx=test_idx, D=D, TY=TY, served=served, un_rl=un_rl, boost=boost, S=S)
    res = {}
    for name, P in (('A', pA), ('B', pB)):
        for hz in (1, 3, 6):
            tgt = np.array([D[i + hz] for i in test_idx])
            ty = np.array([TY[i + hz] for i in test_idx])
            sg = tgt > 1.35 * ty
            pred_s = P[:, hz - 1] > 1.35 * ty
            recall = float((sg & pred_s).sum() / max(1, sg.sum()))
            prec = float((sg & pred_s).sum() / max(1, pred_s.sum()))
            mae_s = float(np.abs(P[sg, hz - 1] - tgt[sg]).mean())
            peak_err = float(((P[sg, hz - 1] - tgt[sg]) / tgt[sg]).mean())
            res[f'{name}_h{hz}'] = dict(recall=recall, precision=prec, mae_surge=mae_s, bias_surge=peak_err)
            print(name, hz, res[f'{name}_h{hz}'])

    # ------------------------------------------------ data for the video
    days = HOURS // 24
    day_un_rl = un_rl.reshape(days, 24).sum(1)
    day_un_base = un_base.reshape(days, 24).sum(1)
    day_D = D.reshape(days, 24).sum(1)
    day_TY = TY.reshape(days, 24).sum(1)
    peak_ratio = (D / TY).reshape(days, 24).max(1)
    labels = {}
    for k in range(days):
        d = (START + dt.timedelta(days=k)).date()
        lab = None
        if d in HOL:
            lab = HOL[d]
        elif d in JAZZ and d.weekday() == 5:
            lab = 'Jazz Festival Saturday'
        elif d in MATCH:
            lab = 'Match day · Páirc Uí Chaoimh'
        elif d in STORM:
            lab = 'Storm warning'
        elif d in EVE:
            lab = 'Christmas Eve'
        elif d in NYE:
            lab = "New Year's Eve"
        elif d in HALLOWEEN:
            lab = 'Halloween'
        elif d == dt.date(d.year, 9, 15):
            lab = 'UCC term begins'
        if lab:
            labels[k] = lab

    def daily(k):
        return dict(date=str((START + dt.timedelta(days=k)).date()), demand=D[k * 24:(k + 1) * 24].round(1).tolist(),
                    typical=TY[k * 24:(k + 1) * 24].round(1).tolist(), supply=S[k * 24:(k + 1) * 24].round(1).tolist(),
                    boost=boost[k * 24:(k + 1) * 24].tolist(), un_rl=un_rl[k * 24:(k + 1) * 24].round(1).tolist(),
                    un_base=un_base[k * 24:(k + 1) * 24].round(1).tolist())

    def k_of(d):
        return (d - START.date()).days

    yoy = {}
    for name, d1, d2 in (("St Patrick's Day", dt.date(2025, 3, 17), dt.date(2026, 3, 17)),
                         ('Christmas Eve', dt.date(2025, 12, 24), dt.date(2026, 12, 24)),
                         ('Jazz Festival Saturday', dt.date(2025, 10, 25), dt.date(2026, 10, 24)),
                         ("New Year's Eve", dt.date(2025, 12, 31), dt.date(2026, 12, 31))):
        yoy[name] = dict(y1=float(day_un_rl[k_of(d1)]), y2=float(day_un_rl[k_of(d2)]),
                         base1=float(day_un_base[k_of(d1)]), base2=float(day_un_base[k_of(d2)]))
    ev_mask = np.array([event_tag((START + dt.timedelta(days=k)).date(), 18) != 'ordinary' for k in range(days)])
    y1 = np.arange(days) < 365
    summary = dict(
        unserved_events_y1=float(day_un_rl[ev_mask & y1].sum()), unserved_events_y2=float(day_un_rl[ev_mask & ~y1].sum()),
        unserved_events_base_y1=float(day_un_base[ev_mask & y1].sum()), unserved_events_base_y2=float(day_un_base[ev_mask & ~y1].sum()),
        unserved_ord_y1=float(day_un_rl[~ev_mask & y1].sum()), unserved_ord_y2=float(day_un_rl[~ev_mask & ~y1].sum()),
        total_requests=float(D.sum()))

    # hero forecast: Jazz Festival Saturday 2026 evening, forecasts issued 3 hours ahead
    hero_day = k_of(dt.date(2026, 10, 24))
    h0 = hero_day * 24
    hero = dict(date='2026-10-24', hours=list(range(12, 30)), actual=[float(D[h0 + h]) for h in range(12, 30)],
                typical=[float(TY[h0 + h]) for h in range(12, 30)], trips_seen=[float(served[h0 + h]) for h in range(12, 30)])
    pos = {int(i): n for n, i in enumerate(test_idx)}
    for hz in (1, 3, 6):
        hero[f'B_h{hz}'] = [float(pB[pos[h0 + h - hz], hz - 1]) for h in range(12, 30)]
        hero[f'A_h{hz}'] = [float(pA[pos[h0 + h - hz], hz - 1]) for h in range(12, 30)]
    # ordinary Tuesday for the "heartbeat" scene
    ordinary = daily(k_of(dt.date(2026, 3, 10)))

    out = dict(day_un_rl=day_un_rl.round(1).tolist(), day_un_base=day_un_base.round(1).tolist(), day_D=day_D.round(0).tolist(),
               day_TY=day_TY.round(0).tolist(), peak_ratio=peak_ratio.round(3).tolist(), labels=labels, yoy=yoy,
               summary=summary, lstm=res, hero=hero, ordinary=ordinary,
               paddys1=daily(k_of(dt.date(2025, 3, 17))), paddys2=daily(k_of(dt.date(2026, 3, 17))))
    json.dump(out, open('city_results.json', 'w'))
    print(json.dumps(summary, indent=1))
    print(json.dumps(yoy, indent=1))
