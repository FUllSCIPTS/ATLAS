#!/usr/bin/env python3
"""ML 23 - Multi-agent RL: two agents sharing one critic (MAPPO) for dispatch and pricing in a city twin.

ATLAS link: the ATLAS Go 1.3 twin layer has two decision agents - Agent 1 (dispatch, every request)
and Agent 2 (pricing and repositioning, per zone) - and the postdoc proposal trains them together:
centralised training with ONE SHARED CRITIC that sees the whole city, decentralised execution where
each agent acts on its own view (MAPPO). In the app they are rehearsal planners (atlas_go/twin.py);
this experiment trains learned versions of both in a small twin of three Cork zones and compares
  * IPPO  - independent PPO: each agent has its own critic on its own observation;
  * MAPPO - multi-agent PPO: both actors use advantages from one centralised critic V(global state);
  * the heuristics "nearest car, never reposition" and random actions.
A concert ends at the Mardyke in the second half of the hour. Agent 2 can move idle cars there or
add a capped surge; Agent 1 must decide whether to send the Mardyke car to a City Centre rider.
Both earn the same team reward: -(rider waiting + 6 x unmet requests + 1.5 x empty km + price jumps),
the objective of the proposal. Agent 1 does not see the concert forecast; only the critic does.
Applies to: fleets, warehouses, traffic signals, power grids - teams of agents with one goal.
Exercise: give Agent 1 the forecast too and compare again; then remove the price-jump penalty.
"""
import numpy as np

from common import note, run, show, table

ZONES = ('Mardyke', 'City Centre', 'Kent Station')
STEPS = 12                     # 5-minute steps: one hour
A1 = ('Centre car', 'Mardyke car', 'Kent car')          # who serves the City Centre rider
A1_WAIT = (2.0, 3.0, 5.0)
A2 = ('do nothing', 'move Kent -> Mardyke', 'move Centre -> Mardyke', 'surge x1.3 at Mardyke')


class TwinCity:
    def __init__(self, rng):
        self.rng = rng

    def reset(self):
        self.t = 0
        self.cars = np.array([1, 2, 3])                     # idle cars per zone
        self.busy = []                                      # (return step, zone)
        self.surge = 0
        return self.state()

    def forecast(self, t=None):
        t = self.t if t is None else t
        return np.array([2.6 if t >= 6 else .4, .6, .5])    # expected requests per step by zone (concert at step 6)

    def obs1(self):                                         # dispatch agent: only the idle cars it can send
        c = self.cars
        return np.array([1, c[1] > 0, c[0] > 0, c[2] > 0, c[0] == 1, c[0] >= 2], float)

    def obs2(self):                                         # pricing agent: zone supply and its forecast
        c, f = self.cars, self.forecast(self.t + 1)
        return np.array([1, c[0] / 3, c[1] / 3, c[2] / 3, f[0] / 3, self.t / STEPS], float)

    def state(self):                                        # what only the centralised critic sees
        c, f = self.cars, self.forecast(self.t + 1)
        return np.array([1, *(c / 3), f[0] / 3, self.t / STEPS, len(self.busy) / 3, self.surge,
                         (c[0] / 3) * (f[0] / 3), (self.t >= 5) * (c[0] == 0)], float)

    def available1(self):
        return np.array([self.cars[1] > 0, self.cars[0] > 0, self.cars[2] > 0], bool)

    def mask1(self):                                        # with no idle car the choice does not matter
        m = self.available1()
        return m if m.any() else np.array([True, False, False])

    def mask2(self):
        return np.array([True, self.cars[2] > 0, self.cars[1] > 0, True], bool)

    def step(self, a1, a2):
        cost = 0.0
        for when, z in [b for b in self.busy if b[0] <= self.t]:
            self.cars[z] += 1
        self.busy = [b for b in self.busy if b[0] > self.t]
        # Agent 2 moves first (5 minutes ahead of the requests)
        self.surge = 0
        if a2 in (1, 2):
            src = 2 if a2 == 1 else 1
            self.cars[src] -= 1
            self.cars[0] += 1
            cost += 1.5                                     # empty km
        elif a2 == 3:
            self.surge = 1
            cost += 1.0                                     # price jump
        # Agent 1 serves the City Centre rider
        if self.available1().any():
            if not self.available1()[a1]:
                a1 = int(np.argmax(self.available1()))
            z = (1, 0, 2)[a1]
            self.cars[z] -= 1
            self.busy.append((self.t + 2, z))
            cost += A1_WAIT[a1]
        else:
            cost += 6.0
        # other requests in each zone, served by local idle cars
        f = self.forecast()
        f[0] *= .7 if self.surge else 1.0                   # some riders choose to wait at a higher price
        for z in (0, 2):
            demand = self.rng.poisson(f[z])
            served = min(demand, self.cars[z])
            self.cars[z] -= served
            for _ in range(served):
                self.busy.append((self.t + 2, z))
            cost += 2.0 * served + 6.0 * (demand - served)
        self.t += 1
        return -cost, self.t >= STEPS


