#!/usr/bin/env python3
"""Machine-learning and optimisation lab: the paper's coupling optimiser and every learner in ATLAS.

Runs the repository's own code (no copies): the coupling BIP from atlas_sim/cluster.py (read from
atlas_sim.zip), the three BIP solvers from run_bip_timing.py, the paper's traffic and telemetry
generators, and the ATLAS Go learners from android-app/. Needs numpy, scipy and scikit-learn
(requirements.txt); PyTorch is not needed.

    python3 ml_lab/ml_optimisation_lab.py              # every section (about 20 s)
    python3 ml_lab/ml_optimisation_lab.py --section 5  # one section

Sections
  1. The coupling BIP: which modules ATLAS extracts as load rises
  2. Inside one decision: latency, cost, risk and availability of every configuration
  3. Anomaly-aware optimisation: an Isolation-Forest score raises a module's crash risk
  4. Three solvers: exhaustive enumeration, branch-and-bound (HiGHS), LP relaxation + rounding
  5. Training is optimisation too: gradient descent vs Adam, early stopping, baselines
  6. Isolation Forest on the paper's telemetry
  7. Reinforcement learning in ATLAS Go: REINFORCE dispatch and Q-learning courier timing
See docs/MACHINE_LEARNING_OPTIMISATION.md for the full teaching guide.
"""
from __future__ import annotations

import argparse
import sys
import time
from itertools import product
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SIM = ROOT / 'atlas_sim'
sys.path.insert(0, str(ROOT if SIM.is_dir() else ROOT / 'atlas_sim.zip'))   # extracted or zipped
sys.path.insert(1, str(ROOT / 'android-app'))
sys.path.insert(2, str(ROOT / 'android-app' / 'training'))

from atlas_sim.cluster import Params, Sim                       # noqa: E402  (paper's simulator)
from atlas_sim.traffic import SERVICES, ecommerce_trace, telemetry  # noqa: E402


def heading(text: str) -> None:
    print('\n' + text + '\n' + '-' * len(text))


def decision_maker(**params) -> Sim:
    """A Sim object holding only what Sim.bip needs: the paper's optimiser without the time loop."""
    sim = object.__new__(Sim)
    sim.p = Params(**{'switch_pen': 0.02, 'rho_max': 0.85, **params})   # tuned values (results/cluster.json)
    sim.n = len(SERVICES)
    sim.cores = np.full(sim.n, sim.p.pod_cores)
    sim.o = dict(hybrid=True, blast='max')
    sim.c = np.zeros(sim.n, int)              # currently deployed: everything inside the monolith
    sim.demand_est = sim.p.demand.copy()
    sim.anom_module = -1
    sim.dec_ms = []
    return sim


def shape(c) -> str:
    loose = [SERVICES[i] for i in range(len(c)) if c[i]]
    mode = 'tight (monolith)' if not loose else 'loose (all services)' if len(loose) == len(c) else 'hybrid'
    return f"{''.join(map(str, c))}  {mode:<20} {', '.join(loose) or '-'}"


# ---------------------------------------------------------------- 1
def section_bip() -> None:
    heading('1. The coupling BIP (atlas_sim/cluster.py -> Sim.bip), solved every 5 s')
    print('c_i = 0 keeps module i inside the monolith (tight), c_i = 1 extracts it as a service (loose).')
    print('min J(c) = a*L/L0 + b*C/C0 + g*R/R0 + switching cost   s.t. rho_m <= 0.85, L <= 200 ms,')
    print('          replicas <= 40, availability >= 0.99; all 2^6 = 64 configurations are evaluated.\n')
    print('modules in order: ' + ', '.join(SERVICES) + '\n')
    print(f"{'load (req/s)':>12}  {'c':<6}  shape")
    times = []
    for lam in (300, 1000, 2000, 2500, 3000, 4000, 6000, 9000):
        sim = decision_maker()
        sim.bip(0, lam, 0.0)                          # first call also builds the 64 candidates
        print(f'{lam:>12}  {shape(sim.bip(0, lam, 0.0))}')
        times.append(sim.dec_ms[-1])
    print(f'one decision takes {np.median(times):.2f} ms here (paper: 0.27 ms mean per decision in the 30 test runs)')
    print('Light load: one process is cheapest. As load rises, modules leave the monolith so it stays below')
    print('rho_max; which ones is the latency/cost/blast-radius trade-off (Catalogue carries the most work).')


