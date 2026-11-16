"""Bank payments (1.5.0): IBAN rules, sandbox bank, split, lifecycle, ledger, and the store's
pay-by-bank, payout and integrity rules for passengers, drivers and food sellers."""
import json
import pytest
from atlas_go import payments as pay
from atlas_go.store import LocalStore
from test_roles import T0, driver, passenger, seller

IBAN = 'IE29 AIBK 9311 5212 3456 78'
GOOD, NO_FUNDS, CLOSED = (pay.SANDBOX_IBANS[k] for k in ('approved', 'insufficient_funds', 'account_closed'))


# ---------------------------------------------------------------------------- pure rules
@pytest.mark.parametrize('iban', ['IE29AIBK93115212345678', 'DE89 3704 0044 0532 0130 00', 'GB82 WEST 1234 5698 7654 32',
                                  'FR14 2004 1010 0505 0001 3M02 606', 'nl91 abna 0417 1643 00', 'IE29-AIBK-9311-5212-3456-78'])
def test_valid_ibans_are_normalised(iban):
    cleaned = pay.clean_iban(iban)
    assert cleaned == cleaned.upper() and ' ' not in cleaned and '-' not in cleaned
    assert pay.make_iban(cleaned[:2], cleaned[4:]) == cleaned        # check digits can be recomputed


@pytest.mark.parametrize('iban,reason', [
    ('IE29AIBK93115212345679', 'check digits'),      # one digit changed
    ('IE29AIBK93115221345678', 'check digits'),      # two digits swapped
    ('IE29AIBK9311521234567', 'has 22 characters'),  # too short
    ('US29AIBK93115212345678', 'SEPA'),              # not a SEPA country
    ('IE2', 'Enter an IBAN'), ('', 'Enter an IBAN'), ("IE29AIBK9311521234'; --", 'Enter an IBAN'), (None, 'Enter an IBAN'),
])
def test_invalid_ibans_are_rejected(iban, reason):
    with pytest.raises(ValueError, match=reason):
        pay.clean_iban(iban)


def test_every_single_digit_typo_is_caught():
    """mod 97 detects every single-character substitution (and every adjacent swap of unequal characters)."""
    iban = pay.clean_iban(IBAN)
    for i in range(4, len(iban)):
        if iban[i].isdigit():
            for digit in '0123456789':
                if digit != iban[i]:
                    with pytest.raises(ValueError):
                        pay.clean_iban(iban[:i] + digit + iban[i + 1:])


def test_bank_record_keeps_no_iban():
    record = pay.bank_record('passenger', '  Aoife   Rider ', IBAN, True, T0)
    assert record['masked'] == 'IE29 •••• 5678' and record['holder'] == 'Aoife Rider' and record['bank'] == 'AIB'
    assert record['mandate']['version'] == pay.MANDATE_VERSION and record['purpose'] == 'debit'
    assert '93115212' not in json.dumps(record)
    assert pay.valid_bank(record, 'passenger') and not pay.valid_bank(record, 'driver')
    payout = pay.bank_record('driver', 'Siobhan Driver', IBAN, False, T0)
    assert payout['purpose'] == 'payout' and 'mandate' not in payout and pay.valid_bank(payout, 'driver')
    with pytest.raises(ValueError, match='mandate'):
        pay.bank_record('passenger', 'Aoife Rider', IBAN, False, T0)
    with pytest.raises(ValueError, match='holder'):
        pay.bank_record('passenger', '12345', IBAN, True, T0)


@pytest.mark.parametrize('kind,amount,net,fee', [
    ('ride', 860, 731, 129), ('ride', 1118, 950, 168), ('shared', 490, 416, 74), ('ride', 10, 8, 2),
    ('food', 1100, 765, 335), ('food', 1730, 1332, 398), ('food', 300, 45, 255),
])
def test_split_adds_up(kind, amount, net, fee):
    assert pay.split(kind, amount) == dict(payee_net=net, platform_fee=fee)
    assert net + fee == amount


