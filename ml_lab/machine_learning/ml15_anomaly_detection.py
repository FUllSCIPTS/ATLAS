#!/usr/bin/env python3
"""ML 15 - Unsupervised anomaly detection: z-scores, Mahalanobis, Isolation Forest and LOF.

ATLAS link: the paper's coupling optimiser takes an Isolation-Forest anomaly score as an input (high
score -> isolate the module). All four detectors here learn "normal" only, then score data.zip, so we
can see which incident kinds each one catches.
Applies to: fraud, intrusion detection, predictive maintenance, quality control.
Exercise: contaminate the training set with 2 % anomalies and see which detector degrades most.
"""
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.neighbors import LocalOutlierFactor

from common import BASIC, CATEGORIES, load_anomaly, note, run, split, standardise, table


def main():
    X, y, cat = load_anomaly()
    L = np.log1p(np.abs(X[:, BASIC + [5]]))                    # basic monitor + queue depth
    normal_idx = np.flatnonzero(y == 0)
    train, _ = split(len(normal_idx), test=0.5, seed=15)
    train = normal_idx[train]                                     # half of the normal minutes, no anomalies
    test = np.setdiff1d(np.arange(len(y)), train)
    Ztr, Zte = standardise(L[train], L[test])

    cov_inv = np.linalg.inv(np.cov(Ztr.T))
    scores = {
        'max |z-score|': np.abs(Zte).max(1),
        'Mahalanobis distance': np.einsum('ij,jk,ik->i', Zte, cov_inv, Zte),
        'Isolation Forest': -IsolationForest(n_estimators=200, random_state=0).fit(Ztr).score_samples(Zte),
        'Local Outlier Factor': -LocalOutlierFactor(20, novelty=True).fit(Ztr).score_samples(Zte),
    }
    yt, ct = y[test], cat[test]
    rows = []
    for name, s in scores.items():
        thr = np.quantile(s[yt == 0], 0.99)                       # alarm budget: 1 % of normal minutes
        per_kind = [f'{(s[ct == k] > thr).mean():.2f}' for k in range(1, 6)]
        rows.append((name, f'{roc_auc_score(yt, s):.3f}', f'{average_precision_score(yt, s):.3f}', *per_kind))
    short = [c.split('_')[0][:8] for c in CATEGORIES[1:]]
    table(['detector', 'ROC-AUC', 'PR-AUC', *short], rows)
    print('  (last five columns: share of each incident kind caught at a 1 % false-alarm budget)')
    note('Seen through four metrics, z-scores catch only incidents extreme in one metric; Mahalanobis')
    note('and LOF also catch "normal values in an abnormal combination". Isolation Forest, the paper\'s')
    note('detector on the full eight metrics, does worst here: no method wins everywhere, and the features')
    note('you give a detector matter more than its name. Fix the alarm budget, then compare recall per kind.')

if __name__ == '__main__':
    run(main, __doc__)
