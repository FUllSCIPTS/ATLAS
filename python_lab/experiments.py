"""ATLAS Python foundations: 20 beginner-to-intermediate reproducible labs.

Each lab returns a metric table (not fabricated observations). Measurements of
runtime/memory are explicitly tagged; operation counts are derived from code.
Run: python python_lab/experiments.py --all --output python_lab/results
Dependencies: matplotlib (Colab includes it).
"""
from __future__ import annotations
import argparse
import csv
import json
import math
import random
import statistics
import time
import tracemalloc
from collections import Counter, deque
from dataclasses import dataclass
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SEED = 2026

def time_ms(action, repeats=7):
    values = []
    for _ in range(repeats):
        start = time.perf_counter()
        action()
        values.append((time.perf_counter() - start)*1000)
    return statistics.median(values)

def peak_kib(action):
    tracemalloc.start()
    try:
        action()
        return tracemalloc.get_traced_memory()[1]/1024
    finally:
        tracemalloc.stop()

def lab_01(n):
    # Printing is IO-bound, so compare exact output characters without printing.
    greetings = ["Hello, learner!"]*n
    return len(greetings), sum(len(x) for x in greetings)

def lab_02(n):
    a = [i for i in range(n)]
    return sum(a), sum(i*i for i in a)

def lab_03(n):
    values = [i for i in range(n)]
    return len(values), sum(x for x in values if x % 2 == 0)

def lab_04(n):
    values = list(range(n))
    return sum(1 for x in values if x % 3 == 0), sum(1 for x in values if x % 5 == 0)

def lab_05(n):
    def count_up(k):
        return list(range(k))
    x = count_up(n)
    return len(x), sum(x)

def lab_06(n):
    # Return counts of characters and words for a generated text.
    text = "Python is readable. "*n
    return len(text), len(text.split())

def lab_07(n):
    a = list(range(n))
    return len(a), len(a[::2])

def lab_08(n):
    # tuples are immutable, sets remove duplicates, dict maps keys to values.
    items = [i % 10 for i in range(n)]
    return len(set(items)), len({i: i*i for i in items})

def lab_09(n):
    # A loop visits n elements; Python comprehensions express the same transform.
    a = list(range(n))
    via_loop = []
    for x in a:
        via_loop.append(x*x)
    via_comp = [x*x for x in a]
    assert via_loop == via_comp
    return len(via_loop), sum(via_comp)

def lab_10(n):
    def multiples(bound, factor=3):
        return [x for x in range(bound) if x % factor == 0]
    return len(multiples(n)), len(multiples(n, 4))

def lab_11(n):
    @dataclass
    class Ride:
        distance_km: float
        rate: float = 2.0
        def fare(self):
            return self.distance_km*self.rate
    rides = [Ride(float(i)) for i in range(n)]
    return len(rides), sum(r.fare() for r in rides)

def lab_12(n):
    class Parent:
        def describe(self): return "ride"
    class Shared(Parent):
        def describe(self): return "shared ride"
    items = [Shared() if i % 2 else Parent() for i in range(n)]
    return sum(x.describe() == "ride" for x in items), sum(x.describe() == "shared ride" for x in items)

def lab_13(n):
    # Deliberately generated corrupt entries test controlled exceptions.
    bad = 0
    for i in range(n):
        try:
            int("invalid" if i % 5 == 0 else str(i))
        except ValueError:
            bad += 1
    return n-bad, bad

def lab_14(n):
    # JSON supports interoperable primitive structures.
    payload = {"rides":[{"id":i,"km":i/10} for i in range(n)]}
    import json
    text = json.dumps(payload)
    assert json.loads(text) == payload
    return len(text), len(payload["rides"])

def lab_15(n):
    # Reproducible generator outputs and memory.
    def squares():
        for x in range(n):
            yield x*x
    g = squares()
    values = list(g)
    return len(values), sum(values)

def lab_16(n):
    # Functional transform/filter/reduce pattern.
    a = list(range(n))
    squares = list(map(lambda x: x*x, a))
    kept = list(filter(lambda x: x % 2 == 0, squares))
    return len(squares), len(kept)

def lab_17(n):
    # Stable sorting and comprehensions, useful for driver scoring.
    rng = random.Random(SEED+n)
    pairs = [(rng.randrange(0,10), i) for i in range(n)]
    ranked = sorted(pairs, key=lambda p: p[0], reverse=True)
    assert all(ranked[i][0] >= ranked[i+1][0] for i in range(len(ranked)-1))
    return len(ranked), len(set(score for score, _ in ranked))

def lab_18(n):
    # Exact operation counts: linear scan and halving a sorted interval.
    a = list(range(n))
    target = n + 1
    linear_checks = 0
    for item in a:
        linear_checks += 1
        if item == target: break
    lo,hi, binary_checks = 0,n-1,0
    while lo <= hi:
        mid = (lo+hi)//2
        binary_checks += 1
        if a[mid] == target: break
        if a[mid] < target: lo = mid+1
        else: hi=mid-1
    return linear_checks, binary_checks

