"""Shared helpers for the ATLAS cryptography labs in this folder.

Every crypto_*.py lab file imports this module. It locates ATLAS's real artefacts (release checksums,
the upload certificate, the CI workflows, the prototype), keeps one registry of numbered experiments,
holds the small building blocks several labs share (toy RSA, PKCS#1 v1.5 encoding, a DER reader), and
provides the command line used by each lab file and by crypto_lab.py.

Everything here is for learning. The RSA keys are generated with Python integers and the padding is
written out by hand so you can see every byte; production code uses a vetted library instead.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import secrets
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASES = ROOT / 'android-app' / 'releases'
WORKFLOWS = ROOT / '.github' / 'workflows'
PROTOTYPE_ZIP = ROOT / 'prototype.zip'
CERTIFICATE = RELEASES / 'upload-certificate.pem'

EXPERIMENTS: dict[int, tuple[str, str, object]] = {}
OPTIONS: dict[str, object] = {'verify': None}   # set from the command line (--verify FILE)

GROUPS = {
    'A': ('Hashing and integrity', 'crypto_a_hashing'),
    'B': ('MACs, key derivation and randomness', 'crypto_b_mac_kdf_random'),
    'C': ('Certificates and PKI', 'crypto_c_pki'),
    'D': ('Digital signatures', 'crypto_d_signatures'),
    'E': ('Post-quantum cryptography', 'crypto_e_post_quantum'),
}

STUDY_PATHS = {
    'foundations': ('First lesson: hash, verify, certificate, signature', [1, 2, 4, 6, 11, 16]),
    'release-engineer': ('Verify what ATLAS ships, the way CI does', [6, 7, 11, 13, 17]),
    'attacker': ('Break the weak constructions', [3, 5, 8, 10, 15, 19]),
    'pki': ('Certificates from bytes to trust decisions', [11, 12, 13, 14]),
    'post-quantum': ('What a quantum computer breaks, and what replaces it', [3, 18, 19, 20]),
    'full': ('Every experiment in order', list(range(1, 21))),
}


# --------------------------------------------------------------------------- output helpers
def experiment(number: int, group: str, title: str):
    def register(fn):
        EXPERIMENTS[number] = (group, title, fn)
        return fn
    return register


def heading(number: int, title: str) -> None:
    print('\n' + '=' * 78)
    print(f'Experiment {number:>2}: {title}')
    print('=' * 78)


def note(text: str) -> None:
    print(f'  -> {text}')


def show(label: str, value) -> None:
    print(f'  {label:<34} {value}')


@contextmanager
def workspace():
    with tempfile.TemporaryDirectory(prefix='atlas-crypto-') as folder:
        yield Path(folder)


# --------------------------------------------------------------------------- hashing helpers
def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def bit_difference(a: bytes, b: bytes) -> int:
    return bin(int.from_bytes(a, 'big') ^ int.from_bytes(b, 'big')).count('1')


def parse_sums(path: Path) -> dict[str, str]:
    """Read a sha256sum-format file: '<64 hex>  <name>' per line ('*name' marks binary mode)."""
    rows = {}
    for line in path.read_text().splitlines():
        if line.strip():
            digest, name = line.split(maxsplit=1)
            rows[name.lstrip('*')] = digest.lower()
    return rows


# --------------------------------------------------------------------------- toy RSA
def is_probable_prime(n: int, rounds: int = 32) -> bool:
    """Miller-Rabin primality test."""
    if n < 2:
        return False
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
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
        candidate = secrets.randbits(bits) | (3 << (bits - 2)) | 1   # top two bits set: p*q has 2*bits bits
        if is_probable_prime(candidate):
            return candidate


def rsa_keypair(bits: int = 1024, e: int = 65537) -> dict:
    """Return {'n', 'e', 'd', 'p', 'q'} for a `bits`-bit modulus (toy: no side-channel care)."""
    while True:
        p, q = random_prime(bits // 2), random_prime(bits // 2)
        phi = (p - 1) * (q - 1)
        if p != q and phi % e:
            return dict(n=p * q, e=e, d=pow(e, -1, phi), p=p, q=q)


# DER-encoded DigestInfo prefixes from RFC 8017 section 9.2, note 1.
DIGEST_INFO = {
    'sha256': bytes.fromhex('3031300d060960864801650304020105000420'),
    'sha384': bytes.fromhex('3041300d060960864801650304020205000430'),
}


def emsa_pkcs1_v15(message: bytes, k: int, alg: str = 'sha256') -> bytes:
    """EMSA-PKCS1-v1_5 encoding: 00 01 FF..FF 00 || DigestInfo || hash(message), k bytes long."""
    t = DIGEST_INFO[alg] + hashlib.new(alg, message).digest()
    if k < len(t) + 11:
        raise ValueError('modulus too short for this hash')
    return b'\x00\x01' + b'\xff' * (k - len(t) - 3) + b'\x00' + t


def rsa_sign(message: bytes, key: dict, alg: str = 'sha256') -> int:
    k = (key['n'].bit_length() + 7) // 8
    return pow(int.from_bytes(emsa_pkcs1_v15(message, k, alg), 'big'), key['d'], key['n'])


def rsa_verify(message: bytes, signature: int, n: int, e: int, alg: str = 'sha256') -> bool:
    k = (n.bit_length() + 7) // 8
    if not 0 <= signature < n:
        return False
    recovered = pow(signature, e, n).to_bytes(k, 'big')
    return secrets.compare_digest(recovered, emsa_pkcs1_v15(message, k, alg))


# --------------------------------------------------------------------------- DER reader
def der_header(data: bytes, pos: int) -> tuple[int, int, int]:
    """Return (tag, start of contents, end of contents) for the DER element at `pos`."""
    tag, length = data[pos], data[pos + 1]
    pos += 2
    if length & 0x80:                          # long form: the low 7 bits say how many length bytes follow
        count = length & 0x7f
        length = int.from_bytes(data[pos:pos + count], 'big')
        pos += count
    return tag, pos, pos + length


def der_children(data: bytes, start: int, end: int) -> list[tuple[int, int, int, int]]:
    """List (tag, header start, contents start, contents end) for each element in data[start:end]."""
    out, pos = [], start
    while pos < end:
        tag, cstart, cend = der_header(data, pos)
        out.append((tag, pos, cstart, cend))
        pos = cend
    return out


def decode_oid(body: bytes) -> str:
    first = body[0]
    parts, value = [first // 40, first % 40], 0
    for byte in body[1:]:
        value = (value << 7) | (byte & 0x7f)
        if not byte & 0x80:
            parts.append(value)
            value = 0
    return '.'.join(map(str, parts))


# --------------------------------------------------------------------------- runner
def load_all() -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    for _, module in GROUPS.values():
        importlib.import_module(module)


def list_experiments(groups=None, paths: bool = True) -> None:
    for group, (title, module) in GROUPS.items():
        if groups and group not in groups:
            continue
        print(f'\n{group}. {title}  (security_lab/{module}.py)')
        for number, (g, name, _) in sorted(EXPERIMENTS.items()):
            if g == group:
                print(f'  {number:>2}. {name}')
    if paths:
        print('\nStudy paths (crypto_lab.py --path NAME)')
        for name, (purpose, steps) in STUDY_PATHS.items():
            print(f'  {name:<17} {purpose}: {" -> ".join(map(str, steps))}')


def run(numbers) -> None:
    for number in numbers:
        _, title, fn = EXPERIMENTS[number]
        heading(number, title)
        with workspace() as folder:
            fn(folder)


def main(argv=None, group: str | None = None, description: str = '') -> None:
    """Command line shared by every crypto lab. group='A' offers only that lab's experiments; group=None
    loads all five lab files and adds --path for the cross-category study paths."""
    if group is None:
        load_all()
    own = sorted(n for n, (g, _, _) in EXPERIMENTS.items() if group in (None, g))
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-e', '--experiment', type=int, action='append', choices=own,
                        metavar='N', help=f'run experiment N (repeatable; {own[0]}-{own[-1]})')
    parser.add_argument('-l', '--list', action='store_true', help='list experiments')
    if group in (None, 'A'):
        parser.add_argument('--verify', type=Path, metavar='FILE',
                            help='check a downloaded APK/AAB against the published SHA256SUMS (experiment 6)')
    if group is None:
        parser.add_argument('-p', '--path', choices=sorted(STUDY_PATHS), help='run a study path')
    args = parser.parse_args(argv)
    OPTIONS['verify'] = getattr(args, 'verify', None)
    if args.list:
        list_experiments([group] if group else None, paths=group is None)
        return
    if group is None and args.path:
        purpose, numbers = STUDY_PATHS[args.path]
        print(f'Study path "{args.path}": {purpose}')
    elif OPTIONS['verify'] and not args.experiment:
        numbers = [6]
    else:
        numbers = args.experiment or own
    run(numbers)
    print('\nDone. Guide: docs/CRYPTOGRAPHY.md')
