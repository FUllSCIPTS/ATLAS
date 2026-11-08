#!/usr/bin/env python3
"""ML 19 - Multi-armed bandits: explore or exploit? epsilon-greedy, UCB1 and Thompson sampling.

ATLAS link: at City Centre, ATLAS Go offers rides to drivers whose acceptance rates it must learn
(atlas_go/intelligence.py DRIVER_POOLS; the app's acceptance model is the Beta posterior of ML 05).
Each offer is a pull of an arm; an accepted offer is a reward. Every offer to a poor driver costs time.
Applies to: A/B testing, ad and news selection, clinical trials, recommender exploration, pricing.
Exercise: make one driver's acceptance drop half-way through and add a sliding window to UCB.
"""
import math

import numpy as np

from common import note, run, show, table
from atlas_go.intelligence import DRIVER_POOLS


def simulate(policy, p, rounds, rng):
    k = len(p)
    n, s = np.zeros(k), np.zeros(k)
    regret = 0.0
    for t in range(1, rounds + 1):
        mean = s / np.maximum(n, 1)
        if policy == 'random':
            a = rng.integers(k)
        elif policy != 'Thompson' and (n == 0).any():
            a = int(np.flatnonzero(n == 0)[0])                             # try every driver once first
        elif policy == 'greedy':
            a = int(np.argmax(mean))
        elif policy == 'eps-greedy':
            a = rng.integers(k) if rng.random() < 0.1 else int(np.argmax(mean))
        elif policy == 'UCB1':
            a = int(np.argmax(mean + np.sqrt(2 * math.log(t) / n)))
        else:                                                              # Thompson: sample each Beta posterior
            a = int(np.argmax(rng.beta(s + 1, n - s + 1)))
        reward = rng.random() < p[a]
        n[a] += 1
        s[a] += reward
        regret += max(p) - p[a]
    return regret, n


def main():
    pool = DRIVER_POOLS[1]                                                 # City Centre
    p = np.array([c.accept for c in pool])
    show('City Centre drivers (true acceptance)', ', '.join(f'{c.name} {c.accept:.2f}' for c in pool))
    rows = []
    for policy in ('random', 'greedy', 'eps-greedy', 'UCB1', 'Thompson'):
        regrets, best_share = [], []
        for run_ in range(60):
            rg, n = simulate(policy, p, 2000, np.random.default_rng(run_))
            regrets.append(rg)
            best_share.append(n[np.argmax(p)] / n.sum())
        rows.append((policy, f'{np.mean(regrets):.1f}', f'{np.percentile(regrets, 90):.1f}', f'{np.mean(best_share):.2f}'))
    table(['policy', 'mean regret (lost accepts)', '90th pct regret', 'offers to best driver'], rows)
    note('Regret = accepts lost versus always offering the best driver (Leah). Greedy looks fine on average')
    note('but has the worst tail: some runs lock onto Sam or Rory for good. Epsilon-greedy never stops paying')
    note('a 10 % exploration tax (including offers to Dara). UCB1 explores until it can prove which of three')
    note('near-equal drivers is best, which is slow here. Thompson samples from the Beta posterior - the same')
    note('Beta-Bernoulli model ATLAS Go uses for acceptance - and wins on both mean and tail.')

if __name__ == '__main__':
    run(main, __doc__)