# ---------------------------------------------------------------- 2
def section_inside(lam: float = 6000.0) -> None:
    heading(f'2. Inside one decision at {lam:.0f} req/s (Sim.eval_all over all 64 configurations)')
    sim = decision_maker()
    sim.bip(0, lam, 0.0)                                   # builds sim.CM and the reference point
    p, CM = sim.p, sim.CM
    L, C, R, A, rho, reps = sim.eval_all(CM, lam, sim.demand_est, np.full(sim.n, p.p0))
    L0, C0, R0 = sim.ref
    J = p.alpha * L / L0 + p.beta * C / C0 + p.gamma * p.gamma_scale * R / R0 \
        + p.switch_pen * np.abs(CM - sim.c[None, :]).sum(1)
    ok = (rho <= p.rho_max) & (L <= p.sla_ms) & (reps <= p.max_rep).all(1) & (A >= p.a_min)
    order = np.argsort(np.where(ok, J, np.inf))
    print(f"{'c':>6} {'rho_m':>6} {'L ms':>8} {'cores':>6} {'avail':>8} {'J':>6}  feasible")
    for k in list(order[:6]) + [int(np.flatnonzero(CM.sum(1) == 0)[0]), int(np.flatnonzero(CM.sum(1) == 6)[0])]:
        print(f"{''.join(map(str, CM[k])):>6} {rho[k]:6.2f} {min(L[k], 9999):8.1f} {C[k]:6.1f} {A[k]:8.5f} "
              f"{J[k]:6.3f}  {'yes' if ok[k] else 'no: ' + ('monolith saturated' if rho[k] > p.rho_max else 'SLA/avail')}")
    print(f'{int(ok.sum())} of 64 configurations are feasible; the optimiser picks the first row.')
    print('The last two rows are the classic choices: all-monolith (infeasible) and all-microservices (costly).')


# ---------------------------------------------------------------- 3
def section_anomaly() -> None:
    heading('3. Anomaly-aware optimisation: Payment misbehaves at 1000 req/s')
    print('The Isolation-Forest score a raises Payment\'s crash probability: p = p0 + p_a / (1 + e^(-20(a - 0.7))).')
    for a in (0.0, 0.5, 0.65, 0.7, 0.8, 0.95):
        sim = decision_maker()
        sim.anom_module = SERVICES.index('Payment')
        print(f'  a = {a:4.2f} -> {shape(sim.bip(0, 1000, a))}')
    print('Above the alert level the optimiser isolates Payment so a crash cannot take the monolith down')
    print('(blast radius). In Sim.run, a >= 0.9 forces every module out (emergency mode).')


# ---------------------------------------------------------------- 4
def bip_solvers():
    """instance() and lp_round() from run_bip_timing.py, loaded without running its benchmark."""
    source = (ROOT / 'run_bip_timing.py').read_text()
    namespace: dict = {'__file__': str(ROOT / 'run_bip_timing.py')}
    exec(compile(source.split('\nR = {}')[0], 'run_bip_timing.py', 'exec'), namespace)
    return namespace


