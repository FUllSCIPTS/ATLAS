# Machine-learning and optimisation labs

Forty-four experiments, one Python file each, kept in two tracks: **24 machine-learning experiments** in
[`machine_learning/`](machine_learning) and **20 optimisation experiments** in [`optimisation/`](optimisation).
New with ATLAS Go 1.3–1.4: **ML 21** digital twin (mirror, foresee, rehearse, guard), **ML 22** actor and
critic networks (A2C), **ML 23** two agents sharing one critic (MAPPO) and **ML 24** LSTM + RL as one
closed loop with validated retraining.
Every experiment runs on its own, uses ATLAS's own data or code wherever it can, prints its results with a
short explanation, and ends with an exercise in its docstring. The original seven-section lab on the
paper's optimiser stays in [`ml_optimisation_lab.py`](ml_optimisation_lab.py). Teaching guide:
[docs/MACHINE_LEARNING_OPTIMISATION.md](../docs/MACHINE_LEARNING_OPTIMISATION.md).

Requirements: numpy, scipy and scikit-learn (`requirements.txt`); PyTorch is not needed.

```bash
python3 ml_lab/machine_learning/ml07_ensembles.py               # one experiment
python3 ml_lab/machine_learning/run_ml.py                       # all 24 ML experiments (about 1.5 min)
python3 ml_lab/machine_learning/run_ml.py --path multi-agent    # actor-critic, then MAPPO
python3 ml_lab/machine_learning/run_ml.py --path unsupervised   # a study path
python3 ml_lab/optimisation/run_optimisation.py --list          # optimisation experiments and paths
python3 ml_lab/optimisation/run_optimisation.py -e 8 -e 17      # chosen experiments
```

## What the experiments use from ATLAS

| ATLAS source | Used by |
|---|---|
| `data.zip`: 10,000 labelled telemetry minutes (`anomaly_data.csv`), 8-day per-minute trace | ML 03-10, 12, 14, 15; OPT 03 |
| `atlas_sim.zip`: the paper's e-commerce traffic and telemetry generators, service demands | ML 01, 02, 11, 16, 17; OPT 01, 04, 07, 14, 19 |
| `atlas_sim.zip`: the paper's coupling optimiser `Sim.bip` / `Sim.eval_all` | OPT 17, 20 |
| `run_bip_timing.py`: the linearised coupling BIP instances | OPT 08, 15, 17 |
| `android-app/atlas_go`: Cork geography, driver pools, dispatch scoring and cost model, learned weights | ML 05, 13, 18, 19; OPT 05, 06, 09-11, 13, 16, 18 |
| `android-app/training/rl_sim.py`: the courier-timing environment | ML 20 |
| `android-app/atlas_go/twin.py`: the digital twin, Agents 1-2 and the Guardian (Layer 2, 1.3.0) | ML 21 |
| `android-app/atlas_go/intelligence.py`: dispatch candidates, reward and cost model, policy v1.4 | ML 22 |
| The proposal's two-agent twin (dispatch + pricing, one team reward) | ML 23 |
| `android-app/atlas_go/loop.py`, `lstm_weights.py`: the live LSTM -> RL loop (Layer 1, 1.4.0) | ML 21, 24 |

## Machine learning (`machine_learning/`)

