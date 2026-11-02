"""Experiment F: train and evaluate the LSTM traffic predictor.

Outputs  results/forecast.json  and  results/forecast_preds.npz
Run:     python run_forecast.py   (about 30-40 min on 2 CPU cores)
"""
import json, os, sys, time
import numpy as np, torch
sys.path.insert(0, os.path.dirname(__file__))
from atlas_sim.traffic import ecommerce_trace, fleet_trace, calendar_features, telemetry
from atlas_sim import forecast as fc

torch.set_num_threads(2)
OUT = os.path.join(os.path.dirname(__file__), "results"); os.makedirs(OUT, exist_ok=True)
H = [5, 15, 60]
R = {}
log = lambda s: (print(s), sys.stdout.flush())

# ------------------------------------------------------------ data (node A)
r, mask, events = ecommerce_trace(365, seed=2026)
rng = np.random.default_rng(7)
X8 = telemetry(r, rng); cal = calendar_features(len(r))
F_raw = fc.build_features(X8, cal)
n = len(r); i_tr, i_va = int(.70 * n), int(.85 * n)
sc = fc.Scaler().fit(F_raw[:i_tr]); F = sc(F_raw).astype(np.float32)
ylog = np.log1p(r).astype(np.float32)
tr = fc.valid_idx(0, i_tr, H); va = fc.valid_idx(i_tr, i_va, H); te = fc.valid_idx(i_va, n, H)
R["data"] = dict(n=n, train=int(i_tr), val=int(i_va - i_tr), test=int(n - i_va),
                 events=len(events), test_events=int(sum(1 for s, _, _ in events if s >= i_va)))
log(f"data {R['data']}")

# ------------------------------------------------------------ LSTM, 3 seeds
models, seed_res = [], []
for seed in (0, 1, 2):
    log(f"LSTM seed {seed}")
    t0 = time.time()
    m = fc.train(F, ylog, tr, va, H, seed=seed, per_epoch=8192, log=log)
    P = fc.predict(m, F, te, H)
    res = {f"h{h}": fc.metrics(r[te + h], P[:, k]) for k, h in enumerate(H)}
    res["epochs"] = m.epochs_run; res["train_s"] = time.time() - t0
    seed_res.append(res); models.append((m, P))
    torch.save(m.state_dict(), os.path.join(OUT, f"lstm_seed{seed}.pt"))
R["lstm_seeds"] = seed_res
best = int(np.argmin([s["h5"]["MAPE"] for s in seed_res]))
m, P = models[0]                                   # seed 0 is the reported model
R["lstm_reported_seed"] = 0

# ------------------------------------------------------------ baselines
P_pers = fc.persistence(r, te, H); P_sn = fc.seasonal_naive(r, te, H)
ar = fc.fit_ar(r, cal, tr, H); P_ar = fc.predict_ar(ar, r, cal, te, H)
log("Bi-LSTM baseline forecaster")
mb = fc.train(F, ylog, tr, va, H, seed=0, bidirectional=True, per_epoch=8192, log=log)
P_bi = fc.predict(mb, F, te, H)
torch.save(mb.state_dict(), os.path.join(OUT, "bilstm_seed0.pt"))
cmp_ = {}
surge = mask[te + 5] == 1
for name, PP in [("LSTM", P), ("Bi-LSTM", P_bi), ("Ridge-AR", P_ar),
                 ("Seasonal naive", P_sn), ("Persistence", P_pers)]:
    d = {f"h{h}": fc.metrics(r[te + h], PP[:, k]) for k, h in enumerate(H)}
    d["h5_ci"] = fc.block_bootstrap_ci(r[te + 5], PP[:, 0])
    d["h5_surge"] = fc.metrics(r[te + 5][surge], PP[surge, 0])
    d["h5_normal"] = fc.metrics(r[te + 5][~surge], PP[~surge, 0])
    d["detect_1000"] = fc.surge_detection(r, PP[:, 0], te, 1000)
    d["detect_5000"] = fc.surge_detection(r, PP[:, 0], te, 5000)
    cmp_[name] = d
    log(f"{name}: {d['h5']} surge {d['h5_surge']['MAPE']:.1f}")
R["test_comparison"] = cmp_
np.savez_compressed(os.path.join(OUT, "forecast_preds.npz"), te=te, r=r, mask=mask,
                    lstm=P, bilstm=P_bi, ar=P_ar, sn=P_sn, pers=P_pers)


# ------------------------------------------------------------ OOD / cross-node
def eval_node(rr, phase_h=0.0, per_node=True, calib_days=7, seed=11):
    g = np.random.default_rng(seed)
    X = telemetry(rr, g); cl = calendar_features(len(rr), phase_h)
    Fr = fc.build_features(X, cl)
    yl = np.log1p(rr).astype(np.float32)
    c = calib_days * 1440
    saved = (m.ymu, m.ysd)
    if per_node:
        # per-node standardisation from the first `calib_days` only; the
        # trained weights are NOT updated (zero-shot transfer).
        FF = fc.Scaler().fit(Fr[:c])(Fr).astype(np.float32)
        m.ymu, m.ysd = float(yl[:c].mean()), float(yl[:c].std())
    else:
        FF = sc(Fr).astype(np.float32)
    idx = fc.valid_idx(c, len(rr), H)
    PP = fc.predict(m, FF, idx, H)
    m.ymu, m.ysd = saved
    out = {f"h{h}": fc.metrics(rr[idx + h], PP[:, k]) for k, h in enumerate(H)}
    pa = fc.predict_ar(ar, rr, cl, idx, H)
    out["ridge_h5"] = fc.metrics(rr[idx + 5], pa[:, 0])
    out["persist_h5"] = fc.metrics(rr[idx + 5], rr[idx])
    return out


