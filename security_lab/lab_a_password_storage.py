#!/usr/bin/env python3
"""Security lab A - what the app stores: hashing, salting, cost and cracking (experiments 1-8).

Runs against the app's real code: android-app/atlas_go/accounts.py (hash_password, verify_password, check_password, public_view).
Standard library only; every experiment works in its own throw-away folder.

    python3 security_lab/lab_a_password_storage.py          # every experiment in this lab
    python3 security_lab/lab_a_password_storage.py --list
    python3 security_lab/lab_a_password_storage.py -e 1

Experiments
   1. Anatomy of a stored credential (salt, hash, iterations) and what public_view hides
   2. Salting: one password, three accounts, three different hashes
   3. Verifying a password: constant-time compare, malformed records fail closed
   4. Work factor: how PBKDF2 cost grows with the iteration count
   5. Attacker's arithmetic: guesses per second and time to exhaust a key space
   6. Dictionary attack on a leaked state.json record
   7. Password policy matrix: what check_password accepts and rejects
   8. Forensics on the device file: no plaintext password anywhere in state.json

All four labs and the cross-category study paths: python3 security_lab/password_storage_demo.py --list
See docs/INFORMATION_SECURITY.md for the full teaching guide.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import time

from lab_common import (
    PASSWORD, acc, attempt, experiment, human, main, new_store, note, register_passenger, timed,
)


@experiment(1, 'A', 'Anatomy of a stored credential')
def exp_record(_):
    record = acc.hash_password(PASSWORD)
    print(f'  hash_password({PASSWORD!r}) returns:')
    for key, value in record.items():
        print(f'    {key:<10} = {value}')
    print(f'  salt   : {len(bytes.fromhex(record["salt"]))} random bytes from secrets.token_bytes')
    print(f'  hash   : {len(bytes.fromhex(record["hash"]))} bytes of PBKDF2-HMAC-SHA256 output')
    print(f'  rounds : {record["iterations"]:,} (accounts.PBKDF2_ITERATIONS)')
    recomputed = hashlib.pbkdf2_hmac('sha256', PASSWORD.encode(), bytes.fromhex(record['salt']),
                                     record['iterations']).hex()
    note(f'Re-deriving with hashlib.pbkdf2_hmac gives the same hash: {recomputed == record["hash"]}')
    account = dict(id='U-1', role='passenger', name='Aoife Murphy', email='aoife@example.ie',
                   phone='+353871234567', created=0, **record)
    print(f'  public_view(account) -> {acc.public_view(account)}')
    note('Screens and logs get public_view: the salt, hash and iteration count never leave storage.')
    note('There is no "decrypt": a hash is one-way, so the app can only re-derive and compare.')


@experiment(2, 'A', 'Salting: one password, three accounts')
def exp_salt(_):
    rows = [acc.hash_password(PASSWORD) for _ in range(3)]
    for i, r in enumerate(rows, 1):
        print(f'  account {i}: salt {r["salt"][:16]}...  hash {r["hash"][:24]}...')
    print(f'  all hashes different: {len({r["hash"] for r in rows}) == 3}')
    fixed = bytes(16)
    unsalted = [hashlib.pbkdf2_hmac('sha256', PASSWORD.encode(), fixed, 1000).hex()[:24] for _ in range(3)]
    print(f'  without a random salt (fixed zero salt): {unsalted}')
    note('Same salt -> same hash: one cracked hash exposes every user who chose that password,')
    note('and precomputed (rainbow) tables work. A per-user salt forces a separate attack per account.')


@experiment(3, 'A', 'Verifying a password')
def exp_verify(_):
    record = acc.hash_password(PASSWORD)
    for guess in (PASSWORD, 'Cork2026', 'cork2026 ', ''):
        print(f'  verify_password({guess!r:<12}) -> {acc.verify_password(guess, record)}')
    broken = {
        'missing salt': {k: v for k, v in record.items() if k != 'salt'},
        'salt not hex': dict(record, salt='zz-not-hex'),
        'iterations as text': dict(record, iterations='200000'),
        'iterations = 0': dict(record, iterations=0),
        'empty record': {},
    }
    for label, rec in broken.items():
        try:
            outcome = acc.verify_password(PASSWORD, rec)
        except ValueError as error:
            outcome = f'raises ValueError("{error}")'
        print(f'  malformed record ({label:<18}) -> {outcome}')
    note('Missing or non-hex fields fail closed (False). "200000" as text is quietly accepted by int(),')
    note('and iterations = 0 raises inside hashlib instead of returning False. In the app this never')
    note('reaches login: LocalStore.validate() refuses any record with iterations that are not an int')
    note('of at least 1,000 (experiment 17). Layered checks cover each other\'s gaps.')
    a = record['hash']
    b = ('1' if a[0] == '0' else '0') + a[1:]
    print(f'  hmac.compare_digest(hash, hash with first digit changed) -> {hmac.compare_digest(a, b)}')
    note('compare_digest takes the same time wherever the first difference is; "==" can stop early')
    note('and leak, byte by byte, how much of a guess matched.')


@experiment(4, 'A', 'Work factor: PBKDF2 cost vs iterations')
def exp_cost(_):
    salt = os.urandom(16)
    base = None
    print(f'  {"iterations":>10}  {"ms per hash":>11}  {"hashes/s (1 core)":>17}  relative')
    for n in (1_000, 10_000, 50_000, 100_000, acc.PBKDF2_ITERATIONS):
        t = timed(lambda: hashlib.pbkdf2_hmac('sha256', PASSWORD.encode(), salt, n), repeat=3)
        base = base or t
        print(f'  {n:>10,}  {t * 1000:>11.2f}  {1 / t:>17,.0f}  x{t / base:,.0f}')
    note('Cost grows linearly with iterations: the defender pays it once per login,')
    note('the attacker pays it for every single guess. ATLAS uses 200,000 (OWASP 2023 suggests')
    note('600,000 for PBKDF2-HMAC-SHA256 on servers - see experiment 20 for raising it safely).')


@experiment(5, 'A', "Attacker's arithmetic: guesses per second")
def exp_rates(_):
    salt = os.urandom(16)
    n = 20_000
    start = time.perf_counter()
    for i in range(n):
        hashlib.sha256(salt + f'guess{i}'.encode()).digest()
    fast = n / (time.perf_counter() - start)
    slow = 1 / timed(lambda: acc.hash_password(PASSWORD, salt=salt), repeat=3)
    print(f'  salted SHA-256 (fast hash) : {fast:>14,.0f} guesses/s on this core')
    print(f'  ATLAS PBKDF2, 200k rounds  : {slow:>14,.1f} guesses/s on this core')
    print(f'  slowdown                    : x{fast / slow:,.0f}')
    print('\n  Time to try every password (one core, worst case):')
    print(f'  {"key space":<34} {"SHA-256":>16} {"ATLAS PBKDF2":>18}')
    spaces = {
        'top-10k common passwords': 10_000,
        '8 lowercase letters (26^8)': 26 ** 8,
        '8 letters+digits (36^8)': 36 ** 8,
        '8 mixed case+digits (62^8)': 62 ** 8,
        '12 mixed case+digits (62^12)': 62 ** 12,
    }
    for label, size in spaces.items():
        print(f'  {label:<34} {human(size / fast):>16} {human(size / slow):>18}')
    note('A GPU rig is ~1,000-10,000x faster than one core, so divide accordingly - and see why a')
    note('common password falls instantly whatever the hash: hashing slows attacks, it cannot fix')
    note('a guessable password.')


@experiment(6, 'A', 'Dictionary attack on a leaked record')
def exp_dictionary(folder):
    store = new_store(folder)
    register_passenger(store, password='summer2024')
    leaked = json.loads((folder / 'state.json').read_text())['accounts'][0]
    print(f'  stolen from state.json: email={leaked["email"]} salt={leaked["salt"][:12]}... '
          f'iterations={leaked["iterations"]:,}')
    wordlist = ['password1', '123456789', 'qwerty123', 'letmein1', 'cork2026', 'dublin2024',
                'iloveyou1', 'welcome1', 'football1', 'summer2023', 'summer2024', 'winter2024']
    start = time.perf_counter()
    for tries, guess in enumerate(wordlist, 1):
        if acc.verify_password(guess, leaked):
            took = time.perf_counter() - start
            print(f'  cracked after {tries} guesses in {took:.2f} s: {guess!r}')
            break
    else:
        print('  not found in the word list')
    note('"summer2024" passes the app policy (letter + digit, 8+ chars) yet sits in every word list.')
    note('Slow hashing costs ~30 ms per guess here; a 10-million-word list still finishes in hours to')
    note('days on GPUs. Defence in depth: device encryption, a breached-password check, and MFA on a server.')


@experiment(7, 'A', 'Password policy matrix')
def exp_policy(_):
    cases = ['short1', 'abcdefgh', '12345678', 'cork2026', 'Correct horse battery 9',
             'a' * 127 + '1', 'a' * 128 + '1', 'pässwörd1', '        1a']
    for case in cases:
        shown = case if len(case) <= 26 else case[:12] + f'...({len(case)} chars)'
        attempt(f'check_password({shown!r})', acc.check_password, case)
    note('Rules: 8-128 characters, at least one letter and one digit. Long passphrases and Unicode')
    note('are allowed (good, NIST SP 800-63B). The 128 cap stops a megabyte "password" costing')
    note('200,000 HMAC rounds over huge input - a cheap denial-of-service guard.')
    note('Gap to discuss: whitespace-only padding and well-known passwords still pass.')


@experiment(8, 'A', 'Forensics on the device file')
def exp_forensics(folder):
    store = new_store(folder)
    register_passenger(store)
    raw = (folder / 'state.json').read_text(encoding='utf-8')
    data = json.loads(raw)
    print(f'  {folder.name}/state.json is {len(raw):,} bytes; account keys: {sorted(data["accounts"][0])}')
    for needle in (PASSWORD, PASSWORD.encode().hex(), hashlib.sha256(PASSWORD.encode()).hexdigest()):
        print(f'  search for {needle[:32]!r:<36} found: {needle in raw}')
    print(f'  but personal data is plain text: email in file = {"aoife@example.ie" in raw}, '
          f'phone = {"+353871234567" in raw}')
    note('Passwords are protected by hashing; the rest of the profile relies on Android app-sandbox')
    note('storage and full-disk encryption. Discussion: what would field-level encryption with a key in')
    note('the Android Keystore add, and what would it cost?')


if __name__ == '__main__':
    main(group='A', description=__doc__.split('\n')[0])
