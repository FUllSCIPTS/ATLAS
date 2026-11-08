"""DSA laboratory: reproducible algorithms, instrumentation, and graphs.
Colab: %run https://raw.githubusercontent.com/FUllSCIPTS/ATLAS/main/dsa_lab/experiments.py
Locally: python dsa_lab/experiments.py --all --output dsa_lab/results
"""
from __future__ import annotations
import argparse
import csv
import math
import random
import statistics
import time
import tracemalloc
from collections import deque
from pathlib import Path
import matplotlib.pyplot as plt

SEED = 2026

def linear_search(a, x):
    steps = 0
    for i, v in enumerate(a):
        steps += 1
        if v == x:
            return i, steps
    return -1, steps

def binary_search(a, x):
    lo, hi, steps = 0, len(a) - 1, 0
    while lo <= hi:
        mid = (lo + hi) // 2
        steps += 1
        if a[mid] == x:
            return mid, steps
        if a[mid] < x: lo = mid + 1
        else: hi = mid - 1
    return -1, steps

def bubble_sort(a):
    a = a.copy()
    comparisons = 0
    for j in range(len(a) - 1):
        swapped = False
        for i in range(len(a) - 1 - j):
            comparisons += 1
            if a[i] > a[i + 1]:
                a[i], a[i + 1] = a[i + 1], a[i]
                swapped = True
        if not swapped: break
    return a, comparisons

def insertion_sort(a):
    a = a.copy()
    comparisons = 0
    for i in range(1, len(a)):
        key, j = a[i], i - 1
        while j >= 0:
            comparisons += 1
            if a[j] <= key: break
            a[j + 1] = a[j]
            j -= 1
        a[j + 1] = key
    return a, comparisons

def merge_sort(a):
    if len(a) <= 1: return a.copy(), 0
    mid = len(a) // 2
    left, c1 = merge_sort(a[:mid])
    right, c2 = merge_sort(a[mid:])
    i = j = 0
    merged, comparisons = [], c1 + c2
    while i < len(left) and j < len(right):
        comparisons += 1
        if left[i] <= right[j]:
            merged.append(left[i]); i += 1
        else:
            merged.append(right[j]); j += 1
    return merged + left[i:] + right[j:], comparisons

