"""DSA laboratory: data structures, algorithms, instrumentation and graphs.

Thirty reproducible experiments (E01-E30). Every structure used by the course
guide (docs/DATA_STRUCTURES_ALGORITHMS.md) is implemented here in plain Python
so that students can read, trace and modify it.

    python dsa_lab/experiments.py                    # self-tests, then usage
    python dsa_lab/experiments.py --list             # experiment register
    python dsa_lab/experiments.py --all              # E01-E30 -> dsa_lab/results
    python dsa_lab/experiments.py --experiment circular_singly
    python dsa_lab/experiments.py --diagrams         # structure drawings (PNG)

Colab: open dsa_lab/DSA_Colab_Labs.ipynb; it imports this file as ``dsa``.

Conventions used everywhere in the course:
* Tree height counts NODES: empty tree 0, single leaf 1.
* BSTs store DISTINCT keys; inserting an existing key leaves the tree unchanged.
* "comparisons" and "steps" are exact counts produced by the code; "ms" values
  are medians of repeated time.perf_counter() samples and vary by machine.
"""
from __future__ import annotations

import argparse
import bisect
import csv
import heapq
import math
import random
import statistics
import time
import tracemalloc
from collections import OrderedDict, deque
from pathlib import Path

SEED = 2026


# =============================================================================
# 1. Searching
# =============================================================================
def linear_search(a, x):
    """Return (index or -1, comparisons)."""
    steps = 0
    for i, v in enumerate(a):
        steps += 1
        if v == x:
            return i, steps
    return -1, steps


def binary_search(a, x):
    """Sorted, indexable ``a``. Invariant: if x is present it lies in a[lo..hi]."""
    lo, hi, steps = 0, len(a) - 1, 0
    while lo <= hi:
        mid = (lo + hi) // 2
        steps += 1
        if a[mid] == x:
            return mid, steps
        if a[mid] < x:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1, steps


def first_occurrence(a, x):
    """Binary search for the FIRST index of x among duplicates, or -1."""
    lo, hi, found = 0, len(a) - 1, -1
    while lo <= hi:
        mid = (lo + hi) // 2
        if a[mid] < x:
            lo = mid + 1
        else:
            if a[mid] == x:
                found = mid
            hi = mid - 1
    return found


# =============================================================================
# 2. Sorting (each returns (new_list, comparisons); inputs are never mutated)
# =============================================================================
def bubble_sort(a, key=lambda v: v):
    a = list(a)
    comparisons = 0
    for j in range(len(a) - 1):
        swapped = False
        for i in range(len(a) - 1 - j):
            comparisons += 1
            if key(a[i]) > key(a[i + 1]):
                a[i], a[i + 1] = a[i + 1], a[i]
                swapped = True
        if not swapped:
            break
    return a, comparisons


def selection_sort(a, key=lambda v: v):
    """Unstable: the long-distance swap can jump an equal key past another."""
    a = list(a)
    comparisons = 0
    for i in range(len(a) - 1):
        smallest = i
        for j in range(i + 1, len(a)):
            comparisons += 1
            if key(a[j]) < key(a[smallest]):
                smallest = j
        a[i], a[smallest] = a[smallest], a[i]
    return a, comparisons


def insertion_sort(a, key=lambda v: v):
    a = list(a)
    comparisons = 0
    for i in range(1, len(a)):
        item, j = a[i], i - 1
        while j >= 0:
            comparisons += 1
            if key(a[j]) <= key(item):
                break
            a[j + 1] = a[j]
            j -= 1
        a[j + 1] = item
    return a, comparisons


def merge_sort(a, key=lambda v: v):
    if len(a) <= 1:
        return list(a), 0
    mid = len(a) // 2
    left, c1 = merge_sort(a[:mid], key)
    right, c2 = merge_sort(a[mid:], key)
    i = j = 0
    merged, comparisons = [], c1 + c2
    while i < len(left) and j < len(right):
        comparisons += 1
        if key(left[i]) <= key(right[j]):          # <= keeps equal keys in order: stable
            merged.append(left[i]); i += 1
        else:
            merged.append(right[j]); j += 1
    return merged + left[i:] + right[j:], comparisons


