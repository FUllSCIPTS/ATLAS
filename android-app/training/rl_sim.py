"""Toy RL simulations used to drive the ATLAS Go "The Learner" video act.

Two small learners, both illustrative (not the production policy):
  1. Ride dispatch  - softmax policy over 4 candidate drivers, trained with REINFORCE.
     Features: ETA, acceptance probability (discrete model), LSTM surge forecast of the
     driver's current zone, and whether the driver is the last one free in that zone.
     Reward arrives late: pickup time, cancellations and the future shortage caused
     by pulling the last driver out of a zone that is about to surge.
  2. Food courier timing - tabular Q-learning over "kitchen slack" (prep estimate minus
     courier travel time). Action: how many minutes to wait before dispatching the courier.
     Reward penalises courier idle time at the counter, food waiting (cooling) and total time.
"""
import json
import numpy as np

rng = np.random.default_rng(7)
CHECK = sorted(set(np.unique(np.geomspace(1, 30000, 140).astype(int)).tolist()) | {0})


# ---------------------------------------------------------------- ride dispatch
def ride_candidates(rng):
    eta = rng.uniform(1.0, 9.0, 4)
    p_acc = rng.uniform(0.35, 0.98, 4)
    surge = rng.uniform(0.0, 1.0, 4) ** 1.5
    last = (rng.uniform(size=4) < 0.45).astype(float)
    return eta, p_acc, surge, last


def ride_features(eta, p_acc, surge, last):
    return np.stack([-eta / 5.0, p_acc, -(surge * last), -surge], axis=1)


def ride_outcome(i, eta, p_acc, surge, last, rng):
    accepted = rng.uniform() < p_acc[i]
    pickup = eta[i] if accepted else eta[i] + 1.5 + rng.uniform(2.0, 5.0)
    cancel = pickup > 8.0 and rng.uniform() < 0.45
    shortage = surge[i] * last[i] * rng.uniform(6.0, 14.0)
    r = -pickup - 10.0 * cancel - shortage
    return r, dict(pickup=pickup, cancel=bool(cancel), shortage=shortage, accepted=bool(accepted))


def train_ride(n=30000, lr=0.004):
    w = np.zeros(4)
    base = -10.0
    rewards, nearest_rewards, snaps = [], [], []
    for ep in range(n + 1):
        if ep in CHECK:
            snaps.append(w.copy().tolist())
        if ep == n:
            break
        eta, p_acc, surge, last = ride_candidates(rng)
        phi = ride_features(eta, p_acc, surge, last)
        z = phi @ w
        p = np.exp(z - z.max()); p /= p.sum()
        a = rng.choice(4, p=p)
        r, _ = ride_outcome(a, eta, p_acc, surge, last, rng)
        grad = phi[a] - p @ phi
        w += lr * (r - base) * grad
        base += 0.01 * (r - base)
        rewards.append(r)
        rn, _ = ride_outcome(int(np.argmin(eta)), eta, p_acc, surge, last, rng)
        nearest_rewards.append(rn)

    return w, np.array(rewards), np.array(nearest_rewards), snaps


# ---------------------------------------------------------------- food timing
SLACKS = np.arange(-2, 19)  # prep estimate - travel time (minutes, rounded)
DELAYS = np.arange(0, 17)


def food_episode(rng):
    e = rng.uniform(6.0, 20.0)
    tau = rng.uniform(2.0, 8.0)
    p = max(2.0, e + rng.normal(0.0, 1.5))
    return e, tau, p


def food_reward(d, tau, p):
    arrive = d + tau
    courier_wait = max(0.0, p - arrive)
    food_wait = max(0.0, arrive - p)
    total = max(p, arrive) + 7.0
    r = -0.6 * courier_wait - 1.2 * food_wait - 0.15 * total
    return r, courier_wait, food_wait, total


def train_food(n=30000):
    Q = np.zeros((len(SLACKS), len(DELAYS)))
    N = np.zeros_like(Q)
    rewards, gaps, now_rewards, qsnaps = [], [], [], []
    for ep in range(n + 1):
        if ep in CHECK:
            qsnaps.append(Q.copy())
        if ep == n:
            break
        e, tau, p = food_episode(rng)
        s = int(np.clip(round(e - tau), SLACKS[0], SLACKS[-1])) - SLACKS[0]
        eps = max(0.03, 1.0 - ep / 12000)
        a = rng.integers(len(DELAYS)) if rng.uniform() < eps else int(np.argmax(Q[s]))
        r, cw, fw, _ = food_reward(DELAYS[a], tau, p)
        N[s, a] += 1
        Q[s, a] += max(0.02, 1.0 / N[s, a]) * (r - Q[s, a])
        rewards.append(r)
        gaps.append(cw + fw)
        now_rewards.append(food_reward(0, tau, p)[0])
    policy = {int(SLACKS[i]): int(DELAYS[np.argmax(Q[i])]) for i in range(len(SLACKS))}
    return Q, policy, np.array(rewards), np.array(gaps), np.array(now_rewards), qsnaps


def smooth(x, k=600):
    c = np.cumsum(np.insert(x, 0, 0.0))
    out = np.empty_like(x)
    for i in range(len(x)):
        lo = max(0, i - k + 1)
        out[i] = (c[i + 1] - c[lo]) / (i + 1 - lo)
    return out


