"""Experiment B: measured solve times of the coupling BIP (linearised form of
Eqs. (1)-(5)) as the number of modules n grows.
  exact-enum : exhaustive enumeration (Phase 2a without pruning)
  exact-milp : branch-and-bound/cut (HiGHS via scipy.optimize.milp)
  lp+round   : LP relaxation + risk-aware rounding + greedy repair (Phase 2b+3)
Output results/bip_timing.json
"""
import json, os, time
import numpy as np
from scipy.optimize import milp, linprog, LinearConstraint, Bounds

OUT = os.path.join(os.path.dirname(__file__), "results")


def instance(n, g):
    lm, ln = g.uniform(.01, .5, n), g.uniform(2, 15, n)
    kp, kn = g.uniform(.5, 3, n), g.uniform(.05, .5, n)
    p, d = g.uniform(1e-4, .05, n), g.integers(1, max(2, n // 3), n).astype(float)
    r = g.integers(1, 6, n).astype(float)
    a, b, c = 1.0, 1.0, 50.0
    f = a * (ln - lm) + b * (kp + kn) - c * p * d
    A = np.vstack([ln - lm, kp + kn, r, -(p * d)])         # latency, cost, replicas, availability
    ub = np.array([0.6 * (ln - lm).sum(), 0.6 * (kp + kn).sum(), 0.6 * r.sum(), -0.3 * (p * d).sum()])
    return f, A, ub, p * d


def feasible(c, A, ub):
    return np.all(A @ c <= ub + 1e-9)


def lp_round(f, A, ub, risk, delta=0.3):
    res = linprog(f, A_ub=A, b_ub=ub, bounds=[(0, 1)] * len(f), method="highs")
    x = res.x if res.status == 0 else np.full(len(f), 0.5)
    tau = 0.5 - delta * risk / max(risk.max(), 1e-12)
    c = (x >= tau).astype(float)
    for _ in range(4 * len(f)):                              # greedy repair
        viol = A @ c - ub
        if np.all(viol <= 1e-9):
            break
        k = int(np.argmax(viol))
        cand = np.where(c == (1 if k < 3 else 0))[0]
        if len(cand) == 0:
            break
        j = cand[np.argmax(A[k, cand] if k < 3 else risk[cand])]
        c[j] = 1 - c[j]
    return c


R = {}
for n in (6, 10, 16, 25, 50, 100, 200, 500):
    g = np.random.default_rng(n); t_enum, t_milp, t_lp, gap = [], [], [], []
    for _ in range(30):
        f, A, ub, risk = instance(n, g)
        if n <= 16:
            t0 = time.perf_counter()
            K = 2 ** n; M = ((np.arange(K)[:, None] >> np.arange(n)[None, :]) & 1).astype(float)
            ok = np.all(M @ A.T <= ub + 1e-9, 1); J = np.where(ok, M @ f, np.inf); _ = M[int(np.argmin(J))]
            t_enum.append((time.perf_counter() - t0) * 1000)
        t0 = time.perf_counter()
        m = milp(f, constraints=LinearConstraint(A, -np.inf, ub), integrality=np.ones(n), bounds=Bounds(0, 1))
        t_milp.append((time.perf_counter() - t0) * 1000)
        t0 = time.perf_counter(); c = lp_round(f, A, ub, risk); t_lp.append((time.perf_counter() - t0) * 1000)
        if m.status == 0 and feasible(c, A, ub):
            gap.append(100 * (f @ c - m.fun) / max(abs(m.fun), 1e-9))
    R[n] = dict(enum_ms=float(np.median(t_enum)) if t_enum else None, milp_ms=float(np.median(t_milp)),
                milp_p95_ms=float(np.percentile(t_milp, 95)), lp_round_ms=float(np.median(t_lp)),
                lp_gap_pct_median=float(np.median(gap)) if gap else None, lp_feasible=len(gap))
    print(n, R[n], flush=True)
json.dump(R, open(os.path.join(OUT, "bip_timing.json"), "w"), indent=1)
