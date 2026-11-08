#!/usr/bin/env python3
"""OPT 18 - Continuous black-box optimisation: (1+1)-ES, differential evolution and particle swarms.

ATLAS link: ATLAS Go dispatches the driver with the highest score w . features (atlas_go/intelligence.py)
and learned w by REINFORCE (learned.RIDE_WEIGHTS). Judged by the app's own cost model
(intelligence.expected_cost) the picked driver changes in jumps as w moves, so the objective has no
useful gradient. Population methods tune w directly; Rastrigin, a classic multi-modal test function,
shows how they cope with many local minima.
Applies to: engineering design, controller and hyperparameter tuning, calibration of simulators.
Exercise: give every method the same budget of 300 evaluations and see which degrades most.
"""
import random

import numpy as np
from scipy.optimize import differential_evolution

from common import note, rastrigin, run, table
from atlas_go import learned as L
from atlas_go.intelligence import _candidates, expected_cost


def dispatch_objective(seed=7, situations=400):
    rng = random.Random(seed)
    F, C = [], []
    for _ in range(situations):
        cs = _candidates(rng)
        F.append([c.features() for c in cs])
        C.append([expected_cost(c) for c in cs])
    F, C = np.array(F), np.array(C)

    def cost(w):                                       # mean expected wait of the driver each w would pick
        pick = np.argmax(F @ np.asarray(w), 1)
        return float(C[np.arange(len(C)), pick].mean())
    return cost, F, C


def one_plus_one_es(f, x, sigma, budget, rng):
    fx, success = f(x), []
    for _ in range(budget - 1):
        y = x + sigma * rng.normal(size=len(x))
        fy = f(y)
        success.append(fy <= fx)
        if fy <= fx:
            x, fx = y, fy
        if len(success) == 10:                          # Rechenberg's 1/5 success rule
            sigma *= 1.22 if sum(success) > 2 else 0.82
            success = []
    return fx, x


def de(f, lo, hi, budget, rng, pop=20, F=0.7, CR=0.9):
    d = len(lo)
    P = rng.uniform(lo, hi, (pop, d))
    fit = np.array([f(p) for p in P])
    used = pop
    while used < budget:
        for i in range(pop):
            a, b, c = P[rng.choice([j for j in range(pop) if j != i], 3, replace=False)]
            trial = np.where(rng.random(d) < CR, np.clip(a + F * (b - c), lo, hi), P[i])   # mutate + crossover
            ft = f(trial)
            used += 1
            if ft <= fit[i]:
                P[i], fit[i] = trial, ft
            if used >= budget:
                break
    return fit.min(), P[int(np.argmin(fit))]


def pso(f, lo, hi, budget, rng, n=20, w=0.7, c1=1.5, c2=1.5):
    d = len(lo)
    X = rng.uniform(lo, hi, (n, d))
    V = np.zeros((n, d))
    pbest, pval = X.copy(), np.array([f(x) for x in X])
    g = pbest[np.argmin(pval)].copy()
    used = n
    while used + n <= budget:
        r1, r2 = rng.random((n, d)), rng.random((n, d))
        V = w * V + c1 * r1 * (pbest - X) + c2 * r2 * (g - X)    # inertia + own memory + swarm's best
        X = np.clip(X + V, lo, hi)
        vals = np.array([f(x) for x in X])
        used += n
        better = vals < pval
        pbest[better], pval[better] = X[better], vals[better]
        g = pbest[np.argmin(pval)].copy()
    return pval.min(), g


def main():
    cost, F, C = dispatch_objective()
    lo, hi = np.zeros(4), np.full(4, 10.0)
    budget = 1500
    rng = np.random.default_rng(18)
    samples = rng.uniform(lo, hi, (budget, 4))
    rs = min(samples, key=cost)
    sp = differential_evolution(cost, list(zip(lo, hi)), maxiter=15, popsize=20, seed=18, polish=False)
    found = {
        'random search': (cost(rs), rs),
        '(1+1)-ES, 1/5 rule': one_plus_one_es(cost, np.full(4, 5.0), 2.0, budget, rng),
        'differential evolution (ours)': de(cost, lo, hi, budget, rng),
        'particle swarm (ours)': pso(cost, lo, hi, budget, rng),
        'scipy differential_evolution': (sp.fun, sp.x),
    }
    fresh, F2, C2 = dispatch_objective(seed=70007, situations=4000)    # new situations: no tuning on these
    rows = [('nearest driver (ETA only)', f'{C[np.arange(len(C)), np.argmax(F[:, :, 0], 1)].mean():.3f}',
             f'{C2[np.arange(len(C2)), np.argmax(F2[:, :, 0], 1)].mean():.3f}'),
            (f'ATLAS Go weights {L.POLICY_VERSION} (REINFORCE)', f'{cost(L.RIDE_WEIGHTS):.3f}', f'{fresh(L.RIDE_WEIGHTS):.3f}')]
    rows += [(k, f'{v:.3f}', f'{fresh(w):.3f}') for k, (v, w) in found.items()]
    rows.append(('oracle (cheapest driver each time)', f'{C.min(1).mean():.3f}', f'{C2.min(1).mean():.3f}'))
    print(f'  {budget} evaluations each; mean expected wait-cost in minutes (lower is better)')
    table(['dispatch weights found by', 'on the 400 tuning situations', 'on 4,000 fresh situations'], rows)
    rows = []
    for name, fn in (('random search', None), ('(1+1)-ES', one_plus_one_es), ('DE (ours)', de), ('PSO (ours)', pso)):
        vals = []
        for s in range(5):
            r = np.random.default_rng(s)
            lo10, hi10 = np.full(10, -5.12), np.full(10, 5.12)
            if fn is None:
                vals.append(rastrigin(r.uniform(lo10, hi10, (20000, 10))).min())
            elif fn is one_plus_one_es:
                vals.append(fn(rastrigin, r.uniform(lo10, hi10), 1.0, 20000, r)[0])
            else:
                vals.append(fn(rastrigin, lo10, hi10, 20000, r)[0])
        rows.append((name, f'{np.mean(vals):.2f}', f'{np.min(vals):.2f}'))
    print('\n  Rastrigin in 10 dimensions (global minimum 0; about 10^10 local minima), 20,000 evaluations:')
    table(['method', 'mean of 5 runs', 'best'], rows)
    note('No gradient is needed: each method only asks "how good is this w?". The (1+1)-ES adapts its step')
    note('size by the 1/5 success rule; DE builds steps from differences between population members, so it')
    note('scales itself to the landscape; PSO moves particles toward their own and the swarm\'s best. On the')
    note('dispatch problem all of them edge past the REINFORCE weights on the situations they were tuned on,')
    note('and a smaller gain survives on fresh situations - always check that column (tuning on a sample can')
    note('overfit it). On Rastrigin the population methods escape local minima that trap a single point.')


if __name__ == '__main__':
    run(main, __doc__)
