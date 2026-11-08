#!/usr/bin/env python3
"""ML 03 - Logistic regression from scratch: is this minute of telemetry an anomaly?

ATLAS link: the paper's anomaly data (data.zip: anomaly_data.csv, 9,500 normal and 500 anomalous
minutes). A probability of "something is wrong" is what the coupling optimiser needs as a risk input.
Applies to: churn, fraud, click-through, diagnosis - any yes/no with a probability attached.
Exercise: add an L2 penalty to the gradient and watch the weights on correlated features shrink.
"""
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

from common import BASIC, FEATURES, load_anomaly, note, run, show, split, standardise, table


def sigmoid(z):
    return 1 / (1 + np.exp(-np.clip(z, -30, 30)))


def main():
    X, y, _ = load_anomaly()
    X = np.log1p(np.abs(X))                                  # heavy tails: work on a log scale
    tr, te = split(len(y), seed=3)
    full = LogisticRegression(max_iter=2000).fit(X[tr], y[tr])
    show('all 8 metrics: test ROC-AUC', f'{roc_auc_score(y[te], full.predict_proba(X[te])[:, 1]):.4f} '
         '(latency and errors give it away)')
    X = X[:, BASIC]
    print('  from here on: only what a basic host monitor sees (requests/s, CPU %, memory %)')
    Xtr, Xte = standardise(X[tr], X[te])
    Xtr, Xte = np.c_[np.ones(len(tr)), Xtr], np.c_[np.ones(len(te)), Xte]

    w = np.zeros(Xtr.shape[1])
    for epoch in range(500):                                 # batch gradient descent on the log-loss
        p = sigmoid(Xtr @ w)
        w -= 0.5 * Xtr.T @ (p - y[tr]) / len(tr)
        if epoch in (0, 9, 99, 499):
            loss = -np.mean(y[tr] * np.log(p + 1e-12) + (1 - y[tr]) * np.log(1 - p + 1e-12))
            show(f'epoch {epoch + 1:>3} log-loss', f'{loss:.4f}')
    p_te = sigmoid(Xte @ w)
    sk = LogisticRegression(max_iter=2000).fit(Xtr[:, 1:], y[tr])
    show('test ROC-AUC: ours / scikit-learn', f'{roc_auc_score(y[te], p_te):.4f} / '
         f'{roc_auc_score(y[te], sk.predict_proba(Xte[:, 1:])[:, 1]):.4f}')
    print('  weights (standardised log features, + means "more anomalous"):')
    table(['feature', 'weight'], [(f, f'{v:+.2f}') for f, v in sorted(zip([FEATURES[i] for i in BASIC], w[1:]), key=lambda t: -abs(t[1]))])
    rows = []
    for t in (0.02, 0.05, 0.1, 0.2, 0.5):
        pred = p_te >= t
        tp, fp = int((pred & (y[te] == 1)).sum()), int((pred & (y[te] == 0)).sum())
        fn = int((~pred & (y[te] == 1)).sum())
        rows.append((t, tp, fp, fn, f'{tp / max(tp + fp, 1):.2f}', f'{tp / max(tp + fn, 1):.2f}'))
    table(['threshold', 'caught', 'false alarms', 'missed', 'precision', 'recall'], rows)
    note('The model outputs a probability; the threshold is a business decision. A low threshold catches')
    note('more incidents but pages engineers for false alarms; a high one is quiet but misses incidents.')
    note('Gradient descent on the log-loss is convex, so ours and scikit-learn land on the same answer.')
    note('With 3 metrics a straight boundary is weak (AUC ~0.8): ML 07 shows what non-linear models add.')


if __name__ == '__main__':
    run(main, __doc__)
