#!/usr/bin/env python3
"""ML 04 - k-nearest neighbours and why feature scaling matters: naming the kind of incident.

ATLAS link: the 500 anomalous minutes in data.zip come in five kinds (CPU exhaustion, memory/queue
exhaustion, downstream failure, request flood, network/disk delay). Knowing which one tells the
operator what to fix. kNN classifies a new minute by the incidents it most resembles.
Applies to: recommendation ("people like you"), case-based reasoning, simple baselines for anything.
Exercise: weight neighbours by 1/distance and compare.
"""
import numpy as np
from sklearn.metrics import accuracy_score
from sklearn.neighbors import KNeighborsClassifier

from common import CATEGORIES, FEATURES, load_anomaly, note, run, show, split, standardise, table


def knn_predict(Xtr, ytr, Xq, k):
    d = ((Xq[:, None, :] - Xtr[None, :, :]) ** 2).sum(-1)       # all pairwise squared distances
    nearest = np.argsort(d, 1)[:, :k]
    votes = ytr[nearest]
    return np.array([np.bincount(v, minlength=6).argmax() for v in votes])


def main():
    X, y, cat = load_anomaly()
    A, c = X[y == 1], cat[y == 1]
    tr, te = split(len(c), seed=4)
    show('ranges of the raw features', ', '.join(f'{f} {A[:, i].min():.3g}-{A[:, i].max():.3g}'
                                                for i, f in enumerate(FEATURES[:4])) + ' ...')
    raw = knn_predict(A[tr], c[tr], A[te], 5)
    Str, Ste = standardise(A[tr], A[te])
    scaled = knn_predict(Str, c[tr], Ste, 5)
    show('5-NN accuracy, raw units', f'{accuracy_score(c[te], raw):.3f}  (rps and latency dominate distance)')
    show('5-NN accuracy, standardised', f'{accuracy_score(c[te], scaled):.3f}')
    rows = []
    for k in (1, 3, 5, 15, 51, 151):
        acc = accuracy_score(c[te], KNeighborsClassifier(k).fit(Str, c[tr]).predict(Ste))
        rows.append((k, f'{acc:.3f}'))
    table(['k', 'accuracy'], rows)
    conf = np.zeros((6, 6), int)
    for t, p in zip(c[te], scaled):
        conf[t, p] += 1
    print('  confusion (rows = true kind, columns = predicted), standardised 5-NN:')
    for i in range(1, 6):
        print(f'  {CATEGORIES[i]:<26}' + ''.join(f'{conf[i, j]:>5}' for j in range(1, 6)))
    note('kNN has no training step: it memorises. Distance is only meaningful when features share a scale;')
    note('in raw units requests/s (hundreds to thousands) swamps error rate (thousandths). Small k is noisy,')
    note('very large k drifts toward the majority kind - the bias-variance trade-off again (ML 02).')


if __name__ == '__main__':
    run(main, __doc__)
