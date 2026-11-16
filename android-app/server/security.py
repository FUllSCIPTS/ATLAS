"""Server-side secrets: password hashes, session tokens and the IBAN fingerprint."""
from __future__ import annotations

import hashlib
import hmac
import secrets

from atlas_go import accounts as acc

DEFAULT_ITERATIONS = 600_000          # OWASP's 2023 figure for PBKDF2-HMAC-SHA256; the phone uses 200,000
_DUMMY = None


def hash_password(password: str, iterations: int) -> tuple[bytes, bytes, int]:
    record = acc.hash_password(password, iterations=iterations)
    return bytes.fromhex(record['salt']), bytes.fromhex(record['hash']), iterations


def verify_password(password: str, row: dict | None, iterations: int) -> bool:
    """Constant-shape check: an unknown email still costs one PBKDF2, so response time does not
    reveal whether an account exists."""
    global _DUMMY
    if row is None:
        if _DUMMY is None or _DUMMY[2] != iterations:
            _DUMMY = hash_password(secrets.token_urlsafe(16), iterations)
        hashlib.pbkdf2_hmac('sha256', (password or '').encode('utf-8'), _DUMMY[0], iterations)
        return False
    digest = hashlib.pbkdf2_hmac('sha256', (password or '').encode('utf-8'), bytes(row['password_salt']),
                                 row['password_iterations'])
    return hmac.compare_digest(digest, bytes(row['password_hash']))


def new_token() -> tuple[str, bytes]:
    """(token for the client, SHA-256 for the database). 256 random bits need no salt or slow hash."""
    token = secrets.token_urlsafe(32)
    return token, token_hash(token)


def token_hash(token: str) -> bytes:
    return hashlib.sha256(token.encode('utf-8')).digest()


def fingerprint(pepper: bytes, iban: str) -> bytes:
    """Keyed hash of an IBAN. An IBAN has too little entropy for a plain hash to hide it; without
    the pepper (kept outside the database) the fingerprint cannot be brute-forced back."""
    return hmac.new(pepper, iban.encode('ascii'), hashlib.sha256).digest()