def quick_sort(a):
    # Pure functional, stable three-way partition; extra memory is not in-place.
    if len(a) <= 1: return a.copy(), 0
    pivot = a[len(a) // 2]
    lt, eq, gt, comparisons = [], [], [], 0
    for x in a:
        comparisons += 1
        if x < pivot: lt.append(x)
        else:
            comparisons += 1
            if x > pivot: gt.append(x)
            else: eq.append(x)
    l, cl = quick_sort(lt); r, cr = quick_sort(gt)
    return l + eq + r, comparisons + cl + cr

def dfs(graph, start):
    seen, order, stack = set(), [], [start]
    while stack:
        node = stack.pop()
        if node in seen: continue
        seen.add(node); order.append(node)
        stack.extend(reversed(graph.get(node, [])))
    return order

def bfs(graph, start):
    seen, order, queue = {start}, [], deque([start])
    while queue:
        node = queue.popleft(); order.append(node)
        for nxt in graph.get(node, []):
            if nxt not in seen:
                seen.add(nxt); queue.append(nxt)
    return order

def dijkstra(graph, source):
    import heapq
    dist = {v: float("inf") for v in graph}
    dist[source] = 0
    heap = [(0, source)]
    while heap:
        cost, u = heapq.heappop(heap)
        if cost != dist[u]: continue
        for v, weight in graph[u]:
            if weight < 0: raise ValueError("Dijkstra needs nonnegative weights")
            if cost + weight < dist[v]:
                dist[v] = cost + weight
                heapq.heappush(heap, (dist[v], v))
    return dist

class Node:
    def __init__(self, value, nxt=None):
        self.value, self.next = value, nxt

def linked_insert_front(head, value):
    return Node(value, head)

def linked_traverse(head):
    out = []
    while head is not None:
        out.append(head.value)
        head = head.next
    return out

class BST:
    def __init__(self): self.root = None
    def insert(self, x):
        if self.root is None:
            self.root = [x, None, None]; return
        p = self.root
        while True:
            k = 1 if x < p[0] else 2
            if p[k] is None:
                p[k] = [x, None, None]; return
            p = p[k]
    def search_steps(self, x):
        p, steps = self.root, 0
        while p is not None:
            steps += 1
            if p[0] == x: return True, steps
            p = p[1 if x < p[0] else 2]
        return False, steps

def measure(func, repeat=5):
    # Median wall clock: descriptive only, not a complexity proof.
    samples = []
    for _ in range(repeat):
        t0 = time.perf_counter()
        func()
        samples.append((time.perf_counter() - t0) * 1000)
    return statistics.median(samples)

def run_experiment(name, sizes=(32, 64, 128, 256, 512), repeats=5):
    rng = random.Random(SEED)
    rows = []
    for n in sizes:
        a = list(range(n))
        shuffled = a.copy(); rng.shuffle(shuffled)
        if name == "growth":
            value = sum(range(n))
            rows.append((n, n, n * n, n * math.log2(max(n, 2))))
            continue
        if name == "search":
            _, c1 = linear_search(a, n + 1)
            _, c2 = binary_search(a, n + 1)
            rows.append((n, c1, c2, 0))
        elif name == "search_cases":
            best = linear_search(a, 0)[1]
            avg = statistics.mean(linear_search(a, x)[1] for x in a)
            worst = linear_search(a, n + 1)[1]
            rows.append((n, best, avg, worst))
        elif name == "sort":
            _, b = bubble_sort(shuffled)
            _, m = merge_sort(shuffled)
            _, q = quick_sort(shuffled)
            rows.append((n, b, m, q))
        elif name == "sort_cases":
            _, best = insertion_sort(a)
            _, average = insertion_sort(shuffled)
            _, worst = insertion_sort(list(reversed(a)))
            rows.append((n, best, average, worst))
        elif name == "runtime":
            rows.append((n, measure(lambda: linear_search(a, n + 1), repeats),
                         measure(lambda: binary_search(a, n + 1), repeats),
                         measure(lambda: merge_sort(shuffled), repeats)))
        elif name == "array_linked":
            head = None
            for v in range(n): head = linked_insert_front(head, v)
            rows.append((n, measure(lambda: [0] + a, repeats),
                         measure(lambda: linked_insert_front(head, -1), repeats),
                         measure(lambda: linked_traverse(head), repeats)))
        elif name == "stack_queue":
            rows.append((n, measure(lambda: [*range(n)].pop(), repeats),
                         measure(lambda: deque(range(n)).popleft(), repeats),
                         measure(lambda: list(range(n)).pop(0), repeats)))
        elif name == "hash":
            d = {x: x for x in a}
            rows.append((n, measure(lambda: d.get(n - 1), repeats),
                         measure(lambda: linear_search(a, n - 1), repeats),
                         measure(lambda: sorted(a), repeats)))
        elif name == "bst":
            balanced_order = []
            def preorder(v):
                if not v: return
                mid = len(v) // 2
                balanced_order.append(v[mid])
                preorder(v[:mid]); preorder(v[mid + 1:])
            preorder(a)
            balanced = BST(); skewed = BST()
            for x in balanced_order: balanced.insert(x)
            for x in a: skewed.insert(x)
            rows.append((n, balanced.search_steps(n - 1)[1],
                         skewed.search_steps(n - 1)[1], math.log2(n)))
        elif name == "graph":
            path = {i: [i + 1] if i < n - 1 else [] for i in range(n)}
            assert len(bfs(path, 0)) == len(dfs(path, 0)) == n
            rows.append((n, measure(lambda: bfs(path, 0), repeats),
                         measure(lambda: dfs(path, 0), repeats), n))
        elif name == "shortest_path":
            graph = {i: [(i + 1, 1)] if i < n - 1 else [] for i in range(n)}
            assert dijkstra(graph, 0)[n - 1] == n - 1
            rows.append((n, measure(lambda: dijkstra(graph, 0), repeats),
                         n, n * math.log2(n)))
        elif name == "recursion_dp":
            def fib_naive(k):
                return k if k < 2 else fib_naive(k - 1) + fib_naive(k - 2)
            def fib_dp(k):
                x, y = 0, 1
                for _ in range(k): x, y = y, x + y
                return x
            k = min(25, max(5, n // 16))
            assert fib_naive(k) == fib_dp(k)
            rows.append((n, measure(lambda: fib_naive(k), repeats),
                         measure(lambda: fib_dp(k), repeats), k))
        elif name == "memory":
            def peak(f):
                tracemalloc.start()
                try:
                    f()
                    return tracemalloc.get_traced_memory()[1] / 1024
                finally: tracemalloc.stop()
            rows.append((n, peak(lambda: list(range(n))),
                         peak(lambda: {x: x for x in range(n)}),
                         peak(lambda: deque(range(n)))))
        elif name == "sorting_stability":
            # Correctness invariant demonstration: repeated keys retain original order.
            data = [(x % 5, x) for x in shuffled]
            stable = sorted(data, key=lambda x: x[0])
            assert all([j for k, j in stable if k == key] ==
                       [j for k, j in data if k == key] for key in range(5))
            rows.append((n, len(stable), len(set(x[0] for x in stable)), 0))
        else: raise ValueError(f"Unknown experiment: {name}")
    return rows

EXPERIMENTS = {
    "growth": ("n", "n²", "n log₂ n"),
    "search": ("linear comparisons", "binary comparisons", "unused"),
    "search_cases": ("best", "average", "worst"),
    "sort": ("bubble comparisons", "merge comparisons", "quick comparisons"),
    "sort_cases": ("insertion best", "insertion random", "insertion worst"),
    "runtime": ("linear ms", "binary ms", "merge ms"),
    "array_linked": ("array front-insert ms", "linked front-insert ms", "linked traversal ms"),
    "stack_queue": ("list stack-pop ms", "deque left-pop ms", "list left-pop ms"),
    "hash": ("dictionary lookup ms", "linear lookup ms", "sort ms"),
    "bst": ("balanced BST steps", "skewed BST steps", "log₂ n reference"),
    "graph": ("BFS ms", "DFS ms", "vertices"),
    "shortest_path": ("Dijkstra ms", "V reference", "V log₂ V reference"),
    "recursion_dp": ("naive Fibonacci ms", "iterative DP ms", "Fibonacci input k"),
    "memory": ("list KiB", "dict KiB", "deque KiB"),
    "sorting_stability": ("records", "distinct keys", "unused"),
}
def save_plot(name, rows, output):
    labels = EXPERIMENTS[name]
    output.mkdir(parents=True, exist_ok=True)
    with (output / f"{name}.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["n", *labels])
        writer.writerows(rows)
    fig, ax = plt.subplots(figsize=(9, 5))
    for j, label in enumerate(labels):
        if label == "unused": continue
        ax.plot([r[0] for r in rows], [r[j + 1] for r in rows],
                marker="o", label=label)
    ax.set_title(f"DSA experiment: {name.replace('_', ' ')}")
    ax.set_xlabel("Input size n")
    ax.set_ylabel("Count / time (ms) / memory (KiB) — see legend")
    ax.grid(alpha=.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output / f"{name}.png", dpi=150)
    plt.close(fig)

def self_test():
    for n in (0, 1, 2, 17, 64):
        a = list(range(n))
        for fn in (bubble_sort, insertion_sort, merge_sort, quick_sort):
            assert fn(a[::-1])[0] == a
            assert fn([2, 1, 2, 0])[0] == [0, 1, 2, 2]
        assert linear_search(a, -1)[0] == -1
        assert binary_search(a, -1)[0] == -1
    assert bfs({0: [1, 2], 1: [3], 2: [], 3: []}, 0) == [0, 1, 2, 3]
    assert dfs({0: [1, 2], 1: [3], 2: [], 3: []}, 0) == [0, 1, 3, 2]
    assert dijkstra({0: [(1, 2), (2, 8)], 1: [(2, 1)], 2: []}, 0)[2] == 3
    print("All algorithm smoke tests passed.")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--experiment", choices=sorted(EXPERIMENTS))
    parser.add_argument("--output", default="dsa_lab/results")
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args()
    self_test()
    if not args.all and not args.experiment:
        parser.print_help(); return
    for name in (EXPERIMENTS if args.all else [args.experiment]):
        # Restrict quadratic experiments to a Colab-friendly scale.
        rows = run_experiment(name, repeats=max(1, args.repeats))
        save_plot(name, rows, Path(args.output))
        print(name, ":", rows[-1], "->", args.output)

if __name__ == "__main__": main()
