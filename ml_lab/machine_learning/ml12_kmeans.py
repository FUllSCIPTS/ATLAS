#!/usr/bin/env python3
"""ML 12 - k-means clustering from scratch: discovering operating regimes without labels.

ATLAS link: the eight-day per-minute telemetry in data.zip (traffic_trace_excerpt.csv). Without any
labels, k-means groups minutes into regimes (night, daytime, peak) that an autoscaler could treat
differently.
Applies to: customer segmentation, image compression, document grouping, vector quantisation.
Exercise: run k-means++ initialisation by hand and count how often plain random starts get stuck.
"""
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from common import load_trace, note, run, show, standardise, table


def kmeans(X, k, seed, iters=100):
    rng = np.random.default_rng(seed)
    C = X[rng.choice(len(X), k, replace=False)]
    for _ in range(iters):
        label = ((X[:, None] - C[None]) ** 2).sum(-1).argmin(1)          # assign to the nearest centre
        new = np.array([X[label == j].mean(0) if (label == j).any() else C[j] for j in range(k)])
        if np.allclose(new, C):
            break
        C = new                                                          # move centres to the means
    inertia = ((X - C[label]) ** 2).sum()
    return label, C, inertia


def main():
    T = load_trace()
    cols = ['rps', 'cpu_pct', 'latency_ms', 'queue_depth']
    raw = np.c_[[T[c] for c in cols]].T
    (X,) = standardise(raw)
    rows = []
    for k in range(2, 8):
        best = min((kmeans(X, k, s) for s in range(5)), key=lambda t: t[2])
        sample = np.random.default_rng(0).choice(len(X), 2000, replace=False)
        rows.append((k, f'{best[2]:.0f}', f'{silhouette_score(X[sample], best[0][sample]):.3f}'))
    print('  choosing k: inertia always falls; silhouette (-1..1) peaks at a good k')
    table(['k', 'inertia', 'silhouette'], rows)
    label, C, inertia = min((kmeans(X, 3, s) for s in range(5)), key=lambda t: t[2])
    sk = KMeans(3, n_init=5, random_state=0).fit(X)
    show('our inertia vs scikit-learn (k=3)', f'{inertia:.0f} vs {sk.inertia_:.0f}')
    hour = (T['minute'] // 60) % 24
    centres = C * raw.std(0) + raw.mean(0)
    rows = []
    for j in np.argsort(centres[:, 0]):
        h = hour[label == j]
        rows.append((j, int((label == j).sum()), *[f'{v:.0f}' for v in centres[j]], f'{np.median(h):.0f}:00'))
    table(['cluster', 'minutes', *cols, 'typical hour'], rows)
    note('No one told k-means about day and night: the regimes fall out of the data. Inertia always drops')
    note('as k grows, so pick k with a criterion (silhouette, elbow) and a use for the clusters. Standardise')
    note('first - k-means uses Euclidean distance (see ML 04).')


if __name__ == '__main__':
    run(main, __doc__)
