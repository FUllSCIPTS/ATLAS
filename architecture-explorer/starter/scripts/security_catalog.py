"""Build the Security & cryptography and the Machine learning & optimisation catalogues.

One table below maps every concept taught in the Architecture Explorer's Security, Cryptography and
ML & Optimisation tabs to the function, constant or file that implements it. The script resolves
current line numbers and writes:

  docs/UML_BLUEPRINT.md   blocks between <!-- BEGIN/END SECURITY CATALOG --> and <!-- BEGIN/END ML CATALOG -->,
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
          "paper": "Paper (research code)", "synth": "App / starter (synthetic data)"}

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
    ("sec-pw-cli", "Command-line lab: 20 experiments and 5 study paths on the real accounts.py and store.py", "main:security_lab/password_storage_demo.py", "main", "lab"),
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
    ("cr-hash-cli", "Command-line lab: checksum collision", "main:security_lab/crypto_lab.py", "section_checksum", "lab"),
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
    ("cr-pki-cli", "Command-line lab: certificate and pin", "main:security_lab/crypto_lab.py", "section_certificate", "lab"),
    # ---- Cryptography: signatures
    ("cr-sig-sign", "Sign the bundle: jarsigner SHA256withRSA, then verify", "main:android-app/scripts/sign-release.py", "main", "impl"),
    ("cr-sig-ci", "CI signing with the upload key from encrypted secrets", "main:android-app/scripts/ci-sign-bundle.py", "main", "impl"),
    ("cr-sig-apk", "APK Signature Scheme v2/v3; verify with apksigner", "main:android-app/releases/1.2.0/README.md", "~apksigner verify", "impl"),
    ("cr-sig-lab-keys", "Explorer lab: generate ECDSA or RSA key pair", "arch:dist/crypto.js", "crSigKeys", "lab"),
    ("cr-sig-lab-sign", "Explorer lab: hash-then-sign", "arch:dist/crypto.js", "crSigSign", "lab"),
    ("cr-sig-lab-verify", "Explorer lab: verify, tamper, wrong key", "arch:dist/crypto.js", "crSigVerify", "lab"),
    ("cr-sig-cli", "Command-line lab: textbook RSA hash-then-sign", "main:security_lab/crypto_lab.py", "section_rsa", "lab"),
    # ---- Cryptography: post-quantum (teaching extension)
    ("cr-pqc-lab-keys", "Lamport keys from SHA-256 only", "arch:dist/crypto.js", "crLamportKeys", "lab"),
    ("cr-pqc-lab-sign", "Lamport sign: reveal one secret per hash bit", "arch:dist/crypto.js", "crLamportSign", "lab"),
    ("cr-pqc-lab-verify", "Lamport verify", "arch:dist/crypto.js", "crLamportVerify", "lab"),
    ("cr-pqc-lab-forge", "Forgery after key reuse", "arch:dist/crypto.js", "crLamportForge", "lab"),
    ("cr-pqc-cli", "Command-line lab: Lamport one-time signature", "main:security_lab/crypto_lab.py", "section_pqc", "lab"),
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
    ("ml-ev-grid", "ATLAS tuning grid", "main:run_cluster.py", "~\"atlas\": \\[dict\\(switch_pen", "paper"),
    ("ml-ev-ablation", "Ablation: remove one component at a time", "main:run_cluster.py", "~if \"ablation\" in which", "paper"),
    ("ml-ev-compare", "Paired Wilcoxon test + rank-biserial effect size", "main:run_cluster.py", "compare", "paper"),
    ("ml-ev-holm", "Holm-Bonferroni correction", "main:run_cluster.py", "holm", "paper"),
    ("ml-ev-stat", "Mean, SD, 95 % t-interval over 30 runs", "main:run_cluster.py", "stat_block", "paper"),
    ("ml-ev-boot", "Block bootstrap CI for forecast errors", "sim:atlas_sim/forecast.py", "block_bootstrap_ci", "paper"),
]

# Explorer topics → rows. Rows may appear under several topics.
TOPICS = {
    "security/passwords": ["sec-pw-params", "sec-pw-hash", "sec-pw-verify", "sec-pw-policy", "sec-pw-public", "sec-pw-register", "sec-pw-test", "sec-pw-lab", "sec-pw-lab-verify", "sec-pw-cli"],
    "security/login": ["sec-login", "sec-login-failures", "sec-login-session", "sec-login-guest", "sec-login-logout", "sec-login-clear", "sec-pw-verify", "sec-login-lab"],
    "security/identity": ["sec-pw-register", "sec-id-email", "sec-id-phone", "sec-id-licence", "sec-id-business", "sec-id-delete", "sec-rbac-screens", "sec-rbac-online", "sec-rbac-location", "sec-rbac-respond", "sec-rbac-book", "sec-rbac-checkout", "sec-rbac-kitchen"],
    "security/gateway": ["sec-gw-routes", "sec-gw-proxy", "sec-gw-keys", "sec-gw-equal", "sec-gw-internal", "sec-gw-trips", "sec-gw-dispatch", "sec-gw-lab"],
    "security/sso": ["sec-sso-target", "sec-gw-keys", "sec-sso-lab"],
    "security/kerberos": ["sec-krb-target", "sec-krb-setup", "sec-krb-messages", "sec-krb-ap", "sec-krb-seal"],
    "security/transport": ["sec-tls-ca", "sec-tls-client", "sec-tls-server", "sec-dep-headers", "sec-dep-reply", "sec-dep-loopback", "sec-dep-systemd", "cr-sig-sign"],
    "security/gaps": ["sec-pw-params", "sec-login-failures", "sec-gw-keys", "sec-gw-internal", "sec-id-licence", "sec-gw-proxy"],
    "crypto/hashes": ["cr-hash-sums", "cr-hash-handover", "cr-hash-pin-tool", "cr-hash-record", "cr-hash-restore", "cr-hash-inventory", "cr-hash-checksum", "cr-hash-c3", "cr-hash-lab-avalanche", "cr-hash-lab-file", "cr-hash-lab-checksum", "cr-hash-cli"],
    "crypto/pki": ["cr-pki-ca", "cr-pki-client", "cr-pki-server", "cr-pki-webpki", "cr-pki-cert", "cr-pki-pin", "cr-pki-pin-ci", "cr-pki-lab-pin", "cr-pki-lab-issue", "cr-pki-lab-verify", "cr-pki-cli"],
    "crypto/signatures": ["cr-sig-sign", "cr-sig-ci", "cr-pki-pin", "cr-sig-apk", "cr-sig-lab-keys", "cr-sig-lab-sign", "cr-sig-lab-verify", "cr-sig-cli"],
    "crypto/pqc": ["cr-pki-webpki", "cr-pki-ca", "cr-sig-sign", "cr-pqc-lab-keys", "cr-pqc-lab-sign", "cr-pqc-lab-verify", "cr-pqc-lab-forge", "cr-pqc-cli"],
    "crypto/gaps": ["cr-hash-checksum", "cr-hash-sums", "cr-pki-cert", "cr-pki-webpki", "sec-gw-internal"],
    "ml/optimizer": ["ml-bip-modules", "ml-bip-params", "ml-bip-model", "ml-bip-ref", "ml-bip-solve", "ml-bip-loop", "ml-bip-apply", "ml-bip-fsm", "ml-bip-lab", "ml-bip-lab-eval", "ml-bip-cli", "ml-bip-cli-inside", "ml-bip-cli-anomaly"],
    "ml/solvers": ["ml-bip-solve", "ml-sol-instance", "ml-sol-lpround", "ml-sol-milp", "ml-sol-model", "ml-sol-solveall", "ml-sol-repair", "ml-sol-refined", "ml-sol-local", "ml-sol-lab", "ml-sol-cli"],
    "ml/forecasting": ["ml-fc-trace", "ml-fc-lstm", "ml-fc-train", "ml-fc-ar", "ml-fc-naive", "ml-fc-run", "ml-fc-starter", "ml-fc-app", "ml-bip-loop", "ml-fc-lab", "ml-fc-cli"],
    "ml/anomaly": ["ml-an-telemetry", "ml-an-fit", "ml-an-run", "ml-an-score", "ml-an-fast", "ml-bip-solve", "ml-an-starter", "ml-an-serve", "ml-an-lab", "ml-an-cli"],
    "ml/rl": ["ml-rl-ride", "ml-rl-weights", "ml-rl-rank", "ml-rl-learnlab", "ml-rl-food", "ml-rl-courier", "ml-rl-accept", "ml-rl-supply", "ml-rl-bandit", "ml-rl-approve", "ml-rl-lab", "ml-rl-cli"],
    "ml/evaluation": ["ml-ev-tune", "ml-ev-grid", "ml-ev-ablation", "ml-ev-compare", "ml-ev-holm", "ml-ev-stat", "ml-ev-boot", "ml-bip-fsm"],
    "ml/gaps": ["ml-bip-modules", "ml-bip-solve", "ml-bip-params", "ml-fc-train", "ml-rl-learnlab", "ml-rl-bandit"],
}
TOPIC_TITLES = {
    "security/passwords": "Security → Password storage", "security/login": "Security → Login & lockout",
    "security/identity": "Security → Identity & roles", "security/gateway": "Security → Gateway auth",
    "security/sso": "Security → Single sign-on", "security/kerberos": "Security → Kerberos",
    "security/transport": "Security → mTLS & deployment", "security/gaps": "Security → Gaps & exercises",
    "crypto/hashes": "Cryptography → Hashes & checksums", "crypto/pki": "Cryptography → PKI & certificates",
    "crypto/signatures": "Cryptography → Digital signatures", "crypto/pqc": "Cryptography → Post-quantum",
    "crypto/gaps": "Cryptography → Gaps & exercises",
    "ml/optimizer": "ML & Optimisation → Coupling BIP (the paper's optimiser)", "ml/solvers": "ML & Optimisation → Solvers",
    "ml/forecasting": "ML & Optimisation → Forecasting", "ml/anomaly": "ML & Optimisation → Isolation Forest",
    "ml/rl": "ML & Optimisation → Reinforcement learning", "ml/evaluation": "ML & Optimisation → Tuning & evaluation",
    "ml/gaps": "ML & Optimisation → Gaps & exercises",
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
            "// Maps every Security, Cryptography and ML & Optimisation concept to its entry in the UML blueprint.\n"
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
