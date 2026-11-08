#!/usr/bin/env python3
"""Crypto lab A - hashing and integrity (experiments 1-7).

Uses ATLAS's real artefacts: android-app/releases/ (SHA256SUMS files, SIGNED_VALIDATION.json, the upload
certificate), .github/workflows/ (the bundletool pin) and prototype.zip (PaymentModule.checksum).
Standard library only.

    python3 security_lab/crypto_a_hashing.py                 # every experiment in this lab
    python3 security_lab/crypto_a_hashing.py --list
    python3 security_lab/crypto_a_hashing.py -e 5
    python3 security_lab/crypto_a_hashing.py --verify atlas-go-1.2.0.apk

Experiments
   1. SHA-256 basics: one-shot vs streaming, bytes vs text, and the Unicode trap
   2. The avalanche effect, measured over 2,000 single-bit changes
   3. Why 256 bits: brute-forcing preimages and collisions of a truncated hash
   4. Checksum vs hash: forging the prototype's PaymentModule.checksum
   5. CRC32 is linear: append four bytes to hit any checksum you like
   6. Verifying ATLAS releases: SHA256SUMS, signing records and a tampered download
   7. Supply-chain pinning: the bundletool hash in CI, and actions pinned by tag

All five crypto labs and the study paths: python3 security_lab/crypto_lab.py --list
See docs/CRYPTOGRAPHY.md for the full teaching guide.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import statistics
import time
import unicodedata
import zipfile
import zlib

from crypto_common import (
    CERTIFICATE, OPTIONS, PROTOTYPE_ZIP, RELEASES, WORKFLOWS, bit_difference, experiment, main, note,
    parse_sums, sha256_hex, show,
)


@experiment(1, 'A', 'SHA-256 basics: one-shot, streaming, bytes vs text')
def exp_basics(_):
    data = CERTIFICATE.read_bytes()
    one_shot = hashlib.sha256(data).hexdigest()
    stream = hashlib.sha256()
    with CERTIFICATE.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024), b''):   # how to hash a 40 MB AAB without loading it
            stream.update(chunk)
    show('file', f'{CERTIFICATE.relative_to(CERTIFICATE.parents[2])} ({len(data):,} bytes)')
    show('one-shot sha256', one_shot)
    show('streamed in 1 KiB chunks', stream.hexdigest())
    show('identical', one_shot == stream.hexdigest())
    show('digest() / hexdigest() length', f'{len(stream.digest())} bytes / {len(stream.hexdigest())} hex characters')
    show('sha256(b"") (well-known value)', sha256_hex(b''))
    nfc, nfd = unicodedata.normalize('NFC', 'Café Crêpe'), unicodedata.normalize('NFD', 'Café Crêpe')
    show('"Café Crêpe" looks the same twice', f'{nfc == nfd} as Python strings ({len(nfc)} vs {len(nfd)} code points)')
    show('sha256 of NFC UTF-8', sha256_hex(nfc.encode())[:32] + '...')
    show('sha256 of NFD UTF-8', sha256_hex(nfd.encode())[:32] + '...')
    note('Hashes work on bytes, not text. Decide the encoding and the normal form (UTF-8, NFC) before')
    note('hashing anything a user typed, such as a kitchen name, or two "equal" strings will not match.')


@experiment(2, 'A', 'The avalanche effect, measured')
def exp_avalanche(_):
    record = b'{"id":"R-1001","pickup":0,"destination":1,"fare":1250}'
    changed = record.replace(b'1250', b'1251')
    a, b = hashlib.sha256(record).digest(), hashlib.sha256(changed).digest()
    show('fare 1250', a.hex())
    show('fare 1251', b.hex())
    show('output bits that differ', f'{bit_difference(a, b)} of 256')
    flips, base = [], hashlib.sha256(record).digest()
    for i in range(2000):
        bit = i % (len(record) * 8)
        mutated = bytearray(record)
        mutated[bit // 8] ^= 1 << (bit % 8)
        flips.append(bit_difference(base, hashlib.sha256(bytes(mutated)).digest()))
    show('2,000 single-bit input changes', f'mean {statistics.mean(flips):.1f}, sd {statistics.stdev(flips):.1f}, '
         f'min {min(flips)}, max {max(flips)} output bits flipped')
    for low in range(96, 160, 8):
        count = sum(low <= f < low + 8 for f in flips)
        print(f'  {low:>3}-{low + 7:<3} {"#" * (count // 10)} {count}')
    note('Ideal is 128 with a binomial spread (sd = 8). No output bit "follows" any input bit, so a')
    note('near-miss digest tells an attacker nothing about how close their guess was.')


@experiment(3, 'A', 'Why 256 bits: preimages and collisions of a truncated hash')
def exp_bruteforce(_):
    def short(data: bytes, bits: int) -> int:
        return int.from_bytes(hashlib.sha256(data).digest(), 'big') >> (256 - bits)

    print(f'  {"bits":>4}  {"attack":<10} {"tries":>10}  {"theory":>10}  {"time":>8}')
    for bits in (16, 20):
        target = short(b'atlas-go-1.2.0.apk', bits)
        start, tries = time.perf_counter(), 0
        while True:
            tries += 1
            if short(f'forged-{tries}'.encode(), bits) == target:
                break
        print(f'  {bits:>4}  {"preimage":<10} {tries:>10,}  {2 ** bits:>10,}  {time.perf_counter() - start:>7.2f}s')
    for bits in (24, 32):
        start, seen, tries = time.perf_counter(), {}, 0
        while True:
            tries += 1
            message = f'ride-{tries}'.encode()
            value = short(message, bits)
            if value in seen:
                break
            seen[value] = message
        theory = int(1.2533 * 2 ** (bits / 2))
        print(f'  {bits:>4}  {"collision":<10} {tries:>10,}  {theory:>10,}  {time.perf_counter() - start:>7.2f}s'
              f'   {seen[value].decode()} / {message.decode()}')
    note('A preimage costs about 2^n tries, a collision only about 2^(n/2) (the birthday paradox).')
    note('Full SHA-256: collisions ~2^128 classically. Grover\'s quantum search cuts preimages to ~2^128,')
    note('still out of reach, which is why the post-quantum plan keeps SHA-256 (experiment 18).')


def load_payment_module():
    """Execute the prototype's real module_server.py from prototype.zip and return PaymentModule."""
    source = zipfile.ZipFile(PROTOTYPE_ZIP).read('prototype/module_server.py').decode()
    namespace = {'__name__': 'module_server'}
    exec(compile(source, 'prototype/module_server.py', 'exec'), namespace)  # noqa: S102 - our own file
    return namespace['PaymentModule']


