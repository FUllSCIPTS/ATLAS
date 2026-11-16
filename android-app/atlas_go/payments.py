"""Bank payments for passengers, drivers and food sellers (1.5.0): IBAN rules, the sandbox bank,
the payment lifecycle, the commission split and a double-entry ledger.

Pure Python, shared by the phone (store.py) and the PostgreSQL server (server/), so the two can
never disagree about what an amount is or where it goes.

The bank is a SANDBOX: IBANs are validated for real (ISO 13616 length and mod-97 check digits), but
no bank is contacted and no money moves. A licensed payment provider (PSD2 / SEPA Direct Debit)
attaches behind the same three calls: mandate, debit and credit. The full IBAN is used once, when
the account is linked, and is never stored: only the holder, country, bank code and last four
characters are kept.
"""
from __future__ import annotations

import re

from .domain import DISHES, fare

# ---------------------------------------------------------------------------- IBAN (ISO 13616)
IBAN_LENGTHS = {
    'AT': 20, 'BE': 16, 'BG': 22, 'CH': 21, 'CY': 28, 'CZ': 24, 'DE': 22, 'DK': 18, 'EE': 20, 'ES': 24,
    'FI': 18, 'FR': 27, 'GB': 22, 'GR': 27, 'HR': 21, 'HU': 28, 'IE': 22, 'IS': 26, 'IT': 27, 'LI': 21,
    'LT': 20, 'LU': 20, 'LV': 21, 'MC': 27, 'MT': 31, 'NL': 18, 'NO': 15, 'PL': 28, 'PT': 25, 'RO': 24,
    'SE': 24, 'SI': 19, 'SK': 24, 'SM': 27,
}
IRISH_BANKS = {'AIBK': 'AIB', 'BOFI': 'Bank of Ireland', 'IPBS': 'permanent tsb', 'REVO': 'Revolut',
               'CITI': 'Citibank', 'BARC': 'Barclays', 'PFSR': 'An Post Money', 'NTSB': 'N26'}
IBAN_SHAPE = re.compile(r'^[A-Z]{2}\d{2}[A-Z0-9]{11,30}$')


def _mod97(text: str) -> int:
    """ISO 7064 mod 97-10 over the rearranged IBAN: letters count as 10..35."""
    return int(''.join(str(int(ch, 36)) for ch in text)) % 97


def iban_check_digits(country: str, bban: str) -> str:
    """The two check digits that make country + digits + bban a valid IBAN."""
    return f'{98 - _mod97(bban + country + "00"):02d}'


def make_iban(country: str, bban: str) -> str:
    """Build a valid IBAN from a country and a BBAN (used for sandbox test accounts)."""
    return clean_iban(country + iban_check_digits(country, bban) + bban)


def clean_iban(value: str) -> str:
    """Normalise and verify an IBAN: SEPA country, exact length, and mod-97 check digits."""
    iban = re.sub(r'[\s-]', '', value or '').upper()
    if not IBAN_SHAPE.match(iban):
        raise ValueError('Enter an IBAN such as IE29 AIBK 9311 5212 3456 78.')
    if iban[:2] not in IBAN_LENGTHS:
        raise ValueError('This IBAN is not from a SEPA country ATLAS Go can pay or debit.')
    if len(iban) != IBAN_LENGTHS[iban[:2]]:
        raise ValueError(f'An IBAN from {iban[:2]} has {IBAN_LENGTHS[iban[:2]]} characters; this one has {len(iban)}.')
    if _mod97(iban[4:] + iban[:4]) != 1:
        raise ValueError('The IBAN check digits do not match. Check for a mistyped character.')
    return iban


def mask_iban(iban: str) -> str:
    return f'{iban[:4]} •••• {iban[-4:]}'


def clean_holder(value: str) -> str:
    value = ' '.join((value or '').split())
    if not 2 <= len(value) <= 60 or any(ord(ch) < 32 for ch in value) or not re.search(r'[^\W\d_]', value):
        raise ValueError('Account holder name must be 2 to 60 characters, as shown on the bank statement.')
    return value


