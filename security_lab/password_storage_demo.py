#!/usr/bin/env python3
"""Information-security lab runner: all 20 ATLAS Go password and sign-in experiments, by study path.

The experiments live in four category files in this folder, each runnable on its own:

    lab_a_password_storage.py       A. What the app stores          experiments  1-8
    lab_b_registration_identity.py  B. Registration and identity    experiments  9-11
    lab_c_signin_defences.py        C. Sign-in defences             experiments 12-15
    lab_d_integrity_lifecycle.py    D. Integrity and lifecycle      experiments 16-20
    lab_common.py                   shared helpers and the command line

They drive the app's real code in android-app/atlas_go/accounts.py and store.py (standard library only).
This file loads all four and adds the study paths that cross categories:

    python3 security_lab/password_storage_demo.py                 # all 20 experiments
    python3 security_lab/password_storage_demo.py --list          # experiments and study paths
    python3 security_lab/password_storage_demo.py --path attacker # one study path
    python3 security_lab/password_storage_demo.py -e 6 -e 13      # chosen experiments

Study paths
    foundations  1 -> 2 -> 3 -> 7 -> 8           what is stored and why
    attacker     4 -> 5 -> 6 -> 13 -> 14 -> 15   a stolen file, a hammered login
    defender     9 -> 10 -> 11 -> 12 -> 13 -> 16 controls at registration and sign-in
    integrity    8 -> 17 -> 18 -> 19             keeping stored data trustworthy
    lifecycle    9 -> 1 -> 12 -> 16 -> 19 -> 20  one user from sign-up to deletion
    full         1 -> 20

See security_lab/README.md and docs/INFORMATION_SECURITY.md for the full teaching guide.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lab_common import EXPERIMENTS, STUDY_PATHS, main  # noqa: E402,F401  (re-exported)

if __name__ == '__main__':
    main(description=__doc__.split('\n')[0])