def sample(x, m=240):
    # x is already smoothed; replace with block means of the raw series when given raw
    return [float(v) for v in x[np.linspace(0, len(x) - 1, m).astype(int)]]


def blocks(x, m=240):
    return [float(b.mean()) for b in np.array_split(x, m)]


if __name__ == "__main__":
    w, rr, rn, snaps = train_ride()
    Q, pol, fr, fg, f0, qsnaps = train_food()

    # Greedy evaluation of each checkpoint on a fixed held-out set (clean learning curves).
    er = np.random.default_rng(11)
    ride_set = [(ride_candidates(er), int(er.integers(1 << 30))) for _ in range(1500)]
    def ride_eval(wv):
        # On-policy: sample from the softmax policy exactly as the agent behaves while learning.
        wv = np.array(wv); tot = 0.0
        for c, sd in ride_set:
            z = ride_features(*c) @ wv; p = np.exp(z - z.max()); p /= p.sum()
            a = int(np.random.default_rng(sd + 1).choice(4, p=p))
            tot += ride_outcome(a, *c, np.random.default_rng(sd))[0]
        return tot / len(ride_set)
    ride_eval_curve = [ride_eval(wv) for wv in snaps]
    fr_rng = np.random.default_rng(12)
    food_set = [food_episode(fr_rng) for _ in range(1500)]
    def food_eval(Qs):
        tot, gap = 0.0, 0.0
        for e, tau, p in food_set:
            si = int(np.clip(round(e - tau), SLACKS[0], SLACKS[-1])) - SLACKS[0]
            a = int(np.argmax(Qs[si])) if np.any(Qs[si]) else int(fr_rng.integers(len(DELAYS)))
            r, cw, fw, _ = food_reward(DELAYS[a], tau, p)
            tot += r; gap += cw + fw
        return tot / len(food_set), gap / len(food_set)
    fe = [food_eval(q) for q in qsnaps]
    food_eval_curve = [x[0] for x in fe]; food_gap_eval = [x[1] for x in fe]
    food_now = float(np.mean([food_reward(0, tau, p)[0] for e, tau, p in food_set]))
    food_now_gap = float(np.mean([sum(food_reward(0, tau, p)[1:3]) for e, tau, p in food_set]))
    ride_nearest = float(np.mean([ride_outcome(int(np.argmin(c[0])), *c, np.random.default_rng(sd))[0] for c, sd in ride_set]))

    # Evaluate the learned ride policy greedily vs nearest-driver baseline.
    ev_rng = np.random.default_rng(99)
    greedy, nearest = [], []
    for _ in range(20000):
        c = ride_candidates(ev_rng)
        phi = ride_features(*c)
        seed = ev_rng.integers(1 << 30)
        greedy.append(ride_outcome(int(np.argmax(phi @ w)), *c, np.random.default_rng(seed))[0])
        nearest.append(ride_outcome(int(np.argmin(c[0])), *c, np.random.default_rng(seed))[0])

    # Evaluate learned food timing vs "dispatch immediately".
    fe_rng = np.random.default_rng(5)
    learned_gap, now_gap, learned_r, now_r, early = [], [], [], [], []
    for _ in range(20000):
        e, tau, p = food_episode(fe_rng)
        s = int(np.clip(round(e - tau), SLACKS[0], SLACKS[-1]))
        d = pol[s]
        r1, cw1, fw1, _ = food_reward(d, tau, p)
        r0, cw0, fw0, _ = food_reward(0, tau, p)
        learned_gap.append(cw1 + fw1); now_gap.append(cw0 + fw0)
        learned_r.append(r1); now_r.append(r0)
        early.append((d + tau) - e)

    out = dict(
        ride=dict(curve=blocks(rr), nearest_curve=blocks(rn),
                  weights=w.tolist(), weight_snaps=snaps,
                  feature_names=["closer ETA", "will accept", "keep last driver in surging zone", "avoid surging zone"],
                  eval_learned=float(np.mean(greedy)), eval_nearest=float(np.mean(nearest)),
                  episodes=len(rr), eval_curve=ride_eval_curve, check=CHECK, nearest_eval=ride_nearest),
        food=dict(curve=blocks(fr), now_curve=blocks(f0), gap_curve=blocks(fg),
                  policy=pol, eval_gap_learned=float(np.mean(learned_gap)), eval_gap_now=float(np.mean(now_gap)),
                  eval_r_learned=float(np.mean(learned_r)), eval_r_now=float(np.mean(now_r)),
                  arrive_vs_estimate=float(np.median(early)), episodes=len(fr),
                  eval_curve=food_eval_curve, gap_eval=food_gap_eval, now_eval=food_now, now_gap=food_now_gap),
    )
    json.dump(out, open("rl_results.json", "w"), indent=1)
    print("ride w", np.round(w, 2), "learned", out["ride"]["eval_learned"], "nearest", out["ride"]["eval_nearest"])
    print("ride eval", [round(x,2) for x in ride_eval_curve[::14]], "nearest", ride_nearest)
    print("food eval", [round(x,2) for x in food_eval_curve[::14]], "now", food_now, "gap", [round(x,2) for x in food_gap_eval[::14]], food_now_gap)
    print("food policy", pol)
    print("food gap learned/now", out["food"]["eval_gap_learned"], out["food"]["eval_gap_now"],
          "r", out["food"]["eval_r_learned"], out["food"]["eval_r_now"], "arrive-est", out["food"]["arrive_vs_estimate"])
