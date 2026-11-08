#!/usr/bin/env python3
"""OPT 20 - Multi-objective optimisation: the latency-cost Pareto front of ATLAS's coupling choices.

ATLAS link: Sim.bip folds latency, cost and crash risk into one number J with fixed weights
(alpha, beta, gamma in atlas_sim/cluster.py Params). Before choosing weights, an engineer should see the
whole trade-off: which couplings are Pareto-optimal (no other is better on both latency and cores)?
Weighted sums can only reach the convex part of that front; the epsilon-constraint method reaches all.
Applies to: engineering design (weight vs strength), portfolios (risk vs return), ML (accuracy vs size),
public policy - wherever goals conflict.
Exercise: add availability as a third objective and count how many couplings become Pareto-optimal.
"""
import numpy as np

from common import coupling_objective, note, run, show, table


def pareto_ranks(points):
    """Non-dominated sorting (as in NSGA-II): rank 1 = Pareto front, rank 2 = front once rank 1 is removed..."""
    rank = np.zeros(len(points), int)
    remaining, r = set(range(len(points))), 1
    while remaining:
        front = {i for i in remaining if not any((points[j] <= points[i]).all() and (points[j] < points[i]).any()
                                                for j in remaining if j != i)}
        for i in front:
            rank[i] = r
        remaining -= front
        r += 1
    return rank


def main():
    lam = 6000
    sim, f = coupling_objective(lam)
    CM = sim.CM
    J, ok, L, C, A = f(CM)
    idx = np.flatnonzero(ok)
    pts = np.c_[L[idx], C[idx]]
    rank = pareto_ranks(pts)
    front = idx[rank == 1]
    order = front[np.argsort(L[front])]
    chosen = sim.bip(0, lam, 0.0)
    k_chosen = int(np.flatnonzero((CM == chosen).all(1))[0])
    rows = [(''.join(map(str, CM[k])), f'{L[k]:.1f}', f'{C[k]:.1f}', f'{A[k]:.5f}', '<- Sim.bip' if k == k_chosen else '')
            for k in order]
    show(f'feasible couplings at {lam} req/s', f'{len(idx)} of 64; Pareto front: {len(front)}; '
         f'fronts in total: {rank.max()}')
    table(['coupling', 'latency ms', 'cores', 'availability', ''], rows)

    hit = set()
    for w in np.linspace(0, 1, 201):                                    # weighted sum, normalised objectives
        s = w * pts[:, 0] / pts[:, 0].max() + (1 - w) * pts[:, 1] / pts[:, 1].max()
        hit.add(int(idx[np.argmin(s)]))
    eps_hit = set()
    for eps in np.unique(L[front]):                                      # min cores s.t. latency <= eps
        feas = idx[L[idx] <= eps + 1e-9]
        eps_hit.add(int(feas[np.argmin(C[feas])]))
    show('front points found by weighted sums', f'{len(hit & set(front.tolist()))} of {len(front)} (201 weight settings)')
    show('found by epsilon-constraint', f'{len(eps_hit & set(front.tolist()))} of {len(front)}')
    show('Sim.bip choice is Pareto-optimal', bool(rank[np.flatnonzero(idx == k_chosen)[0]] == 1) if k_chosen in idx else False)
    note('A plan is Pareto-optimal when nothing beats it on every objective; the front is the menu of')
    note('honest trade-offs. A weighted sum of objectives can only land on the convex hull of that menu,')
    note('so some fair compromises are unreachable by any weights. Fixing a latency budget and minimising')
    note('cost (epsilon-constraint) reaches every point. ATLAS\'s weights pick one point on the front.')


if __name__ == '__main__':
    run(main, __doc__)