| # | File | What you build | Applies beyond ATLAS to |
|---|---|---|---|
| 01 | [`ml01_linear_regression.py`](machine_learning/ml01_linear_regression.py) | Linear regression three ways: normal equations, gradient descent and scikit-learn | any "how much Y per unit of X" question - cost per user, energy per job, sales per ad euro |
| 02 | [`ml02_bias_variance_regularisation.py`](machine_learning/ml02_bias_variance_regularisation.py) | Bias, variance and regularisation: fitting the latency curve with polynomials and ridge | every model with a "complexity knob" - tree depth, number of features, network size |
| 03 | [`ml03_logistic_regression.py`](machine_learning/ml03_logistic_regression.py) | Logistic regression from scratch: is this minute of telemetry an anomaly? | churn, fraud, click-through, diagnosis - any yes/no with a probability attached |
| 04 | [`ml04_knn_and_scaling.py`](machine_learning/ml04_knn_and_scaling.py) | k-nearest neighbours and why feature scaling matters: naming the kind of incident | recommendation ("people like you"), case-based reasoning, simple baselines for anything |
| 05 | [`ml05_naive_bayes.py`](machine_learning/ml05_naive_bayes.py) | Naive Bayes and Bayes' rule: probabilities from counts, and the base-rate trap | spam filtering, text classification, medical tests, any prior-plus-evidence reasoning |
| 06 | [`ml06_decision_tree.py`](machine_learning/ml06_decision_tree.py) | A decision tree from scratch: readable rules for "what kind of incident is this?" | credit rules, triage protocols, any setting where the model must be explained |
| 07 | [`ml07_ensembles.py`](machine_learning/ml07_ensembles.py) | Ensembles: bagging, random forests and gradient boosting versus one tree and a line | tabular data in general - forests and boosting win most tabular benchmarks and competitions |
| 08 | [`ml08_svm_kernels.py`](machine_learning/ml08_svm_kernels.py) | Support vector machines: maximum margins and the kernel trick | text classification, bioinformatics, any small-to-medium data set with a clear margin |
| 09 | [`ml09_neural_network_backprop.py`](machine_learning/ml09_neural_network_backprop.py) | A neural network from scratch: forward pass, backpropagation and mini-batch training | vision, speech, language, forecasting - wherever features are learned rather than designed |
| 10 | [`ml10_metrics_and_imbalance.py`](machine_learning/ml10_metrics_and_imbalance.py) | Evaluation under class imbalance: accuracy lies; precision, recall, PR-AUC and calibration | fraud, defects, disease, intrusion - every rare-event problem |
| 11 | [`ml11_cross_validation_leakage.py`](machine_learning/ml11_cross_validation_leakage.py) | Cross-validation and leakage: why a random split flatters a time-series model | any data with time, users or groups - stock prices, patients, sensors, sessions |
| 12 | [`ml12_kmeans.py`](machine_learning/ml12_kmeans.py) | k-means clustering from scratch: discovering operating regimes without labels | customer segmentation, image compression, document grouping, vector quantisation |
| 13 | [`ml13_dbscan_geo_hotspots.py`](machine_learning/ml13_dbscan_geo_hotspots.py) | Density-based clustering (DBSCAN) on a map: where do ride requests bunch up in Cork? | crime and accident hotspots, GPS trajectory stops, fraud rings, any clusters of odd shape |
| 14 | [`ml14_pca.py`](machine_learning/ml14_pca.py) | Principal component analysis: eight correlated metrics, a few real directions | compression, visualisation, denoising, face recognition, gene expression, finance factors |
| 15 | [`ml15_anomaly_detection.py`](machine_learning/ml15_anomaly_detection.py) | Unsupervised anomaly detection: z-scores, Mahalanobis, Isolation Forest and LOF | fraud, intrusion detection, predictive maintenance, quality control |
| 16 | [`ml16_time_series_forecasting.py`](machine_learning/ml16_time_series_forecasting.py) | Time-series forecasting: naive baselines, Holt-Winters by hand and a lag regression | sales, energy demand, inventory, call centres, web traffic |
| 17 | [`ml17_concept_drift_online.py`](machine_learning/ml17_concept_drift_online.py) | Concept drift and online learning: when yesterday's model meets tomorrow's traffic | fraud patterns, user tastes, sensor ageing, prices - any world that changes under the model |
| 18 | [`ml18_learning_to_rank.py`](machine_learning/ml18_learning_to_rank.py) | Learning to rank: recovering a dispatch policy from pairwise preferences | search results, recommendations, feeds, hiring shortlists - anything shown as a ranked list |
| 19 | [`ml19_bandits.py`](machine_learning/ml19_bandits.py) | Multi-armed bandits: explore or exploit? epsilon-greedy, UCB1 and Thompson sampling | A/B testing, ad and news selection, clinical trials, recommender exploration, pricing |
| 20 | [`ml20_q_learning_courier.py`](machine_learning/ml20_q_learning_courier.py) | Reinforcement learning with tabular Q-learning: when should the courier leave? | robotics, games, inventory control, traffic signals, recommendation sequences |
| 21 | [`ml21_digital_twin.py`](machine_learning/ml21_digital_twin.py) | Digital twin: foresight vs reacting, how many rehearsals a stable choice needs, Agent 2's plans on St Patrick's Day, 3,000 injected faults against the Guardian | factories, power grids, logistics and hospitals - simulate before you act, and shield what you deploy |
| 22 | [`ml22_actor_critic.py`](machine_learning/ml22_actor_critic.py) | Actor and critic networks: an advantage actor-critic (A2C) learns dispatch against REINFORCE, v1.4 and nearest-driver | robotics, recommendation, logistics - RL with noisy, delayed rewards |
| 23 | [`ml23_mappo_shared_critic.py`](machine_learning/ml23_mappo_shared_critic.py) | Multi-agent RL: dispatch and pricing agents with independent critics (IPPO) vs one shared centralised critic (MAPPO) | fleets, warehouses, traffic signals, power grids - teams of agents with one goal |
| 24 | [`ml24_lstm_rl_loop.py`](machine_learning/ml24_lstm_rl_loop.py) | LSTM + RL as one loop: forecast, act, record, update, validate; frozen vs learning over eight weeks | demand planning, energy dispatch, inventory - forecast-then-decide systems that keep learning safely |

