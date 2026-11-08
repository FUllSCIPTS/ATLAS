#!/usr/bin/env python3
"""Crypto lab E - post-quantum cryptography (experiments 18-20).

ATLAS contains no post-quantum cryptography yet (docs/CRYPTOGRAPHY.md section 6). These experiments
build the two ideas behind the NIST standards from scratch - hash-based signatures (SLH-DSA, FIPS 205)
and lattice key encapsulation (ML-KEM, FIPS 203) - at toy sizes, and show how a hybrid key exchange
would protect ATLAS's long-lived location data. Standard library only. Never use these toys for real.

    python3 security_lab/crypto_e_post_quantum.py            # every experiment in this lab
    python3 security_lab/crypto_e_post_quantum.py --list
    python3 security_lab/crypto_e_post_quantum.py -e 19

Experiments
  18. Lamport one-time signatures: quantum-safe signing from SHA-256 alone
  19. Why "one-time": forging a release signature after the key is reused
  20. Lattices and hybrids: a toy LWE key encapsulation combined with Diffie-Hellman

All five crypto labs and the study paths: python3 security_lab/crypto_lab.py --list
See docs/CRYPTOGRAPHY.md for the full teaching guide.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
import time

from crypto_common import experiment, main, note, random_prime, show


# --------------------------------------------------------------------------- Lamport
def lamport_keygen():
    sk = [[secrets.token_bytes(32), secrets.token_bytes(32)] for _ in range(256)]
    pk = [[hashlib.sha256(a).digest(), hashlib.sha256(b).digest()] for a, b in sk]
    return sk, pk


def bits_of(message: bytes) -> list[int]:
    digest = int.from_bytes(hashlib.sha256(message).digest(), 'big')
    return [(digest >> (255 - i)) & 1 for i in range(256)]


def lamport_sign(sk, message: bytes) -> list[bytes]:
    return [sk[i][b] for i, b in enumerate(bits_of(message))]


def lamport_verify(pk, message: bytes, signature: list[bytes]) -> bool:
    return all(hashlib.sha256(s).digest() == pk[i][b] for i, (b, s) in enumerate(zip(bits_of(message), signature)))


@experiment(18, 'E', 'Lamport one-time signatures from SHA-256 alone')
def exp_lamport(_):
    start = time.perf_counter()
    sk, pk = lamport_keygen()
    message = b'atlas-go-1.2.0.apk sha256=737c41ec935e4a87d849a04b1434fbe66fa47bdcb9420387e2a94f58400813cb'
    signature = lamport_sign(sk, message)
    took = time.perf_counter() - start
    bits = bits_of(message)
    show('private key', '256 pairs of random 32-byte values')
    show('public key', '256 pairs of their SHA-256 hashes')
    show('message hash bits 0-15', ''.join(map(str, bits[:16])) + '...')
    show('signature', 'for bit i, reveal secret half [i][bit]')
    show('verify original', lamport_verify(pk, message, signature))
    show('verify 1.2.1 with that signature', lamport_verify(pk, message.replace(b'1.2.0', b'1.2.1'), signature))
    show('keygen + sign time', f'{took * 1000:.1f} ms')
    print(f'\n  {"scheme":<28} {"public key":>12} {"signature":>11}  breaks under Shor?')
    for name, public, sig, shor in (('RSA-4096 (ATLAS upload key)', 512, 512, 'yes'),
                                    ('ECDSA P-256', 64, 64, 'yes'),
                                    ('Lamport (this experiment)', 256 * 2 * 32, 256 * 32, 'no'),
                                    ('ML-DSA-65 (FIPS 204)', 1952, 3309, 'no'),
                                    ('SLH-DSA-SHA2-128s (FIPS 205)', 32, 7856, 'no')):
        print(f'  {name:<28} {public:>10,} B {sig:>9,} B  {shor}')
    note('Security rests only on SHA-256 preimage resistance, which Grover weakens to ~2^128 (exp. 3) -')
    note('the same assumption SLH-DSA makes. The price is size, and the key may sign only ONE message.')


@experiment(19, 'E', 'Why "one-time": forging after key reuse')
def exp_lamport_reuse(_):
    sk, pk = lamport_keygen()
    signed, revealed = [], [set() for _ in range(256)]
    print(f'  {"messages signed":>15}  {"positions with both halves known":>33}  {"forgery cost":>14}')
    for count in range(1, 9):
        message = f'atlas-go-1.2.{count}.apk'.encode()
        signed.append((message, lamport_sign(sk, message)))
        for i, b in enumerate(bits_of(message)):
            revealed[i].add(b)
        both = sum(len(r) == 2 for r in revealed)
        print(f'  {count:>15}  {both:>33}  {"2^" + str(256 - both):>14} tries')
    secret_of = {}
    for message, signature in signed:
        for i, (b, s) in enumerate(zip(bits_of(message), signature)):
            secret_of[(i, b)] = s
    start, tries = time.perf_counter(), 0
    while True:
        tries += 1
        candidate = f'atlas-go-9.9.9-backdoor-{tries}.apk'.encode()
        if all((i, b) in secret_of for i, b in enumerate(bits_of(candidate))):
            break
    forged = [secret_of[(i, b)] for i, b in enumerate(bits_of(candidate))]
    show('forged message', candidate.decode())
    show('tries / time', f'{tries:,} / {time.perf_counter() - start:.2f} s')
    show('verifies under the public key', lamport_verify(pk, candidate, forged))
    note('Each signature reveals half the private key; every reuse reveals more until any message can be')
    note('signed. XMSS and LMS (stateful) keep a counter so no one-time key is reused; SLH-DSA (stateless)')
    note('picks a few-time key pseudo-randomly from a huge hash tree. A signing service that loses its')
    note('counter - a restored backup, a cloned VM - is exactly how stateful schemes fail in practice.')


# --------------------------------------------------------------------------- toy LWE
Q, N, M = 3329, 64, 128          # q is ML-KEM's modulus; N and M are tiny for speed


def small():
    return secrets.randbelow(5) - 2                        # noise in {-2..2}


def lwe_keygen():
    a = [[secrets.randbelow(Q) for _ in range(N)] for _ in range(M)]
    s = [secrets.randbelow(Q) for _ in range(N)]
    e = [small() for _ in range(M)]
    b = [(sum(x * y for x, y in zip(row, s)) + err) % Q for row, err in zip(a, e)]
    return (a, b), s


def lwe_encrypt_bit(public, bit):
    a, b = public
    rows = [i for i in range(M) if secrets.randbelow(2)]   # a random subset of the public equations
    u = [sum(a[i][j] for i in rows) % Q for j in range(N)]
    v = (sum(b[i] for i in rows) + bit * (Q // 2)) % Q
    return u, v


def lwe_decrypt_bit(s, ciphertext):
    u, v = ciphertext
    d = (v - sum(x * y for x, y in zip(u, s))) % Q        # = bit*q/2 + small noise
    return 1 if Q // 4 < d < 3 * Q // 4 else 0


def solve_mod_q(rows, rhs):
    """Gaussian elimination mod the prime Q on N equations: works only if the equations are exact."""
    m = [row[:] + [r] for row, r in zip(rows[:N], rhs[:N])]
    for col in range(N):
        pivot = next(r for r in range(col, N) if m[r][col])
        m[col], m[pivot] = m[pivot], m[col]
        inv = pow(m[col][col], -1, Q)
        m[col] = [x * inv % Q for x in m[col]]
        for r in range(N):
            if r != col and m[r][col]:
                f = m[r][col]
                m[r] = [(x - f * y) % Q for x, y in zip(m[r], m[col])]
    return [row[-1] for row in m]


def hkdf_sha256(ikm: bytes, info: bytes, length: int = 32) -> bytes:
    prk = hmac.new(b'\x00' * 32, ikm, hashlib.sha256).digest()             # extract
    return hmac.new(prk, info + b'\x01', hashlib.sha256).digest()[:length]  # expand (one block)


@experiment(20, 'E', 'Lattices and hybrids: toy LWE KEM plus Diffie-Hellman')
def exp_lwe_hybrid(_):
    (a, b), s = lwe_keygen()
    show('LWE public key', f'A: {M}x{N} numbers mod {Q}, b = A*s + e with e in -2..2')
    secret_s = solve_mod_q(a, [(sum(x * y for x, y in zip(row, s))) % Q for row in a])
    show('if e were 0: solve A*s = b', f'Gaussian elimination recovers s: {secret_s == s}')
    guess = solve_mod_q(a, b)
    show('with the noise e: same solver', f'recovers s: {guess == s}  (the noise makes it the LWE problem)')
    start = time.perf_counter()
    key = secrets.token_bytes(16)
    key_bits = [(key[i // 8] >> (7 - i % 8)) & 1 for i in range(128)]
    ciphertext = [lwe_encrypt_bit((a, b), bit) for bit in key_bits]
    recovered_bits = [lwe_decrypt_bit(s, c) for c in ciphertext]
    recovered = bytes(sum(bit << (7 - j) for j, bit in enumerate(recovered_bits[i:i + 8])) for i in range(0, 128, 8))
    show('encapsulate + decapsulate 128 bits', f'same key: {recovered == key}  ({time.perf_counter() - start:.2f} s)')
    show('noise budget', f'worst case |r.e| <= {M * 2}, decryption fails only past q/4 = {Q // 4}')

    p = random_prime(512)                                  # toy finite-field Diffie-Hellman
    g = 2
    x, y = secrets.randbelow(p - 2) + 1, secrets.randbelow(p - 2) + 1
    gx, gy = pow(g, x, p), pow(g, y, p)
    dh_phone, dh_server = pow(gy, x, p), pow(gx, y, p)
    show('toy Diffie-Hellman (512-bit p)', f'phone and server agree: {dh_phone == dh_server}')
    transcript = b'ATLAS-hybrid-v1|' + gx.to_bytes(64, 'big') + gy.to_bytes(64, 'big')
    session = hkdf_sha256(dh_phone.to_bytes(64, 'big') + key, transcript)
    show('hybrid key HKDF(dh || kem)', session.hex()[:32] + '...')
    future = hkdf_sha256(dh_phone.to_bytes(64, 'big') + secrets.token_bytes(16), transcript)
    show('attacker who breaks only DH', f'derives the session key: {future == session}')
    note('Shor breaks DH and elliptic curves; no quantum algorithm is known to solve LWE. A hybrid feeds')
    note('both secrets through a KDF, so the session survives if either holds. That matters for ATLAS:')
    note('trip and location data recorded today could be decrypted later ("harvest now, decrypt later").')
    note('Real ML-KEM-768 uses module lattices over polynomials: 1,184-byte public key, 1,088-byte')
    note(f'ciphertext. This toy sends {len(ciphertext) * (N + 1) * 12 // 8:,} bytes for the same 128 bits.')


if __name__ == '__main__':
    main(group='E', description=__doc__.split('\n')[0])