@experiment(4, 'A', "Checksum vs hash: forging the prototype's checksum")
def exp_checksum(_):
    PaymentModule = load_payment_module()
    honest, swapped, shifted = PaymentModule(), PaymentModule(), PaymentModule()
    for key, amount in (('pay-1', 1000), ('pay-2', 1000), ('pay-3', 1000)):
        honest.call(key, amount)
    for key, amount in (('pay-1', 1000), ('pay-2', 1000), ('pay-X', 1000)):     # one payment id swapped
        swapped.call(key, amount)
    for key, amount in (('pay-1', 1500), ('pay-2', 500), ('pay-3', 1000)):      # money moved between rides
        shifted.call(key, amount)
    for label, module in (('honest', honest), ('payment id swapped', swapped), ('amounts shifted', shifted)):
        digest = sha256_hex(json.dumps(module.snapshot(), sort_keys=True).encode())
        show(f'{label}', f'checksum {module.checksum()}   sha256 {digest[:20]}...')
    note('PaymentModule.checksum() = (count, total, len(seen)) is identical for all three ledgers: fine for')
    note('recovery class C3 (spot a lost update after a crash), no use against tampering.')
    note('SHA-256 over the snapshot catches the swapped id but NOT the shifted amounts: snapshot() keeps')
    note('only seen ids, total and count, so per-payment amounts never reach the hash. A hash protects')
    note('exactly the bytes you feed it. Exercise: store amounts per key, hash a canonical snapshot')
    note('(json.dumps(..., sort_keys=True) - why sort_keys?), and re-run this experiment.')


def crc32_forge(data: bytes, target: int) -> bytes:
    """Return 4 bytes that make zlib.crc32(data + patch) == target, by running CRC32 backwards."""
    table = []
    for i in range(256):
        c = i
        for _ in range(8):
            c = (c >> 1) ^ 0xEDB88320 if c & 1 else c >> 1
        table.append(c)
    top = {entry >> 24: index for index, entry in enumerate(table)}   # every top byte is unique
    reg = target ^ 0xFFFFFFFF
    for _ in range(4):                                  # undo four steps: find which table entry was XORed in
        index = top[reg >> 24]
        reg = ((reg ^ table[index]) << 8 | index) & 0xFFFFFFFF
    return (reg ^ zlib.crc32(data) ^ 0xFFFFFFFF).to_bytes(4, 'little')