### Study paths (`run_ml.py --path NAME`)

| Path | Experiments | Goal |
|---|---|---|
| `supervised` | 1, 2, 3, 4, 5, 6, 10 | Predict a number or a class, and know when to trust it |
| `trees-and-ensembles` | 6, 7, 10 | Rules, forests and boosting on tabular data |
| `neural-networks` | 1, 3, 9 | From a line to a network, trained by gradient descent |
| `unsupervised` | 12, 13, 14, 15 | Structure and outliers without labels |
| `time-series` | 11, 16, 17 | Forecasting, honest validation and drift |
| `decisions` | 18, 19, 20 | Ranking, bandits and reinforcement learning |
| `trustworthy-ml` | 2, 10, 11, 17 | Overfitting, imbalance, leakage and drift |
| `reinforcement-learning` | 19, 20, 22, 23 | From bandits to actor-critic and two agents with one critic |
| `digital-twin` | 21, 16, 24 | Mirror, foresee, rehearse, guard - then learn as a closed loop |
| `multi-agent` | 22, 23 | Actor and critic networks, then two agents sharing one critic (MAPPO) |
| `lstm-and-rl` | 16, 17, 20, 24 | Forecast, act, record, update and validate: LSTM + RL as one loop |

## Optimisation (`optimisation/`)

Continuous (1-4), linear and integer (5-8), graphs and combinatorial (9-14), metaheuristics and
evolutionary (15-18), black-box and multi-objective (19-20).

