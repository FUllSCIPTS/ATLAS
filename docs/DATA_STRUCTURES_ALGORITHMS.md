# Data Structures and Algorithms — foundations to experimental analysis

**Course format:** 15 teaching weeks · 2 h theory + 2 h lab weekly · Python 3 / Google Colab. **Audience:** complete beginners through intermediate students. This is an independent course; it does not assert that ATLAS deploys every algorithm.

## Navigate to ATLAS Go UML and function catalogue

The app's complete [ATLAS Go UML class diagrams and function inventory](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/docs/UML_BLUEPRINT.md#android-app-atlas-go) are maintained on the **`architecture-explorer` branch**; the [generated Python class/function catalogue](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/docs/ARCHITECTURE.md#complete-source-method-catalog) is on **`main`**. Source links below point to code on `main`. Read them alongside each lesson to identify where the concept appears in the actual application.

**Status legend:** **Implemented in ATLAS Go** means a named function or Python collection actually exists in `android-app/atlas_go/`. **Related application concept** means the app has related behavior but not necessarily the named data structure or algorithm. **Teaching only** means the implementation is in `dsa_lab/`, not the ATLAS Go app.

| DSA topic | Exact ATLAS Go class/function or status | Useful source and catalogue |
|---|---|---|
| ADT / operations | **Implemented:** `LocalStore.book`, `checkout`, `commit` | [store.py](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) · [LocalStore UML](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/docs/UML_BLUEPRINT.md#app-class-diagram) |
| Lists, scans, filtering | **Implemented:** `LocalStore.online_drivers`, `my_history`, `Catalog.menu` | [store.py](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) · [domain.py](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/domain.py) |
| Strings and input validation | **Implemented:** `accounts.clean_name`, `clean_email`, `clean_phone` | [accounts.py](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/accounts.py) |
| Dictionaries / hashing | **Implemented:** `Cart.items`, `Catalog.dishes`, `LocalStore.failures` (Python dict, not linked chaining) | [domain.py](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/domain.py) · [store.py](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) |
| Sorting and ranking | **Implemented:** `intelligence.rank` uses `sorted`; `choose` consumes ranking | [intelligence.py](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py) |
| Selection / nearest | **Implemented:** `geo.nearest_place` uses minimum Haversine distance over saved places | [geo.py](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/geo.py) |
| Geographic visualization | **Implemented:** `geo.ride_position`, `LiveMap.visible_tiles`, `LiveMap._route` | [geo.py](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/geo.py) · [livemap.py](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/livemap.py) |
| State transitions | **Related concept:** `LocalStore.driver_advance`, `advance_ride`, `advance_order` (not a queue ADT) | [store.py](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) · [Lifecycle UML](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/docs/UML_BLUEPRINT.md#on-device-ride-and-order-lifecycles) |
| Linked-list hash chains | **Teaching only:** `ChainHash`, `SNode`, `DNode` | [DSA experiments E16–E18](../dsa_lab/experiments.py) |
| Stack/queue BST traversal | **Teaching only:** `inorder_stack`, `postorder_stack`, `levelorder_queue` | [DSA experiment E19](../dsa_lab/experiments.py) |
| AVL trees / rotations | **Teaching only:** `avl_insert`, `avl_rotate_left`, `avl_rotate_right` | [DSA experiment E20](../dsa_lab/experiments.py) |
| BFS, DFS, Dijkstra | **Teaching only:** graph algorithms in DSA lab; no verified ATLAS Go road-network shortest-path algorithm | [DSA experiments E11–E12](../dsa_lab/experiments.py) |
| Heap, trie, DP examples | **Teaching only:** illustrated ideas here (DP timing in DSA E13); not identified as ATLAS Go APIs | [DSA laboratory](../dsa_lab/experiments.py) |
| Correctness / consistency | **Implemented:** `LocalStore.validate`, `snapshot`, `commit`; `intelligence.self_test` | [store.py](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) · [intelligence.py](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py) |

For complete method signatures rather than just names, use the [ATLAS Go class/function catalogue](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/docs/ARCHITECTURE.md#complete-source-method-catalog) and the [full UML blueprint](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/docs/UML_BLUEPRINT.md). The UML blueprint also describes separate **starter back-end** components: do not confuse planned/server starter functions with code running inside today's on-device ATLAS Go app.

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


# Fully illustrated, standalone lessons

**How to use these lessons:** Read the definition; trace the diagram by hand; calculate the worked example; run the Python snippet in Colab; compare the theory with the 20 labs. All Mermaid figures below are source-controlled and render directly on GitHub. Sizes: n=items; V=vertices; E=edges; h=tree height; w=maximum width; m=hash buckets; α=n/m. A comparison count and a runtime in milliseconds are different measurements.

## Lesson 1 — Problem, algorithm, data structure, and ADT

**ATLAS Go implementation link:** [`LocalStore.book`, `LocalStore.checkout`, `LocalStore.commit`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) illustrate concrete operations and persistence. Browse the [UML Android app overview](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/docs/UML_BLUEPRINT.md#android-app-atlas-go) and [function catalogue](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/docs/ARCHITECTURE.md#complete-source-method-catalog) for class contracts. They are real app methods, not implementations of the lab's abstract queue.



A **problem** specifies an input and desired output; an **algorithm** gives finite, unambiguous steps to obtain that output; a **data structure** organizes values to support those steps. An **abstract data type (ADT)** defines behavior and operations independently of representation. Example: a waiting line is a queue ADT; a linked deque is one implementation; dequeue is an operation; serving the earliest customer is the goal.

~~~mermaid
flowchart LR
 A["Problem: serve arrivals fairly"] --> B["ADT: FIFO queue"]
 B --> C["Implementation: linked deque"]
 C --> D["Algorithm: enqueue arrivals; dequeue next"]
 D --> E["Output: service order"]
~~~

**Worked example:** Find 7 in [2,7,9]. Compare 2 and then 7: two comparisons; returned index is 1 (zero-based). Finding absent 6 takes three comparisons. Python:

~~~python
def linear_search(a, target):
    for i, value in enumerate(a):
        if value == target: return i
    return -1
assert linear_search([2,7,9], 7) == 1
~~~

An algorithm should state **preconditions** (e.g., sorted input for binary search), **postconditions** (correct result) and **termination**. A **loop invariant** is a statement true before and after each iteration, useful for correctness proofs. Linear search invariant: every already inspected position does not contain the target (unless the method returned). **Lab:** E02.

## Lesson 2 — Counting operations and actually measuring complexity

**ATLAS Go implementation link:** [`LocalStore.online_drivers`, `LocalStore.my_history`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) perform scans with list comprehensions; [`intelligence.rank`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py) scores and sorts driver candidates. Use them to count how work scales with accounts, history or candidates. [Source method catalogue](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/docs/ARCHITECTURE.md#complete-source-method-catalog).



Define n first: for an array it is length, for a graph use V and E, for a 2D matrix use rows and columns. Choose a basic operation: a comparison, swap, hash probe or node visit. A single loop with n visits costs n; nested full loops n²; a triangular loop costs 0+1+...+(n−1)=n(n−1)/2. At n=5 this is 10 operations, at n=10 it is 45.

~~~mermaid
flowchart TD
 N["Input size n"] --> A["One loop: n"]
 N --> B["Two full nested loops: n²"]
 N --> C["Halve input repeatedly: log₂ n"]
 N --> D["Split and merge: n log₂ n"]
~~~

~~~python
def triangle(n):
    steps = 0
    for i in range(n):
        for j in range(i):
            steps += 1
    return steps
assert triangle(5) == 10
~~~

**Runtime measurement:** Time the same operation on controlled inputs with time.perf_counter, repeat at least five times and report median plus spread. **Space measurement:** tracemalloc observes traced Python allocations, not total resident memory. Keep data preparation outside timed regions unless it is part of the target algorithm. Re-run with independent random seeds, validate output, note Python/hardware versions and report graph units. Operation counts support mathematical analysis; wall-clock plots alone cannot establish Big-O.

~~~python
import time, statistics, tracemalloc
def median_ms(task, repeats=9):
    times=[]
    for _ in range(repeats):
        t=time.perf_counter(); task()
        times.append(1000*(time.perf_counter()-t))
    return statistics.median(times)
tracemalloc.start()
a=list(range(1000))
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print("Peak traced KiB",peak/1024)
~~~

**Labs:** E01,E06,E14.

## Lesson 3 — Big O, Big Ω and Big Θ

**ATLAS Go implementation link:** [`online_drivers`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) is a practical candidate for O(n) scan analysis, while [`rank`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py) uses Python `sorted` after scoring candidates. These are implementation examples, not claims of measured app-wide bounds. [UML/function catalogue](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/docs/ARCHITECTURE.md#complete-source-method-catalog).

 (the three notations)

For nonnegative functions f and g, **O(g)** is an eventual upper bound: f(n) ≤ c₂g(n) for sufficiently large n; **Ω(g)** is an eventual lower bound f(n) ≥ c₁g(n); **Θ(g)** means both. These bound a chosen function and do **not** automatically mean worst, best or average case.

~~~mermaid
flowchart TD
 F["Complexity f(n)"] --> O["O(g): upper bound"]
 F --> M["Ω(g): lower bound"]
 O --> T["Θ(g): both bounds = tight"]
 M --> T
~~~

**Proof example:** f(n)=3n²+5n+8. For n≥1, 3n² ≤ f(n) ≤ 16n², hence Θ(n²); O(n³) is true but loose. Relative growth for input 64: log₂n=6, n=64, nlog₂n=384, n²=4096. **Cases are separate:** linear search first element takes 1 comparison, absent element n, and uniformly random successful index (n+1)/2 expected comparisons. Hence its best Θ(1), average successful Θ(n), worst Θ(n). **Lab:** E03.

## Lesson 4 — Arrays, 2D and 3D indexing, and strings

**ATLAS Go implementation link:** [`LocalStore.reset`, `online_drivers`, `my_history`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) manipulate Python lists; [`geo.tile_range`, `geo.world_px`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/geo.py) work with coordinate/tile computations; [`LiveMap.visible_tiles`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/livemap.py) processes visible tile locations. The flat 2D/3D indexing formulas are **teaching examples**, not verified ATLAS Go memory-layout code. [Catalogue](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/docs/ARCHITECTURE.md#complete-source-method-catalog).



An array supports indexed access. Python lists are resizable arrays of *references*: a[i] O(1), append amortized O(1), insertion at front O(n). A Python string is immutable, so producing a modified string usually creates new storage. A 2D row-major R×C numeric array has flat index i·C+j; column-major has j·R+i. A 3D X×Y×Z row-major numeric array has (i·Y+j)·Z+k.

~~~mermaid
flowchart LR
 A["index 0 = 12"] --- B["index 1 = 25"] --- C["index 2 = 7"] --- D["index 3 = 40"]
~~~

~~~mermaid
flowchart TB
 M["2 × 3 row-major matrix"] --> R0["row 0: a00 a01 a02 -> offsets 0,1,2"]
 M --> R1["row 1: a10 a11 a12 -> offsets 3,4,5"]
~~~

~~~python
matrix=[[10,20,30],[40,50,60]]
flat=[x for row in matrix for x in row]
assert flat[1*3+2] == matrix[1][2] == 60
assert (1*3+2)*4+3 == 23  # last index of 2×3×4
~~~

**Important:** Nested Python lists do not themselves imply contiguous numeric-matrix memory. Use a contiguous NumPy array to investigate cache effects. **Lab:** E07; extension: measure traversal order.

## Lesson 5 — Singly and doubly linked lists

**ATLAS Go status — teaching extension:** The explicit `Node`, `SNode` and `DNode` structures are in [the DSA lab](../dsa_lab/experiments.py), not in the current ATLAS Go class catalogue. For an app-side alternative to inspect, see the [`Cart` collection in domain.py](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/domain.py) and the [app UML](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/docs/UML_BLUEPRINT.md#android-app-atlas-go); this does **not** mean `Cart` is implemented as a linked list.



A **singly linked node** stores (value,next); a **doubly linked node** stores (value,prev,next). Nodes may be dispersed in memory. Head insertion is O(1); indexed search is O(n). A doubly linked list enables removal of a **known node** in O(1), but locating a key is still O(n).

~~~mermaid
flowchart LR
 H["head"] --> A["7 | next"] --> B["11 | next"] --> C["19 | None"]
~~~

~~~mermaid
flowchart LR
 A["None | 7 | next"] <--> B["prev | 11 | next"] <--> C["prev | 19 | None"]
~~~

~~~python
class Node:
    def __init__(self, value, next=None):
        self.value,self.next=value,next
head=Node(11,Node(19))
head=Node(7,head)
values=[]
while head:
    values.append(head.value)
    head=head.next
assert values == [7,11,19]
~~~

Trace head, middle, tail, absent-key and empty-list deletion. Avoid losing the reference to the next node. **Labs:** E07,E16,E17.

## Lesson 6 — Stack, queue and deque

**ATLAS Go status — teaching analogy:** The stack and FIFO queue implementations are in [DSA labs E08 and E19](../dsa_lab/experiments.py). ATLAS Go has ride/order progression methods [`driver_advance`, `advance_ride`, `advance_order`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) and related [UML lifecycle diagrams](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/docs/UML_BLUEPRINT.md#on-device-ride-and-order-lifecycles), but these are **state transitions**, not proof the app uses `deque` as a FIFO scheduler.



**Stack:** LIFO, like plates: last pushed item is first popped. **Queue:** FIFO, like a ticket line: earliest enqueued item leaves first. **Deque:** both ends are usable. A Python list supports append/pop at end in amortized O(1), while collections.deque provides append/popleft in O(1). list.pop(0) costs O(n), as items shift.

~~~mermaid
flowchart LR
 S["Stack: push A then B"] --> P["pop returns B"]
 Q["Queue: enqueue A then B"] --> R["dequeue returns A"]
~~~

~~~python
from collections import deque
stack=[]; stack.append("A"); stack.append("B")
assert stack.pop()=="B"
queue=deque(); queue.append("A"); queue.append("B")
assert queue.popleft()=="A"
~~~

Stacks implement iterative depth-first tree/graph traversal; queues implement breadth-first traversal. **Labs:** E08,E19.

## Lesson 7 — Hash tables implemented with linked lists

**ATLAS Go implementation link:** Real dictionary-backed collections are used by [`Cart.items`, `Catalog.dishes`, `Catalog.kitchens`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/domain.py) and [`LocalStore.failures`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py). Separate-chaining hash tables using `SNode`/`DNode` are **educational implementations** in [E16–E18](../dsa_lab/experiments.py); Python `dict` itself is not linked-list chaining. [UML catalogue](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/docs/ARCHITECTURE.md#complete-source-method-catalog).



A **hash table** uses a hash function to choose an array bucket. With integer keys, index=hash(key)%m. A **collision** occurs when different keys select the same bucket. **Separate chaining** stores colliding key/value records in a linked list at that bucket.

~~~mermaid
flowchart TB
 K["integer key"] --> H["hash(key) mod 4"]
 H --> B["bucket array"]
 B --> B0["0: empty"]
 B --> B1["1: (9,v9) → (5,v5) → (1,v1)"]
 B --> B2["2: empty"]
 B --> B3["3: (7,v7) → (3,v3)"]
~~~

For m=4, keys 1,5,9 all map to bucket 1. If inserted at the head in that order, the chain is 9→5→1; finding key 1 needs three comparisons. On insert, check whether the key already exists; updating must not add a duplicate. On delete, reconnect predecessor to successor.

~~~mermaid
flowchart LR
 A["singly: 9"] --> B["5"] --> C["1"]
 D["doubly: 9"] <--> E["5"] <--> F["1"]
~~~

**Singly chain:** (key,value,next) and an auxiliary previous pointer while searching/deleting. **Doubly chain:** (key,value,prev,next); after finding a node, neighbor pointers permit O(1) unlinking. The **load factor** α=n/m estimates occupancy: n=8,m=4 ⇒ α=2. Under uniform hashing expected chain lookup O(1+α); all keys colliding gives worst-case O(n). More buckets reduce expected collisions but consume extra memory.

~~~python
# In the existing DSA Colab notebook the lab module is named dsa:
table=dsa.ChainHash(4,"singly")
for key in (1,5,9):
    table.put(key,key*10)
assert table.max_chain()==3
assert table.get(1)[0]==10
assert table.delete(5) and table.validate()
double=dsa.ChainHash(4,"doubly")
for key in (1,5,9):
    double.put(key,key)
assert double.delete(5) and double.validate()
~~~

Python's built-in dict does *not* use these linked lists; it uses an open-addressing design. Fixed-bucket teaching tables expose collisions but production tables usually resize. **Labs:** E09,E16,E17,E18.

## Lesson 8 — Tree vocabulary and all four traversals

**ATLAS Go status — teaching extension:** The node BST and stack/queue traversal functions (`bst_insert_node`, `inorder_stack`, `preorder_stack`, `postorder_stack`, `levelorder_queue`) are implemented in the [DSA laboratory](../dsa_lab/experiments.py). They are not listed as ATLAS Go functions in the [app method catalogue](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/docs/ARCHITECTURE.md#complete-source-method-catalog).



A **tree** is an acyclic connected hierarchy. A **binary tree** allows at most two children per node. A **BST** requires smaller keys in left subtrees and larger keys in right subtrees (our illustrative node insertion ignores duplicates). A **root** has no parent, **leaf** has no children, and **height** measures maximum root-to-leaf depth. Declare whether heights count edges or nodes: the lab uses leaf height=1 and empty height=0.

~~~mermaid
flowchart TD
 R["8 root"] --> L["4"]
 R --> M["12"]
 L --> A["2 leaf"]
 L --> B["6 leaf"]
 M --> C["10 leaf"]
 M --> D["14 leaf"]
~~~

The diagram above yields **inorder** 2,4,6,8,10,12,14 (left-root-right), **preorder** 8,4,2,6,12,10,14 (root-left-right), **postorder** 2,6,4,10,14,12,8 (left-right-root), and **level order** 8,4,12,2,6,10,14 (top-down). Trees are stored as linked nodes; stack and queue are **auxiliary traversal mechanisms**, not the tree storage itself.

~~~mermaid
flowchart LR
 DFS["Depth-first: stack (LIFO)"] --> IO["Inorder / preorder / postorder"]
 BFS["Breadth-first: queue (FIFO)"] --> LO["Level order"]
~~~

~~~python
root=None
for key in (8,4,12,2,6,10,14):
    root=dsa.bst_insert_node(root,key)
assert dsa.inorder_stack(root)==[2,4,6,8,10,12,14]
assert dsa.preorder_stack(root)==[8,4,2,6,12,10,14]
assert dsa.postorder_stack(root)==[2,6,4,10,14,12,8]
assert dsa.levelorder_queue(root)==[8,4,12,2,6,10,14]
~~~

Every traversal visits n nodes once, O(n) time; DFS stack O(h), BFS queue O(w), and a collected output sequence adds O(n) space. A balanced BST has O(log n) lookup; ascending insertion into an unbalanced BST makes a chain of height O(n). **Labs:** E10,E19.

## Lesson 9 — AVL trees and the four rotations

**ATLAS Go status — teaching extension:** AVL insertion, LL/RR/LR/RL rotation and balance validation occur in [DSA E20](../dsa_lab/experiments.py) only. The [ATLAS Go UML catalogue](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/docs/ARCHITECTURE.md#complete-source-method-catalog) has no corresponding AVL class/function; do not treat it as production dispatch code.



An **AVL tree** is a self-balancing BST. Every node must have balance factor BF=height(left)−height(right) in {−1,0,+1}. After inserting a distinct key, update heights and rotate an unbalanced node. Rotations rearrange pointers without changing inorder ordering.

~~~mermaid
flowchart LR
 LL["LL insert 30,20,10"] --> RR["Right-rotate root; 20 becomes root"]
 R1["RR insert 10,20,30"] --> L1["Left-rotate root; 20 becomes root"]
 LR["LR insert 30,10,20"] --> L2["Left-rotate child then right-rotate root"]
 RL["RL insert 10,30,20"] --> R2["Right-rotate child then left-rotate root"]
~~~

~~~mermaid
flowchart TD
 subgraph Before["LL before"]
 A30["30"] --> A20["20"] --> A10["10"]
 end
 subgraph After["LL after right rotation"]
 B20["20"] --> B10["10"]
 B20 --> B30["30"]
 end
~~~

For **LR**, keys [30,10,20] initially form 30(left=10(right=20)). Rotate left at 10, then right at 30, giving 20 with children 10 and 30. For **RL** [10,30,20], rotate right at 30, then left at 10. Insert, search and delete in fully maintained AVL implementations are O(log n); the lab implements AVL **insertion/search**, not full AVL deletion.

~~~python
root=None
for key in (30,10,20):
    root=dsa.avl_insert(root,key)
assert root.key==20
assert dsa.inorder_stack(root)==[10,20,30]
assert dsa.validate_avl(root)==2  # height in nodes
~~~

Verify four rotation cases, tree ordering, computed heights and BF at every node. **Lab:** E20.

## Lesson 10 — Binary heaps, priority queues, and tries

**ATLAS Go status — teaching extension:** `heapq` and trie examples demonstrate possible data structures. Current ATLAS Go candidate ordering uses [`intelligence.rank` with `sorted`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py), rather than a documented heap-priority queue, and no trie API is listed in the [method catalogue](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/docs/ARCHITECTURE.md#complete-source-method-catalog).



A **min-heap** is a complete binary tree where each parent key ≤ its children. This differs from a BST: the left subtree need not contain only smaller values. Heaps use array indices: for parent i, children 2i+1 and 2i+2; parent of non-root i is (i−1)//2. Read minimum O(1); push/pop O(log n). Priority queues schedule tasks by urgency.

~~~mermaid
flowchart TD
 A["2 minimum"] --> B["5"]
 A --> C["8"]
 B --> D["7"]
 B --> E["9"]
~~~

~~~python
import heapq
jobs=[]
for p,name in ((5,"later"),(1,"urgent"),(3,"normal")):
    heapq.heappush(jobs,(p,name))
assert heapq.heappop(jobs)==(1,"urgent")
~~~

A **trie** stores characters as edges and shares common prefixes. Search/insert is O(L) expected when child map lookups are O(1), L=word length, at a possible memory cost.

~~~mermaid
flowchart TD
 X["root"] --> C["c"] --> CA["a"]
 CA --> CAT["t end"]
 CA --> CAR["r end"]
 X --> D["d"] --> DO["o"] --> DOG["g end"]
~~~

The trie stores cat, car and dog; prefix ca is a traversable path but is not an accepted word unless marked as an end.

~~~python
trie={}
for word in ("cat","car","dog"):
    node=trie
    for ch in word: node=node.setdefault(ch,{})
    node["$"]=True
~~~

**Extensions:** add a heap scheduler and trie search with assertions to the Colab notebook; the 20 benchmark runs focus on earlier core experiments.

## Lesson 11 — Graphs, BFS, DFS, Dijkstra, topological sort, union-find

**ATLAS Go implementation link / limitation:** [`geo.haversine_km`, `geo.nearest_place`, `geo.ride_position`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/geo.py) calculate geographic distance, nearest saved place and interpolated ride positions; [`LiveMap._route`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/livemap.py) draws a route visualization. The DSA lab's BFS, DFS and Dijkstra are **not evidence** that ATLAS Go performs road-network routing or Dijkstra dispatch. See [UML live map](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/docs/UML_BLUEPRINT.md#live-map-and-location) and [catalogue](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/docs/ARCHITECTURE.md#complete-source-method-catalog).



A **graph** has V vertices and E edges. Edges may be directed/undirected and weighted/unweighted. In an adjacency list, graph[A] lists neighbors: O(V+E) storage. An adjacency matrix consumes O(V²) storage but checks whether one edge exists in O(1). **BFS** explores by increasing edge count using a queue; **DFS** follows branches using a stack or recursion. Both visit all reachable vertices in O(V+E) time using adjacency lists.

~~~mermaid
flowchart LR
 A["A"] --> B["B"]
 A --> C["C"]
 B --> D["D"]
 C --> D
~~~

Above, adjacency lists A:[B,C], B:[D], C:[D], D:[]. With neighbor ordering as written, BFS from A visits A,B,C,D, while DFS may visit A,B,D,C. A BFS shortest-path guarantee concerns number of edges in **unweighted** graphs.

A **weighted shortest path** considers edge costs. **Dijkstra** uses a priority queue and requires nonnegative edge weights. Common adjacency-list + binary-heap bound O((V+E)log V).

~~~mermaid
flowchart LR
 A["A"] -->|"2"| B["B"]
 A -->|"8"| C["C"]
 B -->|"1"| C
~~~

Shortest path A→C is A→B→C, cost 2+1=3 versus direct cost 8.

~~~python
g={"A":[("B",2),("C",8)],"B":[("C",1)],"C":[]}
assert dsa.dijkstra(g,"A")["C"]==3
~~~

**Topological sorting** orders tasks such that each directed dependency appears before its dependent; it is possible only for a directed acyclic graph (DAG). **Union-find** groups items into connected components with parent links; path compression and union by rank provide O(α(n)) amortized operations, with α the inverse Ackermann function. **Labs:** E11,E12.

## Lesson 12 — Searching, sorting, stability and complexity

**ATLAS Go implementation link:** [`intelligence.rank`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py) returns driver candidates sorted by computed probability, [`choose`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py) selects from the ranked list, [`LocalStore.online_drivers`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) filters a list, and [`Catalog.menu`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/domain.py) filters dishes. The bubble/merge/quick sort functions and binary search in this chapter are **lab implementations**, not verified app functions. [Catalogue](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/docs/ARCHITECTURE.md#complete-source-method-catalog).



**Linear search:** scan until found, O(n) worst case, no sorted-input requirement. **Binary search:** inspect midpoint of sorted indexed data, keep only possible half, O(log n) worst case.

~~~mermaid
flowchart TD
 A["Sorted [2,4,6,8,10,12,14]; target 12"] --> B["Midpoint value 8"]
 B --> C["12 > 8: discard left half and 8"]
 C --> D["Inspect 12: found"]
~~~

**Bubble sort** swaps adjacent out-of-order values; **insertion sort** grows a sorted prefix; **merge sort** recursively splits and merges; **quicksort** partitions around a pivot; **heap sort** repeatedly removes a heap extreme. **Stable sorting** preserves input order among records with equal sort keys.

~~~mermaid
flowchart TD
 A["[7,2,6,1]"] --> B["[7,2]"] --> C["[2,7]"]
 A --> D["[6,1]"] --> E["[1,6]"]
 C --> F["merge: [1,2,6,7]"]
 E --> F
~~~

| Sort | Best | Average | Worst | Typical auxiliary space | Stable |
|---|---|---|---|---|---|
| Bubble with early exit | Θ(n) | Θ(n²) | Θ(n²) | O(1) | Yes |
| Insertion | Θ(n) | Θ(n²) | Θ(n²) | O(1) | Yes |
| Merge (array implementation) | Θ(n log n) | Θ(n log n) | Θ(n log n) | O(n) additional arrays | Yes |
| Conventional in-place quicksort | Θ(n log n) | expected Θ(n log n) under appropriate pivot/input model | Θ(n²) | O(log n) expected recursion | Usually no |
| In-place heap sort | Θ(n log n) | Θ(n log n) | Θ(n log n) | O(1) | No |

**Caution:** the lab's quick_sort is *functional three-way partitioning*, not an in-place implementation; it copies lists and is stable on equal values in that particular program. **Labs:** E02,E04,E05,E15.

## Lesson 13 — Recursion, divide-and-conquer, greedy, DP and backtracking

**ATLAS Go implementation link / limitation:** [`intelligence.choose`, `score`, `rank`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py) are genuine dispatch-selection/scoring functions; their use of ranking is **not equivalent to a proven greedy-optimal algorithm**. Fibonacci recursion, merge-sort divide-and-conquer and backtracking here are educational examples, not listed ATLAS Go functions. [Catalogue](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/docs/ARCHITECTURE.md#complete-source-method-catalog).



**Recursion** invokes a function on smaller inputs and ends at a base case. **Divide-and-conquer** splits into independent subproblems then combines solutions (merge sort: T(n)=2T(n/2)+Θ(n)=Θ(nlog n)). Binary search keeps one half (T(n)=T(n/2)+Θ(1)=Θ(log n)).

~~~mermaid
flowchart TD
 F["fib(4)"] --> A["fib(3)"]
 F --> B["fib(2)"]
 A --> C["fib(2) repeated"]
 A --> D["fib(1)"]
 C --> E["fib(1)"]
 C --> G["fib(0)"]
 B --> H["fib(1)"]
 B --> I["fib(0)"]
~~~

Naive Fibonacci recursion repeats fib(2), wasting computation; **dynamic programming** caches or iterates over overlapping subproblems. **Greedy** takes a locally preferred choice, but needs a proof that it achieves a global optimum. **Backtracking** explores choices and undoes them when invalid (e.g., N-queens).

~~~python
def fib_dp(n):
    a,b=0,1
    for _ in range(n): a,b=b,a+b
    return a
assert fib_dp(10)==55
~~~

Here fib_dp takes Θ(n) time and Θ(1) additional space for loop variables (big-integer bit complexity is a separate consideration). **Lab:** E13.

## Lesson 14 — How to prove correctness and measure memory

**ATLAS Go implementation link:** [`LocalStore.validate`, `snapshot`, `commit`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) check stored state and protect updates; [`intelligence.self_test`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py) checks model behavior. Compare these concrete safeguards with DSA loop invariants and smoke tests, while keeping the proof obligations distinct. [UML function catalogue](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/docs/ARCHITECTURE.md#complete-source-method-catalog).



For a loop: state precondition → show invariant initially → show one step preserves it → show termination → derive postcondition. For binary search, maintain “any matching index must lie within [low,high]” and shrink the interval every iteration. Sorting checks: output nondecreasing and multiset unchanged; linked lists: no lost nodes; AVL: height/BST/balance checks; BFS: reachable vertices visited exactly once.

~~~mermaid
flowchart LR
 P["Precondition"] --> I["Initialize invariant"]
 I --> S["One iteration preserves invariant"]
 S --> T["Termination"]
 T --> Q["Postcondition"]
~~~

Auxiliary memory examples: linked-list traversal O(1), DFS tree stack O(h), BFS tree queue O(w), visited set for general graph O(V), merge-sort temporary arrays O(n). Returning a full traversal order additionally stores O(n) values. Distinguish *asymptotic extra memory* from measured traced peak KiB. **Labs:** E14,E17,E19,E20.

## Lesson 15 — Full map of 20 experiments to learning objectives

**ATLAS Go implementation links:** use the cross-reference catalogue immediately below to move from theory to a relevant real function, or to a DSA-only educational implementation where the function does not exist in ATLAS Go.



| ID | Experiment and question | What to derive or inspect |
|---|---|---|
| E01 | Growth curves | n, nlog n, n² and ratios |
| E02 | Linear vs binary search | Comparison counts and sorted precondition |
| E03 | Search best/average/worst | Distribution and expected comparisons |
| E04 | Bubble/merge/quick | Count comparisons on identical input |
| E05 | Insertion sorted/random/reversed | How ordering affects comparisons |
| E06 | Runtime | Median ms and noise limitations |
| E07 | Array vs linked list | Front-insert copy vs node prepend |
| E08 | Stack and queue | list pop vs deque popleft vs list.pop(0) |
| E09 | Built-in dictionary | Hashing vs linear scan |
| E10 | BSTs | Balanced vs skewed search path |
| E11 | BFS vs DFS | Reachability and O(V+E) |
| E12 | Shortest path | Dijkstra cost and nonnegative edges |
| E13 | Fibonacci recursion vs DP | Repeated overlapping subproblems |
| E14 | Memory | List/dict/deque tracked peak KiB |
| E15 | Sorting stability | Equal-key relative order |
| E16 | Singly linked hash chains | Collisions, comparisons, deletion |
| E17 | Doubly linked hash chains | prev/next invariants, updates |
| E18 | Hash load factor | α=n/m, mean probes, max chain |
| E19 | Tree DFS stack / BFS queue | Traversal orders and timing |
| E20 | AVL vs skewed BST | LL/RR/LR/RL and height |

**Example complete lab analysis:** Hypothesis: AVL search remains logarithmic after ascending inserts while a plain BST degenerates. Independent variable n; dependent variable comparisons to last key; controls: same keys and insertion order; expected theory: O(log n) versus Θ(n); run E20, export CSV/PNG, inspect height and explain why wall-clock alone would not prove the bound. Repeat on random permutations and record variability as an extension.

**Run with Google Colab:** [All 20 experiments](https://colab.research.google.com/github/FUllSCIPTS/ATLAS/blob/main/dsa_lab/DSA_Colab_Labs.ipynb). The notebook loads the lab script as the module named dsa, so examples using dsa work after its setup cell. [Python implementations](../dsa_lab/experiments.py) · [Lab manual](../dsa_lab/README.md). The figures here are conceptual; the experiment runner generates CSV and PNG graphs when executed.

---

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