# ---------------------------------------------------------------------------- linked bank account
MANDATE_VERSION = 'SDD-CORE-1'
MANDATE_TEXT = ('By confirming, you authorise ATLAS Go to send instructions to your bank to debit your '
                'account for the rides and food you book, and your bank to debit your account in accordance '
                'with those instructions. You are entitled to a refund from your bank under the terms of your '
                'agreement with it; claim it within 8 weeks of the debit. Sandbox: no real debit is made.')
PURPOSES = {'passenger': 'debit', 'driver': 'payout', 'seller': 'payout'}


def bank_record(role: str, holder: str, iban: str, consent: bool, now: float, mandate_id: str | None = None) -> dict:
    """What is kept about a linked bank account. The full IBAN is deliberately not part of it."""
    holder, iban = clean_holder(holder), clean_iban(iban)
    if role not in PURPOSES:
        raise ValueError('Only passengers, drivers and food sellers can link a bank account.')
    record = dict(holder=holder, country=iban[:2], last4=iban[-4:], masked=mask_iban(iban),
                  bank=IRISH_BANKS.get(iban[4:8], '') if iban[:2] == 'IE' else '',
                  purpose=PURPOSES[role], linked=int(now))
    if PURPOSES[role] == 'debit':
        if consent is not True:
            raise ValueError('Tick the Direct Debit mandate to pay by bank.')
        record['mandate'] = dict(id=mandate_id or f'M-{int(now * 1000)}', version=MANDATE_VERSION, signed=int(now))
    return record


def valid_bank(bank, role: str) -> bool:
    if not isinstance(bank, dict) or bank.get('purpose') != PURPOSES.get(role):
        return False
    if not all(isinstance(bank.get(k), str) for k in ('holder', 'country', 'last4', 'masked', 'bank')):
        return False
    if bank['country'] not in IBAN_LENGTHS or not re.fullmatch(r'[A-Z0-9]{4}', bank['last4']):
        return False
    if bank['masked'] != f"{bank['masked'][:4]} •••• {bank['last4']}" or type(bank.get('linked')) is not int:
        return False
    mandate = bank.get('mandate')
    if bank['purpose'] == 'debit':
        return isinstance(mandate, dict) and isinstance(mandate.get('id'), str) and \
            mandate.get('version') == MANDATE_VERSION and type(mandate.get('signed')) is int
    return mandate is None


# ---------------------------------------------------------------------------- the sandbox bank
DEBIT_LIMIT = 50_000         # one sandbox debit is capped at €500, like a low-value SEPA limit
MIN_PAYOUT = 100             # €1
DECLINES = {'insufficient_funds': 'Your bank declined the payment: not enough funds.',
            'account_closed': 'Your bank reports this account as closed. Link a different account.',
            'limit_exceeded': 'This amount is above the €500 limit for one bank payment.'}


def sandbox_outcome(last4: str, amount: int) -> str:
    """The sandbox bank's answer, decided only by the account's last four characters and the amount
    (as payment-provider sandboxes do with magic test numbers): ...0002 has no funds, ...0003 is closed."""
    if last4 == '0003':
        return 'account_closed'
    if amount > DEBIT_LIMIT:
        return 'limit_exceeded'
    if last4 == '0002':
        return 'insufficient_funds'
    return 'approved'


SANDBOX_IBANS = {'approved': make_iban('IE', 'AIBK93115212345678'),
                 'insufficient_funds': make_iban('IE', 'AIBK93115200000002'),
                 'account_closed': make_iban('IE', 'AIBK93115200000003')}


# ---------------------------------------------------------------------------- amounts and the split
KINDS = ('ride', 'shared', 'food')
RIDE_COMMISSION_BP = 1500     # 15 % of a ride fare stays with the platform
FOOD_COMMISSION_BP = 1000     # 10 % of the food subtotal
DELIVERY_FEE = 250
SHARED_PRICES = {'pool-1': 490, 'pool-2': 590, 'pool-3': 990, 'pool-4': 690}   # per seat; mirrors store.offers
PRICE_CAP = 2.0               # Layer 2's Guardian cap (twin.PRICE_CAP)
HOUSE_PAYEES = ('fleet', 'kitchen-0', 'kitchen-1', 'kitchen-2')    # simulated drivers and built-in kitchens


