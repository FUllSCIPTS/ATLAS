"""Build the Security & cryptography, Machine learning & optimisation and Data structures & algorithms catalogues.

One table below maps every concept taught in the Architecture Explorer's Security, Cryptography,
ML & Optimisation and Data Structures tabs to the function, constant or file that implements it. The script resolves
current line numbers and writes:

  docs/UML_BLUEPRINT.md   blocks between <!-- BEGIN/END SECURITY CATALOG -->, <!-- BEGIN/END ML CATALOG --> and
                          <!-- BEGIN/END DSA CATALOG -->,
                          one anchor per row
  ../dist/uml-catalog.js  the same rows for the explorer, so each lab links to its catalogue entry

Android app, research code (atlas_sim.zip, run_*.py), labs and workflow files live on the `main`
branch; pass a checkout of it:

    python scripts/security_catalog.py --main ../../ATLAS-main
    python scripts/security_catalog.py --main ../../ATLAS-main --check   # fail if stale
"""
import argparse
import ast
import io
import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]          # architecture-explorer/starter
EXPLORER = ROOT.parent                               # architecture-explorer
REPO = EXPLORER.parent                               # repository root (architecture-explorer branch)
MARKDOWN = ROOT / "docs/UML_BLUEPRINT.md"
SCRIPT_OUT = EXPLORER / "dist/uml-catalog.js"
BLUEPRINT_URL = "https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/docs/UML_BLUEPRINT.md"
MAIN_URL = "https://github.com/FUllSCIPTS/ATLAS/blob/main/"
ARCH_URL = "https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/"
EXPLORER_URL = "https://fullscipts.github.io/ATLAS/"
STATUS = {"impl": "Implemented", "demo": "Demo-grade", "teach": "Teaching extension", "lab": "Explorer / lab",
          "paper": "Paper (research code)", "synth": "App / starter (synthetic data)",
          "related": "Related (similar code, not this exact structure)"}

