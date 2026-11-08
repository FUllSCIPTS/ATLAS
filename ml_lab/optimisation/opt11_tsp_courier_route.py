#!/usr/bin/env python3
"""OPT 11 - The travelling salesman: a courier's multi-drop route, exact (Held-Karp) and heuristic.

ATLAS link: an ATLAS Go courier collecting from the built-in kitchens and dropping orders around Cork
(points from atlas_go/geo.py). Visiting n stops in the shortest loop has (n-1)!/2 candidate tours.
Held-Karp dynamic programming solves 12 stops exactly; nearest-neighbour and 2-opt scale to hundreds.
Applies to: delivery and service routing, PCB drilling, DNA sequencing, telescope scheduling.
Exercise: add time windows (food must arrive within 20 minutes of pickup) - now it is a VRPTW.
"""
import itertools
import math
import time

from common import cork_points, distance_matrix, note, run, show, table, tour_length


def held_karp(D):
    """Exact TSP by DP over subsets: best[S][j] = shortest path from 0 through set S ending at j."""
    n = len(D)
    best = {(1 << j, j): (D[0, j], 0) for j in range(1, n)}
    for size in range(2, n):
        for subset in itertools.combinations(range(1, n), size):
            bits = sum(1 << j for j in subset)
            for j in subset:
                prev = bits & ~(1 << j)
                best[(bits, j)] = min((best[(prev, k)][0] + D[k, j], k) for k in subset if k != j)
    full = (1 << n) - 2
    length, last = min((best[(full, j)][0] + D[j, 0], j) for j in range(1, n))
    tour, bits = [0], full
    while last:
        tour.append(last)
        bits, last = bits & ~(1 << last), best[(bits, last)][1]
    return length, tour


def nearest_neighbour(D, start=0):
    tour, left = [start], set(range(len(D))) - {start}
    while left:
        nxt = min(left, key=lambda j: D[tour[-1], j])
        tour.append(nxt)
        left.remove(nxt)
    return tour


def two_opt(tour, D):
    improved = True
    while improved:
        improved = False
        for i in range(1, len(tour) - 1):
            for j in range(i + 1, len(tour)):
                a, b, c, d = tour[i - 1], tour[i], tour[j], tour[(j + 1) % len(tour)]
                if D[a, c] + D[b, d] < D[a, b] + D[c, d] - 1e-12:          # reverse the segment i..j
                    tour[i:j + 1] = tour[i:j + 1][::-1]
                    improved = True
    return tour


def main():
    D = distance_matrix(cork_points(12, seed=11))
    t0 = time.perf_counter()
    exact, exact_tour = held_karp(D)
    t_hk = time.perf_counter() - t0
    nn = nearest_neighbour(D)
    show('12 stops: candidate tours', f'{math.factorial(11) // 2:,}')
    show('Held-Karp exact', f'{exact:.2f} km in {t_hk:.2f} s, tour {exact_tour}')
    show('nearest neighbour', f'{tour_length(nn, D):.2f} km (+{100 * (tour_length(nn, D) / exact - 1):.1f} %)')
    show('nearest neighbour + 2-opt', f'{tour_length(two_opt(nn, D), D):.2f} km')
    rows = []
    for n in (30, 80, 200):
        D = distance_matrix(cork_points(n, seed=n))
        nn = nearest_neighbour(D)
        t0 = time.perf_counter()
        opt = two_opt(list(nn), D)
        rows.append((n, f'{tour_length(nn, D):.1f}', f'{tour_length(opt, D):.1f}',
                     f'{100 * (1 - tour_length(opt, D) / tour_length(nn, D)):.1f} %', f'{time.perf_counter() - t0:.2f} s'))
    table(['stops', 'nearest neighbour km', 'after 2-opt km', 'saved', '2-opt time'], rows)
    note('Held-Karp is exact in O(n^2 2^n): fine for a dozen stops, impossible for a city. Nearest neighbour')
    note('is fast but strands far stops at the end; 2-opt removes crossings by reversing segments until no')
    note('swap helps - a local optimum, usually within a few per cent of the best. OPT 16 escapes it.')


if __name__ == '__main__':
    run(main, __doc__)