def priced(base: int, multiplier: float) -> int:
    """Fare in cents after a capped busy-time multiplier, rounded to 10 cents (store._priced)."""
    return base if multiplier == 1.0 else int(round(base * multiplier / 10.0)) * 10


def _share(amount: int, basis_points: int) -> int:
    return (amount * basis_points + 5000) // 10000        # integer cents, half rounds up


def split(kind: str, amount: int) -> dict:
    """Who gets what from a captured payment. Always: payee_net + platform_fee == amount."""
    if kind not in KINDS or type(amount) is not int or amount <= 0:
        raise ValueError('Unknown payment kind or amount.')
    if kind == 'food':
        if amount <= DELIVERY_FEE:
            raise ValueError('A food payment includes the delivery fee.')
        fee = DELIVERY_FEE + _share(amount - DELIVERY_FEE, FOOD_COMMISSION_BP)
    else:
        fee = _share(amount, RIDE_COMMISSION_BP)
    return dict(payee_net=amount - fee, platform_fee=fee)


def quote(kind: str, details: dict, menu: dict | None = None) -> int:
    """The amount a booking costs, recomputed from what was booked. The server calls this with the
    client's description and ignores any amount the client sent. menu maps dish id -> price in cents
    for a seller kitchen; built-in dishes use the bundled menu."""
    if not isinstance(details, dict):
        raise ValueError('Booking details are missing.')
    if kind == 'ride':
        multiplier = details.get('multiplier', 1.0)
        if type(multiplier) not in (int, float) or not 1.0 <= multiplier <= PRICE_CAP:
            raise ValueError('Prices are capped at twice the base fare.')
        pickup, destination = details.get('pickup'), details.get('destination')
        if type(pickup) is not int or type(destination) is not int or type(details.get('comfort', False)) is not bool:
            raise ValueError('Invalid route.')
        return priced(fare(pickup, destination, details.get('comfort', False)), float(multiplier))
    if kind == 'shared':
        if details.get('offer') not in SHARED_PRICES or details.get('party') not in (1, 2) or \
                type(details.get('party')) is not int:
            raise ValueError('Invalid shared ride.')
        return SHARED_PRICES[details['offer']] * details['party']
    if kind == 'food':
        items = details.get('items')
        prices = {d.id: d.price for d in DISHES.values()} if menu is None else menu
        if not isinstance(items, dict) or not items:
            raise ValueError('The order has no items.')
        total = 0
        for dish, quantity in items.items():
            if dish not in prices or type(quantity) is not int or not 1 <= quantity <= 10:
                raise ValueError('Unknown dish or quantity.')
            total += prices[dish] * quantity
        return total + DELIVERY_FEE
    raise ValueError('Unknown payment kind.')


# ---------------------------------------------------------------------------- payment lifecycle
STATUSES = ('authorised', 'captured', 'voided', 'declined', 'refunded')
TRANSITIONS = {'authorised': ('captured', 'voided'), 'captured': ('refunded',),
               'voided': (), 'declined': (), 'refunded': ()}


def new_payment(payment_id: str, kind: str, ref: str, payer: str, amount: int, bank: dict, now: float,
                details: dict | None = None) -> dict:
    """Authorise a payment against the payer's mandate. Raises ValueError with the bank's reason when
    the sandbox bank declines; otherwise returns the record in status 'authorised' (money reserved,
    nothing moved yet)."""
    if not valid_bank(bank, 'passenger'):
        raise ValueError('Link a bank account before paying by bank.')
    parts = split(kind, amount)
    outcome = sandbox_outcome(bank['last4'], amount)
    if outcome != 'approved':
        raise ValueError(DECLINES[outcome])
    return dict(id=payment_id, kind=kind, ref=ref, payer=payer, payee=None, amount=amount, **parts,
                last4=bank['last4'], mandate=bank['mandate']['id'], status='authorised',
                created=int(now), updated=int(now), details=dict(details or {}), synced=False)


