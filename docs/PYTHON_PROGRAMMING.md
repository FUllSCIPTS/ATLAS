# Python Programming with ATLAS Go — Standalone Concept-and-Lab Textbook

**Level:** absolute beginner to intermediate. **Plan:** 20 integrated lessons over 10–15 weeks, each with a concept, working Python example, ATLAS Go function reference, laboratory experiment, figure and interpretation exercise. **Tools:** Python 3, GitHub and Google Colab. No Android installation needed.

[Open the 20-lab notebook](https://colab.research.google.com/github/FUllSCIPTS/ATLAS/blob/main/python_lab/Python_Colab_Labs.ipynb) · [Laboratory manual](../python_lab/README.md) · [ATLAS Go UML](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/docs/UML_BLUEPRINT.md#android-app-atlas-go) · [Verified method catalogue](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/docs/ARCHITECTURE.md#complete-source-method-catalog)

## Learning sequence

~~~mermaid
flowchart LR
 A[Syntax and variables] --> B[Control flow]
 B --> C[Collections and functions]
 C --> D[Classes and exceptions]
 D --> E[Persistence and testing]
 E --> F[Profiling and ATLAS Go]
~~~

## How the existing Python application works

ATLAS Go is a Python/Kivy Android application with on-device user, ride and food state. Its *actual* classes are listed in the UML. The standalone lab experiments use **synthetic records and calculations**, not live ride dispatch or payments. In the diagrams, arrows mean functions use other components, not inheritance unless stated.

~~~mermaid
flowchart TD
 UI[AtlasGoApp: screens] --> STORE[LocalStore: account and booking state]
 UI --> GEO[geo: coordinates and travel times]
 UI --> AI[intelligence: dispatch ranking]
 STORE --> DOMAIN[domain: Cart, Catalog and Offer]
 STORE --> FILE[Local JSON state]
~~~

## Course map

| Lesson | Topic | ATLAS Go method | Lab |
|---|---|---|---|
| 01 | Python setup, print and comments | [AtlasGoApp.build](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/app.py) | P01 |
| 02 | Variables, numbers and operators | [fare](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/domain.py) | P02 |
| 03 | Basic data types | [parse_int](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/accounts.py) | P03 |
| 04 | Conditions and boolean logic | [set_online](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) | P04 |
| 05 | Loops and iteration | [outlook](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py) | P05 |
| 06 | Strings and Unicode | [clean_email](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/accounts.py) | P06 |
| 07 | Lists and slicing | [my_history](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) | P07 |
| 08 | Tuples, sets and dictionaries | [Cart](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/domain.py) | P08 |
| 09 | Comprehensions | [online_drivers](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) | P09 |
| 10 | Functions and type hints | [eta_minutes](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/geo.py) | P10 |
| 11 | Classes, methods and dataclasses | [Candidate](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py) | P11 |
| 12 | Inheritance and polymorphism | [AtlasGoApp](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/app.py) | P12 |
| 13 | Exceptions and validation | [validate](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) | P13 |
| 14 | Files, pathlib and JSON | [commit](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) | P14 |
| 15 | Iterators and generators | [visible_tiles](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/livemap.py) | P15 |
| 16 | Lambda, map and filter | [rank](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py) | P16 |
| 17 | Sorting, selection and pipelines | [choose](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py) | P17 |
| 18 | Time complexity and search | [online_drivers](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) | P18 |
| 19 | Testing, assertions and debugging | [self_test](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py) | P19 |
| 20 | Profiling, charts and project structure | [LearningLab](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py) | P20 |

## Lesson 01 — Python setup, print and comments

**Concept explained:** Python executes statements from top to bottom. Notebook cells share a Python runtime. Indentation defines blocks.

**Try in a Python cell:**

~~~python
print('Hello ATLAS')
~~~

**Where ATLAS Go uses it:** Entry point and app construction. See the verified [AtlasGoApp.build source](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/app.py) and [UML function catalogue](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/docs/ARCHITECTURE.md#complete-source-method-catalog). A related reference does not mean the app uses the exact simplified exercise implementation.

**Lab P01:** Open the [Colab notebook](https://colab.research.google.com/github/FUllSCIPTS/ATLAS/blob/main/python_lab/Python_Colab_Labs.ipynb), run this numbered experiment, inspect its CSV and PNG, and explain the input size n, the output values and their units. Predict what should happen if n doubles. **Student challenge:** test zero/empty input or a boundary case; identify the source method in UML and state one difference from the teaching implementation.


## Lesson 02 — Variables, numbers and operators

**Concept explained:** Assignment binds a name to a value. Use +, -, *, /, //, %, and **; calculate money carefully using integer cents.

**Try in a Python cell:**

~~~python
km=5; rate=2; assert km*rate==10
~~~

**Where ATLAS Go uses it:** Ride-fare calculation. See the verified [fare source](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/domain.py) and [UML function catalogue](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/docs/ARCHITECTURE.md#complete-source-method-catalog). A related reference does not mean the app uses the exact simplified exercise implementation.

**Lab P02:** Open the [Colab notebook](https://colab.research.google.com/github/FUllSCIPTS/ATLAS/blob/main/python_lab/Python_Colab_Labs.ipynb), run this numbered experiment, inspect its CSV and PNG, and explain the input size n, the output values and their units. Predict what should happen if n doubles. **Student challenge:** test zero/empty input or a boundary case; identify the source method in UML and state one difference from the teaching implementation.


## Lesson 03 — Basic data types

**Concept explained:** int, float, str, bool and None represent numbers, text, logical values and absence. Explicit conversion can fail.

**Try in a Python cell:**

~~~python
age=int('20'); assert type(age) is int
~~~

**Where ATLAS Go uses it:** User-input conversion. See the verified [parse_int source](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/accounts.py) and [UML function catalogue](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/docs/ARCHITECTURE.md#complete-source-method-catalog). A related reference does not mean the app uses the exact simplified exercise implementation.

**Lab P03:** Open the [Colab notebook](https://colab.research.google.com/github/FUllSCIPTS/ATLAS/blob/main/python_lab/Python_Colab_Labs.ipynb), run this numbered experiment, inspect its CSV and PNG, and explain the input size n, the output values and their units. Predict what should happen if n doubles. **Student challenge:** test zero/empty input or a boundary case; identify the source method in UML and state one difference from the teaching implementation.


## Lesson 04 — Conditions and boolean logic

**Concept explained:** if/elif/else select a branch; and/or/not combine checks; comparison operators test equality and order.

**Try in a Python cell:**

~~~python
role='driver'; assert (role=='driver')
~~~

**Where ATLAS Go uses it:** Driver-role guard. See the verified [set_online source](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) and [UML function catalogue](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/docs/ARCHITECTURE.md#complete-source-method-catalog). A related reference does not mean the app uses the exact simplified exercise implementation.

**Lab P04:** Open the [Colab notebook](https://colab.research.google.com/github/FUllSCIPTS/ATLAS/blob/main/python_lab/Python_Colab_Labs.ipynb), run this numbered experiment, inspect its CSV and PNG, and explain the input size n, the output values and their units. Predict what should happen if n doubles. **Student challenge:** test zero/empty input or a boundary case; identify the source method in UML and state one difference from the teaching implementation.


## Lesson 05 — Loops and iteration

**Concept explained:** for visits iterable values; while repeats until a condition fails. range, enumerate and break support repeated work.

**Try in a Python cell:**

~~~python
total=0
for i in range(5): total+=i
assert total==10
~~~

**Where ATLAS Go uses it:** 24-hour forecast loop. See the verified [outlook source](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py) and [UML function catalogue](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/docs/ARCHITECTURE.md#complete-source-method-catalog). A related reference does not mean the app uses the exact simplified exercise implementation.

**Lab P05:** Open the [Colab notebook](https://colab.research.google.com/github/FUllSCIPTS/ATLAS/blob/main/python_lab/Python_Colab_Labs.ipynb), run this numbered experiment, inspect its CSV and PNG, and explain the input size n, the output values and their units. Predict what should happen if n doubles. **Student challenge:** test zero/empty input or a boundary case; identify the source method in UML and state one difference from the teaching implementation.


## Lesson 06 — Strings and Unicode

**Concept explained:** str is Unicode; bytes are encoded data. Slicing extracts a substring; strings are immutable.

**Try in a Python cell:**

~~~python
name='ATLAS'; assert name[:2]=='AT'
~~~

**Where ATLAS Go uses it:** Email normalization/validation. See the verified [clean_email source](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/accounts.py) and [UML function catalogue](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/docs/ARCHITECTURE.md#complete-source-method-catalog). A related reference does not mean the app uses the exact simplified exercise implementation.

**Lab P06:** Open the [Colab notebook](https://colab.research.google.com/github/FUllSCIPTS/ATLAS/blob/main/python_lab/Python_Colab_Labs.ipynb), run this numbered experiment, inspect its CSV and PNG, and explain the input size n, the output values and their units. Predict what should happen if n doubles. **Student challenge:** test zero/empty input or a boundary case; identify the source method in UML and state one difference from the teaching implementation.


## Lesson 07 — Lists and slicing

**Concept explained:** Lists are ordered mutable sequences. append, pop and slices operate on elements. Assignment aliases; copy makes a new list.

**Try in a Python cell:**

~~~python
items=['r1']; items.append('r2'); assert items[-1]=='r2'
~~~

**Where ATLAS Go uses it:** History stored as list records. See the verified [my_history source](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) and [UML function catalogue](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/docs/ARCHITECTURE.md#complete-source-method-catalog). A related reference does not mean the app uses the exact simplified exercise implementation.

**Lab P07:** Open the [Colab notebook](https://colab.research.google.com/github/FUllSCIPTS/ATLAS/blob/main/python_lab/Python_Colab_Labs.ipynb), run this numbered experiment, inspect its CSV and PNG, and explain the input size n, the output values and their units. Predict what should happen if n doubles. **Student challenge:** test zero/empty input or a boundary case; identify the source method in UML and state one difference from the teaching implementation.


## Lesson 08 — Tuples, sets and dictionaries

**Concept explained:** Tuples are immutable sequences; sets enforce uniqueness; dictionaries map hashable keys to values.

**Try in a Python cell:**

~~~python
d={'ride':1}; assert d['ride']==1
~~~

**Where ATLAS Go uses it:** Basket item dictionary. See the verified [Cart source](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/domain.py) and [UML function catalogue](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/docs/ARCHITECTURE.md#complete-source-method-catalog). A related reference does not mean the app uses the exact simplified exercise implementation.

**Lab P08:** Open the [Colab notebook](https://colab.research.google.com/github/FUllSCIPTS/ATLAS/blob/main/python_lab/Python_Colab_Labs.ipynb), run this numbered experiment, inspect its CSV and PNG, and explain the input size n, the output values and their units. Predict what should happen if n doubles. **Student challenge:** test zero/empty input or a boundary case; identify the source method in UML and state one difference from the teaching implementation.


## Lesson 09 — Comprehensions

**Concept explained:** A list comprehension transforms/filters an iterable. It is concise but should stay readable.

**Try in a Python cell:**

~~~python
xs=[x*x for x in range(5) if x%2==0]; assert xs==[0,4,16]
~~~

**Where ATLAS Go uses it:** Filters online driver records. See the verified [online_drivers source](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) and [UML function catalogue](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/docs/ARCHITECTURE.md#complete-source-method-catalog). A related reference does not mean the app uses the exact simplified exercise implementation.

**Lab P09:** Open the [Colab notebook](https://colab.research.google.com/github/FUllSCIPTS/ATLAS/blob/main/python_lab/Python_Colab_Labs.ipynb), run this numbered experiment, inspect its CSV and PNG, and explain the input size n, the output values and their units. Predict what should happen if n doubles. **Student challenge:** test zero/empty input or a boundary case; identify the source method in UML and state one difference from the teaching implementation.


## Lesson 10 — Functions and type hints

**Concept explained:** def defines reusable code; return passes back a result. Parameters may have defaults. Type annotations describe, not enforce, types.

**Try in a Python cell:**

~~~python
def eta(km,speed=30): return km/speed*60
assert eta(15)==30
~~~

**Where ATLAS Go uses it:** Travel-time helper. See the verified [eta_minutes source](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/geo.py) and [UML function catalogue](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/docs/ARCHITECTURE.md#complete-source-method-catalog). A related reference does not mean the app uses the exact simplified exercise implementation.

**Lab P10:** Open the [Colab notebook](https://colab.research.google.com/github/FUllSCIPTS/ATLAS/blob/main/python_lab/Python_Colab_Labs.ipynb), run this numbered experiment, inspect its CSV and PNG, and explain the input size n, the output values and their units. Predict what should happen if n doubles. **Student challenge:** test zero/empty input or a boundary case; identify the source method in UML and state one difference from the teaching implementation.


## Lesson 11 — Classes, methods and dataclasses

**Concept explained:** Classes group fields and methods; self refers to the instance. dataclass automates common record boilerplate.

**Try in a Python cell:**

~~~python
from dataclasses import dataclass
@dataclass
class Ride:
    km: float
assert Ride(3).km==3
~~~

**Where ATLAS Go uses it:** Driver candidate dataclass. See the verified [Candidate source](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py) and [UML function catalogue](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/docs/ARCHITECTURE.md#complete-source-method-catalog). A related reference does not mean the app uses the exact simplified exercise implementation.

**Lab P11:** Open the [Colab notebook](https://colab.research.google.com/github/FUllSCIPTS/ATLAS/blob/main/python_lab/Python_Colab_Labs.ipynb), run this numbered experiment, inspect its CSV and PNG, and explain the input size n, the output values and their units. Predict what should happen if n doubles. **Student challenge:** test zero/empty input or a boundary case; identify the source method in UML and state one difference from the teaching implementation.


## Lesson 12 — Inheritance and polymorphism

**Concept explained:** Subclasses may override a method. Polymorphism calls the same interface on different object types; composition is often better.

**Try in a Python cell:**

~~~python
class Base:
    def label(self): return 'base'
class Child(Base):
    def label(self): return 'child'
assert Child().label()=='child'
~~~

**Where ATLAS Go uses it:** Subclass of Kivy App. See the verified [AtlasGoApp source](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/app.py) and [UML function catalogue](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/docs/ARCHITECTURE.md#complete-source-method-catalog). A related reference does not mean the app uses the exact simplified exercise implementation.

**Lab P12:** Open the [Colab notebook](https://colab.research.google.com/github/FUllSCIPTS/ATLAS/blob/main/python_lab/Python_Colab_Labs.ipynb), run this numbered experiment, inspect its CSV and PNG, and explain the input size n, the output values and their units. Predict what should happen if n doubles. **Student challenge:** test zero/empty input or a boundary case; identify the source method in UML and state one difference from the teaching implementation.


## Lesson 13 — Exceptions and validation

**Concept explained:** try/except handles anticipated failures; raise reports invalid inputs. Do not catch every exception silently.

**Try in a Python cell:**

~~~python
try:
    int('bad')
except ValueError:
    rejected=True
assert rejected
~~~

**Where ATLAS Go uses it:** Saved-state validation. See the verified [validate source](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) and [UML function catalogue](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/docs/ARCHITECTURE.md#complete-source-method-catalog). A related reference does not mean the app uses the exact simplified exercise implementation.

**Lab P13:** Open the [Colab notebook](https://colab.research.google.com/github/FUllSCIPTS/ATLAS/blob/main/python_lab/Python_Colab_Labs.ipynb), run this numbered experiment, inspect its CSV and PNG, and explain the input size n, the output values and their units. Predict what should happen if n doubles. **Student challenge:** test zero/empty input or a boundary case; identify the source method in UML and state one difference from the teaching implementation.


## Lesson 14 — Files, pathlib and JSON

**Concept explained:** Files persist data across runs. JSON serializes dictionaries, lists and basic scalar values. Atomic writes support consistency.

**Try in a Python cell:**

~~~python
import json
assert json.loads(json.dumps({'ok':True}))['ok']
~~~

**Where ATLAS Go uses it:** Atomic JSON storage. See the verified [commit source](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) and [UML function catalogue](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/docs/ARCHITECTURE.md#complete-source-method-catalog). A related reference does not mean the app uses the exact simplified exercise implementation.

**Lab P14:** Open the [Colab notebook](https://colab.research.google.com/github/FUllSCIPTS/ATLAS/blob/main/python_lab/Python_Colab_Labs.ipynb), run this numbered experiment, inspect its CSV and PNG, and explain the input size n, the output values and their units. Predict what should happen if n doubles. **Student challenge:** test zero/empty input or a boundary case; identify the source method in UML and state one difference from the teaching implementation.


## Lesson 15 — Iterators and generators

**Concept explained:** An iterator yields one item at a time; yield creates a lazy generator. Converting to list materializes all values.

**Try in a Python cell:**

~~~python
def count():
    yield 1
    yield 2
assert list(count())==[1,2]
~~~

**Where ATLAS Go uses it:** Related iteration; generator is an extension. See the verified [visible_tiles source](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/livemap.py) and [UML function catalogue](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/docs/ARCHITECTURE.md#complete-source-method-catalog). A related reference does not mean the app uses the exact simplified exercise implementation.

**Lab P15:** Open the [Colab notebook](https://colab.research.google.com/github/FUllSCIPTS/ATLAS/blob/main/python_lab/Python_Colab_Labs.ipynb), run this numbered experiment, inspect its CSV and PNG, and explain the input size n, the output values and their units. Predict what should happen if n doubles. **Student challenge:** test zero/empty input or a boundary case; identify the source method in UML and state one difference from the teaching implementation.


## Lesson 16 — Lambda, map and filter

**Concept explained:** Higher-order functions take other functions as arguments. Lambda expresses short anonymous operations.

**Try in a Python cell:**

~~~python
assert sorted([3,1,2],key=lambda x:-x)==[3,2,1]
~~~

**Where ATLAS Go uses it:** Sorting by scored probability. See the verified [rank source](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py) and [UML function catalogue](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/docs/ARCHITECTURE.md#complete-source-method-catalog). A related reference does not mean the app uses the exact simplified exercise implementation.

**Lab P16:** Open the [Colab notebook](https://colab.research.google.com/github/FUllSCIPTS/ATLAS/blob/main/python_lab/Python_Colab_Labs.ipynb), run this numbered experiment, inspect its CSV and PNG, and explain the input size n, the output values and their units. Predict what should happen if n doubles. **Student challenge:** test zero/empty input or a boundary case; identify the source method in UML and state one difference from the teaching implementation.


## Lesson 17 — Sorting, selection and pipelines

**Concept explained:** Build features, filter records and rank candidates. Sorting by a key is not graph shortest-path routing.

**Try in a Python cell:**

~~~python
drivers=[('A',4),('B',2)]; assert min(drivers,key=lambda x:x[1])[0]=='B'
~~~

**Where ATLAS Go uses it:** Selects scored driver candidate. See the verified [choose source](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py) and [UML function catalogue](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/docs/ARCHITECTURE.md#complete-source-method-catalog). A related reference does not mean the app uses the exact simplified exercise implementation.

**Lab P17:** Open the [Colab notebook](https://colab.research.google.com/github/FUllSCIPTS/ATLAS/blob/main/python_lab/Python_Colab_Labs.ipynb), run this numbered experiment, inspect its CSV and PNG, and explain the input size n, the output values and their units. Predict what should happen if n doubles. **Student challenge:** test zero/empty input or a boundary case; identify the source method in UML and state one difference from the teaching implementation.


## Lesson 18 — Time complexity and search

**Concept explained:** Count elementary operations as n grows. O is an asymptotic upper bound, not elapsed seconds. Binary search needs sorted input.

**Try in a Python cell:**

~~~python
a=list(range(100)); assert 99 in a
~~~

**Where ATLAS Go uses it:** Linear collection scan. See the verified [online_drivers source](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py) and [UML function catalogue](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/docs/ARCHITECTURE.md#complete-source-method-catalog). A related reference does not mean the app uses the exact simplified exercise implementation.

**Lab P18:** Open the [Colab notebook](https://colab.research.google.com/github/FUllSCIPTS/ATLAS/blob/main/python_lab/Python_Colab_Labs.ipynb), run this numbered experiment, inspect its CSV and PNG, and explain the input size n, the output values and their units. Predict what should happen if n doubles. **Student challenge:** test zero/empty input or a boundary case; identify the source method in UML and state one difference from the teaching implementation.


## Lesson 19 — Testing, assertions and debugging

**Concept explained:** Tests compare expected with actual behavior. Use empty, invalid and boundary cases, and read error traces.

**Try in a Python cell:**

~~~python
def add(a,b): return a+b
assert add(2,3)==5
assert add(-1,1)==0
~~~

**Where ATLAS Go uses it:** On-device model smoke tests. See the verified [self_test source](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py) and [UML function catalogue](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/docs/ARCHITECTURE.md#complete-source-method-catalog). A related reference does not mean the app uses the exact simplified exercise implementation.

**Lab P19:** Open the [Colab notebook](https://colab.research.google.com/github/FUllSCIPTS/ATLAS/blob/main/python_lab/Python_Colab_Labs.ipynb), run this numbered experiment, inspect its CSV and PNG, and explain the input size n, the output values and their units. Predict what should happen if n doubles. **Student challenge:** test zero/empty input or a boundary case; identify the source method in UML and state one difference from the teaching implementation.


## Lesson 20 — Profiling, charts and project structure

**Concept explained:** perf_counter records elapsed runtime; CSV preserves measurements; plots should carry units. Modules organize reusable source.

**Try in a Python cell:**

~~~python
import time
start=time.perf_counter(); sum(range(1000)); assert time.perf_counter()>=start
~~~

**Where ATLAS Go uses it:** Related learning-lab class; benchmark is teaching code. See the verified [LearningLab source](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py) and [UML function catalogue](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/docs/ARCHITECTURE.md#complete-source-method-catalog). A related reference does not mean the app uses the exact simplified exercise implementation.

**Lab P20:** Open the [Colab notebook](https://colab.research.google.com/github/FUllSCIPTS/ATLAS/blob/main/python_lab/Python_Colab_Labs.ipynb), run this numbered experiment, inspect its CSV and PNG, and explain the input size n, the output values and their units. Predict what should happen if n doubles. **Student challenge:** test zero/empty input or a boundary case; identify the source method in UML and state one difference from the teaching implementation.

## Additional foundation lessons — read while completing P01–P20

### Indentation, error messages and notebook state

Python uses indentation to mark suites after if, for, while, def and class. Four spaces are conventional. SyntaxError indicates malformed syntax; NameError an unknown name; TypeError incompatible operations; IndexError invalid positions; ValueError an invalid value. Notebook variables persist between cells: use **Runtime → Restart and run all** to verify the course runs from a clean state.

### Names, references, shallow copies and mutability

Assignment binds references. If two names refer to the same list, mutating it affects both. A slice or copy normally creates a new outer list, but nested objects may remain shared.

~~~python
a=[1,2]; b=a; b.append(3)
assert a==[1,2,3]
c=a.copy(); c.append(4)
assert a==[1,2,3]
~~~

### Scope and safe function defaults

Local variables belong to the function's call. A return statement produces the result; print merely displays it. Avoid mutable default arguments that persist between calls.

~~~python
def new_order(item, cart=None):
    if cart is None:
        cart=[]
    cart.append(item)
    return cart
assert new_order('tea')==['tea']
assert new_order('coffee')==['coffee']
~~~

### Packages, imports and project layout

A .py file is a module; a package organizes related modules. Import standard modules such as math, pathlib, json and time rather than copying their code. Avoid naming your own files json.py, random.py or time.py because these names can shadow standard-library modules. ATLAS Go is organized under android-app/atlas_go, while these independent teaching experiments are under python_lab.

### Complexity and meaningful charts

Theory counts operations (P18), while a benchmark measures elapsed milliseconds (P20). Python dict membership is expected O(1) under hashing assumptions, whereas list membership may scan O(n). The P20 measurements are on prebuilt containers and can be noisy; they are **not** benchmarks of ATLAS Go. P01–P19 plot actual computed values/counts, not arbitrary curves or hardware timings. Every chart has an associated machine-readable CSV and JSON.

### Verification, privacy and limitations

Use assert and independent tests to cover empty, duplicate, missing, extreme and malformed cases. No tutorial cell should upload real customer data, passwords, API keys, or location history. ATLAS Go's local app is not a deployed multi-user booking backend. The DSA, security and cryptography manuals provide related advanced extensions.

## Assessment and capstone

| Criterion | Marks |
|---|---:|
| Explain concept and expected output | 20 |
| Correct Python programs and edge cases | 25 |
| Reproducible experiments and tests | 20 |
| Interpret CSV/PNG charts and units | 20 |
| Follow UML to verified app functions | 15 |

**Capstone:** build a *local synthetic* ride-dispatch simulator with a Ride dataclass, dictionary of drivers, list filtering by online status, a simple geographic distance score, ranking, exception handling, JSON save/load and test assertions. Explain how it differs from the actual ATLAS Go classes in UML. Do not make live bookings.

**Lab report for each experiment:** objective → example → input size → predicted result → code and tests → observed table/graph → explanation → UML method used → limitation and improvement.
