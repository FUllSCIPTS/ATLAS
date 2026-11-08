"""Python foundations laboratory: 20 experiments that each exercise one lesson.

Every lab returns a table of OBSERVED values produced by running Python, plus a
chart that shows the lesson's idea (execution order, rounding error, Unicode
bytes, memory, call counts, ...). Nothing is estimated or invented.

    python python_lab/experiments.py                 # self-tests, then usage
    python python_lab/experiments.py --all           # P01-P20 -> python_lab/results
    python python_lab/experiments.py --experiment 6  # one lab
    python python_lab/experiments.py --list

Course guide: docs/PYTHON_PROGRAMMING.md. Colab: python_lab/Python_Colab_Labs.ipynb.
Only the standard library and matplotlib are needed.
"""
from __future__ import annotations

import argparse
import csv
import functools
import heapq
import io
import json
import math
import random
import sys
import tempfile
import timeit
import tracemalloc
import unicodedata
import unittest
from collections import Counter
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

SEED = 2026


def result(number, title, kind, labels, rows, xlabel, ylabel, notes="", log=False, xticks=None):
    """kind: 'line' (x + series), 'bar' (category + series) or 'heatmap' (row label + cells)."""
    return {"number": number, "title": title, "kind": kind, "labels": list(labels), "rows": rows,
            "xlabel": xlabel, "ylabel": ylabel, "notes": notes, "log": log, "xticks": xticks}


# ----------------------------------------------------------------------------- P01
RECEIPT_PROGRAM = '''
total = 0
for km in (2, 3):
    fare = 350 + 170 * km
    total = total + fare
message = f"total {total} cents"
'''


def lab_01():
    """Execution order: record which line runs at each step (sys.settrace)."""
    code = compile(RECEIPT_PROGRAM, "<receipt>", "exec")
    steps = []

    def tracer(frame, event, arg):
        if frame.f_code.co_filename == "<receipt>" and event == "line":
            steps.append(frame.f_lineno - 1)          # program line numbers start at 1
        return tracer

    namespace = {}
    sys.settrace(tracer)
    try:
        exec(code, namespace)
    finally:
        sys.settrace(None)
    assert namespace["message"] == "total 1550 cents"
    rows = [(i + 1, line) for i, line in enumerate(steps)]
    return result(1, "Execution order of a 5-line program (loop runs twice)", "line",
                  ["line executed"], rows, "step", "program line number",
                  notes="Lines 3-4 repeat because the for-loop runs twice; line 2 is revisited to fetch the next km.")


# ----------------------------------------------------------------------------- P02
def lab_02():
    """Adding 10 cent fares as floats vs as integer cents."""
    rows = []
    for n in (10, 100, 1_000, 10_000, 100_000, 1_000_000):
        as_float = 0.0
        as_cents = 0
        for _ in range(n):
            as_float += 0.10
            as_cents += 10
        exact = Decimal(n) * Decimal("0.10")
        float_error = abs(Decimal(repr(as_float)) - exact)
        cents_error = abs(Decimal(as_cents) / 100 - exact)
        rows.append((n, float(float_error) + 1e-18, float(cents_error) + 1e-18))
    return result(2, "Accumulated rounding error: float euros vs integer cents", "line",
                  ["float euros error", "integer cents error"], rows, "number of 10-cent additions",
                  "absolute error in euros (log; 1e-18 = exact)", log=True,
                  notes="Integer cents are exact; binary floats cannot represent 0.10 exactly.")


# ----------------------------------------------------------------------------- P03
CONVERSION_INPUTS = ["42", " 7 ", "3.5", "-0", "1e3", "0x1A", "seven", "", "True", "٣"]
CONVERTERS = {"int(s)": int, "float(s)": float, "int(s, 16)": lambda s: int(s, 16),
              "bool(s)": bool, "Decimal(s)": Decimal}