def move(payment: dict, status: str, now: float, payee: str | None = None) -> None:
    """Apply one legal transition in place; anything else is refused (state-transition table above)."""
    if status not in TRANSITIONS.get(payment.get('status'), ()):
        raise ValueError(f"A payment that is {payment.get('status')} cannot become {status}.")
    if status == 'captured':
        if not isinstance(payee, str) or not payee:
            raise ValueError('A captured payment needs a payee.')
        payment['payee'] = payee
    payment['status'], payment['updated'] = status, int(now)


def valid_payment(p) -> bool:
    if not isinstance(p, dict) or p.get('kind') not in KINDS or p.get('status') not in STATUSES:
        return False
    if not all(isinstance(p.get(k), str) and p[k] for k in ('id', 'ref', 'payer', 'last4', 'mandate')):
        return False
    if any(type(p.get(k)) is not int or p[k] < 0 for k in ('amount', 'payee_net', 'platform_fee', 'created', 'updated')):
        return False
    if p['amount'] <= 0 or p['payee_net'] + p['platform_fee'] != p['amount'] or type(p.get('synced')) is not bool:
        return False
    if p['status'] in ('captured', 'refunded'):
        return isinstance(p.get('payee'), str) and bool(p['payee'])
    return p.get('payee') is None


def valid_payout(o) -> bool:
    return isinstance(o, dict) and all(isinstance(o.get(k), str) and o[k] for k in ('id', 'account', 'last4')) \
        and type(o.get('amount')) is int and o['amount'] >= MIN_PAYOUT and o.get('status') in ('paid', 'failed') \
        and type(o.get('created')) is int and type(o.get('synced')) is bool


# ---------------------------------------------------------------------------- double-entry ledger
CLEARING, REVENUE = 'bank:clearing', 'revenue:commission'


def payable(account: str) -> str:
    return 'payable:' + account


def entries(payments, payouts=()) -> list[tuple]:
    """Expand records into double-entry lines (transaction id, account, debit, credit), from the
    platform's books: a capture is owed by the bank (debit clearing) and owed to the payee and the
    platform (credits); a payout settles the payee (debit payable, credit clearing). A refund
    reverses its capture. Authorised, voided and declined payments move nothing."""
    lines = []
    for p in payments:
        if p['status'] in ('captured', 'refunded'):
            lines += [(p['id'], CLEARING, p['amount'], 0), (p['id'], payable(p['payee']), 0, p['payee_net']),
                      (p['id'], REVENUE, 0, p['platform_fee'])]
        if p['status'] == 'refunded':
            lines += [(p['id'] + ':refund', CLEARING, 0, p['amount']),
                      (p['id'] + ':refund', payable(p['payee']), p['payee_net'], 0),
                      (p['id'] + ':refund', REVENUE, p['platform_fee'], 0)]
    for o in payouts:
        if o['status'] == 'paid':
            lines += [(o['id'], payable(o['account']), o['amount'], 0), (o['id'], CLEARING, 0, o['amount'])]
    return lines


def balanced(lines) -> bool:
    """Every transaction's debits equal its credits (the ledger invariant)."""
    totals = {}
    for txn, _account, debit, credit in lines:
        if debit < 0 or credit < 0 or (debit > 0) == (credit > 0):
            return False
        totals[txn] = totals.get(txn, 0) + debit - credit
    return all(v == 0 for v in totals.values())


def balance(lines, account: str) -> int:
    """Credit balance of one ledger account, in cents."""
    return sum(credit - debit for _txn, name, debit, credit in lines if name == account)


def wallet(account: str, payments, payouts=()) -> dict:
    """What a driver or seller has earned, been paid and can withdraw."""
    lines = entries(payments, payouts)
    earned = sum(p['payee_net'] for p in payments if p['status'] == 'captured' and p['payee'] == account)
    paid = sum(o['amount'] for o in payouts if o['status'] == 'paid' and o['account'] == account)
    return dict(balance=balance(lines, payable(account)), earned=earned, paid_out=paid)
