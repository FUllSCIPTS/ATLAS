#!/usr/bin/env python3
"""Crypto lab C - certificates and PKI (experiments 11-14).

Works on the real ATLAS Go upload certificate (android-app/releases/upload-certificate.pem) and its pinned
fingerprint (SIGNED_VALIDATION.json), then rebuilds the prototype's private CA for mutual TLS
(prototype.zip: proto_run.py) as a small, readable model. Standard library only.

    python3 security_lab/crypto_c_pki.py                     # every experiment in this lab
    python3 security_lab/crypto_c_pki.py --list
    python3 security_lab/crypto_c_pki.py -e 13

Experiments
  11. PEM, DER and the fingerprint pin: what CI actually hashes
  12. Walking the certificate's DER bytes: version, names, dates, key, extensions
  13. Verifying the certificate's own RSA-4096 / SHA-384 signature by hand
  14. A private CA like the prototype's: chains, CA:FALSE, key usage, SAN and expiry

All five crypto labs and the study paths: python3 security_lab/crypto_lab.py --list
See docs/CRYPTOGRAPHY.md for the full teaching guide.
"""
from __future__ import annotations

import base64
import hashlib
import json
import re
import ssl
import textwrap
import zipfile

from crypto_common import (
    CERTIFICATE, PROTOTYPE_ZIP, RELEASES, decode_oid, der_children, der_header, emsa_pkcs1_v15, experiment,
    main, note, rsa_keypair, rsa_sign, rsa_verify, show,
)

OIDS = {
    '1.2.840.113549.1.1.1': 'rsaEncryption',
    '1.2.840.113549.1.1.11': 'sha256WithRSAEncryption',
    '1.2.840.113549.1.1.12': 'sha384WithRSAEncryption',
    '2.5.4.3': 'CN', '2.5.4.10': 'O', '2.5.4.11': 'OU', '2.5.4.6': 'C',
    '2.5.29.14': 'subjectKeyIdentifier', '2.5.29.19': 'basicConstraints', '2.5.29.15': 'keyUsage',
    '2.5.29.37': 'extKeyUsage', '2.5.29.17': 'subjectAltName',
}
TAGS = {0x02: 'INTEGER', 0x03: 'BIT STRING', 0x04: 'OCTET STRING', 0x05: 'NULL', 0x06: 'OID',
        0x0C: 'UTF8String', 0x13: 'PrintableString', 0x17: 'UTCTime', 0x18: 'GeneralizedTime',
        0x30: 'SEQUENCE', 0x31: 'SET', 0xA0: '[0] version', 0xA3: '[3] extensions'}


def certificate_der() -> bytes:
    return ssl.PEM_cert_to_DER_cert(CERTIFICATE.read_text())


def parse_certificate(der: bytes) -> dict:
    """Pull the fields a verifier needs out of an X.509 certificate (no extension semantics)."""
    _, start, end = der_header(der, 0)
    tbs, sig_alg, sig = der_children(der, start, end)
    fields = der_children(der, tbs[2], tbs[3])
    offset = 1 if fields[0][0] == 0xA0 else 0              # [0] version is optional (absent = v1)
    version = der[fields[0][2] + 2] + 1 if offset else 1
    spki = der_children(der, fields[offset + 5][2], fields[offset + 5][3])
    bits = spki[1]
    rsa_seq = der_children(der, bits[2] + 1, bits[3])       # skip the BIT STRING's "unused bits" byte
    n_el, e_el = der_children(der, rsa_seq[0][2], rsa_seq[0][3])
    validity = der_children(der, fields[offset + 3][2], fields[offset + 3][3])
    return dict(
        version=version,
        serial=int.from_bytes(der[fields[offset][2]:fields[offset][3]], 'big'),
        tbs=der[tbs[1]:tbs[3]],
        sig_alg=decode_oid(der[der_children(der, sig_alg[2], sig_alg[3])[0][2]:der_children(der, sig_alg[2], sig_alg[3])[0][3]]),
        signature=int.from_bytes(der[sig[2] + 1:sig[3]], 'big'),
        n=int.from_bytes(der[n_el[2]:n_el[3]], 'big'),
        e=int.from_bytes(der[e_el[2]:e_el[3]], 'big'),
        not_before=(validity[0][0], der[validity[0][2]:validity[0][3]].decode()),
        not_after=(validity[1][0], der[validity[1][2]:validity[1][3]].decode()),
        tbs_range=(tbs[1], tbs[3]),
    )


def colon(hex_digest: str) -> str:
    return ':'.join(hex_digest[i:i + 2] for i in range(0, len(hex_digest), 2)).upper()