def section_solvers() -> None:
    heading('4. Three ways to solve the linearised BIP (run_bip_timing.py)')
    from scipy.optimize import Bounds, LinearConstraint, milp
    ns = bip_solvers()
    print(f"{'n':>4} {'enumerate 2^n':>14} {'branch&bound':>13} {'LP + rounding':>14} {'LP gap':>8}")
    for n in (6, 12, 16, 50, 200):
        g = np.random.default_rng(n)
        f, A, ub, risk = ns['instance'](n, g)
        t_enum = '-'
        if n <= 16:
            t0 = time.perf_counter()
            M = ((np.arange(2 ** n)[:, None] >> np.arange(n)[None, :]) & 1).astype(float)
            okm = np.all(M @ A.T <= ub + 1e-9, 1)
            best = float(np.min(np.where(okm, M @ f, np.inf)))
            t_enum = f'{(time.perf_counter() - t0) * 1000:9.1f} ms'
        t0 = time.perf_counter()
        m = milp(f, constraints=LinearConstraint(A, -np.inf, ub), integrality=np.ones(n), bounds=Bounds(0, 1))
        t_milp = (time.perf_counter() - t0) * 1000
        t0 = time.perf_counter()
        c = ns['lp_round'](f, A, ub, risk)
        t_lp = (time.perf_counter() - t0) * 1000
        gap = 100 * (f @ c - m.fun) / max(abs(m.fun), 1e-9) if ns['feasible'](c, A, ub) else float('nan')
        if n <= 16:
            assert abs(best - m.fun) < 1e-6 * max(1, abs(best)), 'enumeration and branch-and-bound disagree'
        print(f'{n:>4} {t_enum:>14} {t_milp:10.1f} ms {t_lp:11.1f} ms {gap:7.2f}%')
    print('Enumeration is exact but doubles with every module; branch-and-bound stays exact and fast;')
    print('LP relaxation + risk-aware rounding (tau = 0.5 - 0.3*risk/max risk) + greedy repair is near-optimal')
    print('and scales. Paper, n = 500: 401 ms (B&B) vs 6.4 ms (LP), median gap 0.23% (results/bip_timing.json).')


# ---------------------------------------------------------------- 5
def section_training(lags: int = 30) -> None:
    heading('5. Training is optimisation too: fit a forecaster by gradient descent and by Adam')
    r, _, _ = ecommerce_trace(days=21, seed=2026, n_events=6)
    y = np.log1p(r.astype(float))
    mu, sd = y[: 14 * 1440].mean(), y[: 14 * 1440].std()
    z = (y - mu) / sd
    idx = np.arange(lags, len(z) - 5)
    X = np.stack([z[idx - k] for k in range(lags)], 1)
    X = np.hstack([X, np.ones((len(idx), 1))])
    target = z[idx + 5]                                  # 5-minute-ahead, as in the paper
    tr, va = idx < 14 * 1440, (idx >= 14 * 1440) & (idx < 17 * 1440)
    te = idx >= 17 * 1440
    mse = lambda w, m: float(np.mean((X[m] @ w - target[m]) ** 2))

    def fit(optimiser: str, lr: float, epochs: int = 300, patience: int = 15):
        w = np.zeros(X.shape[1]); m1 = np.zeros_like(w); m2 = np.zeros_like(w)
        best, best_w, bad, curve = np.inf, w, 0, []
        rng = np.random.default_rng(0)
        rows = np.flatnonzero(tr)
        for ep in range(1, epochs + 1):
            for batch in np.array_split(rng.permutation(rows), 40):
                grad = 2 * X[batch].T @ (X[batch] @ w - target[batch]) / len(batch)
                if optimiser == 'adam':                  # torch.optim.Adam defaults: b1 .9, b2 .999
                    m1 = .9 * m1 + .1 * grad; m2 = .999 * m2 + .001 * grad ** 2
                    w = w - lr * (m1 / (1 - .9 ** ep)) / (np.sqrt(m2 / (1 - .999 ** ep)) + 1e-8)
                else:
                    w = w - lr * grad
            v = mse(w, va); curve.append(v)
            if v < best - 1e-5:
                best, best_w, bad = v, w.copy(), 0
            else:
                bad += 1
                if bad >= patience:                      # early stopping, as atlas_sim/forecast.py train()
                    break
        return best_w, curve

    def mae(pred, m):
        return float(np.mean(np.abs(np.expm1(pred * sd + mu) - np.expm1(target[m] * sd + mu))))

    print(f"{'model':<40} {'epochs':>6} {'val MSE':>8} {'test MAE (req/s)':>17}")
    for name, opt, lr in (('AR(30), plain gradient descent', 'gd', 0.01), ('AR(30), Adam', 'adam', 0.003)):
        w, curve = fit(opt, lr)
        print(f'{name:<40} {len(curve):>6} {min(curve):8.4f} {mae(X[te] @ w, te):17.1f}')
    w_exact = np.linalg.lstsq(X[tr], target[tr], rcond=None)[0]
    print(f"{'AR(30), closed form (least squares)':<40} {'-':>6} {mse(w_exact, va):8.4f} {mae(X[te] @ w_exact, te):17.1f}")
    print(f"{'persistence (last value)':<40} {'-':>6} {'-':>8} {mae(X[te][:, 0], te):17.1f}")
    print(f"{'seasonal naive (same minute yesterday)':<40} {'-':>6} {'-':>8} {mae(z[idx[te] + 5 - 1440], te):17.1f}")
    print('This AR model is convex and well scaled, so both optimisers reach the least-squares solution and')
    print('early stopping on the validation days ends training once it stops improving. Adam\'s per-weight step')
    print('sizes matter for the non-convex, badly scaled LSTM in the paper: Adam, lr 1e-3, gradient clipping 1.0,')
    print('early stopping (patience 10). Its test MAE at 5 min is 51.7 req/s vs 72.2 persistence and 111.8')
    print('seasonal naive (results/forecast.json).')


