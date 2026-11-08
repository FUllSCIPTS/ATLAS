#!/usr/bin/env python3
"""ML 05 - Naive Bayes and Bayes' rule: probabilities from counts, and the base-rate trap.

ATLAS link: two Bayesian models live in ATLAS Go. The acceptance model (intelligence.acceptance) is a
Beta(9, 1) prior updated with a driver's accept/decline history; here we also build a Gaussian naive
Bayes incident classifier on data.zip and show why rare events make alarms unreliable.
Applies to: spam filtering, text classification, medical tests, any prior-plus-evidence reasoning.
Exercise: change the prior to Beta(1, 1) and see how fast a new driver's estimate moves.
"""
import sys

import numpy as np
from sklearn.metrics import accuracy_score
from sklearn.naive_bayes import GaussianNB

from common import ROOT, load_anomaly, note, run, show, split, table

sys.path.insert(0, str(ROOT / 'android-app'))
from atlas_go.intelligence import acceptance  # noqa: E402


def main():
    rows = []
    for offered, accepted in ((0, 0), (1, 0), (5, 3), (20, 12), (100, 60)):
        rows.append((f'{accepted}/{offered}', f'{acceptance(offered, accepted):.3f}',
                     f'{accepted / offered:.3f}' if offered else 'undefined'))
    print('  ATLAS Go acceptance model: posterior mean of Beta(9 + accepted, 1 + declined)')
    table(['accepted/offered', 'ATLAS estimate', 'raw ratio'], rows)

    X, y, cat = load_anomaly()
    L = np.log1p(np.abs(X))
    tr, te = split(len(y), seed=5)
    nb = GaussianNB().fit(L[tr], cat[tr])
    show('Gaussian NB, 6 classes, accuracy', f'{accuracy_score(cat[te], nb.predict(L[te])):.3f}')
    mu, var = nb.theta_, nb.var_
    prior = np.log(nb.class_prior_)
    x = L[te[0]]
    loglik = -0.5 * (np.log(2 * np.pi * var) + (x - mu) ** 2 / var).sum(1)
    post = np.exp(prior + loglik - (prior + loglik).max())
    show('by hand: argmax log P(c) + sum log P(x_i|c)', f'{post.argmax()} vs library {nb.predict(L[te[:1]])[0]}')

    sens, spec, base = 0.99, 0.98, 500 / 10000
    ppv = sens * base / (sens * base + (1 - spec) * (1 - base))
    show('detector: 99 % sensitive, 98 % specific', f'at a 5 % base rate P(anomaly | alarm) = {ppv:.2f}')
    base = 0.001
    ppv = sens * base / (sens * base + (1 - spec) * (1 - base))
    show('same detector, 0.1 % base rate', f'P(anomaly | alarm) = {ppv:.3f}')
    note('A prior is a sensible default before evidence: ATLAS trusts a new driver at 0.9 instead of')
    note('0/0. "Naive" assumes features are independent given the class - wrong (CPU and latency move')
    note('together) yet often good enough. Bayes\' rule also explains alarm fatigue: when incidents are')
    note('rare, most alarms are false even for an excellent detector.')


if __name__ == '__main__':
    run(main, __doc__)