def lab_03():
    """Which conversions succeed (1) or raise (0)?"""
    rows = []
    for text in CONVERSION_INPUTS:
        cells = []
        for fn in CONVERTERS.values():
            try:
                fn(text)
                cells.append(1)
            except Exception:
                cells.append(0)
        rows.append((repr(text), *cells))
    return result(3, "Type conversion: which inputs convert (1) or raise (0)", "heatmap",
                  list(CONVERTERS), rows, "converter", "input string",
                  notes="bool('') is False but bool('False') is True; int() accepts surrounding spaces and the "
                        "Arabic-Indic digit '٣'; float accepts '1e3'.")


# ----------------------------------------------------------------------------- P04
def eligible(online, rating, distance_km):
    """Example dispatch rule: online AND rating >= 4.5 AND within 5 km."""
    return online and rating >= 4.5 and distance_km <= 5


def lab_04():
    ratings = [round(3.0 + 0.25 * i, 2) for i in range(9)]          # 3.0 .. 5.0
    distances = [0, 1, 2, 3, 4, 5, 6, 7, 8]
    rows = [(f"rating {r}", *[int(eligible(True, r, d)) for d in distances]) for r in ratings]
    calls = []

    def check(label, value):
        calls.append(label)
        return value

    check("online", False) and check("rating", True) and check("distance", True)
    assert calls == ["online"]                                     # short-circuit
    return result(4, "Decision table: online AND rating>=4.5 AND distance<=5", "heatmap",
                  [f"{d} km" for d in distances], rows, "distance", "rating",
                  notes="'and' stops at the first False: with online=False only one condition is evaluated.")


# ----------------------------------------------------------------------------- P05
def newton_sqrt_iterations(x, tol=1e-12):
    guess, it = x if x > 1 else 1.0, 0
    while abs(guess * guess - x) > tol * x:
        guess = (guess + x / guess) / 2
        it += 1
    return it


def lab_05():
    rows = []
    for n in (2, 4, 8, 16, 32, 64, 128, 256):
        single = sum(1 for _ in range(n))
        nested = sum(1 for _ in range(n) for _ in range(n))
        halving, k = 0, n
        while k > 1:
            k //= 2
            halving += 1
        rows.append((n, single, nested, halving, newton_sqrt_iterations(float(n))))
    return result(5, "How many times does each loop body run?", "line",
                  ["for i in range(n)", "nested for", "while n > 1: n //= 2", "Newton sqrt while-loop"],
                  rows, "n", "iterations (log scale)", log=True)


# ----------------------------------------------------------------------------- P06
UNICODE_SAMPLES = {"Cork": "Cork", "Corcaigh (Irish)": "Corcaigh", "Baile Átha Cliath": "Baile Átha Cliath",
                   "Cork in Tamil": "கோர்க்", "Cork in Japanese": "コーク", "taxi emoji + ' ride'": "🚕 ride"}


