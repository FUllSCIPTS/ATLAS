#!/usr/bin/env python3
"""OPT 16 - Simulated annealing: escaping 2-opt's local optimum on an 80-stop courier route.

ATLAS link: the Cork courier tour of OPT 11 at city scale (80 drops around ATLAS Go's landmarks). 2-opt
stops when no single segment reversal helps. Annealing also accepts worse moves with probability
exp(-increase / T) and cools T slowly, so early on it roams and later it settles - like metal annealing.
Applies to: chip placement, timetabling, protein folding, any large combinatorial search.
Exercise: cool ten times faster and watch annealing fall back to plain local search.
"""
import math

import numpy as np

from common import cork_points, distance_matrix, note, run, show, table, tour_length
from opt11_tsp_courier_route import nearest_neighbour, two_opt


def anneal(tour, D, rng, t0=0.3, t_end=0.002, steps=200000):
    alpha = (t_end / t0) ** (1 / steps)                               # geometric cooling from t0 to t_end
    tour = list(tour)
    length = tour_length(tour, D)
    best, best_len, T = list(tour), length, t0
    n = len(tour)
    history = []
    for k in range(steps):
        i, j = sorted(rng.integers(1, n, 2))
        if i == j:
            continue
        a, b, c, d = tour[i - 1], tour[i], tour[j], tour[(j + 1) % n]
        delta = D[a, c] + D[b, d] - D[a, b] - D[c, d]                  # change if segment i..j is reversed
        if delta < 0 or rng.random() < math.exp(-delta / T):
            tour[i:j + 1] = tour[i:j + 1][::-1]
            length += delta
            if length < best_len - 1e-12:
                best, best_len = list(tour), length
        T *= alpha
        if k % 40000 == 0:
            history.append((k, f'{T:.4f}', f'{length:.2f}', f'{best_len:.2f}'))
    return best, best_len, history


def main():
    D = distance_matrix(cork_points(80, seed=16))
    nn = nearest_neighbour(D)
    local = two_opt(list(nn), D)
    rng = np.random.default_rng(16)
    best, best_len, history = anneal(nn, D, rng)
    polished = tour_length(two_opt(best, D), D)
    print('  annealing from the nearest-neighbour tour:')
    table(['step', 'temperature', 'current km', 'best km'], history)
    show('nearest neighbour', f'{tour_length(nn, D):.2f} km')
    show('2-opt local optimum', f'{tour_length(local, D):.2f} km')
    show('simulated annealing (+ final 2-opt)', f'{polished:.2f} km')
    restarts = min(tour_length(two_opt(list(rng.permutation(80)), D), D) for _ in range(10))
    show('2-opt from 10 random starts (best)', f'{restarts:.2f} km')
    note('At high temperature almost any reversal is accepted, so the tour is shuffled freely; as T falls')
    note('only small uphill moves survive, and at the end annealing behaves like 2-opt. The slow cooling')
    note('is what lets it cross the ridges between local optima. It needs tuning (T0, cooling rate, steps).')


if __name__ == '__main__':
    run(main, __doc__)
