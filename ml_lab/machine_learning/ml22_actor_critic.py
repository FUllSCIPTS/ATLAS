#!/usr/bin/env python3
"""ML 22 - Actor and critic networks: advantage actor-critic (A2C) for ride dispatch vs REINFORCE.

ATLAS link: ATLAS Go dispatches with a softmax policy learned by REINFORCE with a running-average
baseline (android-app/training/rl_sim.py, intelligence.LearningLab). Here the same dispatch problem
(intelligence._candidates, the same reward) is learned by two neural networks:
  * the ACTOR  pi(a | s): a small network that scores each candidate driver (4 features -> 8 tanh -> 1);
    a softmax over the four scores is the policy;
  * the CRITIC V(s): a network that reads the whole situation (all four candidates, 16 inputs ->
    16 tanh -> 1) and predicts the reward to expect before any driver is chosen.
The actor is pushed by the ADVANTAGE A = r - V(s): "was this choice better than usual for this
situation?" A running average b cannot tell an easy situation from a hard one; the critic can, so
the gradient is less noisy and learning needs fewer rides. Both are compared with the v1.4 policy
shipped in the app and the nearest-driver rule on the same 300 held-out situations.
Applies to: any sequential decision with delayed or noisy rewards - robotics, ads, logistics.
Exercise: make the critic see only the chosen driver (not all four) - the advantage gets worse. Why?
"""
import random

import numpy as np

from common import note, run, show, table
from atlas_go import intelligence as ai
from atlas_go import learned as L


def situation(rng: random.Random):
    cands = ai._candidates(rng)
    phi = np.array([c.features() for c in cands])          # 4 drivers x 4 features (as in policy v1.4)
    return cands, phi


def ride_reward(c, rng: random.Random) -> float:
    """Same delayed reward as LearningLab.train: pickup minutes, cancellation, shortage caused elsewhere."""
    accepted = rng.random() < c.accept
    pickup = c.eta if accepted else c.eta + 1.5 + rng.uniform(2.0, 5.0)
    cancel = pickup > 8.0 and rng.random() < .45
    shortage = c.surge * c.last * rng.uniform(6.0, 14.0)
    return -pickup - 10.0 * cancel - shortage


def softmax(z):
    z = z - z.max()
    e = np.exp(z)
    return e / e.sum()


class Actor:
    """Scores each driver with the same small network; softmax over drivers."""

    def __init__(self, seed, hidden=8):
        g = np.random.default_rng(seed)
        self.W = g.normal(0, .5, (4, hidden))
        self.b = np.zeros(hidden)
        self.v = g.normal(0, .1, hidden)

    def scores(self, phi):
        self.h = np.tanh(phi @ self.W + self.b)
        return self.h @ self.v

    def probs(self, phi):
        return softmax(self.scores(phi))

    def update(self, phi, a, advantage, lr):
        p = self.probs(phi)
        g_s = -p
        g_s[a] += 1.0                                       # d log pi(a) / d score_i
        g_v = (g_s[:, None] * self.h).sum(0)
        g_pre = (g_s[:, None] * self.v[None, :]) * (1 - self.h ** 2)
        self.v += lr * advantage * g_v
        self.W += lr * advantage * (phi.T @ g_pre)
        self.b += lr * advantage * g_pre.sum(0)


class Critic:
    """V(s) from all four candidates (16 inputs)."""

    def __init__(self, seed, hidden=16):
        g = np.random.default_rng(seed)
        self.W = g.normal(0, .3, (16, hidden))
        self.b = np.zeros(hidden)
        self.v = g.normal(0, .1, hidden)
        self.c = -8.0

    def value(self, phi):
        self.x = phi.reshape(-1)
        self.h = np.tanh(self.x @ self.W + self.b)
        return float(self.h @ self.v + self.c)

    def update(self, phi, target, lr):
        err = target - self.value(phi)                      # minimise (target - V)^2
        g_pre = err * self.v * (1 - self.h ** 2)
        self.v += lr * err * self.h
        self.c += lr * err
        self.W += lr * np.outer(self.x, g_pre)
        self.b += lr * g_pre
        return err


