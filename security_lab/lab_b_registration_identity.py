#!/usr/bin/env python3
"""Security lab B - registration and identity: validation, uniqueness, roles (experiments 9-11).

Runs against the app's real code: accounts.py (clean_* validators) and store.py (LocalStore.register and role checks).
Standard library only; every experiment works in its own throw-away folder.

    python3 security_lab/lab_b_registration_identity.py          # every experiment in this lab
    python3 security_lab/lab_b_registration_identity.py --list
    python3 security_lab/lab_b_registration_identity.py -e 9

Experiments
   9. Input validation as a security control (email, phone, plate, licence, business, price)
  10. One identity per email: duplicate and case-variant registrations
  11. Role separation: what a passenger, a driver and a seller may do

All four labs and the cross-category study paths: python3 security_lab/password_storage_demo.py --list
See docs/INFORMATION_SECURITY.md for the full teaching guide.
"""
from __future__ import annotations

from lab_common import (
    PASSWORD, acc, attempt, experiment, main, new_store, note, register_driver,
    register_passenger, register_seller,
)


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


if __name__ == '__main__':
    main(group='B', description=__doc__.split('\n')[0])
