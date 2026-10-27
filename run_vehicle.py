"""Experiment V: connected-vehicle fleet case study (14 held-out test days).

Uses the LSTM trained on 42 days of fleet traffic (run_forecast.py) whose
8-minute-ahead out-of-sample predictions drive ATLAS.  Simulation step 1 s;
recovery events are timestamped in continuous time.  Output results/vehicle.json
"""
import json, os, sys
from dataclasses import replace
from multiprocessing import Pool
import numpy as np
from scipy import stats
sys.path.insert(0, os.path.dirname(__file__))
from atlas_sim.cluster import Sim, Params, summarise

OUT = os.path.join(os.path.dirname(__file__), "results")
Z = np.load(os.path.join(OUT, "vehicle_preds.npz"))
v, tev, P = Z["v"], Z["tev"], Z["lstm"]
SERV = ["Ingest", "Route optimisation", "Driver safety", "Maintenance", "Compliance", "Geofencing"]
PV = Params(visit=np.array([1.0, 0.25, 0.6, 0.2, 0.1, 0.5]),
            demand=np.array([0.15, 2.4, 0.5, 0.6, 0.4, 0.2]),
            mono_cores=32.0, max_rep=80, base_ms=5.0, sla_ms=100.0, ref_lam=10000.0)
DAY0 = 49   # first test day


def run(args):
    pol, d = args
    lo = (DAY0 + d) * 1440
    m = v[lo:lo + 1440]
    # forecast made at minute t for t+8, aligned to decision time
    k0 = int(np.searchsorted(tev, lo))
    f = np.full(1440, np.nan); idx = tev[k0:k0 + 1440] - lo
    ok = (idx >= 0) & (idx < 1440); f[idx[ok]] = P[k0:k0 + 1440][ok]
    f = np.where(np.isnan(f), m, f)
    rng = np.random.default_rng(d)
    lam = rng.poisson(np.interp(np.arange(86400) / 60.0, np.arange(1440), m)).astype(float)
    peak = 420 + int(np.argmax(m[420:540]))
    fail = dict(t=float(peak * 60 + rng.uniform(-180, 180)), module=2, kind="exit")
    o = Sim(pol, lam, f, p=PV, seed=d, opts=dict(anomaly=False), failure=fail).run()
    ref = Sim("monolith", lam, f, p=PV, seed=d).run()
    S = summarise(o, ref_cost=float(np.mean(ref["cost"])), warm=60)
    # per-period latency (peak 07-09, off-peak 22-06) and minute-level SLA compliance
    sec = np.arange(86400); mins = sec // 60
    pk = (mins >= 420) & (mins < 540); op = (mins >= 1320) | (mins < 360)
    good = o["lam"] - o["fail"]
    S["peak_mean_ms"] = float((good[pk] * o["lat"][pk]).sum() / good[pk].sum())
    S["offpeak_mean_ms"] = float((good[op] * o["lat"][op]).sum() / good[op].sum())
    S["req_sla_pct"] = 100 - S["sla_viol_pct"]
    S["downtime_min"] = float(o["fail"].sum() / max(o["lam"].mean(), 1) / 60)
    S["mode_hours"] = [float((o["mode"] == k).sum() / 3600) for k in range(3)]
    if d == 0:
        S["trace"] = dict(lam=o["lam"][::60].tolist(), lat=o["lat"][::60].tolist(),
                          mode=o["mode"][::60].tolist(), cost=o["cost"][::60].tolist(), fc=f.tolist(),
                          ref_cost=float(np.mean(ref["cost"])))
    return S


def blk(x):
    x = np.asarray(x, float); n = len(x); m = x.mean(); s = x.std(ddof=1)
    h = stats.t.ppf(.975, n - 1) * s / np.sqrt(n); return dict(mean=float(m), sd=float(s), ci95=[float(m - h), float(m + h)])


if __name__ == "__main__":
    R = {}
    days = list(range(14))
    for pol in ("monolith", "microservices", "atlas"):
        with Pool(2) as pool:
            S = pool.map(run, [(pol, d) for d in days])
        keys = ["peak_mean_ms", "offpeak_mean_ms", "p99_ms", "req_sla_pct", "failed_pct", "mttr_s",
                "rel_cost", "transitions", "downtime_min"]
        R[pol] = {k: blk([s[k] for s in S]) for k in keys}
        R[pol]["mode_hours"] = np.mean([s["mode_hours"] for s in S], 0).tolist()
        R[pol]["trace"] = S[0].get("trace")
        print(pol, {k: round(R[pol][k]["mean"], 2) for k in keys}, R[pol]["mode_hours"], flush=True)
    json.dump(R, open(os.path.join(OUT, "vehicle.json"), "w"), indent=1)