@experiment(11, 'C', 'PEM, DER and the fingerprint pin')
def exp_fingerprint(_):
    pem = CERTIFICATE.read_text()
    body = ''.join(line for line in pem.splitlines() if line and not line.startswith('-----'))
    der = base64.b64decode(body)
    pinned = json.loads((RELEASES / 'SIGNED_VALIDATION.json').read_text())['upload_certificate_sha256']
    show('PEM file', f'{len(pem):,} characters: base64 text wrapped between BEGIN/END lines')
    show('DER (the real certificate)', f'{len(der):,} bytes; starts {der[:4].hex()} (SEQUENCE, long length)')
    show('same as ssl.PEM_cert_to_DER_cert', der == ssl.PEM_cert_to_DER_cert(pem))
    fingerprint = hashlib.sha256(der).hexdigest()
    show('SHA-256 of DER', fingerprint)
    show('keytool / openssl style', colon(fingerprint)[:47] + '...')
    show('pinned in SIGNED_VALIDATION.json', pinned)
    show('pin matches', fingerprint == pinned)
    rewrapped = '-----BEGIN CERTIFICATE-----\n' + '\n'.join(textwrap.wrap(body, 76)) + '\n-----END CERTIFICATE-----\n'
    show('re-wrapped PEM (76 columns)', f'same DER: {ssl.PEM_cert_to_DER_cert(rewrapped) == der}, '
         f'same text: {rewrapped == pem}')
    show('wrong: SHA-256 of the PEM text', hashlib.sha256(pem.encode()).hexdigest()[:32] + '...  (never matches)')
    show('legacy SHA-1 fingerprint', colon(hashlib.sha1(der).hexdigest())[:29] + '...')  # noqa: S324 - display only
    note('A fingerprint is the hash of the DER bytes, not of the PEM text: line breaks and headers do')
    note('not count. ci-sign-bundle.py does exactly this (keytool -printcert -rfc, PEM -> DER, SHA-256)')
    note('and fails the job if the result differs from the pinned value.')


@experiment(12, 'C', "Walking the certificate's DER bytes")
def exp_der_walk(_):
    der = certificate_der()

    def walk(start, end, depth, path):
        for tag, header, cstart, cend in der_children(der, start, end):
            name = TAGS.get(tag, f'tag {tag:#04x}')
            body = der[cstart:cend]
            value = ''
            if tag == 0x06:
                oid = decode_oid(body)
                value = f'{oid} ({OIDS.get(oid, "?")})'
            elif tag in (0x0C, 0x13, 0x17, 0x18):
                value = repr(body.decode())
            elif tag == 0x02:
                number = int.from_bytes(body, 'big')
                value = f'{number}' if number < 1 << 64 else f'{number.bit_length()}-bit number'
            elif tag == 0x03:
                value = f'{(len(body) - 1) * 8} bits'
            print(f'  {"  " * depth}{name:<16} len {cend - cstart:<5} {value}')
            if tag in (0x30, 0x31, 0xA0, 0xA3) and depth < 6:
                walk(cstart, cend, depth + 1, path)
            elif tag == 0x04 and depth < 6 and body[:1] == b'\x04':
                walk(cstart, cend, depth + 1, path)          # extension values are DER inside an OCTET STRING
            elif tag == 0x03 and body[1:2] == b'\x30' and 2 <= depth < 5:
                walk(cstart + 1, cend, depth + 1, path)      # the public key is DER inside a BIT STRING

    _, start, end = der_header(der, 0)
    print(f'  SEQUENCE (Certificate)  len {end - start}')
    walk(start, end, 1, [])
    cert = parse_certificate(der)
    note(f'Version field [0] = {cert["version"] - 1} means X.509 v{cert["version"]}; one extension is present')
    note('(subjectKeyIdentifier), as current keytool versions add by default. Do not assume v1.')
    note(f'notAfter uses {TAGS[cert["not_after"][0]]}: RFC 5280 requires it for dates from 2050, because')
    note('UTCTime has a two-digit year. A parser that only knows UTCTime breaks on this certificate.')


@experiment(13, 'C', "Verifying the certificate's own signature by hand")
def exp_self_signature(_):
    der = certificate_der()
    cert = parse_certificate(der)
    k = (cert['n'].bit_length() + 7) // 8
    show('signature algorithm', f'{cert["sig_alg"]} ({OIDS.get(cert["sig_alg"])})')
    show('public key', f'RSA modulus {cert["n"].bit_length()} bits, e = {cert["e"]}')
    show('signed bytes (tbsCertificate)', f'{len(cert["tbs"]):,} bytes at offset {cert["tbs_range"][0]}')
    recovered = pow(cert['signature'], cert['e'], cert['n']).to_bytes(k, 'big')
    expected = emsa_pkcs1_v15(cert['tbs'], k, 'sha384')
    show('signature^e mod n starts', recovered[:12].hex() + ' ... ff ff 00 ' + recovered[-67:-48].hex())
    show('expected EMSA-PKCS1-v1_5 block', expected[:12].hex() + ' ... ff ff 00 ' + expected[-67:-48].hex())
    show('SHA-384(tbs) inside the block', recovered[-48:].hex()[:48] + '...')
    show('self-signature valid', rsa_verify(cert['tbs'], cert['signature'], cert['n'], cert['e'], 'sha384'))
    start = cert['tbs_range'][0]
    position = der.index(b'ATLAS Go Upload', start)
    tampered = bytearray(der)
    tampered[position + 9] ^= 0x20                         # 'Upload' -> 'upload'
    t = parse_certificate(bytes(tampered))
    show('after changing one letter of CN', f'valid: {rsa_verify(t["tbs"], t["signature"], t["n"], t["e"], "sha384")}, '
         f'fingerprint changes: {hashlib.sha256(tampered).hexdigest() != hashlib.sha256(der).hexdigest()}')
    note('The certificate is signed by its own key, so a valid self-signature only proves "whoever made')
    note('this held the private key" - anyone can make one that says CN=ATLAS Go Upload. Trust comes')
    note('from the pinned fingerprint (experiment 11), not from the signature.')