# Locations. "main:" = file on the main branch; "arch:" = file in architecture-explorer/;
# "zip:" = file inside prototype.zip on main; "sim:" = file inside atlas_sim.zip on main (the paper's
# simulator). Symbol "=NAME" finds an assignment, "~REGEX" a line.
ROWS = [
    # id, concept, location, symbol, status
    # ---- Security: password storage
    ("sec-pw-params", "Work factor and lockout limits", "main:android-app/atlas_go/accounts.py", "=PBKDF2_ITERATIONS", "impl"),
    ("sec-pw-hash", "Hash a password (salt + PBKDF2-HMAC-SHA256)", "main:android-app/atlas_go/accounts.py", "hash_password", "impl"),
    ("sec-pw-verify", "Verify a password (constant-time compare)", "main:android-app/atlas_go/accounts.py", "verify_password", "impl"),
    ("sec-pw-policy", "Password policy (8–128, letter + digit)", "main:android-app/atlas_go/accounts.py", "check_password", "impl"),
    ("sec-pw-public", "Strip salt and hash before display", "main:android-app/atlas_go/accounts.py", "public_view", "impl"),
    ("sec-pw-register", "Store only {salt, hash, iterations} at registration", "main:android-app/atlas_go/store.py", "LocalStore.register", "impl"),
    ("sec-pw-test", "Test: same password, different salts and hashes", "main:android-app/tests/test_accounts_geo.py", "test_password_hash_roundtrip_and_salt", "impl"),
    ("sec-pw-lab", "Explorer lab: PBKDF2 with the app's parameters", "arch:dist/security.js", "secPwHash", "lab"),
    ("sec-pw-lab-verify", "Explorer lab: verify_password replica", "arch:dist/security.js", "secPwVerify", "lab"),
    ("sec-pw-cli", "Command-line lab runner: all 20 experiments and 5 study paths", "main:security_lab/password_storage_demo.py", "~^if __name__ ==", "lab"),
    ("sec-pw-cli-common", "Lab helpers, experiment registry and command line", "main:security_lab/lab_common.py", "main", "lab"),
    ("sec-pw-cli-a", "Lab A: what the app stores (experiments 1-8)", "main:security_lab/lab_a_password_storage.py", "exp_record", "lab"),
    ("sec-pw-cli-b", "Lab B: registration and identity (experiments 9-11)", "main:security_lab/lab_b_registration_identity.py", "exp_validation", "lab"),
    ("sec-pw-cli-c", "Lab C: sign-in defences (experiments 12-15)", "main:security_lab/lab_c_signin_defences.py", "exp_lockout", "lab"),
    ("sec-pw-cli-d", "Lab D: integrity, sessions and lifecycle (experiments 16-20)", "main:security_lab/lab_d_integrity_lifecycle.py", "exp_sessions", "lab"),
    # ---- Security: login and lockout
    ("sec-login", "Sign in, 5 failures → 60 s lockout, generic error", "main:android-app/atlas_go/store.py", "LocalStore.login", "impl"),
    ("sec-login-failures", "Failure counter kept in memory only", "main:android-app/atlas_go/store.py", "~self.failures = \\{\\}", "impl"),
    ("sec-login-session", "Session validated on load (must name an account)", "main:android-app/atlas_go/store.py", "LocalStore.validate", "impl"),
    ("sec-login-guest", "Guest mode (no identity, least privilege)", "main:android-app/atlas_go/store.py", "LocalStore.continue_as_guest", "impl"),
    ("sec-login-logout", "Sign out", "main:android-app/atlas_go/store.py", "LocalStore.logout", "impl"),
    ("sec-login-clear", "Clear the password field after submit", "main:android-app/atlas_go/app.py", "AtlasGoApp.submit_login", "impl"),
    ("sec-login-lab", "Explorer lab: LocalStore.login replica", "arch:dist/security.js", "secLoginAttempt", "lab"),
    # ---- Security: identity and roles
    ("sec-id-email", "Identity proofing: email format", "main:android-app/atlas_go/accounts.py", "clean_email", "impl"),
    ("sec-id-phone", "Identity proofing: phone normalised to E.164", "main:android-app/atlas_go/accounts.py", "clean_phone", "impl"),
    ("sec-id-licence", "Driver licence number (self-declared)", "main:android-app/atlas_go/accounts.py", "clean_licence", "impl"),
    ("sec-id-business", "Food-business number (self-declared)", "main:android-app/atlas_go/accounts.py", "clean_business", "impl"),
    ("sec-id-delete", "De-provision with re-authentication, anonymise history", "main:android-app/atlas_go/store.py", "LocalStore.delete_account", "impl"),
    ("sec-rbac-screens", "RBAC layer 1: screen allow-list per role", "main:android-app/atlas_go/app.py", "AtlasGoApp.render", "impl"),
    ("sec-rbac-online", "RBAC layer 2: only drivers go online", "main:android-app/atlas_go/store.py", "LocalStore.set_online", "impl"),
    ("sec-rbac-location", "RBAC layer 2: only drivers share location", "main:android-app/atlas_go/store.py", "LocalStore.update_location", "impl"),
    ("sec-rbac-respond", "RBAC layer 2: a driver answers only their own job", "main:android-app/atlas_go/store.py", "LocalStore.driver_respond", "impl"),
    ("sec-rbac-book", "RBAC layer 2: only passengers or guests book", "main:android-app/atlas_go/store.py", "LocalStore.book", "impl"),
    ("sec-rbac-checkout", "RBAC layer 2: only passengers or guests order food", "main:android-app/atlas_go/store.py", "LocalStore.checkout", "impl"),
    ("sec-rbac-kitchen", "RBAC layer 2: a seller edits only their own kitchen", "main:android-app/atlas_go/store.py", "LocalStore._my_kitchen", "impl"),
    # ---- Security: gateway authentication
    ("sec-gw-routes", "Route allow-list (method, role, regex)", "arch:starter/services/gateway.py", "=ROUTES", "demo"),
    ("sec-gw-proxy", "Authenticate, check role, assert identity, forward", "arch:starter/services/gateway.py", "proxy", "demo"),
    ("sec-gw-keys", "Bearer keys per actor (demo defaults)", "arch:starter/packages/config.py", "=KEYS", "demo"),
    ("sec-gw-equal", "Timing-safe comparison (hmac.compare_digest)", "arch:starter/packages/config.py", "equal", "demo"),
    ("sec-gw-internal", "Service re-check: internal token and actor role", "arch:starter/packages/config.py", "internal_actor", "demo"),
    ("sec-gw-trips", "Trip Service accepts only gateway-asserted riders", "arch:starter/services/trips.py", "book", "demo"),
    ("sec-gw-dispatch", "Dispatch Service accepts only gateway-asserted drivers", "arch:starter/services/dispatch.py", "offers", "demo"),
    ("sec-gw-lab", "Explorer lab: gateway checks step by step", "arch:dist/security.js", "secGatewayRun", "lab"),
    # ---- Security: SSO (teaching extension)
    ("sec-sso-lab", "OIDC + PKCE flow with ES256 tokens", "arch:dist/security.js", "secSsoNext", "lab"),
    ("sec-sso-target", "Where JWT validation would replace bearer keys", "arch:starter/services/gateway.py", "proxy", "teach"),
    # ---- Security: Kerberos (teaching extension)
    ("sec-krb-setup", "KDC database and string-to-key (PBKDF2)", "arch:dist/security.js", "secKrbSetup", "lab"),
    ("sec-krb-messages", "The six messages AS-REQ … AP-REP", "arch:dist/security.js", "secKrbNext", "lab"),
    ("sec-krb-ap", "Service checks: integrity, expiry, skew, replay cache", "arch:dist/security.js", "secKrbVerifyAp", "lab"),
    ("sec-krb-seal", "AES-256-GCM seal used for tickets", "arch:dist/security.js", "secSeal", "lab"),
    ("sec-krb-target", "What a Kerberos AP-REQ would replace in Dispatch", "arch:starter/packages/config.py", "internal_actor", "teach"),
    # ---- Security: transport and deployment
    ("sec-tls-ca", "Private CA, serverAuth and clientAuth certificates", "zip:prototype/proto_run.py", "make_certs", "impl"),
    ("sec-tls-client", "Client presents its certificate, verifies the server", "zip:prototype/proto_run.py", "client_ctx", "impl"),
    ("sec-tls-server", "Server requires a client certificate (CERT_REQUIRED)", "zip:prototype/module_server.py", "~CERT_REQUIRED", "impl"),
    ("sec-dep-headers", "Security headers and CSP", "arch:server.mjs", "=securityHeaders", "impl"),
    ("sec-dep-reply", "Every response carries the headers", "arch:server.mjs", "reply", "impl"),
    ("sec-dep-loopback", "Listen on 127.0.0.1 only", "arch:server.mjs", "~\\.listen\\(", "impl"),
    ("sec-dep-systemd", "systemd sandbox (DynamicUser, ProtectSystem)", "arch:deploy/atlas-explorer.service", "~DynamicUser", "impl"),
    # ---- Cryptography: hashes and checksums
    ("cr-hash-sums", "Release SHA256SUMS written by CI", "main:.github/workflows/atlas-android.yml", "~> release/SHA256SUMS", "impl"),
    ("cr-hash-handover", "Release SHA256SUMS for hand-over", "main:android-app/scripts/finalize-handover.py", "~hashlib.sha256", "impl"),
    ("cr-hash-pin-tool", "Pinned build tool (bundletool SHA-256)", "main:.github/workflows/atlas-android.yml", "~sha256sum -c -", "impl"),
    ("cr-hash-record", "Signed bundle must equal the recorded SHA-256", "main:.github/workflows/publish-signed-android.yml", "~record\\['sha256'\\]", "impl"),
    ("cr-hash-restore", "Restore signed bundle; both hashes must match", "main:android-app/releases/restore-signed-bundle.py", "restore", "impl"),
    ("cr-hash-inventory", "SHA-256 of every source file in the blueprint", "arch:starter/scripts/generate_blueprint.py", "inventory", "impl"),
    ("cr-hash-checksum", "Non-cryptographic state checksum", "zip:prototype/module_server.py", "PaymentModule.checksum", "impl"),
    ("cr-hash-c3", "Recovery class C3: checksum mismatch → restore", "main:run_recovery_mc.py", "~C3", "impl"),
    ("cr-hash-lab-file", "Explorer lab: hash a download, compare with SHA256SUMS", "arch:dist/crypto.js", "crHashFile", "lab"),
    ("cr-hash-lab-avalanche", "Explorer lab: avalanche effect", "arch:dist/crypto.js", "crUpdateAvalanche", "lab"),
    ("cr-hash-lab-checksum", "Explorer lab: checksum vs SHA-256", "arch:dist/crypto.js", "crChecksum", "lab"),
    ("cr-hash-cli", "Lab A: hashing and integrity (experiments 1-7)", "main:security_lab/crypto_a_hashing.py", "exp_basics", "lab"),
    ("cr-hash-cli-checksum", "Lab A4: forging the prototype checksum", "main:security_lab/crypto_a_hashing.py", "exp_checksum", "lab"),
    ("cr-hash-cli-crc", "Lab A5: forging CRC32", "main:security_lab/crypto_a_hashing.py", "crc32_forge", "lab"),
    ("cr-hash-cli-release", "Lab A6-A7: verify releases and CI pins", "main:security_lab/crypto_a_hashing.py", "exp_release", "lab"),
    ("cr-mac-cli", "Lab B: MACs, key derivation, randomness (experiments 8-10)", "main:security_lab/crypto_b_mac_kdf_random.py", "exp_length_extension", "lab"),
    ("cr-mac-cli-pbkdf2", "Lab B9: PBKDF2 by hand, matching accounts.py", "main:security_lab/crypto_b_mac_kdf_random.py", "pbkdf2_sha256", "lab"),
    ("cr-cli-runner", "Crypto lab runner: 20 experiments, 5 study paths", "main:security_lab/crypto_lab.py", "~^if __name__ ==", "lab"),
    ("cr-cli-common", "Crypto lab helpers: toy RSA, PKCS#1 v1.5, DER reader", "main:security_lab/crypto_common.py", "emsa_pkcs1_v15", "lab"),
    # ---- Cryptography: PKI
    ("cr-pki-ca", "Private CA for mutual TLS", "zip:prototype/proto_run.py", "make_certs", "impl"),
    ("cr-pki-client", "Client context: trust anchor + client certificate", "zip:prototype/proto_run.py", "client_ctx", "impl"),
    ("cr-pki-server", "Server: CERT_REQUIRED against ca.crt", "zip:prototype/module_server.py", "~CERT_REQUIRED", "impl"),
    ("cr-pki-webpki", "Web PKI: HTTPS tile download verified with certifi", "main:android-app/atlas_go/livemap.py", "TileLoader._fetch", "impl"),
    ("cr-pki-cert", "Upload certificate (RSA-4096, self-signed)", "main:android-app/releases/upload-certificate.pem", "", "impl"),
    ("cr-pki-pin", "Certificate pinning: SHA-256 of the DER certificate", "main:android-app/scripts/ci-sign-bundle.py", "certificate_sha256", "impl"),
    ("cr-pki-pin-ci", "Publish workflow re-checks the pin", "main:.github/workflows/publish-signed-android.yml", "~upload_certificate_sha256", "impl"),
    ("cr-pki-lab-pin", "Explorer lab: recompute the real pin", "arch:dist/crypto.js", "crPin", "lab"),
    ("cr-pki-lab-issue", "Explorer lab: issue a certificate", "arch:dist/crypto.js", "crIssue", "lab"),
    ("cr-pki-lab-verify", "Explorer lab: chain, CA flag, validity, EKU checks", "arch:dist/crypto.js", "crVerifyCert", "lab"),
    ("cr-pki-cli", "Lab C: certificates and PKI (experiments 11-14)", "main:security_lab/crypto_c_pki.py", "exp_fingerprint", "lab"),
    ("cr-pki-cli-der", "Lab C12-C13: parse the DER, verify the self-signature", "main:security_lab/crypto_c_pki.py", "parse_certificate", "lab"),
    ("cr-pki-cli-ca", "Lab C14: private CA chain validation", "main:security_lab/crypto_c_pki.py", "validate", "lab"),
    # ---- Cryptography: signatures
    ("cr-sig-sign", "Sign the bundle: jarsigner SHA256withRSA, then verify", "main:android-app/scripts/sign-release.py", "main", "impl"),
    ("cr-sig-ci", "CI signing with the upload key from encrypted secrets", "main:android-app/scripts/ci-sign-bundle.py", "main", "impl"),
    ("cr-sig-apk", "APK Signature Scheme v2/v3; verify with apksigner", "main:android-app/releases/1.2.0/README.md", "~apksigner verify", "impl"),
    ("cr-sig-lab-keys", "Explorer lab: generate ECDSA or RSA key pair", "arch:dist/crypto.js", "crSigKeys", "lab"),
    ("cr-sig-lab-sign", "Explorer lab: hash-then-sign", "arch:dist/crypto.js", "crSigSign", "lab"),
    ("cr-sig-lab-verify", "Explorer lab: verify, tamper, wrong key", "arch:dist/crypto.js", "crSigVerify", "lab"),
    ("cr-sig-cli", "Lab D: digital signatures (experiments 15-17)", "main:security_lab/crypto_d_signatures.py", "exp_textbook", "lab"),
    ("cr-sig-cli-jar", "Lab D17: JAR signing and verification", "main:security_lab/crypto_d_signatures.py", "jar_verify", "lab"),
    # ---- Cryptography: post-quantum (teaching extension)
    ("cr-pqc-lab-keys", "Lamport keys from SHA-256 only", "arch:dist/crypto.js", "crLamportKeys", "lab"),
    ("cr-pqc-lab-sign", "Lamport sign: reveal one secret per hash bit", "arch:dist/crypto.js", "crLamportSign", "lab"),
    ("cr-pqc-lab-verify", "Lamport verify", "arch:dist/crypto.js", "crLamportVerify", "lab"),
    ("cr-pqc-lab-forge", "Forgery after key reuse", "arch:dist/crypto.js", "crLamportForge", "lab"),
    ("cr-pqc-cli", "Lab E: post-quantum (experiments 18-20)", "main:security_lab/crypto_e_post_quantum.py", "exp_lamport", "lab"),
    ("cr-pqc-cli-forge", "Lab E19: forging after Lamport key reuse", "main:security_lab/crypto_e_post_quantum.py", "exp_lamport_reuse", "lab"),
    ("cr-pqc-cli-hybrid", "Lab E20: toy LWE KEM in a hybrid with DH", "main:security_lab/crypto_e_post_quantum.py", "exp_lwe_hybrid", "lab"),
    # ---- ML & optimisation: the paper's coupling BIP
    ("ml-bip-modules", "Six modules: visit ratio and service demand", "sim:atlas_sim/traffic.py", "=VISIT", "paper"),
    ("ml-bip-params", "Objective weights, constraint limits, risk model", "sim:atlas_sim/cluster.py", "~^class Params", "paper"),
    ("ml-bip-model", "Predict latency, cost, risk, availability of all 2^n configurations", "sim:atlas_sim/cluster.py", "Sim.eval_all", "paper"),
    ("ml-bip-ref", "Same model for one configuration (reference point L0, C0)", "sim:atlas_sim/cluster.py", "Sim.eval_config", "paper"),
    ("ml-bip-solve", "Solve the BIP: objective J, constraints, argmin over all configurations", "sim:atlas_sim/cluster.py", "Sim.bip", "paper"),
    ("ml-bip-loop", "Decision epoch: forecast, anomaly score, BIP, overrides, hysteresis", "sim:atlas_sim/cluster.py", "Sim.run", "paper"),
    ("ml-bip-apply", "Apply: dual-run extraction, merge back", "sim:atlas_sim/cluster.py", "Sim.apply", "paper"),
    ("ml-bip-fsm", "Ablation baseline: fixed load thresholds", "sim:atlas_sim/cluster.py", "Sim.fsm_thresholds", "paper"),
    ("ml-bip-lab", "Explorer lab: Sim.eval_all + Sim.bip replica", "arch:dist/ml.js", "mlBipSolve", "lab"),
    ("ml-bip-lab-eval", "Explorer lab: one configuration's latency, cost, risk", "arch:dist/ml.js", "mlEvalConfig", "lab"),
    ("ml-bip-cli", "Command-line lab: load sweep with the real Sim.bip", "main:ml_lab/ml_optimisation_lab.py", "section_bip", "lab"),
    ("ml-bip-cli-inside", "Command-line lab: every configuration at one load", "main:ml_lab/ml_optimisation_lab.py", "section_inside", "lab"),
    ("ml-bip-cli-anomaly", "Command-line lab: anomaly score raises crash risk", "main:ml_lab/ml_optimisation_lab.py", "section_anomaly", "lab"),
    # ---- ML & optimisation: solvers
    ("ml-sol-instance", "Random linearised BIP instances, n = 6 ... 500", "main:run_bip_timing.py", "instance", "paper"),
    ("ml-sol-lpround", "LP relaxation + risk-aware rounding + greedy repair", "main:run_bip_timing.py", "lp_round", "paper"),
    ("ml-sol-milp", "Branch-and-bound (HiGHS via scipy.optimize.milp)", "main:run_bip_timing.py", "~m = milp\\(", "paper"),
    ("ml-sol-model", "Nonlinear model used to judge every method", "main:run_round2.py", "model", "paper"),
    ("ml-sol-solveall", "Exact enumeration vs linearised BIP vs LP method", "main:run_round2.py", "solve_all", "paper"),
    ("ml-sol-repair", "Phase 3: verify on the nonlinear model, greedy flips", "main:run_round2.py", "repair", "paper"),
    ("ml-sol-refined", "Sequential linearisation", "main:run_round2.py", "solve_refined", "paper"),
    ("ml-sol-local", "1-flip local search on the nonlinear objective", "main:run_round2.py", "local_search", "paper"),
    ("ml-sol-lab", "Explorer lab: enumerate 2^n in the browser", "arch:dist/ml.js", "mlEnumerateTiming", "lab"),
    ("ml-sol-cli", "Command-line lab: enumeration vs branch-and-bound vs LP", "main:ml_lab/ml_optimisation_lab.py", "section_solvers", "lab"),
    # ---- ML & optimisation: forecasting
    ("ml-fc-trace", "Paper traffic model: daily, weekly, noise, flash sales", "sim:atlas_sim/traffic.py", "ecommerce_trace", "paper"),
    ("ml-fc-lstm", "LSTM / Bi-LSTM forecaster (2 x 128, dropout 0.2)", "sim:atlas_sim/forecast.py", "~^class LSTMForecaster", "paper"),
    ("ml-fc-train", "Training: Adam, gradient clipping, early stopping", "sim:atlas_sim/forecast.py", "train", "paper"),
    ("ml-fc-ar", "Baseline: Ridge autoregression", "sim:atlas_sim/forecast.py", "fit_ar", "paper"),
    ("ml-fc-naive", "Baseline: seasonal naive", "sim:atlas_sim/forecast.py", "seasonal_naive", "paper"),
    ("ml-fc-run", "Experiment: 3 seeds, horizons 5, 15, 60 min", "main:run_forecast.py", "=H", "paper"),
    ("ml-fc-starter", "Starter DemandLSTM trained with Adam", "arch:starter/ml/forecast.py", "train", "synth"),
    ("ml-fc-app", "App LSTM in numpy with a hand-written Adam step", "main:android-app/training/city_sim.py", "LSTM.step", "synth"),
    ("ml-fc-lab", "Explorer lab: AR forecaster, gradient descent vs Adam", "arch:dist/ml.js", "mlTrainForecaster", "lab"),
    ("ml-fc-cli", "Command-line lab: gradient descent vs Adam vs least squares", "main:ml_lab/ml_optimisation_lab.py", "section_training", "lab"),
    # ---- ML & optimisation: anomaly detection
    ("ml-an-run", "Isolation Forest, normalised score (paper experiment)", "main:run_anomaly.py", "norm_score", "paper"),
    ("ml-an-fit", "Fit on unlabelled telemetry (100 trees, 256 samples)", "main:run_anomaly.py", "~m = IsolationForest\\(", "paper"),
    ("ml-an-telemetry", "Telemetry and injected fault types", "sim:atlas_sim/traffic.py", "telemetry", "paper"),
    ("ml-an-score", "Score inside the simulator; blame a module", "sim:atlas_sim/cluster.py", "Sim.score", "paper"),
    ("ml-an-fast", "Path-length scorer re-implemented for one row", "sim:atlas_sim/cluster.py", "FastIForest.score_samples", "paper"),
    ("ml-an-starter", "Starter: acceptance model + driver Isolation Forest", "arch:starter/ml/discrete.py", "train", "synth"),
    ("ml-an-serve", "Starter: anomaly flag per driver in the scoring API", "arch:starter/ml/serve.py", "score", "synth"),
    ("ml-an-lab", "Explorer lab: grow an Isolation Forest", "arch:dist/ml.js", "mlForestGrow", "lab"),
    ("ml-an-cli", "Command-line lab: Isolation Forest on paper telemetry", "main:ml_lab/ml_optimisation_lab.py", "section_iforest", "lab"),
    # ---- ML & optimisation: reinforcement learning
    ("ml-rl-ride", "Ride dispatch: REINFORCE training", "main:android-app/training/rl_sim.py", "train_ride", "synth"),
    ("ml-rl-food", "Courier timing: tabular Q-learning", "main:android-app/training/rl_sim.py", "train_food", "synth"),
    ("ml-rl-weights", "Approved dispatch weights (policy v1.4)", "main:android-app/atlas_go/learned.py", "=RIDE_WEIGHTS", "synth"),
    ("ml-rl-rank", "Dispatch: softmax over candidate drivers", "main:android-app/atlas_go/intelligence.py", "rank", "synth"),
    ("ml-rl-learnlab", "On-device learning lab (REINFORCE, sandbox)", "main:android-app/atlas_go/intelligence.py", "LearningLab.train", "synth"),
    ("ml-rl-courier", "Courier plan from the learned Q-table", "main:android-app/atlas_go/intelligence.py", "courier_plan", "synth"),
    ("ml-rl-accept", "Acceptance: Beta(9, 1) posterior mean", "main:android-app/atlas_go/intelligence.py", "acceptance", "synth"),
    ("ml-rl-supply", "Driver supply agent with hindsight updates", "main:android-app/training/city_sim.py", "run_rl", "synth"),
    ("ml-rl-bandit", "Starter: action values per demand bucket", "arch:starter/ml/rl.py", "fit", "synth"),
    ("ml-rl-approve", "Starter: held-out approval gate before activation", "arch:starter/ml/rl.py", "approve", "synth"),
    ("ml-rl-lab", "Explorer lab: REINFORCE (LearningLab.train port)", "arch:dist/ml.js", "mlRlTrain", "lab"),
    ("ml-rl-cli", "Command-line lab: REINFORCE and Q-learning", "main:ml_lab/ml_optimisation_lab.py", "section_rl", "lab"),
    # ---- ML & optimisation: tuning and evaluation
    ("ml-ev-tune", "Grid search on validation seeds", "main:run_cluster.py", "tune", "paper"),
    # ---- ML & optimisation: the 40-experiment labs (ml_lab/machine_learning, ml_lab/optimisation)
    ("ml-x-opt-runner", "Optimisation lab runner: 20 experiments, 7 study paths", "main:ml_lab/optimisation/run_optimisation.py", "main", "lab"),
    ("ml-x-opt-ga", "OPT 17: genetic algorithm vs Sim.bip", "main:ml_lab/optimisation/opt17_genetic_algorithm.py", "evolve", "lab"),
    ("ml-x-opt-pareto", "OPT 20: latency-cost Pareto front of the couplings", "main:ml_lab/optimisation/opt20_multi_objective_pareto.py", "pareto_ranks", "lab"),
    ("ml-x-opt-cores", "OPT 04: KKT core allocation across the six modules", "main:ml_lab/optimisation/opt04_constrained_core_allocation.py", "main", "lab"),
    ("ml-x-opt-dpscale", "OPT 14: DP replica schedule with switching costs", "main:ml_lab/optimisation/opt14_dp_autoscaling_schedule.py", "main", "lab"),
    ("ml-x-opt-bb", "OPT 08: branch-and-bound by hand on the coupling BIP", "main:ml_lab/optimisation/opt08_branch_and_bound.py", "branch_and_bound", "lab"),
    ("ml-x-opt-tabu", "OPT 15: local search and tabu search on a 60-module BIP", "main:ml_lab/optimisation/opt15_local_search_tabu.py", "tabu", "lab"),
    ("ml-x-opt-lp", "OPT 05-06: LP, duality and shadow prices", "main:ml_lab/optimisation/opt05_linear_programming_transport.py", "solve", "lab"),
    ("ml-x-opt-sa", "OPT 16: simulated annealing", "main:ml_lab/optimisation/opt16_simulated_annealing.py", "anneal", "lab"),
    ("ml-x-opt-gd", "OPT 01-03: gradient descent, Adam, Newton and BFGS", "main:ml_lab/optimisation/opt02_momentum_and_adam.py", "optimise", "lab"),
    ("ml-x-ml-runner", "ML lab runner: 20 experiments, 7 study paths", "main:ml_lab/machine_learning/run_ml.py", "main", "lab"),
    ("ml-x-ml-hw", "ML 16: Holt-Winters and forecasting baselines", "main:ml_lab/machine_learning/ml16_time_series_forecasting.py", "holt_winters", "lab"),
    ("ml-x-ml-cv", "ML 11: time-series cross-validation and leakage", "main:ml_lab/machine_learning/ml11_cross_validation_leakage.py", "main", "lab"),
    ("ml-x-ml-drift", "ML 17: concept drift and online learning", "main:ml_lab/machine_learning/ml17_concept_drift_online.py", "main", "lab"),
    ("ml-x-opt-bo", "OPT 19: Bayesian optimisation of the forecaster", "main:ml_lab/optimisation/opt19_bayesian_optimisation.py", "main", "lab"),
    ("ml-x-ml-detect", "ML 15: z-score, Mahalanobis, Isolation Forest, LOF", "main:ml_lab/machine_learning/ml15_anomaly_detection.py", "main", "lab"),
    ("ml-x-ml-pca", "ML 14: PCA reconstruction error", "main:ml_lab/machine_learning/ml14_pca.py", "main", "lab"),
    ("ml-x-ml-logit", "ML 03: logistic regression from scratch", "main:ml_lab/machine_learning/ml03_logistic_regression.py", "sigmoid", "lab"),
    ("ml-x-ml-ens", "ML 07: forests and boosting", "main:ml_lab/machine_learning/ml07_ensembles.py", "main", "lab"),
    ("ml-x-ml-nn", "ML 09: neural network with backpropagation", "main:ml_lab/machine_learning/ml09_neural_network_backprop.py", "main", "lab"),
    ("ml-x-ml-q", "ML 20: Q-learning the courier table", "main:ml_lab/machine_learning/ml20_q_learning_courier.py", "main", "lab"),
    ("ml-x-ml-bandit", "ML 19: epsilon-greedy, UCB1, Thompson", "main:ml_lab/machine_learning/ml19_bandits.py", "simulate", "lab"),
    ("ml-x-ml-rank", "ML 18: learning to rank dispatch candidates", "main:ml_lab/machine_learning/ml18_learning_to_rank.py", "main", "lab"),
    ("ml-x-opt-es", "OPT 18: ES, DE and PSO tune the dispatch weights", "main:ml_lab/optimisation/opt18_evolution_strategies_de_pso.py", "dispatch_objective", "lab"),
    ("ml-x-ml-metrics", "ML 10: metrics under class imbalance", "main:ml_lab/machine_learning/ml10_metrics_and_imbalance.py", "main", "lab"),
    ("ml-x-ml-bv", "ML 02: bias, variance and ridge", "main:ml_lab/machine_learning/ml02_bias_variance_regularisation.py", "main", "lab"),
    ("ml-ev-grid", "ATLAS tuning grid", "main:run_cluster.py", "~\"atlas\": \\[dict\\(switch_pen", "paper"),
    ("ml-ev-ablation", "Ablation: remove one component at a time", "main:run_cluster.py", "~if \"ablation\" in which", "paper"),
    ("ml-ev-compare", "Paired Wilcoxon test + rank-biserial effect size", "main:run_cluster.py", "compare", "paper"),
    ("ml-ev-holm", "Holm-Bonferroni correction", "main:run_cluster.py", "holm", "paper"),
    ("ml-ev-stat", "Mean, SD, 95 % t-interval over 30 runs", "main:run_cluster.py", "stat_block", "paper"),
    ("ml-ev-boot", "Block bootstrap CI for forecast errors", "sim:atlas_sim/forecast.py", "block_bootstrap_ci", "paper"),
    # ---- Data structures & algorithms: ATLAS Go code that uses the idea
    ("dsa-app-book", "ADT operation: book a ride", "main:android-app/atlas_go/store.py", "LocalStore.book", "impl"),
    ("dsa-app-checkout", "ADT operation: check out a cart", "main:android-app/atlas_go/store.py", "LocalStore.checkout", "impl"),
    ("dsa-app-online", "Linear scan: drivers that are online", "main:android-app/atlas_go/store.py", "LocalStore.online_drivers", "impl"),
    ("dsa-app-history", "Linear scan: the user's ride and order history", "main:android-app/atlas_go/store.py", "LocalStore.my_history", "impl"),
    ("dsa-app-distances", "2-D table lookup DISTANCES[pickup][destination]", "main:android-app/atlas_go/domain.py", "=DISTANCES", "impl"),
    ("dsa-app-nearest", "Minimum selection: nearest saved place", "main:android-app/atlas_go/geo.py", "nearest_place", "impl"),
    ("dsa-app-tiles", "Grid indexing: tiles that cover the view", "main:android-app/atlas_go/geo.py", "tile_range", "impl"),
    ("dsa-app-fare", "Fare rule evaluated with a stack in the explorer", "main:android-app/atlas_go/domain.py", "fare", "impl"),
    ("dsa-app-lifo", "LIFO work queue: newest tile request first", "main:android-app/atlas_go/livemap.py", "~self.requests = queue.LifoQueue", "impl"),
    ("dsa-app-lru-hit", "LRU cache hit: move_to_end on the OrderedDict", "main:android-app/atlas_go/livemap.py", "TileLoader.texture", "impl"),
    ("dsa-app-lru-evict", "LRU eviction: popitem(last=False) past 160 tiles", "main:android-app/atlas_go/livemap.py", "~self.textures.popitem\\(last=False\\)", "impl"),
    ("dsa-app-dishes", "Hash table: dish id to Dish", "main:android-app/atlas_go/domain.py", "=DISHES", "impl"),
    ("dsa-app-cart", "Hash table: cart quantities per dish", "main:android-app/atlas_go/domain.py", "Cart.add", "impl"),
    ("dsa-app-menu", "Linear filter: a kitchen's menu", "main:android-app/atlas_go/domain.py", "Catalog.menu", "impl"),
    ("dsa-app-pools", "Drivers and pickup minutes used by the heap and sorting labs", "main:android-app/atlas_go/intelligence.py", "=DRIVER_POOLS", "impl"),
    ("dsa-app-rank", "Sorting: rank candidates with sorted()", "main:android-app/atlas_go/intelligence.py", "rank", "impl"),
    ("dsa-app-choose", "Selection: take the best candidate; min for the nearest", "main:android-app/atlas_go/intelligence.py", "choose", "impl"),
    ("dsa-app-zones", "Zone coordinates: the graph lab's vertices", "main:android-app/atlas_go/geo.py", "=ZONE_COORDS", "impl"),
    ("dsa-app-haversine", "Great-circle distance: the graph lab's edge weights", "main:android-app/atlas_go/geo.py", "haversine_km", "impl"),
    ("dsa-app-legs", "Straight-line trip legs (no road graph)", "main:android-app/atlas_go/geo.py", "ride_legs", "related"),
    ("dsa-app-advance", "State machine: advance a ride", "main:android-app/atlas_go/store.py", "LocalStore.advance_ride", "related"),
    ("dsa-app-validate", "Invariant check on saved state", "main:android-app/atlas_go/store.py", "LocalStore.validate", "impl"),
    ("dsa-app-selftest", "Self-test of the on-device models", "main:android-app/atlas_go/intelligence.py", "self_test", "impl"),
    # ---- Data structures & algorithms: course implementations (dsa_lab on main)
    ("dsa-lab-linear", "Linear search with a comparison count", "main:dsa_lab/experiments.py", "linear_search", "lab"),
    ("dsa-lab-binary", "Binary search with a comparison count", "main:dsa_lab/experiments.py", "binary_search", "lab"),
    ("dsa-lab-first", "First occurrence (bisect_left)", "main:dsa_lab/experiments.py", "first_occurrence", "lab"),
    ("dsa-lab-dynarray", "Dynamic array: growth policy and copies", "main:dsa_lab/experiments.py", "DynamicArray.append", "lab"),
    ("dsa-lab-sll-popback", "Singly linked list: pop_back walks to the predecessor", "main:dsa_lab/experiments.py", "SinglyLinkedList.pop_back", "lab"),
    ("dsa-lab-dll-unlink", "Doubly linked list: unlink a known node", "main:dsa_lab/experiments.py", "DoublyLinkedList.unlink", "lab"),
    ("dsa-lab-csll", "Circular singly linked list: tail only, head = tail.next", "main:dsa_lab/experiments.py", "~^class CircularSinglyLinkedList", "lab"),
    ("dsa-lab-csll-rotate", "Circular singly list: rotate by moving the tail", "main:dsa_lab/experiments.py", "CircularSinglyLinkedList.rotate", "lab"),
    ("dsa-lab-cdll", "Circular doubly linked list with a sentinel", "main:dsa_lab/experiments.py", "~^class CircularDoublyLinkedList", "lab"),
    ("dsa-lab-cdll-insert", "Sentinel list: insert_after, the only insertion primitive", "main:dsa_lab/experiments.py", "CircularDoublyLinkedList.insert_after", "lab"),
    ("dsa-lab-cdll-rotate", "Sentinel list: rotate by moving the sentinel", "main:dsa_lab/experiments.py", "CircularDoublyLinkedList.rotate", "lab"),
    ("dsa-lab-josephus", "Josephus problem on a circular singly list", "main:dsa_lab/experiments.py", "josephus_circular", "lab"),
    ("dsa-lab-floyd", "Floyd's tortoise and hare: mu and lambda", "main:dsa_lab/experiments.py", "floyd_cycle", "lab"),
    ("dsa-lab-postfix", "Stack: evaluate a postfix expression", "main:dsa_lab/experiments.py", "evaluate_postfix", "lab"),
    ("dsa-lab-ring", "Ring buffer: enqueue at (front + count) % capacity", "main:dsa_lab/experiments.py", "RingBuffer.enqueue", "lab"),
    ("dsa-lab-lru", "LRU cache: dict + circular doubly list", "main:dsa_lab/experiments.py", "LRUCache.get", "lab"),
    ("dsa-lab-chain", "Hash table with separate chaining and resizing", "main:dsa_lab/experiments.py", "ChainHash.put", "lab"),
    ("dsa-lab-probe", "Open addressing: linear probing", "main:dsa_lab/experiments.py", "OpenAddressHash.put", "lab"),
    ("dsa-lab-tomb", "Open addressing: delete with a tombstone", "main:dsa_lab/experiments.py", "OpenAddressHash.delete", "lab"),
    ("dsa-lab-bstdel", "BST delete: the three cases", "main:dsa_lab/experiments.py", "bst_delete", "lab"),
    ("dsa-lab-avl", "AVL insert with the four rotations", "main:dsa_lab/experiments.py", "avl_insert", "lab"),
    ("dsa-lab-traversal", "Level-order traversal with a queue", "main:dsa_lab/experiments.py", "levelorder_queue", "lab"),
    ("dsa-lab-heap", "Binary min-heap: sift up", "main:dsa_lab/experiments.py", "MinHeap.push", "lab"),
    ("dsa-lab-trie", "Trie: prefix query", "main:dsa_lab/experiments.py", "Trie.starts_with", "lab"),
    ("dsa-lab-bfs", "Breadth-first search", "main:dsa_lab/experiments.py", "bfs", "lab"),
    ("dsa-lab-dfs", "Depth-first search", "main:dsa_lab/experiments.py", "dfs", "lab"),
    ("dsa-lab-dijkstra", "Dijkstra with a binary heap", "main:dsa_lab/experiments.py", "dijkstra", "lab"),
    ("dsa-lab-kruskal", "Kruskal minimum spanning tree with union-find", "main:dsa_lab/experiments.py", "kruskal", "lab"),
    ("dsa-lab-topo", "Topological sort (Kahn)", "main:dsa_lab/experiments.py", "topo_sort_kahn", "lab"),
    ("dsa-lab-insertion", "Insertion sort with counts", "main:dsa_lab/experiments.py", "insertion_sort", "lab"),
    ("dsa-lab-merge", "Merge sort with counts", "main:dsa_lab/experiments.py", "merge_sort", "lab"),
    ("dsa-lab-quick", "Quick sort, random pivot (Lomuto)", "main:dsa_lab/experiments.py", "quick_sort_inplace", "lab"),
    ("dsa-lab-heapsort", "Heap sort", "main:dsa_lab/experiments.py", "heap_sort", "lab"),
    ("dsa-lab-stable", "Count stability violations", "main:dsa_lab/experiments.py", "stability_violations", "lab"),
    ("dsa-lab-fib", "Fibonacci with a memo: call count", "main:dsa_lab/experiments.py", "fib_memo_calls", "lab"),
    ("dsa-lab-knapsack", "0/1 knapsack by dynamic programming", "main:dsa_lab/experiments.py", "knapsack_01", "lab"),
    ("dsa-lab-queens", "N queens by backtracking", "main:dsa_lab/experiments.py", "n_queens", "lab"),
    ("dsa-lab-runner", "Experiment runner E01-E30", "main:dsa_lab/experiments.py", "run_experiment", "lab"),
    ("dsa-lab-selftest", "Self-test of every structure's invariants", "main:dsa_lab/experiments.py", "self_test", "lab"),
    # ---- Data structures & algorithms: explorer labs
    ("dsa-x-lists", "Explorer: draw a list by walking its pointers", "arch:dist/dsa.js", "dsaListSvg", "lab"),
    ("dsa-x-csll", "Explorer: circular singly list (port)", "arch:dist/dsa.js", "~^class DsaCircularSingly", "lab"),
    ("dsa-x-cdll", "Explorer: circular doubly list with sentinel (port)", "arch:dist/dsa.js", "~^class DsaCircularDoubly", "lab"),
    ("dsa-x-josephus", "Explorer: Josephus step", "arch:dist/dsa.js", "dsaJosStep", "lab"),
    ("dsa-x-floyd", "Explorer: tortoise and hare step", "arch:dist/dsa.js", "dsaFloydStep", "lab"),
    ("dsa-x-ring", "Explorer: ring buffer", "arch:dist/dsa.js", "dsaRingOp", "lab"),
    ("dsa-x-lru", "Explorer: LRU cache", "arch:dist/dsa.js", "dsaLruGet", "lab"),
    ("dsa-x-hash", "Explorer: chaining and probing table", "arch:dist/dsa.js", "dsaHashPut", "lab"),
    ("dsa-x-avl", "Explorer: AVL insert", "arch:dist/dsa.js", "dsaAvlInsert", "lab"),
    ("dsa-x-heap", "Explorer: driver min-heap", "arch:dist/dsa.js", "dsaHeapPush", "lab"),
    ("dsa-x-graph", "Explorer: BFS, DFS, Dijkstra and Prim frames", "arch:dist/dsa.js", "dsaGraphFrames", "lab"),
    ("dsa-x-sort", "Explorer: counting sorts", "arch:dist/dsa.js", "dsaSortRun", "lab"),
    ("dsa-x-knapsack", "Explorer: knapsack table", "arch:dist/dsa.js", "dsaKnapsack", "lab"),
    # ---- Cryptography and Security: Foundations (standalone units + live labs in foundations.js)
    ("cr-fd-guide", "Guide: 19 standalone cryptography units (what, why, how)", "main:docs/CRYPTOGRAPHY.md", "~^## Standalone illustrated foundations", "teach"),
    ("cr-fd-rsa-unit", "Guide unit C7.1: RSA", "main:docs/CRYPTOGRAPHY.md", "~^### C7.1 ", "teach"),
    ("cr-fd-dh-unit", "Guide unit C7.2: Diffie–Hellman, ECDH, X25519", "main:docs/CRYPTOGRAPHY.md", "~^### C7.2 ", "teach"),
    ("cr-fd-ecdsa-unit", "Guide unit C7.3: elliptic curves and ECDSA", "main:docs/CRYPTOGRAPHY.md", "~^### C7.3 ", "teach"),
    ("cr-fd-mlkem-unit", "Guide unit C10.1: ML-KEM (FIPS 203)", "main:docs/CRYPTOGRAPHY.md", "~^### C10.1 ", "teach"),
    ("cr-fd-mldsa-unit", "Guide unit C10.2: ML-DSA (FIPS 204) and FN-DSA", "main:docs/CRYPTOGRAPHY.md", "~^### C10.2 ", "teach"),
    ("cr-fd-slh-unit", "Guide unit C10.3: hash-based signatures and SLH-DSA (FIPS 205)", "main:docs/CRYPTOGRAPHY.md", "~^### C10.3 ", "teach"),
    ("cr-fd-units", "Explorer: unit data (what, why, how, pitfalls)", "arch:dist/foundations.js", "=fdCryptoUnits", "lab"),
    ("cr-fd-lab-rsa", "Explorer lab: textbook RSA, CRT and malleability", "arch:dist/foundations.js", "fdRsaLab", "lab"),
    ("cr-fd-lab-oaep", "Explorer lab: real RSA-OAEP 2048", "arch:dist/foundations.js", "fdRsaOaep", "lab"),
    ("cr-fd-lab-dh", "Explorer lab: Diffie–Hellman and a man in the middle", "arch:dist/foundations.js", "fdDhLab", "lab"),
    ("cr-fd-lab-ecdh", "Explorer lab: real ECDH P-256 and X25519", "arch:dist/foundations.js", "fdEcdh", "lab"),
    ("cr-fd-lab-ecdsa", "Explorer lab: toy ECDSA and nonce-reuse key recovery", "arch:dist/foundations.js", "fdEcdsaRun", "lab"),
    ("cr-fd-lab-aead", "Explorer lab: AES-GCM tampering and nonce reuse", "arch:dist/foundations.js", "fdAeadRun", "lab"),
    ("cr-fd-lab-lwe", "Explorer lab: one-bit LWE encryption", "arch:dist/foundations.js", "fdLweRun", "lab"),
    ("cr-fd-lab-kem", "Explorer lab: toy ML-KEM-shaped KEM with implicit rejection", "arch:dist/foundations.js", "fdKemRun", "lab"),
    ("cr-fd-lab-mldsa", "Explorer lab: ML-DSA rejection sampling", "arch:dist/foundations.js", "fdMldsaRun", "lab"),
    ("cr-fd-lab-wots", "Explorer lab: Winternitz one-time signature and Merkle root", "arch:dist/foundations.js", "fdWotsRun", "lab"),
    ("cr-fd-cli-rsa", "Lab D15: textbook RSA and malleability", "main:security_lab/crypto_d_signatures.py", "exp_textbook", "lab"),
    ("cr-fd-cli-lwe", "Lab E20: toy LWE KEM in a hybrid with DH", "main:security_lab/crypto_e_post_quantum.py", "exp_lwe_hybrid", "lab"),
    ("sec-fd-guide", "Guide: 19 standalone information-security units (what, why, how)", "main:docs/INFORMATION_SECURITY.md", "~^## Standalone illustrated foundations", "teach"),
    ("sec-fd-units", "Explorer: unit data (what, why, how, pitfalls)", "arch:dist/foundations.js", "=fdSecUnits", "lab"),
    ("sec-fd-lab-access", "Explorer lab: role, ownership and state checks", "arch:dist/foundations.js", "fdAccessLab", "lab"),
    ("sec-fd-lab-entropy", "Explorer lab: password guessability", "arch:dist/foundations.js", "fdEntropyLab", "lab"),
    ("sec-fd-lab-totp", "Explorer lab: TOTP (RFC 6238) with Web Crypto", "arch:dist/foundations.js", "fdTotp", "lab"),
    ("sec-fd-lab-pkce", "Explorer lab: PKCE S256 (RFC 7636)", "arch:dist/foundations.js", "fdPkceRun", "lab"),
    ("sec-fd-lab-inject", "Explorer lab: SQL injection and XSS encoding", "arch:dist/foundations.js", "fdInjectLab", "lab"),
]

