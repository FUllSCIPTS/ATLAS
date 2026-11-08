#!/usr/bin/env python3
"""Crypto lab B - MACs, key derivation and randomness (experiments 8-10).

Rebuilds SHA-256, HMAC and PBKDF2 from first principles and checks them against hashlib and against the
ATLAS Go app's real password hashing (android-app/atlas_go/accounts.py). Standard library only.

    python3 security_lab/crypto_b_mac_kdf_random.py          # every experiment in this lab
    python3 security_lab/crypto_b_mac_kdf_random.py --list
    python3 security_lab/crypto_b_mac_kdf_random.py -e 8

Experiments
   8. Length extension: why sha256(secret + message) is not a MAC, and how HMAC fixes it
   9. HMAC and PBKDF2 built by hand, reproducing the app's stored password hash
  10. Randomness: predicting Python's random module, and why the app uses secrets

All five crypto labs and the study paths: python3 security_lab/crypto_lab.py --list
See docs/CRYPTOGRAPHY.md for the full teaching guide.
"""
from __future__ import annotations

import hashlib
import hmac
import math
import random
import re
import secrets
import struct
import sys
import time

from crypto_common import ROOT, experiment, main, note, show

sys.path.insert(0, str(ROOT / 'android-app'))
from atlas_go import accounts as acc  # noqa: E402


# --------------------------------------------------------------------------- SHA-256 in pure Python
def _primes(count):
    found, n = [], 2
    while len(found) < count:
        if all(n % p for p in found if p * p <= n):
            found.append(n)
        n += 1
    return found


