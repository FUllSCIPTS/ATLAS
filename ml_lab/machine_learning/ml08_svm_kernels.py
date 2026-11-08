#!/usr/bin/env python3
"""ML 08 - Support vector machines: maximum margins and the kernel trick.

ATLAS link: separating healthy minutes from incidents on two metrics a dashboard plots, CPU % and
memory %. Healthy minutes form a curved band (both rise with load), which a straight line cannot wrap.
Applies to: text classification, bioinformatics, any small-to-medium data set with a clear margin.
Exercise: vary C (how much the margin may be violated) and gamma (how local the RBF kernel is).
"""
import numpy as np
from sklearn.metrics import roc_auc_score
from sklearn.svm import SVC

from common import load_anomaly, note, run, show, split, standardise, table


def main():
    X, y, _ = load_anomaly()
    rng = np.random.default_rng(8)
    keep = np.r_[rng.choice(np.flatnonzero(y == 0), 1500, replace=False), np.flatnonzero(y == 1)]
    X, y = np.log1p(X[keep][:, [1, 2]]), y[keep]             # CPU %, memory %
    tr, te = split(len(y), seed=8)
    Xtr, Xte = standardise(X[tr], X[te])
    rows = []
    for name, model in (('linear kernel', SVC(kernel='linear', C=1)),
                        ('polynomial kernel, degree 3', SVC(kernel='poly', degree=3, C=1)),
                        ('RBF kernel, gamma 0.5', SVC(kernel='rbf', gamma=0.5, C=1)),
                        ('RBF kernel, gamma 5', SVC(kernel='rbf', gamma=5, C=1)),
                        ('RBF kernel, gamma 200', SVC(kernel='rbf', gamma=200, C=1))):
        model.fit(Xtr, y[tr])
        s_tr, s_te = model.decision_function(Xtr), model.decision_function(Xte)
        rows.append((name, len(model.support_), f'{roc_auc_score(y[tr], s_tr):.3f}', f'{roc_auc_score(y[te], s_te):.3f}'))
    table(['model', 'support vectors', 'train AUC', 'test AUC'], rows)
    a, b = Xtr[0], Xtr[1]
    phi = lambda v: np.array([v[0] ** 2, np.sqrt(2) * v[0] * v[1], v[1] ** 2])   # explicit degree-2 features
    show('kernel trick check: (a.b)^2 vs phi(a).phi(b)', f'{(a @ b) ** 2:.6f} vs {phi(a) @ phi(b):.6f}')
    note('An SVM keeps only the boundary cases (support vectors) and maximises the gap around them.')
    note('A kernel computes inner products in a richer feature space without building it, so a "linear"')
    note('method draws curved boundaries. Too large a gamma makes every point its own island: overfitting.')


if __name__ == '__main__':
    run(main, __doc__)