def expected(policy_choice, tests):
    return float(np.mean([ai.expected_cost(cands[policy_choice(phi)]) for cands, phi in tests]))


def train(method, episodes, seed, tests, checkpoints):
    rng = random.Random(seed)
    curve, grad_sq = [], []
    if method == 'reinforce':                               # linear policy + running-average baseline (as the app)
        w, base = np.zeros(4), -10.0
        for ep in range(1, episodes + 1):
            cands, phi = situation(rng)
            p = softmax(phi @ w)
            a = rng.choices(range(4), weights=p)[0]
            r = ride_reward(cands[a], rng)
            g = (r - base) * (phi[a] - p @ phi)
            grad_sq.append(r - base)                        # the signal that scales the gradient
            w += .004 * g
            base += .01 * (r - base)
            if ep in checkpoints:
                curve.append(expected(lambda f: int(np.argmax(f @ w)), tests))
        return curve, grad_sq
    actor, critic = Actor(seed), Critic(seed + 1)
    for ep in range(1, episodes + 1):
        cands, phi = situation(rng)
        p = actor.probs(phi)
        a = rng.choices(range(4), weights=p)[0]
        r = ride_reward(cands[a], rng)
        advantage = r - critic.value(phi)                   # one-step episode: the return is r
        grad_sq.append(advantage)
        critic.update(phi, r, .002)
        actor.update(phi, a, advantage, .002)
        if ep in checkpoints:
            curve.append(expected(lambda f: int(np.argmax(actor.scores(f))), tests))
    return curve, grad_sq


def main():
    test_rng = random.Random(1007)
    tests = [situation(test_rng) for _ in range(300)]
    nearest = expected(lambda f: int(np.argmax(f[:, 0])), tests)            # feature 0 is -ETA/5
    approved = expected(lambda f: int(np.argmax(f @ np.array(L.RIDE_WEIGHTS))), tests)
    checkpoints = [250, 500, 1000, 2000, 4000, 8000]
    rows, noise = [], {}
    results = {}
    for method in ('reinforce', 'actor-critic'):
        curves = []
        for seed in (1, 2, 3):
            curve, g2 = train(method, checkpoints[-1], seed, tests, set(checkpoints))
            curves.append(curve)
            noise.setdefault(method, []).append(np.var(g2[2000:]))
        results[method] = np.mean(curves, 0)
    for k, n in enumerate(checkpoints):
        rows.append((n, f"{results['reinforce'][k]:.2f}", f"{results['actor-critic'][k]:.2f}"))
    table(['rides trained', 'REINFORCE + baseline (min)', 'actor-critic A2C (min)'], rows)
    show('nearest-driver rule', f'{nearest:.2f} min')
    show('approved policy v1.4 (30,000 rides)', f'{approved:.2f} min')
    goal = approved + .1
    first = {m: next((n for n, v in zip(checkpoints, results[m]) if v <= goal), 'not yet') for m in results}
    show(f'rides until within 0.1 min of v1.4 ({goal:.2f})', f"REINFORCE {first['reinforce']} · A2C {first['actor-critic']}")
    show('variance of the learning signal (rides 2,001-8,000)',
         f"REINFORCE r - b: {np.mean(noise['reinforce']):.1f} · A2C r - V(s): {np.mean(noise['actor-critic']):.1f}")
    note('The critic predicts how good a situation is before the choice (several cheap drivers: good;')
    note('only far or reluctant drivers: bad). Subtracting it leaves only the credit due to the choice,')
    note('so the actor\'s gradient is less noisy than with a single running average (REINFORCE baseline).')


if __name__ == '__main__':
    run(main, __doc__)
