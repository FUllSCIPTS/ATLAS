#!/usr/bin/env python3
"""OPT 09 - Shortest paths on a Cork road graph: Dijkstra, A* with a haversine heuristic, Bellman-Ford.

ATLAS link: ATLAS Go moves cars in straight lines (atlas_go/geo.py has no routing engine). A real
dispatcher needs road distances. We build a small graph over Cork's landmarks and driver zones (each
point joined to its nearest neighbours, edges 30 % longer than the crow flies) and route on it.
Applies to: navigation, network packet routing, game AI, project scheduling (longest path), currency
arbitrage detection (Bellman-Ford finds negative cycles).
Exercise: close one edge (a road works) and measure how many shortest paths change.
"""
import heapq

import numpy as np

from common import cork_points, distance_matrix, km, note, run, show, table


def build_graph(pts, k=4):
    from scipy.sparse.csgraph import minimum_spanning_tree
    D = distance_matrix(pts)
    G = {i: {} for i in range(len(pts))}
    for i in range(len(pts)):
        for j in np.argsort(D[i])[1:k + 1]:                   # each junction joins its k nearest
            G[i][int(j)] = G[int(j)][i] = 1.3 * D[i, j]       # roads wind: 30 % detour factor
    mst = minimum_spanning_tree(D).tocoo()                    # plus a spanning tree: everything is reachable
    for i, j in zip(mst.row, mst.col):
        G[int(i)][int(j)] = G[int(j)][int(i)] = 1.3 * D[i, j]
    return G


def dijkstra(G, s, t, h=lambda v: 0.0):
    """A* search; with h = 0 it is Dijkstra. Returns (distance, path, nodes expanded)."""
    dist, prev, seen = {s: 0.0}, {}, set()
    heap = [(h(s), s)]
    while heap:
        _, u = heapq.heappop(heap)
        if u in seen:
            continue
        seen.add(u)
        if u == t:
            break
        for v, w in G[u].items():
            if dist[u] + w < dist.get(v, np.inf):
                dist[v], prev[v] = dist[u] + w, u
                heapq.heappush(heap, (dist[v] + h(v), v))
    path, v = [t], t
    while v != s:
        v = prev[v]
        path.append(v)
    return dist[t], path[::-1], len(seen)


def bellman_ford(G, s):
    dist = {v: np.inf for v in G}
    dist[s] = 0.0
    for _ in range(len(G) - 1):
        changed = False
        for u in G:
            for v, w in G[u].items():
                if dist[u] + w < dist[v]:
                    dist[v], changed = dist[u] + w, True
        if not changed:
            break
    return dist


def main():
    pts = cork_points(120, seed=9)
    G = build_graph(pts)
    show('graph', f'{len(G)} junctions, {sum(len(e) for e in G.values()) // 2} road segments')
    rows = []
    rng = np.random.default_rng(9)
    for _ in range(6):
        s, t = (int(v) for v in rng.choice(len(pts), 2, replace=False))
        d1, path, n1 = dijkstra(G, s, t)
        d2, _, n2 = dijkstra(G, s, t, h=lambda v: km(pts[v], pts[t]))          # admissible: never overestimates
        d3 = bellman_ford(G, s)[t]
        rows.append((f'{s} -> {t}', f'{km(pts[s], pts[t]):.2f}', f'{d1:.2f}', f'{d2:.2f}', f'{d3:.2f}',
                     len(path) - 1, n1, n2))
    table(['trip', 'crow km', 'Dijkstra km', 'A* km', 'Bellman-Ford km', 'segments', 'Dijkstra expanded', 'A* expanded'], rows)
    note('Dijkstra settles junctions in order of distance from the start, so it explores in a circle. A*')
    note('adds an optimistic estimate of the remaining distance (straight-line haversine never exceeds the')
    note('road distance), which steers the search toward the goal yet keeps the answer optimal. Bellman-Ford')
    note('is slower but also handles negative edge weights.')


if __name__ == '__main__':
    run(main, __doc__)
