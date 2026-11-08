#!/usr/bin/env python3
"""OPT 15 - Local search, random restarts and tabu search on a large coupling BIP.

ATLAS link: run_bip_timing.py's linearised coupling BIP with 60 modules (2^60 plans), its latency, cost
and replica budgets halved so the constraints bind (with loose budgets every method finds the optimum).
Flip one module's decision at a time and keep improvements (hill climbing): fast, but it stops at the
first local optimum.
Restarts and tabu search (forbid recently flipped modules, accept the best non-improving move) escape.
HiGHS gives the true optimum to measure against.
Applies to: scheduling, timetabling, graph colouring, feature selection - wherever exact solvers stall.
Exercise: change the tabu tenure from 7 to 2 and to 30 and explain the effect.
"""
import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

from common import bip_instances, note, run, table


def penalised(f, A, ub, weight=50.0):
    def score(c):
        return float(f @ c + weight * np.maximum(A @ c - ub, 0).sum())   # infeasibility costs extra
    return score


def hill_climb(score, c):
    best = score(c)
    while True:
        moves = []
        for j in range(len(c)):
            c[j] = 1 - c[j]
            moves.append((score(c), j))
            c[j] = 1 - c[j]
        value, j = min(moves)
        if value >= best - 1e-12:
            return c, best
        c[j] = 1 - c[j]
        best = value


def tabu(score, c, iters=600, tenure=7):
    best_c, best = c.copy(), score(c)
    current, banned = best, {}
    for it in range(iters):
        moves = []
        for j in range(len(c)):
            c[j] = 1 - c[j]
            s = score(c)
            c[j] = 1 - c[j]
            if banned.get(j, -1) < it or s < best - 1e-12:            # aspiration: a new best overrides tabu
                moves.append((s, j))
        current, j = min(moves)
        c[j] = 1 - c[j]
        banned[j] = it + tenure
        if current < best - 1e-12:
            best, best_c = current, c.copy()
    return best_c, best


def main():
    ns = bip_instances()
    rows = []
    for seed in range(4):
        f, A, ub, _ = ns['instance'](60, np.random.default_rng(100 + seed))
        ub = ub.copy()
        ub[:3] *= 0.5                                  # a resource-starved cluster: 30 % budgets, not 60 %
        opt = milp(f, constraints=LinearConstraint(A, -np.inf, ub), integrality=np.ones(60), bounds=Bounds(0, 1)).fun
        score = penalised(f, A, ub)
        rng = np.random.default_rng(seed)
        ok = lambda c: '' if np.all(A @ c <= ub + 1e-9) else ' (infeasible)'
        gap = lambda v: f'{max(0.0, 100 * (v - opt) / abs(opt)):+.2f} %'
        c1, one = hill_climb(score, rng.integers(0, 2, 60).astype(float))
        c_r, restarts = min((hill_climb(score, rng.integers(0, 2, 60).astype(float)) for _ in range(20)), key=lambda t: t[1])
        c_t, t = tabu(score, rng.integers(0, 2, 60).astype(float))
        rows.append((seed, f'{opt:.2f}', gap(one) + ok(c1), gap(restarts) + ok(c_r), gap(t) + ok(c_t)))
    table(['instance', 'optimum (HiGHS)', 'one hill climb', '20 restarts', 'tabu search'], rows)
    note('Hill climbing flips the single best module until no flip helps: a local optimum, often far from')
    note('the best. Restarting from random plans samples many basins. Tabu search keeps moving - taking the')
    note('best allowed flip even when it is worse - while a short memory forbids undoing recent flips, so')
    note('it walks out of basins instead of cycling. Constraints are handled by a penalty for violations.')


if __name__ == '__main__':
    run(main, __doc__)
