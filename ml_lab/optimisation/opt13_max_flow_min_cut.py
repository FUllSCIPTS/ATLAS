#!/usr/bin/env python3
"""OPT 13 - Network flows: maximum flow and minimum cut (Edmonds-Karp), and bipartite matching.

ATLAS link: two ATLAS questions are flow problems. (1) How many drivers per hour can move from the
city centre to the airport for an evening of arrivals, given corridor capacities between Cork zones
(names from atlas_go/geo.py; capacities illustrative)? (2) How many waiting riders can be served at once
when each driver may only take riders within 2 minutes? Max-flow answers both; the min cut names the
bottleneck.
Applies to: telecom and power networks, evacuation planning, image segmentation, baseball elimination.
Exercise: add a second source (Kent Station) with a super-source node feeding both.
"""
from collections import deque

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import maximum_flow

from common import cork_points, km, note, run, show, table

ROADS = [   # (from, to, drivers per hour)
    ('City Centre', 'South Mall', 120), ('City Centre', 'Grand Parade', 90), ('City Centre', 'Western Road', 60),
    ('South Mall', 'Douglas', 70), ('Grand Parade', 'Douglas', 40), ('Grand Parade', 'Frankfield', 50),
    ('Western Road', 'Frankfield', 30), ('Douglas', 'Ballygarvan', 45), ('Douglas', 'Airport rank', 35),
    ('Frankfield', 'Airport rank', 55), ('Ballygarvan', 'Airport rank', 40),
]


def edmonds_karp(nodes, edges, s, t):
    idx = {v: i for i, v in enumerate(nodes)}
    n = len(nodes)
    cap = np.zeros((n, n))
    for u, v, c in edges:
        cap[idx[u], idx[v]] += c
    flow, augmentations = 0.0, 0
    while True:
        parent = [-1] * n
        parent[idx[s]] = idx[s]
        q = deque([idx[s]])
        while q and parent[idx[t]] == -1:                    # BFS for the shortest augmenting path
            u = q.popleft()
            for v in range(n):
                if parent[v] == -1 and cap[u, v] > 1e-9:
                    parent[v] = u
                    q.append(v)
        if parent[idx[t]] == -1:
            break
        v, push = idx[t], np.inf
        while v != idx[s]:
            push = min(push, cap[parent[v], v])
            v = parent[v]
        v = idx[t]
        while v != idx[s]:                                   # push flow, open the reverse (residual) edge
            cap[parent[v], v] -= push
            cap[v, parent[v]] += push
            v = parent[v]
        flow += push
        augmentations += 1
    reachable = {nodes[i] for i in range(n) if parent[i] != -1}
    return flow, augmentations, reachable


def main():
    nodes = sorted({u for u, _, _ in ROADS} | {v for _, v, _ in ROADS})
    flow, aug, side = edmonds_karp(nodes, ROADS, 'City Centre', 'Airport rank')
    cut = [(u, v, c) for u, v, c in ROADS if u in side and v not in side]
    show('max drivers/hour City Centre -> Airport', f'{flow:.0f} ({aug} augmenting paths)')
    table(['bottleneck road (min cut)', 'capacity'], [(f'{u} -> {v}', c) for u, v, c in cut])
    show('capacity of the cut', f'{sum(c for *_, c in cut)} = max flow (max-flow min-cut theorem)')
    idx = {v: i for i, v in enumerate(nodes)}
    M = np.zeros((len(nodes), len(nodes)), dtype=np.int32)
    for u, v, c in ROADS:
        M[idx[u], idx[v]] = c
    show('scipy.sparse.csgraph.maximum_flow', maximum_flow(csr_matrix(M), idx['City Centre'], idx['Airport rank']).flow_value)

    drivers, riders = cork_points(30, seed=131), cork_points(30, seed=132)
    edges = [('S', f'd{i}', 1) for i in range(30)] + [(f'r{j}', 'T', 1) for j in range(30)]
    edges += [(f'd{i}', f'r{j}', 1) for i, d in enumerate(drivers) for j, r in enumerate(riders) if km(d, r) / 25 * 60 <= 2]
    nodes = ['S', 'T'] + [f'd{i}' for i in range(30)] + [f'r{j}' for j in range(30)]
    matched, _, _ = edmonds_karp(nodes, edges, 'S', 'T')
    show('30 drivers, 30 riders, 2-minute limit', f'{matched:.0f} riders can be served at once '
         f'({len(edges) - 60} feasible driver-rider pairs)')
    note('Max-flow keeps finding a path with spare capacity and pushes flow along it, allowing flow to be')
    note('"undone" through reverse edges. When no path remains, the reachable junctions define the minimum')
    note('cut: widening any other road adds nothing. Unit capacities turn it into maximum matching.')


if __name__ == '__main__':
    run(main, __doc__)
