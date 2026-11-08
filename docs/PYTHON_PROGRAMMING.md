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


---

# Part II — Software Testing Fundamentals and Practical ATLAS Go Experiments

**Purpose.** Learn to establish *evidence* that Python code behaves as specified. This is an **extension to the 20 original Python lessons**, not a claim that the sample experiments test a live payment provider, live Google Maps service, or production backend. All examples use local/synthetic values unless explicitly connected to a real component.

**Prerequisites:** Lessons 01–19, Python 3.10+ for the type hints used in the ATLAS Go application. **Learning path:** test a function → test a class → test multiple components → simulate a failure → automate the checks → interpret results.

## T01 — What is software testing?

A **requirement** describes the expected behavior; an **input** is the test stimulus; an **oracle** determines the correct output; a **test case** records the input and oracle; a **test suite** groups cases; a **test runner** executes them; a **defect** is a mismatch between required and actual behavior. An *assertion* fails when its condition is false. A *regression* occurs when a previously working behavior breaks after a change.

**Analogy:** Before a driver starts a trip, checking one tyre is a *unit* check, verifying the car drives is an *integration/system* check, and making sure the passenger can complete the journey is an *acceptance* check. Each level catches different problems.

| Level / practice | What is checked? | ATLAS Go teaching example |
|---|---|---|
| Static checks | Code without running it | Syntax, format, type checker, dependency review |
| Unit | One function or class in isolation | \`domain.distance\`, \`domain.fare\`, \`Offer.reserve\` |
| Component | A module and its collaborators | Cart/catalog rules |
| Integration | Two or more real components | Store + JSON file; UI-to-store boundary |
| Contract / API | Agreed request/response schema | Proposed FastAPI ride quotation endpoint |
| System / end-to-end (E2E) | Complete user workflow | Log in → request ride → view history |
| Acceptance | User/business requirements | Shared ride cannot overbook seats |
| Smoke / sanity | Small critical subset after build/change | App imports and basic fare calculation |
| Regression | Old behaviors after new changes | Food ordering still works after ride update |
| Security | Abuse/misuse cases | Invalid access, unsafe inputs, secret handling |
| Performance/load/stress | Latency, throughput, resource usage | Dispatch ranking over synthetic candidates |
| Accessibility/usability | Human use and accessibility | Labels, contrast, keyboard/touch navigation |

**Principles:** Testing finds defects but cannot prove an arbitrary program has no defects. Test early, automate repeatable checks, and retain manual exploratory testing for human workflows. A passing test only establishes the behaviors its inputs and assertions cover.

## T02 — Test design: how to choose inputs

For a shared ride with capacity **3**, partition input values into valid (1–3) and invalid (0, negative, greater than 3, non-integer). Test the **boundaries** \`0, 1, 3, 4\`, not just the easy middle value \`2\`.

- **Equivalence partitioning:** one representative from each category of inputs.
- **Boundary-value analysis:** just below, at and just above a limit.
- **Decision tables:** combine rules such as driver online/offline and seat availability.
- **State-transition testing:** available → reserved → released; reject illegal transitions.
- **Pairwise/combinatorial testing:** cover interacting parameters without testing every possible combination.
- **White-box coverage:** exercise branches visible in source.
- **Black-box testing:** derive expectations from requirements rather than implementation.
- **Risk-based testing:** prioritize money, authentication, privacy and booking correctness.

Write each test using **Arrange → Act → Assert (AAA)**: prepare values, call the function, check its result. Name tests after behavior: \`test_reserve_rejects_too_many_seats\`, not \`test_1\`.

## T03 — Experimental setup (local terminal or Google Colab)

From a checkout of this repository:

~~~bash
python -m pip install pytest pytest-cov
python -m pytest -q
~~~

For the experiments below, create a new folder \`testing_lab/\`. In Colab, use \`%%writefile testing_lab/test_example.py\` (create the directory first with \`!mkdir -p testing_lab\`), then run \`!python -m pytest -q testing_lab\`. Colab shell commands start with \`!\`; do **not** enter \`!python\` in a normal Python script. Use a virtual environment locally when practical.

**Independent quick experiment (no installation):**

~~~python
import unittest

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

unittest.TextTestRunner(verbosity=2).run(
    unittest.defaultTestLoader.loadTestsFromTestCase(TestTotal)
)
~~~

Expected: **3 successful tests**. Run the \`unittest\` snippet as one notebook cell. In a CI script use \`python -m unittest discover\` instead.

## T04 — Unit testing with pytest: fares and invalid inputs (Experiment 1)

This uses **real pure-Python ATLAS Go domain functions**. From the repository root, create \`testing_lab/test_domain.py\`:

~~~python
import pytest
from android_app_placeholder import fare  # replace import as explained below

@pytest.mark.parametrize("pickup,destination,expected", [
    (0, 1, 860),   # (350 + 3*170) cents
    (0, 2, 1200),  # (350 + 5*170) cents
])
def test_standard_fare(pickup, destination, expected):
    assert fare(pickup, destination) == expected

def test_invalid_same_pickup_and_dropoff():
    with pytest.raises(ValueError):
        fare(0, 0)
~~~

**Import correction (required):** The actual module is in \`android-app/atlas_go/domain.py\`, but \`android-app\` contains a hyphen, so it is not a Python package name. Replace the placeholder import with:

~~~python
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "android-app"))
from atlas_go.domain import fare
~~~

Run \`python -m pytest -q testing_lab/test_domain.py\` from the repository root. **Oracle:** 860 cents and 1200 cents; same-place ride raises \`ValueError\`. **Interpretation:** Exact currency values are preferable to comparing binary floating-point euros. **Exercise:** add a comfort-ride expected value and a negative index test.

## T05 — Unit testing classes and state (Experiment 2)

The real \`Offer\` dataclass manages available shared seats. This is a local state-transition test; it does **not** reserve a seat through an external backend.

~~~python
from atlas_go.domain import Offer
import pytest

def test_offer_reserve_and_release():
    offer = Offer("demo", "Driver A", 0, 1, 3, 500, 3)
    assert offer.matches(0, 1, 2)
    offer.reserve(2)
    assert offer.seats == 1
    with pytest.raises(ValueError):
        offer.reserve(2)
    assert offer.seats == 1  # invalid attempt must not change state
    offer.release(2)
    assert offer.seats == 3
~~~

Use the same \`sys.path\` bootstrap from T04 at the top of the file. **Challenge:** test \`reserve(0)\`, \`reserve(4)\` and double release; check the intended business rule for each. **Design caveat:** The model is mutable; checking state before and after an error matters as much as checking that an exception occurred.

## T06 — Test doubles, mocking and dependency injection (Experiment 3)

A **stub** returns prearranged data; a **fake** is a simplified working substitute (e.g., in-memory repository); a **mock** checks how code interacts with a dependency; a **spy** records calls. Use doubles to isolate a unit from a clock, network, GPS or payment service; test real integrations separately.

~~~python
from unittest.mock import Mock

def notify_pickup(sender, ride_id):
    sender.send(ride_id, "Driver assigned")

def test_notification_called_once():
    sender = Mock()
    notify_pickup(sender, "ride-7")
    sender.send.assert_called_once_with("ride-7", "Driver assigned")
~~~

**Experiment:** change the implementation to send twice; the test should fail. **Important:** This is a synthetic notification abstraction, **not** evidence ATLAS Go has a production notification service. Avoid mocking the function under test; mock its external dependencies.

## T07 — Integration testing with an isolated database/file (Experiment 4)

ATLAS Go currently stores local state as JSON through \`LocalStore\`; it is **not** a remote SQL database. A genuine integration test can verify that state survives a fresh \`LocalStore\` instance using a temporary directory.

~~~python
from atlas_go.store import LocalStore

def test_store_writes_state(tmp_path):
    path = tmp_path / "state.json"
    first = LocalStore(path)
    first.reset(save=True)
    assert path.exists()
    second = LocalStore(path)
    assert second.snapshot() == first.snapshot()
~~~

Use the same import bootstrap as T04. The \`tmp_path\` fixture isolates each test and avoids modifying actual user data. **If the real app adds SQLite/PostgreSQL later:** test migrations, rollback, unique constraints, transactions, and concurrency with a separate disposable database. Do not label JSON persistence a SQL test.

## T08 — API and contract testing (Experiment 5; proposed backend only)

ATLAS Go's cited Python/Kivy app is local-first. The following **standalone FastAPI teaching service is a proposed extension**, not proof that the current app exposes \`/quote\`.

Create \`testing_lab/quote_api.py\`:

~~~python
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

Create \`testing_lab/test_quote_api.py\`:

~~~python
from fastapi.testclient import TestClient
from quote_api import app

client = TestClient(app)

def test_quote_contract():
    response = client.post("/quote", json={"km": 3})
    assert response.status_code == 200
    assert response.json() == {"fare_cents": 860}

def test_quote_invalid_distance():
    assert client.post("/quote", json={"km": -1}).status_code == 422
~~~

Run from \`testing_lab/\`: \`python -m pip install fastapi httpx pytest\` then \`python -m pytest -q test_quote_api.py\`. **Concepts:** HTTP methods, status codes, JSON schema, positive/negative cases, compatibility, authentication and authorization checks. TestClient executes an in-process ASGI app; it is **not** a real internet/network reliability test.

## T09 — Parameterization, property-based and metamorphic checks (Experiment 6)

Parameterization repeats an assertion over explicitly chosen examples; **property-based testing** generates many examples from constraints. Metamorphic testing checks relationships even when the exact output is difficult to compute.

~~~python
from hypothesis import given, strategies as st
from atlas_go.domain import fare

@given(
    pickup=st.integers(min_value=0, max_value=3),
    destination=st.integers(min_value=0, max_value=3),
)
def test_comfort_never_cheaper(pickup, destination):
    if pickup == destination:
        return
    assert fare(pickup, destination, comfort=True) >= fare(
        pickup, destination, comfort=False
    )
~~~

Install \`hypothesis\` and reuse T04's import bootstrap. **Property:** for valid routes the comfort option is never cheaper. **Challenge:** propose a second property such as fare non-negativity. Generated examples improve breadth, but the property itself still needs to be correct.

## T10 — Coverage, branches and mutation testing (Experiment 7)

Run from repository root:

~~~bash
python -m pytest -q testing_lab --cov=atlas_go --cov-report=term-missing
~~~

The optional \`pytest-cov\` plugin reports statement/line coverage; use \`--cov-branch\` for branch coverage and \`--cov-report=html\` for a navigable report. Ensure \`android-app\` is available on \`PYTHONPATH\` (or use the bootstrap shown in T04).

**Coverage equation:** covered executable lines ÷ measured executable lines × 100. Example: 18/20 = 90%. **90% coverage does not mean 90% correctness.** A test can execute a line without checking its result. For a **manual mutation experiment**, change the comparison in a local copy of \`Offer.reserve\` from \`<=\` to \`<\`, rerun the boundary test, and restore the code. If no test fails, strengthen the suite. Do not mutate or commit production code as part of the final result.

## T11 — Test-driven development (TDD) and debugging (Experiment 8)

Cycle: **Red → Green → Refactor**. Write the failing test first, implement the minimum behavior, then improve the code while keeping tests green.

~~~python
def test_discount_caps_at_total():
    assert discount(100, 200) == 0  # RED: discount not yet defined

def discount(total, coupon):
    if total < 0 or coupon < 0:
        raise ValueError("Negative money")
    return max(0, total - coupon)  # GREEN
~~~

Place the test in a file and initially leave out the implementation to observe the expected NameError. Add the implementation above the test and rerun; then improve naming or types without changing the tested behavior. This is a **separate teaching helper**, not an ATLAS Go checkout discount feature. Read tracebacks from the final exception upward; use breakpoints, \`pdb\`, or targeted logging rather than hiding exceptions.

## T12 — Security and robustness testing (Experiment 9)

Security test categories include **input validation, authentication, authorization, session expiration, rate limiting, sensitive-data redaction, unsafe deserialization, injection resistance, dependency auditing and privacy**. Test using controlled sample accounts and fixtures only—never production users' private information.

~~~python
import json
import pytest

def parse_request(raw):
    data = json.loads(raw)
    if not isinstance(data, dict) or not isinstance(data.get("seats"), int):
        raise ValueError("Invalid seat count")
    if not 1 <= data["seats"] <= 3:
        raise ValueError("Seats outside range")
    return data["seats"]

@pytest.mark.parametrize("payload", [
    '{"seats": 0}', '{"seats": 4}', '{"seats": "two"}',
    '[]', '{"seats": null}', '{"seats": -1}',
])
def test_rejects_bad_requests(payload):
    with pytest.raises(ValueError):
        parse_request(payload)
~~~

**Limitation:** this checks input handling only, not the application's full security. Note that in Python \`bool\` is a subclass of \`int\`; if \`true\` must be rejected, use \`type(value) is int\` rather than \`isinstance(value, int)\`. Add that case as an exercise. Never store real passwords or API tokens in test fixtures.

## T13 — Performance, stress and reliability (Experiment 10)

Functional testing asks **“is the answer correct?”** Performance testing asks **“how efficiently is it produced?”** Load tests measure behavior under expected concurrency; stress tests exceed expected load; soak tests run for extended periods; reliability tests simulate failures. Do not confuse a single timing with a benchmark.

~~~python
from time import perf_counter

def rank_by_distance(drivers):
    return sorted(drivers, key=lambda item: item["km"])

for n in (100, 1000, 10000):
    data = [{"id": i, "km": float(n - i)} for i in range(n)]
    start = perf_counter()
    ranked = rank_by_distance(data)
    elapsed_ms = (perf_counter() - start) * 1000
    assert ranked[0]["km"] <= ranked[-1]["km"]
    print(f"{n} drivers: {elapsed_ms:.3f} ms")
~~~

**Exercise:** repeat measurements, report median and variability, warm up first, test scaling and include hardware/software details. Timings vary with execution environment; do not invent fixed outputs. This **synthetic ranking** is not a benchmark of the real dispatch model. For live backends, only load-test infrastructure you own or are authorized to test.

## T14 — End-to-end, UI, mobile and exploratory testing (Experiment 11)

Draw a full scenario from the [ATLAS Go UML blueprint](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/docs/UML_BLUEPRINT.md#android-app-atlas-go): user opens welcome screen → authenticates or uses an allowed guest route → selects ride → enters pickup/destination → confirms ride → views history. Record **preconditions**, **actions**, **expected UI/state**, **actual observation**, **pass/fail** and **defect ID**.

Test on a real Android device/emulator for small/large screens, rotations, loss of connectivity, denied permissions, restart/recovery, font scaling and touch target accessibility. UI tests require an appropriate mobile test harness and emulator; the pure Python experiments do not replace them. Run manual exploratory sessions using charters such as *“try to book more seats than exist”*. Do not claim an E2E test has passed without executing the actual app workflow.

## T15 — Continuous integration, reproducibility and defect reporting (Experiment 12)

A **CI pipeline** runs tests after commits/pull requests; **CD** deploys only after appropriate checks and approvals. A practical gate is: lint/static checks → unit tests → integration tests → security/dependency checks → build → smoke/E2E → release review.

**Example GitHub Actions workflow to add as \`.github/workflows/python-tests.yml\` (illustrative; adapt to existing project CI):**

~~~yaml
name: Python tests
on:
  push:
  pull_request:
jobs:
  pytest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: python -m pip install pytest pytest-cov hypothesis
      - run: PYTHONPATH=android-app python -m pytest -q testing_lab
~~~

**Warning:** Keep any optional FastAPI tests' dependencies installed if they are included in the same suite. The YAML above is **an example**, not a claim that this workflow is active. Pin actions/dependencies to reviewed versions or SHAs in production workflows.

**Defect-report template:** \`ID | build/commit | environment | steps to reproduce | expected | actual | severity | evidence | owner | status | retest result\`. Severity describes impact; priority describes urgency. Include minimal reproducible inputs and redact secrets.

## Testing vocabulary and practical assessment

| Term | Short meaning |
|---|---|
| Test fixture | Repeatable starting data/environment |
| Setup / teardown | Prepare/clean isolated test resources |
| Test oracle | Basis for deciding expected behavior |
| Positive / negative | Valid operation / invalid operation |
| False positive / false negative | Test raises an incorrect alarm / misses a defect |
| Flaky test | Sometimes passes and sometimes fails without intended code changes |
| Deterministic test | Same controlled inputs/environment give same verdict |
| Mock / stub / fake | Interaction verifier / canned responder / lightweight implementation |
| Branch / line coverage | Executed decision outcomes / executed lines |
| Integration / E2E | Component interactions / whole user journey |
| Regression / smoke | Recheck old behavior / quickly check critical behavior |
| TDD | Write failing test, implement, then refactor |
| CI | Automated checks on code changes |

**Laboratory record for every experiment:** 1. Objective and requirement; 2. source reference and scope; 3. environment and versions; 4. initial state/fixture; 5. test inputs and expected outputs; 6. actual result or traceback; 7. passed/failed/skipped counts; 8. code/coverage report; 9. interpretation and limitation; 10. next test to improve confidence. Mark any simulated result as **illustrative**, never as a measured result.

**Final student mini-project:** Build a small fare-and-shared-seat module with \`fare\` and \`Offer\`; add at least five parameterized boundary tests, a temporary-file integration test, one mock-interaction test, one Hypothesis property, one manually killed mutation and a coverage report. Write one defect ticket based on a deliberately introduced bug. Submit code, reproducible commands, results and a short explanation of which checks are **unit**, **integration** and **system** tests.

**Further reading:** [Python unittest](https://docs.python.org/3/library/unittest.html) · [pytest](https://docs.pytest.org/) · [Hypothesis](https://hypothesis.readthedocs.io/) · [Coverage.py](https://coverage.readthedocs.io/) · [OWASP Web Security Testing Guide](https://owasp.org/www-project-web-security-testing-guide/) · [ATLAS Go architecture and method catalogue](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/docs/ARCHITECTURE.md#complete-source-method-catalog).