def test_split_and_quote_reject_nonsense():
    for bad in (('ride', 0), ('ride', -5), ('ride', 8.6), ('tip', 100), ('food', 250)):
        with pytest.raises(ValueError):
            pay.split(*bad)
    assert pay.quote('ride', dict(pickup=0, destination=1)) == 860
    assert pay.quote('ride', dict(pickup=0, destination=1, comfort=True, multiplier=1.4)) == 1570
    assert pay.quote('shared', dict(offer='pool-1', party=2)) == 980
    assert pay.quote('food', dict(items={'bowl': 1, 'juice': 1})) == 1730
    assert pay.quote('food', dict(items={'k3-1': 2}), menu={'k3-1': 850}) == 1950
    for kind, details in (('ride', dict(pickup=0, destination=0)), ('ride', dict(pickup=0, destination=1, multiplier=4.0)),
                          ('ride', dict(pickup='0', destination=1)), ('shared', dict(offer='pool-9', party=1)),
                          ('shared', dict(offer='pool-1', party=True)), ('food', dict(items={})),
                          ('food', dict(items={'bowl': 11})), ('food', dict(items={'k3-1': 1})), ('gift', {}), ('ride', None)):
        with pytest.raises(ValueError):
            pay.quote(kind, details)


def test_shared_prices_mirror_the_store_offers(tmp_path):
    store = LocalStore(tmp_path / 'state.json')
    assert {o.id: o.price for o in store.offers} == pay.SHARED_PRICES


def test_payment_lifecycle_and_ledger():
    bank = pay.bank_record('passenger', 'Aoife Rider', GOOD, True, T0)
    p = pay.new_payment('P-1', 'ride', 'R-1', 'U-1', 860, bank, T0)
    assert p['status'] == 'authorised' and p['payee'] is None and pay.valid_payment(p)
    assert pay.entries([p]) == []                                    # an authorisation moves nothing
    with pytest.raises(ValueError, match='needs a payee'):
        pay.move(p, 'captured', T0)
    with pytest.raises(ValueError, match='cannot become refunded'):
        pay.move(p, 'refunded', T0)
    pay.move(p, 'captured', T0 + 60, payee='U-2')
    assert pay.valid_payment(p)
    for status in ('captured', 'voided', 'authorised'):
        with pytest.raises(ValueError, match='cannot become'):
            pay.move(p, status, T0, payee='U-2')
    lines = pay.entries([p])
    assert pay.balanced(lines) and pay.balance(lines, pay.payable('U-2')) == 731
    assert pay.balance(lines, pay.REVENUE) == 129 and pay.balance(lines, pay.CLEARING) == -860
    payout = dict(id='O-1', account='U-2', amount=731, last4='3000', status='paid', created=int(T0), synced=False)
    lines = pay.entries([p], [payout])
    assert pay.balanced(lines) and pay.balance(lines, pay.payable('U-2')) == 0 and pay.valid_payout(payout)
    assert pay.wallet('U-2', [p], [payout]) == dict(balance=0, earned=731, paid_out=731)
    pay.move(p, 'refunded', T0 + 120)
    lines = pay.entries([p])
    assert pay.balanced(lines) and all(pay.balance(lines, a) == 0 for a in (pay.CLEARING, pay.REVENUE, pay.payable('U-2')))
    assert not pay.balanced([('t', 'a', 5, 0)]) and not pay.balanced([('t', 'a', 5, 5)]) and not pay.balanced([('t', 'a', -1, 0)])


def test_sandbox_bank_outcomes():
    assert pay.sandbox_outcome('5678', 860) == 'approved'
    assert pay.sandbox_outcome('0002', 860) == 'insufficient_funds'
    assert pay.sandbox_outcome('0003', 1) == 'account_closed'
    assert pay.sandbox_outcome('5678', pay.DEBIT_LIMIT) == 'approved'
    assert pay.sandbox_outcome('5678', pay.DEBIT_LIMIT + 1) == 'limit_exceeded'
    for name, iban in pay.SANDBOX_IBANS.items():
        assert pay.sandbox_outcome(pay.clean_iban(iban)[-4:], 500) == name


# ---------------------------------------------------------------------------- the store
def linked_passenger(store, iban=GOOD):
    user = passenger(store)
    store.link_bank('ride2026x', 'Aoife Rider', iban, consent=True, now=T0)
    return user


def test_linking_needs_an_account_the_password_and_consent(tmp_path):
    s = LocalStore(tmp_path / 'state.json')
    s.continue_as_guest()
    with pytest.raises(ValueError, match='sign in'):
        s.link_bank('x', 'Guest', IBAN, True)
    passenger(s)
    with pytest.raises(ValueError, match='Password is not correct'):
        s.link_bank('wrong-pass1', 'Aoife Rider', IBAN, True)
    with pytest.raises(ValueError, match='mandate'):
        s.link_bank('ride2026x', 'Aoife Rider', IBAN, False)
    with pytest.raises(ValueError, match='check digits'):
        s.link_bank('ride2026x', 'Aoife Rider', IBAN[:-1] + '9', True)
    assert 'bank' not in s.user
    with pytest.raises(ValueError, match='Link a bank account'):
        s.book(0, 1, pay_by_bank=True, now=T0)
    assert s.ride is None and not s.payments
    s.link_bank('ride2026x', 'Aoife Rider', IBAN, True, now=T0)
    raw = (tmp_path / 'state.json').read_text(encoding='utf-8')
    assert '93115212345678' not in raw and 'IE29 •••• 5678' in raw
    assert LocalStore(tmp_path / 'state.json').user['bank'] == s.user['bank']
    with pytest.raises(ValueError, match='Password is not correct'):
        s.unlink_bank('nope12345')
    s.unlink_bank('ride2026x')
    assert 'bank' not in LocalStore(tmp_path / 'state.json').user


