#!/usr/bin/env python3
"""OPT 17 - A genetic algorithm for the coupling decision: selection, crossover, mutation, elitism.

ATLAS link: the paper's optimiser (atlas_sim/cluster.py, Sim.bip) scores all 2^6 = 64 couplings and
takes the best. A genetic algorithm treats each coupling as a chromosome of six genes (0 = inside the
monolith, 1 = extracted) and evolves a population using only the objective - no gradients, no LP.
Part 1 checks it against Sim.bip on the real objective; part 2 runs it on a 60-module BIP from
run_bip_timing.py, where enumeration is impossible, against HiGHS.
Applies to: design optimisation, scheduling, neural architecture search, game strategies, antenna design.
Exercise: replace uniform crossover with one-point crossover and compare convergence.
"""
import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

from common import bip_instances, coupling_objective, note, run, show, table


def evolve(fitness, n, rng, pop=40, generations=80, p_mut=None, elite=2):
    p_mut = p_mut or 1.0 / n
    P = rng.integers(0, 2, (pop, n))
    evaluations, curve = 0, []
    for g in range(generations):
        f = fitness(P)
        evaluations += len(P)
        order = np.argsort(f)
        curve.append(float(f[order[0]]))
        children = [P[i].copy() for i in order[:elite]]                         # elitism: keep the best
        while len(children) < pop:
            a, b = (min(rng.choice(pop, 3, replace=False), key=lambda i: f[i]) for _ in range(2))   # tournaments
            mask = rng.random(n) < 0.5                                          # uniform crossover
            child = np.where(mask, P[a], P[b])
            flip = rng.random(n) < p_mut                                        # mutation
            children.append(np.where(flip, 1 - child, child))
        P = np.array(children)
    f = fitness(P)
    return P[int(np.argmin(f))], float(f.min()), evaluations + len(P), curve


def main():
    rows = []
    for lam in (1000, 2500, 4000, 6000, 9000):
        sim, f = coupling_objective(lam)

        def fitness(P):
            J, ok, *_ = f(P)
            return np.where(ok, J, J + 10.0)                                     # penalise infeasible couplings
        best, value, evals, _ = evolve(fitness, 6, np.random.default_rng(lam), pop=12, generations=10)
        exact = sim.bip(0, lam, 0.0)
        gap = 100 * (value - fitness(exact[None])[0]) / abs(fitness(exact[None])[0])
        rows.append((lam, ''.join(map(str, best)), ''.join(map(str, exact)), f'{gap:+.2f} %', evals))
    table(['load (req/s)', 'GA coupling', 'Sim.bip (all 64)', 'GA objective gap', 'GA evaluations'], rows)

    ns = bip_instances()
    f, A, ub, _ = ns['instance'](60, np.random.default_rng(170))
    ub = ub.copy()
    ub[:3] *= 0.5                                                                # binding budgets, as in OPT 15
    opt = milp(f, constraints=LinearConstraint(A, -np.inf, ub), integrality=np.ones(60), bounds=Bounds(0, 1)).fun

    def penalised(P):
        return P @ f + 50.0 * np.maximum(P @ A.T - ub, 0).sum(1)
    best, value, evals, curve = evolve(penalised, 60, np.random.default_rng(1), pop=80, generations=300)
    show('60 modules: HiGHS optimum', f'{opt:.2f}')
    show('GA best (80 x 300)', f'{value:.2f} ({100 * (value - opt) / abs(opt):+.2f} %), feasible: '
         f'{bool(np.all(A @ best <= ub + 1e-9))}, {evals:,} evaluations of 2^60 = 1.2e18 plans')
    show('best value by generation', '  '.join(f'g{g}: {curve[g]:.0f}' for g in (0, 10, 50, 100, 299)))
    note('Selection keeps good couplings, crossover mixes their genes, mutation keeps exploring, elitism')
    note('never loses the best. With 6 modules the paper is right to enumerate: 64 evaluations, exact, while')
    note('the GA spends 132 and can stop at a near-tie. With 60 modules enumeration is impossible and the GA')
    note('reaches the optimum after 24,080 evaluations. It needs only a score - useful when the objective')
    note('is a simulator, not a formula.')


if __name__ == '__main__':
    run(main, __doc__)
