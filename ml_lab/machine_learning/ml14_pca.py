#!/usr/bin/env python3
"""ML 14 - Principal component analysis: eight correlated metrics, a few real directions.

ATLAS link: the eight telemetry fields in data.zip mostly move together with load (CPU, memory,
latency, network all rise with requests/s). PCA finds the few directions that carry the variance,
and the part PCA cannot rebuild is a natural anomaly score.
Applies to: compression, visualisation, denoising, face recognition, gene expression, finance factors.
Exercise: whiten the components and feed them to ML 04's kNN.
"""
import numpy as np
from sklearn.decomposition import PCA
from sklearn.metrics import roc_auc_score

from common import FEATURES, load_anomaly, note, run, show, standardise, table


def main():
    X, y, _ = load_anomaly()
    L = np.log1p(np.abs(X))
    normal = L[y == 0]
    Z, Zall = standardise(normal, L)
    U, S, Vt = np.linalg.svd(Z - Z.mean(0), full_matrices=False)      # PCA by hand = SVD of centred data
    var = S ** 2 / (S ** 2).sum()
    table(['component', 'variance share', 'cumulative'], [(i + 1, f'{v:.3f}', f'{c:.3f}')
                                                        for i, (v, c) in enumerate(zip(var, np.cumsum(var)))])
    sk = PCA().fit(Z)
    show('same as scikit-learn', np.allclose(var, sk.explained_variance_ratio_))
    print('  loadings of the first component (what "PC1" means):')
    table(['feature', 'weight'], [(f, f'{w:+.2f}') for f, w in sorted(zip(FEATURES, Vt[0]), key=lambda t: -abs(t[1]))[:5]])
    for k in (1, 2, 3, 5):
        V = Vt[:k].T
        rebuilt = (Zall - Z.mean(0)) @ V @ V.T + Z.mean(0)
        err = ((Zall - rebuilt) ** 2).sum(1)                           # what k components cannot explain
        show(f'reconstruction error with {k} components', f'anomaly ROC-AUC {roc_auc_score(y, err):.3f}')
    note('PC1 is "load": the load metrics share one sign (which sign is arbitrary). Normal minutes live near a')
    note('low-dimensional surface; an incident breaks the usual relationships (high latency at low load)')
    note('and lands far from it. Fit PCA on normal data only, or the anomalies shape the components.')


if __name__ == '__main__':
    run(main, __doc__)
