#!/usr/bin/env python3
"""OPT 07 - Dynamic programming: whole cores for six services, and the 0/1 knapsack.

ATLAS link: OPT 04 split 16 cores continuously; real pods get whole cores. Allocating integer cores
to the paper's six services is a resource-allocation DP: best(i, k) = min over c of
latency_i(c) + best(i + 1, k - c). Then a 0/1 knapsack (which optional nightly jobs fit the spare
cores?) shows where greedy shortcuts fail and DP does not.
Applies to: budgeting, cutting stock, sequence alignment, speech recognition (Viterbi), inventory.
Exercise: add a per-service minimum of 2 replicas (the paper's min_rep) and rerun the DP.
"""
from functools import lru_cache

import numpy as np

from common import note, run, show, table


def main():
    from atlas_sim.traffic import DEMAND_MS, SERVICES, VISIT
    lam, total = 2000.0, 16
    rate, mu = lam * VISIT, 1000.0 / DEMAND_MS

    def cost(i, c):                                  # visit-weighted M/M/1 time of service i on c cores (ms)
        spare = c * mu[i] - rate[i]
        return 1000 * VISIT[i] / spare if spare > 0 else float('inf')

    @lru_cache(None)
    def best(i, k):
        if i == len(SERVICES):
            return (0.0, ()) if k == 0 else (float('inf'), ())
        options = []
        for c in range(0, k + 1):
            rest = best(i + 1, k - c)
            options.append((cost(i, c) + rest[0], (c,) + rest[1]))
        return min(options)

    dp_cost, dp_alloc = best(0, total)
    alloc = np.array([int(np.floor(rate[i] / mu[i])) + 1 for i in range(6)])     # greedy: start just feasible
    while alloc.sum() < total:                                                   # add a core where it helps most
        gains = [cost(i, alloc[i]) - cost(i, alloc[i] + 1) for i in range(6)]
        alloc[int(np.argmax(gains))] += 1
    greedy_cost = sum(cost(i, c) for i, c in enumerate(alloc))
    table(['service', 'DP cores', 'greedy cores'], [(s, d, g) for s, d, g in zip(SERVICES, dp_alloc, alloc)])
    show('mean latency: DP / greedy marginal', f'{dp_cost:.3f} ms / {greedy_cost:.3f} ms')
    show('continuous optimum (OPT 04)', '4.30 ms - the price of whole cores is the gap')
    note('Greedy marginal allocation is optimal here because each cost is convex in its cores.')

    jobs = {'report export': (6, 60), 'index rebuild': (5, 45), 'model retrain': (5, 45),
            'cache warm-up': (2, 9), 'backup verify': (1, 5)}
    names = list(jobs)
    cap = 10                                                                    # spare cores tonight
    w = [jobs[n][0] for n in names]
    v = [jobs[n][1] for n in names]
    table_dp = [[0] * (cap + 1) for _ in range(len(names) + 1)]
    for i in range(1, len(names) + 1):
        for k in range(cap + 1):
            table_dp[i][k] = table_dp[i - 1][k]
            if w[i - 1] <= k:
                table_dp[i][k] = max(table_dp[i][k], table_dp[i - 1][k - w[i - 1]] + v[i - 1])
    chosen, k = [], cap
    for i in range(len(names), 0, -1):                                          # trace back the decisions
        if table_dp[i][k] != table_dp[i - 1][k]:
            chosen.append(names[i - 1])
            k -= w[i - 1]
    greedy, room = [], cap
    for n in sorted(names, key=lambda n: -jobs[n][1] / jobs[n][0]):             # best value per core first
        if jobs[n][0] <= room:
            greedy.append(n)
            room -= jobs[n][0]
    print('\n  0/1 knapsack: optional nightly jobs (cores, value) into 10 spare cores')
    show('DP (exact)', f'value {table_dp[-1][cap]}: {", ".join(sorted(chosen))}')
    show('greedy by value per core', f'value {sum(jobs[n][1] for n in greedy)}: {", ".join(sorted(greedy))}')
    note('Dynamic programming solves each sub-problem once and reuses it: O(items x capacity) instead of')
    note('2^items subsets. Greedy works for convex, divisible problems and fails for 0/1 choices, where a')
    note('job that does not quite fit can make the whole plan worse.')


if __name__ == '__main__':
    run(main, __doc__)