def test_ride_paid_by_bank_to_a_registered_driver_then_paid_out(tmp_path):
    s = LocalStore(tmp_path / 'state.json')
    d = driver(s)
    s.logout()
    p = linked_passenger(s)
    s.book(0, 1, driver='Siobhan · registered driver', driver_id=d['id'], now=T0, pay_by_bank=True)
    payment = s.payment(s.ride['payment'])
    assert payment['status'] == 'authorised' and payment['amount'] == s.ride['fare'] == 860 and payment['payer'] == p['id']
    with pytest.raises(ValueError, match='booking you are paying for'):
        s.unlink_bank('ride2026x')
    s.logout()
    s.login('d@atlas.ie', 'drive2026', now=T0)
    assert s.wallet() == dict(balance=0, earned=0, paid_out=0, pending=731)
    s.driver_respond(True, now=T0)
    for _ in range(3):
        s.driver_advance(now=T0)
    assert s.ride is None and payment['status'] == 'captured' and payment['payee'] == d['id']
    assert s.wallet() == dict(balance=731, earned=731, paid_out=0, pending=0)
    assert d['driver']['earnings'] == 860                          # the gross counter is unchanged
    with pytest.raises(ValueError, match='Link the bank account'):
        s.request_payout('drive2026')
    s.link_bank('drive2026', 'Siobhan Driver', 'DE89 3704 0044 0532 0130 00', now=T0)
    with pytest.raises(ValueError, match='Password is not correct'):
        s.request_payout('wrong-pass1')
    with pytest.raises(ValueError, match='Pay out your balance'):
        s.delete_account('drive2026')
    payout = s.request_payout('drive2026', now=T0)
    assert payout['status'] == 'paid' and payout['amount'] == 731 and payout['last4'] == '3000'
    assert s.wallet()['balance'] == 0 and s.my_payouts() == [payout] and s.my_payments() == [payment]
    with pytest.raises(ValueError, match='at least'):
        s.request_payout('drive2026')
    restored = LocalStore(tmp_path / 'state.json')
    assert restored.payments == s.payments and restored.payouts == s.payouts
    assert pay.balanced(pay.entries(restored.payments, restored.payouts))
    s.delete_account('drive2026')                                   # allowed now that the balance is zero


def test_cancel_releases_the_authorisation_and_simulated_drivers_are_house_payees(tmp_path):
    s = LocalStore(tmp_path / 'state.json')
    linked_passenger(s)
    s.book(0, 1, now=T0, pay_by_bank=True)
    first = s.payment(s.ride['payment'])
    s.advance_ride(cancel=True, now=T0)
    assert first['status'] == 'voided' and first['payee'] is None and pay.entries(s.payments) == []
    s.book(0, 1, offer_id='pool-1', party=2, now=T0, pay_by_bank=True)
    shared = s.payment(s.ride['payment'])
    assert shared['kind'] == 'shared' and shared['amount'] == 980 and shared['details'] == dict(offer='pool-1', party=2)
    for _ in range(4):
        s.advance_ride(now=T0)
    assert s.ride is None and shared['status'] == 'captured' and shared['payee'] == 'fleet'
    s.book(0, 1, now=T0)                                            # demo checkout: no payment at all
    assert 'payment' not in s.ride and len(s.payments) == 2
    assert [h.get('payment') for h in s.history] == [first['id'], shared['id']]


@pytest.mark.parametrize('iban,reason', [(NO_FUNDS, 'not enough funds'), (CLOSED, 'closed')])
def test_declined_payment_books_nothing(tmp_path, iban, reason):
    s = LocalStore(tmp_path / 'state.json')
    linked_passenger(s, iban)
    with pytest.raises(ValueError, match=reason):
        s.book(0, 1, offer_id='pool-1', party=2, now=T0, pay_by_bank=True)
    assert s.ride is None and not s.payments and s.offers[0].seats == 3      # no seat was reserved
    s.update_cart('add', 'bowl')
    with pytest.raises(ValueError, match=reason):
        s.checkout(0, now=T0, pay_by_bank=True)
    assert s.order is None and s.cart.count() == 1 and not s.payments
    assert LocalStore(tmp_path / 'state.json').ride is None