# Explorer topics → rows. Rows may appear under several topics.
TOPICS = {
    "security/passwords": ["sec-pw-params", "sec-pw-hash", "sec-pw-verify", "sec-pw-policy", "sec-pw-public", "sec-pw-register", "sec-pw-test", "sec-pw-lab", "sec-pw-lab-verify", "sec-pw-cli", "sec-pw-cli-a", "sec-pw-cli-common"],
    "security/login": ["sec-login", "sec-login-failures", "sec-login-session", "sec-login-guest", "sec-login-logout", "sec-login-clear", "sec-pw-verify", "sec-login-lab", "sec-pw-cli-c", "sec-pw-cli-d"],
    "security/identity": ["sec-pw-register", "sec-id-email", "sec-id-phone", "sec-id-licence", "sec-id-business", "sec-id-delete", "sec-rbac-screens", "sec-rbac-online", "sec-rbac-location", "sec-rbac-respond", "sec-rbac-book", "sec-rbac-checkout", "sec-rbac-kitchen", "sec-pw-cli-b", "sec-pw-cli-d"],
    "security/gateway": ["sec-gw-routes", "sec-gw-proxy", "sec-gw-keys", "sec-gw-equal", "sec-gw-internal", "sec-gw-trips", "sec-gw-dispatch", "sec-gw-lab"],
    "security/sso": ["sec-sso-target", "sec-gw-keys", "sec-sso-lab"],
    "security/kerberos": ["sec-krb-target", "sec-krb-setup", "sec-krb-messages", "sec-krb-ap", "sec-krb-seal"],
    "security/transport": ["sec-tls-ca", "sec-tls-client", "sec-tls-server", "sec-dep-headers", "sec-dep-reply", "sec-dep-loopback", "sec-dep-systemd", "cr-sig-sign"],
    "security/learn": ["sec-fd-guide", "sec-fd-units", "sec-fd-lab-access", "sec-fd-lab-entropy", "sec-fd-lab-totp", "sec-fd-lab-pkce", "sec-fd-lab-inject", "sec-pw-hash", "sec-rbac-screens", "sec-sso-lab"],
    "security/gaps": ["sec-pw-params", "sec-login-failures", "sec-gw-keys", "sec-gw-internal", "sec-id-licence", "sec-gw-proxy"],
    "crypto/hashes": ["cr-hash-sums", "cr-hash-handover", "cr-hash-pin-tool", "cr-hash-record", "cr-hash-restore", "cr-hash-inventory", "cr-hash-checksum", "cr-hash-c3", "cr-hash-lab-avalanche", "cr-hash-lab-file", "cr-hash-lab-checksum", "cr-hash-cli", "cr-hash-cli-checksum", "cr-hash-cli-crc", "cr-hash-cli-release", "cr-mac-cli", "cr-mac-cli-pbkdf2", "cr-cli-runner"],
    "crypto/pki": ["cr-pki-ca", "cr-pki-client", "cr-pki-server", "cr-pki-webpki", "cr-pki-cert", "cr-pki-pin", "cr-pki-pin-ci", "cr-pki-lab-pin", "cr-pki-lab-issue", "cr-pki-lab-verify", "cr-pki-cli", "cr-pki-cli-der", "cr-pki-cli-ca", "cr-cli-common"],
    "crypto/signatures": ["cr-sig-sign", "cr-sig-ci", "cr-pki-pin", "cr-sig-apk", "cr-sig-lab-keys", "cr-sig-lab-sign", "cr-sig-lab-verify", "cr-sig-cli", "cr-sig-cli-jar"],
    "crypto/pqc": ["cr-pki-webpki", "cr-pki-ca", "cr-sig-sign", "cr-pqc-lab-keys", "cr-pqc-lab-sign", "cr-pqc-lab-verify", "cr-pqc-lab-forge", "cr-pqc-cli", "cr-pqc-cli-forge", "cr-pqc-cli-hybrid"],
    "crypto/learn": ["cr-fd-guide", "cr-fd-rsa-unit", "cr-fd-dh-unit", "cr-fd-ecdsa-unit", "cr-fd-mlkem-unit", "cr-fd-mldsa-unit", "cr-fd-slh-unit", "cr-fd-units", "cr-fd-lab-rsa", "cr-fd-lab-oaep", "cr-fd-lab-dh", "cr-fd-lab-ecdh", "cr-fd-lab-ecdsa", "cr-fd-lab-aead", "cr-fd-lab-lwe", "cr-fd-lab-kem", "cr-fd-lab-mldsa", "cr-fd-lab-wots", "cr-fd-cli-rsa", "cr-fd-cli-lwe"],
    "crypto/gaps": ["cr-hash-checksum", "cr-hash-sums", "cr-pki-cert", "cr-pki-webpki", "sec-gw-internal"],
    "ml/optimizer": ["ml-bip-modules", "ml-bip-params", "ml-bip-model", "ml-bip-ref", "ml-bip-solve", "ml-bip-loop", "ml-bip-apply", "ml-bip-fsm", "ml-bip-lab", "ml-bip-lab-eval", "ml-bip-cli", "ml-bip-cli-inside", "ml-bip-cli-anomaly", "ml-x-opt-runner", "ml-x-opt-ga", "ml-x-opt-pareto", "ml-x-opt-cores", "ml-x-opt-dpscale"],
    "ml/solvers": ["ml-bip-solve", "ml-sol-instance", "ml-sol-lpround", "ml-sol-milp", "ml-sol-model", "ml-sol-solveall", "ml-sol-repair", "ml-sol-refined", "ml-sol-local", "ml-sol-lab", "ml-sol-cli", "ml-x-opt-bb", "ml-x-opt-tabu", "ml-x-opt-lp", "ml-x-opt-sa", "ml-x-opt-gd"],
    "ml/forecasting": ["ml-fc-trace", "ml-fc-lstm", "ml-fc-train", "ml-fc-ar", "ml-fc-naive", "ml-fc-run", "ml-fc-starter", "ml-fc-app", "ml-bip-loop", "ml-fc-lab", "ml-fc-cli", "ml-x-ml-runner", "ml-x-ml-hw", "ml-x-ml-cv", "ml-x-ml-drift", "ml-x-opt-bo"],
    "ml/anomaly": ["ml-an-telemetry", "ml-an-fit", "ml-an-run", "ml-an-score", "ml-an-fast", "ml-bip-solve", "ml-an-starter", "ml-an-serve", "ml-an-lab", "ml-an-cli", "ml-x-ml-detect", "ml-x-ml-pca", "ml-x-ml-logit", "ml-x-ml-ens", "ml-x-ml-nn"],
    "ml/rl": ["ml-rl-ride", "ml-rl-weights", "ml-rl-rank", "ml-rl-learnlab", "ml-rl-food", "ml-rl-courier", "ml-rl-accept", "ml-rl-supply", "ml-rl-bandit", "ml-rl-approve", "ml-rl-lab", "ml-rl-cli", "ml-x-ml-q", "ml-x-ml-bandit", "ml-x-ml-rank", "ml-x-opt-es"],
    "ml/evaluation": ["ml-ev-tune", "ml-ev-grid", "ml-ev-ablation", "ml-ev-compare", "ml-ev-holm", "ml-ev-stat", "ml-ev-boot", "ml-bip-fsm", "ml-x-ml-metrics", "ml-x-ml-bv"],
    "ml/gaps": ["ml-bip-modules", "ml-bip-solve", "ml-bip-params", "ml-fc-train", "ml-rl-learnlab", "ml-rl-bandit"],
    "dsa/complexity": ["dsa-app-online", "dsa-app-history", "dsa-app-distances", "dsa-app-nearest", "dsa-app-tiles", "dsa-app-book", "dsa-app-checkout", "dsa-lab-linear", "dsa-lab-binary", "dsa-lab-dynarray", "dsa-lab-runner"],
    "dsa/lists": ["dsa-lab-sll-popback", "dsa-lab-dll-unlink", "dsa-lab-csll", "dsa-lab-csll-rotate", "dsa-lab-cdll", "dsa-lab-cdll-insert", "dsa-lab-cdll-rotate", "dsa-lab-josephus", "dsa-lab-floyd", "dsa-x-lists", "dsa-x-csll", "dsa-x-cdll", "dsa-x-josephus", "dsa-x-floyd"],
    "dsa/queues": ["dsa-app-fare", "dsa-app-lifo", "dsa-app-lru-hit", "dsa-app-lru-evict", "dsa-lab-postfix", "dsa-lab-ring", "dsa-lab-lru", "dsa-lab-cdll", "dsa-x-ring", "dsa-x-lru"],
    "dsa/hashing": ["dsa-app-dishes", "dsa-app-cart", "dsa-app-menu", "dsa-lab-chain", "dsa-lab-probe", "dsa-lab-tomb", "dsa-x-hash"],
    "dsa/trees": ["dsa-app-pools", "dsa-app-rank", "dsa-app-choose", "dsa-lab-bstdel", "dsa-lab-avl", "dsa-lab-traversal", "dsa-lab-heap", "dsa-lab-trie", "dsa-x-avl", "dsa-x-heap"],
    "dsa/graphs": ["dsa-app-zones", "dsa-app-haversine", "dsa-app-legs", "dsa-lab-bfs", "dsa-lab-dfs", "dsa-lab-dijkstra", "dsa-lab-kruskal", "dsa-lab-topo", "dsa-x-graph"],
    "dsa/sorting": ["dsa-app-rank", "dsa-app-pools", "dsa-lab-insertion", "dsa-lab-merge", "dsa-lab-quick", "dsa-lab-heapsort", "dsa-lab-stable", "dsa-lab-first", "dsa-x-sort"],
    "dsa/design": ["dsa-app-validate", "dsa-app-selftest", "dsa-app-advance", "dsa-lab-fib", "dsa-lab-knapsack", "dsa-lab-queens", "dsa-lab-selftest", "dsa-x-knapsack"],
    "dsa/gaps": ["dsa-app-history", "dsa-app-rank", "dsa-app-nearest", "dsa-app-legs", "dsa-app-lifo", "dsa-lab-runner"],
}
TOPIC_TITLES = {
    "security/passwords": "Security → Password storage", "security/login": "Security → Login & lockout",
    "security/identity": "Security → Identity & roles", "security/gateway": "Security → Gateway auth",
    "security/sso": "Security → Single sign-on", "security/kerberos": "Security → Kerberos",
    "security/transport": "Security → mTLS & deployment", "security/learn": "Security → Foundations", "security/gaps": "Security → Gaps & exercises",
    "crypto/hashes": "Cryptography → Hashes & checksums", "crypto/pki": "Cryptography → PKI & certificates",
    "crypto/signatures": "Cryptography → Digital signatures", "crypto/pqc": "Cryptography → Post-quantum",
    "crypto/learn": "Cryptography → Foundations", "crypto/gaps": "Cryptography → Gaps & exercises",
    "ml/optimizer": "ML & Optimisation → Coupling BIP (the paper's optimiser)", "ml/solvers": "ML & Optimisation → Solvers",
    "ml/forecasting": "ML & Optimisation → Forecasting", "ml/anomaly": "ML & Optimisation → Isolation Forest",
    "ml/rl": "ML & Optimisation → Reinforcement learning", "ml/evaluation": "ML & Optimisation → Tuning & evaluation",
    "ml/gaps": "ML & Optimisation → Gaps & exercises",
    "dsa/complexity": "Data Structures → Complexity", "dsa/lists": "Data Structures → Linked lists (all four kinds)",
    "dsa/queues": "Data Structures → Stacks, queues & LRU", "dsa/hashing": "Data Structures → Hash tables",
    "dsa/trees": "Data Structures → Trees & heaps", "dsa/graphs": "Data Structures → Graphs",
    "dsa/sorting": "Data Structures → Sorting & searching", "dsa/design": "Data Structures → Algorithm design",
    "dsa/gaps": "Data Structures → Experiments & exercises",
}
BLOCKS = {  # marker name → (views, introduction)
    "SECURITY CATALOG": (("security", "crypto"), [
        "Every concept in the Architecture Explorer's **Security** and **Cryptography** tabs, linked to the",
        "function, constant or file that implements it. Each row has a stable anchor that the explorer links to.",
        "Status: **Implemented** (in the code), **Demo-grade** (implemented with deliberately simple choices),",
        "**Teaching extension** (not in ATLAS; shows where a standard protocol would attach) or **Explorer / lab**",
        "(teaching code in the explorer or `security_lab/`). Generated by `scripts/security_catalog.py`."]),
    "ML CATALOG": (("ml",), [
        "Every concept in the Architecture Explorer's **ML & Optimisation** tab, linked to the function, constant or",
        "file that implements it, starting with the paper's coupling optimiser (`Sim.bip`). Each row has a stable anchor",
        "that the explorer links to. Status: **Paper (research code)** (`atlas_sim.zip` and `run_*.py` on `main`, as",
        "evaluated in the article), **App / starter (synthetic data)** (ATLAS Go or the server starter, trained on",
        "simulations) or **Explorer / lab** (teaching code in the explorer or `ml_lab/`). Teaching guide:",
        "[docs/MACHINE_LEARNING_OPTIMISATION.md](https://github.com/FUllSCIPTS/ATLAS/blob/main/docs/MACHINE_LEARNING_OPTIMISATION.md).",
        "Generated by `scripts/security_catalog.py`."]),
    "DSA CATALOG": (("dsa",), [
        "Every concept in the Architecture Explorer's **Data Structures** tab, linked to the function, constant or file",
        "that implements it. Status: **Implemented** (the idea runs in ATLAS Go), **Related** (the app does something",
        "similar without this exact structure) or **Explorer / lab** (the course implementation in `dsa_lab/experiments.py`",
        "on `main`, or the explorer's own port in `dist/dsa.js`). Teaching guide:",
        "[docs/DATA_STRUCTURES_ALGORITHMS.md](https://github.com/FUllSCIPTS/ATLAS/blob/main/docs/DATA_STRUCTURES_ALGORITHMS.md).",
        "Generated by `scripts/security_catalog.py`."]),
}


