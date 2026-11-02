"""Experiment F2: out-of-distribution and cross-node evaluation of the trained
node-A LSTM (weights frozen).  Reports MAPE and WAPE (sum|e|/sum|y|, robust to
near-zero night traffic).  Output: results/ood.json
"""
import json, os, sys
import numpy as np, torch
sys.path.insert(0, os.path.dirname(__file__))
from atlas_sim.traffic import ecommerce_trace, calendar_features, telemetry
from atlas_sim import forecast as fc

torch.set_num_threads(2)
OUT = os.path.join(os.path.dirname(__file__), "results"); H = [5, 15, 60]
r, mask, events = ecommerce_trace(365, seed=2026)
X8 = telemetry(r, np.random.default_rng(7)); cal = calendar_features(len(r))
F_raw = fc.build_features(X8, cal); n = len(r); i_tr = int(.70 * n)
sc = fc.Scaler().fit(F_raw[:i_tr]); ylog = np.log1p(r).astype(np.float32)
tr = fc.valid_idx(0, i_tr, H)
m = fc.LSTMForecaster(F_raw.shape[1], 3); m.load_state_dict(torch.load(os.path.join(OUT, "lstm_seed0.pt")))
m.ymu, m.ysd = float(ylog[tr].mean()), float(ylog[tr].std())
ar = fc.fit_ar(r, cal, tr, H)


def wape(y, p):
    return float(100 * np.abs(p - y).sum() / np.abs(y).sum())


def select(y, preds, win=60, h=5):
    """Online forecaster selection: at time t use the forecaster with the lowest
    absolute error over the last `win` minutes whose targets are already known
    (errors up to t-h), i.e. no look-ahead."""
    E = np.stack([np.abs(p - y) for p in preds])               # error of forecast made at t for t+h
    C = np.cumsum(np.concatenate([np.zeros((len(preds), 1)), E], 1), 1)
    out = preds[0].copy()
    for t in range(len(y)):
        hi = t - h + 1; lo = max(0, hi - win)
        if hi > lo:
            k = int(np.argmin(C[:, hi] - C[:, lo])); out[t] = preds[k][t]
    return out


def eval_node(rr, phase_h=0.0, per_node=True, calib_days=7, seed=11):
    X = telemetry(rr, np.random.default_rng(seed)); cl = calendar_features(len(rr), phase_h)
    Fr = fc.build_features(X, cl); yl = np.log1p(rr).astype(np.float32); c = calib_days * 1440
    saved = (m.ymu, m.ysd)
    if per_node:
        FF = fc.Scaler().fit(Fr[:c])(Fr).astype(np.float32); m.ymu, m.ysd = float(yl[:c].mean()), float(yl[:c].std())
    else:
        FF = sc(Fr).astype(np.float32)
    idx = fc.valid_idx(c, len(rr), H); PP = fc.predict(m, FF, idx, H); m.ymu, m.ysd = saved
    y = rr[idx + 5]; pa = fc.predict_ar(ar, rr, cl, idx, H)[:, 0]; pp = rr[idx]
    ps = select(y, [PP[:, 0], pa, pp])
    return dict(LSTM=dict(MAPE=fc.metrics(y, PP[:, 0])["MAPE"], WAPE=wape(y, PP[:, 0])),
                Selector=dict(MAPE=fc.metrics(y, ps)["MAPE"], WAPE=wape(y, ps)),
                Ridge=dict(MAPE=fc.metrics(y, pa)["MAPE"], WAPE=wape(y, pa)),
                Persistence=dict(MAPE=fc.metrics(y, pp)["MAPE"], WAPE=wape(y, pp)))


specs = {
    "Drift: baseline +60%, larger daily cycle": dict(days=37, seed=31, base=900, a_d=500, noise=90, n_events=6, trend=0.6),
    "Irregular: heavy-tailed micro-bursts": dict(days=37, seed=32, bursts=900, n_events=6),
    "Unseen surge shape: steeper, 8-12k RPS": dict(days=37, seed=33, n_events=8, amp=(8000, 12000), peak_frac=0.1, dur=(10, 40)),
    "Node B: UTC+5, 0.5x traffic": dict(days=37, seed=34, phase_h=5, scale=0.5, n_events=6),
    "Node C: UTC-8, 2x traffic, noisier": dict(days=37, seed=35, phase_h=-8, scale=2.0, noise=90, n_events=6),
}
R = {}
# in-distribution reference (test partition of node A)
Z = np.load(os.path.join(OUT, "forecast_preds.npz")); te = Z["te"]; y = r[te + 5]
ps = select(y, [Z["lstm"][:, 0], Z["ar"][:, 0], Z["pers"][:, 0]])
R["Node A, test period (reference)"] = dict(LSTM=dict(MAPE=fc.metrics(y, Z["lstm"][:, 0])["MAPE"], WAPE=wape(y, Z["lstm"][:, 0])),
                                            Selector=dict(MAPE=fc.metrics(y, ps)["MAPE"], WAPE=wape(y, ps)),
                                            Ridge=dict(MAPE=fc.metrics(y, Z["ar"][:, 0])["MAPE"], WAPE=wape(y, Z["ar"][:, 0])),
                                            Persistence=dict(MAPE=fc.metrics(y, Z["pers"][:, 0])["MAPE"], WAPE=wape(y, Z["pers"][:, 0])))
for name, sp in specs.items():
    rr, _, _ = ecommerce_trace(**sp); ph = sp.get("phase_h", 0.0)
    R[name] = eval_node(rr, ph, True)
    R[name]["LSTM_global_scaler"] = eval_node(rr, ph, False)["LSTM"]
    print(name, R[name], flush=True)
json.dump(R, open(os.path.join(OUT, "ood.json"), "w"), indent=1)
