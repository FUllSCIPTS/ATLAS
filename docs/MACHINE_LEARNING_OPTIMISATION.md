# Machine learning and optimisation in ATLAS — a teaching guide

This guide uses ATLAS as a worked example for teaching **optimisation** and **machine learning**. The
centre of the paper is an optimisation algorithm: every five seconds ATLAS solves a **binary integer
program (BIP)** that decides which modules run inside one process (tight coupling) and which run as
separate services (loose coupling). Around it sit four learners: an **LSTM forecaster**, an
**Isolation-Forest anomaly detector**, and the **reinforcement-learning** dispatch and courier
agents of the ATLAS Go app. ATLAS Go 1.3–1.4 adds two more layers of material: a **digital twin**
with three agents (dispatch, pricing, and a Guardian that shields both), and a **closed LSTM → RL
loop** that forecasts, acts, records outcomes and retrains itself on the phone. The guide uses them
to teach **actor and critic networks**, **multi-agent RL with a shared critic (MAPPO)** and
**continuous learning with validation**. Every claim points at the file that implements it.

> **Where each piece runs.**
>
> | Tag | Meaning |
> |---|---|
> | 📄 **Paper** | The algorithm evaluated in the article. Runs in the research code on `main` (`atlas_sim.zip`, `run_*.py`). |
> | ✅ **App / starter** | Runs in the ATLAS Go Android app (`android-app/`) or the server starter (`architecture-explorer` branch). |
> | 🧪 **Synthetic** | Trained on simulated data, by design. The numbers illustrate the method; they are not measurements of real riders or traffic. |
> | 🎓 **Teaching extension** | **Not** in the ATLAS code. Shows where a technique would fit. |
>
> The coupling BIP runs in the paper's simulator, not in the Android app or the server starter.
> §2.6 says exactly where it is and is not used, and how it would attach to the ride-hailing services.

