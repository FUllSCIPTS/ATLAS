"""Account rules for passengers, drivers and food sellers: validation and password hashing.

Pure Python. Passwords are never stored: each account keeps a random 16-byte salt and a
PBKDF2-HMAC-SHA256 hash. Driver licences, vehicle registrations and food-business numbers
are format-checked only; they are self-declared and not verified with any authority.
"""
from __future__ import annotations

import hashlib
import hmac
import re
import secrets

ROLES = ('passenger', 'driver', 'seller')
ROLE_TITLES = {'passenger': 'Passenger', 'driver': 'Driver', 'seller': 'Food seller'}
PBKDF2_ITERATIONS = 200_000
MAX_FAILED_LOGINS = 5
LOCKOUT_SECONDS = 60

EMAIL = re.compile(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$')
# Irish registration: 2-3 digit year, county code, sequence (e.g. 241-C-1234, 12-D-5678)
PLATE = re.compile(r'^\d{2,3}-[A-Z]{1,2}-\d{1,6}$')
LICENCE = re.compile(r'^[A-Z0-9]{5,12}$')
BUSINESS = re.compile(r'^[A-Z0-9-]{4,20}$')


def hash_password(password: str, salt: bytes | None = None, iterations: int = PBKDF2_ITERATIONS) -> dict:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
    return dict(salt=salt.hex(), hash=digest.hex(), iterations=iterations)


def verify_password(password: str, record: dict) -> bool:
    try:
        salt = bytes.fromhex(record['salt'])
        expected = bytes.fromhex(record['hash'])
        iterations = int(record['iterations'])
    except (KeyError, ValueError, TypeError):
        return False
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
    return hmac.compare_digest(digest, expected)


def clean_name(value: str, field: str = 'Name', low: int = 2, high: int = 40) -> str:
    value = ' '.join((value or '').split())
    if not low <= len(value) <= high:
        raise ValueError(f'{field} must be {low} to {high} characters.')
    if any(ord(ch) < 32 for ch in value):
        raise ValueError(f'{field} contains unsupported characters.')
    return value


def clean_email(value: str) -> str:
    value = (value or '').strip().lower()
    if len(value) > 80 or not EMAIL.match(value):
        raise ValueError('Enter a valid email address, for example name@example.ie.')
    return value


def clean_phone(value: str) -> str:
    """Normalise to E.164. Irish numbers may be entered as 08x xxx xxxx."""
    raw = re.sub(r'[\s().-]', '', value or '')
    if raw.startswith('00'):
        raw = '+' + raw[2:]
    if raw.startswith('0') and not raw.startswith('00'):
        raw = '+353' + raw[1:]
    if not re.fullmatch(r'\+[1-9]\d{7,14}', raw):
        raise ValueError('Enter a valid phone number, for example 087 123 4567 or +353 87 123 4567.')
    return raw


def check_password(value: str) -> str:
    value = value or ''
    if len(value) < 8 or len(value) > 128:
        raise ValueError('Password must be 8 to 128 characters.')
    if not re.search(r'[A-Za-z]', value) or not re.search(r'\d', value):
        raise ValueError('Password needs at least one letter and one number.')
    return value


def clean_plate(value: str) -> str:
    value = re.sub(r'\s+', '-', (value or '').strip().upper())
    if not PLATE.match(value):
        raise ValueError('Enter an Irish registration such as 241-C-1234.')
    return value


def clean_licence(value: str) -> str:
    value = re.sub(r'\s+', '', (value or '').upper())
    if not LICENCE.match(value):
        raise ValueError('SPSV driver licence number: 5 to 12 letters or digits.')
    return value


def clean_business(value: str) -> str:
    value = re.sub(r'\s+', '', (value or '').upper())
    if not BUSINESS.match(value):
        raise ValueError('Food business registration: 4 to 20 letters, digits or dashes.')
    return value


def parse_int(value, field: str, low: int, high: int) -> int:
    try:
        number = int(str(value).strip())
    except (TypeError, ValueError):
        raise ValueError(f'{field} must be a whole number.') from None
    if not low <= number <= high:
        raise ValueError(f'{field} must be between {low} and {high}.')
    return number


def parse_price(value: str) -> int:
    """'8.50', '€8,50' or '8' -> 850 cents, between €0.50 and €200."""
    text = (value or '').strip().replace('€', '').replace(',', '.')
    if not re.fullmatch(r'\d{1,3}(\.\d{1,2})?', text):
        raise ValueError('Price must look like 8.50.')
    euros, _, cents = text.partition('.')
    total = int(euros) * 100 + int((cents + '00')[:2])
    if not 50 <= total <= 20000:
        raise ValueError('Price must be between €0.50 and €200.00.')
    return total


def public_view(account: dict) -> dict:
    """Account fields safe to show on screen (no salt or hash)."""
    return {k: v for k, v in account.items() if k not in ('salt', 'hash', 'iterations')}