| # | File | What you build | Applies beyond ATLAS to |
|---|---|---|---|
| 01 | [`opt01_gradient_descent_conditioning.py`](optimisation/opt01_gradient_descent_conditioning.py) | Gradient descent: step size, convergence and why conditioning decides the speed | every model trained by gradient methods, from linear regression to deep networks |
| 02 | [`opt02_momentum_and_adam.py`](optimisation/opt02_momentum_and_adam.py) | Momentum, Nesterov and Adam: faster first-order methods on hard valleys | training any neural network; large-scale logistic regression; matrix factorisation |
| 03 | [`opt03_newton_and_bfgs.py`](optimisation/opt03_newton_and_bfgs.py) | Second-order methods: Newton's method, BFGS and L-BFGS versus gradient descent | statistics (GLMs are fitted by Newton/IRLS), engineering design, any smooth problem of |
| 04 | [`opt04_constrained_core_allocation.py`](optimisation/opt04_constrained_core_allocation.py) | Constrained continuous optimisation: sharing 16 cores among six services (KKT and SLSQP) | budget allocation, portfolio weights, power/bandwidth allocation, chemical equilibria |
| 05 | [`opt05_linear_programming_transport.py`](optimisation/opt05_linear_programming_transport.py) | Linear programming: repositioning idle drivers across Cork (a transportation problem) | logistics, supply chains, production planning, diet and blending problems, network flow |
| 06 | [`opt06_duality_and_sensitivity.py`](optimisation/opt06_duality_and_sensitivity.py) | LP duality and sensitivity: what is one more driver, or one more request, worth? | pricing, capacity investment decisions, economics (shadow prices), column generation |
| 07 | [`opt07_dynamic_programming_knapsack.py`](optimisation/opt07_dynamic_programming_knapsack.py) | Dynamic programming: whole cores for six services, and the 0/1 knapsack | budgeting, cutting stock, sequence alignment, speech recognition (Viterbi), inventory |
| 08 | [`opt08_branch_and_bound.py`](optimisation/opt08_branch_and_bound.py) | Integer programming by branch-and-bound, written by hand, on the paper's coupling BIP | scheduling, facility location, crew rostering, chip design - any yes/no decision model |
| 09 | [`opt09_shortest_paths.py`](optimisation/opt09_shortest_paths.py) | Shortest paths on a Cork road graph: Dijkstra, A* with a haversine heuristic, Bellman-Ford | navigation, network packet routing, game AI, project scheduling (longest path), currency |
| 10 | [`opt10_assignment_hungarian.py`](optimisation/opt10_assignment_hungarian.py) | The assignment problem: matching drivers to riders, greedy versus the Hungarian method | task allocation, organ exchange, school admissions, object tracking between video frames |
| 11 | [`opt11_tsp_courier_route.py`](optimisation/opt11_tsp_courier_route.py) | The travelling salesman: a courier's multi-drop route, exact (Held-Karp) and heuristic | delivery and service routing, PCB drilling, DNA sequencing, telescope scheduling |
| 12 | [`opt12_bin_packing_pods.py`](optimisation/opt12_bin_packing_pods.py) | Bin packing: placing service pods on 8-core nodes (first-fit decreasing vs exact MILP) | VM and container scheduling, truck loading, cutting stock, memory allocation, ad slots |
| 13 | [`opt13_max_flow_min_cut.py`](optimisation/opt13_max_flow_min_cut.py) | Network flows: maximum flow and minimum cut (Edmonds-Karp), and bipartite matching | telecom and power networks, evacuation planning, image segmentation, baseball elimination |
| 14 | [`opt14_dp_autoscaling_schedule.py`](optimisation/opt14_dp_autoscaling_schedule.py) | Dynamic programming over time: a replica schedule with switching costs (myopic vs optimal) | unit commitment in power grids, inventory and production planning, fleet sizing |
| 15 | [`opt15_local_search_tabu.py`](optimisation/opt15_local_search_tabu.py) | Local search, random restarts and tabu search on a large coupling BIP | scheduling, timetabling, graph colouring, feature selection - wherever exact solvers stall |
| 16 | [`opt16_simulated_annealing.py`](optimisation/opt16_simulated_annealing.py) | Simulated annealing: escaping 2-opt's local optimum on an 80-stop courier route | chip placement, timetabling, protein folding, any large combinatorial search |
| 17 | [`opt17_genetic_algorithm.py`](optimisation/opt17_genetic_algorithm.py) | A genetic algorithm for the coupling decision: selection, crossover, mutation, elitism | design optimisation, scheduling, neural architecture search, game strategies, antenna design |
| 18 | [`opt18_evolution_strategies_de_pso.py`](optimisation/opt18_evolution_strategies_de_pso.py) | Continuous black-box optimisation: (1+1)-ES, differential evolution and particle swarms | engineering design, controller and hyperparameter tuning, calibration of simulators |
| 19 | [`opt19_bayesian_optimisation.py`](optimisation/opt19_bayesian_optimisation.py) | Bayesian optimisation: tuning a forecaster in 20 evaluations with a Gaussian process | hyperparameter tuning, A/B-test design, materials and drug discovery, robot gait tuning |
| 20 | [`opt20_multi_objective_pareto.py`](optimisation/opt20_multi_objective_pareto.py) | Multi-objective optimisation: the latency-cost Pareto front of ATLAS's coupling choices | engineering design (weight vs strength), portfolios (risk vs return), ML (accuracy vs size), |

