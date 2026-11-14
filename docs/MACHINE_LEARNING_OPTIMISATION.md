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

The decision is a binary vector $`\mathbf c\in\{0,1\}^{6}`$: $`c_i=0`$ keeps module $`i`$ inside the monolith process (tight), whereas $`c_i=1`$ runs it as an autoscaled service (loose). All zeros is a monolith, all ones is microservices, and a mixture is **hybrid**. Six binary choices have $`2^6=64`$ possible configurations.

### 2.2 Objective and constraints

`Sim.eval_all` predicts four quantities for every candidate at the forecast load $`\lambda^*`$:

| Quantity | Model (in `eval_all`) | Meaning |
|---|---|---|
| Monolith utilisation ρ<sub>m</sub> | λ · Σ<sub>tight</sub> *v<sub>i</sub>d<sub>i</sub>* / (1000 · 16 cores) | How busy the shared process is; exactly linear in **c** |
| Latency *L* | base + M/M/1-style monolith term *D<sub>m</sub>*/(1 − ρ<sub>m</sub>) + per-service time + network hop for every loose call | End-to-end request latency |
| Cost *C* | 16 monolith cores (if any module is tight) + replicas × (pod + sidecar) + fixed cost per service + network cost per remote call | Cores used |
| Risk *R* and availability *A* | Crash probability × **blast radius**: a crash in the monolith takes down the biggest tight module's traffic; a loose module only its own | Expected failed requests |

`Sim.bip` solves the following constrained multi-objective binary optimisation problem (the coefficients and reference scales are defined immediately below):

```math
\begin{aligned}
\min_{\mathbf c\in\{0,1\}^{n}}\quad J(\mathbf c)
&=\alpha\frac{L(\mathbf c)}{L_0}+\beta\frac{C(\mathbf c)}{C_0}
+\gamma\gamma_s\frac{R(\mathbf c)}{R_0}
+\kappa\|\mathbf c-\mathbf c_{\mathrm{now}}\|_1,\\
\text{subject to}\quad &\rho_m(\mathbf c)\le 0.85,\\
&L(\mathbf c)\le 200\,\mathrm{ms},\\
&n_{\mathrm{replicas},i}(\mathbf c)\le40\quad\forall i,\\
&A(\mathbf c)\ge 0.99.
\end{aligned}
```


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

1. **Forecast** — $`\lambda^*=\max(\lambda_{\mathrm{current}},\hat\lambda_{\mathrm{LSTM},5\mathrm{min}})`$. Planning for the forecast is what lets
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
the following two-stage softmax rule:

```math
z_a=\mathbf w^\top\boldsymbol\phi_a
```

```math
\pi(a)=\frac{e^{z_a}}{\sum_{j=1}^{K}e^{z_j}}
```

**What?** The first equation scores driver a using feature weights; the second converts all K drivers' scores into probabilities that sum to one. **Why?** This lets the dispatch policy favour good drivers while keeping stochastic choices for training. **How?** If two drivers score 2 and 1, exponentiate both: their probabilities are about 0.731 and 0.269. The symbols are: w = learned weights, phi_a = features of driver a, z_a = score, pi(a) = selection probability.

Reward (arrives after the decision): −pickup minutes − 10·cancelled −
shortage caused by pulling the last driver out of a zone about to surge. Update:
$`\mathbf w\leftarrow\mathbf w+\eta(r-b)(\boldsymbol\phi_a-\mathbb E_{a'\sim\pi}[\boldsymbol\phi_{a'}])`$ with a running-average baseline $`b`$ (variance reduction).
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

**What.** An **actor** is a network that outputs $`\pi_\theta(a\mid s)`$; a **critic** estimates $`V_\phi(s)`$, the expected future return for a state. For a terminal one-step action the advantage may be $`A=r-V_\phi(s)`$; for a sampled episode, $`A_t=G_t-V_\phi(s_t)`$. A basic actor–critic step is:

```math
\begin{aligned}
\theta&\leftarrow\theta+\eta_a A_t\nabla_\theta\log\pi_\theta(a_t\mid s_t),\\
\phi&\leftarrow\phi+\eta_c(G_t-V_\phi(s_t))\nabla_\phi V_\phi(s_t).
\end{aligned}
```

The actor reinforces actions that beat the critic's prediction; the critic learns to predict the return. For a nonterminal one-step temporal-difference update, use $`A_t\approx r_t+\gamma V_\phi(s_{t+1})-V_\phi(s_t)`$ instead.

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
**MAPPO** (multi-agent PPO) uses a shared critic during training while each actor acts from its own observations. The PPO objective is easier to learn as four independent calculations.

**1. Probability ratio — how much more likely is the old action?**

```math
q_t=\frac{\pi_{\mathrm{new}}(a_t\mid o_{i,t})}{\pi_{\mathrm{old}}(a_t\mid o_{i,t})}
```

Here a_t is the action agent i took, o_{i,t} its observation, and q_t the new/old action-probability ratio (not the environment reward). If old probability is 0.40 and new probability is 0.60, q_t=1.5.

**2. Advantage — was that action better than predicted?**

```math
\widehat A_t=G_t-V_{\mathrm{shared}}(s_t)
```

G_t is realised discounted return; V_shared(s_t) is the shared critic's estimate from the global state. If return is 12 and predicted value 10, advantage = +2. If return is 8, advantage = -2.

**3. Clipped surrogate — stop rewarding excessively large probability changes.**

```math
u_t=\min\left(q_t\widehat A_t,\;\operatorname{clip}(q_t,1-\epsilon,1+\epsilon)\widehat A_t\right)
```

clip(x,l,u) returns l when x<l, u when x>u, otherwise x. With epsilon=0.2, ratio 1.5 and positive advantage 2, the terms are 3 and 2.4; take min = 2.4. This clipping affects the optimisation objective, not a hard bound on final policy behaviour.

**4. Loss — turn the benefit into something an optimiser can minimise.**

```math
\mathcal L_i^{\mathrm{clip}}=-\frac{1}{N}\sum_{t=1}^{N}u_t
```

N is the number of sampled decisions. The negative sign turns maximising the PPO surrogate into minimising a loss. MAPPO also normally optimises a critic loss and may include an entropy bonus. One training batch averages many positive and negative advantages.
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


---

# Part II — Standalone theory textbook: machine learning and optimisation

> **How to use this part:** This part is intentionally self-contained. It assumes no previous machine-learning course and does not require ATLAS source code. Read Chapters T1–T14 in order for theory, then return to §§1–14 above for the ATLAS implementation and experiments. The numbers in toy calculations below are illustrative, not empirical ATLAS measurements.

## Theory contents