def read(location, main):
    kind, path = location.split(":", 1)
    if kind == "main":
        return (main / path).read_text(encoding="utf-8")
    if kind == "arch":
        return (EXPLORER / path).read_text(encoding="utf-8")
    with zipfile.ZipFile(main / ("atlas_sim.zip" if kind == "sim" else "prototype.zip")) as archive:
        return archive.read(path).decode("utf-8")


def python_symbols(text):
    found = {}
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    found[f"{node.name}.{item.name}"] = item.lineno
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            found.setdefault(node.name, node.lineno)
    return found


def locate(text, path, symbol):
    if not symbol:
        return 1
    lines = text.splitlines()
    if symbol.startswith("~"):
        pattern = re.compile(symbol[1:])
        hits = [i for i, line in enumerate(lines, 1) if pattern.search(line)]
    elif symbol.startswith("="):
        pattern = re.compile(rf"^\s*(?:const |let |var )?{re.escape(symbol[1:])}\s*=")
        hits = [i for i, line in enumerate(lines, 1) if pattern.search(line)]
    elif path.endswith(".py"):
        line = python_symbols(text).get(symbol)
        hits = [line] if line else []
    else:
        pattern = re.compile(rf"^\s*(?:async\s+)?function\s+{re.escape(symbol)}\b|^\s*(?:const|let)\s+{re.escape(symbol)}\s*=")
        hits = [i for i, line in enumerate(lines, 1) if pattern.search(line)]
    if not hits:
        raise SystemExit(f"Cannot find {symbol!r} in {path}")
    return hits[0]


