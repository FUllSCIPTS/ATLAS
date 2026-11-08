# DSA laboratory — 30 experiments

[Open the notebook in Google Colab](https://colab.research.google.com/github/FUllSCIPTS/ATLAS/blob/main/dsa_lab/DSA_Colab_Labs.ipynb) · [Course guide (24 lessons)](../docs/DATA_STRUCTURES_ALGORITHMS.md) · [All implementations](experiments.py) · [Live labs in the Architecture Explorer](https://fullscipts.github.io/ATLAS/#dsa)

## Quick start

**Colab:** open the notebook and choose **Runtime → Run all** (about a minute). Each experiment has a *See it* cell that draws or traces the structure and a *Measure it* cell that produces a chart and a CSV. Download `dsa_results.zip` from the Files panel at the end.

**Locally** (Python 3.10+):

~~~bash
python -m pip install matplotlib
python dsa_lab/experiments.py                       # runs the self-tests (70+ assert statements), then usage
python dsa_lab/experiments.py --list                # the experiment register
python dsa_lab/experiments.py --all                 # E01-E30 -> dsa_lab/results (about 10 s)
python dsa_lab/experiments.py --experiment circular_singly
python dsa_lab/experiments.py --diagrams            # PNG drawings of every linked structure
~~~

Each experiment writes `EXX_name.csv` (the numbers) and `EXX_name.png` (the chart). Seed 2026; times are medians of 5 repetitions.

## What is implemented

| Area | Classes and functions in `experiments.py` |
|---|---|
| Searching | `linear_search`, `binary_search`, `first_occurrence` |
| Sorting | `bubble_sort`, `selection_sort`, `insertion_sort`, `merge_sort`, `quick_sort` (functional), `quick_sort_inplace`, `heap_sort`, `counting_sort`, `stability_violations` |
| Arrays | `DynamicArray` (doubling / ×1.5 / fixed increment, counts copies), `row_major`, `col_major`, `row_major_3d` |
| Linked lists | `SinglyLinkedList`, `DoublyLinkedList`, **`CircularSinglyLinkedList`**, **`CircularDoublyLinkedList`** (sentinel), `josephus_circular`, `josephus_formula`, `LRUCache`, `floyd_cycle` |
| Stacks and queues | `balanced_brackets`, `evaluate_postfix`, **`RingBuffer`** (circular array) |
| Hashing | `ChainHash` (singly/doubly chains, optional resizing), `OpenAddressHash` (linear probing, tombstones) |
| Trees | `TreeNode`, `bst_insert_node`, `bst_delete`, four traversals (stack/queue and recursive), `avl_insert`, `avl_delete`, `validate_avl` |
| Heaps and tries | `MinHeap` (push, pop, O(n) heapify), `Trie` (insert, contains, starts_with, delete) |
| Graphs | `bfs`, `dfs`, `bfs_distances`, `dijkstra`, `dijkstra_path`, `topo_sort_kahn`, `topo_sort_dfs`, `UnionFind`, `kruskal` |
| Design paradigms | `fib_naive_calls`, `fib_memo_calls`, `fib_dp`, `knapsack_01`, `n_queens`, `interval_schedule` |
| Drawing | `draw_structure` (singly, doubly, circular, circular-doubly, ring-buffer), `draw_tree` |

Every structure has a `validate()` (or an equivalent check) that the experiments call after each change.

## Experiment register

| ID | `--experiment` | Question | Lesson |
|---|---|---|---|
| E01 | growth | n, n log n, n² | 2–3 |
| E02 | search | linear vs binary comparisons | 19 |
| E03 | search_cases | best / average / worst | 3 |
| E04 | sort | bubble vs merge vs quick | 20 |
| E05 | sort_cases | insertion sort and input order | 20 |
| E06 | runtime | measured search and sort time | 2 |
| E07 | array_linked | front insertion: list vs linked list | 4–5 |
| E08 | stack_queue | draining n items three ways | 9–10 |
| E09 | hash | dict vs scan vs bisect | 11 |
| E10 | bst | balanced vs skewed BST | 13 |
| E11 | graph | BFS/DFS edge examinations | 17 |
| E12 | shortest_path | Dijkstra relaxations and pushes | 18 |
| E13 | recursion_dp | Fibonacci calls | 21–22 |
| E14 | memory | traced KiB of list/dict/deque | 2 |
| E15 | sorting_stability | equal-key order violations | 20 |
| E16 | hash_singly | singly chained table | 11 |
| E17 | hash_doubly | doubly chained table with deletes | 6, 11 |
| E18 | hash_load | uniform vs adversarial keys | 11 |
| E19 | tree_stack_queue | iterative traversals | 12 |
| E20 | avl | AVL vs plain BST | 14 |
| E21 | circular_singly | Josephus problem on a circular list | 7 |
| E22 | circular_doubly | LRU cache on a circular doubly list | 8 |
| E23 | ring_buffer | ring buffer vs deque vs `pop(0)` | 10 |
| E24 | heap | heapify vs n pushes | 15 |
| E25 | trie | prefix query: trie vs scan | 16 |
| E26 | bst_delete | height after deletions, BST vs AVL | 13–14 |
| E27 | union_find | naive vs rank vs compression | 18 |
| E28 | topo_sort | Kahn vs DFS | 18 |
| E29 | open_addressing | probes vs load factor | 11 |
| E30 | dynamic_array | copies for three growth policies | 4 |

## Experimental discipline

- Compare **counts** with mathematical bounds. Compare **times** only between runs on the same machine, and read their *shape*, not their values. Every chart uses one unit on its y-axis; experiments with very different magnitudes use a log scale (stated in the axis label).
- Inputs are rebuilt **outside** the timed region (`measure_setup`).
- `tracemalloc` reports Python allocations, not total process memory.
- Pure-Python structures pay interpreter overhead that C built-ins (`list`, `deque`, `dict`, `OrderedDict`) do not. E07, E22 and E23 show both effects: constant factors win small inputs, growth rates win large ones.

## Report template

**Question → hypothesis with a predicted bound → input sizes and distribution → counted operation or timing method → chart and CSV → derivation → disagreement with theory and why → one extension.**

## Audit notes

The lab was audited and rebuilt in November 2026. Problems found in the previous version, and what changed:

| Previous problem | Fix |
|---|---|
| E08 timed `list(range(n))` construction together with one pop, so all three curves measured the same O(n) build | E08 drains all n items with the input built outside the timer |
| E09 compared dict lookup with `sorted()` on already-sorted data | E09 compares n lookups by dict, linear scan and binary search |
| E15 only tested Python's `sorted`, not the lab's own sorts | E15 counts stability violations for merge, insertion and heap sort |
| E18's "high load" keys were spread perfectly, so no real collisions occurred | E18 contrasts uniform keys with adversarial keys that all collide |
| E11–E13 plotted milliseconds and reference counts on one axis | every chart now has a single unit |
| Circular lists, ring buffers, BST deletion, heaps, tries, union-find and topological sort were described but not implemented or tested | all implemented with self-tests; E21–E30 added |
| Course guide repeated sections, mixed height conventions and had stray text | guide rewritten as 24 standalone lessons; height counts nodes throughout; BSTs store distinct keys |
| Notebook had 20 identical boilerplate cells | each experiment has a concept recap, an illustrative demo and a "what to look for" note |
