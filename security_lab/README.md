# Security labs

Two command-line labs, 20 experiments each, that run ATLAS's real code and artefacts: the
information-security lab (`lab_*.py`, on `android-app/atlas_go/accounts.py` and `store.py`) and the
cryptography lab (`crypto_*.py`, on the releases, certificate, CI workflows and prototype). They use the
Python standard library only, and every experiment works in its own throw-away folder, so nothing on your
machine is changed. The teaching guides are
[docs/INFORMATION_SECURITY.md](../docs/INFORMATION_SECURITY.md) and [docs/CRYPTOGRAPHY.md](../docs/CRYPTOGRAPHY.md).

## Information-security labs, by category

| File | Category | Experiments | App code it exercises |
|---|---|---|---|
| [`lab_a_password_storage.py`](lab_a_password_storage.py) | A. What the app stores | 1–8 | `hash_password`, `verify_password`, `check_password`, `public_view`, `state.json` |
| [`lab_b_registration_identity.py`](lab_b_registration_identity.py) | B. Registration and identity | 9–11 | `clean_*` validators, `LocalStore.register`, role checks |
| [`lab_c_signin_defences.py`](lab_c_signin_defences.py) | C. Sign-in defences | 12–15 | `LocalStore.login`, `LocalStore.failures` |
| [`lab_d_integrity_lifecycle.py`](lab_d_integrity_lifecycle.py) | D. Integrity, sessions and lifecycle | 16–20 | `load`/`validate`, `save`/`commit`, `logout`, `delete_account` |
| [`password_storage_demo.py`](password_storage_demo.py) | Runner for all four | 1–20 | Loads A–D and adds the study paths |
| [`lab_common.py`](lab_common.py) | Shared helpers | – | Experiment registry, helpers, command line |

```bash
python3 security_lab/lab_a_password_storage.py          # one category
python3 security_lab/lab_c_signin_defences.py --list    # its experiments
python3 security_lab/lab_c_signin_defences.py -e 14     # one experiment
python3 security_lab/password_storage_demo.py           # all 20
python3 security_lab/password_storage_demo.py --path attacker
```

### Experiments

**A. What the app stores** — `lab_a_password_storage.py`

1. Anatomy of a stored credential (salt, hash, iterations) and what `public_view` hides
2. Salting: one password, three accounts, three different hashes
3. Verifying a password: constant-time compare, malformed records fail closed
4. Work factor: how PBKDF2 cost grows with the iteration count
5. Attacker's arithmetic: guesses per second and time to exhaust a key space
6. Dictionary attack on a leaked `state.json` record
7. Password policy matrix: what `check_password` accepts and rejects
8. Forensics on the device file: no plaintext password anywhere in `state.json`

**B. Registration and identity** — `lab_b_registration_identity.py`

9. Input validation as a security control (email, phone, plate, licence, business, price)
10. One identity per email: duplicate and case-variant registrations
11. Role separation: what a passenger, a driver and a seller may do

**C. Sign-in defences** — `lab_c_signin_defences.py`

12. Throttling timeline: 5 failures → 60 s lockout → recovery
13. No account enumeration through error messages
14. Timing side channel: unknown email vs wrong password (and the dummy-hash fix)
15. Limits of the lockout: per email, in memory only, gone after a restart

**D. Integrity, sessions and lifecycle** — `lab_d_integrity_lifecycle.py`

16. Sessions: survive a restart, logout, guest mode, session pointing at a deleted user
17. Tampered `state.json` is rejected and quarantined to `state.invalid.json`
18. Atomic saves and rollback: a failed disk write never half-registers a user
19. Account deletion: re-authentication, active-trip guard, anonymised history
20. Upgrading old hashes: rehash-on-login when the iteration count is raised (extension)

### Study paths (`password_storage_demo.py --path NAME`)

| Path | Experiments | Question it answers |
|---|---|---|
| `foundations` | 1 → 2 → 3 → 7 → 8 | What exactly is stored, and why can nobody read the password back? |
| `attacker` | 4 → 5 → 6 → 13 → 14 → 15 | How fast can a stolen file or a login screen be attacked, and what leaks? |
| `defender` | 9 → 10 → 11 → 12 → 13 → 16 | Which controls run at registration and sign-in? |
| `integrity` | 8 → 17 → 18 → 19 | How does the app keep its stored data trustworthy? |
| `lifecycle` | 9 → 1 → 12 → 16 → 19 → 20 | One user from sign-up to deletion, plus rehash-on-login |
| `full` | 1 → 20 | Everything in order |

### Gaps the labs expose (exercises for session 8 of the guide)

- Experiment 14: an unknown email skips PBKDF2, so sign-in timing reveals which emails are registered.
- Experiment 15: the lockout counter lives in memory and resets when the app restarts.
- Experiment 3: a record with `iterations = 0` raises instead of failing closed (store validation stops it first).
- Experiment 9: names may contain the right-to-left override character U+202E.

## Cryptography labs, by category

Twenty experiments on ATLAS's real artefacts: the release checksums and signing records, the upload
certificate and its pin, the CI workflows, the prototype's checksum and private CA, and the app's password
hashing. Large topics are split into small exercises, each of which builds one piece from first principles.

