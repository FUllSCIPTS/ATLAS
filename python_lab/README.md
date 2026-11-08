# Python lab — 20 experiments and a testing workshop

[Course guide](../docs/PYTHON_PROGRAMMING.md) · [Open the notebook in Google Colab](https://colab.research.google.com/github/FUllSCIPTS/ATLAS/blob/main/python_lab/Python_Colab_Labs.ipynb) · [Lab source](experiments.py) · [ATLAS Go method catalogue](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/docs/ARCHITECTURE.md#complete-source-method-catalog)

Each lab runs real Python and charts what it observed. Every lab is about **its lesson's idea** — execution order, rounding, Unicode bytes, aliasing, call counts, exceptions, files, memory, comparisons, mutation testing — not a generic "value vs n" plot. All data is synthetic.

## Getting started

**Colab:** open the notebook and choose **Runtime → Run all**. The setup cell clones this repository (so the examples can import the real ATLAS Go modules), each lesson has a **Try it** cell and a **Lab** cell, and the final section writes and runs a 31-test pytest suite against ATLAS Go. Download `python_20_labs.zip` from the Files panel.

**Locally** (Python 3.10+, from the repository root):

~~~bash
python -m pip install matplotlib
python python_lab/experiments.py                  # runs every lab's assertions, then usage
python python_lab/experiments.py --list
python python_lab/experiments.py --all            # P01-P20 -> python_lab/results
python python_lab/experiments.py --experiment 6
~~~

Each lab writes `lab_NN.csv` (the observed table), `lab_NN.json` (table + title, units and notes) and `lab_NN.png` (the chart).

## Experiment register

| Lab | Lesson | What runs | What the chart shows |
|---|---|---|---|
| P01 | Execution order | a 5-line receipt program traced with `sys.settrace` | line number at each step — the loop's jump back |
| P02 | Numbers | 10-cent additions as floats and as integer cents, up to 10⁶ | absolute error (log): floats drift, cents exact |
| P03 | Types | 5 converters × 10 strings | heatmap of which conversions raise |
| P04 | Conditions | eligibility rule over a rating × distance grid | the decision table as a heatmap |
| P05 | Loops | single, nested, halving and Newton loops | iteration counts (log) |
| P06 | Unicode | six place names in four scripts | characters vs UTF-8 bytes vs UTF-16 units |
| P07 | Lists | `sys.getsizeof` while appending | over-allocation staircase |
| P08 | Collections | `Counter` over 500 synthetic rides | destination frequencies |
| P09 | Comprehensions | 5×5 Haversine matrix from one nested comprehension | distance heatmap |
| P10 | Functions | recursive `fib` vs `@lru_cache` | call counts (log) |
| P11 | Classes | `Ride` dataclass, standard and comfort | fare vs distance |
| P12 | Inheritance | `Car`, `EBike`, `Van` share `cost(km)` | polymorphic cost lines; MRO in notes |
| P13 | Exceptions | 200 messy booking records | outcome counts by exception type |
| P14 | Files | JSON vs CSV for 10–5 000 records; crash during atomic write | file sizes; previous file survives |
| P15 | Generators | list pipeline vs generator pipeline | peak memory (tracemalloc) |
| P16 | Functional style | `filter → map → sorted(key=)` over 40 drivers | top-8 scores |
| P17 | Sorting | `sorted()[:5]` vs `heapq.nsmallest(5)` with a counting `__lt__` | comparisons (log) |
| P18 | Searching | linear vs binary search for an absent key | comparisons (log) |
| P19 | Testing | 6 mutants of `fare_cents` vs a 1-test and a 5-test suite | mutants killed / survived |
| P20 | Profiling | `timeit` of `x in list` vs `x in set` | µs per test (log) — the only timing lab |

## Interpreting results

P20 (and the memory sizes in P07/P15) depend on the machine and Python version; everything else is deterministic (seed 2026). Each lab asserts its own correctness before it is charted — for example P09 asserts the matrix is symmetric, P14 that the old file survived the crash, P17 that both methods return the same five items.

**Report for each lab:** question → prediction → what the code does → table and chart → explanation of the y-axis and units → an edge case → the ATLAS Go function that uses the idea, and one difference between it and the lab code.

## Audit notes

Rebuilt in November 2026. The previous labs P01–P17 plotted arbitrary sums against n that had no connection to their lessons (P01 "print" plotted character counts; P14 "files" never wrote a file; P19 returned the constant (3, 0)), every lesson in the guide was one sentence plus a one-line snippet with a copied boilerplate paragraph, a Part II integration test (`snapshot() == snapshot()`) failed because `Cart` has no `__eq__`, inline code in Part II rendered as literal back-slashed backticks, and the notebook had no kernel metadata. All of these are fixed; every code block in the guide is now executed as part of the course checks.
