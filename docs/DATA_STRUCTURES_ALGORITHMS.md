# Data Structures and Algorithms — foundations to experimental analysis

**Course format:** 15 teaching weeks · 2 h theory + 2 h lab weekly · Python 3 / Google Colab. **Audience:** complete beginners through intermediate students. This is an independent course; it does not assert that ATLAS deploys every algorithm.

## Outcomes
Explain algorithms and abstract data types (ADTs); derive operation counts and asymptotic bounds; distinguish time from auxiliary space; implement linear and non-linear structures; test correctness and invariants; profile repeatably in Colab; interpret charts instead of mistaking an empirical curve for a proof.

## 1. Foundations: from problem to algorithm
A **problem** maps input to required output; an **algorithm** is a finite, unambiguous sequence of steps that solves it. A **data structure** organizes values and operations; an **ADT** specifies behavior independent of representation. Example: a ride queue supports enqueue/dequeue (ADT); Python deque is one implementation. Compare input size n (number of records), operations, preconditions, outputs, termination, and edge cases. Python lists are dynamic arrays; a Python dictionary is a hash table; a queue should use collections.deque rather than list.pop(0).

**Mini-example:** Find 7 in [2, 7, 9]. Linear search compares until it matches (2 comparisons); binary search requires a sorted list and halves the remaining interval. Keep a running count of comparisons; clock time is a different measurement.

## 2. How computational complexity is measured
1. Define input size n and the basic operation (comparison, swap, hash probe, node visit).
2. Define T(n) as the total count; analyze **best**, **expected/average** (state a probability distribution), and **worst** cases separately.
3. For sequential loops, add counts; nested loops multiply counts when independent; for a triangular loop use 1+2+...+(n−1) = n(n−1)/2.
4. For recursion, write a recurrence: binary search T(n)=T(n/2)+O(1), merge sort T(n)=2T(n/2)+O(n).
5. Bound T(n) asymptotically, then separately measure runtime via time.perf_counter and repeat/median, and peak allocations via tracemalloc. Label machine and Python version, dataset, sample size, seed and units.
6. Use theory for scalability; measured timings may be distorted by allocation, cache, interpreter overhead and noise. A wall-clock chart cannot prove Big-O.

## 3. The three asymptotic notations
- **Big O**: f(n)=O(g(n)) if ∃c>0,n₀ such that 0≤f(n)≤c·g(n) for all n≥n₀. Asymptotic *upper bound*, not inherently worst-case.
- **Big Ω**: f(n)=Ω(g(n)) if ∃c>0,n₀ such that 0≤c·g(n)≤f(n) for all n≥n₀. Asymptotic *lower bound*, not inherently best-case.
- **Big Θ**: f(n)=Θ(g(n)) when both hold; a *tight bound*.
Example: f(n)=3n²+5n+8 has O(n²), Ω(n²), and Θ(n²). It is ALSO O(n³), but not Θ(n³). O(1), O(log n), O(n), O(n log n), O(n²), O(2ⁿ) describe growth orders, not seconds.

**Cases:** Linear search successful first element Θ(1), unsuccessful Θ(n), uniformly random successful index expected Θ(n). Binary search on sorted random-access array is worst-case Θ(log n), best Θ(1). Dictionary average expected lookup O(1) under hashing assumptions, but worst-case O(n). Insertion sort best Θ(n), worst Θ(n²). A balanced BST has Θ(log n) lookup, a skewed BST Θ(n).

**Time vs space:** merge sort uses O(n) auxiliary array space; in-place insertion sort O(1) auxiliary space. Recursion stack counts as space. Python slices/concatenations add allocations: the illustrative quick_sort lab is NOT an in-place implementation.

## 4. Linear data structures
**Array / dynamic array:** indexed access O(1), append amortized O(1), front insertion O(n). Row-major 2D array index for A[R][C] is i·C+j; for 3D A[X][Y][Z], index (i·Y+j)·Z+k. Strides and actual memory layout matter.
**Linked list:** node(value,next), prepend O(1), index lookup O(n); doubly linked lists additionally allow backward links.
**Stack (LIFO):** last parked car leaves first; push/pop O(1) amortized using a Python list.
**Queue (FIFO):** passengers served in arrival order; append/popleft O(1) using deque.
**Deque:** O(1) inserts/removals at both ends; **hash table:** key-value mapping, expected O(1) operations, collision handling and load factor.

**Building a hash table with linked lists (separate chaining):** Create an array of m bucket heads; map a key to bucket `hash(key) % m`; traverse the linked nodes to update or find a matching key; prepend a new key-value node if absent. **Singly linked chains** have (key,value,next); **doubly linked chains** additionally maintain prev, enabling removal of a known node in O(1) once a reference is available (finding by key still costs O(chain length)). Both allow insertion at head O(1) excluding duplicate scan; lookup/delete are O(1+α) expected under uniform hashing, α=n/m, and O(n) worst-case. The lab deliberately uses a fixed bucket count and deterministic integer keys to visualize collisions; production tables resize and must account for hash-quality/security tradeoffs. See E16–E18.