def lab_19(n):
    # An actual test suite can compare behavior before profiling.
    def add(a,b): return a+b
    assert add(n,0) == n
    assert add(-n,n) == 0
    assert add(2,3) == 5
    return 3, 0

def lab_20(n):
    # Compare actual timed list vs dictionary retrieval on same prebuilt data.
    a = list(range(n))
    d = {x:x for x in a}
    assert a[-1] == d[n-1] if n else True
    return time_ms(lambda: (n-1) in a), time_ms(lambda: (n-1) in d)

LABS = {
 1: ("Printing and variables",lab_01,("items","characters"),"count"),
 2: ("Numbers and operators",lab_02,("sum","sum_of_squares"),"count"),
 3: ("Types and conversion",lab_03,("list_items","even_values_sum"),"count"),
 4: ("Conditionals",lab_04,("multiples_of_three","multiples_of_five"),"count"),
 5: ("For loops and while loops",lab_05,("iterations","sum"),"count"),
 6: ("Strings and Unicode",lab_06,("characters","words"),"count"),
 7: ("Lists and slicing",lab_07,("all_items","every_other_item"),"count"),
 8: ("Tuples sets and dictionaries",lab_08,("unique_items","mapping_items"),"count"),
 9: ("Comprehensions",lab_09,("items_processed","sum_of_squares"),"count"),
10: ("Functions and parameters",lab_10,("divisible_by_three","divisible_by_four"),"count"),
11: ("Classes and dataclasses",lab_11,("ride_objects","total_fare"),"count"),
12: ("Inheritance and polymorphism",lab_12,("solo_objects","shared_objects"),"count"),
13: ("Exceptions and validation",lab_13,("valid_values","rejected_values"),"count"),
14: ("JSON serialization",lab_14,("json_characters","saved_records"),"count"),
15: ("Iterators and generators",lab_15,("yielded_items","squares_sum"),"count"),
16: ("Map filter lambda",lab_16,("mapped_items","filtered_items"),"count"),
17: ("Sorting and ranking",lab_17,("ranked_items","distinct_scores"),"count"),
18: ("Algorithmic complexity",lab_18,("linear_comparisons","binary_comparisons"),"operations"),
19: ("Testing with assertions",lab_19,("passing_assertions","failing_assertions"),"count"),
20: ("Profiling performance",lab_20,("list_membership_ms","dict_membership_ms"),"measured_ms"),
}
SIZES=(16,32,64,128,256)

def experiment(number, sizes=SIZES):
    if number not in LABS:
        raise ValueError(f"Unknown lab: {number}")
    title, fn, names, unit = LABS[number]
    rows=[]
    for n in sizes:
        a,b=fn(n)
        assert isinstance(a,(float,int)) and isinstance(b,(float,int))
        rows.append({"n":n,names[0]:a,names[1]:b})
    return {"number":number,"title":title,"labels":names,"unit":unit,"rows":rows}

def save_experiment(result, out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    ident=f"lab_{result['number']:02}"
    with (out/f"{ident}.csv").open("w",newline="",encoding="utf8") as f:
        writer=csv.DictWriter(f,fieldnames=["n",*result["labels"]])
        writer.writeheader(); writer.writerows(result["rows"])
    (out/f"{ident}.json").write_text(json.dumps(result,indent=2),encoding="utf8")
    fig,ax=plt.subplots(figsize=(8,4.5))
    for field in result["labels"]:
        ax.plot([r["n"] for r in result["rows"]],[r[field] for r in result["rows"]],
                marker="o",label=field)
    ax.set(xlabel="Input size n",ylabel=result["unit"],title=f"Python {ident}: {result['title']}")
    ax.grid(alpha=.2);ax.legend()
    fig.tight_layout();fig.savefig(out/f"{ident}.png",dpi=150);plt.close(fig)
    return out/f"{ident}.png"

def self_test():
    assert len(LABS)==20
    assert lab_01(3)==(3,45)
    assert lab_04(10)==(4,2)
    assert lab_08(100)==(10,10)
    assert lab_12(4)==(2,2)
    assert lab_13(10)==(8,2)
    assert lab_18(100)[0]==100
    assert lab_18(100)[1] <= 8
    for number in LABS:
        result=experiment(number,(16,32))
        assert len(result["rows"])==2
    print("All 20 Python lab smoke tests passed")

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all",action="store_true")
    parser.add_argument("--experiment",type=int,choices=sorted(LABS))
    parser.add_argument("--output",default="python_lab/results")
    args=parser.parse_args()
    self_test()
    for number in (LABS if args.all else ([args.experiment] if args.experiment else [])):
        result=experiment(number)
        save_experiment(result,args.output)
        print(f"P{number:02}: {result['title']} -> {args.output}")
    if not args.all and not args.experiment:
        parser.print_help()

if __name__=="__main__":
    main()
