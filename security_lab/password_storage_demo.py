#!/usr/bin/env python3
"""Information-security lab: how ATLAS Go registers users, stores passwords and signs them in.

Every experiment drives the app's real code - android-app/atlas_go/accounts.py (hashing, policy,
input validation) and android-app/atlas_go/store.py (LocalStore: register, login, lockout, sessions,
atomic saves, tamper checks, account deletion). Standard library only; each experiment works in its
own throw-away folder, so nothing on your machine is touched.

    python3 security_lab/password_storage_demo.py                 # all 20 experiments
    python3 security_lab/password_storage_demo.py --list          # experiments and study paths
    python3 security_lab/password_storage_demo.py --path attacker # one study path
    python3 security_lab/password_storage_demo.py -e 6 -e 13      # chosen experiments

Experiments
  A. What the app stores
     1. Anatomy of a stored credential (salt, hash, iterations) and what public_view hides
     2. Salting: one password, three accounts, three different hashes
     3. Verifying a password: constant-time compare, malformed records fail closed
     4. Work factor: how PBKDF2 cost grows with the iteration count
     5. Attacker's arithmetic: guesses per second and time to exhaust a key space
     6. Dictionary attack on a leaked state.json record
     7. Password policy matrix: what check_password accepts and rejects
     8. Forensics on the device file: no plaintext password anywhere in state.json
  B. Registration and identity
     9. Input validation as a security control (email, phone, plate, licence, business, price)
    10. One identity per email: duplicate and case-variant registrations
    11. Role separation: what a passenger, a driver and a seller may do
  C. Sign-in defences
    12. Throttling timeline: 5 failures -> 60 s lockout -> recovery
    13. No account enumeration through error messages
    14. Timing side channel: unknown email vs wrong password (and the dummy-hash fix)
    15. Limits of the lockout: per email, in memory only, gone after a restart
  D. Integrity, sessions and lifecycle
    16. Sessions: survive a restart, logout, guest mode, session pointing at a deleted user
    17. Tampered state.json is rejected and quarantined to state.invalid.json
    18. Atomic saves and rollback: a failed disk write never half-registers a user
    19. Account deletion: re-authentication, active-trip guard, anonymised history
    20. Upgrading old hashes: rehash-on-login when the iteration count is raised (extension)

See docs/INFORMATION_SECURITY.md for the full teaching guide.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import statistics
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'android-app'))

from atlas_go import accounts as acc  # noqa: E402
from atlas_go import store as store_module  # noqa: E402
from atlas_go.store import LocalStore  # noqa: E402

PASSWORD = 'cork2026'
EXPERIMENTS: dict[int, tuple[str, str, object]] = {}

STUDY_PATHS = {
    'foundations': ('First lesson: what is stored and why', [1, 2, 3, 7, 8]),
    'attacker': ('Think like an attacker who stole the file or hammers the login', [4, 5, 6, 13, 14, 15]),
    'defender': ('Controls the app applies at registration and sign-in', [9, 10, 11, 12, 13, 16]),
    'integrity': ('Keeping the stored data trustworthy', [8, 17, 18, 19]),
    'lifecycle': ('Follow one user from sign-up to deletion', [9, 1, 12, 16, 19, 20]),
    'full': ('Every experiment in order', list(range(1, 21))),
}


# --------------------------------------------------------------------------- helpers
def experiment(number: int, group: str, title: str):
    def register(fn):
        EXPERIMENTS[number] = (group, title, fn)
        return fn
    return register


def heading(number: int, title: str) -> None:
    print('\n' + '=' * 78)
    print(f'Experiment {number:>2}: {title}')
    print('=' * 78)


def note(text: str) -> None:
    print(f'  -> {text}')


def attempt(label: str, fn, *args, **kwargs):
    """Run an app call and print either its result or the exact message the user would see."""
    try:
        result = fn(*args, **kwargs)
        print(f'  {label:<44} OK    {result!r}' if result is not None else f'  {label:<44} OK')
        return result
    except ValueError as error:
        print(f'  {label:<44} REJECTED  "{error}"')
        return None


@contextmanager
def workspace():
    with tempfile.TemporaryDirectory(prefix='atlas-lab-') as folder:
        yield Path(folder)


def new_store(folder: Path) -> LocalStore:
    return LocalStore(folder / 'state.json')


def register_passenger(store: LocalStore, name='Aoife Murphy', email='aoife@example.ie',
                       phone='087 123 4567', password=PASSWORD, now=None) -> dict:
    return store.register('passenger', name, email, phone, password, now=now)


def register_driver(store: LocalStore, email='ciaran@example.ie') -> dict:
    return store.register('driver', 'Ciaran Walsh', email, '086 555 0101', 'Driver2026',
                          vehicle='Electric hatchback', plate='231-C-4567', licence='IE12345', seats='4', base=1)


def register_seller(store: LocalStore, email='niamh@example.ie') -> dict:
    return store.register('seller', 'Niamh Byrne', email, '085 444 0202', 'Kitchen2026',
                          kitchen='Lab Test Kitchen', cuisine='Irish', registration='IE-123456', place=1, prep='20')


def timed(fn, repeat=5) -> float:
    samples = []
    for _ in range(repeat):
        start = time.perf_counter()
        fn()
        samples.append(time.perf_counter() - start)
    return statistics.median(samples)


def human(seconds: float) -> str:
    for unit, size in (('years', 31_557_600), ('days', 86_400), ('hours', 3600), ('minutes', 60)):
        if seconds >= size:
            return f'{seconds / size:,.1f} {unit}'
    return f'{seconds:.2f} seconds'


# --------------------------------------------------------------------------- A. what is stored
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
    a, b = record['hash'], '0' + record['hash'][1:]
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


# --------------------------------------------------------------------------- B. registration
@experiment(9, 'B', 'Input validation as a security control')
def exp_validation(_):
    checks = [
        ('clean_email', acc.clean_email, ['  Aoife@Example.IE ', 'aoife@@example.ie', 'a@b', 'x' * 75 + '@ex.ie']),
        ('clean_phone', acc.clean_phone, ['087 123 4567', '0035387 1234567', '+44 20 7946 0958', '12345', '+0871234567']),
        ('clean_name', acc.clean_name, ['  Aoife   Murphy ', 'A', 'Aoife\nAdmin', 'Aoife\x1b[31m', 'Ao\x00fe', 'Aoife\u202eetirw', 'Bobby<script>']),
        ('clean_plate', acc.clean_plate, ['231-c-4567', '231 C 4567', '23-C-1234567']),
        ('clean_licence', acc.clean_licence, ['ie12345', 'IE 12345', 'X1']),
        ('clean_business', acc.clean_business, ['ie-123456', 'IE_123456']),
        ('parse_price', acc.parse_price, ['8.50', '€8,50', '0.10', '-5', '1e3']),
    ]
    for name, fn, values in checks:
        for value in values:
            attempt(f'{name}({value!r})', fn, value)
    note('Normalising (lower-case email, E.164 phone, upper-case plate) makes one person = one key,')
    note('which experiment 10 relies on. Newlines are folded into spaces and other control characters')
    note('(NUL, terminal escapes) are refused, so a name cannot forge lines in a receipt or log.')
    note('Gaps to discuss: the right-to-left override U+202E passes (it is not < 32), and "<script>"')
    note('is accepted - escaping on output is the screen\'s job, not the validator\'s.')


@experiment(10, 'B', 'One identity per email')
def exp_duplicate(folder):
    store = new_store(folder)
    register_passenger(store)
    store.logout()
    attempt('register again, same email', register_passenger, store)
    attempt('register again, AOIFE@EXAMPLE.IE', register_passenger, store, email=' AOIFE@EXAMPLE.IE ')
    attempt('register as driver, same email', store.register, 'driver', 'Aoife Murphy', 'aoife@example.ie',
            '087 123 4567', 'Driver2026', vehicle='Electric hatchback', plate='231-C-4567', licence='IE12345')
    attempt('login with upper-case email', lambda: store.login('AOIFE@example.ie', PASSWORD)['email'])
    print(f'  accounts on device: {len(store.accounts)}')
    note('Because emails are normalised before comparison, case tricks cannot create a second identity.')
    note('Trade-off: the duplicate message reveals that this email is registered here (compare with 13).')


@experiment(11, 'B', 'Role separation')
def exp_roles(folder):
    store = new_store(folder)
    passenger = register_passenger(store)
    attempt('passenger: go online as driver', store.set_online, True)
    attempt('passenger: add a dish', store.add_dish, 'Soup', 'Daily soup', '5.00')
    store.logout()
    driver = register_driver(store)
    attempt('driver: book a ride', store.book, 0, 1)
    attempt('driver: go online', store.set_online, True)
    store.logout()
    seller = register_seller(store)
    attempt('seller: add a dish', store.add_dish, 'Seafood chowder', 'With brown bread', '€8,50')
    attempt('seller: go online as driver', store.set_online, True)
    attempt('seller: order food', store.checkout, 1)
    for label, account in (('passenger', passenger), ('driver', driver), ('seller', seller)):
        extra = sorted(set(acc.public_view(account)) - {'id', 'role', 'name', 'email', 'phone', 'created'})
        print(f'  public_view({label:<9}) role={account["role"]:<9} extra profile: {extra}')
    note('Each action checks the signed-in role on the store side, not only by hiding buttons in the UI.')


# --------------------------------------------------------------------------- C. sign-in defences
@experiment(12, 'C', 'Throttling timeline')
def exp_lockout(folder):
    store = new_store(folder)
    register_passenger(store)
    store.logout()
    t0 = 1_000_000.0
    print(f'  MAX_FAILED_LOGINS={acc.MAX_FAILED_LOGINS}, LOCKOUT_SECONDS={acc.LOCKOUT_SECONDS}')
    for i in range(1, acc.MAX_FAILED_LOGINS + 1):
        attempt(f't+{i:>2}s wrong password #{i}', store.login, 'aoife@example.ie', f'wrong{i}', now=t0 + i)
        print(f'  {"":44} failures[email] = {store.failures["aoife@example.ie"]}')
    attempt('t+10s correct password while locked', store.login, 'aoife@example.ie', PASSWORD, now=t0 + 10)
    attempt('t+64s correct password, still locked', store.login, 'aoife@example.ie', PASSWORD, now=t0 + 64)
    attempt('t+66s correct password after lockout',
            lambda: store.login('aoife@example.ie', PASSWORD, now=t0 + 66)['name'])
    print(f'  failures after success: {store.failures}')
    note('While locked the password is not even checked, so guessing is capped at 5 per minute:')
    note('7,200 guesses a day online, versus experiment 5\'s offline rate.')


@experiment(13, 'C', 'No account enumeration through error messages')
def exp_enumeration(folder):
    store = new_store(folder)
    register_passenger(store)
    store.logout()
    attempt('registered email, wrong password', store.login, 'aoife@example.ie', 'nope12345')
    attempt('unknown email', store.login, 'nobody@example.ie', 'nope12345')
    attempt('empty email and password', store.login, '', '')
    for _ in range(acc.MAX_FAILED_LOGINS - 1):
        try:
            store.login('nobody@example.ie', 'nope12345')
        except ValueError:
            pass
    attempt('unknown email, 6th try', store.login, 'nobody@example.ie', 'nope12345')
    note('Same message and same lockout whether or not the account exists, so the login screen')
    note('does not confirm who uses ATLAS. Experiments 10 and 14 show the remaining side doors.')


@experiment(14, 'C', 'Timing side channel on sign-in')
def exp_timing(folder):
    store = new_store(folder)
    register_passenger(store)
    store.logout()

    def try_login(email):
        store.failures.clear()
        try:
            store.login(email, 'wrong-guess-1')
        except ValueError:
            pass

    known = timed(lambda: try_login('aoife@example.ie'), repeat=5)
    unknown = timed(lambda: try_login('nobody@example.ie'), repeat=5)
    print(f'  registered email, wrong password : {known * 1e6:>10,.0f} microseconds')
    print(f'  unknown email                    : {unknown * 1e6:>10,.0f} microseconds'
          f'   (about {known / max(unknown, 1e-9):,.0f}x faster)')
    note('Same words on screen, but an unknown email skips PBKDF2, so a stopwatch tells them apart.')
    dummy = acc.hash_password('dummy-password-0')

    def fixed_login(email, password):
        account = next((a for a in store.accounts if a['email'] == email), None)
        ok = acc.verify_password(password, account or dummy)  # always pay for one PBKDF2
        return bool(account) and ok

    fixed_known = timed(lambda: fixed_login('aoife@example.ie', 'wrong-guess-1'), repeat=5)
    fixed_unknown = timed(lambda: fixed_login('nobody@example.ie', 'wrong-guess-1'), repeat=5)
    print(f'  with a dummy hash: {fixed_known * 1e6:,.0f} vs {fixed_unknown * 1e6:,.0f} microseconds')
    note('Fix: verify against a dummy record when the email is unknown. On a single-user phone the risk')
    note('is small (the attacker already holds the device); on a server login it matters.')


@experiment(15, 'C', 'Limits of the lockout')
def exp_lockout_limits(folder):
    store = new_store(folder)
    register_passenger(store)
    store.logout()
    for i in range(acc.MAX_FAILED_LOGINS):
        try:
            store.login('aoife@example.ie', f'wrong{i}')
        except ValueError:
            pass
    attempt('locked account, correct password', store.login, 'aoife@example.ie', PASSWORD)
    attempt('a different email is not locked', store.login, 'other@example.ie', 'guess12345')
    restarted = new_store(folder)  # app killed and reopened
    print(f'  after restart: failures = {restarted.failures}')
    attempt('after restart, correct password', lambda: restarted.login('aoife@example.ie', PASSWORD)['name'])
    note('Failure counts live in memory (LocalStore.failures) and are keyed by email. Restarting the')
    note('app clears them, and spraying one password across many emails never trips any single lock.')
    note('Discussion: persist the counter, add a device-wide limit, or back off exponentially?')


# --------------------------------------------------------------------------- D. integrity and lifecycle
@experiment(16, 'D', 'Sessions')
def exp_sessions(folder):
    store = new_store(folder)
    user = register_passenger(store)
    print(f'  after register: session={store.session} signed_in={store.signed_in}')
    reopened = new_store(folder)
    print(f'  after app restart: user={reopened.user["name"] if reopened.user else None}')
    reopened.logout()
    print(f'  after logout: session={reopened.session} signed_in={reopened.signed_in}')
    reopened.continue_as_guest()
    print(f'  guest: session={reopened.session} guest={reopened.guest} role={reopened.role} '
          f'(can book, has no account)')
    reopened.login('aoife@example.ie', PASSWORD)
    reopened.delete_account(PASSWORD)
    data = json.loads((folder / 'state.json').read_text())
    print(f'  after deletion: session={data["session"]} accounts={len(data["accounts"])}')
    note(f'The session is just the account id ({user["id"]}) in the device file: there is no token or')
    note('expiry, because the only party to trust is this phone. A server would issue an expiring,')
    note('signed session token instead (see the Kerberos and SSO sections of the guide).')


@experiment(17, 'D', 'Tampered state.json is quarantined')
def exp_tamper(folder):
    tampers = {
        'iterations lowered to 1': lambda d: d['accounts'][0].update(iterations=1),
        'iterations stored as text': lambda d: d['accounts'][0].update(iterations='200000'),
        'duplicate email injected': lambda d: d['accounts'].append(dict(d['accounts'][0], id='U-evil')),
        'role escalated to "admin"': lambda d: d['accounts'][0].update(role='admin'),
        'session for a fake user': lambda d: d.update(session='U-attacker'),
        'hash field emptied': lambda d: d['accounts'][0].update(hash=''),
    }
    for index, (label, change) in enumerate(tampers.items(), 1):
        case = folder / f'case{index}'
        case.mkdir()
        register_passenger(new_store(case))
        data = json.loads((case / 'state.json').read_text())
        change(data)
        (case / 'state.json').write_text(json.dumps(data))
        reopened = new_store(case)
        print(f'  {label:<28} -> accounts loaded: {len(reopened.accounts)}, '
              f'quarantined: {(case / "state.invalid.json").exists()}')
    note('validate() checks every field before any screen reads it. On failure the file is moved to')
    note('state.invalid.json for diagnosis and the app starts clean - it never runs on half-trusted data.')
    note('Discussion: validation catches malformed edits, not a well-formed forged record. What would an')
    note('HMAC over the file (key in Android Keystore) add?')


@experiment(18, 'D', 'Atomic saves and rollback')
def exp_atomic(folder):
    store = new_store(folder)
    register_passenger(store)
    store.logout()
    before = (folder / 'state.json').read_bytes()
    with mock.patch.object(store_module.os, 'fsync', side_effect=OSError('disk full')):
        try:
            store.register('passenger', 'Brian Kelly', 'brian@example.ie', '087 765 4321', 'brian2026')
        except OSError as error:
            print(f'  register during a failed write raised OSError({error})')
    print(f'  in memory: accounts={len(store.accounts)} session={store.session}  (rolled back)')
    print(f'  on disk unchanged: {(folder / "state.json").read_bytes() == before}')
    print(f'  leftover temp file: {(folder / "state.tmp").exists()} (overwritten on the next save)')
    attempt('retry after the disk recovers', lambda: store.register(
        'passenger', 'Brian Kelly', 'brian@example.ie', '087 765 4321', 'brian2026')['email'])
    note('save() writes state.tmp, fsyncs, then os.replace()s it over state.json in one step, and')
    note('commit() restores the in-memory snapshot if that fails. Integrity = no half-written accounts.')


@experiment(19, 'D', 'Account deletion')
def exp_delete(folder):
    store = new_store(folder)
    user = register_passenger(store)
    store.book(0, 1)
    attempt('delete with wrong password', store.delete_account, 'not-mine-1')
    attempt('delete during an active ride', store.delete_account, PASSWORD)
    store.advance_ride(cancel=True)
    print(f'  history before: passenger field = {[r["passenger"] for r in store.history]}')
    attempt('delete with correct password', store.delete_account, PASSWORD)
    print(f'  history after:  passenger field = {[r["passenger"] for r in store.history]}')
    raw = (folder / 'state.json').read_text()
    print(f'  email still in file: {"aoife@example.ie" in raw}; account id still in file: {user["id"] in raw}')
    attempt('login after deletion', store.login, 'aoife@example.ie', PASSWORD)
    seller_store = new_store(folder / 'seller')
    register_seller(seller_store)
    seller_store.delete_account('Kitchen2026')
    k = seller_store.kitchens[0]
    print(f'  deleted seller kitchen: open={k["open"]} owner={k["owner"]!r} registration={k["registration"]!r}')
    note('Deletion demands the password again (re-authentication) so an unlocked phone is not enough,')
    note('waits until no trip is in progress, then removes credentials and personal data while keeping')
    note('anonymised trip records - the GDPR "erasure" vs "keep the books" balance.')


@experiment(20, 'D', 'Upgrading old hashes (extension)')
def exp_rehash(folder):
    store = new_store(folder)
    register_passenger(store)
    old = acc.hash_password(PASSWORD, iterations=10_000)
    store.accounts[0].update(old)
    store.save()
    store.logout()
    print(f'  legacy record: iterations={store.accounts[0]["iterations"]:,}')

    def login_with_upgrade(email, password, target=acc.PBKDF2_ITERATIONS):
        account = store.login(email, password)  # the app's real login
        if account['iterations'] < target:  # proposed extension
            before = store.snapshot()
            account.update(acc.hash_password(password, iterations=target))
            store.commit(before)
            print(f'  upgraded on login: {old["iterations"]:,} -> {account["iterations"]:,} iterations')
        return account

    login_with_upgrade('aoife@example.ie', PASSWORD)
    stored = json.loads((folder / 'state.json').read_text())['accounts'][0]
    print(f'  on disk now: iterations={stored["iterations"]:,}, new salt={stored["salt"] != old["salt"]}')
    print(f'  old password still works: {acc.verify_password(PASSWORD, stored)}')
    note('Because each record carries its own iteration count, the app already verifies old and new')
    note('records side by side. The plaintext is only available at login, so that is the moment to')
    note('re-hash. Exercise: add this to LocalStore.login and write a test for it.')


# --------------------------------------------------------------------------- runner
def list_all() -> None:
    groups = {'A': 'What the app stores', 'B': 'Registration and identity',
              'C': 'Sign-in defences', 'D': 'Integrity, sessions and lifecycle'}
    for group, title in groups.items():
        print(f'\n{group}. {title}')
        for number, (g, name, _) in sorted(EXPERIMENTS.items()):
            if g == group:
                print(f'  {number:>2}. {name}')
    print('\nStudy paths (--path NAME)')
    for name, (purpose, steps) in STUDY_PATHS.items():
        print(f'  {name:<12} {purpose}: {" -> ".join(map(str, steps))}')


def run(numbers) -> None:
    for number in numbers:
        _, title, fn = EXPERIMENTS[number]
        heading(number, title)
        with workspace() as folder:
            fn(folder)


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('-e', '--experiment', type=int, action='append', choices=sorted(EXPERIMENTS),
                        metavar='N', help='run experiment N (repeatable)')
    parser.add_argument('-p', '--path', choices=sorted(STUDY_PATHS), help='run a study path')
    parser.add_argument('-l', '--list', action='store_true', help='list experiments and study paths')
    args = parser.parse_args(argv)
    if args.list:
        list_all()
        return
    if args.path:
        purpose, numbers = STUDY_PATHS[args.path]
        print(f'Study path "{args.path}": {purpose}')
    else:
        numbers = args.experiment or sorted(EXPERIMENTS)
    run(numbers)
    print('\nDone. Guide: docs/INFORMATION_SECURITY.md')


if __name__ == '__main__':
    main()