**Strings:** immutable sequences in Python; slicing and concatenation costs depend on length.

## 5. Non-linear data structures

**Implementing a tree using stack and queue:** A tree itself is represented by linked nodes (key, left, right), not *stored* in a stack or queue. A **stack** is an auxiliary LIFO structure for iterative depth-first traversals: inorder pushes the left spine, visits, then explores right; preorder pushes right before left; postorder uses a visited flag. A **queue** is an auxiliary FIFO structure for breadth-first/level-order traversal, enqueuing children after visiting their parent. Both visit each node once: O(n) time; auxiliary memory O(h) for depth-first (except the illustrated postorder may use O(h) entries) and O(w) for breadth-first where h=height and w=maximum width, with result list O(n) excluded from auxiliary space.

**AVL trees:** A self-balancing BST that keeps |height(left)−height(right)| ≤ 1 at each node. Update heights after insertion, then fix imbalance with **LL** (single right rotation), **RR** (single left), **LR** (left then right), or **RL** (right then left). Insert and lookup are O(log n) for n distinct keys; duplicates are ignored in the pedagogical lab. Tree rotations modify links without changing sorted inorder order. Compare ascending insertions into a plain BST (height n) against AVL (height O(log n)). See implementations in `dsa_lab/experiments.py`.


**Tree:** root, parent, child, leaf, height; binary tree vs binary search tree (BST left < node, right ≥ node), traversals preorder/inorder/postorder/level order. AVL and red-black trees keep height logarithmic; heaps implement priority queues (push/pop O(log n)).
**Trie:** prefix search in O(L) where L is key length, under fixed-cost child access; often a memory tradeoff.
**Graph:** V vertices and E edges; directed/undirected, weighted/unweighted; adjacency lists use O(V+E), adjacency matrices O(V²). BFS and DFS O(V+E); BFS finds shortest paths by edge count in unweighted graphs. Dijkstra with a binary heap is O((V+E) log V) under usual assumptions and requires nonnegative weights. Topological sorting applies only to DAGs.
**Union-find:** near-constant amortized operations O(α(n)) with compression + rank.

## 6. Algorithms, paradigms and correctness
Searching: linear vs binary (sorted precondition). Sorting: bubble, insertion, merge, quick, heap; compare stability, worst-case, auxiliary storage and input distribution. Recursion: base case, shrinking problem, stack. Divide/conquer (merge sort), greedy (interval scheduling), dynamic programming (Fibonacci, knapsack), backtracking (subsets). For correctness, write preconditions, postconditions, loop invariants and termination arguments. For example, at each binary-search iteration, if x occurs it lies in [lo,hi]; interval shrinks.

## 7. 15-week teaching sequence

| Week | Teaching (2 h) | Colab lab (2 h) | Deliverable |
|---|---|---|---|
| 1 | Python, algorithms, ADTs | Environment, basic counters, experiment growth | Definitions and first chart |
| 2 | Counts and input size | search and search_cases | Cases table |
| 3 | O, Ω, Θ; recurrences | growth + runtime | Bound derivations |
| 4 | Arrays, 2D/3D indexing | array_linked | Index formula, timings |
| 5 | Linked lists | array_linked, node invariants | Implementation |
| 6 | Stacks and queues | stack_queue | Correct API selection |
| 7 | Hashing, collision, load | hash, hash_singly, hash_doubly, hash_load | Collision-chain analysis |
| 8 | Sorting basics | sort_cases | Comparisons and cases |
| 9 | Divide and conquer sorts | sort, sorting_stability | Proof of stability |
| 10 | Binary trees, stack/queue traversals and BSTs | bst, tree_stack_queue | Balanced vs skewed chart |
| 11 | AVL rotations, heaps and tries | avl; implement heapq and prefix query | AVL invariants and rotations |
| 12 | Graph representations | graph | BFS/DFS visit sequence |
| 13 | Weighted paths, DAGs | shortest_path | Shortest-path verification |
| 14 | Recursion and DP | recursion_dp, memory | Speed-space analysis |
| 15 | Review and applications | repeat labs + mini-project | Research-style report |

## 8. Laboratory protocol and 20 experiments

Run the self-contained [Colab notebook](../dsa_lab/DSA_Colab_Labs.ipynb), or run the [Python runner](../dsa_lab/experiments.py) and consult the [lab manual](../dsa_lab/README.md). Every experiment exports a CSV and PNG chart (except additional in-notebook conceptual examples), with fixed seed 2026. All charts are exploratory; some pair reference counts and measured times: do not compare unlike units numerically.

