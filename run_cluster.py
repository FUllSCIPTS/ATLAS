"""Experiments C: architecture comparison, forecaster value, ablation and
sensitivity analysis on the cluster simulator.

Requires results/forecast_preds.npz and the saved models from run_forecast.py
and results/iforest.pkl from run_anomaly.py.
Output: results/cluster.json
"""
import json, os, sys, pickle, time
from dataclasses import replace
from multiprocessing import Pool
import numpy as np
from scipy import stats
sys.path.insert(0, os.path.dirname(__file__))
from atlas_sim.cluster import Sim, Params, summarise, FastIForest

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "results")
Z = np.load(os.path.join(OUT, "forecast_preds.npz"))
r, mask, te = Z["r"], Z["mask"], Z["te"]
FC = {"lstm": Z["lstm"][:, 0], "bilstm": Z["bilstm"][:, 0], "ar": Z["ar"][:, 0], "sn": Z["sn"][:, 0]}
ISO = pickle.load(open(os.path.join(OUT, "iforest.pkl"), "rb")); ISO["fast"] = FastIForest(ISO["model"])
VAL = None
if os.path.exists(os.path.join(OUT, "val_preds.npz")):
    VAL = {k: v for k, v in np.load(os.path.join(OUT, "val_preds.npz")).items()}


def events_in(idx_lo, idx_hi):
    ev, i = [], idx_lo
    while i < idx_hi:
        if mask[i] and not mask[i - 1]:
            j = i
            while mask[j]:
                j += 1
            if i - 90 >= idx_lo and i + 140 < idx_hi:
                ev.append((i, j))
            i = j
        i += 1
    return ev


TEST_EV = events_in(int(te[0]) + 60, int(te[-1]))


def window(seed, split="test", startup=None):
    """180-min window around a flash sale + per-second Poisson arrivals."""
    rng = np.random.default_rng(seed)
    if split == "test":
        evs, idx0, P = TEST_EV, int(te[0]), FC
    else:
        evs, idx0 = VAL_EV, int(VAL["idx"][0])
        P = {"lstm": VAL["lstm"], "bilstm": VAL["bilstm"], "ar": VAL["ar"], "sn": VAL["sn"]}
    s, e = evs[seed % len(evs)]
    w0 = s - int(rng.uniform(40, 80))
    m = r[w0:w0 + 180]
    lam = rng.poisson(np.interp(np.arange(180 * 60) / 60.0, np.arange(180), m)).astype(float)
    fc = {k: v[w0 - idx0: w0 - idx0 + 180] for k, v in P.items()}
    fc["oracle"] = r[w0 + 5:w0 + 185]
    fc["none"] = m
    peak = s + int(np.argmax(r[s:e])) - w0
    failure = dict(t=float(peak * 60 + rng.uniform(-180, 180)), module=4, kind="exit")
    anomaly = dict(t0=int(rng.uniform(15, 25) * 60), dur=480, module=3, factor=6.0)
    return lam, fc, failure, anomaly


POLICY_FC = {"monolith": "none", "microservices": "none", "hansel": "bilstm",
             "phybrid": "bilstm", "xscale": "bilstm", "atlas": "lstm"}


