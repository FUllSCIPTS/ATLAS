#!/usr/bin/env python3
"""OPT 14 - Dynamic programming over time: a replica schedule with switching costs (myopic vs optimal).

ATLAS link: the paper's coupling objective has a switching penalty (Params.switch_pen) because changing
the deployment costs start-up time and risk; the autoscaler must cover forecast demand. Choosing the
number of replicas hour by hour to minimise running cost + under-provisioning penalty + switching
cost is a shortest path through (hour, replicas) states - solved exactly by DP (Bellman recursion).
Applies to: unit commitment in power grids, inventory and production planning, fleet sizing.
Exercise: make demand uncertain (two scenarios per hour) and solve the stochastic DP.
"""
import numpy as np

from common import note, run, show, table


def main():
    from atlas_sim.traffic import DEMAND_MS, VISIT, ecommerce_trace
    r, _, _ = ecommerce_trace(days=3, seed=14, n_events=1)
    hourly = r[1440:2880].reshape(24, 60).max(1)                        # peak req/s in each hour
    per_replica = 1000 / (VISIT[1] * DEMAND_MS[1]) * 0.7             # Catalogue: req/s per 1-core pod at 70 %
    need = np.ceil(hourly / per_replica).astype(int)
    R = np.arange(1, need.max() + 4)                                  # replica choices
    run_cost, short_cost, switch_cost = 1.0, 25.0, 6.0               # per replica-hour; per missing replica; per change

    def stage(h, k):
        return run_cost * k + short_cost * max(0, need[h] - k)

    INF = float('inf')
    V = np.full((24, len(R)), INF)
    arg = np.zeros((24, len(R)), int)
    V[0] = [stage(0, k) for k in R]
    for h in range(1, 24):                                           # V[h][k] = stage + min_j V[h-1][j] + switch
        for b, k in enumerate(R):
            prev = V[h - 1] + switch_cost * (np.abs(R - k) > 0)
            arg[h, b] = int(np.argmin(prev))
            V[h, b] = stage(h, k) + prev[arg[h, b]]
    b = int(np.argmin(V[-1]))
    plan = [0] * 24
    for h in range(23, -1, -1):
        plan[h] = int(R[b])
        b = arg[h, b]

    def total(schedule):
        cost = sum(stage(h, k) for h, k in enumerate(schedule))
        return cost + switch_cost * sum(1 for a, c in zip(schedule, schedule[1:]) if a != c)

    reactive = list(need)                                            # follow demand exactly (HPA-like)
    static = [int(need.max())] * 24                                  # provision for the peak all day
    rows = [(f'{h:02d}:00', f'{hourly[h]:.0f}', need[h], reactive[h], plan[h]) for h in range(24) if h % 3 == 0 or plan[h] != reactive[h]]
    table(['hour', 'peak req/s', 'replicas needed', 'reactive', 'DP optimal'], rows)
    for name, s in (('static peak provisioning', static), ('reactive (follow demand)', reactive), ('DP optimal', plan)):
        changes = sum(1 for a, c in zip(s, s[1:]) if a != c)
        show(name, f'cost {total(s):.0f}  ({sum(s)} replica-hours, {changes} changes)')
    note('Each hour\'s best choice depends on the next hours, so a myopic rule cannot be optimal when changes')
    note('cost something. Bellman\'s principle - an optimal plan\'s tail is optimal from where it starts - lets')
    note('DP solve 24 x states sub-problems instead of enumerating every schedule. The paper\'s switch_pen')
    note('plays the same role: it damps flapping between couplings.')


if __name__ == '__main__':
    run(main, __doc__)
