#!/usr/bin/env python3
"""ML 06 - A decision tree from scratch: readable rules for "what kind of incident is this?".

ATLAS link: anomaly kinds in data.zip. An operator can read and audit a depth-3 tree; it says which
metric and which threshold separate a request flood from a CPU exhaustion.
Applies to: credit rules, triage protocols, any setting where the model must be explained.
Exercise: switch the impurity from Gini to entropy and compare the chosen splits.
"""
import numpy as np
from sklearn.metrics import accuracy_score
from sklearn.tree import DecisionTreeClassifier, export_text

from common import CATEGORIES, FEATURES, load_anomaly, note, run, show, split


def gini(y):
    p = np.bincount(y, minlength=6) / max(len(y), 1)
    return 1 - (p ** 2).sum()


def best_split(X, y):
    best = (None, None, gini(y))
    for j in range(X.shape[1]):
        for t in np.unique(np.quantile(X[:, j], np.linspace(0.05, 0.95, 19))):
            left = X[:, j] <= t
            if left.all() or not left.any():
                continue
            g = left.mean() * gini(y[left]) + (~left).mean() * gini(y[~left])
            if g < best[2] - 1e-9:
                best = (j, t, g)
    return best


def grow(X, y, depth, max_depth=3):
    j, t, _ = best_split(X, y)
    if depth == max_depth or j is None or len(y) < 10:
        return int(np.bincount(y, minlength=6).argmax())
    left = X[:, j] <= t
    return (j, t, grow(X[left], y[left], depth + 1, max_depth), grow(X[~left], y[~left], depth + 1, max_depth))


def predict(node, x):
    while isinstance(node, tuple):
        j, t, l, r = node
        node = l if x[j] <= t else r
    return node


def show_tree(node, indent='  '):
    if not isinstance(node, tuple):
        print(f'{indent}-> {CATEGORIES[node]}')
        return
    j, t, l, r = node
    print(f'{indent}if {FEATURES[j]} <= {t:.3g}:')
    show_tree(l, indent + '    ')
    print(f'{indent}else:')
    show_tree(r, indent + '    ')


def main():
    X, y, cat = load_anomaly()
    A, c = X[y == 1], cat[y == 1]
    tr, te = split(len(c), seed=6)
    tree = grow(A[tr], c[tr], 0)
    print('  our tree (Gini impurity, depth 3):')
    show_tree(tree, '    ')
    ours = np.array([predict(tree, x) for x in A[te]])
    sk = DecisionTreeClassifier(max_depth=3, random_state=0).fit(A[tr], c[tr])
    show('test accuracy: ours / scikit-learn', f'{accuracy_score(c[te], ours):.3f} / {accuracy_score(c[te], sk.predict(A[te])):.3f}')
    deep = DecisionTreeClassifier(random_state=0).fit(A[tr], c[tr])
    show('unlimited depth: train / test', f'{deep.score(A[tr], c[tr]):.3f} / {deep.score(A[te], c[te]):.3f} '
         f'({deep.get_n_leaves()} leaves)')
    print('  scikit-learn depth-2 rules:')
    print('\n'.join('    ' + line for line in export_text(
        DecisionTreeClassifier(max_depth=2, random_state=0).fit(A[tr], c[tr]), feature_names=FEATURES).splitlines()))
    note('A tree greedily picks the one question that most purifies the groups, then recurses. Trees need')
    note('no scaling (thresholds, not distances) and read like a runbook. Grown fully they memorise the')
    note('training set, so depth (or pruning) is the regulariser; ML 07 combines many trees instead.')
    note('Greedy splitting is myopic: scikit-learn opens with a different, almost equally pure question')
    note('(disk_ms instead of queue_depth) and its depth-3 tree ends up weaker. Early choices compound.')


if __name__ == '__main__':
    run(main, __doc__)
