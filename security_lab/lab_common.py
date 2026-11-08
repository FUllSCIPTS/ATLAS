"""Shared helpers for the ATLAS Go security labs in this folder.

Every lab_*.py file imports this module. It puts android-app/ on the import path so the labs drive the
app's real code (atlas_go.accounts and atlas_go.store), keeps one registry of numbered experiments, and
provides the command-line runner shared by each lab file and by password_storage_demo.py.
"""
from __future__ import annotations

import argparse
import importlib
import statistics
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'android-app'))

from atlas_go import accounts as acc  # noqa: E402,F401  (re-exported to the lab files)
from atlas_go.store import LocalStore  # noqa: E402

PASSWORD = 'cork2026'
EXPERIMENTS: dict[int, tuple[str, str, object]] = {}

GROUPS = {
    'A': ('What the app stores', 'lab_a_password_storage'),
    'B': ('Registration and identity', 'lab_b_registration_identity'),
    'C': ('Sign-in defences', 'lab_c_signin_defences'),
    'D': ('Integrity, sessions and lifecycle', 'lab_d_integrity_lifecycle'),
}

STUDY_PATHS = {
    'foundations': ('First lesson: what is stored and why', [1, 2, 3, 7, 8]),
    'attacker': ('Think like an attacker who stole the file or hammers the login', [4, 5, 6, 13, 14, 15]),
    'defender': ('Controls the app applies at registration and sign-in', [9, 10, 11, 12, 13, 16]),
    'integrity': ('Keeping the stored data trustworthy', [8, 17, 18, 19]),
    'lifecycle': ('Follow one user from sign-up to deletion', [9, 1, 12, 16, 19, 20]),
    'full': ('Every experiment in order', list(range(1, 21))),
}


# --------------------------------------------------------------------------- helpers
def experiment(number: int, group: str, title: str):
    def register(fn):
        EXPERIMENTS[number] = (group, title, fn)
        return fn
    return register


def heading(number: int, title: str) -> None:
    print('\n' + '=' * 78)
    print(f'Experiment {number:>2}: {title}')
    print('=' * 78)


def note(text: str) -> None:
    print(f'  -> {text}')


def attempt(label: str, fn, *args, **kwargs):
    """Run an app call and print either its result or the exact message the user would see."""
    try:
        result = fn(*args, **kwargs)
        print(f'  {label:<44} OK    {result!r}' if result is not None else f'  {label:<44} OK')
        return result
    except ValueError as error:
        print(f'  {label:<44} REJECTED  "{error}"')
        return None


@contextmanager
def workspace():
    with tempfile.TemporaryDirectory(prefix='atlas-lab-') as folder:
        yield Path(folder)


def new_store(folder: Path) -> LocalStore:
    return LocalStore(folder / 'state.json')


def register_passenger(store: LocalStore, name='Aoife Murphy', email='aoife@example.ie',
                       phone='087 123 4567', password=PASSWORD, now=None) -> dict:
    return store.register('passenger', name, email, phone, password, now=now)


def register_driver(store: LocalStore, email='ciaran@example.ie') -> dict:
    return store.register('driver', 'Ciaran Walsh', email, '086 555 0101', 'Driver2026',
                          vehicle='Electric hatchback', plate='231-C-4567', licence='IE12345', seats='4', base=1)


def register_seller(store: LocalStore, email='niamh@example.ie') -> dict:
    return store.register('seller', 'Niamh Byrne', email, '085 444 0202', 'Kitchen2026',
                          kitchen='Lab Test Kitchen', cuisine='Irish', registration='IE-123456', place=1, prep='20')


def timed(fn, repeat=5) -> float:
    samples = []
    for _ in range(repeat):
        start = time.perf_counter()
        fn()
        samples.append(time.perf_counter() - start)
    return statistics.median(samples)


def human(seconds: float) -> str:
    for unit, size in (('years', 31_557_600), ('days', 86_400), ('hours', 3600), ('minutes', 60)):
        if seconds >= size:
            return f'{seconds / size:,.1f} {unit}'
    return f'{seconds:.2f} seconds'


# --------------------------------------------------------------------------- runner
def load_all() -> None:
    """Import every lab file so all 20 experiments are registered (study paths cross categories)."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    for _, module in GROUPS.values():
        importlib.import_module(module)


def list_experiments(groups=None, paths: bool = True) -> None:
    for group, (title, module) in GROUPS.items():
        if groups and group not in groups:
            continue
        print(f'\n{group}. {title}  (security_lab/{module}.py)')
        for number, (g, name, _) in sorted(EXPERIMENTS.items()):
            if g == group:
                print(f'  {number:>2}. {name}')
    if paths:
        print('\nStudy paths (password_storage_demo.py --path NAME)')
        for name, (purpose, steps) in STUDY_PATHS.items():
            print(f'  {name:<12} {purpose}: {" -> ".join(map(str, steps))}')


def run(numbers) -> None:
    for number in numbers:
        _, title, fn = EXPERIMENTS[number]
        heading(number, title)
        with workspace() as folder:
            fn(folder)


def main(argv=None, group: str | None = None, description: str = '') -> None:
    """Command line shared by every lab. group='A' offers only that lab's experiments; group=None loads
    all four lab files and adds --path for the cross-category study paths."""
    if group is None:
        load_all()
    own = sorted(n for n, (g, _, _) in EXPERIMENTS.items() if group in (None, g))
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-e', '--experiment', type=int, action='append', choices=own,
                        metavar='N', help=f'run experiment N (repeatable; {own[0]}-{own[-1]})')
    parser.add_argument('-l', '--list', action='store_true', help='list experiments')
    if group is None:
        parser.add_argument('-p', '--path', choices=sorted(STUDY_PATHS), help='run a study path')
    args = parser.parse_args(argv)
    if args.list:
        list_experiments([group] if group else None, paths=group is None)
        return
    if group is None and args.path:
        purpose, numbers = STUDY_PATHS[args.path]
        print(f'Study path "{args.path}": {purpose}')
    else:
        numbers = args.experiment or own
    run(numbers)
    print('\nDone. Guide: docs/INFORMATION_SECURITY.md')
