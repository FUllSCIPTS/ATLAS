#!/usr/bin/env python3
"""Security lab C - sign-in defences: lockout, enumeration, timing (experiments 12-15).

Runs against the app's real code: android-app/atlas_go/store.py (LocalStore.login, LocalStore.failures).
Standard library only; every experiment works in its own throw-away folder.

    python3 security_lab/lab_c_signin_defences.py          # every experiment in this lab
    python3 security_lab/lab_c_signin_defences.py --list
    python3 security_lab/lab_c_signin_defences.py -e 12

Experiments
  12. Throttling timeline: 5 failures -> 60 s lockout -> recovery
  13. No account enumeration through error messages
  14. Timing side channel: unknown email vs wrong password (and the dummy-hash fix)
  15. Limits of the lockout: per email, in memory only, gone after a restart

All four labs and the cross-category study paths: python3 security_lab/password_storage_demo.py --list
See docs/INFORMATION_SECURITY.md for the full teaching guide.
"""
from __future__ import annotations

from lab_common import (
    PASSWORD, acc, attempt, experiment, main, new_store, note, register_passenger, timed,
)


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


if __name__ == '__main__':
    main(group='C', description=__doc__.split('\n')[0])