- [T1. Mathematical prerequisites and notation](#t1-mathematical-prerequisites-and-notation)
- [T2. What learning means: tasks, data and generalisation](#t2-what-learning-means-tasks-data-and-generalisation)
- [T3. Supervised learning from first principles](#t3-supervised-learning-from-first-principles)
- [T4. Trees, ensembles, kernels and probabilistic learners](#t4-trees-ensembles-kernels-and-probabilistic-learners)
- [T5. Unsupervised learning, representation and anomalies](#t5-unsupervised-learning-representation-and-anomalies)
- [T6. Neural networks, gradients and sequence models](#t6-neural-networks-gradients-and-sequence-models)
- [T7. Forecasting, drift and online learning](#t7-forecasting-drift-and-online-learning)
- [T8. Reinforcement learning, policy gradients and multi-agent learning](#t8-reinforcement-learning-policy-gradients-and-multi-agent-learning)
- [T9. Optimisation foundations and continuous methods](#t9-optimisation-foundations-and-continuous-methods)
- [T10. Constraints, duality and integer optimisation](#t10-constraints-duality-and-integer-optimisation)
- [T11. Graph, scheduling, dynamic and heuristic optimisation](#t11-graph-scheduling-dynamic-and-heuristic-optimisation)
- [T12. Multi-objective, robust and safe decision-making](#t12-multi-objective-robust-and-safe-decision-making)
- [T13. Experimental design, statistical validity and reproducibility](#t13-experimental-design-statistical-validity-and-reproducibility)
- [T14. Fully worked integrated example, revision questions and glossary](#t14-fully-worked-integrated-example-revision-questions-and-glossary)

## T1. Mathematical prerequisites and notation

**Scalars, vectors and matrices.** A scalar is one number, such as demand $`d=120`$ rides/hour. A vector holds several related numbers, such as $`x=[\text{distance},\text{pickup delay},\text{surge}]`$. A matrix $`X\in\mathbb{R}^{n\times p}`$ contains $`n`$ observations and $`p`$ features. A training set is $`\mathcal D=\{(x_i,y_i)\}_{i=1}^n`$, with labels $`y_i`$; an unlabelled set has only $`x_i`$.

**Linear algebra.** The dot product $`w^\top x=\sum_jw_jx_j`$ scores a candidate; $`\|x\|_2=\sqrt{\sum_jx_j^2}`$ is Euclidean length; matrix multiplication $`Xw`$ produces all linear predictions. The transpose flips row/column orientation. A positive-semidefinite matrix $`H`$ obeys $`z^\top Hz\ge0`$, a key condition in convex optimisation.

**Probability.** $`P(A|B)=P(A\cap B)/P(B)`$ is conditional probability. Bayes' rule is

```math
P(H|E)=\frac{P(E|H)P(H)}{P(E)}
```

A random variable has expectation $`E[X]=\sum_x xP(X=x)`$ (or an integral for continuous $`X`$); variance is $`E[(X-E[X])^2]`$. Covariance tracks two variables changing together, but correlation does not prove causation.

**Derivatives.** A derivative is the local slope: for $`f(w)=(w-3)^2`$, $`f'(w)=2(w-3)`$. The gradient $`\nabla f`$ is the vector of slopes; the Hessian $`\nabla^2f`$ contains second partial derivatives. The chain rule makes neural-network backpropagation possible:

```math
\frac{dL}{dw}=\frac{dL}{d\hat y}\frac{d\hat y}{dw}
```

For $`L=(wx-y)^2/2`$, the gradient is $`(wx-y)x`$.

**Useful distributions.** Bernoulli models yes/no; binomial counts successes; Poisson models arrival counts in a fixed interval when assumptions fit; Gaussian models many continuous noise patterns; beta represents uncertainty about a Bernoulli success probability. If $`p\sim\mathrm{Beta}(\alpha,\beta)`$ and we see $`s`$ successes and $`f`$ failures, then $`p|\mathcal D\sim\mathrm{Beta}(\alpha+s,\beta+f)`$, with posterior mean $`(\alpha+s)/(\alpha+\beta+s+f)`$.

**Scale and units matter.** Never add milliseconds directly to dollars without normalising or defining explicit trade-off weights. Feature standardisation is $`z=(x-\mu_{\rm train})/\sigma_{\rm train}`$. Learn $`\mu,\sigma`$ *only from training data*; reusing test data leaks information.

**Toy example.** Candidate driver A has distance 2 km and acceptance probability 0.8; B has 1 km and 0.5. A score $`s=-1\cdot\text{distance}+4\cdot\text{acceptance}`$ yields A = 1.2 and B = 1.0. The coefficients encode a preference, not a universal truth.

## T2. What learning means: tasks, data and generalisation

A **model** is a parameterised function $`f_\theta(x)`$ mapping inputs to outputs. **Training** chooses parameters $`\theta`$ to minimise empirical loss $`R_{\rm train}(\theta)=\frac1n\sum_i\ell(f_\theta(x_i),y_i)`$. **Generalisation** asks whether the learnt rule works on previously unseen cases from the intended deployment distribution.

| Task | Input → output | Typical loss / criterion | ATLAS analogy |
|---|---|---|---|
| Regression | Features → real number | MAE, MSE | Predicted demand |
| Classification | Features → category/probability | Cross-entropy | Driver accepts? |
| Unsupervised clustering | Features → groups | Silhouette + domain utility | Demand zones |
| Anomaly detection | Telemetry → unusualness score | Precision-recall and detection delay | Fault signals |
| Forecasting | Historical series → future series | Rolling-origin MAE, RMSE | Upcoming surge |
| Contextual bandit | Context → immediate-reward action | Cumulative regret | Choose an offer |
| RL | State → sequential actions | Discounted return, constraints | Reposition supply |
| Optimisation | Decision variables + constraints → best feasible choice | Objective value and violation rate | Module coupling |

**Data pipeline:** define the target → collect consented/relevant observations → inspect missingness, duplicates, outliers and units → split data → fit preprocessing on training portion → fit model → tune on validation → freeze → evaluate once on held-out test → monitor after deployment. A label must be available *after* the event it describes; never smuggle future information into an input feature.

**Bias–variance intuition.** A model that always predicts the same demand is too simple (high bias). A model that memorises every training ride is unstable (high variance). For squared-error regression, expected prediction error decomposes conceptually into squared bias + variance + irreducible noise, under standard assumptions. Regularisation and more data often reduce overfitting; model capacity may reduce underfitting.

**Underfitting versus overfitting.** Training and validation both poor suggests underfitting; training excellent and validation poor suggests overfitting or distribution shift. Learning curves plot both errors as the amount of training data grows.

**Train/validation/test:** training fits weights; validation chooses hyperparameters, thresholds and checkpoints; test estimates final performance. In time series, split chronologically (no random reshuffle across future/past). For the same rider/driver appearing repeatedly, group-aware splits may be needed to prevent identity leakage.

## T3. Supervised learning from first principles

### T3.1 Linear regression

For $`x\in\mathbb R^p`$, predict $`\hat y=w^\top x+b`$ and minimise

```math
J(w,b)=\frac1{2n}\sum_{i=1}^n(\hat y_i-y_i)^2
```

Gradient descent takes $`w\leftarrow w-\eta\nabla_wJ`$, $`b\leftarrow b-\eta\partial J/\partial b`$. With a full-rank design matrix, ordinary least squares has $`\hat w=(X^\top X)^{-1}X^\top y`$; in practice prefer QR/SVD rather than explicitly inverting a matrix.

**Worked step:** one observation $`x=2,y=6`$, model $`\hat y=wx`$, start $`w=1`$, learning rate $`\eta=0.1`$. Loss $`L=(2-6)^2/2=8`$; gradient $`(2-6)2=-8`$; new weight $`w=1.8`$, new prediction $`3.6`$. The update moves toward 6.

**Ridge regression:** add $`\lambda\|w\|_2^2`$ to penalise large coefficients (normally leave intercept unpenalised). **Lasso:** add $`\lambda\|w\|_1`$, which can zero out coefficients. $`\lambda`$ is chosen on validation data.

### T3.2 Logistic regression and calibration

Logistic regression predicts $`p=P(y=1|x)=\sigma(w^\top x+b)`$, with sigmoid $`\sigma(z)=1/(1+e^{-z})`$. Learn by binary cross-entropy:

```math
L=-\frac1n\sum_i[y_i\log p_i+(1-y_i)\log(1-p_i)]
```

A 0.5 threshold is not mandatory. If a missed acceptance and a false acceptance have different costs, tune the decision threshold on validation data. **Calibration** means that of all predictions around 0.8, roughly 80% should succeed; the Brier score $`\frac1n\sum_i(p_i-y_i)^2`$ assesses probability quality.

**Example:** with logit $`z=\ln 3`$, $`\sigma(z)=0.75`$. If the driver declines ($`y=0`$), example cross-entropy is $`-\ln(0.25)=1.386`$; being confidently wrong is penalised.

### T3.3 Nearest neighbours and naive Bayes

**k-nearest neighbours (kNN)** finds training examples nearest to a query and takes a majority vote or distance-weighted average. Distances become meaningless when one unscaled feature dominates. Larger $`k`$ smooths predictions; smaller $`k`$ is more local but noisier.

**Naive Bayes** uses $`P(y|x_1,\dots,x_p)\propto P(y)\prod_jP(x_j|y)`$, assuming features are conditionally independent given the class. This assumption is often imperfect yet useful. Use log probabilities to avoid numerical underflow.

### T3.4 Metrics and imbalanced classes

For a positive class: precision $`=TP/(TP+FP)`$, recall $`=TP/(TP+FN)`$, specificity $`=TN/(TN+FP)`$, $`F_1=2PR/(P+R)`$. Accuracy can mislead when 99% of telemetry is normal. Confusion matrices must state the positive class and chosen threshold. ROC-AUC measures ranking across thresholds; PR-AUC is often more informative when positives are rare.

For regression, $`MAE=\frac1n\sum|y_i-\hat y_i|`$, $`RMSE=\sqrt{\frac1n\sum(y_i-\hat y_i)^2}`$. RMSE emphasises large errors. MAPE is unstable near zero true demand; use a clearly specified alternative such as WAPE or sMAPE where appropriate. Always report the metric's units and aggregation window.

## T4. Trees, ensembles, kernels and probabilistic learners

**Decision trees.** Recursively split the feature space: for example, *if pickup ETA ≤ 4 minutes, use branch A; otherwise branch B*. Classification splits can minimise Gini impurity $`1-\sum_kp_k^2`$ or entropy $`-\sum_kp_k\log p_k`$; regression splits often minimise squared error. Deep trees memorise; depth, leaf-size and pruning control complexity.

**Bagging and random forests.** Train many trees on bootstrap samples and average/vote. Random forests additionally sample a subset of features when splitting, reducing correlation among trees. Ensemble averaging frequently reduces variance, but can still inherit bias or dataset problems.

**Boosting.** Build an additive model $`F_m(x)=F_{m-1}(x)+\eta h_m(x)`$ in which each weak learner addresses the current loss/gradient. Gradient boosting can fit tabular data strongly; tune depth, learning rate and number of estimators, and use early stopping.

**Support vector machines.** A linear soft-margin classifier seeks a wide margin:

```math
\begin{aligned}
\min_{w,b,\xi}\tfrac12\|w\|^2+C\sum_i\xi_i,\quad \\
y_i(w^\top x_i+b)\ge1-\xi_i,\;\xi_i\ge0 
\end{aligned}
```

Kernel functions $`K(x,z)`$ implicitly compare nonlinear features (e.g. the RBF kernel $`\exp[-\gamma\|x-z\|^2]`$). Scale features and validate $`C,\gamma`$.

**Probabilistic estimation.** A frequentist point estimate gives one parameter value; a Bayesian posterior represents uncertainty given a prior and observed data. With a Beta(9,1) prior, 3 accepts and 2 declines give Beta(12,3) and mean $`12/15=0.8`$. This is the theory behind the app's acceptance updater.

**Selecting a model.** For small labelled tabular sets, try a regularised linear model and trees before deep learning; for long sequential structure, use temporal models. Interpretability, training cost, latency, calibration, failure cost and drift robustness are all selection criteria.

## T5. Unsupervised learning, representation and anomalies

**k-means:** choose $`k`$ cluster centres and minimise within-cluster squared distances $`\sum_i\min_j\|x_i-\mu_j\|^2`$. Alternate assigning points and recomputing centres. It prefers roughly spherical Euclidean clusters, is sensitive to scales and initialization, and does not automatically discover the correct number of zones.

**DBSCAN:** group points with sufficiently many neighbours within distance $`\varepsilon`$, leaving isolated points as noise. It can find irregular spatial shapes; its behaviour depends on distance metric, $`\varepsilon`$, min_samples, and uneven densities. Geographic coordinates require an appropriate geographic distance.

**PCA:** centre/scale features as appropriate; find orthogonal directions of greatest variance using eigendecomposition or SVD. Projection $`z=W_k^\top(x-\mu)`$ compresses dimensions. High explained variance does not necessarily mean high predictive value.

**Anomaly detection:** a rule-based method flags explicit limit violations; an Isolation Forest finds points quickly isolated by random splits; one-class SVM learns a boundary around normality; reconstruction methods flag unusually large reconstruction errors. Unlabelled anomaly scores are not calibrated event probabilities. Decide alert thresholds using realistic validation incidents, and report false alarms per hour, recall, detection delay and attribution accuracy.

**Isolation-Forest intuition:** a lone customer at 3 a.m. with 1,000 requests/minute usually needs fewer random splits to isolate than ordinary traffic. A short expected path length corresponds to greater anomaly score; however, seasonal or rare-but-legitimate events may also look unusual.

**Learning to rank:** rank driver candidates using relevance or expected utility; pointwise losses predict each candidate independently, pairwise losses compare two candidates, and listwise losses evaluate a whole ranked list. Beware selection bias: historical dispatch outcomes were observed only for drivers previously offered trips.

## T6. Neural networks, gradients and sequence models

A dense layer is $`h=\phi(Wx+b)`$. Multi-layer networks compose layers: $`\hat y=f_\theta(x)`$. ReLU $`\max(0,z)`$ gives nonlinearity; sigmoid maps to (0,1); softmax $`p_i=e^{z_i}/\sum_je^{z_j}`$ produces categorical probabilities. Backpropagation applies the chain rule from loss to every layer.

**Training loop:** initialise weights → take a mini-batch → forward pass → compute loss → backpropagate gradients → update parameters → validate → stop/checkpoint. Epoch = one pass over all training examples; batch size controls examples per update; learning rate controls update step.

**Optimisers.** Plain SGD: $`\theta_{t+1}=\theta_t-\eta g_t`$. Momentum: $`v_t=\beta v_{t-1}+g_t,\;\theta_{t+1}=\theta_t-\eta v_t`$. Adam:

```math
\begin{aligned}
m_t=\beta_1m_{t-1}+(1-\beta_1)g_t,\quad \\
v_t=\beta_2v_{t-1}+(1-\beta_2)g_t^2 
\end{aligned}
```


```math
\begin{aligned}
\hat m_t=m_t/(1-\beta_1^t),\quad \\
\hat v_t=v_t/(1-\beta_2^t),\quad \\
\theta_{t+1}=\theta_t-\eta\hat m_t/(\sqrt{\hat v_t}+\epsilon) 
\end{aligned}
```

Operations involving vector parameters are elementwise. Adam uses gradient-history estimates, not a guaranteed optimal step. Gradient clipping helps limit exploding gradients; dropout and weight decay regularise; early stopping limits overfitting.

**Why a recurrent model?** A feed-forward model sees the current snapshot; a recurrent network carries a hidden state encoding earlier observations. A vanilla RNN updates $`h_t=\tanh(W_xx_t+W_hh_{t-1}+b)`$, but repeated multiplication through time can cause vanishing/exploding gradients.

**LSTM equations.** For input $`x_t`$, previous hidden $`h_{t-1}`$, previous cell $`c_{t-1}`$, with concatenation $`[h_{t-1},x_t]`$:

```math
\begin{aligned}
f_t=\sigma(W_f[h_{t-1},x_t]+b_f),\quad \\
i_t=\sigma(W_i[h_{t-1},x_t]+b_i) 
\end{aligned}
```


```math
\begin{aligned}
\tilde c_t=\tanh(W_c[h_{t-1},x_t]+b_c),\quad \\
c_t=f_t\odot c_{t-1}+i_t\odot\tilde c_t 
\end{aligned}
```


```math
\begin{aligned}
o_t=\sigma(W_o[h_{t-1},x_t]+b_o),\quad \\
h_t=o_t\odot\tanh(c_t) 
\end{aligned}
```

The **forget gate** controls retained memory; the **input gate** controls newly written information; the **output gate** controls exposed information. Think of the cell as a notebook with erase, write and read controls.

**Worked LSTM gate step:** let old cell be 0.8, forget gate 0.5, input gate 0.25, candidate update 0.6. Then the new cell is $`c_t=0.5(0.8)+0.25(0.6)=0.55`$. This is a valid illustrative cell update because the candidate lies in $`[-1,1]`$.

**Sequence design:** a sliding input window of past 24 hours can predict next six hours; an encoder produces representations and an output head yields a multi-horizon forecast. Fit scalers and transforms on training history only; prevent overlapping future labels from leaking into the earlier split; choose between direct multi-step and recursive prediction. Bidirectional LSTMs are acceptable when the *whole input window* is already observed, but must never use data beyond the prediction time.

## T7. Forecasting, drift and online learning

**Classical baselines:** persistence ($`\hat y_{t+h}=y_t`$); seasonal naive ($`\hat y_{t+h}=y_{t+h-s}`$); moving averages; exponential smoothing ($`\ell_t=\alpha y_t+(1-\alpha)\ell_{t-1}`$); Holt trend; Holt–Winters trend + seasonality; autoregression $`\hat y_t=b+\sum_{j=1}^pw_jy_{t-j}`$. A sophisticated LSTM should beat meaningful baselines on the same horizons, not merely fit training curves.

**Stationarity** loosely means key statistical properties do not change over time. Real demand shows weekday cycles, holidays, special events, road incidents and shifts. Transformations (e.g. log1p) can stabilise scale, but inverse-transform predictions before evaluating in rides/hour.

**Concept drift:** $`P_t(X)`$ may change (covariate shift); $`P_t(Y|X)`$ may change (concept drift). Monitor prediction error, feature distributions, missingness and downstream service quality. Drift detection alone does not prove retraining helps.

**Online learning:** update after new observations arrive. A safe pipeline logs immutable event times, waits for delayed labels, uses bounded update steps, trains a challenger, compares against a champion on untouched holdout/replay data, deploys only after passing gates, and keeps rollback. Off-policy data are biased if actions affect which outcomes get observed; use careful logged-policy evaluation rather than treating all observations as independent randomised trials.

**Forecast → decision.** Predicting a surge is useful only if the resulting action improves fulfilled requests, wait times or cost. Report *decision-aware* evaluation: replace the forecaster while keeping the policy fixed, and compare downstream outcomes.

## T8. Reinforcement learning, policy gradients and multi-agent learning

**Markov decision process (MDP):** $`(\mathcal S,\mathcal A,P,r,\gamma)`$ contains states, actions, transition probabilities, rewards and discount factor $`0\le\gamma<1`$. At time $`t`$, observe $`s_t`$, choose $`a_t`$, receive $`r_t`$ and next state $`s_{t+1}`$. A policy $`\pi(a|s)`$ maps states to action probabilities. The objective is expected discounted return $`E[\sum_{t\ge0}\gamma^tr_t]`$.

**Bellman relationships:**

```math
V^\pi(s)=E_\pi[r_t+\gamma V^\pi(s_{t+1})|s_t=s]
```


```math
Q^*(s,a)=E[r_t+\gamma\max_{a'}Q^*(s_{t+1},a')|s,a]
```

The value $`V`$ concerns a state; $`Q`$ concerns taking a particular action in a state.

**Exploration versus exploitation:** an $`\epsilon`$-greedy agent chooses a random action with probability $`\epsilon`$, otherwise the best known action. Exploration is appropriate in a simulator but may be unsafe on paying customers. Contextual bandits have immediate consequences without explicitly modelling future transitions; full RL models delayed consequences.

**Tabular Q-learning:**

```math
Q(s,a)\leftarrow Q(s,a)+\alpha[r+\gamma\max_{a'}Q(s',a')-Q(s,a)]
```

**Toy calculation:** $`Q(s,a)=5,\;r=2,\;\gamma=0.9,\;\max Q(s',\cdot)=8,\;\alpha=0.1`$. Target $`=2+0.9(8)=9.2`$; updated $`Q=5+0.1(9.2-5)=5.42`$. For a terminal next state, continuation value is zero.

**Deep Q-network (DQN):** approximate Q with a neural network, use replay memory to break correlations and a target network for more stable bootstrapping. Double DQN decouples action selection from target evaluation to reduce maximisation bias. DQN is natural for discrete action spaces.

**Policy gradients:** for a differentiable stochastic policy, REINFORCE updates in the direction

```math
\nabla_\theta J\approx\sum_t(G_t-b(s_t))\nabla_\theta\log\pi_\theta(a_t|s_t)
```

A baseline independent of the sampled action can reduce variance without introducing policy-gradient bias. An actor selects actions; a critic estimates values. For a one-step terminal transition, advantage may be $`r-V(s)`$; for nonterminal one-step TD, use $`A_t\approx r_t+\gamma V(s_{t+1})-V(s_t)`$.

**Generalised advantage estimation (GAE):** define $`\delta_t=r_t+\gamma V(s_{t+1})-V(s_t)`$ and $`\hat A_t=\sum_{l\ge0}(\gamma\lambda)^l\delta_{t+l}`$. The parameter $`\lambda`$ trades bias against variance.

**PPO:** uses four interpretable quantities: new/old action probability ratio, advantage, clipped surrogate, and negative mean loss. See the four worked equations in §10. The clipping term moderates the training objective but is not a guaranteed bound on policy change or safety.

**Multi-agent RL.** Agents may cooperate, compete or both. A shared reward creates credit-assignment challenges. Under **centralised training, decentralised execution (CTDE)**, actors use only permitted local observations at runtime while a training critic can access global state. IPPO uses local critics; MAPPO often uses a centralised value function with PPO-style updates. A shared critic does **not** imply all agents share policy weights. Non-stationarity occurs because other agents' policies are changing during training.

**Safe RL / Guardian:** encode non-negotiable constraints separately from learned rewards, reject actions violating those constraints, fall back to a verified policy and monitor violations. Simulation-based validation is informative but cannot establish universal safety in untested physical conditions.

## T9. Optimisation foundations and continuous methods

An optimisation problem has **decision variables** $`x`$, an **objective** $`f(x)`$, and a **feasible set** $`\mathcal F`$: $`\min_{x\in\mathcal F}f(x)`$. Constraints may be inequalities $`g_i(x)\le0`$, equalities $`h_j(x)=0`$, integrality or discrete-choice restrictions. A feasible decision meets every hard constraint; an optimum is the best feasible decision.

**Convexity:** a set is convex when every line segment joining two feasible points is feasible. A differentiable function is convex if $`f(y)\ge f(x)+\nabla f(x)^\top(y-x)`$; for twice differentiable functions a PSD Hessian is sufficient (and under standard open convex domain assumptions equivalent). Every local minimum of a convex objective over a convex feasible set is global; nonlinear or integer problems generally lack this guarantee.

**Gradient descent** $`x_{t+1}=x_t-\eta\nabla f(x_t)`$ is first-order. **Newton's method** $`x_{t+1}=x_t-[\nabla^2f(x_t)]^{-1}\nabla f(x_t)`$ uses curvature and can converge rapidly near a suitable optimum, but the Hessian may be indefinite, singular or expensive. Practical methods use linear solves, damping or trust regions. **BFGS** approximates inverse curvature using successive gradients.

**Worked continuous step:** minimise $`f(x)=(x-3)^2+1`$. At $`x_0=0`$, $`f'(0)=-6`$. With $`\eta=0.2`$, $`x_1=1.2`$; the objective drops from 10 to 4.24. Exact Newton step moves from 0 to 3 because $`f''=2`$, finding $`f(3)=1`$.

**Conditioning:** the Hessian eigenvalue ratio (for a positive-definite Hessian) describes relative curvature. Poorly conditioned landscapes produce zig-zagging gradient steps; feature scaling, preconditioning or second-order methods can help. Always specify stopping criteria, such as gradient norm, relative objective improvement, maximum iterations and feasibility tolerance.

**Stochastic and black-box methods:** Bayesian optimisation models an expensive unknown score using a surrogate and acquisition function; evolutionary strategies, differential evolution and particle swarm optimisation explore without gradients. These are useful when derivatives are unavailable, but require careful evaluation budgets and repeated seeds.

## T10. Constraints, duality and integer optimisation

**Linear programming (LP):** minimise $`c^\top x`$ subject to $`Ax\le b`$, $`Ex=d`$, and bounds. Continuous LPs admit efficient methods such as simplex and interior-point algorithms. A **binary integer program (BIP)** requires some or all $`x_i\in\{0,1\}`$; combinatorial choice makes it harder.

**Lagrangian:** for $`\min f(x)`$ with $`g_i(x)\le0`$ and $`h_j(x)=0`$,

```math
\mathcal L(x,\lambda,\nu)=f(x)+\sum_i\lambda_i g_i(x)+\sum_j\nu_jh_j(x),\qquad\lambda_i\ge0
```

Under appropriate convexity and constraint qualification, KKT conditions characterise optimality: primal feasibility, dual feasibility, stationarity $`\nabla_x\mathcal L=0`$, and complementary slackness $`\lambda_ig_i(x)=0`$. The multipliers are *shadow prices*: roughly, the marginal change in optimal objective when relaxing a constraint, with sign interpreted using the chosen constraint convention.

**Worked constrained allocation:** allocate $`x`$ workers, minimise $`(x-5)^2`$ subject to $`x\le3`$. The constrained optimum is $`x=3`$ with loss 4. Set $`g(x)=x-3`$; stationarity $`2(x-5)+\lambda=0`$ implies $`\lambda=4`$, with active constraint and positive multiplier. Relaxing the cap slightly improves the loss at roughly four units per worker near that cap.

**LP relaxation:** replace $`c_i\in\{0,1\}`$ by $`0\le c_i\le1`$ to obtain a cheaper lower bound for minimisation. Fractional results must be rounded *and then checked for feasibility*. **Branch-and-bound** solves relaxations at tree nodes, branches on fractional variables and prunes nodes whose bound cannot improve the incumbent. The integrality gap compares the best integer and relaxed objectives and must have a defined denominator.

**Enumeration:** $`n`$ binary decisions yield $`2^n`$ configurations (six modules → 64; 20 modules → 1,048,576). Exhaustive enumeration provides an exact answer for small instances but quickly becomes impractical. Note that solving a linearised model exactly does not guarantee optimality for the original nonlinear model.

**ATLAS-specific formulation:** $`c_i=0`$ means tightly coupled and $`c_i=1`$ means separate service. Its objective balances latency, resource cost, risk and change penalty, subject to utilisation, SLA and availability requirements (see §2). A switching penalty discourages frequent flips; hysteresis adds an explicit dwell rule.

## T11. Graph, scheduling, dynamic and heuristic optimisation

**Graph model:** a graph $`G=(V,E)`$ represents locations and roads with edge weights (time, cost or distance). Dijkstra finds shortest paths for nonnegative weights; Bellman–Ford permits negative weights and detects reachable negative cycles; A* uses a heuristic lower bound (for optimality, conditions such as admissibility and suitable handling of consistency/reopening matter). Do not confuse shortest travel time with straight-line distance.

**Assignment:** choose driver–ride pairs to minimise total cost, with constraints that each driver/ride is assigned at most once. A bipartite weighted assignment can be solved with the Hungarian algorithm. If eligibility, capacities, fairness or time windows enter, the formulation may require integer programming.

**Toy assignment:** two drivers A,B and two rides 1,2 have costs $`C=\begin{bmatrix}3&8\\6&4\end{bmatrix}`$. Assignment A→1, B→2 costs $`3+4=7`$; A→2, B→1 costs $`8+6=14`$. Choose cost 7.

**Knapsack:** maximise $`\sum_iv_ix_i`$ subject to $`\sum_iw_ix_i\le W,\;x_i\in\{0,1\}`$. Dynamic programming uses subproblem state $`(i,\text{remaining capacity})`$. **Bellman's principle of optimality** says an optimal remaining plan is optimal for its resulting subproblem, given a sufficient state.

**Dynamic programming for autoscaling:** define $`V_t(s)=\min_a[c_t(s,a)+V_{t+1}(T(s,a))]`$, with $`s`$ including current replicas and pending startup/dwell state. Leaving the switching state out breaks the Markov property.

**Flow and packing:** max flow transports quantity over edges with capacities; min cut identifies a limiting separation in a network. Bin packing places workloads into a minimum number of finite-capacity pods; first-fit decreasing is a useful heuristic, not a general exact solver.

**Routing and scheduling:** travelling-salesperson, vehicle-routing and pickup/delivery problems add tour consistency, capacity, time windows and precedence. Held–Karp dynamic programming is exact for modest TSP instances; 2-opt iteratively removes crossings/improves tours but may get stuck in a local optimum.

**Metaheuristics:** greedy picks the best immediate move; local search improves a neighbour; tabu search temporarily forbids revisits; simulated annealing sometimes accepts a worse solution with probability $`e^{-\Delta/T}`$ for deterioration $`\Delta>0`$; genetic algorithms use selection, crossover and mutation; PSO updates particles using velocity, personal best and swarm best. Benchmark them with the *same computation budget*, initial states and feasibility checks.

## T12. Multi-objective, robust and safe decision-making

**Trade-offs:** minimising average wait, carbon emissions and surge unfairness often yields no single best point. A solution is **Pareto-dominated** if another feasible solution improves at least one objective without worsening any. The Pareto front contains nondominated solutions.

**Scalarisation:** normalised weighted sum $`\min \sum_kw_kf_k(x)/s_k`$ is simple, but choice of weights and scales changes decisions; weighted sums may miss nonconvex parts of a Pareto front. The **epsilon-constraint method** minimises one objective while bounding the rest.

**Robust optimisation:** when demand $`\lambda`$ is uncertain within uncertainty set $`\mathcal U`$, solve $`\min_x\max_{\lambda\in\mathcal U}f(x,\lambda)`$. This may be conservative; scenario or chance-constrained alternatives need assumptions about uncertainty distribution.

**Chance constraints:** require $`P(L(x,\xi)\le L_{\max})\ge1-\delta`$. Estimate reliability with enough independent and representative scenarios; finite samples cannot prove zero risk. **CVaR** minimises the mean loss in the worst tail beyond a chosen quantile, making rare severe waits more visible than average loss.

**Online control:** continually switching an action may itself be costly. Model $`\kappa\|x_t-x_{t-1}\|_1`$ or dwell-time restrictions; test transient states (boot delays, temporary capacity overlap, crashes). For an RL controller, distinguish *soft penalties* in its reward from *hard constraints* enforced by a Guardian.

**Fairness and privacy:** assess service across locations, times, accessibility needs and rider/driver groups without inferring protected traits from data where unjustified. Document collection purpose, retention, consent, access controls and leakage risk. A low global average wait can hide systematically underserved zones.

## T13. Experimental design, statistical validity and reproducibility

**Start with a hypothesis.** Example: “Adding an LSTM forecast to the same dispatch policy reduces unserved demand during sudden surges without raising average fare beyond a defined tolerance.” Predefine the primary metric, operational constraints, baselines and test distribution.

**Ablation:** remove one component at a time (no forecast, no anomaly detector, no optimisation, no Guardian) while keeping everything else fixed. An ablation answers contribution, not necessarily causal effect under interactions; factorial experiments examine interactions.

**Paired runs:** compare candidate and baseline on the *same* random seeds, arrival streams and demand shocks. If $`d_i=\text{candidate}_i-\text{baseline}_i`$, report $`\bar d`$, sample standard deviation $`s_d`$, and an appropriate confidence interval $`\bar d\pm t_{n-1,0.975}s_d/\sqrt n`$ under the relevant independence/normal-approximation assumptions. Avoid calling each correlated time step an independent replicate.

**Example:** paired improvement values [2,4,3,5,1] minutes yield mean improvement 3 minutes, sample SD $`\sqrt{2.5}\approx1.581`$, SE $`\approx0.707`$. With 5 independent paired runs, 95% t interval uses $`t_{4,0.975}\approx2.776`$, giving approximately [1.04, 4.96] minutes. Report this uncertainty rather than just “3 minutes better.”

**For forecasting:** plot performance by horizon and by normal/peak/event conditions; use chronological rolling-origin evaluation. **For classification:** show PR curve, thresholds, false alarms and calibration. **For RL:** evaluate frozen policies on held-out scenarios across multiple training and evaluation seeds; compare against random, nearest, greedy, fixed and relevant learned policies, and track unsafe proposals. **For optimisation:** report objective, feasibility, runtime median/p95, optimality gap and scaling with problem size.

**Avoid common threats:** test-set tuning, training/test overlap, cherry-picked traces, baseline under-tuning, simulator–reality mismatch, missing failure cases, mixed units, stale data, overclaiming statistical significance and comparing unequal training budgets. Disclose synthetic versus real data explicitly.

**Reproducibility checklist:** record repository commit, environment and dependency versions, input generators and seeds, units, preprocessing, splits, hyperparameters, hardware, timeout, solver optimality tolerances, total training steps, repeat count, evaluation scripts and raw result paths. GitHub-renderable Markdown math may depend on platform; keep plain-text formula explanations alongside displayed equations.

## T14. Fully worked integrated example, revision questions and glossary

### T14.1 One small ride-hailing decision, end-to-end

Assume an hourly demand forecaster predicts **12 requests** in Zone A, with current **9 available drivers**. Available boost actions bring **0, 2 or 4** drivers, at operating costs **0, 3 or 7** units respectively. Define simplified one-hour loss

```math
J(a)=5\max(0,12-(9+a))+\text{cost}(a)
```

Compute: action 0 → shortage 3, loss 15; action 2 → shortage 1, loss $`5+3=8`$; action 4 → shortage 0, loss 7. The feasible best of these three actions is **bring 4 drivers**, loss 7. If there is a hard policy limit of at most 2 relocations, action 4 is infeasible and action 2 wins with loss 8.

Now introduce forecast uncertainty: actual demand could be 8, 12 or 16. Recompute each action for each outcome; compare expected loss (if scenario probabilities are justified) with worst-case loss (robust decision). This illustrates the difference between an LSTM *prediction*, an optimiser *choice*, and a Guardian *feasibility check*. Finally, log realised demand, relocation decision and true outcome so the predictive and decision layers can be evaluated separately.

### T14.2 Questions with short answers

1. **Why standardise using training statistics only?** Otherwise test information leaks into fitting decisions.
2. **Why is 99% classification accuracy potentially misleading?** With 1% anomalies, predicting “normal” always reaches 99% accuracy yet catches none.
3. **How do ridge and lasso differ?** Ridge uses an L2 penalty and shrinks coefficients; lasso uses L1 and may produce exact zeros.
4. **Why might an LSTM outperform persistence?** It can model longer temporal patterns, though performance must be demonstrated on holdout data.
5. **What does a critic estimate?** Expected future return or state/action value; it does not itself choose an action.
6. **How does Q-learning differ from supervised learning?** It bootstraps values from rewards and transitions instead of fitting fixed outcome labels.
7. **Why can a low LP objective be misleading?** Fractional decisions may not be deployable; rounded solutions may violate constraints.
8. **What does a KKT multiplier mean?** Under suitable conditions, marginal sensitivity of the optimal objective to a constraint bound.
9. **Why use paired experiment seeds?** Shared randomness reduces noise in comparisons.
10. **What is the Guardian's role?** Reject unsafe/infeasible learned actions and trigger a defined fallback.
11. **What is the difference between forecast accuracy and decision utility?** A numerically better forecast may not improve, and can even worsen, downstream decisions.
12. **Why might MAPPO not beat IPPO on every benchmark?** Its centralised critic can reduce variance but introduces modelling/optimisation complexity; empirical outcomes depend on task and tuning.

### T14.3 Practice problems (with answers)

**P1 — Gradient descent.** $`L(w)=\frac12(w-4)^2`$, start $`w=0`$, $`\eta=0.25`$. Compute one update. **Answer:** gradient $`-4`$, updated $`w=1`$, loss drops from 8 to 4.5.

**P2 — Classification.** Predictions yield TP=18, FP=6, FN=2, TN=74. Find precision, recall and F1. **Answer:** precision $`18/24=0.75`$, recall $`18/20=0.9`$, F1 $`\approx0.818`$.

**P3 — Bayesian acceptance.** Prior Beta(2,2), five accepts and one decline. **Answer:** posterior Beta(7,3), posterior mean 0.7.

**P4 — Discounted reward.** Rewards 3 now and 4 next step, $`\gamma=0.5`$, episode ends after step 2. **Answer:** $`G_0=3+0.5(4)=5`$.

**P5 — Binary combinations.** Ten modules can be tight or loose. How many assignments? **Answer:** $`2^{10}=1024`$.

**P6 — Constraint repair.** Two options cost 4 and 3 respectively, but option 2 violates a 100 ms SLA. **Answer:** choose feasible option 1, not cheaper infeasible option 2.

### T14.4 Glossary

| Term | Meaning |
|---|---|
| Feature | Input quantity available at decision time |
| Label / target | Outcome the model learns to predict |
| Parameter | Fitted value inside a model, e.g. weight |
| Hyperparameter | Setting chosen outside weight fitting, e.g. learning rate |
| Loss | Numerical penalty the model minimises |
| Generalisation | Performance on unseen, representative cases |
| Calibration | Agreement between predicted probabilities and observed frequencies |
| Epoch | One complete traversal of the training dataset |
| Batch | Subset used for one parameter update |
| Optimiser | Procedure that changes parameters or decisions to improve objective |
| Feasible | Satisfies all hard constraints |
| Local optimum | No sufficiently nearby feasible decision improves objective |
| Global optimum | Best decision over the entire feasible set |
| Regularisation | Discourages complexity/large weights to improve generalisation |
| Time-series leakage | Future data improperly influences earlier predictions |
| MDP | State–action–transition–reward model for sequential decisions |
| Policy | Rule/distribution mapping observations to actions |
| Return | Accumulated, commonly discounted, future reward |
| Advantage | Action's result relative to a value baseline |
| Actor | Model producing action choices/probabilities |
| Critic | Model estimating state/action value |
| CTDE | Train with global context, execute with local observations |
| LP relaxation | Continuous approximation of a discrete optimisation problem |
| Pareto front | Feasible solutions not dominated across objectives |
| Digital twin | Synchronised simulation used to rehearse system behaviour |
| Champion / challenger | Deployed model versus candidate under validation |

### T14.5 Theory → practical ATLAS map

| Read theory | Study existing guide | Run reproducible lab |
|---|---|---|
| T1–T3: foundations, regression and classification | §4, §6 | \`ml_lab/machine_learning/run_ml.py --path supervised\` |
| T4–T5: ensembles, clusters, anomaly detectors | §5 | \`ml_lab/machine_learning/run_ml.py --path unsupervised\` |
| T6–T7: neural training, LSTM and drift | §4, §11 | \`ml_lab/machine_learning/run_ml.py --path time-series\` |
| T8: RL and multi-agent theory | §7, §9, §10 | \`ml_lab/machine_learning/run_ml.py --path multi-agent\` |
| T9–T10: calculus, KKT, BIP | §2, §3 | \`ml_lab/optimisation/run_optimisation.py --path atlas-coupling\` |
| T11–T12: routing, heuristics, robust control | §2, §8 | \`ml_lab/optimisation/run_optimisation.py --path graphs-and-routing\` |
| T13–T14: evaluation and combined decisions | §12, §13 | \`python3 ml_lab/ml_optimisation_lab.py\` |

**Recommended progression:** Mathematical prerequisites → learning tasks and statistical evaluation → supervised/unsupervised models → neural networks and LSTM → online learning → reinforcement learning → continuous and constrained optimisation → deployment safety and fair experimental comparison. A learner can understand this sequence without installing ATLAS; the linked labs then turn theory into practice.

**Further reading:** Bishop, *Pattern Recognition and Machine Learning*; Hastie, Tibshirani & Friedman, *The Elements of Statistical Learning*; Goodfellow, Bengio & Courville, *Deep Learning*; Sutton & Barto, *Reinforcement Learning: An Introduction*; Boyd & Vandenberghe, *Convex Optimization*; Nocedal & Wright, *Numerical Optimization*. These are external references for deeper study, not prerequisites for using this guide.


---

## T15. What it is, why it matters, and how it works — concept-by-concept teaching companion

This chapter is designed for **first-time learners**. Each explanation follows the same three questions: **What?** (definition and goal), **Why?** (when or why we need it), and **How?** (the mechanism, including a small example). The methods are general theory; any ATLAS analogy is illustrative unless Part I identifies a specific implemented function.

### T15.1 Data, samples, features, labels and preprocessing

**What?** A sample is a row representing one observation; features are known quantities used to make a prediction; a label is the outcome to predict. A dataset combines many observations. **Why?** Algorithms cannot infer useful relationships unless inputs are meaningful, consistently measured, and available at decision time. **How?** For predicting a ride acceptance, make each row one historical offer, put distance and estimated pickup delay in the feature columns, and acceptance (0/1) in the label column. Separate the test period first, impute missing training values using training-derived statistics, and apply the same transformation to future data.

**What is feature engineering?** Transforming raw facts into informative variables; e.g. pickup time 17:30 becomes time-of-day sine/cosine so 23:59 is close to 00:01. **Why?** Models are sensitive to how information is represented. **How?** Convert hour $`h`$ to $`\sin(2\pi h/24)`$ and $`\cos(2\pi h/24)`$, fit all statistical preprocessing on the training window, and verify each feature is available before the prediction.

### T15.2 Learning paradigms

**Supervised learning — What?** Learning an input–output mapping from labelled examples. **Why?** We want to predict an observed quantity, such as next-hour demand or the likelihood of a driver accepting. **How?** Select a model, define loss between prediction and actual outcome, adjust parameters using training data, and test on unseen examples.

**Unsupervised learning — What?** Finding patterns without explicit outcome labels. **Why?** The system may need to discover natural demand zones or unusual telemetry before manually labelled incidents exist. **How?** Cluster by similarity, compress correlated features (PCA), or compute outlier scores; then check whether the discovered structure is stable and useful.

**Self-supervised learning — What?** Constructing a training objective from the raw data itself. **Why?** Large data streams contain patterns even when manual labels are scarce. **How?** Hide a portion of a sequence and train a model to predict it; use learned representations for a later labelled task. This is a conceptual extension, not a claim that the ATLAS deployment trains a foundation model.

**Reinforcement learning — What?** Learning decisions from observed rewards and future consequences. **Why?** Selecting a driver may help one ride but deplete supply for subsequent rides. **How?** Define state, action, reward and transition, interact with a simulator/controlled environment, estimate expected returns, then validate a frozen policy before allowing operational use.

### T15.3 Loss, training, validation and generalisation

**Loss — What?** A numerical measure of prediction error (e.g. squared error, log loss). **Why?** Without a measurable objective the optimiser has no direction. **How?** For true demand 100 and forecast 90, absolute error is 10, squared error is 100; averaging over many observations gives MAE or MSE.

**Parameter versus hyperparameter — What?** A parameter is learned (a regression weight); a hyperparameter is selected by an external process (learning rate, network width). **Why?** Mixing the two leads to misleading performance and test leakage. **How?** Fit weights on training data; choose hyperparameters using validation; evaluate the locked choice on test once.

**Cross-validation — What?** Repeated fitting on different training/validation subsets. **Why?** A single split can be unrepresentative. **How?** Use K-fold for approximately exchangeable observations, group K-fold for shared-driver identities and rolling-origin folds for time series. Never move future information backward in time.

**Overfitting and regularisation — What?** Overfitting learns training-specific noise; regularisation discourages overly complex solutions. **Why?** A system that performs excellently on recorded routes may fail on new roads. **How?** Compare training and validation curves, constrain complexity using L1/L2 penalties, early stopping or smaller models, and test on truly unseen weeks/events.

### T15.4 How linear and probabilistic models make predictions

**Linear regression — What?** Predicts a continuous value by a weighted sum of features. **Why?** It is fast, interpretable and a strong baseline. **How?** If demand $`=10+2(\text{event score})`$, an event score 3 predicts 16. Fit the coefficients by minimising squared errors (T3).

**Logistic regression — What?** Converts a linear score into a probability between zero and one. **Why?** Acceptance and cancellation are binary, not unbounded real outcomes. **How?** Compute $`z=w^\top x+b`$, then $`p=1/(1+e^{-z})`$; train with cross-entropy and calibrate the resulting probabilities.

**Naive Bayes — What?** A classifier derived from Bayes' rule with a conditional-independence assumption between features. **Why?** It gives a cheap probabilistic baseline with limited training data. **How?** Multiply class prior by feature likelihoods (usually in log space), normalise over the classes, and compare posterior probabilities.

**Bayesian updating — What?** Revises uncertainty about an unknown parameter after new evidence. **Why?** One driver accepting two rides does not justify perfect certainty. **How?** Start with Beta$`(\alpha,\beta)`$ for acceptance probability, then add successes to $`\alpha`$ and declines to $`\beta`$; compute the posterior mean and credible intervals as required.

### T15.5 How nonparametric and ensemble models work

**kNN — What?** Uses nearby historical observations instead of fitting one global formula. **Why?** Similar local contexts may have similar outcomes. **How?** Standardise inputs, compute distances, select the closest $`k`$ examples, then vote or average. Choose $`k`$ on validation data.

**Decision tree — What?** Learns nested if/else questions. **Why?** Rules like distance < 3 km and demand > threshold are easy to explain. **How?** At each node select the split that decreases Gini impurity, entropy or squared error; stop or prune to avoid memorising noise.

**Random forest — What?** An average of many decorrelated trees. **Why?** Individual trees can change drastically when data change. **How?** Bootstrap observations, randomise split-feature selection, train each tree, and aggregate predictions.

**Boosting — What?** A sequence of learners correcting remaining prediction errors. **Why?** Many small trees can capture useful nonlinear interactions. **How?** Fit a new tree to a loss gradient/residual, add a shrunken contribution to the ensemble, and stop based on validation performance.

**SVM — What?** A classification method maximising the separation margin while penalising errors. **Why?** Wide-margin separation can generalise well, including in nonlinear feature spaces. **How?** Solve the margin-constrained optimisation problem; use a kernel when a linear boundary is insufficient; tune margin penalty and kernel width.

### T15.6 How clustering, dimension reduction and anomaly detection work

**k-means — What?** Partitions points around $`k`$ centroids. **Why?** It can summarise rider pickup areas. **How?** Initialise centres, repeatedly assign observations to the nearest centre and recompute the mean; check cluster stability and suitability.

**DBSCAN — What?** A density-connected clustering method with noise points. **Why?** Pickup locations can form irregular dense streets instead of circular groups. **How?** Define a geographic radius and minimum neighbour count; connect core points and identify isolated points as noise.

**PCA — What?** Finds mutually perpendicular directions explaining maximum data variance. **Why?** Many sensor signals may be redundant. **How?** Centre/scale suitably, compute SVD, retain top principal directions, and project each observation. PCA does not prove causation or guarantee predictive importance.

**Isolation Forest — What?** Detects outliers by random partitioning. **Why?** Fault labels may be rare or unavailable. **How?** Build random split trees; shorter average isolation paths mean more unusual points; tune alert thresholds against realistic false-positive costs.

### T15.7 How neural networks and sequence forecasts learn

**Perceptron/dense network — What?** Weighted inputs followed by a nonlinear activation, possibly stacked in layers. **Why?** Nonlinear combinations of location, time and demand can be difficult for a single straight-line model. **How?** Evaluate every layer forward, compute loss, use chain-rule backpropagation for derivatives, update weights, and validate.

**Gradient descent — What?** Moves the model parameters opposite the loss gradient. **Why?** It can improve parameters without enumerating all possibilities. **How?** Starting $`w=0`$ for $`L=(w-2)^2`$, gradient is $`-4`$; a 0.1 step yields $`w=0.4`$, reducing loss from 4 to 2.56.

**Adam — What?** Adaptive stochastic gradient optimisation using running first/second moments. **Why?** Different neural parameters can have very different gradient scales. **How?** Compute $`m_t`$, $`v_t`$, apply bias correction and use the Adam update in T6; still tune learning rate and validate.

**RNN — What?** Reuses hidden state as it processes a sequence. **Why?** Current demand often depends on previous hours. **How?** Repeatedly update $`h_t`$ from current input and previous hidden state, then predict using $`h_t`$.

**LSTM — What?** A gated recurrent neural network with a memory cell. **Why?** Ordinary recurrent networks can struggle to preserve signals over long intervals. **How?** Forget, input and output gates control cell memory; T6 gives the exact equations. Train on chronological input windows with only historical information.

**Forecast baseline — What?** A simple reference predictor such as “same as last hour” or “same hour yesterday.” **Why?** Complex forecasting is only justified if it improves upon credible simple models. **How?** Evaluate all forecasts over identical future horizons and on holiday/surge conditions, not only average days.

### T15.8 How sequential and multi-agent decision learning works

**Contextual bandit — What?** Chooses among actions using immediate reward conditioned on context. **Why?** A simple offer-ranking problem may not need a full long-term model. **How?** Track reward estimates per context/action and compare actions, with suitable offline exploration and propensity considerations.

**Q-learning — What?** Learns a value for taking each action in each state. **Why?** Future driver availability changes the value of a current move. **How?** Observe transition and reward, compute Bellman target, and update the state–action table (T8); for large state spaces, approximate with a DQN.

**DQN — What?** A neural approximation of the Q-table. **Why?** Millions of state combinations make explicit tables impractical. **How?** Store replay transitions, train a neural network to predict temporal-difference targets, and periodically update a separate target network.

**REINFORCE — What?** A Monte Carlo policy-gradient method that optimises action probabilities directly. **Why?** Stochastic driver selection can learn from complete ride-level outcomes. **How?** Sample actions, collect returns, increase log-probability for better-than-baseline returns and decrease it for worse outcomes.

**Actor–critic — What?** One model chooses actions; another estimates expected return. **Why?** A state-specific critic helps reduce policy-gradient variance relative to a global baseline. **How?** Predict advantage, update actor using advantage-weighted log-policy gradient, and train critic to approximate returns/TD targets.

**PPO — What?** An actor–critic policy-optimisation technique limiting large updates using a clipped probability ratio. **Why?** Overly aggressive policy changes may destroy a useful policy. **How?** Collect experience with an old policy, calculate advantage, optimise the clipped surrogate for a limited number of epochs, then reevaluate. Clipping is not a hard safety guarantee.

**MAPPO — What?** Multi-agent PPO with a critic that can access combined state during training. **Why?** Dispatch and pricing decisions affect one another; local observations may hide important shared effects. **How?** Train each actor on allowed observations, estimate shared advantages from global state, then run actors without the critic's privileged training-only inputs.

**Digital twin — What?** A simulation updated to match real-system conditions. **Why?** Potential decisions can be rehearsed without experimenting on real riders. **How?** Mirror current state, forecast outcomes, simulate alternatives, evaluate them and apply a Guardian before deployment; continuously verify twin fidelity.

### T15.9 How optimisation chooses among alternatives

**Continuous optimisation — What?** Choose real-valued variables to minimise cost. **Why?** Forecast model parameters or CPU fractions need fine-grained adjustment. **How?** Use gradient descent, Newton/BFGS or constrained solvers depending on differentiability, curvature and constraints.

**Linear programming — What?** Optimise linear objective under linear constraints with continuous variables. **Why?** Capacity allocation can often be expressed efficiently with linear costs/limits. **How?** Define variables, objective and inequalities; solve with simplex/interior point; check primal feasibility and shadow prices.

**Integer programming — What?** Require decisions such as “service separated or not” to be integral. **Why?** A half-migrated service is not a deployable option. **How?** Formulate binary decisions; solve small cases by enumeration and larger ones via branch-and-bound/cuts or validated approximate rounding.

**KKT and duality — What?** Mathematical conditions and auxiliary prices associated with constrained optima. **Why?** They identify active limits and sensitivity to scarce resources. **How?** Form the Lagrangian, check primal/dual feasibility, stationarity and complementary slackness under the appropriate regularity conditions (T10).

**Dynamic programming — What?** Solves a multi-step problem using optimally solved smaller states. **Why?** Moving a driver now changes future availability and switch costs. **How?** Define a state sufficient to describe future consequences, then apply a Bellman recurrence from horizon end backward or learn approximate values.

**Dijkstra / A* — What?** Shortest-path algorithms; A* uses a lower-bound heuristic to guide search. **Why?** Nearby drivers in kilometres are not always nearest in travel time. **How?** Build a road graph with travel-time weights, expand candidate paths and stop when optimality conditions are met.

**Hungarian assignment — What?** Exact minimum-cost one-to-one matching in a bipartite cost matrix. **Why?** Assigning each ride greedily may give a worse overall matching. **How?** Compute every eligible driver–ride cost and solve the full assignment subject to exclusivity.

**Simulated annealing — What?** Local search that sometimes accepts worse candidates. **Why?** Greedy search can get trapped in a local minimum. **How?** Propose a neighbouring choice, always accept improvements, accept deterioration $`\Delta>0`$ with probability $`\exp(-\Delta/T)`$, and gradually lower $`T`$.

**Genetic algorithm — What?** Population-based optimisation inspired by selection and mutation. **Why?** Hard discrete spaces may have complex nonconvex objectives. **How?** Encode candidates, evaluate fitness, select better candidates, recombine/mutate, repair constraints and retain the best feasible result.

**Particle swarm optimisation — What?** A population of candidate particles guided by their own and the swarm's best positions. **Why?** It can search continuous black-box objectives without derivatives. **How?** Update velocities/positions, evaluate objective, and revise personal/global bests. Use bounds and multiple seeds.

**Pareto optimisation — What?** Find alternatives for which no objective can improve without worsening another. **Why?** Speed, cost and rider fairness conflict. **How?** Compute nondominated alternatives, show trade-offs and choose operating points using stakeholder-approved weights or explicit constraints.

**Robust optimisation — What?** Seek decisions that remain acceptable over uncertain future scenarios. **Why?** LSTM forecasts can be wrong during concerts or storms. **How?** Evaluate worst cases or scenario distributions, enforce limits, and report the cost of extra conservatism.

**Runtime Guardian — What?** Deterministic checks on decisions before execution. **Why?** Statistical learning and simulated validation do not guarantee every action is safe. **How?** Reject actions exceeding maximum price, unacceptable pickup delay, capacity or response-time limits; use a tested fallback and log why a proposal was blocked.

### T15.10 One complete What → Why → How learning path

Consider **forecasting and repositioning drivers**:

1. **What is the prediction?** The LSTM outputs expected next-hour requests for each zone. **Why?** Relocation takes time. **How?** Train on past-hour windows with chronological holdout.
2. **What is the decision?** A policy or optimiser chooses relocations. **Why?** Excess drivers cost money; too few create waiting queues. **How?** Minimise weighted shortage + idle cost with capacity and feasibility constraints.
3. **What is the feedback?** The next hour reveals actual demand and realised waiting. **Why?** Predictions and actions may fail differently. **How?** Log time-stamped predictions, chosen actions, policy versions and outcomes.
4. **What improves?** A challenger forecaster and challenger policy are trained on authorised new data. **Why?** Demand patterns drift. **How?** Compare frozen candidates on untouched scenarios, deploy only if prespecified quality and safety gates pass.
5. **What protects deployment?** A Guardian and rollback policy. **Why?** A high average reward can hide unacceptable rare failures. **How?** Enforce hard constraints at decision time, record violations, and keep a verified baseline available.

**The central conceptual distinction:** *machine learning estimates patterns; optimisation chooses feasible actions; reinforcement learning learns sequential action policies; simulation tests hypotheses; statistical evaluation measures uncertainty; and operational safety checks protect real-world execution.*


---

## T16. Equation-by-equation explanations: What, Why and How

Use this chapter alongside the equations in Parts I–II. For every formula: identify inputs, interpret the output, substitute numbers, check units, and ask whether it applies to prediction, learning or a constrained decision. Equations shown as standalone blocks use GitHub's `math` fences.

### E1. Dot product and vector length

**What:** A dot product is a weighted sum of features; Euclidean norm measures length. **Why:** Linear regression, driver scores and optimisation use weighted contributions. **How:** weights (2, −1) and features (3, 4) give score 2×3 − 1×4 = 2; feature-vector norm is 5.

```math
w^\top x=\sum_{j=1}^{p}w_jx_j,\qquad \|x\|_2=\sqrt{\sum_{j=1}^{p}x_j^2}
```

Here p counts features, and j indexes each feature.

### E2. Bayes' rule and acceptance updates

**What:** Bayes' rule updates a prior belief after evidence. **Why:** Driver acceptance history is limited and uncertain. **How:** a Beta(2,2) prior with 3 accepts and 1 decline becomes Beta(5,3), mean 5/8 = 0.625.

```math
P(H\mid E)=\frac{P(E\mid H)P(H)}{P(E)}
```

```math
\mathbb E[p\mid s,f]=\frac{\alpha+s}{\alpha+\beta+s+f}
```

H means hypothesis, E evidence, p unknown success probability, alpha/beta prior parameters, s successes and f failures.

### E3. Chain rule and gradient descent

**What:** The chain rule measures how a parameter influences the final loss. Gradient descent changes that parameter opposite the derivative. **Why:** This is the mechanism of model training. **How:** for loss (w−3)² at w=1, derivative is −4; learning rate 0.1 changes w to 1.4.

```math
\frac{dL}{dw}=\frac{dL}{d\widehat y}\frac{d\widehat y}{dw},\qquad w_{t+1}=w_t-\eta\frac{dL}{dw}
```

L is error, y-hat is prediction, w learnable parameter, eta learning rate.

### E4. Standardisation

**What:** Transforms an input relative to the training mean and standard deviation. **Why:** Features on incompatible numerical scales can distort distance and optimisation. **How:** a distance of 8 km, training mean 5 and SD 2, becomes (8−5)/2 = 1.5.

```math
z=\frac{x-\mu_{\mathrm{train}}}{\sigma_{\mathrm{train}}}
```

x is the original feature and z its standardised form. Handle zero-variance columns explicitly; fit statistics on training data only.

### E5. Regression and squared-error loss

**What:** A linear model predicts a continuous quantity; the loss scores differences against actual outcomes. **Why:** It provides a transparent demand-forecasting baseline. **How:** prediction 7 against actual 9 gives half-squared error (7−9)²/2 = 2.

```math
\widehat y=w^\top x+b,\qquad J=\frac{1}{2n}\sum_{i=1}^{n}(\widehat y_i-y_i)^2
```

b is intercept; n is number of samples; the sum averages their errors.

### E6. Ridge and Lasso

**What:** Add penalties on model weights. **Why:** Very large coefficients can lead to overfitting. **How:** weights (3,4) have an L2-squared penalty of 25 and an L1 penalty of 7 before multiplying by lambda.

```math
J_{\mathrm{ridge}}=J_{\mathrm{data}}+\lambda\sum_jw_j^2,\qquad J_{\mathrm{lasso}}=J_{\mathrm{data}}+\lambda\sum_j|w_j|
```

Lambda is a nonnegative validation-selected penalty weight; usually exclude the intercept.

### E7. Logistic regression and probabilistic losses

**What:** A sigmoid converts a score into probability, cross-entropy measures classification loss, and Brier score measures squared probability error. **Why:** An acceptance prediction should represent uncertainty, not just yes/no. **How:** score 0 gives probability 0.5; if acceptance occurs, cross-entropy is about 0.693.

```math
p=\frac{1}{1+e^{-z}},\qquad z=w^\top x+b
```

```math
L_{\mathrm{CE}}=-\frac{1}{n}\sum_i\left[y_i\log p_i+(1-y_i)\log(1-p_i)\right]
```

```math
\mathrm{Brier}=\frac{1}{n}\sum_i(p_i-y_i)^2
```

p_i is forecast probability and y_i is observed binary result; clip exact zero/one probabilities numerically before logarithms.

### E8. Classification and forecasting metrics

**What:** Precision is the proportion of alarms that are real, recall the proportion of real anomalies found; F1 balances both. MAE/RMSE measure numerical errors. **Why:** Accuracy alone hides rare-event failures. **How:** 8 true positives, 2 false positives, 2 missed positives yield precision=recall=F1=0.8.

```math
P=\frac{TP}{TP+FP},\quad R=\frac{TP}{TP+FN},\quad F_1=\frac{2PR}{P+R}
```

```math
\mathrm{MAE}=\frac{1}{n}\sum_i|y_i-\widehat y_i|,\qquad\mathrm{RMSE}=\sqrt{\frac{1}{n}\sum_i(y_i-\widehat y_i)^2}
```

TP/FP/FN count true positives, false positives and false negatives. Specify conventions for any zero denominator.

### E9. Trees, clustering and principal components

**What:** Gini measures class impurity, k-means minimises distances to cluster centres, PCA compresses correlated inputs. **Why:** They handle distinct classification, grouping and representation tasks. **How:** a 50/50 binary tree node has Gini impurity 0.5, while a pure node has zero.

```math
G=1-\sum_{k=1}^{K}p_k^2
```

```math
J_{\mathrm{kmeans}}=\sum_i\min_j\|x_i-\mu_j\|_2^2
```

```math
z=W_K^\top(x-\mu)
```

p_k is class fraction, mu_j a cluster centre, W_K the principal-component directions; K is context-dependent.

### E10. Isolation Forest

**What:** Scores unusual samples by average isolation-tree path length. **Why:** Rare faults may be easier to isolate than ordinary operating points. **How:** a point with path length 2 is scored more anomalous than a point of path length 8 with the same normaliser.

```math
s(x)=2^{-\mathbb E[h(x)]/c(n)}
```

h(x) is path length; c(n) normalises it for sample size. An anomaly score is not automatically a calibrated failure probability.

### E11. Softmax driver selection

**What:** Softmax converts driver scores into probabilities. **Why:** It can balance preferences among multiple feasible drivers. **How:** scores 2 and 1 become approximately 73.1% and 26.9%.

```math
z_a=w^\top\phi_a,\qquad\pi(a)=\frac{e^{z_a}}{\sum_{j=1}^{K}e^{z_j}}
```

w are learned weights, phi_a driver features, K candidate count, pi(a) probability of choosing driver a. The probabilities sum to 1.

### E12. SGD and Adam

**What:** SGD follows current gradients; Adam maintains moving estimates of gradients and squared gradients. **Why:** Gradient directions and scales vary during training. **How:** current weight 5, gradient 2, learning rate 0.1 gives an SGD update to 4.8.

```math
\theta_{t+1}=\theta_t-\eta g_t
```

```math
m_t=\beta_1m_{t-1}+(1-\beta_1)g_t,\qquad v_t=\beta_2v_{t-1}+(1-\beta_2)g_t^2
```

```math
\widehat m_t=\frac{m_t}{1-\beta_1^t},\quad\widehat v_t=\frac{v_t}{1-\beta_2^t},\quad\theta_{t+1}=\theta_t-\eta\frac{\widehat m_t}{\sqrt{\widehat v_t}+\varepsilon}
```

Theta means trainable parameters, g gradient, m momentum-like estimate, v squared-gradient estimate, beta decay rates, epsilon numerical stabiliser.

### E13. LSTM gates

**What:** Forget, input and output gates respectively retain, write and expose memory. **Why:** Forecasts may depend on hours of past context. **How:** old cell 0.8, forget gate 0.5, input 0.25, candidate memory 0.6 gives new cell 0.55.

```math
f_t=\sigma(W_f[h_{t-1},x_t]+b_f),\qquad i_t=\sigma(W_i[h_{t-1},x_t]+b_i)
```

```math
\widetilde c_t=\tanh(W_c[h_{t-1},x_t]+b_c),\qquad c_t=f_t\odot c_{t-1}+i_t\odot\widetilde c_t
```

```math
o_t=\sigma(W_o[h_{t-1},x_t]+b_o),\qquad h_t=o_t\odot\tanh(c_t)
```

x_t is input, h_t hidden state, c_t memory, W/b gate weights/biases and ⊙ elementwise multiplication.

### E14. Forecasting baselines

**What:** Persistence copies the latest observation; seasonal naive copies an equivalent earlier seasonal observation. **Why:** A complex LSTM must justify its extra complexity against strong simple forecasts. **How:** if demand at the same hour last week was 120, weekly seasonal naive predicts 120.

```math
\widehat y_{t+h}^{\mathrm{persist}}=y_t,\qquad\widehat y_{t+h}^{\mathrm{season}}=y_{t+h-s}
```

h is horizon, s seasonal period. The historical index must be available at forecast time.

### E15. Bellman return and Q-learning

**What:** Discounted return sums future rewards; Q-learning updates predicted action quality based on a transition. **Why:** Dispatch actions affect future supply. **How:** Q=5, reward 2, discount 0.9, best next Q=8, step size 0.1 yield updated Q=5.42.

```math
G_t=\sum_{k=0}^{T-t-1}\gamma^k r_{t+k}
```

```math
Q(s,a)\leftarrow Q(s,a)+\alpha\left[r+\gamma\max_{a'}Q(s',a')-Q(s,a)\right]
```

Gamma discounts later rewards, alpha controls learning rate, s and s-prime are current/next state. Use zero continuation at terminal states.

### E16. Policy gradients and actor–critic

**What:** REINFORCE adjusts action probabilities using return; a critic provides a state-specific baseline. **Why:** A good outcome can reflect an easy state rather than a good action. **How:** return 8 versus critic estimate 6 gives positive advantage 2; an outcome of 4 gives negative advantage −2.

```math
\nabla_\theta J\approx\sum_t(G_t-b(s_t))\nabla_\theta\log\pi_\theta(a_t\mid s_t)
```

```math
A_t=G_t-V_\phi(s_t)
```

Theta parameterises actor, phi critic, b baseline and A advantage. Positive advantage reinforces the sampled action relative to alternatives.

### E17. PPO and MAPPO clipping

**What:** PPO compares action probabilities before/after a policy update and clips the surrogate improvement; MAPPO uses a centralised value critic across agents. **Why:** Unbounded updates can destabilise learning. **How:** old/new probabilities .4/.6 give ratio 1.5; with advantage 2 and epsilon .2, clipped benefit is min(3,2.4)=2.4.

```math
q_t=\frac{\pi_{\mathrm{new}}(a_t\mid o_t)}{\pi_{\mathrm{old}}(a_t\mid o_t)}
```

```math
u_t=\min\left(q_t\widehat A_t,\operatorname{clip}(q_t,1-\epsilon,1+\epsilon)\widehat A_t\right)
```

```math
\mathcal L_{\mathrm{PPO}}=-\frac{1}{N}\sum_{t=1}^{N}u_t
```

Here epsilon is clipping width, N batch size and advantage compares return with value estimate. Clipping is an objective heuristic, not a hard safety guarantee.

### E18. Binary deployment optimisation

**What:** Select the lowest-cost feasible configuration of coupled or separate modules. **Why:** Latency, cost, reliability and switching conflicts must be balanced. **How:** of two feasible configurations costing 5.16 and 6.06 in objective units, select 5.16; reject any candidate violating SLA regardless of lower cost.

```math
\min_{c\in\{0,1\}^{n}}J(c)
```

```math
J(c)=\alpha\frac{L(c)}{L_0}+\beta\frac{C(c)}{C_0}+\gamma\gamma_s\frac{R(c)}{R_0}+\kappa\|c-c_{\mathrm{now}}\|_1
```

c is deployment vector; L/C/R are latency/cost/risk; denominators are reference scales; alpha/beta/gamma/kappa weight trade-offs; L1 counts binary flips.

### E19. Newton and convex optimisation

**What:** Gradient descent uses slope; Newton also uses curvature. **Why:** Curvature can help continuous optimisers converge faster near a well-behaved minimum. **How:** for (x−3)²+1 at x=0, gradient −6 and curvature 2 give full Newton step to 3.

```math
x_{t+1}=x_t-\eta\nabla f(x_t)
```

```math
x_{t+1}=x_t-[\nabla^2f(x_t)]^{-1}\nabla f(x_t)
```

A Hessian must be handled with a linear solver and safeguarded when singular/indefinite; a full step is not always safe.

### E20. Lagrangian and KKT

**What:** Lagrange multipliers attach resource prices to constraints; KKT conditions describe stationary constrained optima. **Why:** We need to understand scarce-capacity limits. **How:** minimising (x−5)² with cap x≤3 gives optimum x=3 and multiplier 4, under standard conditions.

```math
\mathcal L(x,\lambda)=f(x)+\lambda g(x),\quad\lambda\ge0
```

```math
\nabla_x\mathcal L=0,\quad g(x)\le0,\quad\lambda g(x)=0
```

The formula illustrates one inequality; full KKT includes all equalities/inequalities and regularity assumptions.

### E21. Bellman dynamic programming

**What:** Express total future minimum cost as immediate cost plus optimal remaining cost. **Why:** Repositioning has consequences over multiple hours. **How:** enumerate legal actions from each state, add immediate cost to next-state value, then choose the smallest.

```math
V_t(s)=\min_{a\in\mathcal A(s)}\left[c_t(s,a)+V_{t+1}(T(s,a))\right]
```

V is cost-to-go, c immediate cost, T transition, A(s) feasible actions, t time index. Choose an appropriate terminal cost at horizon end.

### E22. Robust optimisation and confidence intervals

**What:** Robust optimisation minimises the worst plausible cost, and confidence intervals quantify sampling uncertainty. **Why:** Mean scores may hide severe unusual loads or evaluation noise. **How:** compare each configuration under uncertainty scenarios and report paired-run differences with a confidence interval.

```math
\min_{x\in\mathcal F}\max_{\xi\in\mathcal U}f(x,\xi)
```

```math
\overline d\ \pm\ t_{n-1,0.975}\frac{s_d}{\sqrt n}
```

F is feasible set, U uncertainty set, d mean paired difference, s_d its sample SD. The t interval assumes appropriate sampling independence and distributional conditions.

**Learning routine:** For each equation, say aloud what it predicts or selects, why that goal matters, define every symbol, substitute a two-input toy example, verify the units and feasibility conditions, and then locate the corresponding ATLAS lab.