def test_food_paid_by_bank_to_the_seller_and_to_a_built_in_kitchen(tmp_path):
    s = LocalStore(tmp_path / 'state.json')
    sel = seller(s)
    dish = s.add_dish('Sourdough toastie', 'Cheddar and onion', '8.50')
    s.logout()
    linked_passenger(s)
    s.update_cart('add', dish)
    s.checkout(1, now=T0, pay_by_bank=True)
    payment = s.payment(s.order['payment'])
    assert payment['amount'] == 1100 and payment['details']['items'] == {dish: 1}
    s.logout()
    s.login('s@atlas.ie', 'bread2026', now=T0)
    assert s.wallet()['pending'] == 765
    s.seller_accept(now=T0)
    s.seller_ready(now=T0)
    s.advance_order(now=T0)
    s.advance_order(now=T0)
    assert payment['status'] == 'captured' and payment['payee'] == sel['id']
    assert s.wallet() == dict(balance=765, earned=765, paid_out=0, pending=0)
    s.link_bank('bread2026', 'Lee Side Bakery Ltd', CLOSED, now=T0)
    failed = s.request_payout('bread2026', now=T0)
    assert failed['status'] == 'failed' and s.wallet()['balance'] == 765      # a failed payout moves nothing
    s.link_bank('bread2026', 'Lee Side Bakery Ltd', GOOD, now=T0)
    assert s.request_payout('bread2026', now=T0)['amount'] == 765
    s.logout()
    s.login('p@atlas.ie', 'ride2026x', now=T0)
    s.update_cart('add', 'bowl')
    s.checkout(0, now=T0, pay_by_bank=True)
    house = s.payment(s.order['payment'])
    for _ in range(3):
        s.advance_order(now=T0)
    assert house['status'] == 'captured' and house['payee'] == 'kitchen-0'
    s.delete_account('ride2026x')
    assert all(p['payer'] == 'deleted' for p in s.payments)
    assert LocalStore(tmp_path / 'state.json').payments == s.payments


def tampered(tmp_path, change):
    s = LocalStore(tmp_path / 'state.json')
    d = driver(s)
    s.link_bank('drive2026', 'Siobhan Driver', GOOD, now=T0)
    s.logout()
    linked_passenger(s)
    s.book(0, 1, driver='Siobhan', driver_id=d['id'], now=T0, pay_by_bank=True)
    s.logout()
    s.login('d@atlas.ie', 'drive2026', now=T0)
    s.driver_respond(True, now=T0)
    for _ in range(3):
        s.driver_advance(now=T0)
    s.request_payout('drive2026', now=T0)
    data = json.loads(s.path.read_text(encoding='utf-8'))
    change(data)
    s.path.write_text(json.dumps(data), encoding='utf-8')
    return LocalStore(s.path)


@pytest.mark.parametrize('change', [
    lambda d: d['payments'][0].update(payee_net=860),                     # driver keeps the platform fee
    lambda d: d['payments'][0].update(amount=86000, payee_net=85871),     # payment no longer matches the fare
    lambda d: d['payouts'][0].update(amount=9999),                        # paid out more than was earned
    lambda d: d['payouts'].append(dict(d['payouts'][0])),                 # the same payout twice
    lambda d: d['payments'][0].update(status='voided', payee=None),       # completed ride, payment says voided
    lambda d: d['history'][0].update(payment='P-missing'),                # booking points at no payment
    lambda d: d['accounts'][0]['bank'].update(last4='12'),                # damaged bank record
    lambda d: d['accounts'][1]['bank'].pop('mandate'),                    # debit account without a mandate
    lambda d: d['accounts'][0].update(server=dict(id='x')),               # server link without a token
])
def test_tampered_money_state_is_quarantined(tmp_path, change):
    restored = tampered(tmp_path, change)
    assert not restored.accounts and not restored.payments and not restored.payouts
    assert (tmp_path / 'state.invalid.json').exists()


def test_pre_1_5_state_loads_without_payments(tmp_path):
    s = LocalStore(tmp_path / 'state.json')
    passenger(s)
    data = json.loads(s.path.read_text(encoding='utf-8'))
    for key in ('payments', 'payouts', 'server_url'):
        data.pop(key)
    s.path.write_text(json.dumps(data), encoding='utf-8')
    old = LocalStore(s.path)
    assert old.user and old.payments == [] and old.payouts == [] and old.server_url == ''
