#!/usr/bin/env python3
"""Crypto lab D - digital signatures (experiments 15-17).

Builds RSA signatures up from the textbook formula to SHA256withRSA (PKCS#1 v1.5), the scheme
android-app/scripts/sign-release.py asks jarsigner for, then models how a signed ATLAS Go bundle is
checked entry by entry. Standard library only; keys are generated fresh for every run.

    python3 security_lab/crypto_d_signatures.py              # every experiment in this lab
    python3 security_lab/crypto_d_signatures.py --list
    python3 security_lab/crypto_d_signatures.py -e 17

Experiments
  15. Textbook RSA step by step, and why it is malleable
  16. SHA256withRSA (PKCS#1 v1.5): hash-then-sign with padding, as jarsigner does
  17. Signing a bundle the JAR way: MANIFEST.MF, the .SF file and what each tamper breaks

All five crypto labs and the study paths: python3 security_lab/crypto_lab.py --list
See docs/CRYPTOGRAPHY.md for the full teaching guide.
"""
from __future__ import annotations

import base64
import hashlib
import re
import zipfile

from crypto_common import (
    ROOT, emsa_pkcs1_v15, experiment, main, note, rsa_keypair, rsa_sign, rsa_verify, show,
)


@experiment(15, 'D', 'Textbook RSA step by step, and why it is malleable')
def exp_textbook(_):
    p, q, e = 61, 53, 17                                    # the classic classroom example
    n, phi = p * q, (p - 1) * (q - 1)
    d = pow(e, -1, phi)
    show('p, q', f'{p}, {q}')
    show('n = p*q, phi = (p-1)(q-1)', f'{n}, {phi}')
    show('e (public), d = e^-1 mod phi', f'{e}, {d}   check e*d mod phi = {e * d % phi}')
    m = 1250                                                # a fare in cents, as the "message"
    s = pow(m, d, n)
    show('sign m=1250: s = m^d mod n', s)
    show('verify: s^e mod n', f'{pow(s, e, n)}  == m: {pow(s, e, n) == m}')
    key = rsa_keypair(1024)
    show('same with a 1024-bit key', f'n has {key["n"].bit_length()} bits; factoring n would reveal d')
    m1, m2 = 3, 417                                         # two receipts the owner did sign
    s1, s2 = pow(m1, key['d'], key['n']), pow(m2, key['d'], key['n'])
    forged = s1 * s2 % key['n']                             # no private key used
    show('attacker multiplies two signatures', f'valid signature on {m1 * m2}: {pow(forged, key["e"], key["n"]) == m1 * m2}')
    show('textbook sign of 0 and 1', f'{pow(0, key["d"], key["n"])} and {pow(1, key["d"], key["n"])} (signatures anyone can guess)')
    note('Textbook RSA is multiplicative: sig(a) * sig(b) = sig(a*b). An attacker who sees two signed')
    note('values can sign their product - here 1251 cents - without the key. Real schemes sign a padded')
    note('hash of the message, never the raw number (experiment 16).')


@experiment(16, 'D', 'SHA256withRSA (PKCS#1 v1.5) as jarsigner uses it')
def exp_pkcs1(_):
    script = (ROOT / 'android-app' / 'scripts' / 'sign-release.py').read_text()
    flags = sorted(set(re.findall(r"'(-(?:sigalg|digestalg))',\s*'([^']+)'", script)))
    show('sign-release.py asks jarsigner for', ', '.join(f'{f} {v}' for f, v in flags) or 'see script')
    key = rsa_keypair(2048)
    k = (key['n'].bit_length() + 7) // 8
    message = b'MANIFEST.MF of atlas-go-1.2.0'
    block = emsa_pkcs1_v15(message, k, 'sha256')
    pad = block.index(0, 2) - 2
    print(f'  encoded block ({k} bytes):')
    print('    00 01                       block type 1 (signature)')
    print(f'    ff x {pad:<22} padding')
    print('    00                          separator')
    print(f'    {block[-51:-32].hex()}  DigestInfo: "this is SHA-256"')
    print(f'    {block[-32:].hex()[:40]}...  SHA-256(message)')
    signature = rsa_sign(message, key)
    show('verify original', rsa_verify(message, signature, key['n'], key['e']))
    show('verify with one byte changed', rsa_verify(message + b'!', signature, key['n'], key['e']))
    show('sign twice, same signature', rsa_sign(message, key) == signature)
    s1, s2 = rsa_sign(b'receipt 1', key), rsa_sign(b'receipt 2', key)
    product = s1 * s2 % key['n']
    decoded = pow(product, key['e'], key['n']).to_bytes(k, 'big')
    show('multiply two signatures (exp. 15)', f'decodes to a valid padded block: {decoded[:2] == bytes([0, 1])}')
    note('Padding plus the DigestInfo makes the signed number huge and highly structured, so the')
    note('multiplicative trick no longer lands on a valid block. PKCS#1 v1.5 is deterministic; RSA-PSS')
    note('adds randomness and a security proof and is preferred for new designs. Verifiers must compare')
    note('the whole block (as rsa_verify does), not just search it for the hash.')


def manifest_section(name: str, data: bytes) -> bytes:
    return f'Name: {name}\r\nSHA-256-Digest: {base64.b64encode(hashlib.sha256(data).digest()).decode()}\r\n\r\n'.encode()


