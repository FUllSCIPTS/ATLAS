# ATLAS — Supplementary Code and Data

Code, data, trained models and raw results for the article

> **ATLAS: Learning to Rewire the Web — Predictive Architecture Transformation for Autonomous Cloud Systems**
> 
> Basker Palaniswamy and Paolo Palmieri, Dept. of C.S. & I.T., University College Cork (UCC), Ireland, European Union.
> 
> *Future Internet* (MDPI).

The repository reproduces every table and data-driven figure of the evaluation:
forecasting (LSTM, Bi-LSTM and statistical baselines), out-of-distribution and
cross-node tests, anomaly detection, the architecture comparison with
statistical tests, the forecaster-value and ablation studies, the load and
sensitivity sweeps, the connected-vehicle case study, recovery times and BIP
solve times, the process-level prototype measurements, and the
second-revision checks (exact vs. linearised optimisation, blast-radius and
availability assumptions, system-level value of the anomaly detector, and a
combined-factor stress test).

## Live architecture explorer

Explore the ride-hailing reference design, trace trip and driver events, and inspect the deployment layout.  

1) [Open the ATLAS Architecture Explorer](https://fullscipts.github.io/ATLAS/)

2) [Source and server deployment guide](https://github.com/FUllSCIPTS/ATLAS/tree/architecture-explorer/architecture-explorer)

3) [Final handover and acceptance checks](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/docs/FINAL_HANDOVER.md) · [UML blueprint and class/function catalog](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/docs/UML_BLUEPRINT.md)

4) [ATLAS Go 1.2.0 Python Android app — passenger, driver and food-seller accounts, live map, rides, shared rides and food](android-app/README.md) · [Screenshots and user guide](android-app/docs/USER_GUIDE.md) · [Google Play release guide](android-app/docs/GOOGLE_PLAY.md)

5) [▶ Watch the ATLAS Go demo video (4 min 52 s) — the app (ride booking, driver gets location, food order, shop-to-home delivery); how an RL agent learns who to dispatch and when to send the courier; two years of Cork's holidays and events, with the agent's experience log helping the LSTM predict surges hours ahead; then ATLAS rewiring itself as users scale up and down: monolith → hybrid → microservices → monolith](android-app/docs/video/atlas-go-demo.mp4)

