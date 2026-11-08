# DSA Colab laboratory — 20 experiments

Start here: [Open notebook in Google Colab](https://colab.research.google.com/github/FUllSCIPTS/ATLAS/blob/main/dsa_lab/DSA_Colab_Labs.ipynb) · [Course guide](../docs/DATA_STRUCTURES_ALGORITHMS.md).

## Quick start
In Colab open the notebook and select **Runtime → Run all**. The notebook downloads the public experiment script from this repository; network access is required for that first step. It then runs all 20 experiments, shows charts inline, and writes CSV/PNG outputs. On a local machine: `pip install matplotlib` followed by `python dsa_lab/experiments.py --all --output dsa_lab/results`. Execute only one: `python dsa_lab/experiments.py --experiment bst`. To verify implementation: `python dsa_lab/experiments.py` (runs smoke tests then displays usage).

## Experimental discipline
- Compare **operation counts** to mathematical bounds; compare **elapsed times** only when environment/input sizes are controlled.
- Default sizes 32,64,128,256,512; fixed RNG seed 2026; timing uses median of five `perf_counter` samples. On Colab, repeated executions may vary because runtime load and allocation vary.
- Plot legends name metrics; do not interpret reference V or n log n curves as the same unit as milliseconds. Do not fit a complexity class from five points.
- Dataset precomputation may dominate tiny timings; wrap realistic workloads and report variations. `tracemalloc` reports traced Python allocations, not total process resident memory.
- List front insertion is `[0] + a` (copy), distinct from in-place `a.insert(0,x)`; both are O(n). Linked prepend creates one node and is O(1); all list creation runs before timed linked prepend.
- Basic graphs are directed path graphs, so BFS and DFS both visit all vertices. Dijkstra uses nonnegative integer weights.
- `quick_sort` is functional three-way partition, stable for equal keys but consumes extra storage; this is deliberately NOT a standard in-place quicksort and its comparison counts differ.

## Student report template
**Question → algorithm/data and precondition → input distribution → theoretical T(n)/S(n) → chart → observations → limitations → improvements.** Add CSV and PNG for each experiment. Use normalized count ratios T(2n)/T(n) on *counts*, not just noisy nanosecond measurements. Explain best, average and worst cases separately and show invariants for search/BST/graph.

## Extension code cells
In the notebook, try: (1) rerun shuffled inputs with 10 seeds and error bars; (2) choose n=1024,2048 for non-quadratic routines; (3) study n×m adjacency matrices vs adjacency lists; (4) test heaps/tries/AVL; (5) build an ATLAS-inspired ride dispatch graph.

## Advanced laboratories E16–E20

- **E16 — singly linked hash table:** bucket array + `SNode(key, value, next)`, head insertion, update, lookup and deletion. Inspect collisions using `max_chain()`.
- **E17 — doubly linked hash table:** bucket array + `DNode(key,value,prev,next)`; validate backward links after deleting head, middle, and tail.
- **E18 — load factor:** change m for n keys and compare average successful-search node comparisons; discuss α=n/m and malicious collision worst-case.
- **E19 — tree via stack/queue:** node-linked BST plus explicit stack-based inorder/preorder/postorder and queue-based level-order. Stack/queue are traversal auxiliaries, not tree storage.
- **E20 — AVL:** LL, RR, LR, RL insertion rotations, stored height and BST invariants, AVL search depths vs ascending-inserted skewed BST.

All five are executed through the same `--all` or `--experiment name` interface; they produce CSV and PNG. Use `python dsa_lab/experiments.py --experiment avl` for a focused test. The runner asserts structural invariants before plotting.
