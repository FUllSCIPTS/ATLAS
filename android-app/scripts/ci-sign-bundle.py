"""Sign the tested release AAB in CI with the owner's upload key, held only in GitHub Actions secrets.

Inputs come from environment variables that the workflow maps from encrypted secrets:
  ATLAS_UPLOAD_KEYSTORE_BASE64  PKCS12 keystore, base64-encoded
  ATLAS_UPLOAD_ALIAS            key alias
  ATLAS_UPLOAD_PASSWORD         keystore/key password

If no keystore secret is configured the script exits successfully without signing, so the
unsigned build is still published. When signing, the keystore is written to a private temporary
file, signing uses sign-release.py (passwords are passed by environment name, never printed),
and the resulting certificate must match the recorded upload certificate in SIGNED_VALIDATION.json.
A mismatch fails the job before anything is published. The keystore file is always deleted.
"""
import argparse
import base64
import binascii
import hashlib
import json
import os
import ssl
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def certificate_sha256(bundle: Path) -> str:
    pem = subprocess.run(['keytool', '-printcert', '-rfc', '-jarfile', str(bundle)],
                         check=True, capture_output=True, text=True).stdout
    start = pem.index('-----BEGIN CERTIFICATE-----')
    end = pem.index('-----END CERTIFICATE-----', start) + len('-----END CERTIFICATE-----')
    return hashlib.sha256(ssl.PEM_cert_to_DER_cert(pem[start:end])).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('unsigned', type=Path)
    parser.add_argument('signed', type=Path)
    parser.add_argument('--record', type=Path, default=HERE.parent / 'releases' / 'SIGNED_VALIDATION.json')
    args = parser.parse_args()

    encoded = os.environ.get('ATLAS_UPLOAD_KEYSTORE_BASE64', '').strip()
    if not encoded:
        print('Upload-key secrets are not configured; publishing the unsigned bundle only.')
        return 0
    missing = [n for n in ('ATLAS_UPLOAD_ALIAS', 'ATLAS_UPLOAD_PASSWORD') if not os.environ.get(n)]
    if missing:
        print('Missing signing secrets: ' + ', '.join(missing), file=sys.stderr)
        return 1
    try:
        keystore_bytes = base64.b64decode(encoded, validate=False)
    except (binascii.Error, ValueError):
        print('ATLAS_UPLOAD_KEYSTORE_BASE64 is not valid base64.', file=sys.stderr)
        return 1
    expected = json.loads(args.record.read_text())['upload_certificate_sha256']

    handle, keystore = tempfile.mkstemp(suffix='.p12', dir=os.environ.get('RUNNER_TEMP'))
    try:
        os.chmod(keystore, 0o600)
        with os.fdopen(handle, 'wb') as stream:
            stream.write(keystore_bytes)
        env = dict(os.environ, ATLAS_UPLOAD_KEYSTORE=keystore)
        subprocess.run([sys.executable, str(HERE / 'sign-release.py'), str(args.unsigned), str(args.signed)],
                       check=True, env=env)
    finally:
        Path(keystore).unlink(missing_ok=True)

    actual = certificate_sha256(args.signed)
    if actual != expected:
        args.signed.unlink(missing_ok=True)
        print('Signed with a certificate that does not match the recorded upload certificate; '
              'nothing will be published.', file=sys.stderr)
        return 1
    print('Signed bundle uses the recorded upload certificate ' + actual[:16] + '…')
    return 0


if __name__ == '__main__':
    sys.exit(main())
