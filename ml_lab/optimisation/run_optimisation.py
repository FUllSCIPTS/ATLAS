#!/usr/bin/env python3
"""Run the 20 ATLAS optimisation experiments: all, a few, or a study path.

    python3 ml_lab/optimisation/run_optimisation.py                  # all 20 (about 20 s)
    python3 ml_lab/optimisation/run_optimisation.py --list           # experiments and study paths
    python3 ml_lab/optimisation/run_optimisation.py --path metaheuristics
    python3 ml_lab/optimisation/run_optimisation.py -e 3 -e 7

Every experiment is also a standalone file: python3 ml_lab/optimisation/opt17_genetic_algorithm.py
"""
import argparse
import importlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from common import run  # noqa: E402

STUDY_PATHS = {
    'continuous': ('Gradients, curvature and constraints', [1, 2, 3, 4]),
    'linear-and-integer': ('LP, duality, dynamic programming and branch-and-bound', [5, 6, 7, 8]),
    'graphs-and-routing': ('Paths, matching, tours, packing and flows', [9, 10, 11, 12, 13]),
    'dynamic-programming': ('Bellman\'s principle in three settings', [7, 11, 14]),
    'metaheuristics': ('Local search, tabu, annealing and evolution', [15, 16, 17, 18]),
    'black-box-tuning': ('Optimising when you can only evaluate', [17, 18, 19]),
    'atlas-coupling': ('The paper\'s coupling decision from every angle', [8, 15, 17, 20]),
    'full': ('Every experiment in order', list(range(1, 21))),
}


def experiments():
    found = {}
    for path in sorted(HERE.glob('opt[0-9][0-9]_*.py')):
        found[int(path.name[3:5])] = path.stem
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