def resolve(main):
    rows, cache = {}, {}
    for row_id, concept, location, symbol, status in ROWS:
        if row_id in rows:
            raise SystemExit(f"Duplicate id {row_id}")
        if location not in cache:
            cache[location] = read(location, main)
        kind, path = location.split(":", 1)
        line = locate(cache[location], path, symbol)
        if kind == "main":
            plain = "?plain=1" if path.endswith(".md") else ""
            url = absolute = f"{MAIN_URL}{path}{plain}#L{line}"
            shown = path
        elif kind == "arch":
            relative = "../" + path[len("starter/"):] if path.startswith("starter/") else "../../" + path
            url, absolute, shown = f"{relative}#L{line}", f"{ARCH_URL}{path}#L{line}", "architecture-explorer/" + path
        else:
            archive = "atlas_sim.zip" if kind == "sim" else "prototype.zip"
            url = absolute = f"{MAIN_URL}{archive}"
            shown = f"{archive} → {path}"
        if symbol.startswith("~"):
            text = cache[location].splitlines()[line - 1].strip().replace("|", "\\|").replace("`", "'")
            name = text if len(text) <= 72 else text[:69] + "..."
        else:
            name = symbol.lstrip("=")
        rows[row_id] = dict(concept=concept, symbol=name, path=shown, line=line, url=url, absolute=absolute, status=status)
    for topic, ids in TOPICS.items():
        missing = [i for i in ids if i not in rows]
        if missing:
            raise SystemExit(f"{topic} references unknown ids {missing}")
    return rows


