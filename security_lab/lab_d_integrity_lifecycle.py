#!/usr/bin/env python3
"""Security lab D - integrity, sessions and lifecycle (experiments 16-20).

Runs against the app's real code: android-app/atlas_go/store.py (load/validate, save/commit, logout, delete_account).
Standard library only; every experiment works in its own throw-away folder.

    python3 security_lab/lab_d_integrity_lifecycle.py          # every experiment in this lab
    python3 security_lab/lab_d_integrity_lifecycle.py --list
    python3 security_lab/lab_d_integrity_lifecycle.py -e 16

Experiments
  16. Sessions: survive a restart, logout, guest mode, session pointing at a deleted user
  17. Tampered state.json is rejected and quarantined to state.invalid.json
  18. Atomic saves and rollback: a failed disk write never half-registers a user
  19. Account deletion: re-authentication, active-trip guard, anonymised history
  20. Upgrading old hashes: rehash-on-login when the iteration count is raised (extension)

All four labs and the cross-category study paths: python3 security_lab/password_storage_demo.py --list
See docs/INFORMATION_SECURITY.md for the full teaching guide.
"""
from __future__ import annotations

import json
from unittest import mock

from lab_common import (
    PASSWORD, acc, attempt, experiment, main, new_store, note, register_passenger,
    register_seller,
)
from atlas_go import store as store_module  # noqa: E402  (android-app/ added by lab_common)


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


if __name__ == '__main__':
    main(group='D', description=__doc__.split('\n')[0])