6) [🔐 Information security in ATLAS — live Security view in the explorer](https://fullscipts.github.io/ATLAS/#security) · [Teaching guide](docs/INFORMATION_SECURITY.md)

7) [🔑 Cryptography in ATLAS — live Cryptography view in the explorer](https://fullscipts.github.io/ATLAS/#crypto) · [Teaching guide](docs/CRYPTOGRAPHY.md)

8) [📈 Machine learning and optimisation in ATLAS — the paper's coupling optimiser and every learner, live in the explorer](https://fullscipts.github.io/ATLAS/#ml) · [Teaching guide](docs/MACHINE_LEARNING_OPTIMISATION.md)

## Information security in ATLAS (teaching guide)

ATLAS doubles as a worked example for teaching information security. The full guide is
**[docs/INFORMATION_SECURITY.md](docs/INFORMATION_SECURITY.md)**; the
**[Explorer's Security view](https://fullscipts.github.io/ATLAS/#security)** runs the same material
live in the browser. Each topic is tagged ✅ **implemented** (in the code today),
🧪 **demo-grade** (implemented with deliberately simple choices — good "find the weakness"
exercises), or 🎓 **teaching extension** (a standard protocol mapped onto ATLAS components; **not**
in the ATLAS code).

| Topic | Status | How ATLAS does it | Where |
|---|---|---|---|
| **How user passwords are stored** | ✅ | Never stored. Each account keeps a random 16-byte salt and a **PBKDF2-HMAC-SHA256** hash with **200 000 iterations**; verification recomputes and compares with `hmac.compare_digest` (constant time). `public_view` strips salt and hash before anything reaches the screen | `android-app/atlas_go/accounts.py` |
| **Authentication** | ✅ | Email + password; **5 failed attempts → 60 s lockout**; the same error for unknown email and wrong password (no user enumeration); session = account id, validated on every load | `android-app/atlas_go/store.py` → `login` |
| **Identity management** | ✅ | Register (validated email, E.164 phone, role-specific licence/plate/business checks) → sign in → sign out → **delete with re-authentication**, which anonymises history | `accounts.py`, `store.py`, `android-app/docs/PRIVACY.md` |
| **Authorisation (RBAC)** | ✅ | Three roles — passenger, driver, food seller — enforced twice: screen allow-list in `app.py` and role checks in every `store.py` command | `app.py` → `render`, `store.py` |
| **Gateway authentication** | 🧪 | Server starter: `Authorization: Bearer` key → constant-time match → route allow-list (method, role, regex) → gateway asserts `X-Atlas-Actor` + internal token → each service re-checks with `internal_actor()` | `starter/services/gateway.py`, `starter/packages/config.py` |
| **Single sign-on (SSO)** | 🎓 | OpenID Connect (authorisation code + PKCE) with one ATLAS identity provider for the passenger app, driver app, seller portal and explorer; the gateway would validate signed JWTs instead of static keys | Guide §7 |
| **Kerberos** | 🎓 | The six messages (AS-REQ/REP, TGS-REQ/REP, AP-REQ/REP) mapped onto ATLAS: driver app = client, *ATLAS Identity* = KDC, Dispatch Service = service. **Runs live** in the explorer with AES-GCM, with replay, clock-skew, tampering and expiry attacks | Guide §8, [Explorer → Kerberos](https://fullscipts.github.io/ATLAS/#security-kerberos) |
| **Transport security** | ✅ | Prototype: **mutual TLS** with a private CA, `serverAuth`/`clientAuth` key usages, `CERT_REQUIRED`, 30-day certificates generated at run time | `prototype/proto_run.py`, `prototype/module_server.py` |
| **Secure deployment** | ✅ | Explorer server: loopback only + SSH tunnel, GET/HEAD only, strict CSP and security headers, systemd sandbox (`DynamicUser`, `ProtectSystem=strict`); signed APKs with `SHA256SUMS` | `architecture-explorer/server.mjs`, `deploy/atlas-explorer.service`, `android-app/releases/` |

**Try it**

```bash
python3 security_lab/password_storage_demo.py   # 20 experiments on the real accounts.py + store.py
python3 security_lab/lab_c_signin_defences.py   # or one category: lab_a_ ... lab_d_ (see security_lab/README.md)
python3 security_lab/password_storage_demo.py --list            # experiments and study paths
python3 security_lab/password_storage_demo.py --path attacker   # foundations | attacker | defender | integrity | lifecycle
```

Known gaps (lockout kept in memory only, no MFA, `state.json` not encrypted at rest, default demo
keys, a static internal token over plain HTTP) are listed as student exercises in
[§11 of the guide](docs/INFORMATION_SECURITY.md#11-known-gaps--exercises-for-students).

## Cryptography in ATLAS (teaching guide)

Where ATLAS uses hash functions, checksums, public-key infrastructure, digital signatures and — as a
teaching extension — post-quantum cryptography. Full guide:
**[docs/CRYPTOGRAPHY.md](docs/CRYPTOGRAPHY.md)**; live labs:
**[Explorer → Cryptography](https://fullscipts.github.io/ATLAS/#crypto)**.

| Topic | Status | How ATLAS uses it | Where |
|---|---|---|---|
| **Hash (SHA-256)** | ✅ | `SHA256SUMS` for every release; CI pins `bundletool.jar` to a committed SHA-256; signing records hash the exact signed bundle; the UML blueprint hashes every source file | `android-app/releases/`, `.github/workflows/atlas-android.yml`, `SIGNED_VALIDATION.json`, `starter/scripts/generate_blueprint.py` |
| **Checksum vs hash** | ✅ | The prototype compares a cheap state checksum `(count, total, len(seen))` after recovery (crash class C3): detects lost updates, **not** tampering — a deliberate contrast with SHA-256 | `prototype/module_server.py`, `run_recovery_mc.py` |
| **PKI — private CA** | ✅ | Prototype builds its own CA: RSA-2048 root (`CA:TRUE`), server cert (`serverAuth`, SAN 127.0.0.1) and client cert (`clientAuth`), 30-day lifetime, **mutual TLS** with `CERT_REQUIRED` | `prototype/proto_run.py` |
| **PKI — Web PKI** | ✅ | Map tiles over HTTPS, verified against public CAs from `certifi` | `android-app/atlas_go/livemap.py` |
| **Certificate + pinning** | ✅ | Self-signed **RSA-4096** upload certificate (sha384WithRSA, valid to 2059); CI recomputes its SHA-256 fingerprint and fails unless it equals the pinned `059076…44d7` | `releases/upload-certificate.pem`, `scripts/ci-sign-bundle.py` |
| **Digital signatures** | ✅ | Play bundle signed with **SHA256withRSA** (`jarsigner`), then verified; installable APK signed with **APK Signature Scheme v2/v3**; private key only in a PKCS#12 keystore or encrypted Actions secret | `scripts/sign-release.py`, `releases/1.2.0/` |
| **Post-quantum (PQC)** | 🎓 | Not in ATLAS. Shor breaks the RSA keys and TLS key exchange; SHA-256, HMAC and PBKDF2 survive. The guide maps ML-KEM (FIPS 203), ML-DSA (FIPS 204) and SLH-DSA (FIPS 205) onto ATLAS; the explorer runs a hash-based **Lamport** signature live | `docs/CRYPTOGRAPHY.md` §6 |

```bash
python3 security_lab/crypto_lab.py                              # 20 experiments: hashing, MACs, PKI, signatures, PQC
python3 security_lab/crypto_lab.py --path release-engineer     # or a study path, or one file: crypto_a_ ... crypto_e_
python3 security_lab/crypto_lab.py --verify atlas-go-1.2.0.apk  # check a download against SHA256SUMS
```

## Machine learning and optimisation in ATLAS (teaching guide)

The paper's core is an **optimisation algorithm**: every 5 s ATLAS solves a **binary integer program
(BIP)** that decides which modules stay inside one process (tight) and which run as separate services
(loose). Four learners feed it or run beside it. Full guide:
**[docs/MACHINE_LEARNING_OPTIMISATION.md](docs/MACHINE_LEARNING_OPTIMISATION.md)**; live labs:
**[Explorer → ML & Optimisation](https://fullscipts.github.io/ATLAS/#ml)**. 📄 = evaluated in the paper,
✅ = runs in the ATLAS Go app or server starter (trained on synthetic data).

| Topic | Status | What ATLAS does | Where |
|---|---|---|---|
| **Coupling BIP (the paper's optimiser)** | 📄 | min α·L + β·C + γ·Risk + switching cost over c ∈ {0,1}<sup>n</sup>, subject to monolith utilisation ≤ 0.85, 200 ms SLA, ≤ 40 replicas, availability ≥ 0.99; solved by exhaustive enumeration (n = 6, 0.27 ms per decision); 300 s hysteresis before merging back | `atlas_sim/cluster.py` → `Sim.bip`, `Sim.eval_all`, `Sim.run` |
| **Scaling the solver** | 📄 | LP relaxation + risk-aware rounding + greedy repair vs HiGHS branch-and-bound: 6.4 ms vs 401 ms at n = 500, median gap 0.23 %; agrees with the exact nonlinear optimum in 96 % of 32 400 recorded states | `run_bip_timing.py`, `run_round2.py` |
| **Tuning** | 📄 | Grid search on validation seeds (101–110), tested on seeds 1–30; every baseline tuned the same way | `run_cluster.py` → `tune` |
| **Forecasting** | 📄 ✅ | LSTM (2 × 128, Adam, gradient clipping, early stopping): 5-min MAE 51.7 req/s vs 72.2 persistence; the optimiser plans for max(load, forecast). Starter and app: small LSTMs (the app's has a hand-written Adam step) | `atlas_sim/forecast.py`, `starter/ml/forecast.py`, `training/city_sim.py` |
| **Anomaly detection** | 📄 ✅ | Isolation Forest, no labels: ROC-AUC 0.9999; the score raises a module's crash risk in the BIP, ≥ 0.9 triggers emergency mode | `run_anomaly.py`, `Sim.score`, `starter/ml/discrete.py` |
| **Reinforcement learning** | ✅ | Ride dispatch by **REINFORCE** (softmax over 4 drivers, 5.38 vs 6.42 expected minutes for nearest-driver); courier timing by **Q-learning**; driver supply with hindsight updates; starter bandit with an offline approval gate | `atlas_go/intelligence.py`, `training/rl_sim.py`, `starter/ml/rl.py` |

```bash
python3 ml_lab/ml_optimisation_lab.py              # BIP decisions, solvers, GD vs Adam, Isolation Forest, RL
python3 ml_lab/ml_optimisation_lab.py --section 4  # one section: the three BIP solvers
```

## ATLAS Go Android app

**Version 1.2.0** — a Python/Kivy Android app for Cork with **passenger, driver and food-seller registration**, a **live map** (OpenStreetMap tiles, device location, moving drivers and couriers, offline fallback), solo and shared rides, food ordering from built-in and seller kitchens, and **six on-device ML models** wired into the live flows (dispatch policy, per-driver acceptance model, surge outlook, supply agent, courier timing, learning lab). Accounts and bookings are stored on the phone; rides, deliveries and payments are simulated until an operator back end is connected.

| Open or download | Contents |
|---|---|
| [Installable Android APK 1.2.0 — request access](https://drive.google.com/file/d/1lX5DF9e8ierusJ1OCuVHkeqeCoBgqQfq/view) | **New version 1.2.0:** passenger, driver and food-seller registration, live map (OpenStreetMap, your location, moving drivers and couriers), and six on-device ML models in the live flows. Open the link, click **Request access**; once approved, download with your Google account. Uninstall 1.1.0 first (new signing key). SHA-256 `737c41ec935e4a87d849a04b1434fbe66fa47bdcb9420387e2a94f58400813cb` |
| [ATLAS Go 1.2.0 downloads](android-app/releases/1.2.0/README.md) | APK link (request access), `SHA256SUMS`, release notes, validation evidence and screenshots |
| [Changelog](android-app/CHANGELOG.md) | 1.2.0 changes and compatibility |
| [▶ Demo video — atlas-go-demo.mp4](android-app/docs/video/atlas-go-demo.mp4) | 4 min 52 s, recorded with 1.1.0: rides, food, how the RL agent learns, two years of Cork's calendar, and ATLAS rewiring itself as load changes |

| Welcome | Live map | Driver request | Seller kitchen |
|---|---|---|---|
| <img src="android-app/docs/screenshots/01-welcome.png" alt="Welcome screen with account options" width="200"> | <img src="android-app/docs/screenshots/10-live-map.png" alt="Live map of Cork" width="200"> | <img src="android-app/docs/screenshots/21-driver-request.png" alt="Driver receiving a ride request" width="200"> | <img src="android-app/docs/screenshots/22-seller-order.png" alt="Food seller handling an order" width="200"> |

**Verified (1.2.0):** 117 Python tests; 247 UI assertions in each of two screen configurations with 22 screenshots; model retraining reproduces the bundled models byte for byte; bundle validation, release manifest, 16 KB native alignment and APK v2/v3 signature checks pass ([evidence](android-app/releases/1.2.0/VALIDATION.md)). The Android 16 emulator run executes in GitHub Actions on push.

## Quick start

```bash
git clone https://github.com/FUllSCIPTS/ATLAS.git
cd ATLAS
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# regenerate the figures from the included results (seconds)
python3 make_figures.py

# rerun all experiments from scratch (about 2–3 h on 2 CPU cores)
./run_all.sh
```

`run_all.sh` skips LSTM training when `results/forecast.json` is present;
delete it to retrain. All random seeds are fixed. The prototype needs
`openssl` on the `PATH`; it generates its own short-lived test certificates in
`prototype/certs/` (not committed).

## Repository layout

| Path | Purpose |
|---|---|
| `atlas_sim/traffic.py` | Synthetic workloads (one-year e-commerce trace with flash sales, connected-vehicle fleet trace) and telemetry/anomaly generators |
| `atlas_sim/forecast.py` | LSTM / Bi-LSTM forecaster (PyTorch), Ridge-AR, seasonal-naive and persistence baselines, metrics |
| `atlas_sim/cluster.py` | 1-s cluster simulator with continuous-time failure/recovery events; static monolith, static microservices, HANSEL-like, Predictive-Hybrid, XScale-like and ATLAS (BIP optimiser, state machine, self-healing); option `blast="process"` for the conservative whole-process blast radius |
| `prototype/` | Process-level prototype: a stateful module served in-process or over HTTPS with mutual TLS; switching and recovery protocols measured with real timestamps |
| `run_forecast.py` | Trains the LSTM (3 seeds), Bi-LSTM and baselines; vehicle-fleet LSTM |
| `run_ood.py` | Out-of-distribution and cross-node tests; online forecaster selector |
| `val_preds.py` | Forecasts on the validation period (used only for tuning) |
| `run_anomaly.py` | Isolation Forest: full metric set, contamination and severity sensitivity |
| `run_cluster.py` | Tuning, 30-run architecture comparison (Wilcoxon/Holm), forecaster value, ablation, offered-load sweep, sensitivity analysis |
| `run_vehicle.py` | Connected-vehicle case study (14 held-out test days) |
| `run_recovery_mc.py` | Event-level recovery time per crash class |
| `run_bip_timing.py` | Measured BIP solve times (enumeration, HiGHS branch-and-bound, LP + rounding) |
| `run_round2.py` | Second-revision experiments: exact vs. linearised optimisation (gap in the nonlinear objective), blast-radius and availability checks, system-level value of the anomaly detector (with an oracle detector), 2^4 combined-factor stress test, detector firing pattern |
| `export_datasets.py` | Writes `data/`; `--full` writes the complete 525,600-row trace |
| `make_figures.py` | Regenerates the data-driven figures into `figures/` (override with `ATLAS_FIG_DIR`) |
| `data/` | Anomaly dataset, failure schedule, simulation configuration, 7-day traffic excerpt |
| `results/` | Raw result files (JSON/NPZ) and trained model weights used in the paper |
| `figures/` | Figures as they appear in the paper |
| `run_all.sh` | Runs everything in order |
| `docs/INFORMATION_SECURITY.md` | Information-security teaching guide: password storage, authentication, identity management, RBAC, gateway auth, SSO, Kerberos, mTLS, secure deployment |
| `security_lab/README.md` | Index of the labs: categories, experiments, study paths and the gaps they expose |
| `security_lab/lab_a_password_storage.py` … `lab_d_integrity_lifecycle.py` | Information-security lab in four categories (A stored passwords 1–8, B registration and identity 9–11, C sign-in defences 12–15, D integrity and lifecycle 16–20), each runnable on its own |
| `security_lab/password_storage_demo.py` | Runner for all 20 experiments and the 5 study paths (shared code in `lab_common.py`) |
| `docs/CRYPTOGRAPHY.md` | Cryptography teaching guide: hashes and checksums, PKI and certificates, signatures, post-quantum cryptography |
| `security_lab/crypto_a_hashing.py` … `crypto_e_post_quantum.py` | Cryptography lab in five categories (A hashing 1–7, B MACs/KDF/randomness 8–10, C PKI 11–14, D signatures 15–17, E post-quantum 18–20), each runnable on its own |
| `security_lab/crypto_lab.py` | Runner for all 20 crypto experiments and the 5 study paths; `--verify FILE` checks a download (shared code in `crypto_common.py`) |
| `docs/MACHINE_LEARNING_OPTIMISATION.md` | Machine-learning and optimisation teaching guide: the coupling BIP and its solvers, tuning, LSTM forecasting, Isolation Forest, reinforcement learning, evaluation |
| `ml_lab/ml_optimisation_lab.py` | Command-line lab that runs the paper's BIP, the three solvers, gradient descent vs Adam, Isolation Forest, REINFORCE and Q-learning |

## Experiment → script → result file

| Paper content | Script | Result file |
|---|---|---|
| Forecast accuracy, surge lead times, seeds | `run_forecast.py` | `results/forecast.json` |
| Out-of-distribution and cross-node tests | `run_ood.py` | `results/ood.json` |
| Anomaly detection metrics and sensitivity | `run_anomaly.py` | `results/anomaly.json` |
| Architecture comparison, statistical tests, forecaster value, ablation, load sweep, sensitivity | `run_cluster.py` | `results/cluster.json` |
| Connected-vehicle case study | `run_vehicle.py` | `results/vehicle.json` |
| Recovery time per crash class | `run_recovery_mc.py` | `results/recovery_mc.json` |
| BIP solve times | `run_bip_timing.py` | `results/bip_timing.json` |
| Prototype: call costs, switching, recovery | `prototype/proto_run.py` | `results/prototype.json` |
| Exact vs. linearised formulation, blast radius/availability, anomaly-detector value, combined-factor stress test (second revision) | `run_round2.py` | `results/round2.json` |

## Requirements

Python ≥ 3.10 (results produced with Python 3.13), numpy, scipy (≥ 1.11, for
`milp`), scikit-learn, PyTorch (CPU is sufficient), matplotlib, and `openssl`
for the prototype. See `requirements.txt`.

## Scope of the evidence

All data are synthetic. The simulator encodes the modelling assumptions listed
in `data/simulation_config.json` and in the paper (Table "Data-generation and
simulation parameters"). The prototype runs both processes on one host, so it
measures protocol and process-level overheads, not container orchestration or
cross-node networking. The three published autoscalers are re-implementations
of their decision strategies based on the literature, not the original systems.

## Citation

Please cite the article (see `CITATION.cff`; GitHub shows a "Cite this
repository" button).

## License

MIT — see `LICENSE`.