def run_one(args):
    policy, seed, pd, opts, fc_name, split, noise = args
    lam, fc, failure, anomaly = window(seed, split)
    pd = dict(pd); sc = pd.pop("_scale", 1.0); nf = pd.pop("_nfail", 1)
    if sc != 1.0:
        lam = np.random.default_rng(seed).poisson(lam * sc).astype(float)
        fc = {k: v * sc for k, v in fc.items()}
    if nf == 0:
        failure = None
    elif nf > 1:
        failure = [failure] + [dict(failure, t=failure["t"] + dt) for dt in (-1800.0, 1500.0)][:nf - 1]
        failure = [f for f in failure if 300 < f["t"] < len(lam) - 60]
    p = replace(Params(), **pd)
    f = fc[fc_name or POLICY_FC[policy]]
    if noise:   # synthetic forecast with controlled error around the oracle
        g = np.random.default_rng(seed + 999)
        f = fc["oracle"] * np.maximum(0.05, 1 + g.normal(0, noise * np.sqrt(np.pi / 2), len(f)))
    o = dict(opts or {})
    if fc_name == "none" and policy == "atlas":
        o["forecast"] = False
    t0 = time.time()
    out = Sim(policy, lam, f, p=p, seed=seed, opts=o, failure=failure, anomaly=anomaly, iforest=ISO).run()
    ref = Sim("monolith", lam, f, p=p, seed=seed, failure=None, anomaly=None).run()
    S = summarise(out, ref_cost=float(np.mean(ref["cost"][300:])))
    S["wall_s"] = time.time() - t0
    S["mode_ts"] = out["mode"][::60].tolist() if seed in (1, 2) else None
    if seed in (1,) and policy in ("atlas", "microservices", "monolith"):
        S["trace"] = dict(lam=out["lam"][::10].tolist(), lat=out["lat"][::10].tolist(),
                          mode=out["mode"][::10].tolist(), fc=f.tolist())
    S["recoveries"] = out["recoveries"]
    return S


def pmap(jobs, procs=2):
    with Pool(procs) as pool:
        return pool.map(run_one, jobs, chunksize=1)


def score(S):
    return np.mean([s["sla_viol_pct"] + s["failed_pct"] for s in S]), np.mean([s["rel_cost"] for s in S])


def tune(policy, grid, seeds):
    best = None
    for pd in grid:
        S = pmap([(policy, s, pd, None, None, "val", 0) for s in seeds])
        sc, cost = score(S)
        if best is None or sc < best[0] - 0.02 or (abs(sc - best[0]) <= 0.02 and cost < best[1]):
            best = (sc, cost, pd)
    return best


def stat_block(vals):
    v = np.asarray(vals, float); n = len(v)
    m, sd = float(v.mean()), float(v.std(ddof=1)) if n > 1 else 0.0
    h = float(stats.t.ppf(0.975, n - 1) * sd / np.sqrt(n)) if n > 1 else 0.0
    return dict(mean=m, sd=sd, ci95=[m - h, m + h])


METRICS = ["p99_ms", "mean_ms", "sla_viol_pct", "failed_pct", "rel_cost", "mttr_s", "dec_ms", "transitions"]


def summarise_runs(S):
    return {k: stat_block([s[k] for s in S]) for k in METRICS}


def compare(A, B, key):
    a = np.array([s[key] for s in A]); b = np.array([s[key] for s in B])
    d = a - b
    if np.allclose(d, 0):
        return dict(p=1.0, rbc=0.0)
    w = stats.wilcoxon(a, b, zero_method="wilcox")
    # rank-biserial correlation (paired)
    rk = stats.rankdata(np.abs(d[d != 0])); pos = rk[d[d != 0] > 0].sum(); neg = rk[d[d != 0] < 0].sum()
    return dict(p=float(w.pvalue), rbc=float((pos - neg) / (pos + neg)))


def holm(ps):
    o = np.argsort(ps); m = len(ps); adj = np.empty(m); run = 0
    for k, i in enumerate(o):
        run = max(run, (m - k) * ps[i]); adj[i] = min(1.0, run)
    return adj.tolist()