def softmax_masked(logits, mask):
    z = np.where(mask, logits, -1e9)
    z = z - z.max()
    e = np.exp(z) * mask
    return e / e.sum()


class Actor:
    def __init__(self, n_actions, n_obs, rng):
        self.W = rng.normal(0, .01, (n_actions, n_obs))

    def probs(self, o, mask):
        return softmax_masked(self.W @ o, mask)

    def ppo_update(self, batch, lr=.05, clip=.2, epochs=4):
        for _ in range(epochs):
            for o, mask, a, old_p, adv in batch:
                p = self.probs(o, mask)
                ratio = p[a] / old_p
                if (adv > 0 and ratio > 1 + clip) or (adv < 0 and ratio < 1 - clip):
                    continue                                # clipped: no gradient
                g = -p
                g[a] += 1                                   # d log p(a) / d logits
                self.W += lr * adv * ratio * np.outer(g, o) / len(batch) * 8


class Critic:
    """Linear value function fitted by ridge regression to the returns of the latest batch."""

    def __init__(self, n):
        self.w = np.zeros(n)

    def __call__(self, x):
        return float(x @ self.w)

    def fit(self, X, G):
        X, G = np.array(X), np.array(G)
        self.w = np.linalg.solve(X.T @ X + 1e-2 * np.eye(X.shape[1]), X.T @ G)


def episode(env, act1, act2, record=False):
    env.reset()
    total, rows = 0.0, []
    done = False
    while not done:
        o1, m1, o2, m2, s = env.obs1(), env.mask1(), env.obs2(), env.mask2(), env.state()
        a1, p1 = act1(o1, m1)
        a2, p2 = act2(o2, m2)
        r, done = env.step(a1, a2)
        total += r
        if record:
            rows.append((o1, m1, a1, p1, o2, m2, a2, p2, s, r))
    return total, rows


