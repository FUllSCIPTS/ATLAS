"""Shared helpers for the ATLAS optimisation experiments (opt01_*.py ... opt20_*.py).

Each experiment is its own file and runs on its own:

    python3 ml_lab/optimisation/opt08_branch_and_bound.py

`run_optimisation.py` in this folder lists them, runs them all, or runs a study path. The problems are
ATLAS's own wherever possible: the paper's coupling BIP (atlas_sim/cluster.py, Sim.bip), its service
demands and visit ratios (atlas_sim/traffic.py), the BIP instances of run_bip_timing.py, Cork geography
and the dispatch cost model from ATLAS Go (android-app/atlas_go/). Needs numpy and scipy.
"""
from __future__ import annotations

import math
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'atlas_sim.zip'))
sys.path.insert(1, str(ROOT / 'android-app'))


def heading(title: str) -> None:
    print('\n' + '=' * 78)
    print(title)
    print('=' * 78)


def note(text: str) -> None:
    print(f'  -> {text}')


def show(label: str, value) -> None:
    print(f'  {label:<38} {value}')


def table(header, rows) -> None:
    widths = [max(len(str(h)), *(len(str(r[i])) for r in rows)) for i, h in enumerate(header)]
    print('  ' + '  '.join(f'{h:>{w}}' for h, w in zip(header, widths)))
    for r in rows:
        print('  ' + '  '.join(f'{v:>{w}}' for v, w in zip(r, widths)))


def run(main, doc: str) -> None:
    heading(doc.strip().split('\n')[0])
    start = time.perf_counter()
    main()
    print(f'  ({time.perf_counter() - start:.1f} s)')


# --------------------------------------------------------------------------- the paper's coupling BIP
def decision_maker(**params):
    """A Sim object holding only what Sim.bip needs: the paper's optimiser without the time loop."""
    from atlas_sim.cluster import Params, Sim
    from atlas_sim.traffic import SERVICES
    sim = object.__new__(Sim)
    sim.p = Params(**{'switch_pen': 0.02, 'rho_max': 0.85, **params})   # tuned values (results/cluster.json)
    sim.n = len(SERVICES)
    sim.cores = np.full(sim.n, sim.p.pod_cores)
    sim.o = dict(hybrid=True, blast='max')
    sim.c = np.zeros(sim.n, int)
    sim.demand_est = sim.p.demand.copy()
    sim.anom_module = -1
    sim.dec_ms = []
    return sim


def coupling_objective(lam: float):
    """Return (sim, f) where f(CM) gives J, feasible, latency, cores, availability for configurations CM
    (rows of 0/1 over the six modules), exactly as Sim.bip scores them."""
    sim = decision_maker()
    sim.bip(0, lam, 0.0)                                   # builds the reference point sim.ref

    def f(CM):
        CM = np.atleast_2d(np.asarray(CM, int))
        p = sim.p
        L, C, R, A, rho, reps = sim.eval_all(CM, lam, sim.demand_est, np.full(sim.n, p.p0))
        L0, C0, R0 = sim.ref
        J = p.alpha * L / L0 + p.beta * C / C0 + p.gamma * p.gamma_scale * R / R0 \
            + p.switch_pen * np.abs(CM - sim.c[None, :]).sum(1)
        ok = (rho <= p.rho_max) & (L <= p.sla_ms) & (reps <= p.max_rep).all(1) & (A >= p.a_min)
        return J, ok, L, C, A
    return sim, f


def bip_instances():
    """instance(), lp_round() and feasible() from run_bip_timing.py, loaded without running its benchmark."""
    source = (ROOT / 'run_bip_timing.py').read_text()
    namespace: dict = {'__file__': str(ROOT / 'run_bip_timing.py')}
    exec(compile(source.split('\nR = {}')[0], 'run_bip_timing.py', 'exec'), namespace)
    return namespace


# --------------------------------------------------------------------------- Cork geography
def cork_points(n: int, seed: int = 0):
    """n delivery/pickup points around Cork's landmarks (ATLAS Go geo.py), as (lat, lon)."""
    from atlas_go.geo import KITCHEN_COORDS, PLACE_COORDS, ZONE_COORDS
    anchors = list(PLACE_COORDS) + list(ZONE_COORDS.values()) + list(KITCHEN_COORDS)
    rng = np.random.default_rng(seed)
    pts = []
    for i in range(n):
        lat, lon = anchors[i % len(anchors)]
        pts.append((lat + rng.normal(0, 0.003), lon + rng.normal(0, 0.005)))
    return pts


def km(a, b) -> float:
    from atlas_go.geo import haversine_km
    return haversine_km(a, b)


def distance_matrix(pts):
    n = len(pts)
    return np.array([[km(pts[i], pts[j]) for j in range(n)] for i in range(n)])


def tour_length(tour, D) -> float:
    return float(sum(D[tour[i], tour[(i + 1) % len(tour)]] for i in range(len(tour))))


def rastrigin(x):
    x = np.asarray(x, float)
    return 10 * x.shape[-1] + (x ** 2 - 10 * np.cos(2 * math.pi * x)).sum(-1)
