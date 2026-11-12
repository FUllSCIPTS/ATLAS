# Python Programming with ATLAS Go — an illustrated, standalone course

**Level:** absolute beginner to intermediate. **Plan:** 20 lessons (Part I) + 15 software-testing lessons (Part II) + 12 app-integration labs (Part III) + 10 graded app-building tickets (Part IV), 14–20 weeks. **Tools:** Python 3.10+, a browser, Google Colab (nothing to install). No Android device needed.

[Open the 20 labs in Colab](https://colab.research.google.com/github/FUllSCIPTS/ATLAS/blob/main/python_lab/Python_Colab_Labs.ipynb) · [Lab manual](../python_lab/README.md) · [Lab source](../python_lab/experiments.py) · [ATLAS Go UML](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/docs/UML_BLUEPRINT.md#android-app-atlas-go) · [ATLAS Go method catalogue](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/docs/ARCHITECTURE.md#complete-source-method-catalog)

**How every lesson is built:** *idea* (plain-language explanation and a picture) → *worked examples* (run them; the expected output is shown or asserted) → *common mistakes* → *ATLAS Go* (where the real app uses the idea, with a link to the exact function) → *lab* (what the experiment measures and what its chart shows) → *exercises*. Every code block in this guide runs as written; blocks that use ATLAS Go code first add `android-app` to the import path.

~~~mermaid
flowchart LR
 A["1–6<br/>running code, values,<br/>types, decisions, loops, text"] --> B["7–10<br/>collections,<br/>comprehensions, functions"]
 B --> C["11–13<br/>classes, inheritance,<br/>exceptions"]
 C --> D["14–17<br/>files, generators,<br/>functional style, sorting"]
 D --> E["18–20<br/>complexity, testing, profiling,<br/>modules, packages, imports"]
 E --> F["Part II<br/>software testing"]
 F --> G["Part III<br/>real apps: button → API → database"]
 G --> H["Part IV<br/>graded app-building tickets"]
~~~

## Where the ideas live in ATLAS Go

ATLAS Go is a Python/Kivy Android app that keeps users, rides and food orders on the phone in a JSON file. Arrows below mean "uses".

~~~mermaid
flowchart TD
 UI["app.py — AtlasGoApp (Kivy App subclass): screens, buttons"] --> STORE["store.py — LocalStore: accounts, rides, orders, JSON persistence"]
 UI --> GEO["geo.py — distances, ETAs, map tiles"]
 UI --> AI["intelligence.py — Candidate, rank, choose, outlook, self_test"]
 STORE --> DOMAIN["domain.py — fare, Offer, Cart, Catalog"]
 STORE --> ACC["accounts.py — clean_email, parse_int, password hashing"]
 STORE --> FILE[("state.json")]
~~~

| Lesson | Topic | ATLAS Go code that uses it | Lab |
|---|---|---|---|
| 1 | Running Python, print, comments | [`AtlasGoApp.build`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/app.py) | P01 execution order |
| 2 | Numbers and operators | [`domain.fare`, `money`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/domain.py) | P02 float vs cents |
| 3 | Types and conversion | [`accounts.parse_int`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/accounts.py) | P03 conversion matrix |
| 4 | Conditions and Boolean logic | [`LocalStore.set_online`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) | P04 decision table |
| 5 | Loops | [`intelligence.outlook`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py) | P05 loop counts |
| 6 | Strings and Unicode | [`accounts.clean_email`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/accounts.py) | P06 bytes vs characters |
| 7 | Lists, slicing, aliasing | [`LocalStore.my_history`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) | P07 list over-allocation |
| 8 | Tuples, sets, dicts | [`Cart.items`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/domain.py) | P08 Counter |
| 9 | Comprehensions | [`geo.tile_range`, `online_drivers`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/geo.py) | P09 distance matrix |
| 10 | Functions, scope, recursion | [`geo.eta_minutes`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/geo.py) | P10 call counts |
| 11 | Classes and dataclasses | [`intelligence.Candidate`, `domain.Offer`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py) | P11 Ride class |
| 12 | Inheritance and polymorphism | [`AtlasGoApp(App)`, `LiveMap(StencilView)`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/app.py) | P12 vehicle classes |
| 13 | Exceptions and validation | [`LocalStore.validate`, `clean_email`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) | P13 messy records |
| 14 | Files, pathlib, JSON, CSV | [`LocalStore.save`, `commit`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) | P14 JSON vs CSV, atomic writes |
| 15 | Iterators and generators | [`LiveMap.visible_tiles`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/livemap.py) | P15 memory |
| 16 | Lambda, map, filter, reduce | [`intelligence.rank`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py) | P16 driver pipeline |
| 17 | Sorting and selection | [`intelligence.choose`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py) | P17 top-k comparisons |
| 18 | Complexity and searching | [`LocalStore.online_drivers`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) | P18 search counts |
| 19 | Testing and debugging | [`intelligence.self_test`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py) | P19 mutation testing |
| 20 | Profiling and project structure | [`intelligence.LearningLab`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py) | P20 timeit |

The labs use **synthetic** data (made-up rides and drivers). A link to ATLAS Go means the real app uses the *idea*; the lab code is a simplified teaching version.

---

# Part I — Python foundations

## Lesson 1 — Running Python: statements, print, comments and execution order

**Idea.** A Python program is a list of **statements**. The interpreter runs them **one at a time, top to bottom**, unless a statement (a loop, `if`, function call) sends it elsewhere. `print()` shows a value; a comment (`# …`) is ignored by Python and written for humans. Indentation (4 spaces) groups statements into **blocks**.

~~~mermaid
flowchart TD
 S1["1 total = 0"] --> S2{"2 for km in (2, 3):<br/>another km?"}
 S2 -- "yes" --> S3["3 fare = 350 + 170 * km"] --> S4["4 total = total + fare"] --> S2
 S2 -- "no" --> S5["5 message = f'total {total} cents'"]
~~~

~~~python
# A receipt for two rides: 2 km and 3 km.
total = 0                          # line 1: start at zero cents
for km in (2, 3):                  # line 2: repeat for each distance
    fare = 350 + 170 * km          # line 3: base fare + per-km rate
    total = total + fare           # line 4
message = f"total {total} cents"   # line 5
print(message)                     # total 1550 cents
assert message == "total 1550 cents"
~~~

**Ways to run Python:** a Colab/Jupyter cell (cells share variables — use *Runtime → Restart and run all* to check a notebook works from scratch); the interactive prompt `python3` (prints every expression's value); a script `python3 receipt.py` (prints only what you `print`).

**Reading error messages.** Read the **last line first**: it names the error type and message; the lines above show where it happened.

| Error | Typical cause |
|---|---|
| `SyntaxError` | malformed code: missing `:` or bracket |
| `IndentationError` | inconsistent spaces in a block |
| `NameError` | using a name before assigning it, or a typo |
| `TypeError` | operation on the wrong type (`"3" + 4`) |

**ATLAS Go:** the app starts in [`AtlasGoApp.build`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/app.py), which runs statement by statement to create the store, load state and build the first screen.

**Lab P01** records which line runs at every step of the program above using `sys.settrace`. The chart plots *step* against *line number*: you can see the jump back to line 2 each time the loop repeats (1, 2, 3, 4, 2, 3, 4, 2, 5).

**Exercises.** (1) Predict the trace if the tuple were `(2, 3, 5)`. (2) Introduce each error in the table on purpose and read the message.

## Lesson 2 — Variables, numbers and operators

**Idea.** `name = value` **binds** a name to a value. Python has whole numbers (`int`, unlimited size), decimals (`float`, 64-bit binary floating point) and `complex`.

| Operator | Meaning | Example | Result |
|---|---|---|---|
| `+ - *` | add, subtract, multiply | `350 + 170 * 3` | `860` (precedence: `*` first) |
| `/` | true division, always float | `7 / 2` | `3.5` |
| `//` | floor division (rounds **down**) | `7 // 2`, `-7 // 2` | `3`, `-4` |
| `%` | remainder (sign of the divisor) | `7 % 2`, `-7 % 2` | `1`, `1` |
| `**` | power | `2 ** 10` | `1024` |
| `round` | banker's rounding to even | `round(2.5)`, `round(3.5)` | `2`, `4` |

~~~python
assert 350 + 170 * 3 == 860
assert (7 // 2, -7 // 2, 7 % 2, -7 % 2) == (3, -4, 1, 1)
assert divmod(1118, 100) == (11, 18)          # euros and cents
assert round(2.5) == 2 and round(3.5) == 4    # round half to even
print(0.1 + 0.2)                               # 0.30000000000000004
assert 0.1 + 0.2 != 0.3
~~~

**Why money is stored in integer cents.** 0.10 has no exact binary representation, so adding it repeatedly drifts. `int` cents (or `decimal.Decimal`) are exact.

~~~python
from decimal import Decimal
total = 0.0
for _ in range(10):
    total += 0.10                                           # ten 10-cent fares as floats
assert total != 1.0 and total == 0.9999999999999999         # float drift
# (since Python 3.12, sum() of floats compensates for this; repeated += does not)
assert sum([10] * 10) == 100                                # integer cents: exact
assert sum([Decimal("0.10")] * 10) == Decimal("1.00")       # Decimal: exact
~~~

**ATLAS Go** stores every price in cents: [`domain.fare`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/domain.py) computes `(350 + distance * 170) * (130 if comfort else 100) // 100` and [`money`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/domain.py) formats it with `//` and `%`.

~~~python
import sys; sys.path.insert(0, "android-app")
from atlas_go.domain import fare, money
assert fare(0, 1) == 860 and money(fare(0, 1, comfort=True)) == "€11.18"
~~~

**Lab P02** adds 10 cents *n* times as floats and as integers, for n up to a million, and plots the error against the exact answer (log scale): the float error grows, the integer error stays exactly zero.

**Exercises.** (1) Why is `-7 // 2` equal to −4? (2) Write `split_bill(cents, people)` so the parts are whole cents and add up exactly.

## Lesson 3 — Types and conversion

**Idea.** Every value has a **type**: `int`, `float`, `str`, `bool` (`True`/`False`), `NoneType` (`None`, "no value"). `type(x)` tells you; `isinstance(x, int)` tests it. Text from a keyboard or file is always `str` and must be **converted**, and conversion can fail.

~~~python
assert type(42) is int and type("42") is str and type(None).__name__ == "NoneType"
assert int(" 42 ") == 42 and float("3.5") == 3.5 and str(7) == "7"
assert int("1A", 16) == 26
assert bool("") is False and bool("False") is True     # any non-empty string is True!
assert isinstance(True, int)                            # bool is a subclass of int
try:
    int("3.5")
except ValueError as e:
    print("ValueError:", e)
~~~

**Truthiness:** `0`, `0.0`, `""`, `[]`, `{}`, `None` and `False` are *falsy*; almost everything else is *truthy*.

**ATLAS Go:** [`accounts.parse_int`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/accounts.py) converts form text, turns a failure into a friendly message and checks the range:

~~~python
import sys; sys.path.insert(0, "android-app")
from atlas_go.accounts import parse_int
assert parse_int(" 12 ", "Prep time", 1, 60) == 12
for bad in ("twelve", "0", "61", None):
    try:
        parse_int(bad, "Prep time", 1, 60)
    except ValueError as e:
        print(repr(bad), "->", e)
~~~

**Lab P03** tries five converters (`int`, `float`, `int(s, 16)`, `bool`, `Decimal`) on ten strings and draws a success/failure heatmap. Surprises to explain: `int(" 7 ")` works (spaces stripped); `float("1e3")` works; `int("1e3", 16)` works (it is hexadecimal!); the Arabic-Indic digit `"٣"` converts to 3; `bool` never fails.

**Exercises.** (1) Write `to_bool(text)` that accepts yes/no/true/false in any case and rejects anything else. (2) Why can `isinstance(True, int)` cause a validation bug (see Part II, T12)?

## Lesson 4 — Conditions and Boolean logic

**Idea.** `if / elif / else` chooses one branch. Comparisons (`== != < <= > >=`, `in`, `is`) produce `bool`; `and`, `or`, `not` combine them. `and`/`or` **short-circuit**: Python stops as soon as the answer is known.

~~~mermaid
flowchart TD
 A{"online?"} -- no --> R1["not eligible"]
 A -- yes --> B{"rating ≥ 4.5?"}
 B -- no --> R1
 B -- yes --> C{"distance ≤ 5 km?"}
 C -- no --> R1
 C -- yes --> R2["eligible"]
~~~

~~~python
def eligible(online, rating, distance_km):
    return online and rating >= 4.5 and distance_km <= 5

def describe(rating):
    if rating >= 4.8:
        return "excellent"
    elif rating >= 4.5:
        return "good"
    else:
        return "needs review"

assert eligible(True, 4.6, 3) and not eligible(True, 4.6, 7) and not eligible(False, 5.0, 1)
assert [describe(r) for r in (4.9, 4.5, 4.0)] == ["excellent", "good", "needs review"]
assert 3 < 4 < 5                            # chained comparison
assert (None or "default") == "default"     # or returns the first truthy operand
~~~

**`==` vs `is`:** `==` compares values; `is` asks "same object?" Use `is` only for `None`, `True`, `False`.

**Decision tables** list every combination of conditions and the expected result — the basis of the boundary tests in Part II.

| online | rating ≥ 4.5 | ≤ 5 km | eligible |
|---|---|---|---|
| F | – | – | F |
| T | F | – | F |
| T | T | F | F |
| T | T | T | **T** |

**ATLAS Go:** [`LocalStore.set_online`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) starts with a guard — `if not user or user['role'] != 'driver': raise ValueError(...)` — so only signed-in drivers can go online.

**Lab P04** evaluates the rule over a grid of ratings (3.0–5.0) and distances (0–8 km) and draws the result as a heatmap — the decision table as a picture. It also proves short-circuiting by recording which conditions were actually evaluated.

**Exercises.** (1) Rewrite `describe` with the conditions in the wrong order and find the bug. (2) Write a decision table for "comfort rides need a rating ≥ 4.7 *or* a car newer than 2022".

## Lesson 5 — Loops: for, while, range, enumerate, zip, break, continue

**Idea.** A `for` loop runs its block once **per item** of an iterable (list, string, `range`, dict…). A `while` loop repeats **while a condition is true** — you must make sure it eventually becomes false.

~~~python
for km in range(1, 4):                # 1, 2, 3   (start, stop is excluded)
    print(km, "km")
places = ["UCC", "Kent Station"]
for i, place in enumerate(places, start=1):
    print(i, place)                    # 1 UCC / 2 Kent Station
for place, km in zip(places, [3, 5]):
    print(place, km)
total = 0
for fare in [520, -1, 860, 0, 1200]:
    if fare < 0:
        continue                       # skip bad data
    if fare == 0:
        break                          # stop at the sentinel
    total += fare
assert total == 1380
~~~

~~~python
seconds, guess, x = 0, 10.0, 10.0
while abs(guess * guess - x) > 1e-9:  # Newton's method for √10
    guess = (guess + x / guess) / 2
    seconds += 1
assert round(guess, 6) == round(10 ** 0.5, 6) and seconds < 10
~~~

**How many times does a loop run?** That number is the heart of complexity (Lesson 18).

| Loop | Iterations for n = 64 |
|---|---|
| `for i in range(n)` | 64 |
| nested `for i … for j in range(n)` | 4 096 |
| `while n > 1: n //= 2` | 6 |

**ATLAS Go:** [`intelligence.outlook`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py) loops `for h in range(24)` to build the 24-hour demand forecast shown on the home screen.

**Lab P05** counts loop iterations for single, nested, halving and Newton loops as n grows (log scale): four different growth shapes from four loop shapes.

**Exercises.** (1) Print a 5×5 multiplication table with nested loops. (2) Write a `while` loop that asks for input until a valid number is given (use `input()` in Colab).

## Lesson 6 — Strings and Unicode

**Idea.** A `str` is an immutable sequence of Unicode **code points**. Text on disk or on a network is **bytes**; `encode()` turns text into bytes, `decode()` back. UTF-8 uses 1 byte for ASCII and 2–4 bytes for other characters.

~~~mermaid
flowchart LR
 T["str: 'Átha'<br/>4 code points"] -- ".encode('utf-8')" --> B["bytes: b'\xc3\x81tha'<br/>5 bytes"]
 B -- ".decode('utf-8')" --> T
~~~

~~~python
city = "Baile Átha Cliath"
assert city[0] == "B" and city[-1] == "h" and city[6:10] == "Átha"     # indexing and slicing
assert city.lower().startswith("baile") and city.split() == ["Baile", "Átha", "Cliath"]
assert len(city) == 17 and len(city.encode("utf-8")) == 18             # Á takes 2 bytes
assert "-".join(["Cork", "Kent"]) == "Cork-Kent" and "  ucc ".strip() == "ucc"
fare = 1118
assert f"€{fare // 100}.{fare % 100:02d}" == "€11.18"                  # f-string formatting

import unicodedata
nfc, nfd = unicodedata.normalize("NFC", "é"), unicodedata.normalize("NFD", "é")
assert (len(nfc), len(nfd)) == (1, 2) and nfc != nfd                    # same look, different text!
assert "Straße".casefold() == "strasse"                                 # use casefold() to compare
~~~

Strings are **immutable**: `s.upper()` returns a *new* string. Build long strings with `"".join(parts)`, not `+=` in a loop.

**ATLAS Go:** [`accounts.clean_email`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/accounts.py) strips spaces, lower-cases, limits the length to 80 and checks a regular expression:

~~~python
import sys; sys.path.insert(0, "android-app")
from atlas_go.accounts import clean_email
assert clean_email("  Student@Example.IE ") == "student@example.ie"
~~~

**Lab P06** compares, for six place names (English, Irish, Tamil, Japanese, emoji), the number of characters, UTF-8 bytes and UTF-16 units. A database column limited to "20 bytes" and a form limited to "20 characters" are not the same limit.

**Exercises.** (1) Write `initials("Baile Átha Cliath") → "BÁC"`. (2) Why must you normalise before comparing user-typed names?

## Lesson 7 — Lists: indexing, slicing, mutation, aliasing and copies

**Idea.** A `list` is an ordered, **mutable** sequence. Indexes start at 0; negative indexes count from the end; a slice `a[start:stop:step]` makes a new list.

~~~python
rides = ["r1", "r2", "r3", "r4"]
assert rides[0] == "r1" and rides[-1] == "r4" and rides[1:3] == ["r2", "r3"] and rides[::-1][0] == "r4"
rides.append("r5"); rides.insert(0, "r0"); last = rides.pop()
assert last == "r5" and rides == ["r0", "r1", "r2", "r3", "r4"]
rides.remove("r0")
assert len(rides) == 4 and "r2" in rides and rides.index("r3") == 2
~~~

**Names are labels, not boxes.** Assignment copies the *reference*, so two names can label one list:

~~~mermaid
flowchart LR
 a(["a"]) --> L["list object [1, 2, 3]"]
 b(["b"]) --> L
 c(["c = a.copy()"]) --> L2["new list [1, 2, 3, 4]"]
~~~

~~~python
a = [1, 2]
b = a              # alias: same list
b.append(3)
assert a == [1, 2, 3] and a is b
c = a.copy()       # new outer list
c.append(4)
assert a == [1, 2, 3] and c == [1, 2, 3, 4]
grid = [[0], [0]]
shallow = grid.copy()
shallow[0].append(1)
assert grid[0] == [0, 1]                     # inner lists are still shared!
import copy
deep = copy.deepcopy(grid); deep[0].append(2)
assert grid[0] == [0, 1]                     # deepcopy copies the inner lists too
bad = [[0] * 2] * 2; bad[0][0] = 9
assert bad == [[9, 0], [9, 0]]               # the same row twice — a classic bug
~~~

**ATLAS Go:** [`LocalStore.my_history`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) returns a *new* filtered list of the history; [`snapshot`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) uses `deepcopy` so a failed save can restore the previous state exactly.

**Lab P07** records `sys.getsizeof(list)` after each append (0 → 64 items). The chart is a staircase: Python over-allocates room, so most appends are free and a few trigger a resize — the dynamic array of the DSA course.

**Exercises.** (1) Rotate a list by k with slicing. (2) Explain the output of `bad` above and fix it with a comprehension.

## Lesson 8 — Tuples, sets and dictionaries

| Type | Literal | Ordered | Mutable | Duplicates | Typical use |
|---|---|---|---|---|---|
| `tuple` | `(51.9, -8.5)` | yes | **no** | yes | fixed records, coordinates, dict keys |
| `set` | `{"UCC", "Airport"}` | no | yes | **no** | membership, removing duplicates |
| `dict` | `{"wrap": 2}` | insertion order | yes | keys unique | look-up by key |

~~~python
point = (51.8935, -8.4920)
lat, lon = point                                  # tuple unpacking
assert lat > 51
morning, evening = {"UCC", "Kent", "Airport"}, {"Kent", "Blackrock"}
assert morning & evening == {"Kent"} and len(morning | evening) == 4 and morning - evening == {"UCC", "Airport"}
cart = {}
for item in ["wrap", "juice", "wrap"]:
    cart[item] = cart.get(item, 0) + 1           # count with dict.get
assert cart == {"wrap": 2, "juice": 1}
assert list(cart.items()) == [("wrap", 2), ("juice", 1)]
from collections import Counter, defaultdict
assert Counter(["wrap", "juice", "wrap"]).most_common(1) == [("wrap", 2)]
by_zone = defaultdict(list); by_zone["Douglas"].append("Orla")
assert by_zone == {"Douglas": ["Orla"]}
try:
    {[1, 2]: "x"}                                 # lists are unhashable: not allowed as keys
except TypeError as e:
    print(e)
~~~

**Membership** `x in s` is a scan for lists (O(n)) but a hash lookup for sets and dicts (O(1) on average) — Lab P20 measures the difference.

**ATLAS Go:** [`Cart.items`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/domain.py) is a dict from dish id to quantity; `Catalog.dishes` maps dish ids to `Dish` records; [`LocalStore.failures`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) maps an email to `[count, locked_until]` for sign-in lockout.

~~~python
import sys; sys.path.insert(0, "android-app")
from atlas_go.domain import Cart
cart = Cart()
cart.add("wrap"); cart.add("wrap"); cart.add("juice")
assert cart.items == {"wrap": 2, "juice": 1} and cart.count() == 3 and cart.subtotal() == 2 * 850 + 390
~~~

**Lab P08** counts the destinations of 500 synthetic rides with `Counter` and draws a bar chart; it also reports set union and intersection of morning and evening destinations.

**Exercises.** (1) Invert a dict `{name: zone}` into `{zone: [names]}`. (2) Find the drivers who appear in both of two shift lists.

## Lesson 9 — Comprehensions

**Idea.** A comprehension builds a collection from an iterable in one expression: `[expression for item in iterable if condition]`. Set `{…}` and dict `{k: v …}` comprehensions work the same way; nested `for` clauses read left to right like nested loops.

~~~python
squares = [x * x for x in range(6)]
evens = [x for x in squares if x % 2 == 0]
assert squares == [0, 1, 4, 9, 16, 25] and evens == [0, 4, 16]
lengths = {name: len(name) for name in ["UCC", "Kent"]}
assert lengths == {"UCC": 3, "Kent": 4}
pairs = [(r, c) for r in range(2) for c in range(3)]          # = two nested loops
assert pairs == [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)]
grid = [[r * 3 + c for c in range(3)] for r in range(2)]       # a 2×3 matrix
assert grid == [[0, 1, 2], [3, 4, 5]]
~~~

Keep comprehensions short; if you need several conditions or side effects, write a loop.

**ATLAS Go** uses them in exactly these two shapes: [`LocalStore.online_drivers`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) filters accounts with `[a for a in self.accounts if a['role'] == 'driver' and …]`, and [`geo.tile_range`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/geo.py) lists the visible map tiles with a nested comprehension `[(x % n, y) for y in range(...) for x in range(...)]`.

~~~python
import sys; sys.path.insert(0, "android-app")
from atlas_go import geo
tiles = geo.tile_range(geo.CORK, 13, 512, 256)
assert len(tiles) >= 2 and all(isinstance(t, tuple) for t in tiles)
~~~

**Lab P09** builds a 5×5 distance matrix of Cork places with one nested comprehension and the Haversine formula, asserts it is symmetric with a zero diagonal, and draws it as a heatmap.

**Exercises.** (1) Flatten `[[1, 2], [3], [4, 5]]` with a comprehension. (2) Build `{place: nearest_other_place}` from the distance matrix.

## Lesson 10 — Functions: parameters, return, scope, recursion and decorators

**Idea.** `def` packages steps under a name. **Parameters** receive **arguments**; `return` sends a result back (a function without `return` returns `None`). Variables created inside a function are **local**.

~~~python
def eta_minutes(km: float, speed_kmh: float = 30) -> int:
    """Whole minutes to travel km at speed_kmh; at least 1."""
    return max(1, round(km / speed_kmh * 60))

assert eta_minutes(15) == 30 and eta_minutes(15, speed_kmh=60) == 15 and eta_minutes(0.01) == 1
assert eta_minutes.__doc__.startswith("Whole minutes")

def total(*fares, discount=0):          # *args collects positional arguments
    return sum(fares) - discount
assert total(520, 860, discount=80) == 1300

def order(item, cart=None):             # never use a mutable default like cart=[]
    cart = [] if cart is None else cart
    cart.append(item)
    return cart
assert order("tea") == ["tea"] and order("coffee") == ["coffee"]
~~~

**Type hints** (`km: float -> int`) document intent; Python does **not** enforce them at run time (tools such as `mypy` check them).

**Recursion and caching.** A function may call itself on a smaller input; it needs a base case. A **decorator** wraps a function to add behaviour — `functools.lru_cache` remembers results.

~~~python
import functools
@functools.lru_cache(maxsize=None)
def fib(n):
    return n if n < 2 else fib(n - 1) + fib(n - 2)
assert fib(80) == 23416728348467685          # instant thanks to the cache
~~~

**ATLAS Go:** [`geo.eta_minutes(a, b)`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/geo.py) calls `haversine_km` and returns `max(1, round(...))` — the same shape as the example.

**Lab P10** counts calls of a plain recursive `fib(k)` against an `lru_cache` version for k = 1…25 (log scale): exponential versus linear.

**Exercises.** (1) Write a decorator that counts how many times a function was called. (2) Explain why `def f(x, cart=[])` keeps items between calls.

## Lesson 11 — Classes, objects and dataclasses

**Idea.** A **class** is a blueprint; an **object** (instance) is one thing built from it. Objects hold **attributes** (data) and **methods** (functions that receive the object as `self`). `__init__` sets up a new object; `__repr__` controls how it prints.

~~~mermaid
classDiagram
 class Ride {
   +float km
   +bool comfort
   +fare_cents() int
 }
 class Offer {
   +str id
   +int seats
   +reserve(party)
   +release(party)
 }
~~~

~~~python
class Account:
    def __init__(self, name, balance_cents=0):
        self.name = name
        self.balance_cents = balance_cents
    def pay(self, cents):
        if cents > self.balance_cents:
            raise ValueError("insufficient balance")
        self.balance_cents -= cents
    def __repr__(self):
        return f"Account({self.name!r}, {self.balance_cents})"

acc = Account("Student", 2000)
acc.pay(860)
assert acc.balance_cents == 1140 and repr(acc) == "Account('Student', 1140)"

from dataclasses import dataclass, field
@dataclass(order=True)
class Ride:
    km: float
    comfort: bool = False
    tags: list = field(default_factory=list, compare=False)
    def fare_cents(self) -> int:
        cents = 350 + round(self.km * 170)
        return cents * 130 // 100 if self.comfort else cents

assert Ride(3).fare_cents() == 860 and Ride(3, True).fare_cents() == 1118
assert Ride(3) == Ride(3) and Ride(2) < Ride(5)          # generated __eq__ and __lt__
print(Ride(3))                                            # Ride(km=3, comfort=False, tags=[])
~~~

`@dataclass` writes `__init__`, `__repr__` and `__eq__` for you; `frozen=True` makes instances immutable (and hashable).

**ATLAS Go:** [`intelligence.Candidate`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py) is a `@dataclass(frozen=True)` with a `features()` method; [`domain.Offer`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/domain.py) is a mutable dataclass whose `reserve` and `release` methods change `seats`:

~~~python
import sys; sys.path.insert(0, "android-app")
from atlas_go.domain import Offer
pool = Offer("pool-1", "Alex", 0, 1, capacity=3, price=490, seats=3)
pool.reserve(2)
assert pool.seats == 1 and not pool.matches(0, 1, 2)
pool.release(2)
assert pool.seats == 3
~~~

**Lab P11** plots `Ride.fare_cents()` for 1–10 km, standard and comfort, and checks the dataclass's generated comparison methods.

**Exercises.** (1) Add a `__str__` that prints "3.0 km, €8.60". (2) Make `Ride` frozen and explain why `ride.km = 4` now fails.

## Lesson 12 — Inheritance, polymorphism and composition

**Idea.** A **subclass** inherits attributes and methods from a **base class** and may **override** them. **Polymorphism**: code calls `vehicle.cost(km)` without knowing the exact class, and each class answers in its own way. `super()` calls the parent's version. The **method resolution order** (`Class.__mro__`) is the order Python searches for an attribute.

~~~mermaid
classDiagram
 Vehicle <|-- Car
 Vehicle <|-- EBike
 Car <|-- Van
 class Vehicle { +cost(km) }
 class Car { base=350 per_km=170 }
 class EBike { base=100 per_km=60 +cost(km) range check }
 class Van { per_km=220 }
~~~

~~~python
class Vehicle:
    base, per_km = 0, 0
    def cost(self, km):
        return self.base + self.per_km * km

class Car(Vehicle):
    base, per_km = 350, 170

class EBike(Vehicle):
    base, per_km = 100, 60
    def cost(self, km):
        if km > 15:
            raise ValueError("e-bike range is 15 km")
        return super().cost(km)

class Van(Car):
    per_km = 220                          # base inherited from Car

fleet = [Car(), EBike(), Van()]
assert [v.cost(2) for v in fleet] == [690, 220, 790]       # one call, three behaviours
assert [c.__name__ for c in Van.__mro__] == ["Van", "Car", "Vehicle", "object"]
assert isinstance(Van(), Vehicle) and not isinstance(EBike(), Car)
~~~

**Composition** ("has a") is often better than inheritance ("is a"): a `Ride` *has a* `Vehicle` rather than *being* one. Prefer inheritance only when the subclass really is a special kind of the base.

**ATLAS Go:** [`AtlasGoApp(App)`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/app.py) inherits from Kivy's `App` and overrides `build`, `on_start`, `on_pause` and `on_stop`, which Kivy calls polymorphically; [`LiveMap(StencilView)`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/livemap.py) overrides `on_touch_down/move/up`. `LocalStore` uses composition: it *has a* `Cart` and a `Catalog`.

**Lab P12** plots `cost(km)` for the three classes on one chart and records the MRO.

**Exercises.** (1) Add a `Taxi(Car)` with a night surcharge using `super()`. (2) Redesign with composition: `Ride(vehicle, km)`.

## Lesson 13 — Exceptions and validation

**Idea.** An **exception** signals that something went wrong. `raise` creates one; `try / except` handles the kinds you expect; `else` runs if nothing failed; `finally` always runs (cleanup). Catch **specific** exceptions; never silence everything with a bare `except:`.

~~~mermaid
flowchart TD
 T["try: risky code"] -->|no exception| E["else: success path"]
 T -->|ValueError| H["except ValueError: handle"]
 E --> F["finally: always (close, release)"]
 H --> F
~~~

~~~python
def parse_booking(record):
    if not isinstance(record, dict):
        raise TypeError("booking must be a dict")
    try:
        km = float(record["km"])
    except KeyError:
        raise KeyError("missing km") from None
    if not 0 < km <= 200:
        raise ValueError("km out of range")
    return km

results = []
for rec in ({"km": "4.5"}, {"km": "five"}, {}, [], {"km": -3}, {"km": None}):
    try:
        results.append(parse_booking(rec))
    except (ValueError, KeyError, TypeError) as exc:
        results.append(type(exc).__name__)
    finally:
        pass                                   # e.g. close a file here
assert results == [4.5, "ValueError", "KeyError", "TypeError", "ValueError", "TypeError"]

class BookingError(Exception):                 # your own exception type
    """Raised when a booking breaks a business rule."""
try:
    raise BookingError("seats exceeded")
except BookingError as e:
    assert str(e) == "seats exceeded"
~~~

**Validate at the boundary** (where data enters: forms, files, network) and let errors carry a message a user can act on.

**ATLAS Go:** [`LocalStore.validate`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) checks every field of a loaded `state.json` and raises `ValueError` on corruption; [`clean_email`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/accounts.py) raises with a friendly example; `AtlasGoApp.safe` shows those messages in a dialog instead of crashing.

~~~python
import sys; sys.path.insert(0, "android-app")
from atlas_go.store import LocalStore
try:
    LocalStore.validate({"history": "not a list"})
except ValueError as e:
    print("rejected:", e)
~~~

**Lab P13** validates 200 messy synthetic booking records and draws a bar chart of the outcomes (accepted, ValueError, TypeError, KeyError).

**Exercises.** (1) Add a `seats` check (1–3) and a test for each failure. (2) When is it right to re-raise an exception?

## Lesson 14 — Files, pathlib, JSON, CSV and atomic writes

**Idea.** Files keep data after the program ends. `pathlib.Path` builds paths portably; `with open(...)` closes the file automatically; **JSON** stores nested dicts/lists/strings/numbers/booleans/null as text; **CSV** stores tables (everything comes back as strings).

~~~python
import csv, json, tempfile
from pathlib import Path

folder = Path(tempfile.mkdtemp())
rides = [{"id": 1, "destination": "Kent Station", "km": 5}, {"id": 2, "destination": "UCC", "km": 3}]

(folder / "rides.json").write_text(json.dumps(rides, indent=2), encoding="utf-8")
assert json.loads((folder / "rides.json").read_text(encoding="utf-8")) == rides

with (folder / "rides.csv").open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["id", "destination", "km"])
    writer.writeheader(); writer.writerows(rides)
with (folder / "rides.csv").open(encoding="utf-8") as f:
    back = list(csv.DictReader(f))
assert back[0]["km"] == "5"                      # CSV gives strings: convert yourself
print(sorted(p.name for p in folder.iterdir()))  # ['rides.csv', 'rides.json']
~~~

**Atomic writes.** If the app crashes half-way through writing `state.json`, the file is corrupt. Write to a temporary file first, flush it to disk, then **rename** it over the old file — a rename on one file system is all-or-nothing.

~~~mermaid
sequenceDiagram
 participant App
 participant Tmp as state.tmp
 participant Real as state.json
 App->>Tmp: write full JSON, flush, fsync
 Note over App,Tmp: crash here → state.json still holds the old, valid data
 App->>Real: Tmp.replace(Real)  (atomic rename)
~~~

**ATLAS Go:** [`LocalStore.save`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) does exactly this (`temporary.open('w')`, `json.dump`, `flush`, `os.fsync`, `temporary.replace(self.path)`), and [`commit`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) restores the in-memory snapshot if saving raises `OSError`.

~~~python
import sys, tempfile, json; sys.path.insert(0, "android-app")
from pathlib import Path
from atlas_go.store import LocalStore
path = Path(tempfile.mkdtemp()) / "state.json"
store = LocalStore(path)
store.reset(save=True)
saved = json.loads(path.read_text(encoding="utf-8"))
assert saved["history"] == [] and saved["seats"]["pool-1"] == 3
assert LocalStore(path).cart.items == store.cart.items          # a fresh store reloads the same state
~~~

**Lab P14** writes 10 → 5 000 rides as JSON and CSV, plots the file sizes, and simulates a crash during an atomic write to show that the previous file survives.

**Exercises.** (1) Add a `version` field to saved state and migrate old files. (2) What does `encoding="utf-8"` protect you from on Windows?

## Lesson 15 — Iterators and generators

**Idea.** An **iterable** can be looped over; an **iterator** produces the next item on each `next()` call and raises `StopIteration` at the end. A **generator function** uses `yield` to produce values **lazily**, one at a time, keeping its place between calls. A generator expression `(x*x for x in data)` is the lazy version of a list comprehension.

~~~python
def countdown(n):
    while n > 0:
        yield n                        # pause here, hand n to the caller
        n -= 1

it = countdown(3)
assert next(it) == 3 and next(it) == 2 and list(it) == [1]      # list() drains the rest

def readings(lines):                    # a lazy pipeline: nothing runs until consumed
    for line in lines:
        line = line.strip()
        if line and not line.startswith("#"):
            yield float(line)

data = ["# speeds", "31.5", "", "28.0", "35.5"]
assert sum(readings(data)) == 95.0
squares = (x * x for x in range(10**6))     # no million-item list is built
assert next(squares) == 0

class Shift:                                 # the iterator protocol by hand
    def __init__(self, drivers): self.drivers, self.i = drivers, 0
    def __iter__(self): return self
    def __next__(self):
        if self.i == len(self.drivers): raise StopIteration
        self.i += 1
        return self.drivers[self.i - 1]
assert list(Shift(["Ava", "Sam"])) == ["Ava", "Sam"]
~~~

**ATLAS Go:** [`LiveMap.visible_tiles`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/livemap.py) returns a *list* of tiles (from `geo.tile_range`); turning it into a generator is a good exercise when the map is very large.

**Lab P15** measures peak memory (`tracemalloc`) of a list pipeline versus a generator pipeline for n up to 100 000: the list version grows linearly, the generator version stays flat.

**Exercises.** (1) Write `chunks(items, size)` that yields lists of `size` items. (2) Use `itertools.islice` to take the first 5 values of an infinite generator.

## Lesson 16 — Lambda, map, filter, reduce and key functions

**Idea.** Functions are values: you can pass them to other functions (**higher-order** functions). `lambda args: expression` creates a small unnamed function. `map(f, xs)` applies f to each item; `filter(pred, xs)` keeps items where pred is true; `functools.reduce` folds a sequence into one value. `sorted`, `min` and `max` accept `key=` to say *what* to compare.

~~~python
from functools import reduce
drivers = [{"name": "Ava", "km": 2.0, "rating": 4.9, "online": True},
           {"name": "Sam", "km": 0.5, "rating": 4.2, "online": True},
           {"name": "Leah", "km": 1.0, "rating": 4.7, "online": False}]
online = list(filter(lambda d: d["online"], drivers))
names = list(map(lambda d: d["name"], online))
assert names == ["Ava", "Sam"]
assert min(online, key=lambda d: d["km"])["name"] == "Sam"                 # nearest
assert sorted(online, key=lambda d: (-d["rating"], d["km"]))[0]["name"] == "Ava"   # best rated
assert reduce(lambda total, d: total + d["km"], drivers, 0) == 3.5
assert [d["name"] for d in drivers if d["online"]] == names              # comprehension equivalent
~~~

Comprehensions are usually clearer than `map`/`filter` with a lambda; the `key=` parameter is where lambdas shine.

**ATLAS Go:** [`intelligence.rank`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py) ends with `sorted(..., key=lambda x: -x[1])` to put the most probable driver first, and [`choose`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py) finds the nearest driver with `min(..., key=lambda c: (c.eta, -c.accept))`.

~~~python
import sys; sys.path.insert(0, "android-app")
from atlas_go import intelligence
ranked = intelligence.rank(0)                          # candidates near UCC Campus
probabilities = [p for _, p in ranked]
assert probabilities == sorted(probabilities, reverse=True) and abs(sum(probabilities) - 1) < 1e-9
print([c.name for c, _ in ranked])
~~~

**Lab P16** runs `filter → map → sorted(key=…)` over 40 synthetic drivers and charts the top eight by score.

**Exercises.** (1) Sort by rating descending, then distance ascending, using one key tuple. (2) Rewrite the pipeline with comprehensions and compare readability.

## Lesson 17 — Sorting, selection and pipelines

**Idea.** `sorted(xs)` returns a new list; `xs.sort()` sorts in place and returns `None`. Python's sort (Timsort) is **stable**: equal keys keep their original order, so you can sort by a secondary key first and the primary key second. For "the best k of n", `heapq.nsmallest/nlargest` avoid sorting everything.

~~~python
import heapq
rides = [("Kent", 5), ("UCC", 3), ("Airport", 8), ("City", 3)]
assert sorted(rides, key=lambda r: r[1]) == [("UCC", 3), ("City", 3), ("Kent", 5), ("Airport", 8)]  # stable
by_two_keys = sorted(sorted(rides, key=lambda r: r[0]), key=lambda r: r[1])   # name, then km
assert by_two_keys[:2] == [("City", 3), ("UCC", 3)]
assert heapq.nsmallest(2, rides, key=lambda r: r[1]) == [("UCC", 3), ("City", 3)]
result = rides.sort(key=lambda r: r[1])
assert result is None                                     # .sort() works in place
~~~

A **pipeline** chains small steps: *filter* eligible records → *compute* a feature → *rank* → *select*. Each step is easy to test on its own.

**ATLAS Go:** [`intelligence.choose`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py) is such a pipeline: `rank` filters and scores candidates, then `choose` takes `ranked[0]` and separately finds the nearest driver to explain the choice. Ranking candidates is **not** route-finding — no road network is searched.

**Lab P17** counts comparisons (with a wrapper class whose `__lt__` increments a counter) for `sorted(data)[:5]` versus `heapq.nsmallest(5, data)`, n up to 50 000.

**Exercises.** (1) Prove `sorted` is stable with an example of your own. (2) Return the three nearest online drivers using `heapq`.

## Lesson 18 — Complexity and searching

**Idea.** **Time complexity** describes how the number of basic steps grows with the input size n, ignoring constant factors: O(1) constant, O(log n) halving, O(n) one pass, O(n log n) good sorting, O(n²) all pairs. It is about **growth**, not seconds.

| Operation | list | set / dict |
|---|---|---|
| `x in container` | O(n) scan | O(1) average |
| index `a[i]` | O(1) | — |
| append | O(1) amortised | add O(1) average |
| insert at front | O(n) | — |
| sort | O(n log n) | — |

**Linear vs binary search.** Linear search checks every item (works on anything); binary search halves a **sorted** range each step (log₂ n steps).

~~~python
import bisect
a = list(range(0, 1000, 2))            # sorted even numbers
def linear(a, x):
    for i, v in enumerate(a):
        if v == x:
            return i
    return -1
def binary(a, x):
    lo, hi = 0, len(a) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if a[mid] == x: return mid
        lo, hi = (mid + 1, hi) if a[mid] < x else (lo, mid - 1)
    return -1
assert linear(a, 998) == binary(a, 998) == 499 and binary(a, 7) == -1
i = bisect.bisect_left(a, 500)
assert a[i] == 500                     # standard-library binary search
~~~

**ATLAS Go:** [`LocalStore.online_drivers`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) scans all accounts — O(n), fine for one phone's few accounts; a city-wide server would index drivers by zone in a dict.

**Lab P18** counts comparisons for linear and binary search of an absent key for n = 8 … 32 768 (log scale). See the [DSA course](DATA_STRUCTURES_ALGORITHMS.md) for the full theory.

**Exercises.** (1) How many comparisons does binary search need for one million items? (2) Find the first index of a duplicated value with binary search.

## Lesson 19 — Testing, assertions and debugging

**Idea.** A **test** runs code with chosen inputs and compares the result with the expected answer (the **oracle**). `assert condition, message` stops the program if the condition is false. `unittest` (built in) and `pytest` organise many tests. Choose inputs at the **edges**: empty, zero, one, maximum, just over the maximum, wrong type.

~~~python
import unittest, io

def fare_cents(km: int, comfort: bool = False) -> int:
    if km <= 0:
        raise ValueError("distance must be positive")
    cents = 350 + 170 * km
    return cents * 130 // 100 if comfort else cents

class FareTests(unittest.TestCase):
    def test_typical(self):
        self.assertEqual(fare_cents(3), 860)
    def test_boundary_one_km(self):
        self.assertEqual(fare_cents(1), 520)
    def test_comfort(self):
        self.assertEqual(fare_cents(3, comfort=True), 1118)
    def test_zero_rejected(self):
        with self.assertRaises(ValueError):
            fare_cents(0)

run = unittest.TextTestRunner(stream=io.StringIO()).run(
    unittest.defaultTestLoader.loadTestsFromTestCase(FareTests))
assert run.wasSuccessful() and run.testsRun == 4
~~~

**Mutation testing** asks: *would my tests notice a bug?* Change the code slightly (a *mutant*: `<=` → `<`, 170 → 171) and rerun; a good suite fails (**kills** the mutant).

**Debugging:** read the traceback bottom-up; reproduce with the smallest input; print or log intermediate values; use `breakpoint()` (pdb) to step through; fix, then add a test so the bug cannot return.

**ATLAS Go:** [`intelligence.self_test`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py) runs named checks on the phone (dispatch, acceptance model, surge, courier timing, learning lab) and reports pass/fail for each.

~~~python
import sys; sys.path.insert(0, "android-app")
from atlas_go import intelligence
checks = intelligence.self_test(lab_episodes=200)
for name, ok, detail in checks:
    print("PASS" if ok else "FAIL", name)
~~~

**Lab P19** builds six mutants of `fare_cents` and runs a weak suite (1 test) and a strong suite (5 tests) against each: the weak suite kills 4 of 6, the strong suite all 6. Part II teaches testing in depth.

**Exercises.** (1) Write the test that kills the `<=` → `<` mutant. (2) Add a test for `fare_cents(-1)`.

## Lesson 20 — Profiling, modules, packages and project structure

**Idea.** Measure before optimising. `timeit` repeats a small statement many times and reports the best; `cProfile` shows which functions use the time; `tracemalloc` shows memory. Report the machine, Python version, repeat count and spread — never a single timing.

~~~python
import timeit, cProfile, pstats, io
setup_list, setup_set = list(range(100_000)), set(range(100_000))
t_list = min(timeit.repeat(lambda: 99_999 in setup_list, number=100, repeat=5))
t_set = min(timeit.repeat(lambda: 99_999 in setup_set, number=100, repeat=5))
print(f"list: {t_list/100*1e6:.1f} µs  set: {t_set/100*1e6:.3f} µs")
assert t_set < t_list

profile = cProfile.Profile()
profile.enable(); sorted(range(100_000), key=lambda x: -x); profile.disable()
report = io.StringIO()
pstats.Stats(profile, stream=report).sort_stats("cumulative").print_stats(3)
print(report.getvalue()[:400])
~~~

Once a program outgrows one file, five habits keep it easy to read, test and change: **(1)** split it into modules and packages, **(2)** import in a fixed order, **(3)** choose the right form of `import`, **(4)** keep each class in its own file, and **(5)** group similar functions together.

**1. Modules and packages.** A **module** is one Python file (`module1.py`). A **package** is a folder of modules with an `__init__.py` file (`physics/`). `import physics` runs `physics/__init__.py` once and gives you whatever that file defines or imports; `import physics.module1` loads one module from the folder. The program you *run* (`main.py`) sits **next to** the package folder, not inside it.

~~~text
project/
├── main.py              ← run this:  python main.py   (it does  import physics)
└── physics/             ← package = folder (its name is what you import)
    ├── __init__.py      ← runs on  import physics ; chooses what physics.<name> offers
    ├── module1.py       ← module = file: motion  (speed, distance)
    ├── module2.py       ← module = file: energy  (kinetic_energy)
    └── particle.py      ← one class in its own file (habit 4): class Particle
~~~

The block below writes exactly these files into a temporary folder and runs `main.py` with a fresh Python, so you see real imports — then shows what goes wrong if `main.py` is put *inside* the package.

~~~python
import subprocess, sys, tempfile, textwrap
from pathlib import Path

files = {
    "physics/__init__.py": '''
        """physics: motion and energy formulas."""
        from .module1 import distance, speed      # re-export, so main.py can write physics.speed(...)
        from .module2 import kinetic_energy
        __all__ = ["distance", "kinetic_energy", "speed"]
    ''',
    "physics/module1.py": '''
        """Motion: functions about distance and time, grouped together."""
        def speed(distance_m, time_s):
            return distance_m / time_s

        def distance(speed_ms, time_s):
            return speed_ms * time_s
    ''',
    "physics/module2.py": '''
        """Energy."""
        def kinetic_energy(mass_kg, speed_ms):
            return 0.5 * mass_kg * speed_ms ** 2
    ''',
    "physics/particle.py": '''
        """One class per file: Particle lives in particle.py."""
        from .module1 import speed
        from .module2 import kinetic_energy

        class Particle:
            def __init__(self, mass_kg):
                self.mass_kg = mass_kg

            def energy_after(self, distance_m, time_s):
                return kinetic_energy(self.mass_kg, speed(distance_m, time_s))
    ''',
    "main.py": '''
        import physics                          # the folder name; runs physics/__init__.py
        from physics import module2             # one module of the package
        from physics.particle import Particle   # one class from one module

        v = physics.speed(100, 9.58)
        print(f"{v:.2f}", round(module2.kinetic_energy(94, v)), round(Particle(94).energy_after(100, 9.58)))
    ''',
}

with tempfile.TemporaryDirectory() as root:
    for name, body in files.items():
        path = Path(root, name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(body).lstrip())

    run = subprocess.run([sys.executable, "main.py"], cwd=root, capture_output=True, text=True)
    print(run.stdout.strip())                         # 10.44 5121 5121
    assert run.stdout.split() == ["10.44", "5121", "5121"]

    # Mistake: main.py inside the package. Python adds the *script's own folder* (physics/)
    # to the search path, so it cannot see a folder called physics.
    Path(root, "physics", "main.py").write_text("import physics\nprint(physics.speed(10, 2))\n")
    inside = subprocess.run([sys.executable, "physics/main.py"], cwd=root, capture_output=True, text=True)
    assert "No module named 'physics'" in inside.stderr

    # Fix (if it must live inside): run it as a module from the project folder.
    as_module = subprocess.run([sys.executable, "-m", "physics.main"], cwd=root, capture_output=True, text=True)
    assert as_module.stdout.strip() == "5.0"
~~~

Never name your own files `json.py`, `random.py`, `math.py` or `time.py`: they would hide the standard-library module of the same name. Guard script code with `if __name__ == "__main__":` so that importing a module does not run it.

**2. Import order.** Put all imports at the top of the file, in three groups separated by one blank line (the [PEP 8](https://peps.python.org/pep-0008/#imports) convention):

1. **standard library** — modules that ship with Python (`json`, `math`, `pathlib`);
2. **third-party libraries** — installed with `pip` (`numpy`, `kivy`, `fastapi`);
3. **local application** — your own project's modules and packages (`physics`, `.store`).

Inside each group, list plain `import x` lines first, then the specific `from x import name` lines, alphabetically. `from __future__ import …` always comes first of all.

~~~text
from __future__ import annotations          # 0. always first, if used

import json                                 # 1. standard library
import math
from pathlib import Path

import numpy as np                          # 2. third-party (pip install numpy)
from kivy.clock import Clock                #    specific names from a third-party library

import physics                              # 3. local application
from physics.particle import Particle       #    specific names from your own package
~~~

The reader sees at a glance what the file needs from Python, from outside and from your own code. Tools sort imports for you: `ruff check --select I --fix .` or `isort .`. The block below classifies every import in ATLAS Go and checks the order holds in all of its modules:

~~~python
import re, sys
from pathlib import Path

def import_groups(path):
    """Group of each top-level import: 0 __future__, 1 standard library, 2 third-party, 3 local."""
    groups = []
    for line in Path(path).read_text().splitlines():
        match = re.match(r"from ([\w.]+) import |import ([\w.]+)", line)
        if match:
            name = match.group(1) or match.group(2)
            if name == "__future__":
                groups.append(0)
            elif name.startswith("."):
                groups.append(3)
            elif name.split(".")[0] in sys.stdlib_module_names:
                groups.append(1)
            else:
                groups.append(2)
    return groups

print(import_groups("android-app/atlas_go/livemap.py"))   # [0, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3]
for module in sorted(Path("android-app/atlas_go").glob("*.py")):
    groups = import_groups(module)
    assert groups == sorted(groups), f"{module.name}: imports out of order"
~~~

**3. How to import.** Suppose `module5.py` contains one function, `def sum(a, b)`. There are two main ways to use it, and two ways to rename on import:

| Form | Then write | Use it when |
|---|---|---|
| `import module5` | `module5.sum(2, 3)` | default — the reader sees where `sum` comes from |
| `from module5 import sum` | `sum(2, 3)` | you use one name often — but see the mistake below |
| `from module5 import sum as add` | `add(2, 3)` | the name clashes with another one |
| `import module5 as m5` | `m5.sum(2, 3)` | the module name is long (`import numpy as np`) |

Avoid `from module5 import *`: it pulls in every public name silently and hides where they came from.

~~~python
import sys, tempfile
from pathlib import Path

folder = tempfile.mkdtemp()
Path(folder, "module5.py").write_text('def sum(a, b):\n    """Add two numbers."""\n    return a + b\n')
sys.path.insert(0, folder)              # let Python find module5.py (a real project does not need this)

import module5                          # form 1: the module, used as module5.sum
assert module5.sum(2, 3) == 5
assert sum([1, 2, 3]) == 6              # Python's built-in sum is untouched

from module5 import sum                 # form 2: the name itself
assert sum(2, 3) == 5                   # 'sum' now means module5.sum ...
try:
    sum([1, 2, 3])                      # ... so the built-in sum is hidden ("shadowed")
except TypeError as error:
    print("shadowed:", error)
del sum                                 # remove our name: the built-in is visible again
assert sum([1, 2, 3]) == 6

from module5 import sum as add          # form 3: rename on import — the safe choice here
import module5 as m5                    # form 4: shorter module name
assert add(2, 3) == m5.sum(2, 3) == 5
~~~

Better still, do not name your own function `sum`, `list`, `id` or `max`: call it `add` or `total` and the clash never happens.

**4. Keep one class in a separate file.** Give each substantial class its own module, named after the class in lower case: `class Particle` → `particle.py`, `class LocalStore` → `store.py`. You can find any class from the file list; a change to one class touches one file; and its tests live in a matching `test_particle.py`. The exception is a few *small* classes that only make sense together, such as the dataclasses of one data model: they may share a file.

**5. Group similar functions together.** Put functions that work on the same kind of data, or serve the same purpose, in the same module, side by side: motion formulas in `module1.py`, energy formulas in `module2.py`. Inside a file, keep related functions next to each other. A catch-all `utils.py` of unrelated helpers is the opposite: nobody knows what is in it.

~~~python
import inspect, sys
sys.path.insert(0, "android-app")
from atlas_go import accounts, geo

def own_functions(module):
    """Functions defined in this module (not imported into it), in source order."""
    found = [f for _, f in inspect.getmembers(module, inspect.isfunction) if f.__module__ == module.__name__]
    return [f.__name__ for f in sorted(found, key=lambda f: f.__code__.co_firstlineno)]

print(own_functions(geo)[:6])      # ['haversine_km', 'eta_minutes', 'leg_seconds', 'lerp', 'nearest_place', 'valid_point']
assert {"haversine_km", "eta_minutes", "tile_range", "ride_position"} <= set(own_functions(geo))
assert all(name.startswith(("hash_", "verify_", "clean_", "check_", "parse_", "public_"))
           for name in own_functions(accounts))       # every accounts function hashes, checks or cleans account data
~~~

**Common mistakes.** Running a script from inside its own package (`python physics/main.py`) — run `python main.py` from the project folder, or `python -m physics.main`. Forgetting `__init__.py`, or forgetting to import a module in it and then expecting `physics.module1` to exist after `import physics`. `from module import sum` hiding the built-in `sum`. Mixing the three import groups, or importing in the middle of a file. A 2 000-line file holding every class. A `utils.py` that collects unrelated functions. Two modules that import each other (a **circular import**): move the shared part into a third module.

~~~text
android-app/                 # not importable by name (hyphen) → add it to sys.path
└── atlas_go/                # package
    ├── __init__.py          # package docstring and __version__
    ├── domain.py            # pure rules: five small food-ordering dataclasses kept together
    ├── store.py             # one class: LocalStore (persistence + rules)
    ├── location.py          # one class: DeviceLocation
    ├── geo.py               # 15 related geography functions, no classes
    ├── accounts.py          # 12 related account functions: hash, verify, clean, parse
    ├── intelligence.py      # learned policies
    └── app.py               # Kivy UI (needs a display)
python_lab/experiments.py    # this course's labs: argparse CLI + importable functions
~~~

**ATLAS Go:** [`intelligence.LearningLab`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py) trains and evaluates a dispatch policy on the phone and reports results; it is organised as a class with `reset`, `train` and `result` methods. The pure modules (`domain`, `geo`, `intelligence`) import without Kivy, which is why the examples in this guide can use them. The five habits in the real app:
- **Packages:** `atlas_go/` is the package; [`store.py`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py#L7-L15) imports its neighbours with relative imports (`from . import geo`, `from .domain import Cart, …`).
- **Import order:** [`livemap.py` lines 8–29](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/livemap.py#L8-L29) is the textbook layout — `__future__`, then eight standard-library imports, a blank line, eight `kivy` imports, a blank line, two local imports.
- **One class per file:** [`LocalStore`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py#L30) in `store.py`, [`DeviceLocation`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/location.py#L13) in `location.py`, [`Acceptance`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/acceptance.py#L19) in `acceptance.py`. The allowed exception: [`domain.py`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/domain.py#L24-L116) keeps the five small dataclasses `Dish`, `Offer`, `Kitchen`, `Catalog` and `Cart` together because they form one model.
- **Similar functions together:** [`geo.py`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/geo.py) holds only geography — distances and times, then map pixels and tiles, then ride and order positions; [`accounts.py`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/accounts.py#L27-L124) holds only account data — password hashing first, then the field validators.

**Lab P20** times `x in list` and `x in set` with `timeit` for n = 100 … 100 000 (log scale).

**Exercises.** (1) Profile `intelligence.rank` 10 000 times and find the slowest function. (2) Turn your capstone into a package with a CLI entry point. (3) Add `physics/module3.py` with `momentum(mass_kg, speed_ms)`, re-export it from `__init__.py`, and call `physics.momentum(94, 10.44)` from `main.py`. (4) Rename `module5.sum` to `add` and rewrite the four import forms. (5) Shuffle the imports of a copy of `livemap.py`, run `import_groups` to see the order break, then fix it with `ruff check --select I --fix`. (6) `app.py` holds six classes: decide which of them would be easier to find and test in their own files, and sketch the new file list.

## Capstone (Part I)

Build a *local, synthetic* ride-dispatch simulator: a `Ride` dataclass; a dict of drivers; filtering of online drivers; Haversine distances; ranking with `sorted(key=…)`; validation with exceptions; atomic JSON save/load; and at least ten tests. Explain in writing how it differs from the real ATLAS Go classes in the [UML blueprint](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/docs/UML_BLUEPRINT.md#android-app-atlas-go). Do not use real people's data.

**Assessment:** explain concepts and predict output 20 · correct programs with edge cases 25 · reproducible labs and tests 20 · interpret charts and units 20 · trace ideas to the real ATLAS Go code 15.

---

# Part II — Software testing fundamentals with ATLAS Go

**Purpose:** learn to produce *evidence* that code behaves as specified. The tests below run against **real ATLAS Go functions** where possible (`domain.fare`, `Offer`, `LocalStore`) and against small teaching services otherwise; none of them touches a payment provider, a live map or a production backend. Prerequisite: Lessons 1–19.

Every test file below begins with this bootstrap, because the folder `android-app` contains a hyphen and is not an importable package name:

~~~python
# file: testing_lab/conftest.py
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]          # repository root
sys.path.insert(0, str(ROOT / "android-app"))
sys.path.insert(0, str(ROOT / "testing_lab"))
~~~

Create the folder `testing_lab/` in your checkout, save each block that starts with `# file:` under that name, and run `python -m pytest -q testing_lab` from the repository root. (In Colab: `!mkdir -p testing_lab`, then `%%writefile testing_lab/test_x.py` at the top of a cell, then `!python -m pytest -q testing_lab`.)

## T01 — What is software testing?

A **requirement** says what should happen; a **test case** is an input plus an **oracle** (the expected result); a **test suite** groups cases; a **runner** executes them; a **defect** is a difference between required and actual behaviour; a **regression** is something that used to work and broke after a change.

| Level / practice | What is checked | ATLAS Go example |
|---|---|---|
| Static checks | code without running it | `pyflakes`, `mypy`, formatting |
| Unit | one function or class | `domain.fare`, `Offer.reserve` |
| Component | one module with its collaborators | `Cart` + `Catalog` |
| Integration | real components together | `LocalStore` + the JSON file |
| Contract / API | agreed request/response schema | the teaching FastAPI quote service (T08) |
| System / end-to-end | a whole user journey | sign in → request ride → see history |
| Acceptance | business requirements | a shared ride never overbooks seats |
| Smoke | a quick check after a build | app imports; one fare computes |
| Regression | old behaviour after changes | food ordering still works after a ride change |
| Security | misuse and abuse | invalid input, access control, secrets |
| Performance | latency, throughput, memory | ranking 10 000 synthetic candidates |
| Accessibility / usability | people can use it | labels, contrast, touch targets |

~~~mermaid
flowchart BT
 U["many fast unit tests"] --> I["fewer integration tests"] --> E["few slow end-to-end tests"]
~~~

Testing can show the presence of defects, never their absence: a passing test only covers the inputs and assertions it contains.

## T02 — Test design: how to choose inputs

For a shared ride with **capacity 3**, the valid party sizes are 1–3. Test the **boundaries** 0, 1, 3, 4, not just 2.

- **Equivalence partitioning:** one representative per class of inputs (valid, too small, too large, wrong type).
- **Boundary-value analysis:** just below, on, and just above each limit.
- **Decision tables:** every combination of conditions (Lesson 4).
- **State-transition testing:** available → reserved → released; illegal transitions rejected.
- **Pairwise testing:** cover every pair of parameter values without every full combination.
- **White-box:** exercise each branch you can see in the source. **Black-box:** derive expectations from the requirement.
- **Risk-based:** test money, authentication, privacy and booking correctness first.

Write each test as **Arrange → Act → Assert** and name it after the behaviour: `test_reserve_rejects_more_seats_than_available`, not `test_1`.

## T03 — A first test with no installation (`unittest`)

~~~python
import unittest, io

def total_cents(unit_cents: int, quantity: int) -> int:
    if unit_cents < 0 or quantity < 0:
        raise ValueError("Negative inputs are invalid")
    return unit_cents * quantity

class TestTotal(unittest.TestCase):
    def test_normal(self):
        self.assertEqual(total_cents(250, 3), 750)
    def test_zero(self):
        self.assertEqual(total_cents(250, 0), 0)
    def test_invalid(self):
        with self.assertRaises(ValueError):
            total_cents(250, -1)

result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=2).run(
    unittest.defaultTestLoader.loadTestsFromTestCase(TestTotal))
assert result.testsRun == 3 and result.wasSuccessful()
~~~

From a terminal, `python -m pip install pytest pytest-cov hypothesis` gives the tools used in T04–T15.

## T04 — Unit tests with pytest: fares (Experiment 1)

~~~python
# file: testing_lab/test_domain.py
import pytest
from atlas_go.domain import fare, distance

@pytest.mark.parametrize("pickup,destination,expected", [
    (0, 1, 860),    # UCC -> City Centre: 350 + 3*170
    (0, 2, 1200),   # UCC -> Kent Station: 350 + 5*170
    (2, 3, 2050),   # Kent Station -> Airport: 350 + 10*170
])
def test_standard_fare(pickup, destination, expected):
    assert fare(pickup, destination) == expected

def test_comfort_is_30_percent_more():
    assert fare(0, 1, comfort=True) == 860 * 130 // 100 == 1118

@pytest.mark.parametrize("pickup,destination", [(0, 0), (-1, 1), (0, 4)])
def test_invalid_routes_rejected(pickup, destination):
    with pytest.raises(ValueError):
        distance(pickup, destination)
~~~

**Oracle:** 860, 1200 and 2050 cents come from the fare formula and the distance table in `domain.py`. Integer cents avoid floating-point comparisons.

## T05 — Testing a class with state (Experiment 2)

~~~python
# file: testing_lab/test_offer.py
import pytest
from atlas_go.domain import Offer

def test_reserve_and_release():
    offer = Offer("demo", "Driver A", 0, 1, capacity=3, price=500, seats=3)
    assert offer.matches(0, 1, 2)
    offer.reserve(2)
    assert offer.seats == 1
    with pytest.raises(ValueError):
        offer.reserve(2)
    assert offer.seats == 1                  # a failed attempt must not change state
    offer.release(2)
    assert offer.seats == 3

@pytest.mark.parametrize("party", [0, 4, -1])
def test_reserve_rejects_out_of_range(party):
    offer = Offer("demo", "Driver A", 0, 1, capacity=3, price=500, seats=3)
    with pytest.raises(ValueError):
        offer.reserve(party)
    assert offer.seats == 3

def test_release_never_exceeds_capacity():
    offer = Offer("demo", "Driver A", 0, 1, capacity=3, price=500, seats=3)
    offer.release(2)                         # double release is clamped
    assert offer.seats == 3
~~~

Check the state **after** an error as carefully as the error itself.

## T06 — Test doubles: stubs, fakes, mocks, spies (Experiment 3)

A **stub** returns canned answers; a **fake** is a simplified working implementation (an in-memory repository); a **mock** verifies how it was called; a **spy** records calls for later checks. Use them to isolate code from clocks, networks, GPS or payments — and test the real integration separately.

~~~python
# file: testing_lab/test_doubles.py
from unittest.mock import Mock

def notify_pickup(sender, ride_id):
    sender.send(ride_id, "Driver assigned")

def eta_text(clock, pickup_at):
    minutes = max(0, round((pickup_at - clock()) / 60))
    return f"{minutes} min"

def test_notification_sent_once():
    sender = Mock()
    notify_pickup(sender, "ride-7")
    sender.send.assert_called_once_with("ride-7", "Driver assigned")

def test_eta_with_a_stub_clock():
    assert eta_text(lambda: 1000.0, pickup_at=1300.0) == "5 min"
~~~

The notifier is a teaching abstraction, **not** an ATLAS Go service. Mock the dependencies, never the function under test.

## T07 — Integration test with an isolated file (Experiment 4)

`LocalStore` persists to a JSON file. pytest's `tmp_path` fixture gives each test a fresh folder, so real user data is never touched.

~~~python
# file: testing_lab/test_store.py
import json
from atlas_go.store import LocalStore

def test_reset_writes_valid_state(tmp_path):
    path = tmp_path / "state.json"
    LocalStore(path).reset(save=True)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["history"] == [] and data["seats"]["pool-1"] == 3

def test_state_survives_a_restart(tmp_path):
    path = tmp_path / "state.json"
    first = LocalStore(path)
    first.reset(save=True)
    second = LocalStore(path)                       # a fresh object reads the file
    assert second.cart.items == first.cart.items
    assert [o.seats for o in second.offers] == [o.seats for o in first.offers]
    assert second.history == first.history
~~~

Compare **data**, not whole objects: `Cart` defines no `__eq__`, so `second.snapshot() == first.snapshot()` is False even when the state is identical (the previous version of this course made that mistake). ATLAS Go uses JSON, not SQL — the [Web Technology course](WEB_TECHNOLOGY.md) covers database integration tests.

## T08 — API contract tests with FastAPI (Experiment 5; teaching service)

ATLAS Go is local-first and exposes no `/quote` endpoint; this small FastAPI service is a teaching extension (`pip install fastapi httpx`).

~~~python
# file: testing_lab/quote_api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class Quote(BaseModel):
    km: float

@app.post("/quote")
def quote(body: Quote):
    if not 0 < body.km <= 100:
        raise HTTPException(status_code=422, detail="Distance out of range")
    return {"fare_cents": 350 + round(body.km * 170)}
~~~

~~~python
# file: testing_lab/test_quote_api.py
from fastapi.testclient import TestClient
from quote_api import app

client = TestClient(app)

def test_quote_contract():
    response = client.post("/quote", json={"km": 3})
    assert response.status_code == 200
    assert response.json() == {"fare_cents": 860}

def test_quote_rejects_bad_input():
    assert client.post("/quote", json={"km": -1}).status_code == 422
    assert client.post("/quote", json={"km": "far"}).status_code == 422
    assert client.post("/quote", json={}).status_code == 422
~~~

`TestClient` calls the app in-process; it does not test the real network.

## T09 — Property-based and metamorphic tests (Experiment 6)

A **property** must hold for *every* valid input; Hypothesis generates hundreds of inputs and shrinks any failure to the smallest example. A **metamorphic** test checks a relationship between outputs when the exact output is hard to know.

~~~python
# file: testing_lab/test_properties.py
from hypothesis import given, strategies as st
from atlas_go.domain import fare, distance

places = st.integers(min_value=0, max_value=3)

@given(pickup=places, destination=places)
def test_comfort_never_cheaper(pickup, destination):
    if pickup != destination:
        assert fare(pickup, destination, comfort=True) >= fare(pickup, destination)

@given(pickup=places, destination=places)
def test_distance_is_symmetric(pickup, destination):        # metamorphic relation
    if pickup != destination:
        assert distance(pickup, destination) == distance(destination, pickup)
~~~

## T10 — Coverage and mutation testing (Experiment 7)

~~~bash
python -m pytest -q testing_lab --cov=atlas_go --cov-branch --cov-report=term-missing
~~~

**Coverage** = executed lines (or branches) ÷ measured lines × 100. 90 % coverage does **not** mean 90 % correct: a line can run without its result being checked. **Mutation testing** measures checking: change `if not 1 <= party <= self.seats` in a *local copy* of `Offer.reserve` to `1 < party`, rerun — `test_reserve_and_release` should now fail. Lab P19 automates this idea.

## T11 — Test-driven development and debugging (Experiment 8)

**Red → Green → Refactor:** write a failing test, write the least code to pass it, then improve the code with the tests green.

~~~python
# file: testing_lab/test_discount.py
import pytest

def discount(total_cents, coupon_cents):          # written AFTER the tests below failed
    if total_cents < 0 or coupon_cents < 0:
        raise ValueError("Negative money")
    return max(0, total_cents - coupon_cents)

def test_discount_caps_at_zero():
    assert discount(100, 200) == 0

def test_discount_rejects_negative():
    with pytest.raises(ValueError):
        discount(-1, 0)
~~~

To see *red*, delete the function and run the tests: `NameError`. This is a teaching helper, not an ATLAS Go feature.

## T12 — Security and robustness tests (Experiment 9)

Categories: input validation, authentication, authorisation, session expiry, rate limiting, secret redaction, unsafe deserialisation, injection, dependency auditing, privacy. Use synthetic fixtures only.

~~~python
# file: testing_lab/test_parse.py
import json
import pytest

def parse_request(raw):
    data = json.loads(raw)
    seats = data.get("seats") if isinstance(data, dict) else None
    if type(seats) is not int:                      # rejects True/False too (bool is an int subclass)
        raise ValueError("Invalid seat count")
    if not 1 <= seats <= 3:
        raise ValueError("Seats outside range")
    return seats

@pytest.mark.parametrize("payload", [
    '{"seats": 0}', '{"seats": 4}', '{"seats": "two"}', '[]',
    '{"seats": null}', '{"seats": -1}', '{"seats": true}', '{"seats": 2.0}',
])
def test_rejects_bad_requests(payload):
    with pytest.raises(ValueError):
        parse_request(payload)

def test_accepts_valid():
    assert parse_request('{"seats": 2}') == 2
~~~

## T13 — Performance, load and reliability (Experiment 10)

Functional tests ask "is it right?"; performance tests ask "how fast, how much, how many at once?" Load = expected traffic; stress = beyond it; soak = for a long time; reliability = with injected failures.

~~~python
from time import perf_counter
import statistics

def rank_by_distance(drivers):
    return sorted(drivers, key=lambda item: item["km"])

for n in (1_000, 10_000, 100_000):
    data = [{"id": i, "km": float(n - i)} for i in range(n)]
    samples = []
    for _ in range(5):
        start = perf_counter()
        ranked = rank_by_distance(data)
        samples.append((perf_counter() - start) * 1000)
    assert ranked[0]["km"] <= ranked[-1]["km"]
    print(f"{n:>7} drivers: median {statistics.median(samples):.2f} ms (spread {max(samples)-min(samples):.2f})")
~~~

Report the median and spread, warm up first, record hardware and Python version. This synthetic ranking is not a benchmark of ATLAS Go; only load-test systems you own.

## T14 — End-to-end, UI and exploratory testing (Experiment 11)

Write an end-to-end scenario from the [UML blueprint](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/docs/UML_BLUEPRINT.md#android-app-atlas-go): open → sign in or continue as guest → choose pickup and destination → confirm → see the ride in history. For each step record precondition, action, expected screen/state, actual result, pass/fail, defect id. Run it on a real device or emulator (small and large screens, rotation, offline, denied location permission, app killed and restarted, large fonts). Exploratory charter example: *"try to book more shared seats than exist"*. Never report an E2E pass you did not execute. Browser end-to-end testing with Playwright is shown in the [Web Technology course](WEB_TECHNOLOGY.md).

## T15 — Continuous integration and defect reports (Experiment 12)

A **CI pipeline** runs checks on every push: lint → unit → integration → security/dependencies → build → smoke/E2E → release review. An example workflow (illustrative — adapt it before adding it to the repository):

~~~yaml
name: Python tests
on: [push, pull_request]
jobs:
  pytest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: python -m pip install pytest pytest-cov hypothesis fastapi httpx
      - run: python -m pytest -q testing_lab
~~~

**Defect report:** `ID | commit | environment | steps to reproduce | expected | actual | severity | evidence | owner | status | retest`. Severity = impact; priority = urgency. Give the smallest reproducing input and redact secrets.

## Testing vocabulary

| Term | Meaning |
|---|---|
| fixture | repeatable starting data or environment (`tmp_path`) |
| setup / teardown | prepare / clean up test resources |
| oracle | how the expected result is known |
| positive / negative test | valid / invalid use |
| false positive / false negative | alarm without a defect / defect without an alarm |
| flaky test | passes and fails without code changes |
| line / branch coverage | executed lines / executed decision outcomes |
| mutant killed | a deliberate bug that some test detected |
| TDD | red → green → refactor |
| CI | automated checks on every change |

**Mini-project:** a fare-and-shared-seat module with five parameterised boundary tests, a `tmp_path` integration test, a mock-interaction test, a Hypothesis property, a killed mutant and a coverage report; plus one defect ticket for a bug you introduced on purpose. Label which tests are unit, integration and system tests.

**Further reading:** [Python tutorial](https://docs.python.org/3/tutorial/) · [unittest](https://docs.python.org/3/library/unittest.html) · [pytest](https://docs.pytest.org/) · [Hypothesis](https://hypothesis.readthedocs.io/) · [Coverage.py](https://coverage.readthedocs.io/) · [OWASP Web Security Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)

---

# Part III — Building real apps: integration flows

[Lab source](../python_lab/app_integration.py) · [Integration tests](../python_lab/tests/test_app_integration.py) · [Open in Colab (Part III section)](https://colab.research.google.com/github/FUllSCIPTS/ATLAS/blob/main/python_lab/Python_Colab_Labs.ipynb)

Parts I and II looked at one function at a time. In a real app, **one button click crosses five layers** before any data comes back, and most bugs live *between* the layers: a form that sends a request twice, a list that repeats a row, a save that erases someone else's change, a crash that leaves half the data written. Part III builds a complete ride-booking app with the standard library only — so every hop is visible — and runs twelve labs on it.

~~~mermaid
sequenceDiagram
    actor U as User
    participant S as RideScreen (button + handler)
    participant C as ApiClient (urllib)
    participant A as ApiServer (http.server)
    participant V as RideService (rules)
    participant D as SQLite
    U->>S: click "Book"
    S->>S: read form, client-side checks
    S->>C: POST /api/rides + Idempotency-Key
    C->>A: HTTP request (JSON body)
    A->>V: create_ride(body, key)
    V->>V: validate, price
    V->>D: BEGIN, SELECT key, INSERT, COMMIT
    D-->>V: new row
    V-->>A: ride dict
    A-->>C: 201 Created + JSON
    C-->>S: Response(status, body)
    S-->>U: new row in the table, form cleared
~~~

| Layer | Class in `app_integration.py` | Its one job |
|---|---|---|
| UI | `Button`, `RideScreen` | turn a click into a request; turn the response into what the user sees |
| client | `ApiClient` | send HTTP, apply timeouts and the retry policy |
| route | `ApiServer` | parse URL/JSON, call the service, map exceptions to status codes |
| service | `RideService` | business rules, transactions, cache |
| data | `Database` | SQLite with `CHECK`, `FOREIGN KEY`, `UNIQUE` constraints |

**Run it:** `python python_lab/app_integration.py --all` (charts in `python_lab/results_app`), `python -m pytest -q python_lab/tests` (34 tests), and `python python_lab/app_integration.py --serve` to click the same API in a browser at http://127.0.0.1:8010 with DevTools → Network open.

Every example below starts the whole app on a free local port:

~~~python
import sys
sys.path.insert(0, "python_lab")
from app_integration import App

with App(drivers=3, rides=4) as app:
    resp = app.screen.load_button.click()          # button -> handler -> HTTP -> route -> service -> SQLite
    print(resp.status, resp.headers["X-Total-Count"])
    print(app.screen.render())
~~~

## A01 — Tracing one click

**Idea.** A click is an event; the handler builds a request; the server's route calls the service; the service runs SQL; the result climbs back. `Trace` records each hop from both threads (UI and server).

~~~python
with App(drivers=2, rides=3) as app:
    app.trace.clear()
    app.screen.load_button.click()
    print("\n".join(app.trace.lines()))
~~~

**Chart.** Layer reached at each hop: a "V" down to the database and back. The route runs two SELECTs (COUNT for the total, then the page). **Exercise:** click "Stats" instead and compare the depth and number of hops.

## A02 — Form → POST → INSERT → screen

**Idea.** The *Book* handler validates the form, sends JSON, and only touches the table after a 2xx. A 422 shows a field-specific message; the form keeps its values so the user can fix them.

~~~python
with App(drivers=2) as app:
    app.screen.form.update(passenger="Aoife", pickup="UCC", destination="Cork Airport", km="5.8")
    resp = app.screen.book_button.click().result()      # Book is asynchronous, like fetch()
    print(resp.status, resp.body["fare_cents"], app.db.count("rides"))
~~~

**Chart.** Rows in the database, rows on screen and requests sent over seven clicks. Two clicks never leave the browser; one reaches the server and is rejected. **Common mistake:** adding the row to the table *before* the server answers ("optimistic UI") without undoing it on failure.

## A03 — Validation in three places

**Idea.** The form gives fast feedback but can be bypassed (curl, scripts, an old app version). The API is the authority. Database constraints are the last line of defence and catch what the code forgot — here a missing driver is only caught by the `FOREIGN KEY`.

~~~python
with App(drivers=1) as app:
    bad = {"passenger": "Aoife", "pickup": "UCC", "destination": "UCC", "distance_km": 5}
    resp = app.client.post("/api/rides", bad)               # skips the form entirely
    print(resp.status, resp.body)                            # 422 with the offending field
~~~

**Chart.** A heatmap of input × layer. **Exercise:** add a `CHECK` that rejects unknown places in SQL and watch the last row change.

## A04 — Search-as-you-type and debouncing

**Idea.** Sending a request on every key press multiplies traffic and database work. *Debouncing* waits until typing pauses. User text goes into `LIKE ?` as a parameter, with `%` and `_` escaped.

~~~python
from app_integration import debounced, keystrokes
events = keystrokes("airport", pauses={3: 500})
print(debounced(events, 300))          # ['air', 'airport']
~~~

**Chart.** HTTP requests, SQL SELECTs and rows transferred per strategy; all strategies end on the same results.

## A05 — Double submit

**Idea.** A second click can arrive while the first request is still in flight. Two independent fixes: disable the button (stops it in the browser) and an `Idempotency-Key` header (the server returns the first ride for a repeat — this also protects automatic retries).

~~~python
with App(drivers=1, disable_while_sending=False, send_request_key=True) as app:
    app.screen.form.update(passenger="Aoife", pickup="UCC", destination="Douglas", km="4")
    app.screen.book_button.click(); app.screen.book_button.click(); app.screen.wait()
    print(app.client.requests, "requests ->", app.db.count("rides"), "ride")
~~~

## A06 — "Load more": offset vs keyset pagination

**Idea.** `LIMIT 10 OFFSET 20` counts positions, so a row inserted between clicks shifts every page and a row is shown twice. Keyset pagination (`WHERE id < last_seen_id`) cannot repeat or skip.

**Chart.** Rows shown and duplicate rows after each click, with a new ride inserted after click 2. **Exercise:** delete a row between clicks instead — which mode now *skips* a row?

## A07 — Concurrent edits and optimistic locking

**Idea.** Two people open the same record and both save. Without a check the second save silently erases the first (a *lost update*). With a `version` column, `UPDATE ... WHERE id = ? AND version = ?` changes no rows for the stale copy, the API returns **409 Conflict**, and the screen reloads.

~~~python
with App(drivers=1, rides=1) as app:
    from app_integration import RideScreen
    bob = RideScreen(app.client, app.trace)
    app.screen.open_button.click(1); bob.open_button.click(1)
    app.screen.editing["passenger"] = "Alice"; print(app.screen.save_button.click().status)   # 200
    bob.editing["passenger"] = "Bob";          print(bob.save_button.click().status)          # 409
    bob.close()
~~~

## A08 — Transactions across three tables

**Idea.** *Assign* must update the ride, mark the driver busy and write an audit row. If the process crashes after the first write, only a transaction (`BEGIN … COMMIT`, `ROLLBACK` on error) keeps the three tables consistent.

**Chart.** 12 clicks with 4 injected crashes: without a transaction 4 rides are "assigned" to drivers who are still free and have no audit entry; with one there are none. The user sees a 500 message with a reference number either way — never a traceback.

## A09 — The N+1 query problem

**Idea.** Looping over rides and looking up each driver runs 1 + N queries; one `LEFT JOIN` runs 1. `sqlite3`'s `set_trace_callback` counts every statement.

~~~python
with App(drivers=3, rides=10, assigned=True) as app:
    mark = len(app.db.statements)
    app.client.get("/api/rides-with-drivers?strategy=n_plus_1")
    print(app.db.selects_since(mark), "SELECTs")             # 11
~~~

## A10 — Caching and invalidation

**Idea.** A cache saves work but can show stale data. Invalidate it whenever a write changes what it summarises.

**Chart.** Aggregate queries and stale screens for no cache, a cache that is never cleared, and clear-on-write.

## A11 — Errors, timeouts and retries

**Idea.** Retry only failures that may succeed next time (503, timeouts, refused connections), with exponential back-off. Never retry 4xx (the request is wrong) or 500 (a bug). Map every failure to a plain sentence (`user_message`).

~~~python
from collections import deque
with App(drivers=1) as app:
    app.server.faults["/api/stats"] = deque([503, 503])     # fail twice, then recover
    resp = app.screen.refresh_button.click()
    print(resp.status, "after", resp.attempts, "attempts")
~~~

## A12 — An end-to-end journey

**Idea.** An end-to-end test follows a user story (open, book, assign, complete, cancel, refresh) and after **every** step checks that the screen and the database agree. Rejected actions (409) must change nothing.

**Chart.** Database row counts and cumulative requests after each step.

## Part III exercises

1. Add a **Delete** button for cancelled rides (`DELETE /api/rides/{id}` → 204) with a test that a requested ride cannot be deleted (409).
2. Add a **drivers dropdown** that only lists online, free drivers; make *Assign* use it and test that an offline driver is rejected.
3. Make *Book* retry automatically on 503 — and prove with a test that the `Idempotency-Key` stops duplicates.
4. Show **stale responses**: make search request 1 slow and request 2 fast, and fix the screen so an old response never overwrites a newer one.
5. Replace the in-memory database with a file (`Database(path="rides.db")`) and show that data survives a restart (hint: the schema needs `CREATE TABLE IF NOT EXISTS`).

---

# Part IV — Graded app-building tasks

[Tickets](../python_lab/app_tasks/TICKETS.md) · [Starter](../python_lab/app_tasks/starter.py) · [Acceptance tests](../python_lab/app_tasks/tests/) · [Autograder](../python_lab/app_tasks/grade.py)

Part III *observed* integration flows. Part IV asks you to **build** them, the way you would on a team. Ten tickets add real features to the running app from Part III. Each ticket has:

- a user story;
- an API contract;
- numbered acceptance criteria (AC);
- non-functional requirements;
- a definition of done.

An autograder runs 123 acceptance tests, each named after the criterion it checks, and gives a score out of 100.

| Ticket | Feature | What it really teaches |
|---|---|---|
| T01 | delete a cancelled ride | 204, foreign keys, deleting children first in one transaction, updating the UI only after success |
| T02 | available-drivers dropdown | a read endpoint with one query; UI state that depends on other state |
| T03 | accounts, login, sessions | PBKDF2 with salt, random tokens stored hashed, expiry, identical 401s (no user enumeration) |
| T04 | roles | middleware, 401 vs 403, never trusting the client's role or name, re-checking the role on every request |
| T05 | rate limiting | sliding window, 429 + `Retry-After`, a lock around check-and-record, injected clocks |
| T06 | CSV export | downloads, RFC 4180, spreadsheet formula injection, JOIN instead of N+1 |
| T07 | migration + ratings | `PRAGMA user_version`, atomic migrations, `CHECK`, a race-free conditional `UPDATE` |
| T08 | live search | async UI, discarding out-of-order responses |
| T09 | sort and filter | whitelisting identifiers, binding values, totals vs pages |
| T10 | notifications | the transactional outbox, at-least-once delivery, retries, dead letters |

~~~bash
python python_lab/app_tasks/grade.py --task 1     # one ticket and its failing criteria
python python_lab/app_tasks/grade.py              # everything -> score / 100
python python_lab/app_tasks/grade.py --check      # instructors: solution 100, starter 0, 21 bugs caught
~~~

**How to work a ticket.** Before coding, write the sequence of hops, as in Part III: which button, which request, which route, which SQL, which response, what the screen shows. Then implement the server side and check it with the API acceptance tests, then the screen. Finally read the definition of done as a reviewer would.

**Why the grading can be trusted.** The autograder checks itself. The reference solution must pass every test on repeated runs, the empty starter must fail every ticket, and 21 copies of the solution with one realistic bug each (plaintext passwords, a revealing login error, CSV formula injection, a sort column pasted into SQL, a stale response applied, a migration re-run…) must each be caught. Clocks and network delays are injected, so results never depend on timing.