if __name__ == "__main__":
    which = sys.argv[1:] or ["tune", "main", "forecast", "ablation", "load", "sensitivity"]
    path = os.path.join(OUT, "cluster.json")
    R = json.load(open(path)) if os.path.exists(path) else {}
    VAL_EV = events_in(int(VAL["idx"][0]) + 60, int(VAL["idx"][-1])) if VAL is not None else None
    TEST = list(range(1, 31)); VALS = list(range(101, 111))
    R["test_events"] = len(TEST_EV)
    if "tune" in which:
        grids = {
            "microservices": [dict(hpa_target=a, hpa_down_window=b) for a in (.5, .6, .7, .8) for b in (120., 300.)],
            "hansel": [dict(hpa_target=a, hpa_down_window=b) for a in (.5, .6, .7, .8) for b in (120., 300.)],
            "phybrid": [dict(hpa_target=a, hpa_down_window=b) for a in (.5, .6, .7, .8) for b in (120., 300.)],
            "xscale": [dict(hpa_target=a, hpa_down_window=b) for a in (.5, .6, .7, .8) for b in (120., 300.)],
            "atlas": [dict(switch_pen=a, rho_max=b, hpa_target=c) for a in (.02, .05, .1) for b in (.75, .85) for c in (.6, .7)],
        }
        R["tuned"] = {"monolith": {}}
        for pol, g in grids.items():
            t0 = time.time(); b = tune(pol, g, VALS)
            R["tuned"][pol] = b[2]; print(pol, b, f"{time.time()-t0:.0f}s", flush=True)
        json.dump(R, open(path, "w"), indent=1)
    T = R["tuned"]
    if "main" in which:
        runs = {}
        for pol in ["monolith", "microservices", "hansel", "phybrid", "xscale", "atlas"]:
            t0 = time.time()
            runs[pol] = pmap([(pol, s, T[pol], None, None, "test", 0) for s in TEST])
            print(pol, {k: round(v["mean"], 2) for k, v in summarise_runs(runs[pol]).items()}, f"{time.time()-t0:.0f}s", flush=True)
        R["main"] = {pol: summarise_runs(S) for pol, S in runs.items()}
        tests = {}
        for key in ["p99_ms", "sla_viol_pct", "failed_pct", "rel_cost", "mttr_s"]:
            ps, res = [], {}
            for pol in ["monolith", "microservices", "hansel", "phybrid", "xscale"]:
                c = compare(runs["atlas"], runs[pol], key); res[pol] = c; ps.append(c["p"])
            for pol, pa in zip(res, holm(ps)):
                res[pol]["p_holm"] = pa
            tests[key] = res
        R["main_tests"] = tests
        R["main_traces"] = {pol: runs[pol][0].get("trace") for pol in ("atlas", "microservices", "monolith")}
        R["main_mode_share"] = {pol: np.mean([s["mode_share"] for s in runs[pol]], 0).tolist() for pol in runs}
        R["main_recovery_steps"] = [rr["steps"] for s in runs["atlas"] for rr in s["recoveries"]]
        json.dump(R, open(path, "w"), indent=1)
    if "forecast" in which:
        F = {}
        for su in [(8.0, 30.0), (60.0, 120.0)]:
            key = f"startup {int(su[0])}-{int(su[1])} s"; F[key] = {}
            pd = dict(T["atlas"]); pd["startup_s"] = su
            for name, opts in [("fsm-thresholds, reactive", dict(bip=False)), ("none", None), ("sn", None),
                               ("ar", None), ("lstm", None), ("oracle", None)]:
                fcn = "none" if name.startswith("fsm") else name
                S = pmap([("atlas", s, pd, opts, fcn, "test", 0) for s in TEST])
                F[key][name] = summarise_runs(S)
                print(key, name, {k: round(v["mean"], 2) for k, v in F[key][name].items()}, flush=True)
            pdm = dict(T["microservices"]); pdm["startup_s"] = su
            F[key]["static microservices (HPA)"] = summarise_runs(
                pmap([("microservices", s, pdm, None, None, "test", 0) for s in TEST]))
        R["forecast_value"] = F
        json.dump(R, open(path, "w"), indent=1)
    if "ablation" in which:
        A = {}
        for name, opts in [("ATLAS (full)", {}), ("- LSTM forecast (reactive)", dict(forecast=False)),
                           ("- anomaly detector", dict(anomaly=False)), ("- BIP (fixed thresholds)", dict(bip=False)),
                           ("- hybrid mode (binary tight/loose)", dict(hybrid=False)),
                           ("- self-healing (k8s restart)", dict(heal="k8s")), ("- hysteresis", dict(hysteresis=False))]:
            fcn = "none" if opts.get("forecast") is False else None
            S = pmap([("atlas", s, T["atlas"], opts, fcn, "test", 0) for s in TEST])
            A[name] = summarise_runs(S); A[name]["mode_share"] = np.mean([s["mode_share"] for s in S], 0).tolist()
            print(name, {k: round(v["mean"], 2) for k, v in A[name].items() if isinstance(v, dict)}, flush=True)
        R["ablation"] = A
        json.dump(R, open(path, "w"), indent=1)
    if "load" in which:
        LD = {}; seeds = list(range(1, 11))
        for sc in (0.5, 1.0, 1.5, 2.0, 2.5):
            LD[str(sc)] = {}
            for pol in ["monolith", "microservices", "hansel", "phybrid", "xscale", "atlas"]:
                pd = dict(T[pol]); pd["_scale"] = sc
                S = pmap([(pol, s, pd, None, None, "test", 0) for s in seeds])
                LD[str(sc)][pol] = {k: stat_block([s[k] for s in S]) for k in ["p99_ms", "sla_viol_pct", "failed_pct", "rel_cost"]}
            print("load", sc, {p_: round(v["sla_viol_pct"]["mean"], 2) for p_, v in LD[str(sc)].items()}, flush=True)
        R["load_sweep"] = LD
        json.dump(R, open(path, "w"), indent=1)
    if "sensitivity" in which:
        SEN = {}; seeds = list(range(1, 11))
        sweeps = {
            "workload intensity (x)": [("scale", v) for v in (0.5, 1.0, 1.5, 2.0)],
            "service demand (x)": [("demand", v) for v in (0.7, 1.0, 1.3)],
            "network latency (ms)": [("net_ms", v) for v in (1.0, 4.0, 10.0, 20.0)],
            "pod start-up (s)": [("startup_s", v) for v in ((2.0, 5.0), (8.0, 30.0), (30.0, 60.0), (60.0, 120.0))],
            "forecast MAPE (%)": [("noise", v) for v in (0.0, 0.1, 0.2, 0.4)],
            "failures per run": [("nfail", v) for v in (0, 1, 3)],
            "weights (alpha,beta,gamma)": [("w", v) for v in ((1, 1, 1), (2, 1, 1), (1, 2, 1), (1, 1, 5))],
            "switching penalty": [("switch_pen", v) for v in (0.0, 0.05, 0.2)],
        }
        for sw, vals in sweeps.items():
            SEN[sw] = {}
            for name, v in vals:
                res = {}
                for pol in ("atlas", "microservices", "hansel"):
                    pd = dict(T[pol]); noise = 0; opts = None; fcn = None
                    if name == "scale":
                        pd["_scale"] = v
                    elif name == "demand":
                        pd["demand"] = Params().demand * v
                    elif name == "noise":
                        noise = v
                    elif name == "nfail":
                        pd["_nfail"] = v
                    elif name == "w":
                        if pol != "atlas": continue
                        pd.update(alpha=v[0], beta=v[1], gamma=v[2])
                    elif name == "switch_pen":
                        if pol != "atlas": continue
                        pd["switch_pen"] = v
                    else:
                        pd[name] = v
                    S = pmap([(pol, s, pd, opts, fcn, "test", noise) for s in seeds])
                    res[pol] = {k: stat_block([s[k] for s in S]) for k in ["p99_ms", "sla_viol_pct", "failed_pct", "rel_cost"]}
                SEN[sw][str(v)] = res
                print(sw, v, {p_: (round(x["sla_viol_pct"]["mean"], 2), round(x["rel_cost"]["mean"], 2)) for p_, x in res.items()}, flush=True)
        R["sensitivity"] = SEN
        json.dump(R, open(path, "w"), indent=1)
