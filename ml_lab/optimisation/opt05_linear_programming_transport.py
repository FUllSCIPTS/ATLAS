#!/usr/bin/env python3
"""OPT 05 - Linear programming: repositioning idle drivers across Cork (a transportation problem).

ATLAS link: ATLAS Go's driver zones and saved pickup places (android-app/atlas_go/geo.py). Before an
evening surge, idle drivers in eight zones must cover the expected demand at the four places with the
least total driving. Every quantity is linear, so it is a linear program: solved here by HiGHS
(scipy.optimize.linprog) and checked against a greedy "nearest place first" plan.
Applies to: logistics, supply chains, production planning, diet and blending problems, network flow.
Exercise: add a capacity limit per road corridor and see which constraints become binding.
"""
import numpy as np
from scipy.optimize import linprog

from common import km, note, run, show, table
from atlas_go.geo import PLACE_COORDS, ZONE_COORDS


def problem():
    zones = ['Mardyke', 'Douglas', 'Blackpool', 'Ballygarvan', 'Montenotte', 'Western Road', 'Frankfield', 'South Mall']
    supply = np.array([6, 9, 5, 4, 6, 5, 4, 7])                   # idle drivers per zone
    demand = np.array([10, 16, 9, 7])                             # expected requests per place (sum 42 <= 46)
    D = np.array([[km(ZONE_COORDS[z], p) for p in PLACE_COORDS] for z in zones])
    return zones, supply, demand, D


def solve(supply, demand, D):
    m, n = D.shape
    A_ub = np.zeros((m, m * n))                                  # each zone sends at most its drivers
    for i in range(m):
        A_ub[i, i * n:(i + 1) * n] = 1
    A_eq = np.zeros((n, m * n))                                  # each place gets exactly its demand
    for j in range(n):
        A_eq[j, j::n] = 1
    return linprog(D.ravel(), A_ub=A_ub, b_ub=supply, A_eq=A_eq, b_eq=demand, bounds=(0, None), method='highs')


def main():
    zones, supply, demand, D = problem()
    res = solve(supply, demand, D)
    X = res.x.reshape(D.shape)
    rows = [(z, s, *[f'{v:.0f}' if v > 1e-9 else '.' for v in X[i]]) for i, (z, s) in enumerate(zip(zones, supply))]
    table(['zone', 'idle', 'UCC', 'City Centre', 'Kent Stn', 'Airport'], rows)
    show('LP optimum: total driving', f'{res.fun:.2f} km for {demand.sum()} drivers')
    show('solution is integral without asking', bool(np.allclose(X, np.round(X))))
    left = supply.astype(float).copy()
    need = demand.astype(float).copy()
    greedy = 0.0
    for i, j in sorted(np.ndindex(D.shape), key=lambda ij: D[ij]):       # cheapest pairs first
        k = min(left[i], need[j])
        greedy += k * D[i, j]
        left[i] -= k
        need[j] -= k
    show('greedy "shortest pairs first"', f'{greedy:.2f} km  (+{100 * (greedy / res.fun - 1):.1f} %)')
    show('variables / constraints', f'{D.size} / {len(zones) + len(PLACE_COORDS)}; HiGHS iterations {res.nit}')
    note('A linear program\'s optimum sits at a corner of the feasible polytope; the simplex method walks')
    note('corners, interior-point methods cut through the middle. Transportation problems have totally')
    note('unimodular constraints, so the LP corner is already whole drivers - no integer solver needed.')
    note('Greedy grabs the cheapest pairs first and pays for it at the end.')


if __name__ == '__main__':
    run(main, __doc__)
