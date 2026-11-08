# Security labs

Command-line labs that run the ATLAS Go app's real code (`android-app/atlas_go/accounts.py` and
`store.py`). They use the Python standard library only, and every experiment works in its own throw-away
folder, so nothing on your machine is changed. The teaching guides are
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

## Cryptography lab

| File | Sections |
|---|---|
| [`crypto_lab.py`](crypto_lab.py) | SHA-256 and the avalanche effect; checksum vs cryptographic hash; verifying a release with `SHA256SUMS`; the upload certificate's pinned fingerprint; hash-then-sign with toy RSA; a Lamport post-quantum one-time signature |

```bash
python3 security_lab/crypto_lab.py
python3 security_lab/crypto_lab.py --verify atlas-go-1.2.0.apk
```
