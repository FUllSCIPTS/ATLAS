import argparse
import random
import time
from uuid import UUID, uuid4

from ml.registry import MODELS, read_json, write_json
from packages.db import database

STATES = (0, 1)
ACTIONS = (0, 1)
BASELINE = {0: 0, 1: 0}
MIN_EVAL_PER_CELL = 8


def current_policy():
    return read_json(MODELS / "active-policy.json", {"version": "baseline", "actions": BASELINE})


def fixture():
    rng = random.Random(19)
    return [(state, action, (0.35 if state == action else 0.05) + rng.uniform(-.05, .05))
            for _ in range(160) for state in STATES for action in ACTIONS]


def experiences():
    with database() as db:
        return [tuple(row[key] for key in ("state", "action", "reward")) for row in db.run(
            "SELECT state, action, reward FROM experience ORDER BY occurred_at, trip_id"
        ).fetchall()]


def fit(samples, source):
    if len(samples) < 80:
        raise ValueError("Need at least 80 completed trips before training from ride outcomes")
    split = int(.7 * len(samples))
    q = {(state, action): 0.0 for state in STATES for action in ACTIONS}
    for state, action, reward in samples[:split]:
        q[state, action] += .09 * (reward - q[state, action])
    actions = {state: max(ACTIONS, key=lambda action: q[state, action]) for state in STATES}
    evaluation = {}
    for state in STATES:
        for action in ACTIONS:
            rewards = [reward for s, a, reward in samples[split:] if s == state and a == action]
            evaluation[f"{state}:{action}"] = {"count": len(rewards), "mean": sum(rewards) / len(rewards) if rewards else None}
    version = str(uuid4())
    candidate = {"version": version, "actions": actions, "evaluation": evaluation, "source": source}
    write_json(MODELS / "policies" / f"{version}.json", candidate)
    return candidate


def approve(version, allow_demo=False):
    version = str(UUID(version))
    candidate = read_json(MODELS / "policies" / f"{version}.json")
    if candidate is None:
        raise ValueError("Unknown policy candidate")
    if candidate["source"] == "synthetic-demo" and not allow_demo:
        raise ValueError("Synthetic candidates require --allow-demo")
    for state in STATES:
        action = candidate["actions"][str(state)]
        proposed = candidate["evaluation"][f"{state}:{action}"]
        baseline = candidate["evaluation"][f"{state}:0"]
        if min(proposed["count"], baseline["count"]) < MIN_EVAL_PER_CELL:
            raise ValueError(f"Insufficient held-out support for state {state}")
        if proposed["mean"] < baseline["mean"]:
            raise ValueError(f"Candidate reward falls below baseline in state {state}")
    write_json(MODELS / "active-policy.json", candidate)
    return candidate


def watch(seconds):
    previous = 0
    while True:
        samples = experiences()
        if len(samples) >= 80 and len(samples) > previous:
            candidate = fit(samples, "recorded-rides")
            previous = len(samples)
            print(f"Candidate {candidate['version']} from {previous} rides. Review before activation.", flush=True)
        time.sleep(seconds)


def main():
    parser = argparse.ArgumentParser()
    subcommands = parser.add_subparsers(dest="command", required=True)
    train_parser = subcommands.add_parser("train")
    train_parser.add_argument("--demo", action="store_true")
    approve_parser = subcommands.add_parser("approve")
    approve_parser.add_argument("version")
    approve_parser.add_argument("--allow-demo", action="store_true")
    watch_parser = subcommands.add_parser("watch")
    watch_parser.add_argument("--seconds", type=int, default=60)
    subcommands.add_parser("rollback")
    args = parser.parse_args()
    if args.command == "train":
        print(fit(fixture(), "synthetic-demo") if args.demo else fit(experiences(), "recorded-rides"))
    elif args.command == "approve":
        print(approve(args.version, args.allow_demo))
    elif args.command == "watch":
        if args.seconds < 1:
            parser.error("--seconds must be positive")
        watch(args.seconds)
    else:
        write_json(MODELS / "active-policy.json", {"version": "baseline", "actions": BASELINE})
        print("Rolled back to baseline")


if __name__ == "__main__":
    main()