def quick_sort(a, key=lambda v: v):
    """Functional three-way partition (copies lists; NOT in-place)."""
    if len(a) <= 1:
        return list(a), 0
    pivot = key(a[len(a) // 2])
    lt, eq, gt, comparisons = [], [], [], 0
    for x in a:
        comparisons += 1
        if key(x) < pivot:
            lt.append(x)
        else:
            comparisons += 1
            (gt if key(x) > pivot else eq).append(x)
    left, cl = quick_sort(lt, key)
    right, cr = quick_sort(gt, key)
    return left + eq + right, comparisons + cl + cr


def quick_sort_inplace(a):
    """Lomuto partition with a random pivot; returns (sorted copy, comparisons)."""
    a = list(a)
    rng = random.Random(SEED)
    comparisons = 0
    stack = [(0, len(a) - 1)]
    while stack:
        lo, hi = stack.pop()
        if lo >= hi:
            continue
        p = rng.randint(lo, hi)
        a[p], a[hi] = a[hi], a[p]
        pivot, store = a[hi], lo
        for i in range(lo, hi):
            comparisons += 1
            if a[i] < pivot:
                a[i], a[store] = a[store], a[i]
                store += 1
        a[store], a[hi] = a[hi], a[store]
        stack.append((lo, store - 1))
        stack.append((store + 1, hi))
    return a, comparisons


def heap_sort(a, key=lambda v: v):
    """In-place max-heap sort on a copy. Unstable."""
    a = list(a)
    comparisons = 0

    def sift(start, end):
        nonlocal comparisons
        root = start
        while 2 * root + 1 <= end:
            child = 2 * root + 1
            if child + 1 <= end:
                comparisons += 1
                if key(a[child]) < key(a[child + 1]):
                    child += 1
            comparisons += 1
            if key(a[root]) < key(a[child]):
                a[root], a[child] = a[child], a[root]
                root = child
            else:
                return

    for start in range(len(a) // 2 - 1, -1, -1):
        sift(start, len(a) - 1)
    for end in range(len(a) - 1, 0, -1):
        a[0], a[end] = a[end], a[0]
        sift(0, end - 1)
    return a, comparisons


def counting_sort(a, upper):
    """Non-comparison sort for integers 0..upper; Theta(n + upper) time and space."""
    counts = [0] * (upper + 1)
    for v in a:
        counts[v] += 1
    out = []
    for value, c in enumerate(counts):
        out.extend([value] * c)
    return out


def stability_violations(sort_fn, records):
    """Count equal-key pairs whose original order the sort reversed."""
    out = sort_fn(records, key=lambda r: r[0])[0]
    seen = {}
    bad = 0
    for k, original_index in out:
        if k in seen and original_index < seen[k]:
            bad += 1
        seen[k] = max(seen.get(k, -1), original_index)
    return bad


# =============================================================================
# 3. Dynamic array (what a Python list does underneath)
# =============================================================================
class DynamicArray:
    """Fixed-capacity block that is replaced by a larger block when full.

    ``growth`` is either a factor (2.0 doubling, 1.5) or an int increment.
    ``copies`` counts element copies caused by resizing (the hidden cost).
    """

    def __init__(self, growth=2.0, capacity=1):
        self.growth, self.capacity = growth, capacity
        self.block = [None] * capacity
        self.size = 0
        self.copies = 0
        self.resizes = 0

    def _grow(self):
        if isinstance(self.growth, int):
            new_capacity = self.capacity + self.growth
        else:
            new_capacity = max(self.capacity + 1, int(self.capacity * self.growth))
        new_block = [None] * new_capacity
        for i in range(self.size):
            new_block[i] = self.block[i]
        self.copies += self.size
        self.resizes += 1
        self.block, self.capacity = new_block, new_capacity

    def append(self, value):
        if self.size == self.capacity:
            self._grow()
        self.block[self.size] = value
        self.size += 1

    def insert(self, index, value):
        """Shift-right insertion: O(n - index) element moves."""
        if not 0 <= index <= self.size:
            raise IndexError(index)
        if self.size == self.capacity:
            self._grow()
        for i in range(self.size, index, -1):
            self.block[i] = self.block[i - 1]
        self.block[index] = value
        self.size += 1

    def __getitem__(self, i):
        if not 0 <= i < self.size:
            raise IndexError(i)
        return self.block[i]

    def __len__(self):
        return self.size

    def to_list(self):
        return self.block[:self.size]


def row_major(i, j, cols):
    return i * cols + j


def col_major(i, j, rows):
    return j * rows + i


def row_major_3d(i, j, k, Y, Z):
    return (i * Y + j) * Z + k


# =============================================================================
# 4. Linked lists: singly, doubly, circular singly, circular doubly (sentinel)
# =============================================================================
class Node:
    """Singly linked node (value, next)."""
    __slots__ = ("value", "next")

    def __init__(self, value, nxt=None):
        self.value, self.next = value, nxt

    def __repr__(self):
        return f"Node({self.value!r})"


class DNodeL:
    """Doubly linked node (value, prev, next) used by the list classes."""
    __slots__ = ("value", "prev", "next")

    def __init__(self, value, prev=None, nxt=None):
        self.value, self.prev, self.next = value, prev, nxt

    def __repr__(self):
        return f"DNode({self.value!r})"


def linked_insert_front(head, value):
    return Node(value, head)


def linked_traverse(head):
    out = []
    while head is not None:
        out.append(head.value)
        head = head.next
    return out


class SinglyLinkedList:
    """head -> ... -> tail -> None, with a tail pointer for O(1) append."""

    def __init__(self, values=()):
        self.head = self.tail = None
        self.size = 0
        for v in values:
            self.push_back(v)

    def push_front(self, value):                      # O(1)
        self.head = Node(value, self.head)
        if self.tail is None:
            self.tail = self.head
        self.size += 1

    def push_back(self, value):                       # O(1) thanks to tail
        node = Node(value)
        if self.tail is None:
            self.head = self.tail = node
        else:
            self.tail.next = node
            self.tail = node
        self.size += 1

    def pop_front(self):                              # O(1)
        if self.head is None:
            raise IndexError("pop from empty list")
        node = self.head
        self.head = node.next
        if self.head is None:
            self.tail = None
        self.size -= 1
        return node.value

    def pop_back(self):                               # O(n): must find the predecessor
        if self.head is None:
            raise IndexError("pop from empty list")
        if self.head is self.tail:
            return self.pop_front()
        p = self.head
        while p.next is not self.tail:
            p = p.next
        value = self.tail.value
        p.next = None
        self.tail = p
        self.size -= 1
        return value

    def find(self, value):
        """Return (node or None, comparisons)."""
        p, steps = self.head, 0
        while p is not None:
            steps += 1
            if p.value == value:
                return p, steps
            p = p.next
        return None, steps

    def insert_after(self, node, value):              # O(1) given the node
        node.next = Node(value, node.next)
        if node is self.tail:
            self.tail = node.next
        self.size += 1

    def remove(self, value):
        """Delete the first node holding value; keep head/tail correct."""
        prev, p = None, self.head
        while p is not None and p.value != value:
            prev, p = p, p.next
        if p is None:
            return False
        if prev is None:
            self.head = p.next
        else:
            prev.next = p.next
        if p is self.tail:
            self.tail = prev
        self.size -= 1
        return True

    def reverse(self):
        """Iterative pointer reversal: O(n) time, O(1) extra space."""
        prev, p = None, self.head
        self.tail = self.head
        while p is not None:
            p.next, prev, p = prev, p, p.next
        self.head = prev

    def __iter__(self):
        p = self.head
        while p is not None:
            yield p.value
            p = p.next

    def __len__(self):
        return self.size

    def to_list(self):
        return list(self)

    def validate(self):
        count, p, last = 0, self.head, None
        while p is not None:
            count += 1
            last = p
            if count > self.size:
                return False                          # unexpected cycle or bad size
            p = p.next
        return count == self.size and last is self.tail


class DoublyLinkedList:
    """None <- head <-> ... <-> tail -> None."""

    def __init__(self, values=()):
        self.head = self.tail = None
        self.size = 0
        for v in values:
            self.push_back(v)

    def push_front(self, value):
        node = DNodeL(value, None, self.head)
        if self.head is None:
            self.tail = node
        else:
            self.head.prev = node
        self.head = node
        self.size += 1
        return node

    def push_back(self, value):
        node = DNodeL(value, self.tail, None)
        if self.tail is None:
            self.head = node
        else:
            self.tail.next = node
        self.tail = node
        self.size += 1
        return node

    def unlink(self, node):                           # O(1) for a KNOWN node
        if node.prev is None:
            self.head = node.next
        else:
            node.prev.next = node.next
        if node.next is None:
            self.tail = node.prev
        else:
            node.next.prev = node.prev
        node.prev = node.next = None
        self.size -= 1
        return node.value

    def pop_front(self):
        if self.head is None:
            raise IndexError("pop from empty list")
        return self.unlink(self.head)

    def pop_back(self):                               # O(1), unlike the singly list
        if self.tail is None:
            raise IndexError("pop from empty list")
        return self.unlink(self.tail)

    def find(self, value):
        p, steps = self.head, 0
        while p is not None:
            steps += 1
            if p.value == value:
                return p, steps
            p = p.next
        return None, steps

    def to_list(self):
        out, p = [], self.head
        while p is not None:
            out.append(p.value)
            p = p.next
        return out

    def to_list_backward(self):
        out, p = [], self.tail
        while p is not None:
            out.append(p.value)
            p = p.prev
        return out

    def validate(self):
        count, prev, p = 0, None, self.head
        while p is not None:
            if p.prev is not prev:
                return False
            count += 1
            if count > self.size:
                return False
            prev, p = p, p.next
        return count == self.size and prev is self.tail


class CircularSinglyLinkedList:
    """Singly linked ring.  Only ``tail`` is stored; head is ``tail.next``.

        tail ──► [last] ──► [first] ──► ... ──► [last]   (the arrow wraps)

    Keeping the tail (not the head) makes BOTH ends O(1): push_back inserts
    after the tail and advances tail; push_front inserts after the tail only.
    """

    def __init__(self, values=()):
        self.tail = None
        self.size = 0
        for v in values:
            self.push_back(v)

    @property
    def head(self):
        return None if self.tail is None else self.tail.next

    def push_front(self, value):                      # O(1)
        node = Node(value)
        if self.tail is None:
            node.next = node                          # a one-node ring points to itself
            self.tail = node
        else:
            node.next = self.tail.next
            self.tail.next = node
        self.size += 1
        return node

    def push_back(self, value):                       # O(1)
        self.push_front(value)
        self.tail = self.tail.next                    # the new front becomes the new tail
        return self.tail

    def pop_front(self):                              # O(1)
        if self.tail is None:
            raise IndexError("pop from empty ring")
        first = self.tail.next
        if first is self.tail:
            self.tail = None
        else:
            self.tail.next = first.next
        self.size -= 1
        return first.value

    def rotate(self, k=1):
        """Advance the start of the ring by k positions: k pointer moves, no copying."""
        steps = 0
        if self.tail is None:
            return steps
        for _ in range(k % self.size):
            self.tail = self.tail.next
            steps += 1
        return steps

    def find(self, value):
        """Stop when we come back to the start, NOT when we reach None (there is none)."""
        if self.tail is None:
            return None, 0
        p, steps = self.tail.next, 0
        while True:
            steps += 1
            if p.value == value:
                return p, steps
            if p is self.tail:
                return None, steps
            p = p.next

    def remove(self, value):
        if self.tail is None:
            return False
        prev, p = self.tail, self.tail.next
        for _ in range(self.size):
            if p.value == value:
                if p is prev:                         # the only node
                    self.tail = None
                else:
                    prev.next = p.next
                    if p is self.tail:
                        self.tail = prev
                self.size -= 1
                return True
            prev, p = p, p.next
        return False

    def __iter__(self):
        if self.tail is None:
            return
        p = self.tail.next
        for _ in range(self.size):
            yield p.value
            p = p.next

    def __len__(self):
        return self.size

    def to_list(self):
        return list(self)

    def validate(self):
        """Ring property: walking size steps from the head returns to the head via tail."""
        if self.tail is None:
            return self.size == 0
        p = self.tail.next
        for _ in range(self.size - 1):
            if p is self.tail:
                return False                          # ring shorter than size
            p = p.next
        return p is self.tail and self.tail.next is self.head


class CircularDoublyLinkedList:
    """Circular doubly linked list with a SENTINEL (dummy) node.

        ┌──────────────────────────────────────────┐
        ▼                                          │
     [sentinel] <-> [first] <-> ... <-> [last] <->─┘

    The sentinel is always present, so an empty list is a sentinel pointing to
    itself and no operation needs an ``if head is None`` special case.
    """

    def __init__(self, values=()):
        self.sentinel = DNodeL(None)
        self.sentinel.prev = self.sentinel.next = self.sentinel
        self.size = 0
        for v in values:
            self.push_back(v)

    def insert_after(self, node, value):              # the ONLY insertion primitive
        new = DNodeL(value, node, node.next)
        node.next.prev = new
        node.next = new
        self.size += 1
        return new

    def unlink(self, node):                           # the ONLY removal primitive
        if node is self.sentinel:
            raise ValueError("cannot remove the sentinel")
        node.prev.next = node.next
        node.next.prev = node.prev
        node.prev = node.next = None
        self.size -= 1
        return node.value

    def push_front(self, value):
        return self.insert_after(self.sentinel, value)

    def push_back(self, value):
        return self.insert_after(self.sentinel.prev, value)

    def pop_front(self):
        if self.size == 0:
            raise IndexError("pop from empty list")
        return self.unlink(self.sentinel.next)

    def pop_back(self):
        if self.size == 0:
            raise IndexError("pop from empty list")
        return self.unlink(self.sentinel.prev)

    def move_to_front(self, node):                    # O(1): used by the LRU cache
        node.prev.next = node.next
        node.next.prev = node.prev
        node.prev, node.next = self.sentinel, self.sentinel.next
        self.sentinel.next.prev = node
        self.sentinel.next = node

    def rotate(self, k=1):
        """Advance the start of the list by k positions (k<0 goes backwards),
        exactly like CircularSinglyLinkedList.rotate. Only the sentinel moves;
        the shorter direction is chosen, so at most size//2 pointer moves."""
        if self.size == 0:
            return 0
        k = (-k) % self.size                          # internal walk is "rightwards"
        if k == 0:
            return 0
        steps = min(k, self.size - k)
        # Detach the sentinel, walk to the new position, reattach.
        s = self.sentinel
        first = s.next
        s.prev.next, first.prev = first, s.prev       # close the ring without the sentinel
        anchor = s.prev                               # last element
        if k <= self.size - k:
            for _ in range(k):
                anchor = anchor.prev
        else:
            for _ in range(self.size - k):
                anchor = anchor.next
        # Insert the sentinel after anchor: the element after it becomes the new first.
        s.prev, s.next = anchor, anchor.next
        anchor.next.prev = s
        anchor.next = s
        return steps

    def __iter__(self):
        p = self.sentinel.next
        while p is not self.sentinel:
            yield p.value
            p = p.next

    def to_list(self):
        return list(self)

    def to_list_backward(self):
        out, p = [], self.sentinel.prev
        while p is not self.sentinel:
            out.append(p.value)
            p = p.prev
        return out

    def __len__(self):
        return self.size

    def validate(self):
        count, p = 0, self.sentinel
        while True:
            if p.next.prev is not p:
                return False
            p = p.next
            if p is self.sentinel:
                break
            count += 1
            if count > self.size:
                return False
        return count == self.size


def josephus_circular(n, k):
    """Josephus problem on a circular singly linked list.

    n people stand in a ring; counting starts at person 1 and every k-th person
    leaves. Returns (elimination order, pointer moves).
    """
    ring = CircularSinglyLinkedList(range(1, n + 1))
    order, moves = [], 0
    prev = ring.tail
    while ring.size:
        for _ in range(k - 1):
            prev = prev.next
            moves += 1
        victim = prev.next
        order.append(victim.value)
        if victim is prev:
            ring.tail = None
        else:
            prev.next = victim.next
            if victim is ring.tail:
                ring.tail = prev
        ring.size -= 1
    return order, moves


def josephus_list(n, k):
    """Same problem with a Python list; counts elements shifted by pop(index)."""
    people = list(range(1, n + 1))
    order, shifts, i = [], 0, 0
    while people:
        i = (i + k - 1) % len(people)
        shifts += len(people) - i - 1
        order.append(people.pop(i))
    return order, shifts


def josephus_formula(n, k):
    """Survivor by recurrence J(1)=0, J(n)=(J(n-1)+k) mod n (1-based result)."""
    j = 0
    for m in range(2, n + 1):
        j = (j + k) % m
    return j + 1


class LRUCache:
    """Least-recently-used cache: dict for O(1) lookup + circular doubly list
    (with sentinel) for O(1) recency updates. Front = most recent."""

    def __init__(self, capacity):
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self.capacity = capacity
        self.order = CircularDoublyLinkedList()
        self.nodes = {}
        self.hits = self.misses = 0

    def get(self, key):
        node = self.nodes.get(key)
        if node is None:
            self.misses += 1
            return None
        self.hits += 1
        self.order.move_to_front(node)
        return node.value[1]

    def put(self, key, value):
        node = self.nodes.get(key)
        if node is not None:
            node.value = (key, value)
            self.order.move_to_front(node)
            return
        if len(self.nodes) == self.capacity:
            old_key, _ = self.order.pop_back()        # least recently used
            del self.nodes[old_key]
        self.nodes[key] = self.order.push_front((key, value))

    def keys(self):
        return [k for k, _ in self.order]


class ListLRU:
    """Naive LRU for comparison: list.remove is O(n)."""

    def __init__(self, capacity):
        self.capacity, self.items, self.data = capacity, [], {}

    def get(self, key):
        if key not in self.data:
            return None
        self.items.remove(key)
        self.items.insert(0, key)
        return self.data[key]

    def put(self, key, value):
        if key in self.data:
            self.items.remove(key)
        elif len(self.items) == self.capacity:
            del self.data[self.items.pop()]
        self.items.insert(0, key)
        self.data[key] = value


def floyd_cycle(head):
    """Tortoise and hare. Returns (has_cycle, mu = index where the cycle starts,
    lam = cycle length); (False, None, None) for a None-terminated list."""
    slow = fast = head
    while fast is not None and fast.next is not None:
        slow, fast = slow.next, fast.next.next
        if slow is fast:
            break
    else:
        return False, None, None
    mu, slow = 0, head
    while slow is not fast:
        slow, fast, mu = slow.next, fast.next, mu + 1
    lam, fast = 1, slow.next
    while fast is not slow:
        fast, lam = fast.next, lam + 1
    return True, mu, lam


# =============================================================================
# 5. Stacks, queues, deques, ring buffers
# =============================================================================
class RingBuffer:
    """Circular-array FIFO queue: fixed block, ``front`` index and ``count``.

    enqueue writes at (front + count) % capacity; dequeue reads at front and
    advances front = (front + 1) % capacity. No element ever moves.
    """

    def __init__(self, capacity, grow=False):
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self.block = [None] * capacity
        self.front = 0
        self.count = 0
        self.grow = grow
        self.wraps = 0

    @property
    def capacity(self):
        return len(self.block)

    def is_empty(self):
        return self.count == 0

    def is_full(self):
        return self.count == len(self.block)

    def enqueue(self, value):
        if self.is_full():
            if not self.grow:
                raise OverflowError("ring buffer full")
            self._resize(2 * len(self.block))
        back = (self.front + self.count) % len(self.block)
        if back < self.front:
            self.wraps += 1
        self.block[back] = value
        self.count += 1

    def dequeue(self):
        if self.is_empty():
            raise IndexError("dequeue from empty ring buffer")
        value = self.block[self.front]
        self.block[self.front] = None
        self.front = (self.front + 1) % len(self.block)
        self.count -= 1
        return value

    def peek(self):
        if self.is_empty():
            raise IndexError("peek at empty ring buffer")
        return self.block[self.front]

    def _resize(self, capacity):
        items = self.to_list()
        self.block = items + [None] * (capacity - len(items))
        self.front = 0

    def to_list(self):
        return [self.block[(self.front + i) % len(self.block)] for i in range(self.count)]


def balanced_brackets(text):
    """Classic stack application: every closer must match the latest opener."""
    pairs = {")": "(", "]": "[", "}": "{"}
    stack = []
    for ch in text:
        if ch in "([{":
            stack.append(ch)
        elif ch in pairs:
            if not stack or stack.pop() != pairs[ch]:
                return False
    return not stack


def evaluate_postfix(tokens):
    """Evaluate reverse-Polish notation with a stack, e.g. '3 4 + 2 *' -> 14."""
    stack = []
    ops = {"+": lambda a, b: a + b, "-": lambda a, b: a - b,
           "*": lambda a, b: a * b, "/": lambda a, b: a / b}
    for tok in tokens.split():
        if tok in ops:
            b, a = stack.pop(), stack.pop()
            stack.append(ops[tok](a, b))
        else:
            stack.append(float(tok) if "." in tok else int(tok))
    if len(stack) != 1:
        raise ValueError("malformed expression")
    return stack[0]


# =============================================================================
# 6. Hash tables: separate chaining (singly/doubly) and open addressing
# =============================================================================
class SNode:
    def __init__(self, key, value, nxt=None):
        self.key, self.value, self.next = key, value, nxt


class DNode:
    def __init__(self, key, value, prev=None, nxt=None):
        self.key, self.value, self.prev, self.next = key, value, prev, nxt


class ChainHash:
    """Fixed-size pedagogical hash table with separate chaining.

    kind='singly' or 'doubly'. Integer keys give deterministic buckets because
    CPython hashes small non-negative ints to themselves (hash(-1) is -2!).
    Set ``max_load`` to enable resizing (doubling) when n/m exceeds it.
    """

    def __init__(self, buckets=17, kind="singly", max_load=None):
        if buckets < 1 or kind not in ("singly", "doubly"):
            raise ValueError("invalid bucket count or chain kind")
        self.buckets = [None] * buckets
        self.kind = kind
        self.size = 0
        self.max_load = max_load
        self.rehashed = 0

    def index(self, key):
        return hash(key) % len(self.buckets)

    def load_factor(self):
        return self.size / len(self.buckets)

    def put(self, key, value):
        i = self.index(key)
        p = self.buckets[i]
        comparisons = 0
        while p:
            comparisons += 1
            if p.key == key:
                p.value = value                       # update, never duplicate
                return comparisons
            p = p.next
        old = self.buckets[i]
        if self.kind == "singly":
            self.buckets[i] = SNode(key, value, old)
        else:
            self.buckets[i] = DNode(key, value, None, old)
            if old is not None:
                old.prev = self.buckets[i]
        self.size += 1
        if self.max_load is not None and self.load_factor() > self.max_load:
            self._resize(2 * len(self.buckets))
        return comparisons

    def _resize(self, m):
        old = self.buckets
        self.buckets = [None] * m
        self.size = 0
        for root in old:
            p = root
            while p:
                self.put(p.key, p.value)
                self.rehashed += 1
                p = p.next

    def get(self, key, default=None):
        p = self.buckets[self.index(key)]
        comparisons = 0
        while p:
            comparisons += 1
            if p.key == key:
                return p.value, comparisons
            p = p.next
        return default, comparisons

    def delete(self, key):
        i = self.index(key)
        prev, p = None, self.buckets[i]
        while p:
            if p.key == key:
                if prev is None:
                    self.buckets[i] = p.next
                else:
                    prev.next = p.next
                if self.kind == "doubly" and p.next is not None:
                    p.next.prev = prev
                self.size -= 1
                return True
            prev, p = p, p.next
        return False

    def chain_lengths(self):
        out = []
        for root in self.buckets:
            count, p = 0, root
            while p:
                count += 1
                p = p.next
            out.append(count)
        return out

    def max_chain(self):
        return max(self.chain_lengths(), default=0)

    def validate(self):
        total = 0
        for i, root in enumerate(self.buckets):
            prev, p = None, root
            while p:
                if self.kind == "doubly" and p.prev is not prev:
                    return False
                if self.index(p.key) != i:
                    return False                      # node in the wrong bucket
                total += 1
                prev, p = p, p.next
        return total == self.size


def chain_table(n, buckets, kind, keys=None):
    t = ChainHash(buckets, kind)
    for x in (range(n) if keys is None else keys):
        t.put(x, x * 2)
    assert t.validate() and t.size == n
    return t


_TOMBSTONE = object()


class OpenAddressHash:
    """Open addressing with linear probing and tombstones (deleted markers).

    probe sequence: h, h+1, h+2, ... (mod m). Resizes (doubles) when the load
    factor would exceed ``max_load`` unless max_load is None.
    """

    def __init__(self, m=8, max_load=0.7):
        self.keys = [None] * m
        self.values = [None] * m
        self.size = 0
        self.max_load = max_load

    def _probe(self, key):
        m = len(self.keys)
        i = hash(key) % m
        for step in range(m):
            yield (i + step) % m, step + 1

    def put(self, key, value):
        if self.max_load is not None and (self.size + 1) / len(self.keys) > self.max_load:
            self._resize(2 * len(self.keys))
        first_free = None
        for slot, probes in self._probe(key):
            k = self.keys[slot]
            if k is None:
                target = slot if first_free is None else first_free
                self.keys[target], self.values[target] = key, value
                self.size += 1
                return probes
            if k is _TOMBSTONE:
                if first_free is None:
                    first_free = slot
            elif k == key:
                self.values[slot] = value
                return probes
        if first_free is not None:
            self.keys[first_free], self.values[first_free] = key, value
            self.size += 1
            return len(self.keys)
        raise OverflowError("table full")

    def get(self, key, default=None):
        for slot, probes in self._probe(key):
            k = self.keys[slot]
            if k is None:
                return default, probes
            if k is not _TOMBSTONE and k == key:
                return self.values[slot], probes
        return default, len(self.keys)

    def delete(self, key):
        for slot, _ in self._probe(key):
            k = self.keys[slot]
            if k is None:
                return False
            if k is not _TOMBSTONE and k == key:
                self.keys[slot], self.values[slot] = _TOMBSTONE, None
                self.size -= 1
                return True
        return False

    def _resize(self, m):
        pairs = [(k, v) for k, v in zip(self.keys, self.values)
                 if k is not None and k is not _TOMBSTONE]
        self.keys, self.values, self.size = [None] * m, [None] * m, 0
        for k, v in pairs:
            self.put(k, v)


# =============================================================================
# 7. Trees: BST, traversals, deletion, AVL
# =============================================================================
class TreeNode:
    def __init__(self, key):
        self.key, self.left, self.right, self.height = key, None, None, 1

    def __repr__(self):
        return f"TreeNode({self.key!r})"


class BST:
    """Iterative BST over TreeNode used by the balanced-vs-skewed experiment."""

    def __init__(self):
        self.root = None

    def insert(self, x):
        self.root = bst_insert_node(self.root, x)

    def search_steps(self, x):
        p, steps = self.root, 0
        while p is not None:
            steps += 1
            if p.key == x:
                return True, steps
            p = p.left if x < p.key else p.right
        return False, steps


def bst_insert_node(node, key):
    if node is None:
        return TreeNode(key)
    cur = node
    while True:
        if key == cur.key:
            return node                               # distinct keys only
        side = "left" if key < cur.key else "right"
        child = getattr(cur, side)
        if child is None:
            setattr(cur, side, TreeNode(key))
            return node
        cur = child


def bst_min(node):
    while node.left is not None:
        node = node.left
    return node


def bst_delete(node, key):
    """Recursive BST deletion covering the three cases:
    leaf -> remove; one child -> splice the child up;
    two children -> copy the inorder successor's key, then delete the successor."""
    if node is None:
        return None
    if key < node.key:
        node.left = bst_delete(node.left, key)
    elif key > node.key:
        node.right = bst_delete(node.right, key)
    else:
        if node.left is None:
            return node.right
        if node.right is None:
            return node.left
        successor = bst_min(node.right)
        node.key = successor.key
        node.right = bst_delete(node.right, successor.key)
    return node


def tree_height(node):
    """Height in nodes, computed (not stored)."""
    if node is None:
        return 0
    return 1 + max(tree_height(node.left), tree_height(node.right))


def is_bst(node, low=None, high=None):
    if node is None:
        return True
    if (low is not None and node.key <= low) or (high is not None and node.key >= high):
        return False
    return is_bst(node.left, low, node.key) and is_bst(node.right, node.key, high)


def inorder_recursive(node, out=None):
    out = [] if out is None else out
    if node is not None:
        inorder_recursive(node.left, out)
        out.append(node.key)
        inorder_recursive(node.right, out)
    return out


def inorder_stack(root):
    stack, order, node = [], [], root
    while stack or node:
        while node:
            stack.append(node)
            node = node.left
        node = stack.pop()
        order.append(node.key)
        node = node.right
    return order


def preorder_stack(root):
    if root is None:
        return []
    stack, order = [root], []
    while stack:
        node = stack.pop()
        order.append(node.key)
        if node.right:
            stack.append(node.right)                  # pushed first, popped last
        if node.left:
            stack.append(node.left)
    return order


def postorder_stack(root):
    if root is None:
        return []
    stack, order = [(root, False)], []
    while stack:
        node, expanded = stack.pop()
        if expanded:
            order.append(node.key)
        else:
            stack.append((node, True))
            if node.right:
                stack.append((node.right, False))
            if node.left:
                stack.append((node.left, False))
    return order


def levelorder_queue(root):
    if root is None:
        return []
    queue, order = deque([root]), []
    while queue:
        node = queue.popleft()
        order.append(node.key)
        if node.left:
            queue.append(node.left)
        if node.right:
            queue.append(node.right)
    return order


def build_balanced(keys):
    """Insert the middle key first, recursively: a height-minimal BST."""
    root = None

    def go(lo, hi):
        nonlocal root
        if lo > hi:
            return
        mid = (lo + hi) // 2
        root = bst_insert_node(root, keys[mid])
        go(lo, mid - 1)
        go(mid + 1, hi)

    go(0, len(keys) - 1)
    return root


def avl_height(node):
    return node.height if node else 0


def avl_update(node):
    node.height = 1 + max(avl_height(node.left), avl_height(node.right))


def avl_balance(node):
    return avl_height(node.left) - avl_height(node.right)


def avl_rotate_right(y):
    x, middle = y.left, y.left.right
    x.right, y.left = y, middle
    avl_update(y)
    avl_update(x)
    return x


def avl_rotate_left(x):
    y, middle = x.right, x.right.left
    y.left, x.right = x, middle
    avl_update(x)
    avl_update(y)
    return y


def _avl_rebalance(node):
    avl_update(node)
    bf = avl_balance(node)
    if bf > 1:
        if avl_balance(node.left) < 0:
            node.left = avl_rotate_left(node.left)    # LR
        return avl_rotate_right(node)                 # LL
    if bf < -1:
        if avl_balance(node.right) > 0:
            node.right = avl_rotate_right(node.right)  # RL
        return avl_rotate_left(node)                  # RR
    return node


def avl_insert(node, key):
    if node is None:
        return TreeNode(key)
    if key == node.key:
        return node
    if key < node.key:
        node.left = avl_insert(node.left, key)
    else:
        node.right = avl_insert(node.right, key)
    return _avl_rebalance(node)


def avl_delete(node, key):
    """Full AVL deletion: BST delete, then rebalance every node on the way up."""
    if node is None:
        return None
    if key < node.key:
        node.left = avl_delete(node.left, key)
    elif key > node.key:
        node.right = avl_delete(node.right, key)
    else:
        if node.left is None or node.right is None:
            return node.left or node.right
        successor = bst_min(node.right)
        node.key = successor.key
        node.right = avl_delete(node.right, successor.key)
    return _avl_rebalance(node)


def validate_avl(node, low=None, high=None):
    """Raise AssertionError on any violation; return height in nodes."""
    if node is None:
        return 0
    if (low is not None and node.key <= low) or (high is not None and node.key >= high):
        raise AssertionError("BST ordering violated")
    lh = validate_avl(node.left, low, node.key)
    rh = validate_avl(node.right, node.key, high)
    if abs(lh - rh) > 1 or node.height != max(lh, rh) + 1:
        raise AssertionError("AVL height/balance violated")
    return node.height


def tree_search_steps(root, key):
    count = 0
    while root:
        count += 1
        if key == root.key:
            return count
        root = root.left if key < root.key else root.right
    return count


# =============================================================================
# 8. Binary heap, priority queue, trie
# =============================================================================
class MinHeap:
    """Array-based binary min-heap.  children of i: 2i+1, 2i+2; parent: (i-1)//2.
    ``swaps`` counts element exchanges (the basic operation of sifting)."""

    def __init__(self, items=None):
        self.a = []
        self.swaps = 0
        if items:
            self.a = list(items)
            self.heapify()

    def __len__(self):
        return len(self.a)

    def peek(self):
        if not self.a:
            raise IndexError("peek at empty heap")
        return self.a[0]

    def push(self, item):                             # O(log n): sift up
        a = self.a
        a.append(item)
        i = len(a) - 1
        while i > 0:
            parent = (i - 1) // 2
            if a[i] < a[parent]:
                a[i], a[parent] = a[parent], a[i]
                self.swaps += 1
                i = parent
            else:
                break

    def _sift_down(self, i):
        a, n = self.a, len(self.a)
        while True:
            smallest, l, r = i, 2 * i + 1, 2 * i + 2
            if l < n and a[l] < a[smallest]:
                smallest = l
            if r < n and a[r] < a[smallest]:
                smallest = r
            if smallest == i:
                return
            a[i], a[smallest] = a[smallest], a[i]
            self.swaps += 1
            i = smallest

    def pop(self):                                    # O(log n): move last to root, sift down
        a = self.a
        if not a:
            raise IndexError("pop from empty heap")
        last = a.pop()
        if not a:
            return last
        top, a[0] = a[0], last
        self._sift_down(0)
        return top

    def heapify(self):
        """Bottom-up (Floyd) heap construction: O(n), not O(n log n)."""
        for i in range(len(self.a) // 2 - 1, -1, -1):
            self._sift_down(i)

    def is_heap(self):
        a = self.a
        return all(a[(i - 1) // 2] <= a[i] for i in range(1, len(a)))


class Trie:
    """Prefix tree: each node is a dict of child characters plus an end flag."""

    END = "$"

    def __init__(self, words=()):
        self.root = {}
        self.words = 0
        for w in words:
            self.insert(w)

    def insert(self, word):
        node = self.root
        for ch in word:
            node = node.setdefault(ch, {})
        if self.END not in node:
            node[self.END] = True
            self.words += 1

    def _walk(self, prefix):
        node, steps = self.root, 0
        for ch in prefix:
            steps += 1
            node = node.get(ch)
            if node is None:
                return None, steps
        return node, steps

    def contains(self, word):
        node, _ = self._walk(word)
        return node is not None and self.END in node

    def starts_with(self, prefix):
        """All stored words beginning with prefix, in lexicographic order."""
        node, _ = self._walk(prefix)
        out = []
        if node is None:
            return out

        def collect(n, path):
            if self.END in n:
                out.append(prefix + path)
            for ch in sorted(k for k in n if k != self.END):
                collect(n[ch], path + ch)

        collect(node, "")
        return out

    def delete(self, word):
        """Remove the word and prune nodes that no longer lead to any word."""
        path = [self.root]
        for ch in word:
            nxt = path[-1].get(ch)
            if nxt is None:
                return False
            path.append(nxt)
        if self.END not in path[-1]:
            return False
        del path[-1][self.END]
        self.words -= 1
        for i in range(len(word) - 1, -1, -1):
            if path[i + 1]:
                break
            del path[i][word[i]]
        return True

    def node_count(self):
        def count(n):
            return 1 + sum(count(c) for k, c in n.items() if k != self.END)
        return count(self.root)


# =============================================================================
# 9. Graphs
# =============================================================================
def dfs(graph, start):
    seen, order, stack = set(), [], [start]
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        order.append(node)
        stack.extend(reversed(graph.get(node, [])))
    return order


def bfs(graph, start):
    seen, order, queue = {start}, [], deque([start])
    while queue:
        node = queue.popleft()
        order.append(node)
        for nxt in graph.get(node, []):
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return order


def bfs_distances(graph, start):
    """Edge-count distances and the number of edge examinations."""
    dist, queue, examined = {start: 0}, deque([start]), 0
    while queue:
        u = queue.popleft()
        for v in graph.get(u, []):
            examined += 1
            if v not in dist:
                dist[v] = dist[u] + 1
                queue.append(v)
    return dist, examined


def dfs_count(graph, start):
    seen, stack, examined = {start}, [start], 0
    while stack:
        u = stack.pop()
        for v in graph.get(u, []):
            examined += 1
            if v not in seen:
                seen.add(v)
                stack.append(v)
    return seen, examined


def dijkstra(graph, source, stats=None):
    dist = {v: float("inf") for v in graph}
    dist[source] = 0
    heap = [(0, source)]
    pushes = relaxations = 0
    while heap:
        cost, u = heapq.heappop(heap)
        if cost != dist[u]:
            continue                                  # stale entry ("lazy deletion")
        for v, weight in graph[u]:
            if weight < 0:
                raise ValueError("Dijkstra needs nonnegative weights")
            relaxations += 1
            if cost + weight < dist[v]:
                dist[v] = cost + weight
                heapq.heappush(heap, (dist[v], v))
                pushes += 1
    if stats is not None:
        stats.update(pushes=pushes, relaxations=relaxations)
    return dist


def dijkstra_path(graph, source, target):
    dist = {v: float("inf") for v in graph}
    prev = {}
    dist[source] = 0
    heap = [(0, source)]
    while heap:
        cost, u = heapq.heappop(heap)
        if cost != dist[u]:
            continue
        for v, w in graph[u]:
            if cost + w < dist[v]:
                dist[v], prev[v] = cost + w, u
                heapq.heappush(heap, (dist[v], v))
    if dist[target] == float("inf"):
        return None, float("inf")
    path = [target]
    while path[-1] != source:
        path.append(prev[path[-1]])
    return path[::-1], dist[target]


def topo_sort_kahn(graph):
    """Kahn's algorithm. Returns (order, edges_processed); raises on a cycle."""
    indegree = {u: 0 for u in graph}
    for u in graph:
        for v in graph[u]:
            indegree[v] = indegree.get(v, 0) + 1
    queue = deque(sorted(u for u, d in indegree.items() if d == 0))
    order, processed = [], 0
    while queue:
        u = queue.popleft()
        order.append(u)
        for v in graph.get(u, []):
            processed += 1
            indegree[v] -= 1
            if indegree[v] == 0:
                queue.append(v)
    if len(order) != len(indegree):
        raise ValueError("graph has a cycle: no topological order exists")
    return order, processed


def topo_sort_dfs(graph):
    """DFS finishing order reversed; detects back edges (cycles) with colours."""
    WHITE, GREY, BLACK = 0, 1, 2
    colour = {u: WHITE for u in graph}
    order, processed = [], 0
    for start in graph:
        if colour[start] != WHITE:
            continue
        stack = [(start, iter(graph[start]))]
        colour[start] = GREY
        while stack:
            u, it = stack[-1]
            for v in it:
                processed += 1
                if colour.get(v, WHITE) == GREY:
                    raise ValueError("graph has a cycle: no topological order exists")
                if colour.get(v, WHITE) == WHITE:
                    colour[v] = GREY
                    stack.append((v, iter(graph.get(v, []))))
                    break
            else:
                colour[u] = BLACK
                order.append(u)
                stack.pop()
    return order[::-1], processed


class UnionFind:
    """Disjoint-set forest. ``steps`` counts parent-pointer hops in find()."""

    def __init__(self, n, rank=True, compress=True):
        self.parent = list(range(n))
        self.rank = [0] * n
        self.use_rank, self.compress = rank, compress
        self.steps = 0
        self.components = n

    def find(self, x):
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
            self.steps += 1
        if self.compress:
            while self.parent[x] != root:
                self.parent[x], x = root, self.parent[x]
        return root

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.use_rank:
            if self.rank[ra] < self.rank[rb]:
                ra, rb = rb, ra
            self.parent[rb] = ra
            if self.rank[ra] == self.rank[rb]:
                self.rank[ra] += 1
        else:
            self.parent[ra] = rb                      # naive: may build a long chain
        self.components -= 1
        return True


def kruskal(n, edges):
    """Minimum spanning tree with union-find; edges are (w, u, v)."""
    uf, tree, total = UnionFind(n), [], 0
    for w, u, v in sorted(edges):
        if uf.union(u, v):
            tree.append((u, v, w))
            total += w
    return tree, total


# =============================================================================
# 10. Recursion, dynamic programming, backtracking, greedy
# =============================================================================
def fib_naive_calls(k):
    calls = 0

    def f(m):
        nonlocal calls
        calls += 1
        return m if m < 2 else f(m - 1) + f(m - 2)

    return f(k), calls


def fib_memo_calls(k):
    calls, memo = 0, {}

    def f(m):
        nonlocal calls
        calls += 1
        if m < 2:
            return m
        if m not in memo:
            memo[m] = f(m - 1) + f(m - 2)
        return memo[m]

    return f(k), calls


def fib_dp(k):
    x, y = 0, 1
    for _ in range(k):
        x, y = y, x + y
    return x


def knapsack_01(weights, values, capacity):
    """Bottom-up 0/1 knapsack, Theta(n*W). Returns (best value, chosen indices)."""
    n = len(weights)
    best = [[0] * (capacity + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        w, v = weights[i - 1], values[i - 1]
        for c in range(capacity + 1):
            best[i][c] = best[i - 1][c]
            if w <= c and best[i - 1][c - w] + v > best[i][c]:
                best[i][c] = best[i - 1][c - w] + v
    chosen, c = [], capacity
    for i in range(n, 0, -1):
        if best[i][c] != best[i - 1][c]:
            chosen.append(i - 1)
            c -= weights[i - 1]
    return best[n][capacity], chosen[::-1]


def n_queens(n):
    """Backtracking: count solutions and the number of placements tried."""
    cols, d1, d2 = set(), set(), set()
    solutions = tried = 0

    def place(r):
        nonlocal solutions, tried
        if r == n:
            solutions += 1
            return
        for c in range(n):
            tried += 1
            if c in cols or r - c in d1 or r + c in d2:
                continue
            cols.add(c); d1.add(r - c); d2.add(r + c)
            place(r + 1)
            cols.remove(c); d1.remove(r - c); d2.remove(r + c)

    place(0)
    return solutions, tried


def interval_schedule(intervals):
    """Greedy: earliest finishing time first is provably optimal for the number
    of non-overlapping intervals."""
    chosen, end = [], float("-inf")
    for s, f in sorted(intervals, key=lambda iv: iv[1]):
        if s >= end:
            chosen.append((s, f))
            end = f
    return chosen


# =============================================================================
# 11. Measurement helpers
# =============================================================================
def measure(func, repeat=5):
    """Median wall-clock milliseconds of func(): descriptive only."""
    samples = []
    for _ in range(repeat):
        t0 = time.perf_counter()
        func()
        samples.append((time.perf_counter() - t0) * 1000)
    return statistics.median(samples)


def measure_setup(setup, action, repeat=5):
    """Like measure() but rebuilds the input with setup() OUTSIDE the timed region."""
    samples = []
    for _ in range(repeat):
        data = setup()
        t0 = time.perf_counter()
        action(data)
        samples.append((time.perf_counter() - t0) * 1000)
    return statistics.median(samples)


def peak_kib(func):
    tracemalloc.start()
    try:
        func()
        return tracemalloc.get_traced_memory()[1] / 1024
    finally:
        tracemalloc.stop()


# =============================================================================
# 12. Structure drawings (matplotlib) - used by the notebook and --diagrams
# =============================================================================
def draw_structure(kind, values, path=None, title=None, ax=None):
    """Draw a linked structure as boxes and arrows.

    kind: 'singly', 'doubly', 'circular', 'circular-doubly', 'ring-buffer'.
    For 'ring-buffer' pass values=(block, front, count).
    """
    import matplotlib
    if path is not None and ax is None:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

    own = ax is None
    if own:
        fig, ax = plt.subplots(figsize=(9, 4.2 if "circular" in kind or kind == "ring-buffer" else 2.2))
    ax.set_axis_off()
    ax.set_aspect("equal")

    def box(x, y, text, colour="#e8f0fe", w=0.9, h=0.55):
        ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.02",
                                    fc=colour, ec="#1b3a6b", lw=1.4))
        ax.text(x, y, text, ha="center", va="center", fontsize=11, family="monospace")

    def arrow(p, q, colour="#1b3a6b", rad=0.0, style="-|>"):
        ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=13, color=colour,
                                     lw=1.3, connectionstyle=f"arc3,rad={rad}"))

    values = list(values) if kind != "ring-buffer" else values
    if kind in ("singly", "doubly"):
        n = len(values)
        for i, v in enumerate(values):
            box(1.6 * i, 0, str(v))
            if i + 1 < n:
                arrow((1.6 * i + 0.47, 0.08), (1.6 * (i + 1) - 0.47, 0.08))
                if kind == "doubly":
                    arrow((1.6 * (i + 1) - 0.47, -0.1), (1.6 * i + 0.47, -0.1), colour="#b5462f")
        ax.text(-0.9, 0.55, "head", fontsize=10, color="#1b3a6b")
        arrow((-0.6, 0.48), (-0.3, 0.2))
        end = 1.6 * (n - 1) + 0.47 if n else 0
        ax.text(end + 0.35, 0, "None", va="center", fontsize=10, color="#666")
        ax.set_xlim(-1.2, 1.6 * max(n, 1) + 0.6)
        ax.set_ylim(-0.8, 0.9)
    elif kind in ("circular", "circular-doubly"):
        items = (["S"] if kind == "circular-doubly" else []) + [str(v) for v in values]
        n = max(len(items), 1)
        r = 1.6 + 0.12 * n
        pts = [(r * math.cos(math.pi / 2 - 2 * math.pi * i / n),
                r * math.sin(math.pi / 2 - 2 * math.pi * i / n)) for i in range(n)]
        for i, (x, y) in enumerate(pts):
            colour = "#fde7c8" if (kind == "circular-doubly" and i == 0) else "#e8f0fe"
            box(x, y, items[i], colour)
        for i in range(n):
            (x1, y1), (x2, y2) = pts[i], pts[(i + 1) % n]
            dx, dy = x2 - x1, y2 - y1
            d = math.hypot(dx, dy) or 1
            ux, uy = dx / d, dy / d
            arrow((x1 + 0.5 * ux, y1 + 0.33 * uy), (x2 - 0.5 * ux, y2 - 0.33 * uy), rad=-0.15)
            if kind == "circular-doubly":
                arrow((x2 - 0.5 * ux, y2 - 0.33 * uy - 0.05), (x1 + 0.5 * ux, y1 + 0.33 * uy - 0.05),
                      colour="#b5462f", rad=-0.15)
        if kind == "circular" and values:
            ax.text(pts[-1][0] - 1.1, pts[-1][1] + 0.5, "tail", color="#1b3a6b")
            ax.text(pts[0][0] + 0.55, pts[0][1] + 0.35, "head = tail.next", color="#1b3a6b", fontsize=9)
        lim = r + 1.0
        ax.set_xlim(-lim - 0.8, lim + 0.8)
        ax.set_ylim(-lim, lim)
    elif kind == "ring-buffer":
        block, front, count = values
        m = len(block)
        r = 1.8
        for i in range(m):
            a = math.pi / 2 - 2 * math.pi * i / m
            x, y = r * math.cos(a), r * math.sin(a)
            used = (i - front) % m < count
            box(x, y, "" if block[i] is None else str(block[i]), "#d7f5dd" if used else "#f2f2f2", w=0.75)
            ax.text(1.35 * x, 1.35 * y, str(i), ha="center", va="center", fontsize=8, color="#777")
        back = (front + count) % m
        for idx, label, colour in ((front, "front", "#1b3a6b"), (back, "back", "#b5462f")):
            a = math.pi / 2 - 2 * math.pi * idx / m
            ax.annotate(label, xy=(0.72 * r * math.cos(a), 0.72 * r * math.sin(a)),
                        xytext=(0.25 * r * math.cos(a), 0.25 * r * math.sin(a)),
                        ha="center", color=colour, fontsize=10,
                        arrowprops=dict(arrowstyle="-|>", color=colour))
        ax.set_xlim(-3, 3)
        ax.set_ylim(-2.7, 2.7)
    else:
        raise ValueError(kind)
    if title:
        ax.set_title(title)
    if own:
        fig.tight_layout()
        if path is not None:
            fig.savefig(path, dpi=150)
            plt.close(fig)
        return fig
    return ax


def draw_tree(root, path=None, title=None, ax=None):
    """Draw a binary tree (TreeNode) with inorder x-positions."""
    import matplotlib
    if path is not None and ax is None:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    pos, counter = {}, [0]

    def place(node, depth):
        if node is None:
            return
        place(node.left, depth + 1)
        pos[node] = (counter[0], -depth)
        counter[0] += 1
        place(node.right, depth + 1)

    place(root, 0)
    own = ax is None
    if own:
        fig, ax = plt.subplots(figsize=(max(4, 0.6 * len(pos)), 1 + 0.9 * (tree_height(root) or 1)))
    for node, (x, y) in pos.items():
        for child in (node.left, node.right):
            if child is not None:
                cx, cy = pos[child]
                ax.plot([x, cx], [y, cy], color="#1b3a6b", lw=1.2, zorder=1)
    for node, (x, y) in pos.items():
        ax.scatter([x], [y], s=520, color="#e8f0fe", edgecolors="#1b3a6b", zorder=2)
        ax.text(x, y, str(node.key), ha="center", va="center", fontsize=10, zorder=3)
    ax.set_axis_off()
    if title:
        ax.set_title(title)
    if own:
        fig.tight_layout()
        if path is not None:
            fig.savefig(path, dpi=150)
            plt.close(fig)
        return fig
    return ax


# =============================================================================
# 13. The thirty experiments
# =============================================================================
DEFAULT_SIZES = (32, 64, 128, 256, 512)

#  name: (id, title, column labels, y-axis label, x-axis label, sizes or None)
EXPERIMENTS = {
    "growth": ("E01", "Growth of n, n log2 n and n^2",
               ("n", "n^2", "n log2 n"), "basic operations", "input size n", None),
    "search": ("E02", "Linear vs binary search (absent key)",
               ("linear comparisons", "binary comparisons", "floor(log2 n)+1"), "comparisons", "input size n", None),
    "search_cases": ("E03", "Linear search best / average / worst",
                     ("best", "average (successful)", "worst (absent)"), "comparisons", "input size n", None),
    "sort": ("E04", "Bubble vs merge vs quick sort on the same shuffled input",
             ("bubble", "merge", "quick (functional)"), "comparisons", "input size n", None),
    "sort_cases": ("E05", "Insertion sort on sorted / random / reversed input",
                   ("sorted (best)", "random (average)", "reversed (worst)"), "comparisons", "input size n", None),
    "runtime": ("E06", "Measured time: linear search, binary search, merge sort",
                ("linear search", "binary search", "merge sort"), "median ms", "input size n", None),
    "array_linked": ("E07", "Front insertion: Python list vs linked list; traversal",
                     ("list insert(0) x n", "linked push_front x n", "linked traversal"), "median ms (log scale)", "input size n",
                     (256, 1024, 4096, 16384)),
    "stack_queue": ("E08", "Removing all n items: stack pop, deque popleft, list pop(0)",
                    ("list.pop() (stack)", "deque.popleft() (queue)", "list.pop(0) (bad queue)"), "median ms", "input size n",
                    (256, 512, 1024, 2048, 4096)),
    "hash": ("E09", "n lookups: dict vs linear scan vs binary search",
             ("dict", "linear scan", "bisect on sorted list"), "median ms", "input size n", None),
    "bst": ("E10", "BST search path: balanced vs ascending-insert (skewed)",
            ("balanced BST", "skewed BST", "floor(log2 n)+1"), "nodes visited", "input size n", None),
    "graph": ("E11", "BFS and DFS edge examinations on a random graph",
              ("BFS edges examined", "DFS edges examined", "E (reference)"), "edge examinations", "vertices V", None),
    "shortest_path": ("E12", "Dijkstra work on a random weighted graph",
                      ("relaxations", "heap pushes", "E (reference)"), "operations", "vertices V", None),
    "recursion_dp": ("E13", "Fibonacci: naive recursion vs memoisation vs loop",
                     ("naive calls", "memoised calls", "loop iterations"), "calls / iterations (log scale)", "k",
                     (5, 10, 15, 20, 25)),
    "memory": ("E14", "Traced peak memory of list, dict and deque",
               ("list", "dict", "deque"), "peak KiB (tracemalloc)", "input size n", None),
    "sorting_stability": ("E15", "Stability: equal-key order violations",
                          ("merge sort", "insertion sort", "heap sort"), "violated equal-key pairs", "input size n", None),
    "hash_singly": ("E16", "Hash table, singly linked chains (m = n/4)",
                    ("mean successful comparisons", "max chain length", "1 + alpha/2 (theory)"), "nodes", "input size n", None),
    "hash_doubly": ("E17", "Hash table, doubly linked chains after delete/reinsert",
                    ("mean successful comparisons", "max chain length", "1 + alpha/2 (theory)"), "nodes", "input size n", None),
    "hash_load": ("E18", "Load factor: uniform keys vs adversarial keys (m = n/8)",
                  ("uniform mean comparisons", "adversarial mean comparisons", "1 + alpha/2 (theory)"),
                  "comparisons (log scale)", "input size n", None),
    "tree_stack_queue": ("E19", "Iterative traversals with an explicit stack / queue",
                         ("inorder (stack)", "preorder (stack)", "level order (queue)"), "median ms", "input size n", None),
    "avl": ("E20", "AVL vs plain BST after ascending inserts",
            ("AVL search steps", "plain BST search steps", "AVL height"), "nodes", "input size n", None),
    "circular_singly": ("E21", "Josephus problem (k = 3): circular list vs Python list",
                        ("circular pointer moves", "list elements shifted", "n(k-1) reference"), "operations", "people n", None),
    "circular_doubly": ("E22", "LRU cache: circular doubly list + dict vs list-based LRU",
                        ("sentinel-list LRU", "list LRU", "OrderedDict LRU"), "median us per operation", "cache capacity",
                        (16, 64, 256, 1024, 2048)),
    "ring_buffer": ("E23", "FIFO of n items, 4 passes: ring buffer vs deque vs list.pop(0)",
                    ("ring buffer", "collections.deque", "list.pop(0)"), "median ms (log scale)", "items n",
                    (1024, 4096, 16384, 32768)),
    "heap": ("E24", "Building a heap: bottom-up heapify vs n pushes",
             ("heapify swaps", "n pushes swaps", "n (reference)"), "swaps", "input size n",
             (64, 256, 1024, 4096, 16384)),
    "trie": ("E25", "Prefix query: trie walk vs scanning every word",
             ("trie characters walked", "scan words examined", "matches"), "operations (log scale)", "stored words n",
             (100, 400, 1600, 6400, 25600)),
    "bst_delete": ("E26", "BST deletion: plain BST vs AVL height after deleting half",
                   ("plain BST height", "AVL height", "log2(n) reference"), "height (nodes)", "keys inserted n",
                   (64, 256, 1024, 4096)),
    "union_find": ("E27", "Union-find path work over n unions + n finds",
                   ("naive", "union by rank", "rank + path compression"), "parent hops (log scale)", "elements n",
                   (64, 256, 1024, 4096)),
    "topo_sort": ("E28", "Topological sort on a random DAG",
                  ("Kahn edges processed", "DFS edges processed", "E (reference)"), "edges", "vertices V", None),
    "open_addressing": ("E29", "Open addressing (linear probing) vs chaining by load factor",
                        ("linear probing (measured)", "chaining (measured)", "probing theory 0.5(1+1/(1-a))"),
                        "mean successful probes", "load factor alpha x 100", (10, 30, 50, 70, 90)),
    "dynamic_array": ("E30", "Hidden copying cost of n appends",
                      ("doubling copies", "x1.5 copies", "+16 increment copies"), "element copies (log scale)",
                      "appends n", (64, 256, 1024, 4096, 16384)),
}
LOG_SCALE = {"array_linked", "ring_buffer", "recursion_dp", "hash_load", "trie", "union_find", "dynamic_array"}


def _random_graph(n, rng, avg_degree=4, weighted=False):
    graph = {i: [] for i in range(n)}
    for u in range(n):
        for _ in range(avg_degree):
            v = rng.randrange(n)
            if v != u:
                graph[u].append((v, rng.randint(1, 20)) if weighted else v)
    return graph


def run_experiment(name, sizes=None, repeats=5):
    if name not in EXPERIMENTS:
        raise ValueError(f"Unknown experiment: {name}")
    sizes = sizes or EXPERIMENTS[name][5] or DEFAULT_SIZES
    rng = random.Random(SEED)
    rows = []
    for n in sizes:
        a = list(range(n))
        shuffled = a.copy()
        rng.shuffle(shuffled)
        if name == "growth":
            rows.append((n, n, n * n, round(n * math.log2(max(n, 2)), 1)))
        elif name == "search":
            rows.append((n, linear_search(a, n + 1)[1], binary_search(a, n + 1)[1],
                         math.floor(math.log2(n)) + 1))
        elif name == "search_cases":
            rows.append((n, linear_search(a, 0)[1],
                         statistics.mean(linear_search(a, x)[1] for x in a),
                         linear_search(a, n + 1)[1]))
        elif name == "sort":
            rows.append((n, bubble_sort(shuffled)[1], merge_sort(shuffled)[1], quick_sort(shuffled)[1]))
        elif name == "sort_cases":
            rows.append((n, insertion_sort(a)[1], insertion_sort(shuffled)[1],
                         insertion_sort(a[::-1])[1]))
        elif name == "runtime":
            queries = shuffled[:32]
            rows.append((n, measure(lambda: [linear_search(a, q) for q in queries], repeats),
                         measure(lambda: [binary_search(a, q) for q in queries], repeats),
                         measure(lambda: merge_sort(shuffled), repeats)))
        elif name == "array_linked":
            def list_front():
                out = []
                for v in range(n):
                    out.insert(0, v)

            def linked_front():
                head = None
                for v in range(n):
                    head = Node(v, head)

            head = None
            for v in range(n):
                head = Node(v, head)
            rows.append((n, measure(list_front, repeats), measure(linked_front, repeats),
                         measure(lambda: linked_traverse(head), repeats)))
        elif name == "stack_queue":
            def drain_stack(data):
                while data:
                    data.pop()

            def drain_deque(data):
                while data:
                    data.popleft()

            def drain_front(data):
                while data:
                    data.pop(0)

            rows.append((n, measure_setup(lambda: list(range(n)), drain_stack, repeats),
                         measure_setup(lambda: deque(range(n)), drain_deque, repeats),
                         measure_setup(lambda: list(range(n)), drain_front, repeats)))
        elif name == "hash":
            d = {x: x for x in a}
            rows.append((n, measure(lambda: [d.get(q) for q in shuffled], repeats),
                         measure(lambda: [linear_search(a, q) for q in shuffled], repeats),
                         measure(lambda: [bisect.bisect_left(a, q) for q in shuffled], repeats)))
        elif name == "bst":
            balanced, skewed = BST(), BST()
            balanced.root = build_balanced(a)
            for x in a:
                skewed.insert(x)
            rows.append((n, balanced.search_steps(n - 1)[1], skewed.search_steps(n - 1)[1],
                         math.floor(math.log2(n)) + 1))
        elif name == "graph":
            g = _random_graph(n, rng)
            edges = sum(len(v) for v in g.values())
            _, eb = bfs_distances(g, 0)
            _, ed = dfs_count(g, 0)
            rows.append((n, eb, ed, edges))
        elif name == "shortest_path":
            g = _random_graph(n, rng, weighted=True)
            stats = {}
            dijkstra(g, 0, stats)
            rows.append((n, stats["relaxations"], stats["pushes"], sum(len(v) for v in g.values())))
        elif name == "recursion_dp":
            k = n
            value, naive = fib_naive_calls(k)
            value2, memo = fib_memo_calls(k)
            assert value == value2 == fib_dp(k)
            rows.append((k, naive, memo, k))
        elif name == "memory":
            rows.append((n, peak_kib(lambda: list(range(n))), peak_kib(lambda: {x: x for x in range(n)}),
                         peak_kib(lambda: deque(range(n)))))
        elif name == "sorting_stability":
            records = [(x % 5, i) for i, x in enumerate(shuffled)]   # 5 keys, many duplicates
            rows.append((n, stability_violations(merge_sort, records),
                         stability_violations(insertion_sort, records),
                         stability_violations(heap_sort, records)))
        elif name == "hash_singly":
            table = chain_table(n, max(1, n // 4), "singly", keys=shuffled)
            assert table.get(n - 1)[0] == 2 * (n - 1)
            probes = statistics.mean(table.get(x)[1] for x in range(n))
            rows.append((n, probes, table.max_chain(), 1 + table.load_factor() / 2))
        elif name == "hash_doubly":
            table = chain_table(n, max(1, n // 4), "doubly", keys=shuffled)
            for x in range(0, n, 3):
                assert table.delete(x)
            assert table.validate()
            for x in range(0, n, 3):
                table.put(x, 2 * x)
            assert table.validate() and table.size == n
            probes = statistics.mean(table.get(x)[1] for x in range(n))
            rows.append((n, probes, table.max_chain(), 1 + table.load_factor() / 2))
        elif name == "hash_load":
            m = max(1, n // 8)
            uniform = chain_table(n, m, "singly", keys=shuffled)
            adversarial = chain_table(n, m, "singly", keys=[i * m for i in range(n)])  # all in bucket 0
            rows.append((n, statistics.mean(uniform.get(x)[1] for x in shuffled),
                         statistics.mean(adversarial.get(i * m)[1] for i in range(n)),
                         1 + uniform.load_factor() / 2))
        elif name == "tree_stack_queue":
            tree = build_balanced(a)
            assert inorder_stack(tree) == a and sorted(levelorder_queue(tree)) == a
            rows.append((n, measure(lambda: inorder_stack(tree), repeats),
                         measure(lambda: preorder_stack(tree), repeats),
                         measure(lambda: levelorder_queue(tree), repeats)))
        elif name == "avl":
            avl = plain = None
            for key in a:
                avl = avl_insert(avl, key)
                plain = bst_insert_node(plain, key)
            h = validate_avl(avl)
            assert inorder_stack(avl) == a
            rows.append((n, tree_search_steps(avl, n - 1), tree_search_steps(plain, n - 1), h))
        elif name == "circular_singly":
            k = 3
            o1, moves = josephus_circular(n, k)
            o2, shifts = josephus_list(n, k)
            assert o1 == o2 and o1[-1] == josephus_formula(n, k)
            rows.append((n, moves, shifts, n * (k - 1)))
        elif name == "circular_doubly":
            ops = [rng.randrange(2 * n) for _ in range(max(4000, 8 * n))]   # enough to fill the cache

            def run_cache(cache):
                for key in ops:
                    if cache.get(key) is None:
                        cache.put(key, key)

            def od_cache():
                od = OrderedDict()
                for key in ops:
                    if key in od:
                        od.move_to_end(key)
                    else:
                        od[key] = key
                        if len(od) > n:
                            od.popitem(last=False)

            per_op = 1000 / len(ops)
            rows.append((n, per_op * measure(lambda: run_cache(LRUCache(n)), repeats),
                         per_op * measure(lambda: run_cache(ListLRU(n)), repeats),
                         per_op * measure(od_cache, repeats)))
        elif name == "ring_buffer":
            def ring():
                q = RingBuffer(max(1, n // 2), grow=True)
                for _ in range(4):
                    for v in range(n):
                        q.enqueue(v)
                    while not q.is_empty():
                        q.dequeue()

            def dq():
                q = deque()
                for _ in range(4):
                    for v in range(n):
                        q.append(v)
                    while q:
                        q.popleft()

            def lst():
                q = []
                for _ in range(4):
                    for v in range(n):
                        q.append(v)
                    while q:
                        q.pop(0)

            rows.append((n, measure(ring, repeats), measure(dq, repeats), measure(lst, repeats)))
        elif name == "heap":
            data = shuffled
            h1 = MinHeap(data)
            assert h1.is_heap()
            h2 = MinHeap()
            for x in data:
                h2.push(x)
            assert h2.is_heap()
            rows.append((n, h1.swaps, h2.swaps, n))
        elif name == "trie":
            letters = "abcdefghijklmnopqrstuvwxyz"
            words = {"".join(rng.choice(letters) for _ in range(rng.randint(4, 9))) for _ in range(n)}
            words = sorted(words)
            t = Trie(words)
            prefix = words[len(words) // 2][:3]
            node, walked = t._walk(prefix)
            matches = t.starts_with(prefix)
            assert matches == [w for w in words if w.startswith(prefix)]
            rows.append((len(words), walked, len(words), len(matches)))
        elif name == "bst_delete":
            plain = avl = None
            for key in shuffled:
                plain = bst_insert_node(plain, key)
                avl = avl_insert(avl, key)
            for key in shuffled[: n // 2]:
                plain = bst_delete(plain, key)
                avl = avl_delete(avl, key)
            remaining = sorted(shuffled[n // 2:])
            assert inorder_recursive(plain) == remaining == inorder_stack(avl)
            assert is_bst(plain)
            rows.append((n, tree_height(plain), validate_avl(avl), round(math.log2(n), 2)))
        elif name == "union_find":
            results = []
            for rank, compress in ((False, False), (True, False), (True, True)):
                uf = UnionFind(n, rank=rank, compress=compress)
                for i in range(n - 1):
                    uf.union(i, i + 1)                # builds a chain for the naive version
                for _ in range(n):
                    uf.find(0)
                assert uf.components == 1
                results.append(uf.steps)
            rows.append((n, *results))
        elif name == "topo_sort":
            order = shuffled
            rank = {v: i for i, v in enumerate(order)}
            g = {v: [] for v in range(n)}
            for _ in range(3 * n):
                u, v = rng.randrange(n), rng.randrange(n)
                if u != v:
                    if rank[u] > rank[v]:
                        u, v = v, u
                    g[u].append(v)                    # edges respect a hidden order -> DAG
            o1, p1 = topo_sort_kahn(g)
            o2, p2 = topo_sort_dfs(g)
            for out in (o1, o2):
                pos = {v: i for i, v in enumerate(out)}
                assert all(pos[u] < pos[v] for u in g for v in g[u])
            rows.append((n, p1, p2, sum(len(v) for v in g.values())))
        elif name == "open_addressing":
            alpha = n / 100
            m = 2048
            count = int(alpha * m)
            keys = rng.sample(range(10 ** 7), count)
            oa = OpenAddressHash(m, max_load=None)
            ch = ChainHash(m, "singly")
            for k in keys:
                oa.put(k, k)
                ch.put(k, k)
            probes_oa = statistics.mean(oa.get(k)[1] for k in keys)
            probes_ch = statistics.mean(ch.get(k)[1] for k in keys)
            rows.append((n, probes_oa, probes_ch, 0.5 * (1 + 1 / (1 - alpha))))
        elif name == "dynamic_array":
            copies = []
            for growth in (2.0, 1.5, 16):
                arr = DynamicArray(growth)
                for v in range(n):
                    arr.append(v)
                assert arr.to_list() == list(range(n))
                copies.append(arr.copies)
            rows.append((n, *copies))
    return rows


def save_plot(name, rows, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ident, title, labels, ylabel, xlabel, _ = EXPERIMENTS[name]
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    stem = f"{ident}_{name}"
    with (output / f"{stem}.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([xlabel, *labels])
        writer.writerows(rows)
    fig, ax = plt.subplots(figsize=(9, 5))
    styles = ("-o", "-s", "--^")
    for j, label in enumerate(labels):
        ax.plot([r[0] for r in rows], [r[j + 1] for r in rows], styles[j], label=label)
    if name in LOG_SCALE:
        ax.set_yscale("log")
    ax.set_title(f"{ident} - {title}")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(alpha=.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output / f"{stem}.png", dpi=150)
    plt.close(fig)
    return output / f"{stem}.png"


def save_diagrams(output):
    """Reference drawings of every linked structure used in the course."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    draw_structure("singly", [7, 11, 19], output / "singly.png", "Singly linked list")
    draw_structure("doubly", [7, 11, 19], output / "doubly.png", "Doubly linked list")
    draw_structure("circular", [7, 11, 19, 23], output / "circular_singly.png",
                   "Circular singly linked list (tail.next is the head)")
    draw_structure("circular-doubly", [7, 11, 19], output / "circular_doubly.png",
                   "Circular doubly linked list with sentinel S")
    rb = RingBuffer(8)
    for v in range(10, 16):
        rb.enqueue(v)
    for _ in range(4):
        rb.dequeue()
    for v in range(16, 20):
        rb.enqueue(v)
    draw_structure("ring-buffer", (rb.block, rb.front, rb.count), output / "ring_buffer.png",
                   "Ring buffer after wrap-around (front=4, count=6)")
    root = None
    for k in (8, 4, 12, 2, 6, 10, 14):
        root = bst_insert_node(root, k)
    draw_tree(root, output / "bst.png", "BST from keys 8,4,12,2,6,10,14")
    avl = None
    for k in range(1, 16):
        avl = avl_insert(avl, k)
    draw_tree(avl, output / "avl.png", "AVL tree after inserting 1..15 in order")


# =============================================================================
# 14. Self-tests (run before every experiment)
# =============================================================================
def self_test():
    rng = random.Random(SEED)
    # searching and sorting
    for n in (0, 1, 2, 17, 64):
        a = list(range(n))
        for fn in (bubble_sort, selection_sort, insertion_sort, merge_sort, quick_sort, heap_sort):
            assert fn(a[::-1])[0] == a
            assert fn([2, 1, 2, 0])[0] == [0, 1, 2, 2]
        assert quick_sort_inplace(a[::-1])[0] == a
        assert linear_search(a, -1)[0] == -1 and binary_search(a, -1)[0] == -1
    assert first_occurrence([1, 2, 2, 2, 3], 2) == 1 and first_occurrence([1, 3], 2) == -1
    assert counting_sort([3, 0, 2, 3, 1], 3) == [0, 1, 2, 3, 3]
    recs = [(1, 0), (0, 1), (1, 2), (0, 3)]
    assert stability_violations(merge_sort, recs) == 0
    assert stability_violations(insertion_sort, recs) == 0
    # dynamic array
    arr = DynamicArray(2.0)
    for v in range(9):
        arr.append(v)
    arr.insert(0, -1)
    assert arr.to_list() == [-1, *range(9)] and arr.capacity == 16 and arr.copies == 1 + 2 + 4 + 8
    assert row_major(1, 2, 3) == 5 and col_major(1, 2, 2) == 5 and row_major_3d(1, 2, 3, 3, 4) == 23
    # singly / doubly
    s = SinglyLinkedList([1, 2, 3])
    s.push_front(0); s.push_back(4)
    assert s.to_list() == [0, 1, 2, 3, 4] and s.validate()
    assert s.remove(0) and s.remove(4) and s.remove(2) and not s.remove(9)
    assert s.to_list() == [1, 3] and s.validate() and s.tail.value == 3
    s.reverse()
    assert s.to_list() == [3, 1] and s.validate() and s.pop_back() == 1 and s.pop_back() == 3
    assert s.validate() and s.head is None and s.tail is None
    d = DoublyLinkedList([1, 2, 3])
    node, _ = d.find(2)
    d.unlink(node)
    assert d.to_list() == [1, 3] == d.to_list_backward()[::-1] and d.validate()
    assert d.pop_back() == 3 and d.pop_front() == 1 and d.validate() and d.size == 0
    # circular singly
    c = CircularSinglyLinkedList()
    assert c.validate() and c.to_list() == [] and c.find(1) == (None, 0)
    c.push_back(1)
    assert c.tail.next is c.tail and c.validate()
    c.push_back(2); c.push_front(0)
    assert c.to_list() == [0, 1, 2] and c.validate() and c.head.value == 0
    assert c.rotate(1) == 1 and c.to_list() == [1, 2, 0]
    assert c.find(9)[1] == 3                          # stops after one lap
    assert c.remove(0) and c.to_list() == [1, 2] and c.validate() and c.tail.value == 2
    assert c.pop_front() == 1 and c.pop_front() == 2 and c.tail is None and c.validate()
    assert josephus_circular(7, 3)[0] == [3, 6, 2, 7, 5, 1, 4] == josephus_list(7, 3)[0]
    assert josephus_formula(7, 3) == 4 and josephus_formula(41, 3) == 31
    # circular doubly with sentinel
    cd = CircularDoublyLinkedList([1, 2, 3, 4, 5])
    assert cd.validate() and cd.to_list_backward() == [5, 4, 3, 2, 1]
    assert cd.rotate(2) == 2 and cd.to_list() == [3, 4, 5, 1, 2] and cd.validate()
    assert cd.rotate(-1) == 1 and cd.to_list() == [2, 3, 4, 5, 1] and cd.validate()
    assert cd.rotate(4) == 1 and cd.to_list() == [1, 2, 3, 4, 5]   # forward 4 = back 1
    assert cd.pop_front() == 1 and cd.pop_back() == 5 and cd.to_list() == [2, 3, 4] and cd.validate()
    empty = CircularDoublyLinkedList()
    assert empty.validate() and empty.sentinel.next is empty.sentinel and empty.rotate(3) == 0
    lru = LRUCache(2)
    lru.put("a", 1); lru.put("b", 2)
    assert lru.get("a") == 1
    lru.put("c", 3)                                   # evicts b (least recently used)
    assert lru.get("b") is None and lru.keys() == ["c", "a"] and lru.order.validate()
    # cycle detection
    n1, n2, n3, n4 = Node(1), Node(2), Node(3), Node(4)
    n1.next, n2.next, n3.next, n4.next = n2, n3, n4, n2
    assert floyd_cycle(n1) == (True, 1, 3)
    assert floyd_cycle(Node(1, Node(2))) == (False, None, None)
    assert floyd_cycle(CircularSinglyLinkedList([1, 2, 3]).head)[0]
    # stack / queue applications and ring buffer
    assert balanced_brackets("{[()()]}") and not balanced_brackets("([)]") and not balanced_brackets("((")
    assert evaluate_postfix("3 4 + 2 *") == 14
    rb = RingBuffer(3)
    for v in (1, 2, 3):
        rb.enqueue(v)
    assert rb.is_full() and rb.dequeue() == 1
    rb.enqueue(4)
    assert rb.to_list() == [2, 3, 4] and rb.wraps == 1
    try:
        rb.enqueue(5)
        raise AssertionError("overflow not detected")
    except OverflowError:
        pass
    # hash tables
    for kind in ("singly", "doubly"):
        table = ChainHash(2, kind)
        for k in (0, 2, 4):
            table.put(k, str(k))
        assert table.max_chain() == 3 and table.validate()
        assert table.get(2)[0] == "2" and table.delete(2) and table.validate()
        assert table.get(2)[0] is None and not table.delete(2)
        table.put(4, "updated")
        assert table.size == 2 and table.get(4)[0] == "updated"
    grow = ChainHash(2, "singly", max_load=1.0)
    for k in range(20):
        grow.put(k, k)
    assert len(grow.buckets) >= 16 and grow.validate() and all(grow.get(k)[0] == k for k in range(20))
    oa = OpenAddressHash(4)
    for k in range(10):
        oa.put(k, k * k)
    assert all(oa.get(k)[0] == k * k for k in range(10))
    assert oa.delete(3) and oa.get(3)[0] is None and oa.get(4)[0] == 16
    oa.put(3, 99)
    assert oa.get(3)[0] == 99 and oa.size == 10
    # trees
    root = None
    for k in (8, 4, 12, 2, 6, 10, 14):
        root = bst_insert_node(root, k)
    assert inorder_stack(root) == inorder_recursive(root) == [2, 4, 6, 8, 10, 12, 14]
    assert preorder_stack(root) == [8, 4, 2, 6, 12, 10, 14]
    assert postorder_stack(root) == [2, 6, 4, 10, 14, 12, 8]
    assert levelorder_queue(root) == [8, 4, 12, 2, 6, 10, 14]
    root = bst_delete(root, 2)                        # leaf
    root = bst_delete(root, 12)                       # two children
    root = bst_delete(root, 14)                       # leaf -> 10 left alone
    assert inorder_stack(root) == [4, 6, 8, 10] and is_bst(root)
    root = bst_delete(root, 4)                        # one child
    assert inorder_stack(root) == [6, 8, 10] and is_bst(root)
    for keys in ([30, 20, 10], [10, 20, 30], [30, 10, 20], [10, 30, 20]):
        r = None
        for k in keys:
            r = avl_insert(r, k)
        assert validate_avl(r) == 2 and r.key == 20
        assert preorder_stack(r) == [20, 10, 30] and postorder_stack(r) == [10, 30, 20]
    t = None
    keys = list(range(200))
    rng.shuffle(keys)
    for k in keys:
        t = avl_insert(t, k)
    for k in keys[:150]:
        t = avl_delete(t, k)
        validate_avl(t)
    assert inorder_stack(t) == sorted(keys[150:])
    # heap and trie
    h = MinHeap([5, 3, 8, 1, 9, 2])
    assert h.is_heap() and [h.pop() for _ in range(6)] == [1, 2, 3, 5, 8, 9]
    tr = Trie(["cat", "car", "cart", "dog"])
    assert tr.contains("car") and not tr.contains("ca") and tr.starts_with("ca") == ["car", "cart", "cat"]
    assert tr.delete("cart") and not tr.contains("cart") and tr.contains("car") and tr.words == 3
    # graphs
    assert bfs({0: [1, 2], 1: [3], 2: [], 3: []}, 0) == [0, 1, 2, 3]
    assert dfs({0: [1, 2], 1: [3], 2: [], 3: []}, 0) == [0, 1, 3, 2]
    g = {"A": [("B", 2), ("C", 8)], "B": [("C", 1)], "C": []}
    assert dijkstra(g, "A")["C"] == 3 and dijkstra_path(g, "A", "C") == (["A", "B", "C"], 3)
    dag = {"shop": ["cook"], "cook": ["pack"], "pack": ["deliver"], "deliver": []}
    assert topo_sort_kahn(dag)[0] == ["shop", "cook", "pack", "deliver"] == topo_sort_dfs(dag)[0]
    for fn in (topo_sort_kahn, topo_sort_dfs):
        try:
            fn({1: [2], 2: [1]})
            raise AssertionError("cycle not detected")
        except ValueError:
            pass
    uf = UnionFind(5)
    uf.union(0, 1); uf.union(3, 4)
    assert uf.find(0) == uf.find(1) and uf.find(0) != uf.find(3) and uf.components == 3
    assert kruskal(4, [(1, 0, 1), (3, 1, 2), (2, 0, 2), (4, 2, 3)])[1] == 7
    # recursion, DP, backtracking, greedy
    assert fib_naive_calls(10) == (55, 177) and fib_memo_calls(10)[0] == 55 and fib_dp(10) == 55
    assert knapsack_01([1, 3, 4, 5], [1, 4, 5, 7], 7) == (9, [1, 2])
    assert n_queens(6)[0] == 4 and n_queens(8)[0] == 92
    assert len(interval_schedule([(1, 4), (3, 5), (0, 6), (5, 7), (8, 9), (5, 9)])) == 3
    print("All data-structure and algorithm self-tests passed.")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--all", action="store_true", help="run E01-E30")
    parser.add_argument("--experiment", choices=sorted(EXPERIMENTS))
    parser.add_argument("--list", action="store_true", help="print the experiment register")
    parser.add_argument("--diagrams", action="store_true", help="draw the structure diagrams")
    parser.add_argument("--output", default="dsa_lab/results")
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args()
    if args.list:
        for name, (ident, title, *_rest) in EXPERIMENTS.items():
            print(f"{ident}  {name:<18} {title}")
        return
    self_test()
    if args.diagrams:
        save_diagrams(Path(args.output) / "diagrams")
        print("Diagrams ->", Path(args.output) / "diagrams")
    if not args.all and not args.experiment:
        if not args.diagrams:
            parser.print_help()
        return
    for name in (EXPERIMENTS if args.all else [args.experiment]):
        rows = run_experiment(name, repeats=max(1, args.repeats))
        save_plot(name, rows, Path(args.output))
        print(f"{EXPERIMENTS[name][0]} {name}: last row {rows[-1]} -> {args.output}")


if __name__ == "__main__":
    main()
