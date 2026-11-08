# Python lab — complete concept-and-lab curriculum

[Standalone illustrated course](../docs/PYTHON_PROGRAMMING.md) · [Run the 20 experiments in Google Colab](https://colab.research.google.com/github/FUllSCIPTS/ATLAS/blob/main/python_lab/Python_Colab_Labs.ipynb) · [ATLAS Go UML class/function catalogue](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/docs/ARCHITECTURE.md#complete-source-method-catalog)

Each lesson pairs a beginner-friendly Python concept with a reproducible experiment and a real ATLAS Go function/class link where relevant. All lab data are synthetic. No authentication, API keys, live routing or real bookings are needed.

## Getting started

In Colab open the notebook, choose **Runtime → Run all**. The first code cell downloads the runner from GitHub. Use the Files sidebar to download python_20_labs.zip after executing. For a local Python 3.10+ environment:

~~~bash
python -m pip install matplotlib
python python_lab/experiments.py --all --output python_lab/results
python python_lab/experiments.py --experiment 11
python python_lab/experiments.py
~~~

Each PNN exports lab_NN.csv (source values), lab_NN.png (graph) and lab_NN.json (structured results). The runner performs smoke tests and provides a --experiment selector.

## Experiment register

| Lab | Topic | Metric status |
|---|---|---|
| P01 | Python setup, print and comments | calculated/count values |
| P02 | Variables, numbers and operators | calculated/count values |
| P03 | Basic data types | calculated/count values |
| P04 | Conditions and boolean logic | calculated/count values |
| P05 | Loops and iteration | calculated/count values |
| P06 | Strings and Unicode | calculated/count values |
| P07 | Lists and slicing | calculated/count values |
| P08 | Tuples, sets and dictionaries | calculated/count values |
| P09 | Comprehensions | calculated/count values |
| P10 | Functions and type hints | calculated/count values |
| P11 | Classes, methods and dataclasses | calculated/count values |
| P12 | Inheritance and polymorphism | calculated/count values |
| P13 | Exceptions and validation | calculated/count values |
| P14 | Files, pathlib and JSON | calculated/count values |
| P15 | Iterators and generators | calculated/count values |
| P16 | Lambda, map and filter | calculated/count values |
| P17 | Sorting, selection and pipelines | calculated/count values |
| P18 | Time complexity and search | exact comparison count |
| P19 | Testing, assertions and debugging | calculated/count values |
| P20 | Profiling, charts and project structure | actual median measured milliseconds |

## Experimental interpretation

P01–P19 are real calculations with operation counts, character counts, sums or other declared metrics; they are not timings or estimates of speed. P18 counts linear and binary-search comparisons. P20 uses repeated perf_counter timing on prebuilt list and dictionary lookups, records median milliseconds, and is affected by machine noise. Fix the random seed where randomness is used. Mathematical growth and measured time must not be conflated.

For each experiment record the input size and data shape, algorithm, hypothesis, CSV result, PNG chart, what its y-axis measures, an edge case, and a source-link/UML comparison. Never infer that the teaching code is identical to ATLAS Go business logic.
