#!/usr/bin/env python3
"""OPT 10 - The assignment problem: matching drivers to riders, greedy versus the Hungarian method.

ATLAS link: ATLAS Go dispatches one ride at a time to the best-scoring driver (intelligence.rank). When
several requests arrive together, matching them jointly is an assignment problem: minimise total pickup
time over one-to-one pairings. scipy's linear_sum_assignment solves it exactly in polynomial time.
Applies to: task allocation, organ exchange, school admissions, object tracking between video frames.
Exercise: maximise the sum of ATLAS Go dispatch scores instead of minimising minutes.
"""
import itertools

import numpy as np
from scipy.optimize import linear_sum_assignment

from common import cork_points, km, note, run, show, table


def main():
    rng = np.random.default_rng(10)
    rows = []
    for size in (5, 8, 25, 100):
        gaps = []
        for trial in range(20):
            drivers = cork_points(size, seed=1000 + trial)
            riders = cork_points(size, seed=2000 + trial)
            rng.shuffle(riders)
            C = np.array([[km(d, r) / 25 * 60 for r in riders] for d in drivers])     # minutes at 25 km/h
            ri, ci = linear_sum_assignment(C)
            opt = C[ri, ci].sum()
            free, greedy = set(range(size)), 0.0
            for i in range(size):                                                  # requests in arrival order
                j = min(free, key=lambda j: C[j, i])                               # nearest free driver
                greedy += C[j, i]
                free.remove(j)
            gaps.append(100 * (greedy / opt - 1))
            if size == 8 and trial == 0:
                brute = min(sum(C[i, p[i]] for i in range(size)) for p in itertools.permutations(range(size)))
                show('8 x 8 check: Hungarian vs all 40,320 pairings', f'{opt:.2f} vs {brute:.2f} minutes')
        rows.append((size, f'{np.mean(gaps):.1f} %', f'{np.max(gaps):.1f} %'))
    table(['requests at once', 'greedy extra time (mean)', 'worst of 20'], rows)
    note('Greedy gives each request the nearest free driver, so early requests can take a driver a later')
    note('request needed badly. The Hungarian algorithm (O(n^3)) finds the global optimum; checking 8! = 40,320')
    note('pairings agrees, but brute force is hopeless beyond a dozen. Batching requests for a few seconds')
    note('and assigning them jointly is how ride-hailing platforms cut pickup times.')


if __name__ == '__main__':
    run(main, __doc__)
