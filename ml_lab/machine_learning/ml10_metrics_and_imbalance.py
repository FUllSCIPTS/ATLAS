#!/usr/bin/env python3
"""ML 10 - Evaluation under class imbalance: accuracy lies; precision, recall, PR-AUC and calibration.

ATLAS link: only 5 % of minutes in data.zip are anomalous, and in production far fewer. A detector
that always answers "normal" is 95 % accurate and useless.
Applies to: fraud, defects, disease, intrusion - every rare-event problem.
Exercise: rebalance by undersampling the normal minutes and compare with class weights.
"""
import numpy as np
from sklearn.calibration import calibration_curve
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (accuracy_score, average_precision_score, brier_score_loss, confusion_matrix,
                             f1_score, precision_score, recall_score, roc_auc_score)

from common import BASIC, load_anomaly, note, run, split, table


def main():
    X, y, _ = load_anomaly()
    X = np.log1p(np.abs(X[:, BASIC]))
    tr, te = split(len(y), seed=10)
    rf = RandomForestClassifier(300, min_samples_leaf=5, random_state=0, n_jobs=-1).fit(X[tr], y[tr])
    p = rf.predict_proba(X[te])[:, 1]
    rows = []
    for name, pred, score in (('always "normal"', np.zeros(len(te), int), np.zeros(len(te))),
                              ('forest, threshold 0.5', (p >= 0.5).astype(int), p),
                              ('forest, threshold 0.15', (p >= 0.15).astype(int), p)):
        rows.append((name, f'{accuracy_score(y[te], pred):.3f}', f'{precision_score(y[te], pred, zero_division=0):.2f}',
                     f'{recall_score(y[te], pred):.2f}', f'{f1_score(y[te], pred):.2f}',
                     f'{roc_auc_score(y[te], score) if score.any() else 0.5:.3f}',
                     f'{average_precision_score(y[te], score) if score.any() else y[te].mean():.3f}'))
    table(['detector', 'accuracy', 'precision', 'recall', 'F1', 'ROC-AUC', 'PR-AUC'], rows)
    tn, fp, fn, tp = confusion_matrix(y[te], (p >= 0.15).astype(int)).ravel()
    print(f'  confusion at 0.15: {tp} caught, {fn} missed, {fp} false alarms, {tn} correct all-clears')
    frac, mean = calibration_curve(y[te], p, n_bins=5, strategy='quantile')
    print('  calibration (when the model says p, how often is it really an anomaly?):')
    table(['mean predicted p', 'observed rate'], [(f'{m:.3f}', f'{f:.3f}') for m, f in zip(mean, frac)])
    print(f'  Brier score {brier_score_loss(y[te], p):.4f} (lower is better; always-0.05 scores '
          f'{brier_score_loss(y[te], np.full(len(te), 0.05)):.4f})')
    note('Report precision and recall (or PR-AUC) for rare events: ROC-AUC looks good even when most alarms')
    note('are false, because it is dominated by the many easy negatives. If a probability feeds a decision')
    note('- ATLAS turns anomaly scores into crash risk - check calibration, not just ranking.')


if __name__ == '__main__':
    run(main, __doc__)
