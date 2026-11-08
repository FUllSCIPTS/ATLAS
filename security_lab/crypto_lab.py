#!/usr/bin/env python3
"""Cryptography lab runner: all 20 ATLAS crypto experiments, by study path.

The experiments live in five category files in this folder, each runnable on its own:

    crypto_a_hashing.py          A. Hashing and integrity                experiments  1-7
    crypto_b_mac_kdf_random.py   B. MACs, key derivation and randomness  experiments  8-10
    crypto_c_pki.py              C. Certificates and PKI                 experiments 11-14
    crypto_d_signatures.py       D. Digital signatures                   experiments 15-17
    crypto_e_post_quantum.py     E. Post-quantum cryptography            experiments 18-20
    crypto_common.py             shared helpers and the command line

They use ATLAS's real artefacts (release checksums, the upload certificate, CI workflows, the prototype
and the app's password hashing) and the Python standard library only. This file loads all five:

    python3 security_lab/crypto_lab.py                             # all 20 experiments
    python3 security_lab/crypto_lab.py --list                      # experiments and study paths
    python3 security_lab/crypto_lab.py --path release-engineer     # one study path
    python3 security_lab/crypto_lab.py -e 13 -e 17                 # chosen experiments
    python3 security_lab/crypto_lab.py --verify atlas-go-1.2.0.apk # check a download (experiment 6)

Study paths
    foundations       1 -> 2 -> 4 -> 6 -> 11 -> 16     hash, verify, certificate, signature
    release-engineer  6 -> 7 -> 11 -> 13 -> 17         verify what ATLAS ships, the way CI does
    attacker          3 -> 5 -> 8 -> 10 -> 15 -> 19    break the weak constructions
    pki               11 -> 12 -> 13 -> 14             certificates from bytes to trust decisions
    post-quantum      3 -> 18 -> 19 -> 20              what a quantum computer breaks, and what replaces it
    full              1 -> 20

See security_lab/README.md and docs/CRYPTOGRAPHY.md for the full teaching guide.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from crypto_common import EXPERIMENTS, STUDY_PATHS, main  # noqa: E402,F401  (re-exported)

if __name__ == '__main__':
    main(description=__doc__.split('\n')[0])