# --------------------------------------------------------------------------- 14: a model of proto_run.py's PKI
def issue(issuer_name, issuer_key, subject, key, *, ca, usage, san=None, days=30, start=0):
    tbs = dict(issuer=issuer_name, subject=subject, n=key['n'], e=key['e'], ca=ca, usage=usage, san=san,
               not_before=start, not_after=start + days)
    blob = json.dumps(tbs, sort_keys=True).encode()        # stands in for DER: canonical bytes to sign
    return dict(tbs=tbs, signature=rsa_sign(blob, issuer_key))


def validate(chain, anchor, *, purpose, host=None, day=1):
    """Check a leaf-first chain against one trust anchor, the way TLS does (simplified)."""
    for i, cert in enumerate(chain):
        issuer = chain[i + 1]['tbs'] if i + 1 < len(chain) else anchor['tbs']
        blob = json.dumps(cert['tbs'], sort_keys=True).encode()
        if cert['tbs']['issuer'] != issuer['subject']:
            return f'issuer "{cert["tbs"]["issuer"]}" not found'
        if not rsa_verify(blob, cert['signature'], issuer['n'], issuer['e']):
            return 'bad signature'
        if not issuer['ca']:
            return f'"{issuer["subject"]}" is CA:FALSE and may not issue certificates'
        if not cert['tbs']['not_before'] <= day <= cert['tbs']['not_after']:
            return f'expired or not yet valid (day {day})'
    leaf = chain[0]['tbs']
    if purpose not in leaf['usage']:
        return f'extendedKeyUsage {leaf["usage"]} does not allow {purpose}'
    if host and leaf['san'] != host:
        return f'subjectAltName {leaf["san"]} does not match {host}'
    return 'OK'


@experiment(14, 'C', "A private CA like the prototype's mutual TLS")
def exp_private_ca(_):
    commands = [line.strip() for line in zipfile.ZipFile(PROTOTYPE_ZIP).read('prototype/proto_run.py').decode().splitlines()
                if re.search(r'basicConstraints|extendedKeyUsage|subjectAltName', line)]
    print('  prototype/proto_run.py sets:')
    for line in commands:
        print(f'    {line[:92]}')
    ca_key, server_key, client_key, evil_key = (rsa_keypair(1024) for _ in range(4))
    ca = issue('atlas-ca', ca_key, 'atlas-ca', ca_key, ca=True, usage=[])
    server = issue('atlas-ca', ca_key, 'server', server_key, ca=False, usage=['serverAuth'], san='IP:127.0.0.1')
    client = issue('atlas-ca', ca_key, 'client', client_key, ca=False, usage=['clientAuth'])
    forged = issue('server', server_key, 'payments', evil_key, ca=False, usage=['serverAuth'], san='IP:127.0.0.1')
    rogue_ca = issue('atlas-ca', evil_key, 'atlas-ca', evil_key, ca=True, usage=[])
    impostor = issue('atlas-ca', evil_key, 'server', evil_key, ca=False, usage=['serverAuth'], san='IP:127.0.0.1')
    cases = [
        ('server cert, client checks it', [server], dict(purpose='serverAuth', host='IP:127.0.0.1')),
        ('client cert, server checks it', [client], dict(purpose='clientAuth')),
        ('client cert presented as a server', [client], dict(purpose='serverAuth', host='IP:127.0.0.1')),
        ('server cert for the wrong address', [server], dict(purpose='serverAuth', host='IP:10.0.0.5')),
        ('leaf key used to issue a cert', [forged, server], dict(purpose='serverAuth', host='IP:127.0.0.1')),
        ('server cert on day 31', [server], dict(purpose='serverAuth', host='IP:127.0.0.1', day=31)),
        ('impostor from a look-alike CA', [impostor], dict(purpose='serverAuth', host='IP:127.0.0.1')),
    ]
    for label, chain, kwargs in cases:
        show(label, validate(chain, ca, **kwargs))
    show('impostor checked against its own CA', validate([impostor], rogue_ca, purpose='serverAuth', host='IP:127.0.0.1'))
    note('Same subject name "atlas-ca" is not enough: the trust anchor is the CA\'s key (ca.crt), loaded by')
    note('both sides with CERT_REQUIRED. Every rejection above maps to one openssl line: CA:FALSE stops a')
    note('stolen leaf key minting certificates, EKU separates clients from servers, SAN binds the address,')
    note('and -days 30 limits how long a leaked key is useful.')


if __name__ == '__main__':
    main(group='C', description=__doc__.split('\n')[0])
