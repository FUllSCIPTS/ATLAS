#!/usr/bin/env python3
"""ML 20 - Reinforcement learning with tabular Q-learning: when should the courier leave?

ATLAS link: ATLAS Go's courier timing table (atlas_go/learned.py COURIER_DELAY) was learned by
Q-learning in android-app/training/rl_sim.py. We retrain it from scratch with the same environment
(food_episode, food_reward) and compare our table with the shipped one and with "send now".
Applies to: robotics, games, inventory control, traffic signals, recommendation sequences.
Exercise: add a discount factor and a second step (the courier can wait at a midpoint) - now the
problem needs bootstrapped targets r + gamma * max Q(s', .).
"""
import sys

import numpy as np

from common import ROOT, note, run, show, table
from atlas_go import learned as L

sys.path.insert(0, str(ROOT / 'android-app' / 'training'))
from rl_sim import DELAYS, SLACKS, food_episode, food_reward  # noqa: E402


def main():
    rng = np.random.default_rng(20)
    Q = np.zeros((len(SLACKS), len(DELAYS)))
    N = np.zeros_like(Q)
    episodes = 40000
    for ep in range(episodes):
        e, tau, p = food_episode(rng)                       # kitchen estimate, courier travel, true prep time
        s = int(np.clip(round(e - tau), SLACKS[0], SLACKS[-1])) - SLACKS[0]
        eps = max(0.03, 1.0 - ep / 15000)                   # explore a lot early, then mostly exploit
        a = rng.integers(len(DELAYS)) if rng.random() < eps else int(np.argmax(Q[s]))
        r = food_reward(DELAYS[a], tau, p)[0]
        N[s, a] += 1
        Q[s, a] += max(0.02, 1 / N[s, a]) * (r - Q[s, a])   # one-step episodes: target is just r
    ours = {int(SLACKS[i]): int(DELAYS[np.argmax(Q[i])]) for i in range(len(SLACKS))}
    rows = [(s, ours[s], L.COURIER_DELAY[s]) for s in range(-2, 19, 2)]
    table(['kitchen slack (min)', 'our Q-learning wait', 'ATLAS Go table'], rows)
    agree = np.mean([abs(ours[s] - L.COURIER_DELAY[s]) <= 1 for s in ours])
    show('slack values where tables agree within 1 min', f'{agree:.0%}')
    test = np.random.default_rng(99)
    scores = {'send immediately': [], 'our policy': [], 'ATLAS Go table': []}
    gaps = {k: [] for k in scores}
    for _ in range(5000):
        e, tau, p = food_episode(test)
        s = int(np.clip(round(e - tau), SLACKS[0], SLACKS[-1]))
        for name, d in (('send immediately', 0), ('our policy', ours[s]), ('ATLAS Go table', L.COURIER_DELAY[s])):
            r, cw, fw, _ = food_reward(d, tau, p)
            scores[name].append(r)
            gaps[name].append(cw + fw)
    table(['policy', 'mean reward', 'courier idle + food waiting (min)'],
          [(k, f'{np.mean(v):.2f}', f'{np.mean(gaps[k]):.2f}') for k, v in scores.items()])
    note('Q(s, a) estimates the reward of waiting a minutes when the kitchen slack is s; the policy is the')
    note('best a in each row. Epsilon-greedy exploration tries every action before trusting the table. The')
    note('learned rule waits about "slack minus one minute": the courier arrives as the food is ready.')


if __name__ == '__main__':
    run(main, __doc__)