**Interactive companion:** [ATLAS Architecture Explorer → ML & Optimisation](https://fullscipts.github.io/ATLAS/#ml) —
run the coupling BIP live (move the load and the anomaly score and watch modules leave the monolith),
compare the three solvers, train a forecaster with gradient descent and Adam, build an Isolation
Forest, train the REINFORCE dispatch policy, rehearse drivers in the digital twin and test the
Guardian, train an actor-critic against REINFORCE, train two agents with independent critics and with
one shared critic, and run ATLAS Go's LSTM in your browser and replay its live loop. Every concept links to its
function in the [UML catalogue](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/docs/UML_BLUEPRINT.md#machine-learning-and-optimisation-catalogue).

**Command-line lab:** `python3 ml_lab/ml_optimisation_lab.py` (numpy, scipy, scikit-learn; about 3 s).
It imports the repository's own code — the BIP from `atlas_sim.zip`, the solvers from
`run_bip_timing.py`, the learners from `android-app/` — rather than copies.

**Forty-four experiments, one file each** ([ml_lab/README.md](../ml_lab/README.md)):

| Track | Folder | Experiments | Study paths (`--path`) |
|---|---|---|---|
| Machine learning | `ml_lab/machine_learning/` (`run_ml.py`) | 1 linear regression · 2 bias-variance and ridge · 3 logistic regression · 4 kNN and scaling · 5 naive Bayes and Bayes' rule · 6 decision tree · 7 forests and boosting · 8 SVM kernels · 9 neural network and backprop · 10 metrics under imbalance · 11 cross-validation and leakage · 12 k-means · 13 DBSCAN on Cork · 14 PCA · 15 four anomaly detectors · 16 forecasting baselines and Holt-Winters · 17 concept drift and online learning · 18 learning to rank · 19 bandits · 20 Q-learning · **21 digital twin** · **22 actor and critic networks (A2C)** · **23 two agents, one shared critic (MAPPO)** · **24 LSTM + RL closed loop** | `supervised`, `trees-and-ensembles`, `neural-networks`, `unsupervised`, `time-series`, `decisions`, `trustworthy-ml`, `reinforcement-learning`, `digital-twin`, `multi-agent`, `lstm-and-rl` |
| Optimisation | `ml_lab/optimisation/` (`run_optimisation.py`) | 1 gradient descent and conditioning · 2 momentum, Nesterov, Adam · 3 Newton and BFGS · 4 KKT core allocation · 5 LP transport of drivers · 6 duality and shadow prices · 7 dynamic programming and knapsack · 8 branch-and-bound on the coupling BIP · 9 Dijkstra, A*, Bellman-Ford · 10 Hungarian assignment · 11 TSP: Held-Karp and 2-opt · 12 bin packing pods · 13 max flow / min cut · 14 DP autoscaling with switching costs · 15 local search and tabu · 16 simulated annealing · 17 genetic algorithm · 18 (1+1)-ES, differential evolution, PSO · 19 Bayesian optimisation · 20 Pareto fronts | `continuous`, `linear-and-integer`, `graphs-and-routing`, `dynamic-programming`, `metaheuristics`, `black-box-tuning`, `atlas-coupling` |

```bash
python3 ml_lab/machine_learning/run_ml.py --path decisions
python3 ml_lab/optimisation/opt17_genetic_algorithm.py
python3 ml_lab/machine_learning/run_ml.py --path multi-agent      # actor-critic, then MAPPO
python3 ml_lab/machine_learning/ml24_lstm_rl_loop.py              # the 1.4 loop, frozen vs learning
```

Companion guides: [INFORMATION_SECURITY.md](INFORMATION_SECURITY.md) ·
[CRYPTOGRAPHY.md](CRYPTOGRAPHY.md).

---

## Contents

1. [Map of machine learning and optimisation in ATLAS](#1-map-of-machine-learning-and-optimisation-in-atlas)
2. [The paper's optimisation algorithm: the coupling BIP](#2-the-papers-optimisation-algorithm-the-coupling-bip---paper)
3. [Hyperparameter tuning](#3-hyperparameter-tuning---paper)
4. [Forecasting demand: LSTM and baselines](#4-forecasting-demand-lstm-and-baselines)
5. [Anomaly detection: Isolation Forest](#5-anomaly-detection-isolation-forest)
6. [Predicting acceptance: logistic regression and a Bayesian update](#6-predicting-acceptance-logistic-regression-and-a-bayesian-update)
7. [Reinforcement learning: dispatch, courier timing and supply](#7-reinforcement-learning-dispatch-courier-timing-and-supply)
8. [The digital twin: mirror, foresee, rehearse, guard](#8-the-digital-twin-mirror-foresee-rehearse-guard)
9. [Actor and critic networks](#9-actor-and-critic-networks)
10. [Multi-agent RL: two agents, one shared critic](#10-multi-agent-rl-two-agents-one-shared-critic)
11. [LSTM + RL as one loop: forecast, act, record, update, validate](#11-lstm--rl-as-one-loop-forecast-act-record-update-validate)
12. [Evaluating fairly: splits, seeds and statistics](#12-evaluating-fairly-splits-seeds-and-statistics---paper)
13. [Known gaps — exercises for students](#13-known-gaps--exercises-for-students)
14. [Suggested lesson plan](#14-suggested-lesson-plan)

---

## 1. Map of machine learning and optimisation in ATLAS

| Component | Technique | Problem type | Where | Tag |
|---|---|---|---|---|
| **Coupling decision** | Binary integer program; exhaustive enumeration, LP relaxation + risk-aware rounding + repair, branch-and-bound | Combinatorial optimisation | `atlas_sim/cluster.py` → `Sim.bip`, `Sim.eval_all`; `run_bip_timing.py`; `run_round2.py` | 📄 |
| **Hysteresis and switching cost** | Penalty term + 300 s dwell before merging back | Stability of repeated optimisation | `Sim.run`, `Params.switch_pen`, `Params.down_dwell_s` | 📄 |
| **Policy tuning** | Grid search on validation runs | Hyperparameter optimisation | `run_cluster.py` → `tune` | 📄 |
| **Traffic forecast** | LSTM / Bi-LSTM (PyTorch, Adam); Ridge-AR, persistence, seasonal naive baselines | Supervised regression (time series) | `atlas_sim/forecast.py`; `run_forecast.py`; `run_ood.py` | 📄 |
| **Anomaly detector** | Isolation Forest (100 trees, 256 samples) | Unsupervised outlier detection | `run_anomaly.py`; `Sim.score`; `FastIForest` | 📄 |
| **Demand forecast (starter)** | 1-layer LSTM, Adam, 75 epochs | Supervised regression | `starter/ml/forecast.py` | ✅ 🧪 |
| **Acceptance + driver anomaly (starter)** | Logistic regression; Isolation Forest | Classification; outlier detection | `starter/ml/discrete.py`; served by `starter/ml/serve.py` | ✅ 🧪 |
| **Dispatch policy (starter)** | Incremental action-value estimate per state + held-out approval gate | Contextual bandit | `starter/ml/rl.py` → `fit`, `approve` | ✅ 🧪 |
| **Ride dispatch (app)** | Softmax policy over 4 drivers, REINFORCE | Policy-gradient RL | `android-app/atlas_go/intelligence.py`; `training/rl_sim.py` → `train_ride` | ✅ 🧪 |
| **Courier timing (app)** | Tabular Q-learning, ε-greedy | Value-based RL | `training/rl_sim.py` → `train_food`; `intelligence.courier_plan` | ✅ 🧪 |
| **Driver supply (app)** | Tabular agent with full-information (hindsight) updates | RL / online learning | `training/city_sim.py` → `run_rl` | ✅ 🧪 |
| **Surge forecaster (app)** | LSTM written in numpy with a hand-written Adam step | Supervised regression | `training/city_sim.py` → `LSTM.step` | ✅ 🧪 |
| **Acceptance (app)** | Beta(9, 1) prior, Bernoulli updates | Bayesian estimation | `intelligence.acceptance` | ✅ |
| **Learning lab (app)** | On-device REINFORCE retraining, never used to dispatch | Policy-gradient RL | `intelligence.LearningLab` | ✅ |
| **Digital twin (app, 1.3)** | Mirror with fidelity score; 30-min foresight from the outlook; Monte Carlo rehearsal | Simulation-based planning | `atlas_go/twin.py` → `mirror`, `foresee`, `ratio_30`, `rehearse` | ✅ 🧪 |
| **Agent 1 · dispatch (app, 1.3)** | Rehearses Layer 1's top-3 drivers (200 rollouts), lowest 30-min total wait | Planning on top of a learned policy | `twin.agent1`, `twin.decide_ride` | ✅ 🧪 |
| **Agent 2 · pricing + moves (app, 1.3)** | Three rehearsed plans per area, capped surge ×2.0 | Planning / constrained optimisation | `twin.agent2`, `twin.driver_hint` | ✅ 🧪 |
| **Agent 3 · Guardian (app, 1.3)** | Hard limits, time budget, fallback to Layer 1, 500-rollout re-test | Runtime shield (safe RL) | `twin.check_dispatch`, `check_price`, `retest_pricing`, `fault_drill` | ✅ |
| **Live LSTM (app, 1.4)** | 24 h → 16 hidden → 6 h, pure Python inference every city hour | Time-series regression | `atlas_go/loop.py` → `lstm_hidden`, `head`, `Loop.forecast`; `training/export_lstm.py` | ✅ 🧪 |
| **Forecast-aware supply agent (app, 1.4)** | Q over (calendar, LSTM level); hindsight updates every hour | Value-based RL | `Loop.choose`, `Loop.step` | ✅ 🧪 |
| **Continuous retraining (app, 1.4)** | Nightly LSTM head refit + agent challenger; champion/challenger validation | Online learning with validation | `Loop.daily_update` | ✅ 🧪 |
| **Actor-critic (lab)** | Actor network + critic network V(s), advantage r − V(s) | Policy-gradient RL | `ml_lab/machine_learning/ml22_actor_critic.py` | 🎓 |
| **Two agents, one critic (lab)** | IPPO vs MAPPO (centralised critic, decentralised actors) | Multi-agent RL | `ml_lab/machine_learning/ml23_mappo_shared_critic.py` | 🎓 |

---

## 2. The paper's optimisation algorithm: the coupling BIP — 📄 Paper

### 2.1 The decision

The evaluated application has six modules (`atlas_sim/traffic.py`):

| Module | Gateway | Catalogue | Cart | Inventory | Payment | Order |
|---|---|---|---|---|---|---|
| Visit ratio *v<sub>i</sub>* | 1.00 | 1.00 | 0.45 | 0.35 | 0.18 | 0.15 |
| Demand *d<sub>i</sub>* (core-ms per visit) | 0.5 | 2.0 | 1.5 | 1.5 | 4.0 | 3.0 |

The decision is a vector **c ∈ {0,1}<sup>6</sup>**: *c<sub>i</sub>* = 0 keeps module *i* inside the
monolith process (tight), *c<sub>i</sub>* = 1 runs it as its own autoscaled service (loose). All zeros
is a monolith, all ones is microservices, anything else is **hybrid**. There are 2<sup>6</sup> = 64
candidates.

### 2.2 Objective and constraints

`Sim.eval_all` predicts four quantities for every candidate at the forecast load λ\*:

| Quantity | Model (in `eval_all`) | Meaning |
|---|---|---|
| Monolith utilisation ρ<sub>m</sub> | λ · Σ<sub>tight</sub> *v<sub>i</sub>d<sub>i</sub>* / (1000 · 16 cores) | How busy the shared process is; exactly linear in **c** |
| Latency *L* | base + M/M/1-style monolith term *D<sub>m</sub>*/(1 − ρ<sub>m</sub>) + per-service time + network hop for every loose call | End-to-end request latency |
| Cost *C* | 16 monolith cores (if any module is tight) + replicas × (pod + sidecar) + fixed cost per service + network cost per remote call | Cores used |
| Risk *R* and availability *A* | Crash probability × **blast radius**: a crash in the monolith takes down the biggest tight module's traffic; a loose module only its own | Expected failed requests |

`Sim.bip` then solves

> **minimise** J(**c**) = α·L/L₀ + β·C/C₀ + γ·γ<sub>s</sub>·R/R₀ + κ·‖**c** − **c**<sub>now</sub>‖₁
>
> **subject to** ρ<sub>m</sub> ≤ ρ<sub>max</sub> = 0.85, L ≤ 200 ms SLA, replicas ≤ 40 per service, A ≥ 0.99

L₀, C₀, R₀ are the all-monolith values at a reference load (650 req/s), so the three terms are
comparable. The last term is a **switching cost** (κ = `switch_pen`, tuned to 0.02): moving a
module is not free, so the optimiser changes the deployment only when it pays. Crash probability is
p₀ = 10⁻⁴ per epoch, plus a logistic overload term when the host utilisation passes 0.9, plus an
**anomaly term** p<sub>a</sub>/(1 + e<sup>−20(a − 0.7)</sup>) on the module the Isolation Forest blames (§5).

What the optimiser chooses as load rises (from `python3 ml_lab/ml_optimisation_lab.py --section 1`):

| Load (req/s) | c (G C Ca I P O) | Shape |
|---|---|---|
| 300 – 2000 | 000000 | monolith: one process is cheapest |
| 2500 | 000010 | hybrid: Payment out |
| 3000 | 000011 | hybrid: Payment, Order out |
| 4000 | 010000 | hybrid: Catalogue out |
| 6000 | 010010 | hybrid: Catalogue, Payment out (29 of 64 candidates feasible) |
| 9000 | 011010 | hybrid: Catalogue, Cart, Payment out |

At 6000 req/s the all-monolith option is infeasible (ρ<sub>m</sub> = 1.83) and all-microservices is
feasible but costs J = 6.06 against 5.16 for the hybrid choice. In the 30 test runs ATLAS spent 81 %
of the time tight, 18 % hybrid and 0.5 % fully loose (`results/cluster.json`, `ablation` → `mode_share`).

### 2.3 How one decision runs (`Sim.run`, every 5 s)

1. **Forecast** — λ\* = max(current load, LSTM 5-min forecast). Planning for the forecast is what lets
   pods start before a flash sale arrives (§4).
2. **Anomaly score** — `Sim.score` runs the Isolation Forest on telemetry and attributes the anomaly to
   the module whose measured demand deviates most.
3. **Optimise** — `Sim.bip` (or `fsm_thresholds` in the ablation).
4. **Override** — score ≥ 0.9 → emergency, every module loose; score ≥ 0.7 → force the blamed module out.
5. **Hysteresis** — extracting happens at once; merging back waits until the lower configuration has
   persisted for 300 s (`down_dwell_s`). Without this the optimiser oscillates.
6. **Apply** — `Sim.apply`: new pods start (8–30 s) while the module keeps running inside the monolith
   (dual-run); the hand-over costs a 40 ms state barrier measured in the prototype.

### 2.4 Solving it: three methods

| Method | Paper phase | How | Where |
|---|---|---|---|
| **Exhaustive enumeration** | Phase 2a | Evaluate all 2<sup>n</sup> candidates on the exact nonlinear model, vectorised; exact | `Sim.bip` (n = 6); `run_round2.solve_all` (E) |
| **Linearise + LP relaxation + risk-aware rounding + repair** | Phases 2b and 3 (Steps 19–23) | Linearise J and the constraints around **c**<sub>now</sub> by one-flip finite differences; solve the LP with 0 ≤ c ≤ 1 (HiGHS); round with a **risk-aware threshold** τ<sub>i</sub> = 0.5 − δ·risk<sub>i</sub>/max risk (δ = 0.3), so risky modules are extracted more readily; verify on the nonlinear model and greedily flip modules until feasible | `run_bip_timing.lp_round`; `run_round2.solve_all` (LP), `repair` |
| **Branch-and-bound** | exact reference | Mixed-integer solver (HiGHS via `scipy.optimize.milp`) on the linearised BIP | `run_bip_timing.py` |
| **Sequential linearisation + local search** | second revision | Re-linearise around each candidate until it stops changing, then 1-flip descent on the nonlinear objective | `run_round2.solve_refined`, `local_search` |

Measured solve times (median of 30 random instances, `results/bip_timing.json`):

| Modules n | Enumeration | Branch-and-bound | LP + rounding | LP gap to optimum (median) |
|---|---|---|---|---|
| 6 | 0.16 ms | 9.0 ms | 2.3 ms | 3.7 % |
| 16 | 11.9 ms | 8.8 ms | 2.8 ms | 0 % |
| 100 | — | 12.3 ms | 3.4 ms | 0 % |
| 200 | — | 59.9 ms | 4.2 ms | 0.12 % |
| 500 | — | 401 ms (p95 759 ms) | 6.4 ms | 0.23 % |

Enumeration is the right tool for six modules (0.27 ms per decision inside the simulator) and
impossible at 50. The LP method was feasible in all 30 instances at every size.

**Is the linearisation good enough?** `run_round2.py` replays 32 400 decision states recorded in the
30 test runs and compares each method with the exact nonlinear optimum (`results/round2.json`,
`formulation_sim`): the linearised BIP and the LP method agree with the exact choice in 96.5 % and
96.4 % of states and are always feasible after repair. On the hardest states (where the exact answer
is hybrid) the LP method agrees 78 % of the time, and sequential linearisation narrows the gap further
(`formulation_synth2`). Students should notice both halves: excellent on the paper's workload, weaker
on states built to be hard.

### 2.5 What the optimiser is worth (ablation, 30 test runs)

| Variant | p99 latency | SLA violations | Relative cost | Transitions |
|---|---|---|---|---|
| **ATLAS (full)** | **90.0 ms** | **0.12 %** | 1.30 | 7.6 |
| BIP replaced by fixed thresholds | 121.1 ms | 0.23 % | 1.49 | 15.0 |
| No hybrid mode (all tight or all loose) | 127.0 ms | 0.25 % | 1.34 | 13.0 |
| No hysteresis | 105.4 ms | 0.30 % | 1.23 | 18.2 |
| No LSTM forecast (reactive) | 92.6 ms | 0.13 % | 1.29 | 6.9 |
| No anomaly detector | 89.2 ms | 0.11 % | 1.30 | 7.1 |

Source: `results/cluster.json` → `ablation`. The optimiser and the hybrid choices it makes carry most of
the benefit; hysteresis keeps it stable. For comparison, all-microservices with a tuned autoscaler
has p99 129.6 ms at relative cost 1.67, and the monolith 3.56 s at 1.00.

### 2.6 Where the BIP is used — and where it is not

| Place | Uses the BIP? | Notes |
|---|---|---|
| `atlas_sim/cluster.py` (paper simulator) | **Yes** — `Sim.bip` every 5 s in policy `atlas` | Six-module e-commerce application |
| `run_cluster.py`, `run_vehicle.py`, `run_round2.py` | **Yes** — through `Sim` | Main comparison, ablation, load and sensitivity sweeps, connected-vehicle case study |
| `run_bip_timing.py` | **Yes** — solver benchmark | Synthetic instances, n = 6 … 500 |
| `prototype.zip` → `proto_run.py` | Executes one decision | Measures the tight ↔ loose hand-over of `PaymentModule` and crash recovery; the switch is commanded by the experiment, not by the BIP |
| Server starter, ATLAS Go app | **No** | They use the learners in §4–§7. 🎓 Exercise 1 in §13 maps the BIP onto the ride-hailing services |

---

## 3. Hyperparameter tuning — 📄 Paper

Every policy is tuned before testing, on **validation** runs (seeds 101–110) that never appear in the
test set (seeds 1–30). `run_cluster.tune` runs a **grid search**: score = SLA-violation % + failed %,
ties within 0.02 broken by lower cost.

| Policy | Grid | Chosen |
|---|---|---|
| ATLAS | switch_pen ∈ {0.02, 0.05, 0.1} × ρ<sub>max</sub> ∈ {0.75, 0.85} × HPA target ∈ {0.6, 0.7} (12 points) | 0.02, 0.85, 0.7 |
| Microservices, HANSEL-like | HPA target ∈ {0.5 … 0.8} × scale-down window ∈ {120, 300 s} | 0.5, 120 s |
| PHYBRID-like, XSCALE-like | same grid | 0.6, 120 s / 0.6, 300 s |

Tuning the baselines as carefully as ATLAS is what makes the comparison fair.

---

## 4. Forecasting demand: LSTM and baselines

**Paper (📄, `atlas_sim/forecast.py`, `run_forecast.py`).** One year of per-minute traffic with 48
flash sales; split 70/15/15 % by time (train / validation / test). Input: the last 60 minutes of eight
telemetry fields plus calendar features (sin/cos of hour and weekday). Output: log-load 5, 15 and 60
minutes ahead.

- **Model:** `LSTMForecaster`, 2 layers × 128 units, dropout 0.2 (Bi-LSTM variant too).
- **Training is optimisation:** minimise mean-squared error with **Adam** (lr 10⁻³), mini-batches of
  64, **gradient clipping** at norm 1.0, **early stopping** with patience 10 on validation MSE, keeping
  the best weights (`train`).
- **Baselines:** persistence, seasonal naive (same minute yesterday), Ridge regression on 60 lags of log-load, the same minute yesterday and calendar features (`fit_ar`).

| 5-min-ahead test | MAE (req/s) | RMSE | MAPE |
|---|---|---|---|
| **LSTM** | **51.7** | 98.7 | 14.8 % |
| Bi-LSTM | 53.5 | 104.5 | 14.8 % |
| Ridge-AR | 57.5 | 151.4 | 15.1 % |
| Persistence | 72.2 | 120.2 | 19.2 % |
| Seasonal naive | 111.8 | 313.3 | 35.1 % |

Source: `results/forecast.json`. During flash sales the error is much larger (MAE 745 req/s), which is
why ATLAS plans for max(load, forecast) rather than the forecast alone. `run_ood.py` tests
out-of-distribution traffic and other nodes.

**Server starter (✅ 🧪, `starter/ml/forecast.py`).** `DemandLSTM`: one LSTM layer of 12 units over a
12-step window of trip counts, Adam (lr 0.015), 75 full-batch epochs on a synthetic daily cycle; served
by `serve.py` → `score`.

**ATLAS Go (✅ 🧪, `training/city_sim.py`).** An LSTM written in numpy, including the Adam update by
hand (`LSTM.step`: first and second moment estimates, bias correction) — the clearest place in the
repository to read Adam line by line.

**ATLAS Go 1.4 (✅ 🧪, `training/export_lstm.py` → `atlas_go/lstm_weights.py`, `atlas_go/loop.py`).** A compact
LSTM — 24 hours in, 16 hidden units, demand ÷ ordinary demand for the next 1–6 hours — trained in numpy on
the supply agent's **experience log** (served trips, unserved requests, boosts) plus 30 calendar inputs
(hour and weekday on the unit circle, 11 event tags, now and 3 hours ahead). Held out on July–December 2026:
next-hour error 9.3 % (surge recall 0.81, precision 0.65). The phone runs it in pure Python
(`lstm_hidden`, `head`); its forecast matches the numpy model to 2 × 10⁻⁶. See §11 for the loop it drives.

The command-line lab (§5 there) fits the same 5-minute-ahead problem with a linear AR(30) model using
plain gradient descent, Adam and the closed-form least-squares solution, with early stopping.

---

## 5. Anomaly detection: Isolation Forest

An Isolation Forest builds random trees by picking a random feature and a random split value until
each point is alone. **Anomalies are isolated in fewer splits**, so a short average path length means a
high score s(x) = 2<sup>−E[h(x)]/c(n)</sup>. It needs **no labels**.

| Where | Data | Settings | Result |
|---|---|---|---|
| 📄 `run_anomaly.py` | 8 telemetry fields; 5 injected anomaly types (CPU, memory, downstream, flood, network/disk) | 100 trees, 256 samples, contamination 0.05; labels used only for evaluation | ROC-AUC 0.9999, F1 0.975 (10 seeds) |
| 📄 `Sim.score` | Telemetry synthesised from simulator state | Score normalised to 0–1; alert 0.7, emergency 0.9 | Feeds the BIP's risk term (§2.2) |
| 📄 `FastIForest` | — | Re-implements scikit-learn's `score_samples` for one row, about 50× faster | Shows the algorithm without the library |
| ✅ 🧪 `starter/ml/discrete.py` | Driver (distance km, speed km/h) | 35 trees, contamination 0.03 | Flags implausible driver telemetry per scoring request |

The ablation in §2.5 shows the detector barely changes the average result; `run_round2.py`
(`anomaly`) builds the two scenarios where it matters — an anomaly at peak load, and one that precedes
a crash of the same module.

---

## 6. Predicting acceptance: logistic regression and a Bayesian update

- **Server starter (✅ 🧪, `discrete.py`)** — logistic regression on (distance, speed) predicts whether a
  driver accepts an offer; evaluated with the **Brier score** (calibration), returned per driver by
  `serve.py`.
- **ATLAS Go (✅, `intelligence.acceptance`)** — for each registered driver, a **Beta(9, 1) prior** updated
  with that driver's own accepts and declines: posterior mean (accepted + 9)/(offered + 10). A new
  driver starts at 0.9 and the estimate moves as evidence arrives — Bayesian estimation in one line.

---

## 7. Reinforcement learning: dispatch, courier timing and supply

**Ride dispatch — REINFORCE (✅ 🧪, `intelligence.py`, `training/rl_sim.py`).** For each ride, four
candidate drivers; features φ = [−ETA/5, acceptance, −surge·last-free-driver, −surge]; policy
π(a) = softmax(w·φ<sub>a</sub>). Reward (arrives after the decision): −pickup minutes − 10·cancelled −
shortage caused by pulling the last driver out of a zone about to surge. Update:
w ← w + η (r − b)(φ<sub>a</sub> − E<sub>π</sub>[φ]) with a running-average baseline b (variance reduction).
After 30 000 episodes the bundled policy v1.4 costs 5.38 expected minutes against 6.42 for "send the
nearest driver"; `LearningLab` retrains it from zero on the phone and compares, but never dispatches
with the candidate.

**Courier timing — Q-learning (✅ 🧪, `rl_sim.train_food`).** State: kitchen slack = preparation estimate
− courier travel (−2 … 18 min). Action: wait 0 … 16 min before sending the courier. Reward:
−0.6·courier idle − 1.2·food waiting − 0.15·total time. ε-greedy exploration decaying to 0.03; step
size 1/N(s, a), floored at 0.02. The learned table (`learned.COURIER_DELAY`) is what `courier_plan` uses in the app.

**Driver supply — tabular agent (✅ 🧪, `city_sim.run_rl`).** Every hour, choose a boost of 0–150 % extra
drivers; reward −unserved riders − 0.25·idle extra drivers. Because the experience log records the
uncensored demand, the agent updates **every** action in hindsight (full-information learning), not
just the one it took.

**Supply agent 1.4 — the agent acts on the LSTM (✅ 🧪, `loop.py`).** The state is the calendar context
*and the LSTM's forecast level for the coming hour* (8 levels); the action is the same 0–150 % boost.
Trained with the same hindsight updates on the LSTM's forecasts, it costs 18 % less than the
calendar-only agent on the held-out half-year (29,896 vs 36,343; no boost: 52,965). §11 shows it running.

**Server starter (✅ 🧪, `starter/ml/rl.py`).** A two-state, two-action **contextual bandit**: an
incremental action-value estimate per (demand bucket, action) from recorded trips; `approve` refuses a
candidate unless every state has ≥ 8 held-out samples and its reward is not below the baseline action.
This **offline approval gate** is the safety pattern the app's learning lab mirrors.

---

## 8. The digital twin: mirror, foresee, rehearse, guard

**What.** A digital twin is a simulation that is kept in step with a real system and used to try
decisions before they are made. ATLAS Go 1.3 adds one for Cork (`atlas_go/twin.py`, ✅ 🧪) as a separate
**Layer 2** on top of the learned models (Layer 1), which it only *reads*:

| Step | What it does | Code | Measured (ML 21) |
|---|---|---|---|
| **Mirror** | Copies every driver, the active car and the courier; *fidelity* = how well positions are known (registered drivers with only a home area count 0.6) | `mirror` | 1.00 with only simulated drivers |
| **Foresee** | Demand ratio for the next 30 minutes per pickup place, from Layer 1's calendar-aware outlook | `ratio_30`, `foresee`, `extra_requests` | error 0.12–0.16 in festival weeks vs 0.43–0.65 for "last hour again" |
| **Rehearse — Agent 1** | Plays each of Layer 1's top-3 drivers 200 times: rider wait, declines, and riders left waiting if a busy area loses its last car; sends the lowest total wait | `rehearse`, `agent1` | 200 rollouts agree with a 5,000-rollout reference 100 % of the time (5 rollouts: 72–100 %) |
| **Rehearse — Agent 2** | Three plans per area every 5 min — keep prices; surge only; small surge + move idle cars — scored by wait + 1.5 × price jump + empty km | `agent2`, `driver_hint` | St Patrick's 13:00, City Centre: wait 11.4 → 4.2 min with ×1.4 and 2 moved cars |
| **Guard — Agent 3** | Checks every decision against hard limits (Layer 1's top 3 only, not declined/offline, pickup ≤ Layer 1's + 8 min, price ×1.0–×2.0 and ≤ twin's expectation + 0.5, 250 ms budget); blocks, falls back to Layer 1, re-tests the agent 500 times before handing back | `check_dispatch`, `check_price`, `retest_pricing`, `fault_drill`, `decide_ride` | 3,000 of 3,000 injected faults caught; 0 false alarms on 6,000 normal decisions |

**Why.** Learned policies see a snapshot (*"which driver now?"*); the twin asks *"what will this do to the
city in 30 minutes?"* before anything reaches a phone. The Guardian is a **runtime shield**: it does not
optimise, it keeps a narrow, testable promise — an agent's mistake is caught before it reaches a rider,
and the service falls back to the tested baseline instead of failing.

**How it connects.** `decide_ride` returns Layer 1's answer (`intelligence.choose`, base fare) whenever
Layer 2 is off, an agent is being re-tested, or the Guardian blocks. A unit test checks that
`intelligence.py` and `learned.py` are byte-identical to 1.2.0.

Lab: `ml_lab/machine_learning/ml21_digital_twin.py` · Explorer: [ML & Optimisation → Digital twin](https://fullscipts.github.io/ATLAS/#ml-twin) ·
UML: [ML catalogue → Digital twin](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/docs/UML_BLUEPRINT.md#uml-ml-twin)

---

## 9. Actor and critic networks

**What.** An **actor** is a network that outputs the policy π(a | s); a **critic** is a second network that
predicts the value V(s) of a situation. The actor is trained with the **advantage** A = r − V(s)
(one-step) or A = G<sub>t</sub> − V(s<sub>t</sub>) (return to go):

```text
actor   θ ← θ + η_a · A · ∇θ log π_θ(a | s)          "do more of choices that beat the critic's expectation"
critic  φ ← φ + η_c · (G − V_φ(s)) · ∇φ V_φ(s)       "predict how good this situation is, before choosing"
```

**Why.** REINFORCE (§7) uses one running average b as the baseline. It cannot tell an easy situation
(three cheap, willing drivers) from a hard one (only far, reluctant drivers), so most of r − b is about the
situation, not the choice. A critic that reads the whole situation removes that part: the remaining
advantage is the credit due to the action, so the gradient is less noisy.

**How in ATLAS (lab, 🎓 on 🧪 data).** `ml22_actor_critic.py` learns ride dispatch on the app's own
environment (`intelligence._candidates`, the same delayed reward as `LearningLab.train`):

- actor: one small network scores every candidate driver (4 features → 8 tanh → 1), softmax over drivers;
- critic: V(s) from all four candidates (16 inputs → 16 tanh → 1);
- evaluated on the same 300 held-out situations as the explorer's REINFORCE lab.

| Rides trained | REINFORCE + baseline | Actor-critic (A2C) |
|---|---|---|
| 1,000 | 5.64 min | 5.52 min |
| 2,000 | 5.62 | **5.48** (within 0.1 of v1.4) |
| 8,000 | 5.47 | **5.34** |

Policy v1.4 (30,000 rides): 5.38 min; nearest driver: 6.42. Variance of the learning signal: r − b 23.4,
r − V(s) 18.9. In the app, dispatch is still the REINFORCE policy v1.4 plus Agent 1's rehearsal; the
actor-critic is the natural next step (§13, gap 5).

Explorer: [ML & Optimisation → Actor & critic](https://fullscipts.github.io/ATLAS/#ml-actorcritic) ·
UML: [ML catalogue → Actor & critic](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/docs/UML_BLUEPRINT.md#uml-ml-actorcritic)

---

## 10. Multi-agent RL: two agents, one shared critic

**What.** When several agents share one reward, each agent's return also depends on what the others did.
**Centralised training, decentralised execution (CTDE)** handles this: during training one **shared
critic** V(s<sub>global</sub>) sees the whole city; at run time each actor acts on its **own** view.
**MAPPO** (multi-agent PPO) trains every actor with advantages from that shared critic and PPO's clipped
objective:

```text
ratio   ρ = π_new(a | o_i) / π_old(a | o_i)
loss_i  = −E[ min( ρ · A,  clip(ρ, 1 − ε, 1 + ε) · A ) ],   A = G_t − V_shared(s_t),  ε = 0.2
```

**IPPO** is the same but each agent fits its own critic on its own observation.

**How in ATLAS (lab, 🎓).** The proposal behind ATLAS Go 1.3 has exactly two learning agents with one team
reward — rider wait + unmet demand + empty km + price jumps. In the app they are rehearsal planners
(§8); `ml23_mappo_shared_critic.py` trains learned versions in a three-zone twin (Mardyke, City Centre,
Kent Station) where a concert ends at the Mardyke in the second half of the hour:

- **Agent 2 · pricing + moves** sees zone supply and the concert forecast: do nothing, move a car from
  Kent or the Centre to the Mardyke, or a capped ×1.3 surge;
- **Agent 1 · dispatch** sees only its idle cars: serve a City Centre rider with the Centre, Mardyke or Kent car;
- **shared critic** sees everything (cars, busy cars, forecast, time, surge).

| Policy (500 test hours) | Team cost per hour |
|---|---|
| Nearest car, never reposition | 140.9 |
| Random | 130.3 |
| IPPO (own critics) | 112.5 ± 3.7 |
| MAPPO (one shared critic) | 113.3 ± 5.0 |

| Spread of advantages (2nd half of training) | Agent 1 | Agent 2 |
|---|---|---|
| IPPO | 29.9 | 18.1 |
| MAPPO | **17.4** | 17.4 |

Both learn to move cars to the Mardyke before the concert and to keep its car there (about 20 % better than
the heuristic). The shared critic cuts the noise in Agent 1's learning signal by about 40 % — Agent 1 cannot
see the concert, the critic can — and MAPPO improves faster in mid-training; in this small twin both end at
similar policies. Honest takeaway: a shared critic is about *credit assignment and variance*, which matters
more as agents and partial observability grow.

Explorer: [ML & Optimisation → Two agents, one critic](https://fullscipts.github.io/ATLAS/#ml-marl) ·
UML: [ML catalogue → Multi-agent RL](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/docs/UML_BLUEPRINT.md#uml-ml-marl)

---

## 11. LSTM + RL as one loop: forecast, act, record, update, validate

**What.** Until 1.3, the LSTM and the RL agents met only offline: the agent's experience log trained the
LSTM in the simulation, and the phone used fixed tables. ATLAS Go 1.4 closes the loop on the phone
(`atlas_go/loop.py`, ✅ 🧪):

```text
every city hour   LSTM(last 24 h of served, unserved, boost, calendar)  →  demand for the next 6 h
                  supply agent: state = (calendar, LSTM level)          →  extra drivers 0–150 %
                  city reveals demand                                   →  experience log (14 days)
                  challenger Q-table learns with hindsight from the log
every night       LSTM output layer refitted on logged hidden states    →  challenger LSTM
                  validation: LSTM on the last 24 held-out hours; agent replayed on the last 7 days
                  keep a challenger only if it is better  (champion / challenger)
```

**Why validate.** Continuous learning can make a model worse (noise, drift, a bad day). Each challenger
is compared with the current champion on data it was not trained on; a worse one is never deployed and
the reason is logged.

| Measured (ML 24) | Result |
|---|---|
| Four periods (Jazz, St Patrick's, Christmas, February) | loop 11,758 vs calendar agent 13,137 (−10.5 %) vs no boost 24,468; worse than the calendar table around St Patrick's and Christmas, better overall |
| Eight weeks, cost of the last two, learning on vs frozen | −15.7 % (Jan–Feb 2027), −1.5 % (May–Jun), −12.1 % (Sep–Oct) |
| Forecast error by horizon (28 days) | 13.4, 12.2, 11.7, 12.3, 13.2, 14.3 % for 1–6 h |
| A deliberately bad challenger (always +150 %) | replay cost 13,160 vs 2,177 → rejected; champion unchanged |

**Limits.** The city is simulated; on the phone only the LSTM's output layer is retrained (the recurrent
weights are retrained offline with `export_lstm.py`). The live forecast also feeds the dispatch policy's
surge feature (`AtlasGoApp.live_surge`).

Lab: `ml_lab/machine_learning/ml24_lstm_rl_loop.py` · Explorer: [ML & Optimisation → LSTM + RL loop](https://fullscipts.github.io/ATLAS/#ml-loop) ·
UML: [ML catalogue → LSTM + RL loop](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/docs/UML_BLUEPRINT.md#uml-ml-loop)

---

## 12. Evaluating fairly: splits, seeds and statistics — 📄 Paper

- **Separate data for each purpose:** forecaster trained, early-stopped and tested on disjoint time
  ranges; policies tuned on validation seeds 101–110, compared on test seeds 1–30.
- **Paired tests:** each test seed runs every policy on the same traffic; `run_cluster.compare` uses the
  **Wilcoxon signed-rank test** with the **rank-biserial correlation** as effect size.
- **Multiple comparisons:** `run_cluster.holm` applies the **Holm–Bonferroni** step-down correction.
- **Confidence intervals:** t-intervals over 30 runs (`stat_block`); **block bootstrap** over days for
  forecast errors (`forecast.block_bootstrap_ci`) because neighbouring minutes are correlated.

---

## 13. Known gaps — exercises for students

| # | Observation | Where | Exercise |
|---|---|---|---|
| 1 | The BIP is evaluated on a six-module e-commerce model, not on the ride-hailing services | `atlas_sim/traffic.py` | 🎓 Define *v<sub>i</sub>*, *d<sub>i</sub>* for gateway, trips, dispatch, ML scoring and run `Sim.bip` on them |
| 2 | Enumeration is exponential | `Sim.bip` | Replace it with `lp_round` for n = 20 and measure the decision time and the gap |
| 3 | The objective weights α = β = γ = 1 are fixed | `Params` | Sweep them and draw the latency–cost Pareto front |
| 4 | The LSTM's flash-sale error is 15× its error in normal traffic (MAE 745 vs 48 req/s) | `results/forecast.json` | Add the anomaly score or a surge flag as an input; or plan on an upper quantile (quantile loss) |
| 5 | REINFORCE needs thousands of episodes | `LearningLab` | Done as a lab (§9, ML 22: A2C reaches v1.4's level in a quarter of the rides); move the critic into `LearningLab` and compare on the phone |
| 6 | All app and starter learners are trained on simulated data | `training/`, `starter/ml/` | Discuss what would change with real logs: bias from the old policy (off-policy evaluation), drift, privacy |
| 7 | The bandit in `rl.py` has two states | `starter/ml/rl.py` | Extend the state with zone and hour; keep the approval gate |
| 8 | Agents 1 and 2 in the app plan by rehearsal; they do not learn | `twin.agent1`, `twin.agent2` | Replace them with the MAPPO actors of ML 23, keep the Guardian in front, and compare in the twin |
| 9 | Only the LSTM's output layer is retrained on the phone | `Loop.daily_update` | Add truncated backpropagation through time for the recurrent weights and validate as for the head |
| 10 | The loop validates on the last 24 hours / 7 days only | `HOLDOUT`, `REPLAY_HOURS` | Try longer windows and a significance test (§12) before accepting a challenger |
| 11 | The twin's foresight uses the calendar outlook, not the live LSTM | `twin.ratio_30` | Feed `Loop.now()` into `foresee` and measure Agent 2's plans again |

---

## 14. Suggested lesson plan

| Session | Topic | Use |
|---|---|---|
| 1 | Formulating a decision as optimisation | §2.1–2.2; explorer → Coupling BIP: move the load slider |
| 2 | Integer programming and relaxations | §2.4; lab section 4; explorer → Solvers |
| 3 | Stability: switching costs and hysteresis | §2.3, §2.5 ablation |
| 4 | Training as optimisation | §4; lab section 5; explorer → Forecasting (GD vs Adam) |
| 5 | Unsupervised anomaly detection | §5; explorer → Isolation Forest |
| 6 | Reinforcement learning | §7; explorer → RL: train REINFORCE live; read `train_food` |
| 7 | Honest evaluation | §3, §12; reproduce one row of the ablation |
| 8 | Digital twins and runtime shields | §8; ML 21; explorer → Digital twin: rehearse drivers, break the Guardian |
| 9 | Actor and critic networks | §9; ML 22; explorer → Actor & critic: train A2C against REINFORCE |
| 10 | Multi-agent RL with a shared critic | §10; ML 23; explorer → Two agents, one critic: IPPO vs MAPPO |
| 11 | Closing the loop: LSTM + RL with validation | §11; ML 24; explorer → LSTM + RL loop; ATLAS Go → How ATLAS learns → Run 7 city days |