def _icbrt(n):
    x = 1 << ((n.bit_length() + 2) // 3)
    while True:
        y = (2 * x + n // (x * x)) // 3
        if y >= x:
            return x
        x = y


# "Nothing up my sleeve" constants: fractional parts of square and cube roots of the first primes.
H0 = [math.isqrt(p << 64) & 0xFFFFFFFF for p in _primes(8)]
K = [_icbrt(p << 96) & 0xFFFFFFFF for p in _primes(64)]


def _rotr(x, n):
    return ((x >> n) | (x << (32 - n))) & 0xFFFFFFFF


def _compress(state, block):
    w = list(struct.unpack('>16L', block))
    for i in range(16, 64):
        s0 = _rotr(w[i - 15], 7) ^ _rotr(w[i - 15], 18) ^ (w[i - 15] >> 3)
        s1 = _rotr(w[i - 2], 17) ^ _rotr(w[i - 2], 19) ^ (w[i - 2] >> 10)
        w.append((w[i - 16] + s0 + w[i - 7] + s1) & 0xFFFFFFFF)
    a, b, c, d, e, f, g, h = state
    for i in range(64):
        t1 = (h + (_rotr(e, 6) ^ _rotr(e, 11) ^ _rotr(e, 25)) + ((e & f) ^ (~e & g)) + K[i] + w[i]) & 0xFFFFFFFF
        t2 = ((_rotr(a, 2) ^ _rotr(a, 13) ^ _rotr(a, 22)) + ((a & b) ^ (a & c) ^ (b & c))) & 0xFFFFFFFF
        a, b, c, d, e, f, g, h = (t1 + t2) & 0xFFFFFFFF, a, b, c, (d + t1) & 0xFFFFFFFF, e, f, g
    return [(x + y) & 0xFFFFFFFF for x, y in zip(state, (a, b, c, d, e, f, g, h))]


def md_padding(length: int) -> bytes:
    """SHA-256 padding for a message of `length` bytes: 0x80, zeros, then the bit length (64-bit)."""
    return b'\x80' + b'\x00' * ((55 - length) % 64) + struct.pack('>Q', length * 8)


def sha256_py(message: bytes, state=None, prior: int = 0) -> bytes:
    """SHA-256 written out. `state`/`prior` let you resume from a known digest (length extension)."""
    state = list(state or H0)
    data = message + md_padding(prior + len(message))
    for i in range(0, len(data), 64):
        state = _compress(state, data[i:i + 64])
    return struct.pack('>8L', *state)


# --------------------------------------------------------------------------- 8
@experiment(8, 'B', 'Length extension: sha256(secret + message) is not a MAC')
def exp_length_extension(_):
    show('hand-written SHA-256 == hashlib', sha256_py(b'ATLAS') == hashlib.sha256(b'ATLAS').digest())
    show('first round constant K[0]', f'{K[0]:08x}  (cube root of 2, fractional part)')
    secret = secrets.token_bytes(16)                       # known only to the server
    message = b'ride=R-1001&fare=1250'
    naive_tag = hashlib.sha256(secret + message).digest()  # a "signed receipt link" done wrong
    show('receipt the user sees', f'{message.decode()}  tag={naive_tag.hex()[:24]}...')

    extension = b'&refund=1250'                            # the attacker knows message, tag, len(secret)
    glue = md_padding(len(secret) + len(message))
    forged_message = message + glue + extension
    state = struct.unpack('>8L', naive_tag)                # the tag IS the internal state after the secret+message
    forged_tag = sha256_py(extension, state, prior=len(secret) + len(message) + len(glue))
    server_accepts = hmac.compare_digest(hashlib.sha256(secret + forged_message).digest(), forged_tag)
    show('forged message (bytes)', repr(forged_message)[:72] + '...')
    show('server checks sha256(secret+msg)', f'accepts the forged tag: {server_accepts}')
    good_tag = hmac.new(secret, message, hashlib.sha256).digest()
    forged = hmac.new(secret, forged_message, hashlib.sha256).digest()
    show('same attack against HMAC-SHA256', f'accepts: {hmac.compare_digest(good_tag, forged)}')
    note('SHA-256 publishes its whole internal state as the digest, so anyone can keep hashing from it.')
    note('The attacker never learned the secret. HMAC hashes twice with the key (inner and outer),')
    note('so the outer hash hides the inner state. ATLAS uses HMAC inside PBKDF2 (experiment 9).')


# --------------------------------------------------------------------------- 9
def hmac_sha256(key: bytes, message: bytes) -> bytes:
    if len(key) > 64:
        key = hashlib.sha256(key).digest()
    key = key.ljust(64, b'\x00')
    inner = hashlib.sha256(bytes(k ^ 0x36 for k in key) + message).digest()
    return hashlib.sha256(bytes(k ^ 0x5C for k in key) + inner).digest()


def pbkdf2_sha256(password: bytes, salt: bytes, iterations: int) -> bytes:
    """One 32-byte block of PBKDF2-HMAC-SHA256 (RFC 8018): U1 = HMAC(P, S || INT(1)), Ui = HMAC(P, Ui-1)."""
    inner = hashlib.sha256()
    outer = hashlib.sha256()
    key = password.ljust(64, b'\x00') if len(password) <= 64 else hashlib.sha256(password).digest().ljust(64, b'\x00')
    inner.update(bytes(k ^ 0x36 for k in key))             # pre-keyed hash objects: same maths, fewer bytes hashed
    outer.update(bytes(k ^ 0x5C for k in key))

    def prf(data):
        i, o = inner.copy(), outer.copy()
        i.update(data)
        o.update(i.digest())
        return o.digest()

    u = prf(salt + b'\x00\x00\x00\x01')
    result = int.from_bytes(u, 'big')
    for _ in range(iterations - 1):
        u = prf(u)
        result ^= int.from_bytes(u, 'big')
    return result.to_bytes(32, 'big')


@experiment(9, 'B', 'HMAC and PBKDF2 by hand, reproducing the app')
def exp_pbkdf2(_):
    key, msg = b'atlas-internal-token', b'GET /trips'
    show('hand-written HMAC == hmac module', hmac_sha256(key, msg) == hmac.new(key, msg, hashlib.sha256).digest())
    record = acc.hash_password('cork2026')                 # the app's real function
    show('accounts.hash_password(cork2026)', f'salt {record["salt"]}  iterations {record["iterations"]:,}')
    start = time.perf_counter()
    mine = pbkdf2_sha256(b'cork2026', bytes.fromhex(record['salt']), record['iterations'])
    took = time.perf_counter() - start
    show('stored hash', record['hash'])
    show('hand-written PBKDF2', f'{mine.hex()}')
    show('identical', f'{mine.hex() == record["hash"]}   ({took:.2f} s in pure Python)')
    show('first 3 rounds U1, U2, U3', ' '.join(pbkdf2_sha256(b'cork2026', bytes.fromhex(record['salt']), n).hex()[:8]
                                              for n in (1, 2, 3)))
    note('PBKDF2 = HMAC applied 200,000 times, XOR-ing every round together. Nothing in the stored record')
    note('is secret except the password; the work factor is the defence. Memory-hard KDFs (scrypt,')
    note('Argon2id) also make GPUs pay in RAM - the security lab, experiment 4, times the cost.')


# --------------------------------------------------------------------------- 10
def untemper(y: int) -> int:
    """Invert the Mersenne Twister output tempering to recover one internal state word."""
    y ^= y >> 18
    y ^= (y << 15) & 0xEFC60000
    t = y
    for _ in range(5):
        t = y ^ ((t << 7) & 0x9D2C5680)
    y = t & 0xFFFFFFFF
    t = y
    for _ in range(3):
        t = y ^ (t >> 11)
    return t & 0xFFFFFFFF


@experiment(10, 'B', 'Randomness: predicting random, trusting secrets')
def exp_randomness(_):
    server = random.Random()                               # a server that (wrongly) uses random for tokens
    observed = [server.getrandbits(32) for _ in range(624)]  # e.g. 624 public "order numbers"
    clone = random.Random()
    clone.setstate((3, tuple(untemper(v) for v in observed) + (624,), None))
    predicted = clone.randbytes(16).hex()
    actual = server.randbytes(16).hex()
    show('observed outputs', '624 x 32-bit values (2.5 KB)')
    show('predicted next 16-byte "salt"', predicted)
    show('server actually produced', actual)
    show('prediction correct', predicted == actual)
    show('secrets.token_bytes(16)', f'{secrets.token_bytes(16).hex()}  (os.urandom: unpredictable)')
    acc_src = (ROOT / 'android-app' / 'atlas_go' / 'accounts.py').read_text()
    store_src = (ROOT / 'android-app' / 'atlas_go' / 'store.py').read_text()
    show('accounts.py draws salts with', ', '.join(sorted(set(re.findall(r'secrets\.\w+', acc_src)))) or 'n/a')
    show('store.py record ids', ', '.join(sorted(set(re.findall(r"f'[A-Z]-\{time_ns\(\)\}'", store_src)))) or 'n/a')
    note('random is a Mersenne Twister: fast and fine for simulations, but 624 outputs reveal its whole')
    note('state. Salts, tokens and keys must come from secrets / os.urandom - as accounts.py does.')
    note('Account, ride and order ids are <letter>-<nanosecond clock>: guessable. That is fine for an')
    note('identifier, never for a secret. Rule: anything that grants access must be unguessable, not just')
    note('unique.')


if __name__ == '__main__':
    main(group='B', description=__doc__.split('\n')[0])