def markdown(rows, views, intro):
    out = intro + [""]
    anchored = set()
    for topic, ids in TOPICS.items():
        view, key = topic.split("/")
        if view not in views:
            continue
        lab = f"{EXPLORER_URL}#{view}-{key}"
        out += [f'<a name="uml-{view}-{key}"></a>', "", f"### {TOPIC_TITLES[topic]}", "",
                f"[Open in the explorer ↗]({lab})", "",
                "| Concept | Function / symbol | Location | Status |", "| --- | --- | --- | --- |"]
        for row_id in ids:
            row = rows[row_id]
            anchor = "" if row_id in anchored else f'<a name="{row_id}"></a>'
            anchored.add(row_id)
            symbol = f"`{row['symbol']}`" if row["symbol"] else "—"
            out.append(f"| {anchor}{row['concept']} | {symbol} | [{row['path']} L{row['line']}]({row['url']}) | {STATUS[row['status']]} |")
        out.append("")
    return "\n".join(out).rstrip()


def script(rows):
    exported = {k: {f: v[f] for f in ("concept", "symbol", "path", "line", "status")} | {"source": v["absolute"]} for k, v in rows.items()}
    data = {"blueprint": BLUEPRINT_URL, "status": STATUS, "rows": exported, "topics": TOPICS}
    return ("// Generated by architecture-explorer/starter/scripts/security_catalog.py; do not edit by hand.\n"
            "// Maps every Security, Cryptography, ML & Optimisation and Data Structures concept to its entry in the UML blueprint.\n"
            "const umlCatalog = " + json.dumps(data, indent=1, ensure_ascii=False) + ";\n")


def replace_block(document, content, name):
    start, end = f"<!-- BEGIN {name} -->", f"<!-- END {name} -->"
    if document.count(start) != 1 or document.count(end) != 1:
        raise SystemExit(f"Expected one {name} marker pair in {MARKDOWN.name}")
    before, rest = document.split(start, 1)
    _, after = rest.split(end, 1)
    return f"{before}{start}\n\n{content}\n\n{end}{after}"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--main", type=Path, required=True, help="checkout of the main branch")
    parser.add_argument("--check", action="store_true", help="fail if an output is stale")
    args = parser.parse_args()
    rows = resolve(args.main.resolve())
    document = MARKDOWN.read_text(encoding="utf-8")
    for name, (views, intro) in BLOCKS.items():
        document = replace_block(document, markdown(rows, views, intro), name)
    outputs = {MARKDOWN: document, SCRIPT_OUT: script(rows)}
    for path, content in outputs.items():
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                parser.exit(1, f"{path.relative_to(EXPLORER)} is stale. Run python scripts/security_catalog.py --main PATH.\n")
        else:
            path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