def lab_06():
    rows = []
    for label, s in UNICODE_SAMPLES.items():          # ASCII-safe labels: chart fonts lack some scripts
        rows.append((label, len(s), len(s.encode("utf-8")), len(s.encode("utf-16-le")) // 2))
    e_nfc, e_nfd = unicodedata.normalize("NFC", "é"), unicodedata.normalize("NFD", "é")
    assert len(e_nfc) == 1 and len(e_nfd) == 2 and e_nfc != e_nfd
    assert unicodedata.normalize("NFC", e_nfd) == e_nfc
    return result(6, "Characters vs encoded size", "bar",
                  ["len(str) code points", "UTF-8 bytes", "UTF-16 code units"], rows, "text", "count",
                  notes="'é' can be 1 code point (NFC) or 2 (NFD); normalise before comparing user input.")


# ----------------------------------------------------------------------------- P07
def lab_07():
    rows, items = [], []
    for i in range(65):
        rows.append((i, sys.getsizeof(items)))
        items.append(i)
    a = [1, 2]
    b = a
    b.append(3)
    assert a == [1, 2, 3]                                          # alias
    nested = [[0], [0]]
    shallow = nested.copy()
    shallow[0].append(1)
    assert nested[0] == [0, 1]                                     # shallow copy shares rows
    return result(7, "sys.getsizeof(list) while appending: over-allocation steps", "line",
                  ["bytes for the list object"], rows, "number of items", "bytes",
                  notes="The list grows its pointer array in jumps, so most appends cost no reallocation.")


# ----------------------------------------------------------------------------- P08
def synthetic_rides(n=500, seed=SEED):
    rng = random.Random(seed)
    places = ["UCC Campus", "Cork City Centre", "Kent Station", "Cork Airport"]
    weights = [4, 6, 3, 2]
    return [{"id": i, "destination": rng.choices(places, weights)[0], "km": rng.randint(1, 10)}
            for i in range(n)]


def lab_08():
    rides = synthetic_rides()
    counts = Counter(r["destination"] for r in rides)
    morning = {r["destination"] for r in rides[:50]}
    evening = {r["destination"] for r in rides[-50:]}
    assert morning | evening >= morning & evening
    rows = [(place, c) for place, c in counts.most_common()]
    return result(8, "Counter: destinations of 500 synthetic rides", "bar", ["rides"], rows,
                  "destination", "count",
                  notes=f"set union {len(morning | evening)}, intersection {len(morning & evening)}; "
                        "tuples are hashable dict keys, lists are not.")


# ----------------------------------------------------------------------------- P09
CORK_PLACES = {"UCC": (51.8935, -8.4920), "City Centre": (51.8985, -8.4706),
               "Kent Station": (51.9018, -8.4582), "Airport": (51.8413, -8.4911),
               "Blackrock": (51.9006, -8.4026)}


def haversine_km(a, b):
    lat1, lon1, lat2, lon2 = map(math.radians, (*a, *b))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371.0088 * math.asin(math.sqrt(h))


def lab_09():
    names = list(CORK_PLACES)
    matrix = [[round(haversine_km(CORK_PLACES[a], CORK_PLACES[b]), 2) for b in names] for a in names]
    assert all(matrix[i][i] == 0 for i in range(len(names)))
    assert all(matrix[i][j] == matrix[j][i] for i in range(len(names)) for j in range(len(names)))
    rows = [(a, *row) for a, row in zip(names, matrix)]
    return result(9, "Distance matrix (km) built with a nested list comprehension", "heatmap",
                  names, rows, "to", "from", notes="Symmetric with a zero diagonal - both are asserted.")


# ----------------------------------------------------------------------------- P10
def lab_10():
    rows = []
    for k in range(1, 26, 3):
        calls = 0

        def fib(n):
            nonlocal calls
            calls += 1
            return n if n < 2 else fib(n - 1) + fib(n - 2)

        fib(k)
        naive = calls
        calls = 0

        @functools.lru_cache(maxsize=None)
        def fib_cached(n):
            nonlocal calls
            calls += 1
            return n if n < 2 else fib_cached(n - 1) + fib_cached(n - 2)

        fib_cached(k)
        rows.append((k, naive, calls))
    return result(10, "Function calls: plain recursion vs @functools.lru_cache", "line",
                  ["plain recursive calls", "cached calls"], rows, "k in fib(k)", "calls (log scale)", log=True)


# ----------------------------------------------------------------------------- P11
@dataclass(order=True)
class Ride:
    km: float
    comfort: bool = False
    tags: list = field(default_factory=list, compare=False)

    BASE_CENTS = 350
    PER_KM_CENTS = 170

    def fare_cents(self) -> int:
        cents = self.BASE_CENTS + round(self.km * self.PER_KM_CENTS)
        return cents * 130 // 100 if self.comfort else cents


def lab_11():
    rows = [(km, Ride(km).fare_cents(), Ride(km, comfort=True).fare_cents()) for km in range(1, 11)]
    assert Ride(3) == Ride(3) and Ride(2) < Ride(3)                # generated __eq__ / __lt__
    assert Ride(3).fare_cents() == 860                             # same formula as ATLAS Go domain.fare
    return result(11, "Ride dataclass: fare_cents() for standard and comfort", "line",
                  ["standard", "comfort (x1.3)"], rows, "distance km", "fare (cents)")


# ----------------------------------------------------------------------------- P12
class Vehicle:
    per_km = 0
    base = 0

    def cost(self, km):
        return self.base + self.per_km * km

    def describe(self):
        return f"{type(self).__name__}: {self.base} + {self.per_km}/km"


class Car(Vehicle):
    base, per_km = 350, 170


class EBike(Vehicle):
    base, per_km = 100, 60

    def cost(self, km):                                            # override with a range limit
        if km > 15:
            raise ValueError("e-bike range is 15 km")
        return super().cost(km)


class Van(Car):
    per_km = 220                                                   # inherits base from Car


def lab_12():
    fleet = [Car(), EBike(), Van()]
    rows = [(km, *[v.cost(km) for v in fleet]) for km in range(0, 16, 3)]
    assert [c.__name__ for c in Van.__mro__] == ["Van", "Car", "Vehicle", "object"]
    return result(12, "Polymorphism: one cost(km) call, three classes", "line",
                  [v.describe() for v in fleet], rows, "distance km", "cost (cents)",
                  notes="Van.__mro__ = Van -> Car -> Vehicle -> object.")


# ----------------------------------------------------------------------------- P13
def parse_booking(record):
    if not isinstance(record, dict):
        raise TypeError("booking must be a dict")
    try:
        km = float(record["km"])
    except KeyError:
        raise KeyError("missing km") from None
    if not 0 < km <= 200:
        raise ValueError("km out of range")
    seats = int(record.get("seats", 1))
    if not 1 <= seats <= 3:
        raise ValueError("seats out of range")
    return km, seats


def messy_records(n=200, seed=SEED):
    rng = random.Random(seed)
    makers = [lambda: {"km": rng.randint(1, 20), "seats": rng.randint(1, 3)},
              lambda: {"km": "five"}, lambda: {"seats": 2}, lambda: {"km": -3},
              lambda: {"km": 4, "seats": 9}, lambda: ["km", 4], lambda: {"km": None}]
    return [rng.choices(makers, [12, 2, 2, 1, 2, 1, 1])[0]() for _ in range(n)]


def lab_13():
    outcome = Counter()
    for rec in messy_records():
        try:
            parse_booking(rec)
            outcome["accepted"] += 1
        except (ValueError, KeyError, TypeError) as exc:
            outcome[type(exc).__name__] += 1
    rows = sorted(outcome.items(), key=lambda kv: -kv[1])
    return result(13, "Validating 200 messy booking records", "bar", ["records"], rows,
                  "outcome", "count", notes="float(None) raises TypeError; float('five') ValueError.")


# ----------------------------------------------------------------------------- P14
def atomic_write(path: Path, text: str, crash_after=None):
    """Write to a temporary file, then rename over the target (atomic on one file system)."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        f.write(text if crash_after is None else text[:crash_after])
    if crash_after is not None:
        raise OSError("simulated crash before rename")
    tmp.replace(path)


def lab_14():
    rows = []
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        for n in (10, 100, 1000, 5000):
            rides = synthetic_rides(n)
            (d / "rides.json").write_text(json.dumps(rides), encoding="utf-8")
            with (d / "rides.csv").open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=["id", "destination", "km"])
                w.writeheader()
                w.writerows(rides)
            assert json.loads((d / "rides.json").read_text(encoding="utf-8")) == rides
            back = list(csv.DictReader((d / "rides.csv").open(encoding="utf-8")))
            assert back[0]["km"] == str(rides[0]["km"])                # CSV reads back STRINGS
            rows.append((n, (d / "rides.json").stat().st_size, (d / "rides.csv").stat().st_size))
        target = d / "state.json"
        atomic_write(target, json.dumps({"rides": 1}))
        try:
            atomic_write(target, json.dumps({"rides": 2}), crash_after=5)
        except OSError:
            pass
        assert json.loads(target.read_text()) == {"rides": 1}       # old state survived the crash
    return result(14, "File size on disk: JSON vs CSV", "line", ["JSON bytes", "CSV bytes"], rows,
                  "records", "bytes", notes="A crash during atomic_write leaves the previous file intact.")


# ----------------------------------------------------------------------------- P15
def lab_15():
    rows = []
    for n in (1_000, 10_000, 50_000, 100_000):
        def eager():
            squares = [x * x for x in range(n)]
            evens = [s for s in squares if s % 2 == 0]
            return sum(evens)

        def lazy():
            squares = (x * x for x in range(n))
            evens = (s for s in squares if s % 2 == 0)
            return sum(evens)

        assert eager() == lazy()
        rows.append((n, peak_kib(eager), peak_kib(lazy)))
    return result(15, "Peak memory: list pipeline vs generator pipeline", "line",
                  ["lists (eager)", "generators (lazy)"], rows, "n", "peak KiB (tracemalloc)")


def peak_kib(fn):
    tracemalloc.start()
    try:
        fn()
        return tracemalloc.get_traced_memory()[1] / 1024
    finally:
        tracemalloc.stop()


# ----------------------------------------------------------------------------- P16
def synthetic_drivers(n=40, seed=SEED):
    rng = random.Random(seed)
    return [{"name": f"D{i:02}", "online": rng.random() < 0.7, "km": round(rng.uniform(0.2, 8), 1),
             "rating": round(rng.uniform(3.5, 5.0), 2)} for i in range(n)]


def lab_16():
    drivers = synthetic_drivers()
    online = filter(lambda d: d["online"], drivers)
    scored = map(lambda d: (d["name"], round(d["rating"] * 2 - d["km"], 2)), online)
    top = sorted(scored, key=lambda pair: pair[1], reverse=True)[:8]
    total = functools.reduce(lambda acc, d: acc + d["online"], drivers, 0)
    assert total == sum(d["online"] for d in drivers)
    return result(16, "filter -> map -> sorted(key=lambda): top 8 online drivers", "bar", ["score = 2*rating - km"],
                  top, "driver", "score", notes=f"{total} of {len(drivers)} synthetic drivers online.")


# ----------------------------------------------------------------------------- P17
class Counted:
    """Wraps a value and counts every < comparison made by sorting code."""
    comparisons = 0
    __slots__ = ("v",)

    def __init__(self, v):
        self.v = v

    def __lt__(self, other):
        Counted.comparisons += 1
        return self.v < other.v


def lab_17():
    rng = random.Random(SEED)
    rows = []
    for n in (100, 1_000, 10_000, 50_000):
        data = [Counted(rng.random()) for _ in range(n)]
        Counted.comparisons = 0
        full = sorted(data)[:5]
        c_sorted = Counted.comparisons
        Counted.comparisons = 0
        best = heapq.nsmallest(5, data)
        c_heap = Counted.comparisons
        assert [x.v for x in full] == [x.v for x in best]
        rows.append((n, c_sorted, c_heap))
    return result(17, "Top 5 of n: sorted()[:5] vs heapq.nsmallest(5)", "line",
                  ["sorted then slice", "heapq.nsmallest"], rows, "n", "comparisons (log scale)", log=True)


# ----------------------------------------------------------------------------- P18
def lab_18():
    import bisect
    rows = []
    for n in (8, 64, 512, 4096, 32768):
        a = list(range(n))
        target = n                                                 # absent: worst case
        linear = 0
        for x in a:
            linear += 1
            if x == target:
                break
        lo, hi, binary = 0, n - 1, 0
        while lo <= hi:
            mid = (lo + hi) // 2
            binary += 1
            if a[mid] == target:
                break
            lo, hi = (mid + 1, hi) if a[mid] < target else (lo, mid - 1)
        assert bisect.bisect_left(a, target) == n
        rows.append((n, linear, binary))
    return result(18, "Comparisons to search for an absent key", "line", ["linear search", "binary search"],
                  rows, "n", "comparisons (log scale)", log=True)


# ----------------------------------------------------------------------------- P19
def fare_cents(km: int, comfort: bool = False) -> int:
    if km <= 0:
        raise ValueError("distance must be positive")
    cents = 350 + 170 * km
    return cents * 130 // 100 if comfort else cents


MUTANTS = {
    "base 350 -> 300": "cents = 300 + 170 * km",
    "rate 170 -> 171": "cents = 350 + 171 * km",
    "<= becomes <": "if km < 0:",
    "comfort 130 -> 120": "return cents * 120 // 100 if comfort else cents",
    "comfort branch swapped": "return cents if comfort else cents * 130 // 100",
    "* km -> + km": "cents = 350 + 170 + km",
}


def _mutant(new_line):
    """Build a copy of fare_cents with one line replaced (chosen by its first word)."""
    import inspect
    target = {"cents": "cents = 350 + 170 * km", "if": "if km <= 0:",
              "return": "return cents * 130 // 100 if comfort else cents"}[new_line.split(" ")[0]]
    namespace = {}
    exec(inspect.getsource(fare_cents).replace(target, new_line), namespace)
    return namespace["fare_cents"]


def _suite(fn, strong):
    class T(unittest.TestCase):
        def test_typical(self):
            self.assertEqual(fn(3), 860)

    if strong:
        def test_one_km(self):
            self.assertEqual(fn(1), 520)

        def test_comfort(self):
            self.assertEqual(fn(3, comfort=True), 1118)

        def test_zero_rejected(self):
            with self.assertRaises(ValueError):
                fn(0)

        def test_standard_not_comfort(self):
            self.assertLess(fn(5), fn(5, comfort=True))

        T.test_one_km, T.test_comfort, T.test_zero_rejected, T.test_standard_not_comfort = (
            test_one_km, test_comfort, test_zero_rejected, test_standard_not_comfort)
    run = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T))
    return run.wasSuccessful()


def lab_19():
    rows = []
    for strong in (False, True):
        assert _suite(fare_cents, strong)                         # the real code passes both suites
        killed = sum(not _suite(_mutant(line), strong) for line in MUTANTS.values())
        rows.append(("1 test (weak)" if not strong else "5 tests (strong)", killed, len(MUTANTS) - killed))
    return result(19, "Mutation testing: how many deliberate bugs does each suite catch?", "bar",
                  ["mutants killed", "mutants survived"], rows, "test suite", "mutants")


# ----------------------------------------------------------------------------- P20
def lab_20():
    rows = []
    for n in (100, 1_000, 10_000, 100_000):
        as_list = list(range(n))
        as_set = set(as_list)
        probe = n - 1
        t_list = min(timeit.repeat(lambda: probe in as_list, number=200, repeat=5)) / 200 * 1e6
        t_set = min(timeit.repeat(lambda: probe in as_set, number=200, repeat=5)) / 200 * 1e6
        rows.append((n, t_list, t_set))
    return result(20, "Membership test time: list vs set (timeit, best of 5)", "line",
                  ["x in list", "x in set"], rows, "n", "microseconds per test (log scale)", log=True,
                  notes="Measured on this machine; re-run to see the variation.")


LABS = {i: globals()[f"lab_{i:02}"] for i in range(1, 21)}
TITLES = {
    1: "Program execution order", 2: "Numbers and rounding", 3: "Types and conversion",
    4: "Conditions and decision tables", 5: "Loops", 6: "Strings and Unicode", 7: "Lists, aliasing and memory",
    8: "Tuples, sets, dictionaries, Counter", 9: "Comprehensions", 10: "Functions, recursion and caching",
    11: "Classes and dataclasses", 12: "Inheritance and polymorphism", 13: "Exceptions and validation",
    14: "Files, JSON, CSV and atomic writes", 15: "Iterators and generators", 16: "Lambda, map, filter, reduce",
    17: "Sorting and selection", 18: "Searching and complexity", 19: "Testing and mutation testing",
    20: "Profiling with timeit",
}


def experiment(number):
    if number not in LABS:
        raise ValueError(f"Unknown lab: {number}")
    return LABS[number]()


def save_experiment(res, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    ident = f"lab_{res['number']:02}"
    with (out / f"{ident}.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([res["xlabel"], *res["labels"]])
        w.writerows(res["rows"])
    (out / f"{ident}.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    fig, ax = plt.subplots(figsize=(9, 5))
    rows, labels = res["rows"], res["labels"]
    if res["kind"] == "line":
        for j, label in enumerate(labels):
            ax.plot([r[0] for r in rows], [r[j + 1] for r in rows], marker="o", label=label)
        ax.legend()
    elif res["kind"] == "bar":
        width = 0.8 / len(labels)
        xs = range(len(rows))
        for j, label in enumerate(labels):
            ax.bar([x + j * width for x in xs], [r[j + 1] for r in rows], width, label=label)
        ax.set_xticks([x + width * (len(labels) - 1) / 2 for x in xs])
        ax.set_xticklabels([str(r[0]) for r in rows], rotation=20, ha="right")
        if len(labels) > 1:
            ax.legend()
    else:
        grid = [list(r[1:]) for r in rows]
        im = ax.imshow(grid, cmap="Blues", aspect="auto")
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=30, ha="right")
        ax.set_yticks(range(len(rows)))
        ax.set_yticklabels([str(r[0]) for r in rows])
        for i, row in enumerate(grid):
            for j, v in enumerate(row):
                ax.text(j, i, v, ha="center", va="center", fontsize=8,
                        color="white" if v > (max(map(max, grid)) or 1) * 0.6 else "black")
        fig.colorbar(im, ax=ax)
    if res["log"]:
        ax.set_yscale("log")
    ax.set_title(f"P{res['number']:02} - {res['title']}")
    ax.set_xlabel(res["xlabel"])
    ax.set_ylabel(res["ylabel"])
    ax.grid(alpha=.2)
    fig.tight_layout()
    fig.savefig(out / f"{ident}.png", dpi=150)
    plt.close(fig)
    return out / f"{ident}.png"


def self_test():
    assert len(LABS) == 20
    assert eligible(True, 4.5, 5) and not eligible(True, 4.4, 1) and not eligible(False, 5, 0)
    assert parse_booking({"km": "4", "seats": "2"}) == (4.0, 2)
    for bad, exc in (({"km": 0}, ValueError), ({}, KeyError), ([], TypeError), ({"km": 2, "seats": 4}, ValueError)):
        try:
            parse_booking(bad)
            raise AssertionError(f"accepted {bad}")
        except exc:
            pass
    assert Ride(1).fare_cents() == 520 and Ride(3, True).fare_cents() == 1118
    assert Car().cost(2) == 690 and Van().cost(2) == 790 and EBike().cost(2) == 220
    assert round(haversine_km(CORK_PLACES["UCC"], CORK_PLACES["Airport"]), 1) == 5.8
    assert fare_cents(3) == 860 and fare_cents(3, True) == 1118
    for n in range(1, 21):
        res = experiment(n)
        assert res["rows"] and all(len(r) == len(res["labels"]) + 1 for r in res["rows"]), n
    print("All 20 Python labs ran and their internal assertions passed.")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--experiment", type=int, choices=sorted(LABS))
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--output", default="python_lab/results")
    args = parser.parse_args()
    if args.list:
        for n, t in TITLES.items():
            print(f"P{n:02}  {t}")
        return
    self_test()
    targets = list(LABS) if args.all else [args.experiment] if args.experiment else []
    for n in targets:
        res = experiment(n)
        save_experiment(res, args.output)
        print(f"P{n:02}: {res['title']} -> {args.output}")
    if not targets:
        parser.print_help()


if __name__ == "__main__":
    main()