| File | Category | Experiments | ATLAS artefact it uses |
|---|---|---|---|
| [`crypto_a_hashing.py`](crypto_a_hashing.py) | A. Hashing and integrity | 1–7 | `releases/SHA256SUMS*`, `SIGNED_VALIDATION.json`, `.github/workflows/`, `prototype.zip` |
| [`crypto_b_mac_kdf_random.py`](crypto_b_mac_kdf_random.py) | B. MACs, key derivation, randomness | 8–10 | `atlas_go/accounts.py` (PBKDF2, salts), `store.py` (ids) |
| [`crypto_c_pki.py`](crypto_c_pki.py) | C. Certificates and PKI | 11–14 | `releases/upload-certificate.pem`, `prototype/proto_run.py` |
| [`crypto_d_signatures.py`](crypto_d_signatures.py) | D. Digital signatures | 15–17 | `scripts/sign-release.py` (SHA256withRSA, JAR signing) |
| [`crypto_e_post_quantum.py`](crypto_e_post_quantum.py) | E. Post-quantum cryptography | 18–20 | The PQ migration plan in `docs/CRYPTOGRAPHY.md` §6 |
| [`crypto_lab.py`](crypto_lab.py) | Runner for all five | 1–20 | Loads A–E, adds study paths and `--verify FILE` |
| [`crypto_common.py`](crypto_common.py) | Shared helpers | – | Toy RSA, PKCS#1 v1.5, DER reader, command line |

```bash
python3 security_lab/crypto_c_pki.py                      # one category
python3 security_lab/crypto_c_pki.py -e 13                # one experiment
python3 security_lab/crypto_lab.py --path release-engineer
python3 security_lab/crypto_lab.py --verify atlas-go-1.2.0.apk
```

### Experiments

**A. Hashing and integrity** — `crypto_a_hashing.py`

1. SHA-256 basics: one-shot vs streaming, bytes vs text, and the Unicode (NFC/NFD) trap
2. The avalanche effect, measured over 2,000 single-bit changes
3. Why 256 bits: brute-forcing preimages and birthday collisions of a truncated hash
4. Checksum vs hash: forging the prototype's `PaymentModule.checksum`
5. CRC32 is linear: append four bytes to hit any checksum
6. Verifying ATLAS releases: `SHA256SUMS`, signing records and a tampered download
7. Supply-chain pinning: the bundletool hash in CI, and actions pinned by movable tag

**B. MACs, key derivation and randomness** — `crypto_b_mac_kdf_random.py`

8. Length extension: forging `sha256(secret + message)` with a hand-written SHA-256; HMAC resists
9. HMAC and PBKDF2 built by hand, reproducing a hash from `accounts.hash_password`
10. Randomness: predicting Python's `random` from 624 outputs; why salts come from `secrets`

**C. Certificates and PKI** — `crypto_c_pki.py`

11. PEM, DER and the fingerprint pin: what CI actually hashes
12. Walking the certificate's DER bytes: version, names, dates, key, extensions
13. Verifying the certificate's RSA-4096 / SHA-384 self-signature by hand
14. A private CA like the prototype's: chains, CA:FALSE, key usage, SAN and expiry

**D. Digital signatures** — `crypto_d_signatures.py`

15. Textbook RSA step by step, and forging by multiplying signatures
16. SHA256withRSA (PKCS#1 v1.5): hash-then-sign with padding, as jarsigner does
17. Signing a bundle the JAR way: `MANIFEST.MF`, the `.SF` file and what each tamper breaks

**E. Post-quantum cryptography** — `crypto_e_post_quantum.py`

18. Lamport one-time signatures from SHA-256 alone, with a size comparison to RSA, ML-DSA and SLH-DSA
19. Why "one-time": forging a release signature after the key is reused
20. Lattices and hybrids: a toy LWE key encapsulation combined with Diffie-Hellman through HKDF

### Study paths (`crypto_lab.py --path NAME`)

| Path | Experiments | Goal |
|---|---|---|
| `foundations` | 1 → 2 → 4 → 6 → 11 → 16 | Hash, verify, certificate, signature |
| `release-engineer` | 6 → 7 → 11 → 13 → 17 | Verify what ATLAS ships, the way CI does |
| `attacker` | 3 → 5 → 8 → 10 → 15 → 19 | Break the weak constructions |
| `pki` | 11 → 12 → 13 → 14 | Certificates from bytes to trust decisions |
| `post-quantum` | 3 → 18 → 19 → 20 | What a quantum computer breaks, and what replaces it |
| `full` | 1 → 20 | Everything in order |

### Findings the labs surface (exercises)

- Experiment 4: `snapshot()` keeps no per-payment amounts, so even a SHA-256 over it misses moved money.
- Experiment 6: `SHA256SUMS` is not signed, so whoever can replace a download can replace its checksum.
- Experiment 7: all GitHub Actions steps are pinned by movable tag, not by commit SHA.
- Experiment 10: account, ride and order ids are clock-based, so they are unique but guessable.
- Experiment 12: the upload certificate is X.509 v3 with a subjectKeyIdentifier, and its `notAfter` is a
  GeneralizedTime (after 2049).

All toy constructions (RSA without a vetted library, Lamport, LWE, 512-bit Diffie-Hellman) are for
learning only.
