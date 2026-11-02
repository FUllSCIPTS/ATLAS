"""Forecasts on the validation partition (used only for tuning the policies)."""
import os, sys, numpy as np, torch
sys.path.insert(0, os.path.dirname(__file__))
from atlas_sim.traffic import ecommerce_trace, calendar_features, telemetry
from atlas_sim import forecast as fc
torch.set_num_threads(2)
OUT = os.path.join(os.path.dirname(__file__), "results"); H = [5, 15, 60]
r, mask, events = ecommerce_trace(365, seed=2026)
X8 = telemetry(r, np.random.default_rng(7)); cal = calendar_features(len(r))
F_raw = fc.build_features(X8, cal); n = len(r); i_tr, i_va = int(.70 * n), int(.85 * n)
sc = fc.Scaler().fit(F_raw[:i_tr]); F = sc(F_raw).astype(np.float32)
ylog = np.log1p(r).astype(np.float32); tr = fc.valid_idx(0, i_tr, H)
va = fc.valid_idx(i_tr, i_va, H)
out = {"idx": va}
for name, bi, f in (("lstm", False, "lstm_seed0.pt"), ("bilstm", True, "bilstm_seed0.pt")):
    m = fc.LSTMForecaster(F.shape[1], 3, bidirectional=bi); m.load_state_dict(torch.load(os.path.join(OUT, f)))
    m.ymu, m.ysd = float(ylog[tr].mean()), float(ylog[tr].std())
    out[name] = fc.predict(m, F, va, H)[:, 0]
ar = fc.fit_ar(r, cal, tr, H); out["ar"] = fc.predict_ar(ar, r, cal, va, H)[:, 0]
out["sn"] = fc.seasonal_naive(r, va, H)[:, 0]
np.savez_compressed(os.path.join(OUT, "val_preds.npz"), **out); print("ok", len(va))
