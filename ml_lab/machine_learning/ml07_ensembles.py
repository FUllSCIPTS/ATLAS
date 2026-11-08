#!/usr/bin/env python3
"""ML 07 - Ensembles: bagging, random forests and gradient boosting versus one tree and a line.

ATLAS link: the same anomaly question as ML 03, from the basic host monitor (requests/s, CPU, memory),
where a straight boundary scores only ~0.8. Many weak trees together find the curved boundary.
Applies to: tabular data in general - forests and boosting win most tabular benchmarks and competitions.
Exercise: plot test AUC against the number of boosting rounds and find where it stops improving.
"""
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.tree import DecisionTreeClassifier

from common import BASIC, FEATURES, load_anomaly, note, run, show, split, table


def main():
    X, y, _ = load_anomaly()
    X = np.log1p(np.abs(X[:, BASIC]))
    tr, te = split(len(y), seed=7)
    models = {
        'logistic regression (linear)': LogisticRegression(max_iter=2000),
        'one tree, depth 6': DecisionTreeClassifier(max_depth=6, random_state=0),
        'one tree, unlimited depth': DecisionTreeClassifier(random_state=0),
        'random forest, 200 trees': RandomForestClassifier(200, min_samples_leaf=3, random_state=0, n_jobs=-1),
        'gradient boosting, 200 rounds': GradientBoostingClassifier(n_estimators=200, max_depth=3, random_state=0),
    }
    rows = []
    for name, model in models.items():
        model.fit(X[tr], y[tr])
        rows.append((name, f'{roc_auc_score(y[tr], model.predict_proba(X[tr])[:, 1]):.3f}',
                     f'{roc_auc_score(y[te], model.predict_proba(X[te])[:, 1]):.3f}'))
    table(['model', 'train AUC', 'test AUC'], rows)

    rng = np.random.default_rng(0)                      # bagging by hand: bootstrap, fit, average
    votes = np.zeros(len(te))
    for b in range(50):
        boot = rng.choice(tr, len(tr))
        votes += DecisionTreeClassifier(random_state=b).fit(X[boot], y[boot]).predict_proba(X[te])[:, 1]
    show('our bagging: 50 bootstrapped full trees', f'test AUC {roc_auc_score(y[te], votes / 50):.3f}')
    rf = models['random forest, 200 trees']
    show('forest feature importance', ', '.join(f'{FEATURES[i]} {v:.2f}' for i, v in zip(BASIC, rf.feature_importances_)))
    note('One deep tree memorises (train AUC 1.0) and generalises worse. Averaging many trees trained on')
    note('bootstrap samples cancels their independent errors (bagging); random forests also decorrelate')
    note('trees by sampling features. Boosting instead adds small trees that each fix the last one\'s errors.')


if __name__ == '__main__':
    run(main, __doc__)