| ID | Experiment | Hypothesis / variable | Recorded output |
|---|---|---|---|
| E01 | growth | n, n log n, n² expand differently | theoretical operation count |
| E02 | search | linear vs binary on sorted data | comparisons |
| E03 | search_cases | linear first/random/absent | best/mean/worst comparisons |
| E04 | sort | bubble vs merge vs functional quick | comparisons |
| E05 | sort_cases | insertion sorted/random/reverse | comparisons |
| E06 | runtime | linear/binary/merge | median ms |
| E07 | array_linked | array and linked insertion/traversal | median ms |
| E08 | stack_queue | list stack, deque FIFO, list FIFO | median ms |
| E09 | hash | dictionary vs scan vs sort | median ms |
| E10 | bst | balanced vs skewed BST | visited nodes |
| E11 | graph | BFS vs DFS path graph | median ms |
| E12 | shortest_path | Dijkstra directed path | median ms plus V references |
| E13 | recursion_dp | naive Fibonacci vs iteration | median ms |
| E14 | memory | list/dict/deque allocations | peak KiB |
| E15 | sorting_stability | preserve original equal-key order | records / distinct keys |
| E16 | hash_singly | hash table with singly linked collision chains | mean comparisons, maximum chain, load |
| E17 | hash_doubly | doubly linked collision chains; delete/update correctness | mean comparisons, maximum chain, load |
| E18 | hash_load | contrast low and high collision load factors | mean comparisons and chain lengths |
| E19 | tree_stack_queue | implement inorder/preorder with stack, breadth-first with queue; postorder verified separately | median ms |
| E20 | avl | LL/RR/LR/RL and search height vs skewed BST | visited nodes and AVL height |

For every E01–E20 record (a) objective, (b) hypothesis, (c) input size and distribution, (d) program and exact basic operation or timing method, (e) plotted graph, (f) complexity derivation, (g) discrepancy/limitations, (h) one extension. Run at least three independent trials for microbenchmarking, report median plus spread rather than claiming precise timings.

### Guided worked examples for the five advanced laboratories

**E16 (singly linked hash chain):** m=3, keys 2,5,8 map to index 2 (integer hash mod 3). Bucket 2 becomes 8→5→2. Looking up 2 takes 3 node comparisons. Updating 5 changes its value rather than adding a duplicate; deleting a head, middle and tail must preserve links.

**E17 (doubly linked hash chain):** the same bucket is 8↔5↔2 with prev/next links. Deleting 5 changes 8.next to 2 and 2.prev to 8; verify both directions and head removal. For comparisons, the extra prev pointer does not magically make key lookup O(1).

**E18 (load factor):** hold keys n constant, vary bucket count m; α=n/m. With more buckets, collisions typically decrease; malicious or bad hashes can still force O(n) chains. Plot measured successful-search node comparisons alongside maximum chain length.

**E19 (tree traversal):** insert 2 with children 1 and 3. Stack-based inorder yields [1,2,3]; preorder [2,1,3]; postorder [1,3,2]; queue-based level order [2,1,3]. Swap a stack for a queue and explain which exploration order changes.

**E20 (AVL rotations):** LL insertion [30,20,10] → right rotation to root 20; RR [10,20,30] → left rotation; LR [30,10,20] → rotate left child then right root; RL [10,30,20] → rotate right child then left root. Validate BST ordering, stored heights and balance factors after every insertion.

### Extension / research questions
- Change chain bucket count and fit search comparisons against load factor α, not merely n; test custom colliding keys.
- Compare singly and doubly chain memory overhead via `tracemalloc` and discuss Python object-model effects.
- Add a sentinel circular doubly linked chain and test edge cases.
- Implement full AVL deletion and check balancing after every deletion.
- Compare breadth-first peak frontier memory on balanced vs skewed trees, and stack-based DFS memory.
- Include random tree insertion orders across seeds and error bars for search depth.

## 9. Assessment (100 points)
Theory derivations 20; coding correctness/edge cases 25; protocol and measurement 20; figure/table interpretation 20; reproducibility, discussion and report 15. Require independent explanation of data choice, assumptions, and a case where observed measurements contradict simplistic predictions.

## 10. ATLAS connections (design examples, not implementation claims)
Ride requests form a FIFO queue; driver lookup can use a hash map; dispatch graphs can represent roads; priority queues can support scheduling; sorting ranks drivers; graph search supports routing; predicted demand can be aggregated over a 2D geographic grid. The teaching exercises are illustrative and should not be interpreted as deployed ATLAS implementation details.

## 11. Exercises and challenge extensions
1. Trace n(n−1)/2 comparisons on reverse insertion sort; prove the loop invariant.
2. Implement binary search for first occurrence among duplicates.
3. Compare row-major vs column-major traversal of a NumPy array; explain caches.
4. Implement linked-list delete, cycle detection (Floyd), and unit tests.
5. Implement circular queue and compare to deque.
6. Force dictionary hash collisions with a custom key and explain worst-case caveats.
7. Implement AVL rotations and compare heights.
8. Implement heap-based dispatch simulation with 1,000 priorities.
9. Test BFS vs Dijkstra on unit-weight graphs; explain when results coincide.
10. Design a ride-booking mini-project: queue requests, look up drivers, compute paths and visualize operational counts.

**Further reading:** CLRS, *Introduction to Algorithms*; Open Data Structures (Pat Morin); Python docs for collections, time, tracemalloc and heapq. Reproducibility: specify Python/library versions, CPU, samples and random seed.
