#!/usr/bin/env python3
"""Cryptography lab: hashes, checksums, certificates, signatures and a post-quantum signature.

Standard library only. Uses ATLAS's real release records and upload certificate.

    python3 security_lab/crypto_lab.py                  # run every section
    python3 security_lab/crypto_lab.py --verify FILE    # check a downloaded APK/AAB against SHA256SUMS

Sections
  1. SHA-256 and the avalanche effect
  2. Checksum vs cryptographic hash (the prototype's state checksum)
  3. Verifying a release with SHA256SUMS
  4. The upload certificate and its pinned SHA-256 fingerprint
  5. Hash-then-sign with textbook RSA (toy, for learning only)
  6. Post-quantum: a Lamport one-time signature built only from SHA-256
See docs/CRYPTOGRAPHY.md for the full teaching guide.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import secrets
import ssl
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASES = ROOT / 'android-app' / 'releases'


def heading(text: str) -> None:
    print('\n' + text + '\n' + '-' * len(text))


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def bit_difference(a: str, b: str) -> int:
    return bin(int(a, 16) ^ int(b, 16)).count('1')


# ---------------------------------------------------------------- 1
def section_hash() -> None:
    heading('1. SHA-256 and the avalanche effect')
    a, b = sha256(b'ATLAS ride R-1001 fare 1250'), sha256(b'ATLAS ride R-1001 fare 1251')
    print(f"fare 1250 -> {a}")
    print(f"fare 1251 -> {b}")
    print(f"one character changed, {bit_difference(a, b)} of 256 output bits flipped (about half is ideal)")
    print('fixed 32-byte output, one-way, and no known way to find two inputs with the same hash')


# ---------------------------------------------------------------- 2
def section_checksum() -> None:
    heading("2. Checksum vs cryptographic hash (prototype's PaymentModule.checksum)")

    def checksum(state):  # same shape as prototype/module_server.py
        return (state['count'], state['total'], len(state['seen']))

    honest = {'seen': ['p1', 'p2', 'p3'], 'total': 3000, 'count': 3}
    altered = {'seen': ['p1', 'p2', 'pX'], 'total': 3000, 'count': 3}   # a payment id swapped
    print(f"checksum(honest)  = {checksum(honest)}")
    print(f"checksum(altered) = {checksum(altered)}   <- identical: detects accidental loss, not tampering")
    h1 = sha256(json.dumps(honest, sort_keys=True).encode())
    h2 = sha256(json.dumps(altered, sort_keys=True).encode())
    print(f"sha256(honest)    = {h1[:32]}...")
    print(f"sha256(altered)   = {h2[:32]}...   <- different")
    print('ATLAS uses the cheap checksum after recovery (crash class C3 in run_recovery_mc.py), where the')
    print('threat is a lost update, not an attacker. Against an attacker you need a hash or a MAC.')


# ---------------------------------------------------------------- 3
def parse_sums(path: Path) -> dict[str, str]:
    rows = {}
    for line in path.read_text().splitlines():
        if line.strip():
            digest, name = line.split(maxsplit=1)
            rows[name.lstrip('*')] = digest
    return rows


def section_sums(verify: Path | None) -> None:
    heading('3. Verifying a release with SHA256SUMS')
    sums = parse_sums(RELEASES / '1.2.0' / 'SHA256SUMS')
    for name, digest in sums.items():
        print(f"published  {digest}  {name}")
    if verify:
        actual = sha256(verify.read_bytes())
        match = [n for n, d in sums.items() if hmac.compare_digest(d, actual)]
        print(f"your file  {actual}  {verify.name}")
        print('MATCH: ' + match[0] if match else 'NO MATCH: corrupted, tampered, or a different build')
    else:
        print('run with --verify path/to/atlas-go-1.2.0.apk to check a download (same as sha256sum -c)')
    print('CI does the same for its own tools: atlas-android.yml pins bundletool.jar to SHA-256 a099cfa1...')


# ---------------------------------------------------------------- 4
def section_certificate() -> None:
    heading('4. The upload certificate and its pinned fingerprint')
    pem = (RELEASES / 'upload-certificate.pem').read_text()
    der = ssl.PEM_cert_to_DER_cert(pem)
    fingerprint = sha256(der)
    pinned = json.loads((RELEASES / 'SIGNED_VALIDATION.json').read_text())['upload_certificate_sha256']
    try:
        info = ssl._ssl._test_decode_cert(str(RELEASES / 'upload-certificate.pem'))  # CPython helper
        subject = ', '.join('='.join(x) for rdn in info['subject'] for x in rdn)
        print(f"subject     {subject}")
        print(f"valid       {info['notBefore']}  ->  {info['notAfter']}")
    except Exception:  # noqa: BLE001 - helper is CPython-specific
        pass
    print(f"DER bytes   {len(der)}   (RSA-4096 public key, sha384WithRSAEncryption, self-signed)")
    print(f"SHA-256     {fingerprint}")
    print(f"pinned      {pinned}")
    print('MATCH: CI accepts this signer' if hmac.compare_digest(fingerprint, pinned) else 'MISMATCH: CI would fail')
    print('ci-sign-bundle.py and publish-signed-android.yml refuse any bundle whose certificate hash differs.')


# ---------------------------------------------------------------- 5
def is_probable_prime(n: int, rounds: int = 32) -> bool:
    if n < 2:
        return False
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29):
        if n % p == 0:
            return n == p
    d, s = n - 1, 0
    while d % 2 == 0:
        d, s = d // 2, s + 1
    for _ in range(rounds):
        x = pow(secrets.randbelow(n - 3) + 2, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


def random_prime(bits: int) -> int:
    while True:
        candidate = secrets.randbits(bits) | (3 << (bits - 2)) | 1   # top two bits set: n has 2*bits bits
        if is_probable_prime(candidate):
            return candidate


def section_rsa() -> None:
    heading('5. Hash-then-sign with textbook RSA (toy: no padding, never use in production)')
    e = 65537
    while True:
        p, q = random_prime(512), random_prime(512)
        phi = (p - 1) * (q - 1)
        if p != q and phi % e:
            break
    n, d = p * q, pow(e, -1, (p - 1) * (q - 1))
    release = b'atlas-go-1.2.0.apk contents...'
    h = int.from_bytes(hashlib.sha256(release).digest(), 'big')
    signature = pow(h, d, n)                       # sign: only the private key d can do this
    print(f"n (public)  {n.bit_length()} bits, e = {e}")
    print(f"signature   {hex(signature)[:42]}...")
    ok = pow(signature, e, n) == h                 # verify: anyone with (n, e)
    tampered = int.from_bytes(hashlib.sha256(release + b'!').digest(), 'big')
    print(f"verify original  -> {ok}")
    print(f"verify tampered  -> {pow(signature, e, n) == tampered}")
    print('ATLAS signs with SHA256withRSA (jarsigner, PKCS#1 v1.5 padding) and APK Signature Scheme v2/v3.')


# ---------------------------------------------------------------- 6
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


def section_pqc() -> None:
    heading('6. Post-quantum: Lamport one-time signature (only SHA-256, no number theory)')
    sk, pk = lamport_keygen()
    message = b'atlas-go-1.2.0.apk'
    signature = lamport_sign(sk, message)
    print(f"public key  {256 * 2 * 32:,} bytes   signature {256 * 32:,} bytes   (RSA-4096 signature: 512 bytes)")
    print(f"verify original -> {lamport_verify(pk, message, signature)}")
    print(f"verify tampered -> {lamport_verify(pk, b'atlas-go-1.2.1.apk', signature)}")
    second = lamport_sign(sk, b'atlas-go-1.2.0-patched.apk')   # key reuse
    revealed = sum(1 for a, b in zip(signature, second) if a != b)
    print(f"signing a second message with the same key reveals {revealed} more secret halves -> forgeries become")
    print('possible. That is why it is "one-time"; SLH-DSA (FIPS 205) builds many-time signatures from this idea.')
    print("Shor's algorithm breaks RSA and elliptic curves; it gives no shortcut against SHA-256 preimages.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--verify', type=Path, help='a downloaded file to check against SHA256SUMS')
    args = parser.parse_args()
    section_hash()
    section_checksum()
    section_sums(args.verify)
    section_certificate()
    section_rsa()
    section_pqc()


if __name__ == '__main__':
    main()
