# Kivy lab — 11 experiments on the ATLAS Go front end

[Course guide](../docs/KIVY_FRONTEND.md) · [Lab source](experiments.py) · [ATLAS Go source](../android-app/atlas_go/) · [ATLAS Go method catalogue](../android-app/docs/ARCHITECTURE.md#complete-source-method-catalog)

Each lab runs real Kivy 2.3.1 — and, wherever possible, the **real ATLAS Go code** (`AtlasGoApp.render`, `RouteMap`, `LiveMap`, `livemap.text_texture`) — and charts what it observed. Every lab is about **its lesson's idea**: lifecycle order, layout shares, density, wrapping, closures, canvas growth, texture caching, redraw coalescing, touch panning and thread hand-off. Each lab asserts its own result before it is charted.

## Getting started

Kivy needs a display, so these labs run locally rather than in Google Colab. From the repository root, with Python 3.10+:

~~~bash
python -m pip install kivy==2.3.1 matplotlib
python kivy_lab/experiments.py                    # runs all 11 labs as a self-test, then usage
python kivy_lab/experiments.py --list
python kivy_lab/experiments.py --all              # K01-K11 -> kivy_lab/results
python kivy_lab/experiments.py --experiment 10
~~~

On a Linux server, container or CI runner with no screen, wrap any command in a virtual display: `xvfb-run -a python kivy_lab/experiments.py --all` (Debian/Ubuntu: `sudo apt install xvfb`).

Each lab writes `lab_NN.csv` (the observed table), `lab_NN.json` (table + title, units and notes) and `lab_NN.png` (the chart). The labs never touch the network (tile downloads are pointed at a closed local port) and keep app data in a temporary folder.

## Experiment register

| Lab | Lesson | What runs | What the chart shows | Reference result |
|---|---|---|---|---|
| K01 | 1 App lifecycle | a probe `App` in a child process records each callback | step number of each call | build → on_start → first frame → on_stop ×2 → run() returns |
| K02 | 2 Widget tree | the real `AtlasGoApp.render()` on 12 screens, 5 times each | widgets per screen and median ms | Welcome 20 widgets / ≈ 8 ms; Intelligence 82 / ≈ 45 ms |
| K03 | 3 Layouts | fixed 48 px header, hint-1 body, hint-0.25 footer; window 300–900 px | child heights | header flat at 48; body : footer = 4 : 1 |
| K04 | 4 Units | `dp(48)` and `sp(14)` at Android densities 1.0–4.0 and font scale 1.3 | pixels | dp(48) = 48 → 192 px; large text: sp(14) 42 → 54.6 px |
| K05 | 5 Binding | ATLAS Go's label recipe with/without the `width → text_size` binding | label height and text width | unbound: 21 px tall, up to 4,170 px wide; bound: 39 → 201 px tall |
| K06 | 6 Events | 5 nav buttons made in a loop, late-binding vs `key=key` lambdas | screen opened by each button | late binding: all open *profile*; default argument: each its own |
| K07 | 8 Canvas | the real `RouteMap` vs the same drawing without `canvas.clear()`, 10 resizes | instructions on the canvas | 44 constant vs 42 → 252 |
| K08 | 9 Text textures | 200 map labels (25 distinct) as new `CoreLabel`s vs `livemap.text_texture` | ms and textures rendered | 200 textures ≈ 9 ms vs 25 textures ≈ 1 ms |
| K09 | 10 Clock | 1–100 changes in one frame, direct draw vs `LiveMap._schedule` pattern | draws (log) | n draws vs always 1 |
| K10 | 11 Touch | a simulated 100 px, −60 px drag on the real `LiveMap` at zoom 12–16 | screen shift and ground distance (log) | always (100, −60) px; 3,516 m at zoom 12 → 220 m at zoom 16 |
| K11 | 12 Threads | 40 worker-thread results delivered directly vs via `Clock.schedule_once` | deliveries on main vs worker thread | direct 0/40 on main; Clock 40/0 |

## Interpreting results

K02 and K08 are timings and depend on the machine; the reference figures came from a Linux container with a virtual display (Xvfb). Every other lab is deterministic. K01 shows a real Kivy 2.3.1 behaviour worth knowing: an app that calls `self.stop()` receives `on_stop` twice, which is why ATLAS Go's `on_stop` only does things that are safe to repeat.

**Report for each lab:** question → prediction → what the code does → table and chart → explanation of the y-axis and units → an edge case → the ATLAS Go code that uses the idea, and one difference between it and the lab code.

## Course checks

Every `python` block in [the course guide](../docs/KIVY_FRONTEND.md) is a complete program that checks itself with `assert` and closes its own window; all 16 were executed with `xvfb-run` against Kivy 2.3.1 when the course was written, together with `python kivy_lab/experiments.py --all`.
