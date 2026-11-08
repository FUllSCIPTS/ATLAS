#!/usr/bin/env python3
"""ML 18 - Learning to rank: recovering a dispatch policy from pairwise preferences.

ATLAS link: ATLAS Go ranks candidate drivers with a learned linear score over four features
(atlas_go/intelligence.py: score, rank; weights in learned.RIDE_WEIGHTS). Here we learn such weights
from "driver A was better than driver B" comparisons labelled by the app's own cost model
(intelligence.expected_cost), and evaluate on the app's test set.
Applies to: search results, recommendations, feeds, hiring shortlists - anything shown as a ranked list.
Exercise: replace the pairwise loss with a listwise softmax (ListNet) and compare.
"""
import random

import numpy as np

from common import note, run, show, table
from atlas_go import learned as L
from atlas_go.intelligence import _candidates, expected_cost, score


def main():
    rng = random.Random(18)
    A, B = [], []
    for _ in range(4000):                                     # 4,000 dispatch situations, 4 drivers each
        cs = _candidates(rng)
        i, j = rng.sample(range(4), 2)
        better, worse = (cs[i], cs[j]) if expected_cost(cs[i]) < expected_cost(cs[j]) else (cs[j], cs[i])
        A.append(better.features())
        B.append(worse.features())
    D = np.array(A) - np.array(B)                             # pairwise: P(better ranked first) = sigmoid(w.(a-b))
    w = np.zeros(4)
    for _ in range(3000):
        p = 1 / (1 + np.exp(-D @ w))
        w += 0.5 * D.T @ (1 - p) / len(D) - 1e-3 * w
    test_rng = random.Random(1018)
    test = [_candidates(test_rng) for _ in range(2000)]

    def evaluate(weights=None, rule=None):
        cost, top1 = 0.0, 0
        for cs in test:
            pick = rule(cs) if rule else max(range(4), key=lambda k: score(cs[k], weights))
            best = min(range(4), key=lambda k: expected_cost(cs[k]))
            cost += expected_cost(cs[pick])
            top1 += pick == best
        return f'{cost / len(test):.2f}', f'{top1 / len(test):.2f}'

    rows = [('nearest driver (ETA only)', *evaluate(rule=lambda cs: min(range(4), key=lambda k: cs[k].eta))),
            ('learned pairwise ranker (ours)', *evaluate(list(w))),
            (f'ATLAS Go policy {L.POLICY_VERSION} (REINFORCE)', *evaluate(L.RIDE_WEIGHTS)),
            ('oracle: lowest expected cost', *evaluate(rule=lambda cs: min(range(4), key=lambda k: expected_cost(cs[k]))))]
    table(['ranking', 'expected wait-cost (min)', 'picks the best driver'], rows)
    names = ['closer ETA', 'will accept', 'keep last driver in surge', 'avoid surging zone']
    scale = max(L.RIDE_WEIGHTS) / max(w)
    show('our weights (scaled to ATLAS max)', ', '.join(f'{n} {v * scale:.2f}' for n, v in zip(names, w)))
    show('ATLAS Go learned weights', ', '.join(f'{n} {v:.2f}' for n, v in zip(names, L.RIDE_WEIGHTS)))
    note('Ranking only needs the order of scores, so we learn from comparisons rather than absolute labels')
    note('(RankNet-style logistic loss on score differences). The nearest driver is not the best one:')
    note('acceptance and keeping a surging zone covered matter. Both learned rankers beat the simple rule.')


if __name__ == '__main__':
    run(main, __doc__)