def train(method, seed, iterations=60, batch=16):
    rng = np.random.default_rng(seed)
    env = TwinCity(rng)
    actor1, actor2 = Actor(3, 6, rng), Actor(4, 6, rng)
    central = Critic(11)
    own1, own2 = Critic(6), Critic(6)
    curve, spread = [], []

    def sample(actor):
        def act(o, m):
            p = actor.probs(o, m)
            a = int(rng.choice(len(p), p=p))
            return a, p[a]
        return act

    for it in range(iterations):
        data, totals = [], []
        for _ in range(batch):
            total, rows = episode(env, sample(actor1), sample(actor2), record=True)
            totals.append(total)
            G, returns = 0.0, []
            for row in reversed(rows):
                G += row[-1]
                returns.append(G)
            data += list(zip(rows, reversed(returns)))
        curve.append(-np.mean(totals))
        if method == 'mappo':
            central.fit([row[8] for row, _ in data], [g for _, g in data])
            adv1 = adv2 = [g - central(row[8]) for row, g in data]
        else:
            own1.fit([row[0] for row, _ in data], [g for _, g in data])
            own2.fit([row[4] for row, _ in data], [g for _, g in data])
            adv1 = [g - own1(row[0]) for row, g in data]
            adv2 = [g - own2(row[4]) for row, g in data]
        sd1, sd2 = np.std(adv1) + 1e-8, np.std(adv2) + 1e-8
        spread.append((sd1, sd2))                           # how noisy each actor's learning signal is
        actor1.ppo_update([(row[0], row[1], row[2], row[3], a / sd1) for (row, _), a in zip(data, adv1)])
        actor2.ppo_update([(row[4], row[5], row[6], row[7], a / sd2) for (row, _), a in zip(data, adv2)])
    greedy1 = lambda o, m: (int(np.argmax(np.where(m, actor1.W @ o, -1e9))), 1.0)
    greedy2 = lambda o, m: (int(np.argmax(np.where(m, actor2.W @ o, -1e9))), 1.0)
    return curve, (greedy1, greedy2), (actor1, actor2), np.mean(spread[iterations // 2:], 0)


def evaluate(act1, act2, seed=99, n=500):
    env = TwinCity(np.random.default_rng(seed))
    return -np.mean([episode(env, act1, act2)[0] for _ in range(n)])


def main():
    nearest = lambda o, m: (int(np.argmax(m)), 1.0)                          # Centre car if any
    nothing = lambda o, m: (0, 1.0)
    rnd = np.random.default_rng(5)
    random_act = lambda o, m: (int(rnd.choice(np.flatnonzero(m))), 1.0)
    results, curves, policies, noise = {}, {}, {}, {}
    for method in ('ippo', 'mappo'):
        finals, cs, sp = [], [], []
        for seed in (1, 2, 3, 4):
            curve, (g1, g2), actors, spread = train(method, seed)
            cs.append(curve)
            sp.append(spread)
            finals.append(evaluate(g1, g2))
            policies[method] = actors
        results[method] = (np.mean(finals), np.std(finals))
        curves[method] = np.mean(cs, 0)
        noise[method] = np.mean(sp, 0)
    table(['training iteration (16 hours each)', 'IPPO cost / hour', 'MAPPO cost / hour'],
          [(k + 1, f"{curves['ippo'][k]:.1f}", f"{curves['mappo'][k]:.1f}") for k in (0, 4, 9, 19, 39, 59)])
    rows = [('nearest car, never reposition', f'{evaluate(nearest, nothing):.1f}'),
            ('random', f'{evaluate(random_act, random_act):.1f}'),
            ('IPPO (independent critics)', f"{results['ippo'][0]:.1f} ± {results['ippo'][1]:.1f}"),
            ('MAPPO (one shared critic)', f"{results['mappo'][0]:.1f} ± {results['mappo'][1]:.1f}")]
    table(['policy (500 test hours, greedy)', 'team cost per hour'], rows)
    table(['learning signal (spread of advantages, 2nd half)', 'Agent 1', 'Agent 2'],
          [('IPPO: own critic on own view', f"{noise['ippo'][0]:.1f}", f"{noise['ippo'][1]:.1f}"),
           ('MAPPO: shared critic on the whole city', f"{noise['mappo'][0]:.1f}", f"{noise['mappo'][1]:.1f}")])
    a1, a2 = policies['mappo']
    env = TwinCity(np.random.default_rng(0))
    env.reset()
    trace = []
    for t in range(STEPS):
        o1, m1, o2, m2 = env.obs1(), env.mask1(), env.obs2(), env.mask2()
        x1 = int(np.argmax(np.where(m1, a1.W @ o1, -1e9)))
        x2 = int(np.argmax(np.where(m2, a2.W @ o2, -1e9)))
        trace.append((t * 5, ' '.join(map(str, env.cars)), A2[x2], A1[x1]))
        env.step(x1, x2)
    table(['minute', 'idle cars M/C/K', 'Agent 2 (pricing + moves)', 'Agent 1 (dispatch)'], trace)
    note('Both agents get the same reward, so each return also depends on the other agent. Agent 1 sees only its')
    note('idle cars: its own critic cannot tell an early quiet minute from the concert rush, so its advantages')
    note('are noisy. The shared critic sees the whole city and the forecast, and cuts that noise by about 40 %:')
    note('MAPPO improves faster in the middle of training. In this small twin both end at similar policies,')
    note('which beat "nearest car" by about 20 %. At run time each actor acts on its own view only.')


if __name__ == '__main__':
    run(main, __doc__)