@experiment(5, 'A', 'CRC32 is linear: hit any checksum by appending four bytes')
def exp_crc(_):
    original = b'atlas-go-1.2.0.apk: genuine build'
    forged = b'atlas-go-1.2.0.apk: MALICIOUS build'
    target = zlib.crc32(original)
    patch = crc32_forge(forged, target)
    show('crc32(original)', f'{target:08x}')
    show('crc32(forged)', f'{zlib.crc32(forged):08x}')
    show('patch appended to forged', patch.hex())
    show('crc32(forged + patch)', f'{zlib.crc32(forged + patch):08x}   match = {zlib.crc32(forged + patch) == target}')
    show('sha256(original) vs (forged+patch)', f'{sha256_hex(original)[:16]}... vs {sha256_hex(forged + patch)[:16]}...')
    note('CRC32 (used inside every ZIP, APK and AAB entry) catches transmission noise, but it is linear')
    note('over GF(2), so it can be inverted in microseconds. Never use a CRC as a security check.')


@experiment(6, 'A', 'Verifying ATLAS releases: SHA256SUMS and signing records')
def exp_release(folder):
    files = {name: parse_sums(RELEASES / name) for name in ('SHA256SUMS', 'SHA256SUMS-1.0.0')}
    files['1.2.0/SHA256SUMS'] = parse_sums(RELEASES / '1.2.0' / 'SHA256SUMS')
    for source, rows in files.items():
        for name, digest in rows.items():
            print(f'  {source:<18} {digest[:24]}...  {name}')
    record = json.loads((RELEASES / 'SIGNED_VALIDATION.json').read_text())
    listed = files['SHA256SUMS-1.0.0'].get(record['file'])
    show('SIGNED_VALIDATION.json sha256', record['sha256'][:24] + '...')
    show('same file in SHA256SUMS-1.0.0', f'{(listed or "missing")[:24]}...  agree = {listed == record["sha256"]}')

    def sha256sum_check(path, rows):           # what `sha256sum -c` does, streaming the file
        digest = hashlib.sha256()
        with path.open('rb') as handle:
            for chunk in iter(lambda: handle.read(1 << 20), b''):
                digest.update(chunk)
        actual = digest.hexdigest()
        return actual, [n for n, d in rows.items() if hmac.compare_digest(d, actual)]

    fake = folder / 'atlas-go-1.2.0.apk'
    fake.write_bytes(os.urandom(4096))
    actual, match = sha256sum_check(fake, files['1.2.0/SHA256SUMS'])
    show('a lookalike "atlas-go-1.2.0.apk"', f'{actual[:24]}...  -> {"MATCH " + match[0] if match else "NO MATCH (reject)"}')
    if OPTIONS.get('verify'):
        path = OPTIONS['verify']
        rows = {k: v for table in files.values() for k, v in table.items()}
        actual, match = sha256sum_check(path, rows)
        show(f'your file {path.name}', f'{actual}')
        show('result', 'MATCH ' + match[0] if match else 'NO MATCH: corrupted, tampered, or a different build')
    else:
        note('Check a real download: python3 security_lab/crypto_lab.py --verify atlas-go-1.2.0.apk')
    note('A matching hash only helps if the expected value came by a channel the attacker cannot change.')
    note('SHA256SUMS sits next to the files it describes and is not signed (guide section 7, gap 2):')
    note('whoever can replace the APK on the server can replace SHA256SUMS too.')


@experiment(7, 'A', 'Supply-chain pinning in CI')
def exp_pinning(_):
    workflow = (WORKFLOWS / 'atlas-android.yml').read_text()
    url = re.search(r'(https://\S+bundletool\S+\.jar)', workflow)
    pin = re.search(r"echo '([0-9a-f]{64})  (\S+)' \| sha256sum -c -", workflow)
    show('download', url.group(1) if url else 'not found')
    show('pinned sha256', pin.group(1) if pin else 'not found')
    substituted = b'PK\x03\x04 a jar served by a compromised mirror'
    show('substituted jar sha256', sha256_hex(substituted)[:32] + '...')
    show('sha256sum -c result', 'OK' if pin and sha256_hex(substituted) == pin.group(1) else 'FAILED -> job stops')
    uses = []
    for path in sorted(WORKFLOWS.glob('*.yml')):
        uses += re.findall(r'uses:\s*([\w./-]+)@([\w.-]+)', path.read_text())
    by_sha = [u for u in uses if re.fullmatch(r'[0-9a-f]{40}', u[1])]
    show('GitHub Actions steps (uses:)', f'{len(uses)} total, {len(by_sha)} pinned to a commit SHA, '
         f'{len(uses) - len(by_sha)} to a movable tag')
    for action, ref in sorted(set(uses)):
        print(f'  {"":34} {action}@{ref}')
    note('bundletool is pinned by content: a different file cannot pass, even from the right URL.')
    note('Every action is pinned by tag (@v6, @v7...): whoever controls the tag can move it to new code.')
    note('Pinning uses: to a full commit SHA applies the same idea to CI steps - a good first pull request.')


if __name__ == '__main__':
    main(group='A', description=__doc__.split('\n')[0])
