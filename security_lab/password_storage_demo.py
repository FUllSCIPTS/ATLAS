#!/usr/bin/env python3
"""Information-security lab: how ATLAS Go stores and checks passwords.

Runs against the app's real code in android-app/atlas_go/accounts.py (standard library only).

    python3 security_lab/password_storage_demo.py

Sections
  1. What is stored for an account (salt, hash, iterations) - never the password
  2. Same password, two accounts -> different hashes (why salts matter)
  3. Verification uses a constant-time comparison
  4. Why a slow hash matters: guesses per second, fast SHA-256 vs ATLAS PBKDF2
  5. A tiny dictionary attack against a leaked record
  6. Login throttling: 5 failures -> 60 s lockout, and the generic error message
See docs/INFORMATION_SECURITY.md for the full teaching guide.
"""
from __future__ import annotations

import hashlib
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'android-app'))

from atlas_go import accounts as acc  # noqa: E402


def heading(text: str) -> None:
    print('\n' + text + '\n' + '-' * len(text))


def main() -> None:
    heading('1. What ATLAS Go stores for an account')
    record = acc.hash_password('cork2026')
    print(f"password entered : cork2026   (discarded after hashing)")
    print(f"salt  (16 bytes) : {record['salt']}")
    print(f"hash  (32 bytes) : {record['hash']}")
    print(f"iterations       : {record['iterations']:,}  (PBKDF2-HMAC-SHA256)")
    shown = acc.public_view(dict(id='U-1', name='Aoife', email='aoife@example.ie', **record))
    print(f"shown on screen  : {sorted(shown)}  (public_view strips salt, hash, iterations)")

    heading('2. Same password, two accounts')
    other = acc.hash_password('cork2026')
    print(f"account A hash   : {record['hash'][:32]}...")
    print(f"account B hash   : {other['hash'][:32]}...")
    print(f"equal?           : {record['hash'] == other['hash']}  -> a leaked file does not reveal shared passwords,")
    print('                    and a precomputed (rainbow) table is useless.')

    heading('3. Verification')
    print(f"verify('cork2026') -> {acc.verify_password('cork2026', record)}")
    print(f"verify('cork2027') -> {acc.verify_password('cork2027', record)}")
    print('compare uses hmac.compare_digest: time does not depend on where the bytes differ.')

    heading('4. Cost per guess for an attacker who stole state.json')
    n = 20_000
    start = time.perf_counter()
    for i in range(n):
        hashlib.sha256(b'salt' + str(i).encode()).digest()
    fast = n / (time.perf_counter() - start)
    trials = 3
    start = time.perf_counter()
    for i in range(trials):
        acc.hash_password(f'guess{i}', salt=bytes(16))
    slow = trials / (time.perf_counter() - start)
    print(f"plain salted SHA-256     : {fast:>14,.0f} guesses/s on this CPU")
    print(f"ATLAS PBKDF2 (200k iter) : {slow:>14,.1f} guesses/s on this CPU")
    print(f"slow-down factor         : {fast / slow:>14,.0f} x")
    print(f"8-char lowercase+digits  : 36^8 = {36**8:,} guesses -> "
          f"{36**8 / fast / 3600:,.1f} h vs {36**8 / slow / 3600 / 24 / 365:,.0f} years (one core)")

    heading('5. Dictionary attack on the leaked record')
    leaked = acc.hash_password('summer2024')
    wordlist = ['password1', 'letmein12', 'cork12345', 'qwerty123', 'summer2024', 'dublin2025']
    start = time.perf_counter()
    for word in wordlist:
        if acc.verify_password(word, leaked):
            print(f"cracked: '{word}' after {wordlist.index(word) + 1} guesses, "
                  f"{time.perf_counter() - start:.2f} s")
            break
    print('lesson: salting and stretching slow attackers down; they do not save a guessable password.')
    print("policy (check_password): 8-128 characters with a letter and a digit, e.g. "
          f"check_password('abc') -> ", end='')
    try:
        acc.check_password('abc')
    except ValueError as error:
        print(error)

    heading('6. Login throttling in LocalStore.login')
    from atlas_go.store import LocalStore
    with tempfile.TemporaryDirectory() as folder:
        store = LocalStore(Path(folder) / 'state.json')
        store.register('passenger', 'Aoife Murphy', 'aoife@example.ie', '087 123 4567', 'cork2026')
        store.logout()
        now = 1_000_000.0
        for attempt in range(1, acc.MAX_FAILED_LOGINS + 2):
            try:
                store.login('aoife@example.ie', 'wrong-pass1', now=now)
            except ValueError as error:
                print(f"attempt {attempt}: {error}")
        try:
            store.login('nobody@example.ie', 'cork2026', now=now)
        except ValueError as error:
            print(f"unknown email   : {error}   <- same message: no user enumeration")
        try:
            store.login('aoife@example.ie', 'cork2026', now=now + 1)
        except ValueError as error:
            print(f"right password while locked: {error}")
        store.login('aoife@example.ie', 'cork2026', now=now + acc.LOCKOUT_SECONDS + 1)
        print(f"after {acc.LOCKOUT_SECONDS} s: signed in as {store.user['name']} (role {store.role})")


if __name__ == '__main__':
    main()