### Study paths (`run_optimisation.py --path NAME`)

| Path | Experiments | Goal |
|---|---|---|
| `continuous` | 1, 2, 3, 4 | Gradients, curvature and constraints |
| `linear-and-integer` | 5, 6, 7, 8 | LP, duality, dynamic programming and branch-and-bound |
| `graphs-and-routing` | 9, 10, 11, 12, 13 | Paths, matching, tours, packing and flows |
| `dynamic-programming` | 7, 11, 14 | Bellman's principle in three settings |
| `metaheuristics` | 15, 16, 17, 18 | Local search, tabu, annealing and evolution |
| `black-box-tuning` | 17, 18, 19 | Optimising when you can only evaluate |
| `atlas-coupling` | 8, 15, 17, 20 | The paper's coupling decision from every angle |

## Findings worth discussing

- **ML 01:** seeding the trace and the telemetry generator with the same seed made their noise identical and
  biased the fitted slope by 9 %; with independent seeds the fit recovers the generator's true slope.
- **ML 11:** under shuffled folds a random forest beats the "same as now" baseline; under forward-chaining
  validation it loses to it.
- **ML 15:** on four basic metrics, Isolation Forest (the paper's detector on all eight) catches the fewest
  incidents at a 1 % false-alarm budget; Mahalanobis distance and LOF catch the most.
- **ML 16:** the weekly seasonal-naive forecast beats every fitted model on the 3-day test.
- **ML 18, OPT 18:** weights learned from pairwise preferences, or tuned by differential evolution or PSO,
  match or slightly beat ATLAS Go's REINFORCE weights on the app's own cost model, and beat the nearest-driver rule.
- **ML 21:** in festival and holiday weeks the twin's calendar-aware foresight cuts the 30-minute demand-ratio
  error from 0.43-0.65 ("last hour again") to 0.12-0.16; the Guardian catches 3,000 of 3,000 injected faults with
  no false alarms on 6,000 normal decisions.
- **ML 22:** with a learned critic the actor reaches within 0.1 min of policy v1.4 after 2,000 rides; REINFORCE
  with a running baseline needs 8,000. The critic lowers the variance of the learning signal by about 20 %.
- **ML 23:** both multi-agent methods beat "nearest car" by about 20 %; the shared critic cuts the noise in the
  dispatch agent's advantages by about 40 % and learns faster in mid-training, but ends at a similar policy.
- **ML 24:** the LSTM-informed agent costs 10.5 % less than the 1.2 calendar agent over four periods (not in
  every period); over eight weeks validated nightly learning lowers cost by 1.5-16 % against frozen models.
- **OPT 17:** with six modules enumeration (64 evaluations, exact) is the right choice, as the paper does; a
  genetic algorithm pays off only at 60 modules.
- **OPT 20:** the paper's chosen coupling at 6,000 req/s is Pareto-optimal for latency and cost; weighted sums
  reach only 3 of the 5 Pareto-optimal couplings.
