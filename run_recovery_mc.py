"""Experiment R: event-level (continuous-time) recovery model per crash class.

Each recovery is a sequence of timestamped steps whose durations are drawn
from the distributions below (seconds).  No time-step discretisation is
involved, so sub-second and few-second recovery intervals are resolved.
C1 step durations at process level are cross-checked against the measured
prototype (prototype/proto_run.py).  Output: results/recovery_mc.json
"""
import json, os, zlib
import numpy as np
from scipy import stats

OUT = os.path.join(os.path.dirname(__file__), "results")
U = lambda g, a, b: float(g.uniform(a, b))

# ATLAS defaults: probe 1 s, 3 consecutive failures, warm restart 2-6 s,
# Tier-1 replay 0.3-1.5 s, Tier-2 restore 5-20 s, Tier-3 restore 60-300 s,
# verify 1-2 s, canary 3 s.  Kubernetes defaults: liveness/readiness period
# 10 s, failureThreshold 3, CrashLoopBackOff 10-40 s.  Manual: on-call
# acknowledgement 60-180 s + diagnosis/repair ranges given per class.
def atlas(cls, g):
    if cls == "C1-exit":
        s = dict(detect=U(g, .2, .8), classify=.05, isolate=.1, restart=U(g, 2, 6), restore=U(g, .3, 1.5),
                 verify=U(g, 1, 2), canary=3.0)
    elif cls == "C1-hang":
        s = dict(detect=2 + U(g, 0, 1) + .3, classify=.05, isolate=.1, restart=U(g, 2, 6),
                 restore=U(g, .3, 1.5), verify=U(g, 1, 2), canary=3.0)
    elif cls == "C2":     # crash after a config change: two failed restarts, then GitOps rollback
        s = dict(detect=2 * U(g, 2, 6) + U(g, .2, .8), classify=.05, isolate=.1, rollback=U(g, 5, 15),
                 restart=U(g, 2, 6), restore=U(g, .3, 1.5), verify=U(g, 1, 2), canary=3.0)
    elif cls == "C3":     # checksum mismatch -> Tier-2 (p=.8) or Tier-3 (p=.2) restore + replay
        tier = U(g, 5, 20) if g.random() < .8 else U(g, 60, 300)
        s = dict(detect=U(g, .1, 1), classify=.05, isolate=.1, restore=tier, replay=U(g, 1, 5),
                 verify=U(g, 10, 30), canary=3.0)
    elif cls == "C4":     # cascade: anomaly + multi-failure signature, emergency loose, parallel restarts
        s = dict(detect=U(g, 3, 10), classify=.05, isolate=U(g, .5, 2), restart=U(g, 8, 30),
                 restore=U(g, .3, 1.5), verify=U(g, 2, 5), canary=3.0)
    return s


def k8s(cls, g):
    if cls == "C1-exit":
        s = dict(detect=U(g, .2, .8), restart=U(g, 2, 6), readiness=U(g, 0, 10), endpoints=U(g, 1, 2))
    elif cls == "C1-hang":
        s = dict(detect=20 + U(g, 0, 10) + 1, restart=U(g, 2, 6), readiness=U(g, 0, 10), endpoints=U(g, 1, 2))
    elif cls == "C2":     # CrashLoopBackOff until an operator rolls back
        s = dict(backoff=U(g, 10, 40) + U(g, 20, 80), page=U(g, 60, 180), rollback=U(g, 300, 900),
                 restart=U(g, 2, 6), readiness=U(g, 0, 10))
    elif cls == "C3":
        s = dict(detect=U(g, 60, 600), page=U(g, 60, 180), restore=U(g, 1800, 5400))
    elif cls == "C4":     # retry storm: repeated liveness failures and restarts across services
        s = dict(detect=20 + U(g, 0, 10), restart_rounds=sum(U(g, 8, 30) + U(g, 10, 40) for _ in range(int(g.integers(2, 5)))),
                 readiness=U(g, 0, 10))
    return s


def manual(cls, g):
    rep = {"C1-exit": (300, 900), "C1-hang": (300, 900), "C2": (1200, 3600), "C3": (3600, 10800), "C4": (1800, 7200)}[cls]
    return dict(page=U(g, 60, 180), repair=U(g, *rep))


def ci(v):
    v = np.asarray(v); n = len(v); m = v.mean(); h = stats.t.ppf(.975, n - 1) * v.std(ddof=1) / np.sqrt(n)
    return dict(mean=float(m), sd=float(v.std(ddof=1)), ci95=[float(m - h), float(m + h)],
                median=float(np.median(v)), p95=float(np.percentile(v, 95)))


R = {}
for cls in ["C1-exit", "C1-hang", "C2", "C3", "C4"]:
    R[cls] = {}
    for name, fn in (("ATLAS", atlas), ("Kubernetes defaults", k8s), ("Manual", manual)):
        g = np.random.default_rng(zlib.crc32(f"{cls}|{name}".encode()))
        runs = [fn(cls, g) for _ in range(30)]
        tot = [sum(s.values()) for s in runs]
        R[cls][name] = dict(mttr_s=ci(tot), steps_mean={k: float(np.mean([s[k] for s in runs])) for k in runs[0]})
    print(cls, {k: round(v["mttr_s"]["mean"], 1) for k, v in R[cls].items()})
json.dump(R, open(os.path.join(OUT, "recovery_mc.json"), "w"), indent=1)
