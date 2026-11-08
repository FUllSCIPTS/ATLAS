#!/usr/bin/env python3
"""OPT 12 - Bin packing: placing service pods on 8-core nodes (first-fit decreasing vs exact MILP).

ATLAS link: when ATLAS extracts modules (Sim.bip), each becomes pods of 1, 2 or 4 cores (the paper's
vertical sizes) plus a 0.1-core Envoy sidecar (Params.sidecar_cores) and a 1-core datastore share per
service (Params.svc_fixed_cores). Those pods must be packed onto nodes; every extra node costs money.
Applies to: VM and container scheduling, truck loading, cutting stock, memory allocation, ad slots.
Exercise: add a second resource (memory) - now it is vector bin packing and FFD needs a new sort key.
"""
import math

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

from common import note, run, show, table


def pods(rng, services=6):
    items = []
    for _ in range(services):
        size = rng.choice([1.0, 2.0, 4.0], p=[0.5, 0.3, 0.2])
        items += [size + 0.1] * int(rng.integers(2, 6))             # replicas, each with its sidecar
        items.append(1.0)                                           # the service's datastore share
    return np.array(items)


def first_fit(items, cap, decreasing=False):
    bins = []
    for x in (sorted(items, reverse=True) if decreasing else items):
        for b in bins:
            if sum(b) + x <= cap + 1e-9:
                b.append(x)
                break
        else:
            bins.append([x])
    return bins


def next_fit(items, cap):
    bins = [[]]
    for x in items:
        if sum(bins[-1]) + x > cap + 1e-9:
            bins.append([])
        bins[-1].append(x)
    return bins


def exact(items, cap):
    n = len(items)
    m = len(first_fit(items, cap, True))                            # never need more bins than FFD
    # variables: x[i, b] (item i in bin b), then y[b] (bin b used)
    c = np.r_[np.zeros(n * m), np.ones(m)]
    A, lo, hi = [], [], []
    for i in range(n):                                               # each item in exactly one bin
        row = np.zeros(n * m + m); row[i * m:(i + 1) * m] = 1
        A.append(row); lo.append(1); hi.append(1)
    for b in range(m):                                               # capacity, only if the bin is used
        row = np.zeros(n * m + m); row[b:n * m:m] = items; row[n * m + b] = -cap
        A.append(row); lo.append(-np.inf); hi.append(0)
    for b in range(m - 1):                                           # symmetry breaking: use bins in order
        row = np.zeros(n * m + m); row[n * m + b] = -1; row[n * m + b + 1] = 1
        A.append(row); lo.append(-np.inf); hi.append(0)
    res = milp(c, constraints=LinearConstraint(np.array(A), lo, hi), integrality=np.ones(n * m + m),
               bounds=Bounds(0, 1), options={'time_limit': 20})
    return int(round(res.fun))


def main():
    cap = 8.0
    rng = np.random.default_rng(12)
    rows = []
    for trial in range(5):
        items = pods(rng)
        lower = math.ceil(items.sum() / cap - 1e-9)
        rows.append((len(items), f'{items.sum():.1f}', lower, len(next_fit(items, cap)), len(first_fit(items, cap)),
                     len(first_fit(items, cap, True)), exact(items, cap)))
    table(['pods', 'cores', 'lower bound', 'next fit', 'first fit', 'first fit decreasing', 'exact (MILP)'], rows)
    show('FFD guarantee', 'at most 11/9 OPT + 6/9 nodes (Dosa 2007)')
    note('Bin packing is NP-hard, yet first-fit decreasing - place the biggest pods first, each into the')
    note('first node with room - is usually optimal or one node off. The volume lower bound ceil(sum/cap)')
    note('tells you when a heuristic is provably optimal without solving the MILP.')


if __name__ == '__main__':
    run(main, __doc__)
