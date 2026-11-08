#!/usr/bin/env python3
"""OPT 04 - Constrained continuous optimisation: sharing 16 cores among six services (KKT and SLSQP).

ATLAS link: the paper's six modules (atlas_sim/traffic.py: SERVICES, VISIT ratios, DEMAND in core-ms
per visit) and its 16-core budget. Treat each service as an M/M/1 queue whose speed grows with its
cores; how should the cores be split to minimise the mean response time? Lagrange multipliers give a
closed form (Kleinrock's square-root rule); a general solver (SLSQP) confirms it.
Applies to: budget allocation, portfolio weights, power/bandwidth allocation, chemical equilibria.
Exercise: add a minimum of 1 core per service and observe which KKT multipliers become active.
"""
import numpy as np
from scipy.optimize import minimize

from common import note, run, show, table


def main():
    from atlas_sim.traffic import DEMAND_MS, SERVICES, VISIT
    lam, total = 2000.0, 16.0                       # requests/s, cores
    rate = lam * VISIT                              # visits/s per service
    mu = 1000.0 / DEMAND_MS                         # visits/s one core can serve
    need = rate / mu                                # cores just to keep up (utilisation 1)

    def latency(c):                                 # mean ms per request: sum of visit-weighted M/M/1 times
        spare = c * mu - rate
        return np.inf if (spare <= 0).any() else 1000 * float((VISIT / spare).sum())

    spare_budget = total - need.sum()
    x = np.sqrt(VISIT * mu)                         # KKT: spare capacity x_i proportional to sqrt(v_i mu_i)
    x *= spare_budget / (x / mu).sum()
    c_kkt = (x + rate) / mu
    res = minimize(latency, np.full(6, total / 6) + 0.5 * need, method='SLSQP',
                   constraints=[{'type': 'eq', 'fun': lambda c: c.sum() - total}],
                   bounds=[(n + 1e-3, total) for n in need])
    proportional = need / need.sum() * total
    equal = np.full(6, total / 6)
    rows = [(s, f'{n:.2f}', f'{e:.2f}', f'{p:.2f}', f'{k:.2f}', f'{q:.2f}')
            for s, n, e, p, k, q in zip(SERVICES, need, equal, proportional, c_kkt, res.x)]
    table(['service', 'cores to keep up', 'equal split', 'proportional', 'KKT closed form', 'SLSQP'], rows)
    for name, c in (('equal split', equal), ('proportional to load', proportional),
                    ('KKT square-root rule', c_kkt), ('SLSQP (numerical)', res.x)):
        show(name, f'mean latency {latency(c):.2f} ms' if np.isfinite(latency(c)) else 'a service is overloaded: infinite queue')
    nu = (VISIT * mu / x ** 2)[0] * 1000
    show('Lagrange multiplier nu', f'{nu:.3f} ms saved per extra core (the "shadow price" of the budget)')
    show('check: one more core, re-optimised', f'{latency(c_kkt) - latency_with(total + 1, rate, mu, VISIT):.3f} ms saved '
         '(less: the multiplier is a derivative, returns diminish)')
    note('At the optimum every service has the same marginal benefit per core (the Lagrange condition).')
    note('Splitting equally overloads the Catalogue (it needs 4 cores). Splitting in proportion to load')
    note('over-serves the heaviest service. The square-root rule gives each service what it needs to keep up')
    note('plus spare in proportion to sqrt(visits x speed) - and a general solver lands on the same answer.')


def latency_with(total, rate, mu, visit):
    need = rate / mu
    x = np.sqrt(visit * mu)
    x *= (total - need.sum()) / (x / mu).sum()
    return 1000 * float((visit / x).sum())


if __name__ == '__main__':
    run(main, __doc__)
