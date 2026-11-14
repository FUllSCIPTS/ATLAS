#!/usr/bin/env python3
"""Run the 24 ATLAS machine-learning experiments: all, a few, or a study path.

    python3 ml_lab/machine_learning/run_ml.py                  # all 24 (about two minutes)
    python3 ml_lab/machine_learning/run_ml.py --list           # experiments and study paths
    python3 ml_lab/machine_learning/run_ml.py --path unsupervised
    python3 ml_lab/machine_learning/run_ml.py -e 3 -e 7

Every experiment is also a standalone file: python3 ml_lab/machine_learning/ml07_ensembles.py
"""
import argparse
import importlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from common import run  # noqa: E402

STUDY_PATHS = {
    'supervised': ('Predict a number or a class, and know when to trust it', [1, 2, 3, 4, 5, 6, 10]),
    'trees-and-ensembles': ('Rules, forests and boosting on tabular data', [6, 7, 10]),
    'neural-networks': ('From a line to a network, trained by gradient descent', [1, 3, 9]),
    'unsupervised': ('Structure and outliers without labels', [12, 13, 14, 15]),
    'time-series': ('Forecasting, honest validation and drift', [11, 16, 17]),
    'decisions': ('Ranking, bandits and reinforcement learning', [18, 19, 20]),
    'reinforcement-learning': ('From bandits to actor-critic and two agents with one critic', [19, 20, 22, 23]),
    'digital-twin': ('Mirror, foresee, rehearse, guard - then learn as a closed loop (ATLAS Go 1.3-1.4)', [21, 16, 24]),
    'multi-agent': ('Actor and critic networks, then two agents sharing one critic (MAPPO)', [22, 23]),
    'lstm-and-rl': ('Forecast, act, record, update and validate: LSTM + RL as one loop', [16, 17, 20, 24]),
    'trustworthy-ml': ('Overfitting, imbalance, leakage and drift', [2, 10, 11, 17]),
    'full': ('Every experiment in order', list(range(1, 25))),
}


def experiments():
    found = {}
    for path in sorted(HERE.glob('ml[0-9][0-9]_*.py')):
        found[int(path.name[2:4])] = path.stem
    return found


def main():
    exps = experiments()
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('-e', '--experiment', type=int, action='append', choices=sorted(exps), metavar='N')
    parser.add_argument('-p', '--path', choices=sorted(STUDY_PATHS))
    parser.add_argument('-l', '--list', action='store_true')
    args = parser.parse_args()
    if args.list:
        for n, stem in exps.items():
            doc = importlib.import_module(stem).__doc__.strip().split('\n')[0]
            print(f'  {doc}')
        print('\nStudy paths (--path NAME)')
        for name, (purpose, steps) in STUDY_PATHS.items():
            print(f'  {name:<20} {purpose}: {" -> ".join(map(str, steps))}')
        return
    numbers = STUDY_PATHS[args.path][1] if args.path else (args.experiment or sorted(exps))
    for n in numbers:
        module = importlib.import_module(exps[n])
        run(module.main, module.__doc__)


if __name__ == '__main__':
    main()