ood = {}
specs = {
    "ID test (reference)": None,
    "Drift: baseline +60%, larger daily cycle": dict(days=37, seed=31, base=900, a_d=500, noise=90, n_events=6, trend=0.6),
    "Irregular: heavy-tailed micro-bursts": dict(days=37, seed=32, bursts=900, n_events=6),
    "Unseen surge shape: steeper, 8-12k RPS": dict(days=37, seed=33, n_events=8, amp=(8000, 12000), peak_frac=0.1, dur=(10, 40)),
    "Node B: UTC+5, 0.5x scale": dict(days=37, seed=34, phase_h=5, scale=0.5, n_events=6),
    "Node C: UTC-8, 2x scale, noisier": dict(days=37, seed=35, phase_h=-8, scale=2.0, noise=120, a_d=450, n_events=6),
}
for name, sp in specs.items():
    if sp is None:
        ood[name] = dict(h5=cmp_["LSTM"]["h5"], h15=cmp_["LSTM"]["h15"], h60=cmp_["LSTM"]["h60"],
                         ridge_h5=cmp_["Ridge-AR"]["h5"], persist_h5=cmp_["Persistence"]["h5"]); continue
    rr, _, _ = ecommerce_trace(**sp)
    ph = sp.get("phase_h", 0.0)
    ood[name] = eval_node(rr, ph, per_node=True)
    if "Node" in name or "Drift" in name:
        ood[name]["zero_shot_global_scaler_h5"] = eval_node(rr, ph, per_node=False)["h5"]
    log(f"{name}: {ood[name]['h5']}")
R["ood"] = ood

# ------------------------------------------------------------ vehicle fleet
log("Vehicle fleet LSTM")
v, meta = fleet_trace(63, seed=5)
vc = calendar_features(len(v))
Fv_raw = np.concatenate([np.log1p(v)[:, None], vc], 1).astype(np.float32)
i1, i2 = 42 * 1440, 49 * 1440
scv = fc.Scaler().fit(Fv_raw[:i1]); Fv = scv(Fv_raw).astype(np.float32)
vlog = np.log1p(v).astype(np.float32)
HV = [8]
trv = fc.valid_idx(0, i1, HV); vav = fc.valid_idx(i1, i2, HV); tev = fc.valid_idx(i2, len(v), HV)
mv = fc.train(Fv, vlog, trv, vav, HV, seed=0, per_epoch=8192, log=log)
torch.save(mv.state_dict(), os.path.join(OUT, "lstm_vehicle.pt"))
Pv = fc.predict(mv, Fv, tev, HV)[:, 0]
yv = v[tev + 8]
minute = (tev + 8) % 1440
periods = {"Overnight (22:00-06:00)": (minute >= 1320) | (minute < 360),
           "Pre-surge ramp (06:00-07:00)": (minute >= 360) & (minute < 420),
           "Morning surge (07:00-09:00)": (minute >= 420) & (minute < 540),
           "Daytime plateau (09:00-18:00)": (minute >= 540) & (minute < 1080),
           "Evening drop-off (18:00-22:00)": (minute >= 1080) & (minute < 1320)}
arv = []
from sklearn.linear_model import Ridge
def vfeat(idx):
    lv = np.log1p(v); L = lv[idx[:, None] - np.arange(60)[None, :]]
    return np.concatenate([L, lv[np.maximum(idx + 8 - 1440, 0)][:, None], vc[idx]], 1)
trv2 = trv[trv >= 1440]
rv = Ridge(1.0).fit(vfeat(trv2), np.log1p(v[trv2 + 8]))
Pv_ar = np.expm1(rv.predict(vfeat(tev)))
Pv_sn = v[tev + 8 - 1440]; Pv_p = v[tev]
veh = {"test_days": 14, "periods": {}}
for nm, msk in periods.items():
    veh["periods"][nm] = dict(rate=float(yv[msk].mean()),
                              LSTM=fc.metrics(yv[msk], Pv[msk])["MAPE"],
                              Ridge=fc.metrics(yv[msk], Pv_ar[msk])["MAPE"],
                              SeasonalNaive=fc.metrics(yv[msk], Pv_sn[msk])["MAPE"],
                              Persistence=fc.metrics(yv[msk], Pv_p[msk])["MAPE"])
veh["overall"] = dict(rate=float(yv.mean()), LSTM=fc.metrics(yv, Pv), Ridge=fc.metrics(yv, Pv_ar),
                      SeasonalNaive=fc.metrics(yv, Pv_sn), Persistence=fc.metrics(yv, Pv_p),
                      LSTM_ci=fc.block_bootstrap_ci(yv, Pv))
veh["epochs"] = mv.epochs_run
veh["test_day_meta"] = meta[49:]
R["vehicle"] = veh
np.savez_compressed(os.path.join(OUT, "vehicle_preds.npz"), tev=tev, v=v, lstm=Pv, ar=Pv_ar)
log(json.dumps(veh["overall"], indent=1))
json.dump(R, open(os.path.join(OUT, "forecast.json"), "w"), indent=1)
log("done")