# ---------------------------------------------------------------- 6
def section_iforest() -> None:
    heading('6. Isolation Forest on the paper\'s telemetry (run_anomaly.py, one seed)')
    from sklearn.ensemble import IsolationForest
    from sklearn.metrics import roc_auc_score
    g = np.random.default_rng(1)
    r, mask, _ = ecommerce_trace(days=30, seed=2026, n_events=8)
    normal = r[(mask == 0) & (r > 50)]
    Xn = telemetry(g.choice(normal, 4000), g)
    cats = ['cpu', 'mem', 'down', 'flood', 'netdisk']
    Xa = np.vstack([telemetry(g.choice(normal, 60), np.random.default_rng(k), anomaly=c) for k, c in enumerate(cats)])
    model = IsolationForest(n_estimators=100, max_samples=256, contamination=0.05, random_state=0).fit(Xn[:3000])
    X = np.vstack([Xn[3000:], Xa]); y = np.r_[np.zeros(1000), np.ones(len(Xa))]
    score = -model.score_samples(X)
    print('Trained on normal telemetry only [rps, cpu, mem, latency, errors, queue, net, disk]; no labels.')
    print(f'ROC-AUC on held-out normal + {len(Xa)} injected anomalies: {roc_auc_score(y, score):.4f} (paper: 0.9999)')
    for k, c in enumerate(cats):
        s = score[1000 + 60 * k: 1060 + 60 * k]
        print(f'  {c:<8} mean score {s.mean():.3f}   (normal {score[:1000].mean():.3f})')
    print('Anomalies are isolated in fewer random splits, so their path length is short and the score high.')


# ---------------------------------------------------------------- 7
def section_rl() -> None:
    heading('7. Reinforcement learning in ATLAS Go (android-app/atlas_go/intelligence.py, training/rl_sim.py)')
    from atlas_go import intelligence as I
    lab = I.LearningLab()
    print('Ride dispatch: softmax policy over 4 drivers, features [-eta/5, acceptance, -surge*last, -surge],')
    print('trained with REINFORCE (policy gradient with a running-average baseline). Expected cost in minutes:')
    for episodes in (0, 300, 3000, 12000):
        lab.reset(); lab.train(episodes)
        res = lab.result()
        print(f'  after {episodes:>6} episodes  candidate {res["candidate"]:.2f}   nearest-driver rule {res["nearest"]:.2f}'
              f'   approved v1 policy {res["approved"]:.2f}   w = {res["weights"]}')
    import rl_sim
    Q, policy, *_ = rl_sim.train_food(n=15000)
    print('Courier timing: tabular Q-learning, epsilon-greedy, state = kitchen slack (prep - travel, minutes):')
    print('  slack -> wait before dispatch: ' + ', '.join(f'{s}->{policy[s]}' for s in (0, 2, 4, 6, 8, 10, 12)))
    plan = I.courier_plan(0)
    print(f"  in the app: kitchen {plan['prep']} min, travel {plan['travel']} min -> send after {plan['dispatch_after']} min,"
          f" courier waits {plan['courier_wait']} min instead of {plan['naive_wait']}")


SECTIONS = [section_bip, section_inside, section_anomaly, section_solvers, section_training, section_iforest, section_rl]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--section', type=int, choices=range(1, len(SECTIONS) + 1), help='run one section')
    args = parser.parse_args()
    for k, section in enumerate(SECTIONS, 1):
        if args.section in (None, k):
            section()


if __name__ == '__main__':
    main()
