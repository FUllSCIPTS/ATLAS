# Data Structures and Algorithms — an illustrated, standalone course

**Format:** 24 lessons, 30 laboratory experiments, 15 teaching weeks (2 h theory + 2 h lab). **Language:** Python 3. **Audience:** complete beginners to intermediate students. Every lesson can be read on its own: it defines its terms, draws the structure, traces an example by hand, gives runnable code and complexity tables, lists the usual mistakes, and ends with a lab and exercises.

[Live labs in the Architecture Explorer](https://fullscipts.github.io/ATLAS/#dsa) · [Open the 30 experiments in Google Colab](https://colab.research.google.com/github/FUllSCIPTS/ATLAS/blob/main/dsa_lab/DSA_Colab_Labs.ipynb) · [Lab manual](../dsa_lab/README.md) · [All implementations (`dsa_lab/experiments.py`)](../dsa_lab/experiments.py) · [ATLAS Go UML](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/docs/UML_BLUEPRINT.md#android-app-atlas-go) · [ATLAS Go method catalogue](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/docs/ARCHITECTURE.md#complete-source-method-catalog)

**Interactive companion:** [ATLAS Architecture Explorer → Data Structures](https://fullscipts.github.io/ATLAS/#dsa) —
step through singly, doubly and circular linked lists, Josephus and Floyd's cycle detection, a stack,
ring-buffer queue and LRU cache, open-addressing hashing with tombstones, BST, AVL, heap and trie,
BFS, DFS, Dijkstra and Prim on Cork's zones, seven sorts with traces, and knapsack, memoised Fibonacci
and N-Queens. Every lab is a pointer-based port of `dsa_lab/experiments.py` and re-checks the structure
after each operation; each topic links to the ATLAS code and to the lessons below.

**Running the code in this guide.** Every Python block runs as written. Blocks that call `dsa.…` use the lab module; run this once first (in Colab the notebook's setup cell does it for you):

~~~python
import sys; sys.path.insert(0, "dsa_lab")      # from the repository root
import experiments as dsa
~~~

## Contents

| Part | Lessons |
|---|---|
| A. Foundations | [1 Problems, algorithms and ADTs](#lesson-1--problems-algorithms-data-structures-and-adts) · [2 Counting and measuring](#lesson-2--counting-operations-and-measuring-honestly) · [3 Asymptotic notation](#lesson-3--asymptotic-notation-cases-amortised-cost-and-recurrences) |
| B. Linear structures | [4 Arrays and dynamic arrays](#lesson-4--arrays-dynamic-arrays-multi-dimensional-indexing-and-strings) · [5 Singly linked lists](#lesson-5--singly-linked-lists) · [6 Doubly linked lists](#lesson-6--doubly-linked-lists) · [7 Circular singly linked lists](#lesson-7--circular-singly-linked-lists) · [8 Circular doubly linked lists, sentinels, LRU, cycles](#lesson-8--circular-doubly-linked-lists-sentinels-lru-caches-and-cycle-detection) · [9 Stacks](#lesson-9--stacks) · [10 Queues, deques and ring buffers](#lesson-10--queues-deques-and-ring-buffers-circular-arrays) · [11 Hash tables](#lesson-11--hash-tables-chaining-open-addressing-load-factor-and-resizing) |
| C. Non-linear structures | [12 Trees and traversals](#lesson-12--trees-and-the-four-traversals) · [13 Binary search trees](#lesson-13--binary-search-trees-search-insert-and-the-three-deletion-cases) · [14 AVL trees](#lesson-14--avl-trees-and-the-four-rotations) · [15 Heaps](#lesson-15--binary-heaps-priority-queues-and-heap-sort) · [16 Tries](#lesson-16--tries-prefix-trees) · [17 Graphs, BFS, DFS](#lesson-17--graphs-representations-bfs-and-dfs) · [18 Shortest paths, DAGs, union-find](#lesson-18--shortest-paths-topological-order-union-find-and-spanning-trees) |
| D. Algorithm design | [19 Searching](#lesson-19--searching) · [20 Sorting](#lesson-20--sorting-stability-and-the-n-log-n-lower-bound) · [21 Recursion and divide-and-conquer](#lesson-21--recursion-and-divide-and-conquer) · [22 Greedy, DP, backtracking](#lesson-22--greedy-algorithms-dynamic-programming-and-backtracking) · [23 Correctness](#lesson-23--proving-correctness-and-testing-invariants) |
| E. Practice | [24 Laboratory protocol and the 30 experiments](#lesson-24--laboratory-protocol-and-the-30-experiments) · [Teaching plan](#15-week-teaching-plan) · [Assessment](#assessment-100-marks) · [Exercises](#exercise-bank) |

~~~mermaid
flowchart LR
 A["A. Foundations<br/>ADT · counting · O Ω Θ"] --> B["B. Linear<br/>arrays · linked lists · circular lists<br/>stacks · queues · hashing"]
 B --> C["C. Non-linear<br/>trees · BST · AVL · heaps<br/>tries · graphs"]
 C --> D["D. Design<br/>search · sort · D&C<br/>greedy · DP · backtracking"]
 D --> E["E. Practice<br/>30 experiments · report"]
~~~

**Notation used throughout.** n = number of items; V, E = vertices, edges; h = tree height **counted in nodes** (empty tree 0, single leaf 1); w = maximum tree width; m = hash buckets; α = n/m (load factor); log means log₂ unless stated. A **comparison count** and a **time in milliseconds** are different measurements and are never plotted as if they were the same unit.

## How this course relates to ATLAS Go

ATLAS Go is the Python/Kivy ride-and-food app in this repository. Several lessons point to a real function in it so you can see a concept in production-style code. The status column is strict: **Implemented** means the named code exists in [`android-app/atlas_go/`](../android-app/atlas_go/); **Related** means the app does something similar without using that exact structure; **Teaching only** means the structure lives only in [`dsa_lab/experiments.py`](../dsa_lab/experiments.py).

| Topic | Status and exact code | Where |
|---|---|---|
| ADT operations | **Implemented:** `LocalStore.book`, `checkout`, `commit` | [store.py](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) · [LocalStore UML](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/docs/UML_BLUEPRINT.md#app-class-diagram) |
| Linear scans and filtering | **Implemented:** `LocalStore.online_drivers`, `my_history`; `Catalog.menu` | [store.py](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) · [domain.py](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/domain.py) |
| 2-D table lookup | **Implemented:** `domain.DISTANCES[pickup][destination]` inside `distance()` | [domain.py](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/domain.py) |
| Dictionaries (hashing) | **Implemented:** `Cart.items`, `Catalog.dishes`, `LocalStore.failures` — Python `dict`, which uses open addressing, not linked chains | [domain.py](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/domain.py) · [store.py](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) |
| Sorting and ranking | **Implemented:** `intelligence.rank` sorts candidates with `sorted`; `choose` takes the best | [intelligence.py](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py) |
| Minimum selection | **Implemented:** `geo.nearest_place` takes the minimum Haversine distance | [geo.py](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/geo.py) |
| Grid indexing | **Implemented:** `geo.world_px`, `geo.tile_range`, `LiveMap.visible_tiles` | [geo.py](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/geo.py) · [livemap.py](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/livemap.py) |
| State machines | **Related:** `LocalStore.driver_advance`, `advance_ride`, `advance_order` move a ride/order through states; they are not a queue ADT | [store.py](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) · [Lifecycle UML](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/docs/UML_BLUEPRINT.md#on-device-ride-and-order-lifecycles) |
| LRU cache | **Implemented:** `TileLoader.texture` calls `textures.move_to_end(key)` on a hit and `_deliver` evicts with `textures.popitem(last=False)` past `memory=160` tiles — an LRU cache on an `OrderedDict`; the course's `LRUCache` builds the same thing from a dict and a circular doubly linked list | [livemap.py](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/livemap.py) |
| Correctness checks | **Implemented:** `LocalStore.validate`, `snapshot`, `commit`; `intelligence.self_test` | [store.py](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) · [intelligence.py](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py) |
| Linked lists (all four kinds), ring buffer, hash chains, open addressing, BST/AVL, heap, trie, graph algorithms, union-find, DP | **Teaching only** | [`dsa_lab/experiments.py`](../dsa_lab/experiments.py) |

The UML blueprint also documents a separate **server starter** on the `architecture-explorer` branch; do not confuse its planned back-end functions with code running inside today's on-device app.

---

# Part A — Foundations

## Lesson 1 — Problems, algorithms, data structures and ADTs

**ATLAS link:** [`LocalStore.book`, `checkout`, `commit`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) are operations on the app's state. Each has a precondition (for example, the pickup and destination must differ), an effect, and a failure mode.

**Definitions.**
- A **problem** states what output is required for every valid input. *Example:* given a list of driver distances, return the index of the smallest.
- An **algorithm** is a finite sequence of unambiguous steps that solves the problem for **every** valid input and then stops.
- A **data structure** is a concrete way of organising data in memory (an array, a linked list, a hash table).
- An **abstract data type (ADT)** is a promise about behaviour — a set of operations and their meaning — that says nothing about memory. "Queue: `enqueue(x)` adds at the back, `dequeue()` removes the oldest" is an ADT. A Python `deque`, a linked list and a ring buffer are three different **implementations** of it.

~~~mermaid
flowchart LR
 P["Problem<br/>serve ride requests fairly"] --> A["ADT<br/>FIFO queue: enqueue, dequeue, is_empty"]
 A --> I1["Implementation 1<br/>linked list"]
 A --> I2["Implementation 2<br/>ring buffer (circular array)"]
 A --> I3["Implementation 3<br/>collections.deque"]
 I1 --> G["Algorithm<br/>enqueue each arrival; dequeue next"]
 I2 --> G
 I3 --> G
 G --> O["Output<br/>service order"]
~~~

**Why separate ADT from implementation?** Because the *same* program can switch implementation to change performance without changing correctness. A queue built on `list.pop(0)` is correct but each dequeue shifts every remaining element; `deque.popleft()` is O(1). Experiments E08 and E23 measure exactly this.

**The contract of an algorithm.** Write three things before writing code:

| Item | Meaning | Linear search example |
|---|---|---|
| Precondition | What must be true of the input | `a` is a finite sequence |
| Postcondition | What is true of the output | returns `i` with `a[i] == x`, or −1 if `x` not in `a` |
| Termination | Why it stops | the loop index increases and is bounded by `len(a)` |

**Worked example (trace by hand).** Search for 7 in `[2, 7, 9]`.

| Step | i | a[i] | a[i] == 7? | comparisons so far |
|---|---|---|---|---|
| 1 | 0 | 2 | no | 1 |
| 2 | 1 | 7 | **yes → return 1** | 2 |

Searching for the absent value 6 needs 3 comparisons and returns −1.

~~~python
def linear_search(a, target):
    for i, value in enumerate(a):
        if value == target:
            return i
    return -1

assert linear_search([2, 7, 9], 7) == 1
assert linear_search([2, 7, 9], 6) == -1
assert linear_search([], 6) == -1          # the empty input is a valid input
~~~

**Common mistakes.** Forgetting the empty input; returning inside the loop on the *first mismatch*; assuming sorted input when the precondition does not say so.

**Lab:** E02, E03. **Exercises:** (1) Write the contract for "return the two nearest drivers". (2) Name two implementations of the *stack* ADT and one operation where they differ in cost.

## Lesson 2 — Counting operations and measuring honestly

**ATLAS link:** [`online_drivers`, `my_history`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) each scan a list once; [`intelligence.rank`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py) scores every candidate and then sorts. Count how their work grows with the number of accounts or candidates.

**Step 1 — define the input size n.** Length of a list; for a graph use V and E; for an R×C table use R and C.
**Step 2 — choose the basic operation**: a comparison, a swap, a hash probe, a node visit. Count only that.
**Step 3 — write T(n)**, the count as a function of n.

| Code shape | Count T(n) | n = 10 | n = 1000 |
|---|---|---|---|
| one loop over n | n | 10 | 1 000 |
| two independent nested loops | n² | 100 | 1 000 000 |
| triangular loop `for i in range(n): for j in range(i)` | 0+1+…+(n−1) = n(n−1)/2 | 45 | 499 500 |
| halve until 1 | ⌊log₂ n⌋ + 1 | 4 | 10 |
| split in halves, linear merge | ≈ n log₂ n | 33 | 9 966 |

~~~mermaid
flowchart TD
 N["input size n"] --> A["one pass<br/>n"]
 N --> B["all pairs<br/>n²"]
 N --> C["halving<br/>log₂ n"]
 N --> D["halve + merge<br/>n log₂ n"]
 N --> E["all subsets<br/>2ⁿ"]
~~~

~~~python
def triangle(n):
    steps = 0
    for i in range(n):
        for j in range(i):
            steps += 1
    return steps

assert [triangle(n) for n in (0, 1, 5, 10)] == [0, 0, 10, 45]
assert all(triangle(n) == n * (n - 1) // 2 for n in range(50))
~~~

**Measuring time and memory (and what that measurement does *not* prove).**

~~~python
import time, statistics, tracemalloc

def median_ms(task, repeats=9):
    samples = []
    for _ in range(repeats):
        t = time.perf_counter(); task()
        samples.append(1000 * (time.perf_counter() - t))
    return statistics.median(samples)

data = list(range(100_000))
print("scan ms:", round(median_ms(lambda: 99_999 in data), 3))

tracemalloc.start()
squares = [x * x for x in range(10_000)]
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print("peak traced KiB:", round(peak / 1024, 1))
~~~

Rules for honest measurement: build the input **outside** the timed region (E08 originally broke this rule — see the [lab manual](../dsa_lab/README.md#audit-notes)); repeat and report the **median** and spread; fix random seeds; record Python version and machine; check the output is correct before trusting the time. `tracemalloc` sees Python allocations only, not the whole process. **A timing chart can suggest a growth rate but cannot prove one** — five points on a noisy machine fit many curves.

**Lab:** E01, E06, E14. **Exercises:** (1) Count comparisons of `max(a)` exactly. (2) Why might doubling n *not* double the measured time of a linear scan at n = 100?

## Lesson 3 — Asymptotic notation, cases, amortised cost and recurrences

**Definitions** (for non-negative functions f, g):

| Notation | Meaning | Formal definition |
|---|---|---|
| f = O(g) | f grows **no faster** than g (upper bound) | ∃ c > 0, n₀: f(n) ≤ c·g(n) for all n ≥ n₀ |
| f = Ω(g) | f grows **at least** as fast as g (lower bound) | ∃ c > 0, n₀: f(n) ≥ c·g(n) for all n ≥ n₀ |
| f = Θ(g) | same growth (tight bound) | f = O(g) **and** f = Ω(g) |
| f = o(g) | strictly slower | f(n)/g(n) → 0 |
| f = ω(g) | strictly faster | f(n)/g(n) → ∞ |

~~~mermaid
flowchart TD
 F["a cost function f(n)"] --> O["O(g): eventually below c₂·g"]
 F --> M["Ω(g): eventually above c₁·g"]
 O --> T["both ⇒ Θ(g): sandwiched"]
 M --> T
~~~

**Proof example.** f(n) = 3n² + 5n + 8. For n ≥ 1: 3n² ≤ f(n) ≤ 3n² + 5n² + 8n² = 16n². So c₁ = 3, c₂ = 16, n₀ = 1 and f = Θ(n²). It is also O(n³) (true but loose) and **not** Θ(n³).

**Bounds are not cases.** O, Ω, Θ bound a *function*. Best, average and worst **cases** are *different functions* of the same algorithm, and each can be given any bound:

| Algorithm | Best case | Average case | Worst case |
|---|---|---|---|
| Linear search | Θ(1) (first item) | Θ(n) ((n+1)/2 successful) | Θ(n) (absent) |
| Binary search | Θ(1) | Θ(log n) | Θ(log n) |
| Insertion sort | Θ(n) (sorted) | Θ(n²) | Θ(n²) (reversed) |
| Hash-table lookup | Θ(1) | Θ(1 + α) expected | Θ(n) (all keys collide) |
| BST search | Θ(1) | Θ(log n) random inserts | Θ(n) (skewed) |

**Common growth orders**, from fastest to slowest at n = 64: 1 < log n = 6 < n = 64 < n log n = 384 < n² = 4 096 < 2ⁿ ≈ 1.8 × 10¹⁹.

**Amortised cost** is the average cost per operation over a worst-case *sequence*. Appending to a dynamic array that doubles when full costs Θ(n) on the rare resize, but n appends cost < 3n element writes in total, so each append is **amortised O(1)** (Lesson 4, E30).

**Recurrences.** Recursive algorithms give equations:

| Algorithm | Recurrence | Solution |
|---|---|---|
| Binary search | T(n) = T(n/2) + Θ(1) | Θ(log n) |
| Merge sort | T(n) = 2T(n/2) + Θ(n) | Θ(n log n) |
| Naive Fibonacci | T(n) = T(n−1) + T(n−2) + Θ(1) | Θ(φⁿ), φ ≈ 1.618 |
| Tree traversal | T(n) = T(k) + T(n−k−1) + Θ(1) | Θ(n) |

**Master theorem** (for T(n) = a·T(n/b) + Θ(n^d)): if d > log_b a → Θ(n^d); if d = log_b a → Θ(n^d log n); if d < log_b a → Θ(n^{log_b a}). Merge sort: a = 2, b = 2, d = 1 = log₂2 → Θ(n log n).

**Lab:** E01, E03, E30. **Exercises:** (1) Prove 2n + 10 = O(n) with explicit c, n₀. (2) Is n² = O(n log n)? Prove or refute. (3) Solve T(n) = 4T(n/2) + n with the master theorem.

---

# Part B — Linear data structures

## Lesson 4 — Arrays, dynamic arrays, multi-dimensional indexing and strings

**ATLAS link:** [`domain.distance`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/domain.py) reads a 2-D table `DISTANCES[pickup][destination]` in O(1); [`geo.tile_range` and `LiveMap.visible_tiles`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/geo.py) compute grid ranges of map tiles.

**An array** is a block of equal-sized cells at consecutive addresses. The address of cell i is `base + i × cell_size`, so **indexing is O(1)** whatever i is.

~~~mermaid
flowchart LR
 subgraph block["one contiguous block (capacity 6, size 4)"]
 direction LR
 A0["[0] 12"] --- A1["[1] 25"] --- A2["[2] 7"] --- A3["[3] 40"] --- A4["[4] free"] --- A5["[5] free"]
 end
~~~

**A dynamic array** (Python `list`, Java `ArrayList`) keeps spare capacity. When it is full it allocates a bigger block and **copies** everything across. With doubling, n appends cause copies of 1 + 2 + 4 + … < 2n elements: amortised O(1) per append. With a fixed increment (+16) the copies add up to ≈ n²/32: Θ(n) per append. E30 counts the copies exactly.

| Appends | Capacity sequence (doubling from 1) | Copies so far |
|---|---|---|
| 1 | 1 | 0 |
| 2 | 2 | 1 |
| 3 | 4 | 3 |
| 5 | 8 | 7 |
| 9 | 16 | 15 |

~~~python
arr = dsa.DynamicArray(growth=2.0)
for v in range(9):
    arr.append(v)
assert arr.capacity == 16 and arr.copies == 1 + 2 + 4 + 8
arr.insert(0, -1)                        # shifts 9 elements right: O(n)
assert arr.to_list() == [-1, 0, 1, 2, 3, 4, 5, 6, 7, 8]
~~~

| Operation (dynamic array) | Cost |
|---|---|
| `a[i]`, `a[i] = x` | O(1) |
| append / pop at the end | amortised O(1) |
| insert / delete at index i | O(n − i) (shifting) |
| search for a value | O(n) |

**2-D and 3-D indexing.** A matrix with R rows and C columns stored **row-major** puts A[i][j] at flat index `i·C + j`; **column-major** (Fortran, MATLAB) uses `j·R + i`. A 3-D X×Y×Z array in row-major order uses `(i·Y + j)·Z + k`.

~~~mermaid
flowchart TB
 M["2 × 3 matrix [[a b c],[d e f]]"] --> RM["row-major: a b c d e f<br/>A[1][2] → 1·3+2 = 5"]
 M --> CM["column-major: a d b e c f<br/>A[1][2] → 2·2+1 = 5"]
~~~

~~~python
matrix = [[10, 20, 30], [40, 50, 60]]
flat = [x for row in matrix for x in row]
assert flat[dsa.row_major(1, 2, cols=3)] == matrix[1][2] == 60
assert dsa.row_major_3d(1, 2, 3, Y=3, Z=4) == 23          # last cell of 2×3×4
~~~

Python's nested lists are lists of *references* to separate row objects, not one contiguous block; use NumPy to study cache effects (exercise 3 below).

**Strings** are immutable arrays of characters. `s[i]` is O(1); `s + t` builds a new string of length |s|+|t|; building a string with `+=` in a loop can be Θ(n²) — use `"".join(parts)`.

**Lab:** E07, E30. **Exercises:** (1) Derive the column-major formula for 3-D. (2) Show that growth ×1.5 is still amortised O(1). (3) Time row-wise vs column-wise sums of a 2 000 × 2 000 NumPy array and explain the difference.

## Lesson 5 — Singly linked lists

**ATLAS status:** teaching only ([`SinglyLinkedList`](../dsa_lab/experiments.py)). ATLAS Go keeps its history in Python lists.

A **singly linked list** is a chain of **nodes**; each node holds a value and a reference `next` to the following node. The list object remembers `head` (first node), optionally `tail` (last node) and `size`. The last node's `next` is `None`. Nodes can be anywhere in memory.

~~~mermaid
flowchart LR
 H(["head"]) --> A["7 | next"] --> B["11 | next"] --> C["19 | next"] --> N(["None"])
 T(["tail"]) --> C
~~~

**Insertion — three positions.**

~~~mermaid
flowchart LR
 subgraph front["push_front(3): new.next = head; head = new"]
 direction LR
 X["3"] --> A1["7"] --> B1["11"]
 end
 subgraph after["insert_after(node 7, 9): new.next = 7.next; 7.next = new"]
 direction LR
 A2["7"] --> Y["9"] --> B2["11"]
 end
~~~

The **order of the two pointer assignments matters**: in `insert_after`, setting `node.next = new` first would lose the rest of the list.

**Deletion — every case.** To delete you need the node **before** the one you remove, because that is the pointer you change.

| Case | Pointer changes | Extra care |
|---|---|---|
| delete head | `head = head.next` | if list becomes empty, `tail = None` |
| delete middle node p (predecessor q) | `q.next = p.next` | — |
| delete tail | `q.next = None` | `tail = q` |
| value absent | none | return False |
| empty list | none | return False / raise |

**Reversal** — walk once, turning each arrow round. Trace on 1 → 2 → 3:

| step | prev | p | after `p.next = prev` |
|---|---|---|---|
| 1 | None | 1 | 1 → None |
| 2 | 1 | 2 | 2 → 1 → None |
| 3 | 2 | 3 | 3 → 2 → 1 → None; head = 3 |

~~~python
s = dsa.SinglyLinkedList([7, 11, 19])
s.push_front(3)
s.push_back(23)
assert s.to_list() == [3, 7, 11, 19, 23] and s.validate()
node, comparisons = s.find(11)
s.insert_after(node, 13)
assert s.to_list() == [3, 7, 11, 13, 19, 23] and comparisons == 3
assert s.remove(3) and s.remove(13) and s.remove(23)     # head, middle, tail
assert s.to_list() == [7, 11, 19] and s.tail.value == 19 and s.validate()
s.reverse()
assert s.to_list() == [19, 11, 7] and s.validate()
~~~

| Operation | Singly linked list | Dynamic array |
|---|---|---|
| access k-th item | O(k) | O(1) |
| push / pop at front | **O(1)** | O(n) |
| push at back (with tail) | O(1) | amortised O(1) |
| pop at back | **O(n)** (find predecessor) | O(1) |
| insert after a known node | O(1) | O(n) |
| search | O(n) | O(n) |
| memory | value + 1 pointer per node | values + spare capacity |

**Common mistakes.** Losing the rest of the list by overwriting `next` too early; forgetting to update `tail` when deleting the last node; `while p.next:` loops that crash on an empty list.

**Lab:** E07. **Exercises:** (1) Return the k-th node from the end in one pass. (2) Merge two sorted lists without creating new nodes. (3) Detect a palindrome list in O(n) time and O(1) extra space.

## Lesson 6 — Doubly linked lists

**ATLAS status:** teaching only ([`DoublyLinkedList`](../dsa_lab/experiments.py)).

Each node also stores `prev`. The list can be walked both ways, and a node you already hold can be removed in O(1) because its predecessor is `node.prev`.

~~~mermaid
flowchart LR
 N1(["None"]) <-.- A["prev | 7 | next"]
 A <--> B["prev | 11 | next"] <--> C["prev | 19 | next"]
 C -.-> N2(["None"])
 H(["head"]) --> A
 T(["tail"]) --> C
~~~

**Unlinking a known node p** — four cases collapse into two independent questions:

~~~text
if p.prev is None: head = p.next      else: p.prev.next = p.next
if p.next is None: tail = p.prev      else: p.next.prev = p.prev
~~~

~~~python
d = dsa.DoublyLinkedList([7, 11, 19])
node, _ = d.find(11)
d.unlink(node)                                  # O(1) once the node is known
assert d.to_list() == [7, 19] and d.to_list_backward() == [19, 7] and d.validate()
assert d.pop_back() == 19                       # O(1): tail.prev is the new tail
assert d.validate() and d.head is d.tail
~~~

**The invariant** a doubly linked list must satisfy, checked by `validate()`: for every node p, `p.next.prev is p` (when p.next exists), `head.prev is None`, `tail.next is None`, and the forward walk visits exactly `size` nodes ending at `tail`.

| | Singly | Doubly |
|---|---|---|
| pointers per node | 1 | 2 |
| pop at back | O(n) | **O(1)** |
| delete a known node | O(n) (need predecessor) | **O(1)** |
| walk backwards | no | yes |
| pointer updates per insert | 2 | 4 |

**Lab:** E17 uses doubly linked hash chains. **Exercises:** (1) Insert before a known node. (2) Explain why finding a *key* is still O(n) even though deleting a *node* is O(1).

## Lesson 7 — Circular singly linked lists

**ATLAS status:** teaching only ([`CircularSinglyLinkedList`](../dsa_lab/experiments.py), [`josephus_circular`](../dsa_lab/experiments.py)). The natural ATLAS example is a **round-robin** rota — e.g. cycling through drivers in a zone so each gets offered a job in turn — which ATLAS Go does not implement; it is a design exercise.

In a **circular** list the last node's `next` points back to the first node instead of `None`. There is no end: you can keep walking forever, so every loop must stop when it **returns to where it started**.

~~~mermaid
flowchart LR
 T(["tail"]) --> D
 A["7 (head)"] --> B["11"] --> C["19"] --> D["23 (tail)"]
 D -- "tail.next = head" --> A
~~~

**The tail-pointer trick.** Store only `tail`. The head is `tail.next`, so both ends are one step away:

| Operation | How | Cost |
|---|---|---|
| `head` | `tail.next` | O(1) |
| `push_front(x)` | `new.next = tail.next; tail.next = new` | O(1) |
| `push_back(x)` | `push_front(x)`, then `tail = tail.next` | O(1) |
| `pop_front()` | `first = tail.next; tail.next = first.next` | O(1) |
| `rotate(k)` (advance start) | move `tail` forward k times | O(k), **no data moves** |
| `find(x)` | walk from head until found or back past tail | O(n) |
| `pop_back()` | needs the node before tail | O(n) |

**The one-node ring and the empty ring** are the edge cases: a single node points to **itself**; an empty list has `tail = None`.

~~~mermaid
flowchart LR
 subgraph one["one node"]
 X["5"] --> X
 end
 subgraph empty["empty"]
 E(["tail = None"])
 end
~~~

**Trace — build [0, 1, 2] and rotate by one.**

| Step | Action | Ring (from head) | tail |
|---|---|---|---|
| 1 | `push_back(1)` | 1 → (1) | 1 |
| 2 | `push_back(2)` | 1 → 2 → (1) | 2 |
| 3 | `push_front(0)` | 0 → 1 → 2 → (0) | 2 |
| 4 | `rotate(1)` | 1 → 2 → 0 → (1) | 0 |

~~~python
c = dsa.CircularSinglyLinkedList()
c.push_back(1); c.push_back(2); c.push_front(0)
assert c.to_list() == [0, 1, 2] and c.tail.next is c.head and c.validate()
assert c.rotate(1) == 1 and c.to_list() == [1, 2, 0]      # one pointer move
node, steps = c.find(99)
assert node is None and steps == 3                         # stops after one lap
assert c.remove(0) and c.to_list() == [1, 2] and c.validate()
~~~

**Traversal must count or compare, never test for `None`:**

~~~python
def print_ring(ring):
    if ring.tail is None:
        return []
    out, p = [], ring.tail.next
    while True:
        out.append(p.value)
        if p is ring.tail:          # back at the last node: stop
            return out
        p = p.next

assert print_ring(dsa.CircularSinglyLinkedList([4, 5, 6])) == [4, 5, 6]
~~~

**Application — the Josephus problem.** n people stand in a circle; every k-th person leaves; who remains? With a circular list each elimination is "walk k−1 steps, unlink the next node": **n(k−1) pointer moves in total**. With a Python list, `pop(i)` shifts every later element, Θ(n²) in total. Trace for n = 7, k = 3:

| Round | Ring before | Count 1-2-3 lands on | Removed |
|---|---|---|---|
| 1 | 1 2 3 4 5 6 7 | 3 | 3 |
| 2 | 1 2 4 5 6 7 | 6 | 6 |
| 3 | 1 2 4 5 7 | 2 | 2 |
| 4 | 1 4 5 7 | 7 | 7 |
| 5 | 1 4 5 | 5 | 5 |
| 6 | 1 4 | 1 | 1 |
| — | 4 | survivor | **4** |

~~~python
order, moves = dsa.josephus_circular(7, 3)
assert order == [3, 6, 2, 7, 5, 1, 4] and moves == 7 * 2
assert dsa.josephus_formula(7, 3) == 4                     # J(n) = (J(n-1)+k) mod n
~~~

**Round-robin scheduling** is the same structure: the CPU (or a dispatcher) serves the head, then `rotate(1)` moves to the next; a finished task is removed in O(1) if you hold its predecessor.

**Common mistakes.** `while p is not None` (infinite loop); forgetting the self-loop for a one-node ring; deleting the tail without moving `tail` to its predecessor; using `head` and `tail` both and letting them drift apart.

**Lab:** E21 (Josephus: circular list vs Python list). **Exercises:** (1) Split a circular list into two halves. (2) Insert into a *sorted* circular list keeping it sorted (check the wrap-around case). (3) Implement `pop_back` and state its cost.

## Lesson 8 — Circular doubly linked lists, sentinels, LRU caches and cycle detection

**ATLAS status:** teaching only ([`CircularDoublyLinkedList`](../dsa_lab/experiments.py), [`LRUCache`](../dsa_lab/experiments.py)). **LRU in the app:** ATLAS Go's map [`TileLoader`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/livemap.py) is an LRU cache — `texture` calls `textures.move_to_end(key)` on a hit and `_deliver` evicts the oldest tile with `textures.popitem(last=False)` once more than 160 are held. It uses `collections.OrderedDict` (a dict plus a doubly linked list) instead of a hand-built list. [Try it in the explorer](https://fullscipts.github.io/ATLAS/#dsa-queues).

A **circular doubly linked list** joins the two ends of a doubly linked list. Adding a **sentinel** — a dummy node that holds no data and never leaves — removes every special case: the empty list is the sentinel pointing to itself, `first = sentinel.next`, `last = sentinel.prev`.

~~~mermaid
flowchart LR
 S["S (sentinel)"] <--> A["7"] <--> B["11"] <--> C["19"]
 C <-- "wraps" --> S
~~~

~~~mermaid
flowchart LR
 subgraph empty["empty list"]
 S0["S"] -- next --> S0
 S0 -- prev --> S0
 end
~~~

**Only two primitives are needed**; everything else is built from them:

~~~text
insert_after(node, x):   new = Node(x, prev=node, next=node.next)
                         node.next.prev = new
                         node.next = new
unlink(p):               p.prev.next = p.next
                         p.next.prev = p.prev
push_front = insert_after(sentinel)      push_back = insert_after(sentinel.prev)
pop_front  = unlink(sentinel.next)       pop_back  = unlink(sentinel.prev)
~~~

No `if head is None`, no `if p is tail`: the sentinel is always there to be a neighbour. All six operations are O(1).

**Rotation in either direction** moves only the sentinel, and because the list is doubly linked it can walk the **shorter way round**: at most ⌊n/2⌋ steps.

~~~python
cd = dsa.CircularDoublyLinkedList([1, 2, 3, 4, 5])
assert cd.rotate(2) == 2 and cd.to_list() == [3, 4, 5, 1, 2]
assert cd.rotate(-1) == 1 and cd.to_list() == [2, 3, 4, 5, 1]
assert cd.rotate(4) == 1 and cd.to_list() == [1, 2, 3, 4, 5]   # forward 4 = back 1
assert cd.to_list_backward() == [5, 4, 3, 2, 1] and cd.validate()
~~~

| Operation | Doubly (head/tail) | **Circular doubly + sentinel** |
|---|---|---|
| push/pop either end | O(1), with empty-list special cases | O(1), no special cases |
| unlink known node | O(1), 4 cases | O(1), 1 case |
| rotate by k | O(n) (relink ends) | O(min(k, n−k)) |
| empty test | `head is None` | `sentinel.next is sentinel` |
| extra memory | 0 | one node |

### Application: an LRU cache

A **least-recently-used cache** holds at most `capacity` items; on overflow it evicts the item unused for longest. It needs two O(1) operations at once:
- find an item by key → a **dict** from key to list node;
- move that item to "most recent", and find the oldest → a **circular doubly linked list** (front = newest, `sentinel.prev` = oldest).

~~~mermaid
flowchart LR
 subgraph map["dict: key → node"]
 KA["'a'"]
 KC["'c'"]
 end
 S["S"] <--> C["('c',3) newest"] <--> A["('a',1) oldest"] <--> S
 KA -.-> A
 KC -.-> C
~~~

~~~python
lru = dsa.LRUCache(2)
lru.put("a", 1); lru.put("b", 2)
assert lru.get("a") == 1          # 'a' becomes most recent; order: a, b
lru.put("c", 3)                   # full: evict the least recent, 'b'
assert lru.get("b") is None and lru.keys() == ["c", "a"] and lru.order.validate()
~~~

E22 compares this with a list-based LRU (`list.remove` is O(n)) and with `collections.OrderedDict`, which is implemented in C with the same doubly-linked idea.

### Detecting a cycle: Floyd's tortoise and hare

A list built by mistake may contain a loop. Move `slow` one step and `fast` two steps; if they ever meet there is a cycle. Then a second walk finds where the cycle starts (μ) and its length (λ). O(n) time, O(1) space.

~~~mermaid
flowchart LR
 A["1"] --> B["2 (cycle start, μ = 1)"] --> C["3"] --> D["4"] --> B
~~~

~~~python
n1, n2, n3, n4 = (dsa.Node(v) for v in (1, 2, 3, 4))
n1.next, n2.next, n3.next, n4.next = n2, n3, n4, n2
assert dsa.floyd_cycle(n1) == (True, 1, 3)                      # starts at index 1, length 3
assert dsa.floyd_cycle(dsa.Node(1, dsa.Node(2))) == (False, None, None)
assert dsa.floyd_cycle(dsa.CircularSinglyLinkedList([1, 2, 3]).head)[0]   # a ring IS a cycle
~~~

**The four linked lists side by side:**

| | Singly | Doubly | Circular singly | Circular doubly + sentinel |
|---|---|---|---|---|
| last node points to | None | None | head | sentinel |
| stored references | head (+tail) | head, tail | tail only | sentinel |
| push front / back | O(1) / O(1) with tail | O(1) / O(1) | O(1) / O(1) | O(1) / O(1) |
| pop front / back | O(1) / **O(n)** | O(1) / O(1) | O(1) / **O(n)** | O(1) / O(1) |
| delete known node | O(n) | O(1) | O(n) | O(1) |
| rotate by k | O(n) | O(n) | O(k) | O(min(k, n−k)) |
| typical use | stacks, hash chains | browser history, editors | round-robin, Josephus | LRU caches, OS run queues, playlists |

**Lab:** E22. **Exercises:** (1) Add `insert_before`. (2) Implement a music playlist with `next`, `previous` and `shuffle-to-front`. (3) Prove that tortoise and hare meet within λ steps after the tortoise enters the cycle.

## Lesson 9 — Stacks

**ATLAS status:** related. Python's own **call stack** runs every ATLAS Go function; screen "back" behaviour in [`AtlasGoApp.on_keyboard`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/app.py) is a navigation decision, not an explicit stack.

A **stack** is LIFO — last in, first out — like a pile of plates. Operations: `push(x)`, `pop()`, `peek()`, `is_empty()`, all O(1). In Python use a `list` (`append`/`pop` at the end) or a singly linked list (push/pop at the head).

~~~mermaid
flowchart LR
 E["empty"] -->|push A| S1["A"] -->|push B| S2["A B"] -->|push C| S3["A B C"] -->|pop → C| S4["A B"]
~~~

**Applications.**

| Problem | How the stack helps |
|---|---|
| Bracket matching | push openers; each closer must match the top |
| Postfix evaluation | push numbers; an operator pops two and pushes the result |
| Undo | push each action; undo pops the latest |
| Depth-first search | the frontier is a stack (Lesson 17) |
| Recursion | each call's local variables live in a stack frame |

Trace `balanced_brackets("{[()]}")`: push `{`, push `[`, push `(`, `)` matches `(`, `]` matches `[`, `}` matches `{`, stack empty → balanced. For `"([)]"`, the `)` meets top `[` → unbalanced.

~~~python
assert dsa.balanced_brackets("{[()()]}") and not dsa.balanced_brackets("([)]")
assert dsa.evaluate_postfix("3 4 + 2 *") == 14      # (3 + 4) * 2
stack = []
stack.append("A"); stack.append("B")
assert stack.pop() == "B" and stack[-1] == "A"
~~~

**Lab:** E08, E19. **Exercises:** (1) Convert infix to postfix (shunting-yard). (2) Implement a min-stack whose `get_min()` is O(1).

## Lesson 10 — Queues, deques and ring buffers (circular arrays)

**ATLAS status:** related. [`LocalStore.tick`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) advances rides and orders through their states over time; a dispatch **queue** of ride requests is the design you would add for many simultaneous passengers.

A **queue** is FIFO — first in, first out. A **deque** (double-ended queue) allows both ends. The trap: a Python `list` used as a queue with `pop(0)` shifts every remaining element, so n dequeues cost Θ(n²).

### The ring buffer

A **ring buffer** (circular array, circular queue) stores the queue in a fixed array and lets the indices **wrap around** with the modulo operator. Nothing is ever shifted.

~~~text
enqueue(x):  back = (front + count) % capacity;  block[back] = x;  count += 1
dequeue():   x = block[front];  front = (front + 1) % capacity;  count -= 1
full  ⇔ count == capacity            empty ⇔ count == 0
~~~

~~~mermaid
flowchart LR
 subgraph ring["capacity 8, front = 4, count = 6 — the queue wraps past index 7"]
 direction LR
 I0["[0] 18"] --- I1["[1] 19"] --- I2["[2] free ← back"] --- I3["[3] free"] --- I4["[4] 14 ← front"] --- I5["[5] 15"] --- I6["[6] 16"] --- I7["[7] 17"]
 end
~~~

Queue order (front to back) is 14, 15, 16, 17, 18, 19 — indices 4, 5, 6, 7, 0, 1.

**Trace (capacity 3).**

| Action | block | front | count | Notes |
|---|---|---|---|---|
| enqueue 1, 2, 3 | [1, 2, 3] | 0 | 3 | full |
| dequeue → 1 | [–, 2, 3] | 1 | 2 | |
| enqueue 4 | [4, 2, 3] | 1 | 3 | back = (1+2) % 3 = 0: **wrap** |
| to_list | | | | 2, 3, 4 |

~~~python
rb = dsa.RingBuffer(3)
for v in (1, 2, 3):
    rb.enqueue(v)
assert rb.is_full() and rb.dequeue() == 1
rb.enqueue(4)
assert rb.block == [4, 2, 3] and rb.front == 1 and rb.to_list() == [2, 3, 4]
try:
    rb.enqueue(5)
except OverflowError:
    print("full: a fixed ring buffer rejects (or overwrites, or grows)")
~~~

Ring buffers are used for keyboard and network buffers, audio streams, log tails and producer–consumer queues because their memory never moves. A growable ring (`grow=True`) doubles and **re-linearises** the elements when full.

| Queue implementation | enqueue | dequeue | notes |
|---|---|---|---|
| `list.append` + `list.pop(0)` | O(1)* | **O(n)** | shifts; fast memmove hides it for small n |
| singly linked list with tail | O(1) | O(1) | one allocation per item |
| `collections.deque` | O(1) | O(1) | C blocks of 64 items |
| ring buffer | O(1) (amortised if growable) | O(1) | fixed memory, no shifting |

E23's measurement is a good lesson in constant factors: the pure-Python ring buffer is *slower* than `list.pop(0)` for a few thousand items (C `memmove` is very fast), but `list.pop(0)` grows quadratically and loses badly by 16 000 items.

**Priority queues** remove the *most urgent* item rather than the oldest — see heaps in Lesson 15.

**Lab:** E08, E23. **Exercises:** (1) Implement a ring buffer that **overwrites** the oldest item when full (a log tail). (2) Implement a queue with two stacks; show amortised O(1).

## Lesson 11 — Hash tables: chaining, open addressing, load factor and resizing

**ATLAS link:** ATLAS Go uses Python dictionaries everywhere: [`Cart.items`, `Catalog.dishes`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/domain.py), [`LocalStore.failures`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) (failed sign-ins per email). CPython's `dict` uses **open addressing**, not linked chains.

A **hash table** stores key–value pairs in an array of m **buckets**. A **hash function** turns a key into an integer; `index = hash(key) mod m` picks the bucket. Two different keys landing in the same bucket is a **collision**; the two classic remedies are chaining and open addressing.

~~~mermaid
flowchart TB
 K["key"] --> H["hash(key) mod 4"]
 H --> B0["bucket 0: empty"]
 H --> B1["bucket 1: (9,v9) → (5,v5) → (1,v1)"]
 H --> B2["bucket 2: empty"]
 H --> B3["bucket 3: (7,v7) → (3,v3)"]
~~~

### Separate chaining

Each bucket holds a linked list of the entries that hashed there. With m = 4, keys 1, 5, 9 all go to bucket 1; inserting at the chain head in that order gives 9 → 5 → 1, and finding 1 takes three comparisons. `put` must **search first** so an existing key is updated rather than duplicated. **Singly linked chains** delete with a trailing `prev` pointer; **doubly linked chains** can unlink a found node directly.

~~~python
table = dsa.ChainHash(4, "singly")
for key in (1, 5, 9):
    table.put(key, key * 10)
assert table.chain_lengths() == [0, 3, 0, 0]
assert table.get(1) == (10, 3)                  # value, comparisons
table.put(5, 555)                                # update, not a duplicate
assert table.size == 3 and table.get(5)[0] == 555
assert table.delete(5) and table.validate()
~~~

**Load factor** α = n/m. Under *simple uniform hashing* the expected chain length is α, a successful search inspects about **1 + α/2** nodes and an unsuccessful one **α**. Keep α bounded by **resizing**: when α exceeds a threshold, double m and reinsert everything (Θ(n) once, amortised O(1) per insert).

~~~python
growing = dsa.ChainHash(2, "singly", max_load=1.0)
for k in range(20):
    growing.put(k, k)
assert len(growing.buckets) >= 16 and growing.load_factor() <= 1.0 and growing.validate()
~~~

### Open addressing (linear probing)

All entries live **in the array itself**. On a collision, try the next slot: h, h+1, h+2, … (mod m). Deleting must leave a **tombstone**, otherwise searches for keys further along the probe sequence would stop early at the hole.

~~~mermaid
flowchart LR
 S0["[0] 16"] --- S1["[1] 1"] --- S2["[2] 9 ← hash 1, probed to 2"] --- S3["[3] tombstone"] --- S4["[4] 4"] --- S5["[5] free"]
~~~

~~~python
oa = dsa.OpenAddressHash(8, max_load=None)
for k in (1, 9, 17):                 # all hash to slot 1 (mod 8)
    oa.put(k, str(k))
assert oa.keys[1:4] == [1, 9, 17] and oa.get(17) == ("17", 3)
assert oa.delete(9) and oa.get(17) == ("17", 3)   # tombstone keeps the chain walkable
~~~

Expected probes for a successful search under linear probing ≈ ½(1 + 1/(1−α)): 1.5 at α = 0.5 but 5.5 at α = 0.9 — **open addressing degrades sharply near full**, which is why tables resize at α ≈ 0.6–0.75. E29 measures both methods against this formula.

| | Separate chaining | Open addressing |
|---|---|---|
| where entries live | nodes outside the array | inside the array |
| α can exceed 1 | yes | no |
| deletion | unlink node | tombstone |
| cache behaviour | pointer chasing | contiguous probes |
| sensitive to high α | gradually | sharply |

**Adversarial keys.** A hash table's O(1) is an *expected* bound under assumptions about the keys. If an attacker chooses keys that all collide (E18 uses multiples of m), every operation becomes Θ(n). Real systems randomise string hashing for this reason (Python's `PYTHONHASHSEED`). Note also that in CPython `hash(-1) == -2`, so even "integers hash to themselves" has an exception.

**Lab:** E09, E16, E17, E18, E29. **Exercises:** (1) Plot chain-length histograms for α = 0.5, 1, 2. (2) Implement quadratic probing and compare clustering. (3) Explain why a tombstone may be reused by `put` but not ended at by `get`.

---

# Part C — Non-linear data structures

## Lesson 12 — Trees and the four traversals

**ATLAS status:** teaching only ([`TreeNode`, traversal functions](../dsa_lab/experiments.py)). The [UML class diagram](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/docs/UML_BLUEPRINT.md#app-class-diagram) itself is a tree-like hierarchy, but no tree ADT exists in ATLAS Go.

A **tree** is a connected, acyclic hierarchy of nodes. Vocabulary: **root** (no parent), **parent/child**, **siblings**, **leaf** (no children), **internal node**, **depth** of a node (edges from the root), **height** of a tree (**nodes** on the longest root-to-leaf path in this course), **subtree**. A **binary tree** gives each node at most two children, `left` and `right`.

~~~mermaid
flowchart TD
 R["8 (root, depth 0)"] --> L["4"]
 R --> M["12"]
 L --> A["2 (leaf)"]
 L --> B["6 (leaf)"]
 M --> C["10 (leaf)"]
 M --> D["14 (leaf, depth 2)"]
~~~

Height of this tree = 3 (nodes 8, 4, 2). Number of nodes in a *perfect* binary tree of height h = 2^h − 1, so h ≥ log₂(n + 1).

| Traversal | Rule | Order on the tree above | Uses |
|---|---|---|---|
| preorder | node, left, right | 8 4 2 6 12 10 14 | copy/serialise a tree |
| inorder | left, node, right | 2 4 6 8 10 12 14 | sorted output of a BST |
| postorder | left, right, node | 2 6 4 10 14 12 8 | delete/free a tree, evaluate expressions |
| level order | top to bottom, left to right | 8 4 12 2 6 10 14 | shortest path in edges, printing by level |

**Recursion vs an explicit stack/queue.** The three depth-first orders are naturally recursive; replacing the call stack by an explicit **stack** avoids Python's recursion limit. Level order needs a **queue**. The tree itself is stored as linked nodes; the stack and queue are only *auxiliary* structures used while walking.

~~~mermaid
flowchart LR
 DFS["depth-first: stack (LIFO)"] --> O1["preorder / inorder / postorder"]
 BFS["breadth-first: queue (FIFO)"] --> O2["level order"]
~~~

**Iterative inorder trace** (stack shown bottom → top):

| Step | Action | Stack | Output |
|---|---|---|---|
| 1 | push left spine 8, 4, 2 | 8 4 2 | |
| 2 | pop 2, visit; 2 has no right | 8 4 | 2 |
| 3 | pop 4, visit; go right to 6, push | 8 6 | 2 4 |
| 4 | pop 6, visit | 8 | 2 4 6 |
| 5 | pop 8, visit; go right: push 12, 10 | 12 10 | 2 4 6 8 |
| … | | | 2 4 6 8 10 12 14 |

~~~python
root = None
for key in (8, 4, 12, 2, 6, 10, 14):
    root = dsa.bst_insert_node(root, key)
assert dsa.inorder_stack(root) == dsa.inorder_recursive(root) == [2, 4, 6, 8, 10, 12, 14]
assert dsa.preorder_stack(root) == [8, 4, 2, 6, 12, 10, 14]
assert dsa.postorder_stack(root) == [2, 6, 4, 10, 14, 12, 8]
assert dsa.levelorder_queue(root) == [8, 4, 12, 2, 6, 10, 14]
assert dsa.tree_height(root) == 3
~~~

Every traversal is Θ(n) time. Extra space: O(h) for the depth-first stack, O(w) for the breadth-first queue (w = widest level, up to about n/2 in a complete tree); the output list itself is another O(n).

**Lab:** E19. **Exercises:** (1) Rebuild a tree from its preorder and inorder sequences. (2) Compute the width of every level with one BFS.

## Lesson 13 — Binary search trees: search, insert and the three deletion cases

**ATLAS status:** teaching only ([`bst_insert_node`, `bst_delete`](../dsa_lab/experiments.py)).

A **binary search tree (BST)** is a binary tree where, for every node, **all keys in the left subtree are smaller and all keys in the right subtree are larger**. This course stores **distinct keys**; inserting an existing key does nothing. Search follows one path: go left if the target is smaller, right if larger. Cost = height of the tree.

**Insertion order decides the shape.** Inserting 8, 4, 12, 2, 6, 10, 14 gives the perfect tree of Lesson 12 (height 3). Inserting 1, 2, 3, …, 7 gives a **skewed** tree — a linked list leaning right — with height 7.

~~~mermaid
flowchart TD
 subgraph skew["ascending inserts 1..4: height 4"]
 S1["1"] --> S2["2"] --> S3["3"] --> S4["4"]
 end
~~~

### Deletion — three cases

| Case | Example (tree of Lesson 12) | Action |
|---|---|---|
| leaf | delete 2 | remove it: parent's pointer becomes None |
| one child | delete 4 after 2 is gone | splice: parent points to 4's only child (6) |
| two children | delete 12 | copy the **inorder successor** (smallest key in the right subtree, 14) into 12's node, then delete 14 from the right subtree |

~~~mermaid
flowchart LR
 subgraph before["delete 12 (two children)"]
 A8["8"] --> A4["4"]
 A8 --> A12["12"]
 A12 --> A10["10"]
 A12 --> A14["14 = successor"]
 end
 subgraph after["after"]
 B8["8"] --> B4["4"]
 B8 --> B14["14"]
 B14 --> B10["10"]
 end
 before --> after
~~~

~~~python
root = None
for key in (8, 4, 12, 2, 6, 10, 14):
    root = dsa.bst_insert_node(root, key)
root = dsa.bst_delete(root, 2)        # leaf
root = dsa.bst_delete(root, 12)       # two children: 14 replaces 12
assert dsa.preorder_stack(root) == [8, 4, 6, 14, 10] and dsa.is_bst(root)
root = dsa.bst_delete(root, 4)        # one child: 6 moves up
assert dsa.inorder_stack(root) == [6, 8, 10, 14] and dsa.is_bst(root)
~~~

**Why the successor works:** it is larger than everything in the left subtree and smaller than everything else in the right subtree, so it can take the deleted node's place without breaking the ordering rule; it has no left child, so removing it is an easy case.

| Operation | Balanced (h ≈ log n) | Skewed (h = n) |
|---|---|---|
| search / insert / delete | O(log n) | O(n) |
| min / max | O(log n) | O(n) |
| inorder (sorted output) | O(n) | O(n) |

**Lab:** E10, E26. **Exercises:** (1) Delete using the inorder *predecessor* instead. (2) Prove that an inorder traversal of a BST is sorted. (3) Count BST shapes for 3 keys (there are 5).

## Lesson 14 — AVL trees and the four rotations

**ATLAS status:** teaching only ([`avl_insert`, `avl_delete`, `validate_avl`](../dsa_lab/experiments.py)).

An **AVL tree** is a BST that keeps itself balanced: at every node the **balance factor** BF = height(left) − height(right) must be −1, 0 or +1. Each node stores its height. After an insert or delete, walk back up the path, update heights and **rotate** at the first node whose BF becomes ±2. Rotations re-hang three nodes and their subtrees **without changing inorder order**, so the BST property survives.

| Imbalance at node z | Shape | Fix |
|---|---|---|
| LL: BF(z) = +2, BF(z.left) ≥ 0 | left child's left is heavy | single **right** rotation at z |
| RR: BF(z) = −2, BF(z.right) ≤ 0 | right child's right is heavy | single **left** rotation at z |
| LR: BF(z) = +2, BF(z.left) < 0 | left child's right is heavy | left rotation at z.left, then right at z |
| RL: BF(z) = −2, BF(z.right) > 0 | right child's left is heavy | right rotation at z.right, then left at z |

~~~mermaid
flowchart LR
 subgraph LLb["LL: insert 30, 20, 10"]
 a30["30 (BF +2)"] --> a20["20"] --> a10["10"]
 end
 subgraph LLa["right-rotate at 30"]
 b20["20"] --> b10["10"]
 b20 --> b30["30"]
 end
 LLb --> LLa
~~~

~~~mermaid
flowchart LR
 subgraph LRb["LR: insert 30, 10, 20"]
 c30["30"] --> c10["10"]
 c10 -- right --> c20["20"]
 end
 subgraph LRm["left-rotate at 10"]
 d30["30"] --> d20["20"] --> d10["10"]
 end
 subgraph LRa["right-rotate at 30"]
 e20["20"] --> e10["10"]
 e20 --> e30["30"]
 end
 LRb --> LRm --> LRa
~~~

**Right rotation in pointers** (y is the unbalanced node, x = y.left, T2 = x.right):

~~~text
      y              x
     / \            / \
    x   T3   →     T1  y
   / \                / \
  T1  T2             T2  T3        inorder T1 x T2 y T3 is unchanged
~~~

~~~python
for keys in ([30, 20, 10], [10, 20, 30], [30, 10, 20], [10, 30, 20]):   # LL, RR, LR, RL
    r = None
    for k in keys:
        r = dsa.avl_insert(r, k)
    assert r.key == 20 and dsa.validate_avl(r) == 2

t = None
for k in range(1, 16):                 # ascending inserts: a plain BST would have height 15
    t = dsa.avl_insert(t, k)
assert dsa.validate_avl(t) == 4 and t.key == 8
for k in (1, 2, 3, 4, 5):              # full AVL deletion rebalances on the way up
    t = dsa.avl_delete(t, k)
    dsa.validate_avl(t)
assert dsa.inorder_stack(t) == list(range(6, 16))
~~~

An AVL tree of height h has at least F(h+2) − 1 nodes (F = Fibonacci), so **h < 1.45 log₂(n + 2)**: search, insert and delete are all O(log n) worst case. Red-black trees (used by Java's `TreeMap`) relax balance slightly to rotate less often.

**Lab:** E20, E26. **Exercises:** (1) Insert 50, 40, 60, 30, 45, 35 by hand and draw each rotation. (2) Find a deletion that triggers rotations at two different levels.

## Lesson 15 — Binary heaps, priority queues and heap sort

**ATLAS link:** [`intelligence.rank`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py) sorts all candidates; if only the best k were needed, a heap (`heapq.nsmallest`) would do it in O(n log k).

A **binary min-heap** is a **complete** binary tree (every level full except possibly the last, filled left to right) in which every parent ≤ its children. It is *not* a BST: siblings are unordered. Completeness lets it live in an array with **no pointers**: children of i are 2i+1 and 2i+2, the parent of i is (i−1)//2.

~~~mermaid
flowchart TD
 A["[0] 1"] --> B["[1] 3"]
 A --> C["[2] 2"]
 B --> D["[3] 5"]
 B --> E["[4] 9"]
 C --> F["[5] 8"]
~~~

Array form: `[1, 3, 2, 5, 9, 8]`.

| Operation | How | Cost |
|---|---|---|
| `peek` | `a[0]` | O(1) |
| `push(x)` | append, then **sift up** (swap with parent while smaller) | O(log n) |
| `pop()` | move last to root, then **sift down** (swap with smaller child) | O(log n) |
| `heapify(list)` | sift down every internal node, from the last to the root | **O(n)** |

**Why heapify is O(n), not O(n log n):** half the nodes are leaves (no work), a quarter sift at most one level, an eighth two levels… Σ (n/2^{k+1})·k ≤ n. E24 counts the swaps: bottom-up heapify needs far fewer than n successive pushes.

~~~python
h = dsa.MinHeap([5, 3, 8, 1, 9, 2])          # bottom-up heapify
assert h.is_heap() and h.peek() == 1
assert [h.pop() for _ in range(6)] == [1, 2, 3, 5, 8, 9]

import heapq                                   # the standard library version
jobs = []
for priority, name in ((5, "later"), (1, "urgent"), (3, "normal")):
    heapq.heappush(jobs, (priority, name))
assert heapq.heappop(jobs) == (1, "urgent")
~~~

**Heap sort** = heapify (O(n)) + n pops (O(n log n)) in place, O(1) extra space, **not stable**. **Priority queues** built on heaps drive Dijkstra's algorithm (Lesson 18), event simulations and schedulers.

**Lab:** E24. **Exercises:** (1) Implement `decrease_key` with a position map. (2) Find the k largest of a million numbers with a size-k min-heap.

## Lesson 16 — Tries (prefix trees)

**ATLAS status:** teaching only ([`Trie`](../dsa_lab/experiments.py)). A natural extension would be place-name autocomplete in the booking form.

A **trie** stores strings character by character along paths from the root; words that share a prefix share the path. A marker (`$`) says "a word ends here". Lookup and insertion cost O(L) for a word of length L, **independent of how many words are stored**.

~~~mermaid
flowchart TD
 R["root"] --> C["c"] --> CA["a"]
 CA --> CAR["r $"] --> CART["t $"]
 CA --> CAT["t $"]
 R --> D["d"] --> DO["o"] --> DOG["g $"]
~~~

Stored: car, cart, cat, dog. "ca" is a valid **path** but not a **word** (no `$`).

~~~python
t = dsa.Trie(["cat", "car", "cart", "dog"])
assert t.contains("car") and not t.contains("ca")
assert t.starts_with("ca") == ["car", "cart", "cat"]
assert t.delete("cart") and not t.contains("cart") and t.contains("car")   # prunes the 't' node
~~~

**Prefix query:** walk the prefix (L steps), then collect the subtree. Scanning a list of n words with `startswith` examines all n. E25 shows the trie walking 3 characters while the scan examines every word. Cost: memory — one dict per node.

**Lab:** E25. **Exercises:** (1) Count words with a given prefix in O(L) by storing counts in nodes. (2) Implement a compressed (radix) trie.

## Lesson 17 — Graphs: representations, BFS and DFS

**ATLAS link / limitation:** [`geo.haversine_km`, `geo.nearest_place`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/geo.py) compute straight-line distances and [`LiveMap._route`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/livemap.py) draws a route; ATLAS Go does **not** run graph search over a road network. The graph algorithms here are teaching implementations.

A **graph** G = (V, E) has vertices and edges; edges may be **directed** or **undirected**, **weighted** or not. Representations:

~~~mermaid
flowchart LR
 A["A"] --> B["B"]
 A --> C["C"]
 B --> D["D"]
 C --> D
~~~

| Representation | Above graph | Space | "Is (u, v) an edge?" | "List neighbours of u" |
|---|---|---|---|---|
| adjacency list | A:[B, C] B:[D] C:[D] D:[] | O(V + E) | O(deg u) | O(deg u) |
| adjacency matrix | 4×4 of 0/1, row A = 0 1 1 0 | O(V²) | O(1) | O(V) |
| edge list | (A,B) (A,C) (B,D) (C,D) | O(E) | O(E) | O(E) |

**BFS** (breadth-first) uses a **queue** and visits vertices in rings of increasing edge distance, so it finds **shortest paths by number of edges** in unweighted graphs. **DFS** (depth-first) uses a **stack** (or recursion) and follows one branch as deep as possible; it finds cycles, connected components and topological orders. Both are Θ(V + E) with adjacency lists — every vertex is enqueued/pushed once, every edge examined once (twice if undirected).

| Step | BFS queue | BFS visited | DFS stack | DFS visited |
|---|---|---|---|---|
| start | [A] | | [A] | |
| 1 | [B, C] | A | [C, B] | A |
| 2 | [C, D] | A B | [C, D] | A B |
| 3 | [D] | A B C | [C] | A B D |
| 4 | [] | A B C D | [] | A B D C |

~~~python
g = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
assert dsa.bfs(g, "A") == ["A", "B", "C", "D"]
assert dsa.dfs(g, "A") == ["A", "B", "D", "C"]
dist, examined = dsa.bfs_distances(g, "A")
assert dist == {"A": 0, "B": 1, "C": 1, "D": 2} and examined == 4   # each edge once
~~~

**Lab:** E11. **Exercises:** (1) Count connected components of an undirected graph. (2) Detect whether a graph is bipartite with BFS colouring.

## Lesson 18 — Shortest paths, topological order, union-find and spanning trees

### Dijkstra's algorithm (non-negative weights)

Keep a tentative distance for every vertex; repeatedly take the closest unfinished vertex from a **min-heap** and **relax** its outgoing edges (`if dist[u] + w < dist[v]: dist[v] = dist[u] + w`). With a binary heap: O((V + E) log V). **Requires w ≥ 0** — a negative edge could make a "finished" vertex cheaper later (use Bellman–Ford instead).

~~~mermaid
flowchart LR
 A["A (0)"] -->|"2"| B["B (2)"]
 A -->|"8"| C["C (8 → 3)"]
 B -->|"1"| C
~~~

| Pop | dist A | dist B | dist C | heap after |
|---|---|---|---|---|
| A (0) | 0 | 2 | 8 | (2,B) (8,C) |
| B (2) | 0 | 2 | **3** | (3,C) (8,C) |
| C (3) | done | | | (8,C) is stale: skipped |

~~~python
g = {"A": [("B", 2), ("C", 8)], "B": [("C", 1)], "C": []}
assert dsa.dijkstra(g, "A") == {"A": 0, "B": 2, "C": 3}
assert dsa.dijkstra_path(g, "A", "C") == (["A", "B", "C"], 3)
~~~

### Topological sort (DAGs only)

A **topological order** lists the vertices of a **directed acyclic graph** so that every edge goes forward — e.g. the steps of a food order: accept → cook → pack → deliver. **Kahn's algorithm** repeatedly removes a vertex of in-degree 0; if vertices remain at the end, the graph has a cycle and no order exists. DFS gives the same result by reversing finishing times. Both Θ(V + E).

~~~mermaid
flowchart LR
 shop["accept order"] --> cook --> pack --> deliver
 cook --> notify["notify courier"]
~~~

~~~python
dag = {"accept": ["cook"], "cook": ["pack", "notify"], "pack": ["deliver"], "notify": [], "deliver": []}
order, processed = dsa.topo_sort_kahn(dag)
assert order.index("cook") < order.index("pack") < order.index("deliver") and processed == 4
try:
    dsa.topo_sort_kahn({1: [2], 2: [1]})
except ValueError as e:
    print(e)                                    # graph has a cycle
~~~

### Union-find (disjoint sets)

Maintain a partition of items into groups with `find(x)` (which group?) and `union(a, b)` (merge). Each group is a tree of parent pointers; the root names the group. **Union by rank** hangs the shorter tree under the taller; **path compression** points every visited node straight at the root. Together: amortised O(α(n)) per operation, where α is the inverse Ackermann function (≤ 4 for any practical n). E27 shows the naive version doing millions of pointer hops where the optimised one does a few thousand.

~~~python
uf = dsa.UnionFind(5)
uf.union(0, 1); uf.union(3, 4)
assert uf.find(0) == uf.find(1) and uf.find(0) != uf.find(3) and uf.components == 3
~~~

### Minimum spanning tree (Kruskal)

Sort edges by weight and add each edge that joins two different components (checked with union-find). Greedy, and provably optimal (cut property). O(E log E).

~~~python
tree, total = dsa.kruskal(4, [(1, 0, 1), (3, 1, 2), (2, 0, 2), (4, 2, 3)])
assert total == 7 and len(tree) == 3          # V − 1 edges
~~~

**Lab:** E12, E27, E28. **Exercises:** (1) Show Dijkstra failing with a negative edge. (2) Use BFS instead of Dijkstra when all weights are 1 and compare results.

---

# Part D — Algorithm design

## Lesson 19 — Searching

**ATLAS link:** [`LocalStore.online_drivers`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) is a linear filter; [`geo.nearest_place`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/geo.py) is a minimum search.

| Method | Precondition | Worst case | Notes |
|---|---|---|---|
| linear search | none | Θ(n) | works on linked lists and unsorted data |
| binary search | **sorted, random access** | Θ(log n) | halve the interval each step |
| hash lookup | hashable keys | Θ(1) expected | Lesson 11 |
| BST search | balanced tree | Θ(log n) | Lessons 13–14 |

**Binary search trace** for 12 in `[2, 4, 6, 8, 10, 12, 14]`:

| lo | hi | mid | a[mid] | decision |
|---|---|---|---|---|
| 0 | 6 | 3 | 8 | 12 > 8 → lo = 4 |
| 4 | 6 | 5 | 12 | **found at 5** |

Invariant: *if 12 is in the list, its index lies in [lo, hi]*. Each step keeps the invariant and shrinks hi − lo, so the loop terminates.

~~~python
a = [2, 4, 6, 8, 10, 12, 14]
assert dsa.binary_search(a, 12) == (5, 2)
assert dsa.binary_search(a, 7) == (-1, 3)
assert dsa.first_occurrence([1, 2, 2, 2, 3], 2) == 1      # leftmost duplicate
import bisect
assert bisect.bisect_left([1, 2, 2, 2, 3], 2) == 1         # the standard-library equivalent
~~~

Common bugs: `mid = (lo + hi) // 2` with `hi = len(a)` and `lo <= hi` (off by one); forgetting `mid ± 1` (infinite loop); using binary search on unsorted data.

**Lab:** E02, E03, E09.

## Lesson 20 — Sorting, stability and the n log n lower bound

**ATLAS link:** [`intelligence.rank`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py) relies on Python's `sorted` (Timsort: stable, O(n log n) worst case, O(n) on already-sorted runs).

~~~mermaid
flowchart TD
 A["[7, 2, 6, 1]"] --> B["[7, 2]"]
 A --> C["[6, 1]"]
 B --> B1["[7]"]
 B --> B2["[2]"]
 C --> C1["[6]"]
 C --> C2["[1]"]
 B1 --> M1["merge → [2, 7]"]
 B2 --> M1
 C1 --> M2["merge → [1, 6]"]
 C2 --> M2
 M1 --> F["merge → [1, 2, 6, 7]"]
 M2 --> F
~~~

| Algorithm | Idea | Best | Average | Worst | Extra space | Stable |
|---|---|---|---|---|---|---|
| bubble (early exit) | swap adjacent inversions | Θ(n) | Θ(n²) | Θ(n²) | O(1) | yes |
| selection | swap minimum into place | Θ(n²) | Θ(n²) | Θ(n²) | O(1) | **no** |
| insertion | grow a sorted prefix | Θ(n) | Θ(n²) | Θ(n²) | O(1) | yes |
| merge | split, sort halves, merge | Θ(n log n) | Θ(n log n) | Θ(n log n) | O(n) | yes |
| quick (in place, random pivot) | partition around a pivot | Θ(n log n) | Θ(n log n) expected | Θ(n²) | O(log n) expected | no |
| heap | heapify, pop maximum | Θ(n log n) | Θ(n log n) | Θ(n log n) | O(1) | **no** |
| counting | count occurrences of each key 0..k | Θ(n + k) | Θ(n + k) | Θ(n + k) | O(n + k) | yes |

The lab also contains `quick_sort`, a *functional* three-way quicksort that copies lists (easy to read, not in place). **Stability** means records with equal keys keep their input order — essential when you sort by a second key after a first (sort by name, then stably by rating). E15 counts stability violations: merge and insertion sort produce 0, heap sort hundreds.

~~~python
records = [(1, "a"), (0, "b"), (1, "c"), (0, "d")]
by_key = lambda r: r[0]
assert dsa.merge_sort(records, key=by_key)[0] == [(0, "b"), (0, "d"), (1, "a"), (1, "c")]
assert dsa.counting_sort([3, 0, 2, 3, 1], upper=3) == [0, 1, 2, 3, 3]
assert dsa.quick_sort_inplace([5, 1, 4, 2, 3])[0] == [1, 2, 3, 4, 5]
~~~

**Why no comparison sort beats n log n:** a comparison sort is a binary decision tree whose leaves are the n! possible orderings; a tree with n! leaves has height ≥ log₂ n! = Θ(n log n). Counting sort escapes the bound because it does not compare keys.

**Lab:** E04, E05, E15. **Exercises:** (1) Make selection sort stable. (2) Show the quicksort worst case with a first-element pivot on sorted input.

## Lesson 21 — Recursion and divide-and-conquer

A **recursive** function solves a problem by calling itself on smaller inputs. It needs a **base case** that stops the recursion and a **progress** argument that every call is smaller. Each active call is a **stack frame**; Python's default limit is about 1 000 frames.

~~~mermaid
flowchart TD
 F["fib(4)"] --> A["fib(3)"]
 F --> B["fib(2)"]
 A --> C["fib(2) — repeated!"]
 A --> D["fib(1)"]
 C --> E["fib(1)"]
 C --> G["fib(0)"]
 B --> H["fib(1)"]
 B --> I["fib(0)"]
~~~

Naive Fibonacci makes 177 calls for fib(10) and 242 785 for fib(25) because the same subproblems are solved again and again (E13).

**Divide and conquer:** *divide* into independent subproblems, *conquer* recursively, *combine*. Merge sort (Lesson 20), binary search (Lesson 19), quickselect, Karatsuba multiplication and closest-pair-of-points all follow this pattern; the master theorem (Lesson 3) gives their cost.

~~~python
def power(x, n):                       # x**n with O(log n) multiplications
    if n == 0:
        return 1                        # base case
    half = power(x, n // 2)             # smaller problem
    return half * half * (x if n % 2 else 1)

assert power(3, 13) == 3 ** 13
assert dsa.fib_naive_calls(10) == (55, 177)
~~~

**Lab:** E13.

## Lesson 22 — Greedy algorithms, dynamic programming and backtracking

**ATLAS link / limitation:** [`intelligence.choose`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py) greedily picks the best-scored driver for each request. Greedy choice per request is **not** proven globally optimal for a whole day of dispatch — exactly the gap greedy algorithms must close with a proof.

| Paradigm | Idea | Needs | Example in the lab |
|---|---|---|---|
| greedy | take the locally best choice, never undo | a proof (exchange argument / cut property) | `interval_schedule`, `kruskal` |
| dynamic programming | solve each overlapping subproblem once, store it | optimal substructure + overlapping subproblems | `fib_memo_calls`, `fib_dp`, `knapsack_01` |
| backtracking | extend a partial solution, undo when it fails | a way to prune | `n_queens` |

**Greedy interval scheduling.** Choose the most non-overlapping bookings: sort by **finishing time** and take each that starts after the last chosen one ends. (Choosing the *shortest* or *earliest-starting* first can fail.)

~~~python
bookings = [(1, 4), (3, 5), (0, 6), (5, 7), (8, 9), (5, 9)]
assert dsa.interval_schedule(bookings) == [(1, 4), (5, 7), (8, 9)]
~~~

**Dynamic programming — 0/1 knapsack.** best[i][c] = best value using the first i items with capacity c = max(skip item i, take it if it fits). Table size (n+1)(W+1): Θ(nW) time.

| item | weight | value |
|---|---|---|
| 0 | 1 | 1 |
| 1 | 3 | 4 |
| 2 | 4 | 5 |
| 3 | 5 | 7 |

~~~python
assert dsa.knapsack_01([1, 3, 4, 5], [1, 4, 5, 7], 7) == (9, [1, 2])   # weights 3+4, value 4+5
assert dsa.fib_memo_calls(25)[1] == 49 and dsa.fib_dp(25) == 75025
~~~

A greedy "best value per kilo" rule picks item 3 (7/5 = 1.4) then item 0 → value 8 < 9: greedy is not optimal for 0/1 knapsack.

**Backtracking — N-queens.** Place one queen per row; skip columns and diagonals already attacked; undo on dead ends. 8 queens has 92 solutions.

~~~python
solutions, tried = dsa.n_queens(8)
assert solutions == 92
print("placements tried:", tried, "of", 8 ** 8, "naive")
~~~

**Lab:** E13. **Exercises:** (1) Longest common subsequence of two strings with a DP table. (2) Coin change with coins {1, 3, 4} for amount 6: show greedy fails.

## Lesson 23 — Proving correctness and testing invariants

**ATLAS link:** [`LocalStore.validate`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) rejects corrupt saved state; [`snapshot`/`commit`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) restore the previous state if saving fails; [`intelligence.self_test`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py) runs model smoke tests on the device.

**Loop invariant proof** in five steps:

~~~mermaid
flowchart LR
 P["precondition"] --> I["invariant true<br/>before the loop"]
 I --> S["one iteration<br/>keeps it true"]
 S --> T["loop terminates"]
 T --> Q["invariant + exit<br/>condition ⇒ postcondition"]
~~~

**Structural invariants** are the executable version: every structure in the lab has a `validate()` that the experiments call after every change.

| Structure | Invariant checked |
|---|---|
| singly list | walk reaches `tail` in exactly `size` steps |
| doubly list | `p.next.prev is p` for every node |
| circular singly | `size` steps from the head return to the head through `tail` |
| circular doubly + sentinel | every `next.prev` is its own node; `size` nodes between sentinel visits |
| ring buffer | 0 ≤ count ≤ capacity; `to_list` has `count` items |
| hash table | every node sits in bucket `hash(key) mod m`; total = size |
| BST / AVL | ordering, stored heights, |BF| ≤ 1 |
| heap | parent ≤ child for every index |
| sorted output | non-decreasing **and** a permutation of the input |

~~~python
import random
rng = random.Random(1)
for trial in range(200):                       # randomised differential testing
    data = [rng.randrange(50) for _ in range(rng.randrange(30))]
    for sort in (dsa.merge_sort, dsa.heap_sort, dsa.insertion_sort, dsa.quick_sort):
        out = sort(data)[0]
        assert out == sorted(data)              # oracle: Python's sorted
~~~

Run `python dsa_lab/experiments.py` to execute all self-tests (70+ assert statements, many inside loops, covering every structure and edge case in this guide).

---

# Part E — Practice

## Lesson 24 — Laboratory protocol and the 30 experiments

Run all experiments locally with `python dsa_lab/experiments.py --all` (≈ 10 s) or in [Colab](https://colab.research.google.com/github/FUllSCIPTS/ATLAS/blob/main/dsa_lab/DSA_Colab_Labs.ipynb). Each writes `EXX_name.csv` and `EXX_name.png`; `--diagrams` also draws the structures. Seed 2026; times are medians of 5 runs.

| ID | name | Question | Columns plotted | Lesson |
|---|---|---|---|---|
| E01 | growth | How fast do n, n log n, n² grow? | operation counts | 2–3 |
| E02 | search | Linear vs binary comparisons for an absent key | comparisons | 19 |
| E03 | search_cases | Best / average / worst linear search | comparisons | 3 |
| E04 | sort | Bubble vs merge vs quick on the same input | comparisons | 20 |
| E05 | sort_cases | Insertion sort on sorted / random / reversed | comparisons | 3, 20 |
| E06 | runtime | Measured time of search and sort | ms | 2 |
| E07 | array_linked | n front insertions: list vs linked list | ms (log) | 4–5 |
| E08 | stack_queue | Draining n items: pop(), popleft(), pop(0) | ms | 9–10 |
| E09 | hash | n lookups: dict, scan, bisect | ms | 11, 19 |
| E10 | bst | Search path in balanced vs skewed BST | nodes | 13 |
| E11 | graph | BFS/DFS edge examinations vs E | edges | 17 |
| E12 | shortest_path | Dijkstra relaxations and heap pushes vs E | operations | 18 |
| E13 | recursion_dp | Fibonacci calls: naive, memo, loop | calls (log) | 21–22 |
| E14 | memory | Peak traced KiB of list, dict, deque | KiB | 2 |
| E15 | sorting_stability | Equal-key order violations | pairs | 20 |
| E16 | hash_singly | Singly chained table vs 1 + α/2 | nodes | 11 |
| E17 | hash_doubly | Doubly chained table after deletes | nodes | 6, 11 |
| E18 | hash_load | Uniform vs adversarial keys | comparisons (log) | 11 |
| E19 | tree_stack_queue | Iterative traversals | ms | 12 |
| E20 | avl | AVL vs plain BST after ascending inserts | nodes | 14 |
| E21 | circular_singly | Josephus: ring pointer moves vs list shifts | operations | 7 |
| E22 | circular_doubly | LRU: sentinel list vs list vs OrderedDict | µs/op | 8 |
| E23 | ring_buffer | FIFO: ring buffer vs deque vs pop(0) | ms (log) | 10 |
| E24 | heap | Heapify vs n pushes | swaps | 15 |
| E25 | trie | Prefix query: trie walk vs scan | operations (log) | 16 |
| E26 | bst_delete | Height after deleting half the keys | nodes | 13–14 |
| E27 | union_find | Naive vs rank vs rank + compression | hops (log) | 18 |
| E28 | topo_sort | Kahn vs DFS edges processed | edges | 18 |
| E29 | open_addressing | Probes vs load factor, with theory curve | probes | 11 |
| E30 | dynamic_array | Copies for doubling, ×1.5, +16 | copies (log) | 4 |

**Report for every experiment:** (a) question, (b) hypothesis with a predicted bound, (c) input sizes and distribution, (d) basic operation or timing method, (e) chart and CSV, (f) derivation of the bound, (g) where measurement disagrees with theory and why, (h) one extension.

**Worked analysis — E21.** *Hypothesis:* the circular list needs n(k−1) pointer moves (linear), the Python list Θ(n²) element shifts. *Result at n = 512, k = 3:* 1 024 moves vs 78 544 shifts; the moves column equals the n(k−1) reference exactly. *Discussion:* `list.pop(i)` shifts with a fast C `memmove`, so wall-clock times differ far less than the counts — the reason this experiment counts operations rather than timing them.

**Worked analysis — E23.** *Result:* below ~4 000 items `list.pop(0)` is faster than the pure-Python ring buffer; at 32 768 items it was about 7× slower on our test machine (your numbers will differ; the shape will not). Constant factors decide small inputs; growth rates decide large ones.

## 15-week teaching plan

| Week | Theory (2 h) | Lab (2 h) | Deliverable |
|---|---|---|---|
| 1 | Lesson 1–2: ADTs, counting | E01, E02 | contracts + first chart |
| 2 | Lesson 3: O/Ω/Θ, cases, recurrences | E03, E05 | cases table with bounds |
| 3 | Lesson 4: arrays, dynamic arrays | E07, E30 | amortised-cost derivation |
| 4 | Lessons 5–6: singly and doubly lists | E07, list self-tests | delete-all-cases implementation |
| 5 | Lesson 7: circular singly lists | E21 | Josephus report |
| 6 | Lesson 8: circular doubly, sentinel, LRU, Floyd | E22 | LRU cache with tests |
| 7 | Lessons 9–10: stacks, queues, ring buffers | E08, E23 | postfix evaluator; ring buffer |
| 8 | Lesson 11: hashing | E09, E16–E18, E29 | load-factor analysis |
| 9 | Lessons 12–13: trees, BST, deletion | E10, E19, E26 | BST with all deletion cases |
| 10 | Lesson 14: AVL | E20, E26 | rotation traces |
| 11 | Lessons 15–16: heaps, tries | E24, E25 | top-k and autocomplete |
| 12 | Lesson 17: graphs, BFS, DFS | E11 | components / bipartite |
| 13 | Lesson 18: Dijkstra, topo sort, union-find | E12, E27, E28 | shortest-path verification |
| 14 | Lessons 19–22: search, sort, D&C, greedy, DP | E04, E13, E15 | DP table + greedy counterexample |
| 15 | Lesson 23: correctness; review | mini-project | research-style report |

## Assessment (100 marks)

Theory derivations 20 · correct code including edge cases 25 · experimental protocol 20 · interpretation of charts and tables 20 · reproducibility and written discussion 15. Every report must include one case where a measurement contradicts a naive prediction and explain why (E07, E23 and E29 provide good candidates).

## Exercise bank

1. Prove the triangular loop count n(n−1)/2 and the insertion-sort worst case equal it.
2. Binary search for the first and last occurrence of a duplicate key.
3. Row-major vs column-major traversal of a NumPy array; explain cache lines.
4. Singly list: delete all occurrences of a value in one pass.
5. Circular list: split into two circular halves; insert into a sorted ring.
6. Circular doubly list: implement a playlist with `next`, `prev`, `remove_current`.
7. LRU cache with a time-to-live per entry.
8. Ring buffer that overwrites the oldest entry; use it to keep the last 100 GPS fixes.
9. Hash table: implement double hashing; compare clusters with linear probing at α = 0.8.
10. Full AVL deletion by hand for a 12-node tree; verify with `validate_avl`.
11. Heap-based dispatch simulation: 1 000 requests with priorities; report waiting times.
12. Trie autocomplete for Cork place names; rank suggestions by frequency.
13. Dijkstra vs BFS on unit weights: prove the results coincide.
14. Topological order for the ATLAS food-order lifecycle; add a cycle and detect it.
15. Mini-project: a ride-booking simulator using a queue of requests, a hash map of drivers, a heap of available drivers by distance and a graph of zones; report operation counts.

**Further reading:** Cormen, Leiserson, Rivest, Stein — *Introduction to Algorithms*; Pat Morin — *Open Data Structures* (free); Sedgewick & Wayne — *Algorithms*; Python documentation for `collections`, `heapq`, `bisect`, `tracemalloc`.
