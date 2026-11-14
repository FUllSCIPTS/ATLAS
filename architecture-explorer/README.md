# ATLAS Architecture Explorer

**Live demo** · [Open the ATLAS Architecture Explorer](https://fullscipts.github.io/ATLAS/)

A self-hosted copy of the interactive ride-hailing and food-delivery reference design. It serves the architecture map, the component catalog, the deployment view and the folder tree for three systems: the server starter, the ATLAS Go 1.4.0 Android app with passenger, driver and seller accounts, a live map and its on-device intelligence (dispatch policy, acceptance model, courier timing, holiday surge outlook, learning lab and the offline training that produces `learned.py`), and **ATLAS Go 1.4 · two learning layers** — the 1.3.0 digital twin with Agent 1 (dispatch), Agent 2 (pricing and moves) and the Guardian on top of Layer 1, and the 1.4.0 live LSTM → RL loop with nightly champion/challenger validation, with four traceable flows (a ride through both layers, pricing an area, one city hour, one night). Open the app view directly at `/#go` and the two layers at `/#golayers`. The ride, driver and learning flows are illustrative. The server runs the explorer alone. It has no dependencies on FastAPI, PostgreSQL, Kafka, or trained models.

## Run the ride-hailing application

The starter includes the passenger and driver apps, FastAPI services, PostgreSQL and Kafka configuration, trained model commands, and an end-to-end smoke test. [Starter README](starter/README.md) · [Implementation guide](https://fullscipts.github.io/ATLAS/build.html)

[Final handover and runbook](starter/docs/FINAL_HANDOVER.md) · [UML blueprint and exact class/function inventory](starter/docs/UML_BLUEPRINT.md)

## Run from Git

Install a supported Node.js LTS release and Git on the server. The explorer uses Node.js built-ins and needs no npm install or build step.

Clone the public deployment branch. The explorer is in its own directory within the ATLAS research repository.

```bash
git clone --branch architecture-explorer --single-branch https://github.com/FUllSCIPTS/ATLAS.git atlas-architecture-explorer
cd atlas-architecture-explorer/architecture-explorer
node server.mjs
```

The source repository is public. Access to a running deployment is controlled by your server.

## Security view (information-security teaching)

The **Security** tab ([live](https://fullscipts.github.io/ATLAS/#security)) explains how ATLAS handles authentication, password storage, identity management, role-based access, gateway authentication, single sign-on and Kerberos, and links each control to the code that implements it. Labs run in the browser with Web Crypto: PBKDF2 password hashing with the app's exact parameters, the login lockout, a step-through of the gateway's checks, an OpenID Connect + PKCE flow with real ES256 tokens, and a six-message Kerberos exchange with real AES-GCM and attack scenarios (wrong password, clock skew, tampered ticket, expired ticket, replay). SSO and Kerberos are labelled as teaching extensions: they are not part of the ATLAS code. A **Foundations** topic presents all 19 standalone units of the guide (S1–S13.6: CIA and STRIDE, IAAA, access-control models, sessions and CSRF, API security, OAuth/OIDC, Kerberos, TLS 1.3, secure deployment, network security, OWASP Top 10, logging and incident response, GDPR, governance, social engineering) as what / why / how, with live labs for role-ownership-state checks, password guessability, TOTP (RFC 6238 test vectors), PKCE (RFC 7636) and SQL injection/XSS encoding. Deep links: `#security-learn`, `#security-passwords`, `#security-login`, `#security-identity`, `#security-gateway`, `#security-sso`, `#security-kerberos`, `#security-transport`, `#security-gaps`. The source is `dist/security.js`; the written guide is [docs/INFORMATION_SECURITY.md](https://github.com/FUllSCIPTS/ATLAS/blob/main/docs/INFORMATION_SECURITY.md).

## Cryptography view

The **Cryptography** tab ([live](https://fullscipts.github.io/ATLAS/#crypto)) shows where ATLAS uses hash functions and checksums, public-key infrastructure (keys and certificates), digital signatures and, as a teaching extension, post-quantum cryptography. Labs use Web Crypto in the browser: the avalanche effect; checking a downloaded APK or AAB against every published SHA-256; the prototype's recovery checksum versus SHA-256; recomputing the real upload certificate's pinned fingerprint; a private CA with mutual-TLS checks (wrong key usage, expired, rogue CA, edited subject, leaf used as CA); ECDSA and SHA256withRSA signing with tamper tests; and a Lamport one-time signature that is forged after key reuse. A **Foundations** topic presents all 19 standalone units of the guide (C1–C10.5) as what / why / how, with live labs: textbook RSA with CRT and malleability plus real RSA-OAEP; Diffie–Hellman with a man in the middle plus real ECDH P-256 and X25519; toy ECDSA with private-key recovery from a reused nonce; AES-256-GCM tampering and nonce reuse; one-bit LWE; a toy KEM with the shape of ML-KEM (FIPS 203) including implicit rejection; ML-DSA rejection sampling; and a Winternitz one-time signature with a Merkle root. The Post-quantum topic also lists FN-DSA (draft FIPS 206), HQC and the NIST IR 8547 deadlines. The unit content and labs live in `dist/foundations.js`. Deep links: `#crypto-learn`, `#crypto-hashes`, `#crypto-pki`, `#crypto-signatures`, `#crypto-pqc`, `#crypto-gaps`. The source is `dist/crypto.js`; the written guide is [docs/CRYPTOGRAPHY.md](https://github.com/FUllSCIPTS/ATLAS/blob/main/docs/CRYPTOGRAPHY.md).

## Machine learning & optimisation view

The **ML & Optimisation** tab ([live](https://fullscipts.github.io/ATLAS/#ml)) shows the paper's optimisation algorithm and every learner in ATLAS. The **coupling BIP** lab is a line-by-line replica of `Sim.eval_all` and `Sim.bip` (`atlas_sim/cluster.py` on `main`): move the load and the anomaly score, deploy a choice to see the switching cost, disable hybrid mode, and watch which of the six modules leave the monolith across the load range. Other labs: the measured solve times of enumeration, branch-and-bound and LP relaxation with risk-aware rounding, plus a live 2ⁿ enumeration; a forecaster trained on the paper's traffic model with gradient descent and with Adam, with early stopping; an Isolation Forest grown on the starter's driver data; REINFORCE training of the ATLAS Go dispatch policy against the nearest-driver rule and the approved v1.4 policy, and the learned Q-learning courier table; tuning, ablation and the statistics used in the evaluation. ATLAS Go 1.3–1.4 labs: the **digital twin** (ports of `twin.rehearse`, `agent1`, `agent2` and the Guardian's checks: set the demand, rehearse Layer 1's top three drivers, find how many rollouts give a stable choice, try to get a bad price past the Guardian, run the 3,000-fault drill and the 500-rollout re-test); **actor & critic networks** (A2C trained live against REINFORCE on the same rides, with the critic's value of easy and hard situations); **two agents, one critic** (dispatch and pricing actors trained with IPPO and with MAPPO's shared centralised critic in a three-zone twin, with learning curves, advantage noise and a test hour); and the **LSTM + RL loop** (the phone's LSTM run in the browser with a parity check against Python, what-if event tags and demand shocks, and an hour-by-hour replay of the loop over the Cork Jazz weekend with every nightly validation). Deep links: `#ml-optimizer`, `#ml-solvers`, `#ml-forecasting`, `#ml-anomaly`, `#ml-rl`, `#ml-twin`, `#ml-actorcritic`, `#ml-marl`, `#ml-loop`, `#ml-evaluation`, `#ml-gaps`. The source is `dist/ml.js` with the LSTM weights and the recorded loop in `dist/ml-live.js` (regenerate with `starter/scripts/export_ml_live.py --main <main checkout>`); the written guide is [docs/MACHINE_LEARNING_OPTIMISATION.md](https://github.com/FUllSCIPTS/ATLAS/blob/main/docs/MACHINE_LEARNING_OPTIMISATION.md).

## Data structures & algorithms view

The **Data Structures** tab ([live](https://fullscipts.github.io/ATLAS/#dsa)) is the interactive companion to the 24-lesson course in [docs/DATA_STRUCTURES_ALGORITHMS.md](https://github.com/FUllSCIPTS/ATLAS/blob/main/docs/DATA_STRUCTURES_ALGORITHMS.md). Every structure is a real pointer-based port of `dsa_lab/experiments.py`, drawn by walking its own `next`/`prev` pointers, with its invariant checked after each operation. Labs: comparison counts as n doubles; all four linked lists (singly, doubly, circular singly with only a tail, circular doubly with a sentinel) with push, pop and rotate, the Josephus problem on a ring and Floyd's tortoise and hare; a stack evaluating the app's fare rule, a ring buffer and an LRU cache compared with the map's `TileLoader`; chaining vs linear probing on the app's dish ids; BST vs AVL, a min-heap of the app's drivers and a trie of Cork place names; BFS, DFS, Dijkstra and Prim on a graph of the app's sixteen Cork zones; seven sorts counted on the same input, stability and binary search; memoisation, a knapsack DP and N queens. Each lab says whether ATLAS Go uses the idea (and where) or whether it is teaching only. Deep links: `#dsa-complexity`, `#dsa-lists`, `#dsa-queues`, `#dsa-hashing`, `#dsa-trees`, `#dsa-graphs`, `#dsa-sorting`, `#dsa-design`, `#dsa-gaps`. The source is `dist/dsa.js`.

## UML catalogue links

Every concept in the Security, Cryptography, ML & Optimisation and Data Structures tabs links to its function in the [Security and cryptography catalogue](starter/docs/UML_BLUEPRINT.md#security-and-cryptography-catalogue), the [Machine learning and optimisation catalogue](starter/docs/UML_BLUEPRINT.md#machine-learning-and-optimisation-catalogue) or the [Data structures and algorithms catalogue](starter/docs/UML_BLUEPRINT.md#data-structures-and-algorithms-catalogue) of the UML blueprint, which in turn links to the exact source line. Both the catalogue and `dist/uml-catalog.js` are generated from one table in `starter/scripts/security_catalog.py`. After changing any linked code, run it with a checkout of `main` (Android app, research code, workflows and labs live there), then refresh the blueprint, and confirm both with `--check`:

```bash
python starter/scripts/security_catalog.py --main ../ATLAS-main
python starter/scripts/generate_blueprint.py
python starter/scripts/security_catalog.py --main ../ATLAS-main --check && python starter/scripts/generate_blueprint.py --check
```

## Access privately

The app listens on the server's loopback address, `127.0.0.1:8080`. From your workstation, open an SSH tunnel and visit [http://127.0.0.1:8080/](http://127.0.0.1:8080/).

```bash
ssh -N -o ExitOnForwardFailure=yes -L 127.0.0.1:8080:127.0.0.1:8080 YOUR_USER@YOUR_SERVER
```

Port 8080 needs no inbound firewall rule. SSH controls remote access. Other processes and users on the server can reach its loopback interface, so use a server you trust. If you add an HTTPS reverse proxy, require authentication for every explorer route before exposing it. On a port conflict, set `PORT` for the service and update the tunnel's destination port.

## Install as a Linux service

Clone or move the checkout to `/opt/atlas-architecture-explorer`. Keep the files readable by the service and writable only by the deployment user. Install Node.js on the system path available to systemd.

```bash
cd /opt/atlas-architecture-explorer/architecture-explorer
sudo install -m 0644 deploy/atlas-explorer.service /etc/systemd/system/atlas-explorer.service
sudo systemctl daemon-reload
sudo systemctl enable --now atlas-explorer
curl -fsS http://127.0.0.1:8080/healthz
```

Expected health response is `ok`. View service logs with `sudo journalctl -u atlas-explorer -n 50`.

To update from GitHub, run `git pull --ff-only` as the deployment user and restart the service with `sudo systemctl restart atlas-explorer`. Run the health check again after the restart. To roll back, check out the previous known-good commit with `git checkout --detach COMMIT_SHA` and restart. Return to the `architecture-explorer` branch before pulling again.
