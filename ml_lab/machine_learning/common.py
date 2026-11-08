"""Shared helpers for the ATLAS machine-learning experiments (ml01_*.py ... ml20_*.py).

Each experiment is its own file and runs on its own:

    python3 ml_lab/machine_learning/ml03_logistic_regression.py

`run_ml.py` in this folder lists them, runs them all, or runs a study path. The data are ATLAS's own:
the labelled telemetry and the eight-day traffic trace in data.zip, the paper's traffic and telemetry
generators in atlas_sim.zip, and the ATLAS Go learners and Cork geography in android-app/.
Needs numpy, scipy and scikit-learn (requirements.txt); PyTorch is not needed.
"""
from __future__ import annotations

import csv
import io
import sys
import time
import zipfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'atlas_sim.zip'))       # the paper's simulator package, imported from the zip
sys.path.insert(1, str(ROOT / 'android-app'))         # ATLAS Go (atlas_go) and its training code

FEATURES = ['rps', 'cpu_pct', 'mem_pct', 'latency_ms', 'error_rate', 'queue_depth', 'net_MBps', 'disk_ms']
BASIC = [0, 1, 2]        # what a basic host monitor sees: requests/s, CPU %, memory %
CATEGORIES = ['normal', 'cpu_exhaustion', 'memory_queue_exhaustion', 'downstream_failure',
              'request_flood', 'network_disk_delay']


def heading(title: str) -> None:
    print('\n' + '=' * 78)
    print(title)
    print('=' * 78)


def note(text: str) -> None:
    print(f'  -> {text}')


def show(label: str, value) -> None:
    print(f'  {label:<38} {value}')


def table(header, rows, widths=None) -> None:
    widths = widths or [max(len(str(h)), *(len(str(r[i])) for r in rows)) for i, h in enumerate(header)]
    print('  ' + '  '.join(f'{h:>{w}}' for h, w in zip(header, widths)))
    for r in rows:
        print('  ' + '  '.join(f'{v:>{w}}' for v, w in zip(r, widths)))


def _csv(member: str) -> list[dict]:
    with zipfile.ZipFile(ROOT / 'data.zip') as z:
        return list(csv.DictReader(io.TextIOWrapper(z.open(member), encoding='utf-8')))


def load_anomaly():
    """data/anomaly_data.csv: 10,000 telemetry rows, 8 features, label (0/1) and one of 6 categories."""
    rows = _csv('data/anomaly_data.csv')
    X = np.array([[float(r[f]) for f in FEATURES] for r in rows])
    y = np.array([int(r['label']) for r in rows])
    cat = np.array([CATEGORIES.index(r['category']) for r in rows])
    return X, y, cat


def load_trace():
    """data/traffic_trace_excerpt.csv: 8 days of per-minute telemetry from the paper's e-commerce trace."""
    rows = _csv('data/traffic_trace_excerpt.csv')
    return {k: np.array([float(r[k]) for r in rows]) for k in ['minute'] + FEATURES}


def traffic(days: int = 28, seed: int = 0, **kw):
    """The paper's e-commerce load generator (atlas_sim/traffic.py): requests/s per minute."""
    from atlas_sim.traffic import ecommerce_trace
    r, mask, events = ecommerce_trace(days=days, seed=seed, **kw)
    return r.astype(float), mask, events


def telemetry(r, seed: int = 12345, anomaly=None):
    """Paper telemetry for load r. Use a seed different from the trace seed: two default_rng(s)
    streams with the same s draw the same normals, which would correlate the noise with the load."""
    from atlas_sim.traffic import telemetry as _t
    return _t(r, np.random.default_rng(seed), anomaly=anomaly)


def split(n: int, test: float = 0.3, seed: int = 0):
    idx = np.random.default_rng(seed).permutation(n)
    k = int(n * (1 - test))
    return idx[:k], idx[k:]


def standardise(train, *others):
    mu, sd = train.mean(0), train.std(0) + 1e-12
    return [(a - mu) / sd for a in (train, *others)]


def run(main, doc: str) -> None:
    """Print an experiment's title and run it; used by every ml*.py file and by run_ml.py."""
    heading(doc.strip().split('\n')[0])
    start = time.perf_counter()
    main()
    print(f'  ({time.perf_counter() - start:.1f} s)')
