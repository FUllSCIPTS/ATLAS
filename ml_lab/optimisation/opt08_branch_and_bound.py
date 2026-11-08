#!/usr/bin/env python3
"""OPT 08 - Integer programming by branch-and-bound, written by hand, on the paper's coupling BIP.

ATLAS link: run_bip_timing.py generates linearised coupling BIPs (which of n modules to extract, under
latency, cost, replica and availability budgets) and solves them by enumeration, HiGHS branch-and-bound
and LP relaxation + rounding. Here branch-and-bound is spelled out: solve the LP relaxation, branch on
a fractional module, prune any branch whose LP bound cannot beat the best plan found so far.
Applies to: scheduling, facility location, crew rostering, chip design - any yes/no decision model.
Exercise: branch on the most fractional variable instead of the first, and count nodes again.
"""
import time

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, linprog, milp

from common import bip_instances, note, run, show, table


def branch_and_bound(f, A, ub):
    n = len(f)
    best = {'value': np.inf, 'x': None, 'nodes': 0, 'pruned': 0}

    def node(lo, hi):
        best['nodes'] += 1
        res = linprog(f, A_ub=A, b_ub=ub, bounds=list(zip(lo, hi)), method='highs')
        if res.status != 0:
            return                                              # infeasible branch
        if res.fun >= best['value'] - 1e-9:
            best['pruned'] += 1
            return                                              # bound: cannot beat the incumbent
        frac = np.flatnonzero(np.abs(res.x - np.round(res.x)) > 1e-6)
        if len(frac) == 0:
            best['value'], best['x'] = res.fun, np.round(res.x)  # new incumbent
            return
        j = frac[0]
        for value in ((1, 0) if res.x[j] >= 0.5 else (0, 1)):  # explore the nearer side first
            lo2, hi2 = lo.copy(), hi.copy()
            lo2[j] = hi2[j] = value
            node(lo2, hi2)

    node(np.zeros(n), np.ones(n))
    return best


def main():
    ns = bip_instances()
    rows = []
    for n in (8, 14, 20, 30, 50, 80):
        f, A, ub, risk = ns['instance'](n, np.random.default_rng(n))
        t0 = time.perf_counter()
        bb = branch_and_bound(f, A, ub)
        t_bb = time.perf_counter() - t0
        t0 = time.perf_counter()
        ref = milp(f, constraints=LinearConstraint(A, -np.inf, ub), integrality=np.ones(n), bounds=Bounds(0, 1))
        t_milp = time.perf_counter() - t0
        lp = linprog(f, A_ub=A, b_ub=ub, bounds=[(0, 1)] * n, method='highs')
        enum = '-'
        if n <= 20:
            M = ((np.arange(2 ** n)[:, None] >> np.arange(n)[None, :]) & 1).astype(float)
            enum = f'{np.min(np.where(np.all(M @ A.T <= ub + 1e-9, 1), M @ f, np.inf)):.3f}'
        rows.append((n, f'{2 ** n:.1e}', bb['nodes'], bb['pruned'], f'{bb["value"]:.3f}', f'{ref.fun:.3f}', enum,
                     f'{lp.fun:.3f}', f'{t_bb * 1000:.0f} / {t_milp * 1000:.0f}'))
    table(['n', 'plans 2^n', 'B&B nodes', 'pruned', 'ours', 'HiGHS', 'enumerate', 'LP bound', 'ms ours/HiGHS'], rows)
    show('meaning of the LP bound', 'relaxing 0/1 to [0,1] can only help, so it bounds the best integer plan')
    note('Branch-and-bound explores a tree of partial decisions but visits only a sliver of the 2^n plans:')
    note('every LP relaxation gives an optimistic bound, and any branch whose bound is worse than the best')
    note('complete plan so far is cut off. When the LP optimum is already 0/1 (n = 30, 50 here) one node')
    note('suffices. HiGHS adds presolve, cutting planes and heuristics on top, which is why it is faster.')


if __name__ == '__main__':
    run(main, __doc__)
