"""Experiment A: Isolation Forest anomaly detection (full metric set).

Outputs results/anomaly.json, results/iforest.pkl, results/anomaly_scatter.npz
"""
import json, os, sys, pickle
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.metrics import roc_auc_score, average_precision_score, precision_recall_fscore_support
sys.path.insert(0, os.path.dirname(__file__))
from atlas_sim.traffic import ecommerce_trace, telemetry

OUT = os.path.join(os.path.dirname(__file__), "results"); os.makedirs(OUT, exist_ok=True)
CATS = ["cpu", "mem", "down", "flood", "netdisk"]
CAT_NAMES = {"cpu": "CPU exhaustion", "mem": "Memory/queue exhaustion",
             "down": "Downstream failure", "flood": "Request flood (DDoS-like)",
             "netdisk": "Network/disk delay"}
r, mask, _ = ecommerce_trace(365, seed=2026)
normal_r = r[(mask == 0) & (r > 50)]


def dataset(seed, sev=1.0):
    """sev < 1 blends each anomaly towards a normal state at the same load
    (X = X_normal + sev * (X_anom - X_normal)) to create subtler anomalies."""
    g = np.random.default_rng(seed)
    Xn = telemetry(g.choice(normal_r, 9500), g)
    Xa, ya = [], []
    for k, c in enumerate(CATS):
        rr = g.choice(normal_r, 100)
        g2 = np.random.default_rng(seed * 100 + k)
        base = telemetry(rr, np.random.default_rng(seed * 100 + k))
        an = telemetry(rr, np.random.default_rng(seed * 100 + k), anomaly=c)
        Xa.append(base + sev * (an - base)); ya += [k + 1] * 100
    X = np.concatenate([Xn] + Xa); y = np.array([0] * 9500 + ya)
    p = g.permutation(len(y)); return X[p], y[p]


def split(y, g):
    idx = g.permutation(len(y)); a, b = int(.6 * len(y)), int(.8 * len(y))
    return idx[:a], idx[a:b], idx[b:]


def rules(X):     # static threshold detector used as a baseline
    return (X[:, 1] > 85) | (X[:, 3] > 500) | (X[:, 2] > 90)


def evaluate(yb, pred, score=None):
    p, rc, f, _ = precision_recall_fscore_support(yb, pred, average="binary", zero_division=0)
    fpr = float(((pred == 1) & (yb == 0)).sum() / max((yb == 0).sum(), 1))
    d = dict(precision=float(p), recall=float(rc), F1=float(f), FPR=fpr)
    if score is not None:
        d["ROC_AUC"] = float(roc_auc_score(yb, score)); d["PR_AUC"] = float(average_precision_score(yb, score))
    return d


def norm_score(model, X, lo, hi):
    s = -model.score_samples(X)                   # Liu et al. anomaly score s(x,n) in (0,1]
    return np.clip((s - lo) / (hi - lo), 0, 1)


res = {"runs": [], "contamination": {}, "rules": [], "per_category": {c: [] for c in CATS},
       "severity": {}}
for seed in range(10):
    g = np.random.default_rng(100 + seed)
    X, y = dataset(seed); yb = (y > 0).astype(int)
    tr, va, te = split(y, g)
    m = IsolationForest(n_estimators=100, max_samples=256, contamination=0.05,
                        random_state=seed).fit(X[tr])       # labels never used in fitting
    sv = -m.score_samples(X[va]); lo, hi = np.percentile(sv, 1), np.percentile(sv, 99.9)
    a_te = norm_score(m, X[te], lo, hi)
    pred_c = (m.predict(X[te]) == -1).astype(int)             # contamination=0.05 threshold
    # validation-selected threshold (max F1), then frozen for test
    a_va = norm_score(m, X[va], lo, hi)
    grid = np.linspace(0.05, 0.99, 95)
    f1s = [evaluate(yb[va], (a_va >= t).astype(int))["F1"] for t in grid]
    t_star = float(grid[int(np.argmax(f1s))])
    run = dict(seed=seed, thr_val=t_star,
               contamination_005=evaluate(yb[te], pred_c, a_te),
               val_threshold=evaluate(yb[te], (a_te >= t_star).astype(int), a_te),
               alert_07=evaluate(yb[te], (a_te >= 0.7).astype(int)),
               emergency_09=evaluate(yb[te], (a_te >= 0.9).astype(int)))
    res["runs"].append(run)
    res["rules"].append(evaluate(yb[te], rules(X[te]).astype(int)))
    pv = (a_te >= t_star)
    for k, c in enumerate(CATS):
        mk = y[te] == k + 1
        res["per_category"][c].append(dict(IF=float(pv[mk].mean()), rules=float(rules(X[te][mk]).mean())))
    for cont in ["auto", 0.01, 0.03, 0.05, 0.10]:
        mm = IsolationForest(n_estimators=100, max_samples=256, contamination=cont,
                             random_state=seed).fit(X[tr])
        res["contamination"].setdefault(str(cont), []).append(
            evaluate(yb[te], (mm.predict(X[te]) == -1).astype(int), -mm.score_samples(X[te])))
    for sev in (0.5, 0.25):
        Xs, ys = dataset(seed, sev); ybs = (ys > 0).astype(int)
        ms = IsolationForest(n_estimators=100, max_samples=256, contamination=0.05,
                             random_state=seed).fit(Xs[tr])
        svs = -ms.score_samples(Xs[va]); los, his = np.percentile(svs, 1), np.percentile(svs, 99.9)
        avs = norm_score(ms, Xs[va], los, his)
        ts = float(grid[int(np.argmax([evaluate(ybs[va], (avs >= t).astype(int))["F1"] for t in grid]))])
        ats = norm_score(ms, Xs[te], los, his)
        res["severity"].setdefault(str(sev), []).append(evaluate(ybs[te], (ats >= ts).astype(int), ats))
        res["severity"].setdefault(str(sev) + "_rules", []).append(evaluate(ybs[te], rules(Xs[te]).astype(int)))
    if seed == 0:
        pickle.dump(dict(model=m, lo=lo, hi=hi), open(os.path.join(OUT, "iforest.pkl"), "wb"))
        np.savez_compressed(os.path.join(OUT, "anomaly_scatter.npz"), X=X[te], y=y[te], a=a_te, thr=t_star)


def agg(lst):
    keys = lst[0].keys()
    return {k: [float(np.mean([d[k] for d in lst])), float(np.std([d[k] for d in lst], ddof=1))] for k in keys}


summary = {k: agg([r_[k] for r_ in res["runs"]]) for k in
           ["contamination_005", "val_threshold", "alert_07", "emergency_09"]}
summary["rules"] = agg(res["rules"])
summary["thr_val"] = [float(np.mean([r_["thr_val"] for r_ in res["runs"]])),
                      float(np.std([r_["thr_val"] for r_ in res["runs"]], ddof=1))]
summary["contamination"] = {k: agg(v) for k, v in res["contamination"].items()}
summary["severity"] = {k: agg(v) for k, v in res["severity"].items()}
summary["per_category"] = {CAT_NAMES[c]: {"IF": [float(np.mean([d["IF"] for d in v])), float(np.std([d["IF"] for d in v], ddof=1))],
                                          "rules": [float(np.mean([d["rules"] for d in v])), float(np.std([d["rules"] for d in v], ddof=1))]}
                           for c, v in res["per_category"].items()}
json.dump(summary, open(os.path.join(OUT, "anomaly.json"), "w"), indent=1)
print(json.dumps(summary, indent=1))