def jar_sign(path, key):
    """Write META-INF/MANIFEST.MF, ATLAS.SF and ATLAS.RSA into a zip, the way jarsigner lays them out."""
    with zipfile.ZipFile(path) as z:
        entries = {i.filename: z.read(i) for i in z.infolist()}
    sections = {name: manifest_section(name, data) for name, data in entries.items()}
    manifest = b'Manifest-Version: 1.0\r\nCreated-By: crypto lab\r\n\r\n' + b''.join(sections.values())
    sf = (b'Signature-Version: 1.0\r\nSHA-256-Digest-Manifest: '
          + base64.b64encode(hashlib.sha256(manifest).digest()) + b'\r\n\r\n'
          + b''.join(f'Name: {n}\r\nSHA-256-Digest: {base64.b64encode(hashlib.sha256(s).digest()).decode()}\r\n\r\n'.encode()
                     for n, s in sections.items()))
    signature = rsa_sign(sf, key).to_bytes((key['n'].bit_length() + 7) // 8, 'big')
    with zipfile.ZipFile(path, 'a') as z:
        z.writestr('META-INF/MANIFEST.MF', manifest)
        z.writestr('META-INF/ATLAS.SF', sf)
        z.writestr('META-INF/ATLAS.RSA', signature)        # real jarsigner wraps this in PKCS#7 / CMS


def jar_verify(path, key):
    with zipfile.ZipFile(path) as z:
        files = {i.filename: z.read(i) for i in z.infolist()}
    manifest, sf = files['META-INF/MANIFEST.MF'], files['META-INF/ATLAS.SF']
    if not rsa_verify(sf, int.from_bytes(files['META-INF/ATLAS.RSA'], 'big'), key['n'], key['e']):
        return 'FAIL: signature over ATLAS.SF'
    want = re.search(rb'SHA-256-Digest-Manifest: (\S+)', sf).group(1)
    if base64.b64decode(want) != hashlib.sha256(manifest).digest():
        return 'FAIL: ATLAS.SF does not match MANIFEST.MF'
    listed = dict(re.findall(rb'Name: (\S+)\r\nSHA-256-Digest: (\S+)', manifest))
    for name, data in files.items():
        if name.startswith('META-INF/'):
            continue
        if name.encode() not in listed:
            return f'WARNING: unsigned entry {name} (not in MANIFEST.MF)'
        if base64.b64decode(listed[name.encode()]) != hashlib.sha256(data).digest():
            return f'FAIL: digest of {name}'
    return 'OK: all entries verified'


@experiment(17, 'D', 'Signing a bundle the JAR way')
def exp_jar(folder):
    key = rsa_keypair(2048)
    entries = {'base/manifest/AndroidManifest.xml': b'<manifest package="org.atlas.mobility"/>',
               'base/dex/classes.dex': b'dex\n035\x00 compiled ATLAS Go code',
               'base/assets/places.json': b'["UCC Campus","Cork City Centre","Kent Station","Cork Airport"]'}

    def build(name, mutate=None, after_sign=None):
        path = folder / name
        with zipfile.ZipFile(path, 'w') as z:
            for entry, data in entries.items():
                z.writestr(entry, data)
        jar_sign(path, key)
        if after_sign:
            after_sign(path)
        return path

    def rewrite(path, changes):
        with zipfile.ZipFile(path) as z:
            files = {i.filename: z.read(i) for i in z.infolist()}
        files.update(changes)
        with zipfile.ZipFile(path, 'w') as z:
            for entry, data in files.items():
                z.writestr(entry, data)

    signed = build('signed.aab')
    with zipfile.ZipFile(signed) as z:
        mf = z.read('META-INF/MANIFEST.MF').decode().split('\r\n\r\n')[1]
    print('  MANIFEST.MF section:')
    for line in mf.split('\r\n'):
        print(f'    {line}')
    show('untouched bundle', jar_verify(signed, key))
    evil = b'dex\n035\x00 code with a backdoor'
    cases = [
        ('classes.dex replaced', lambda p: rewrite(p, {'base/dex/classes.dex': evil})),
        ('... and MANIFEST.MF digest updated', lambda p: rewrite(p, {
            'base/dex/classes.dex': evil,
            'META-INF/MANIFEST.MF': zipfile.ZipFile(p).read('META-INF/MANIFEST.MF').replace(
                base64.b64encode(hashlib.sha256(entries['base/dex/classes.dex']).digest()),
                base64.b64encode(hashlib.sha256(evil).digest()))})),
        ('new file added, not in manifest', lambda p: rewrite(p, {'base/assets/extra.js': b'fetch("evil")'})),
        ('signed by a different key', None),
    ]
    for label, action in cases:
        if action:
            show(label, jar_verify(build(f'{len(label)}.aab', after_sign=action), key))
        else:
            show(label, jar_verify(build('other.aab'), rsa_keypair(2048)))
    note('Three layers: each entry is hashed into MANIFEST.MF, the manifest is hashed into the .SF file,')
    note('and only the .SF is signed. An attacker must break one of them to get past jarsigner -verify.')
    note('JAR signing does not cover entries missing from the manifest or the ZIP structure itself, which')
    note('is why Android added APK Signature Scheme v2/v3 (the 1.2.0 APK): one signature over the file.')


if __name__ == '__main__':
    main(group='D', description=__doc__.split('\n')[0])
