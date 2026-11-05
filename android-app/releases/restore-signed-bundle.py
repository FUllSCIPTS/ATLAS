"""Restore the existing signed AAB using public ZIP/signature metadata.

This does not sign a new build and never needs an upload key. Both the tested
input and the exact signed output must match their recorded SHA-256 values.
"""

import argparse
import base64
import hashlib
import json
import struct
import tempfile
import zipfile
import zlib
from pathlib import Path


def digest(data):
    return hashlib.sha256(data).hexdigest()


def restore(unsigned, output, recipe_path):
    recipe = json.loads(recipe_path.read_text())
    if recipe['format'] != 1:
        raise ValueError('Unsupported signed ZIP recipe')
    source = unsigned.read_bytes()
    if digest(source) != recipe['unsigned_sha256']:
        raise ValueError('Input is not the verified unsigned release')
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=output.parent, delete=False) as dest:
            temporary = Path(dest.name)
            with zipfile.ZipFile(unsigned) as archive:
                restored_entries = set()
                for segment in recipe['segments']:
                    if 'literal' in segment:
                        dest.write(base64.b64decode(segment['literal'], validate=True))
                        continue
                    name = segment['entry']
                    if name in restored_entries:
                        raise ValueError('Duplicate application payload entry')
                    entry = archive.getinfo(name)
                    if entry.compress_type != segment['method']:
                        raise ValueError('Payload compression method changed')
                    name_size, extra_size = struct.unpack_from('<HH', source, entry.header_offset + 26)
                    start = entry.header_offset + 30 + name_size + extra_size
                    compressed = source[start:start + entry.compress_size]
                    if digest(compressed) != segment['compressed_sha256']:
                        payload = archive.read(entry)
                        if entry.compress_type == zipfile.ZIP_STORED:
                            compressed = payload
                        elif entry.compress_type == zipfile.ZIP_DEFLATED:
                            compressor = zlib.compressobj(6, zlib.DEFLATED, -15)
                            compressed = compressor.compress(payload) + compressor.flush()
                        else:
                            raise ValueError('Unsupported payload compression method')
                    if digest(compressed) != segment['compressed_sha256']:
                        raise ValueError('Cannot reproduce the signed payload bytes: ' + name)
                    dest.write(compressed)
                    restored_entries.add(name)
                if len(restored_entries) != recipe['payload_entries']:
                    raise ValueError('Application payload count does not match')
        if temporary.stat().st_size != recipe['signed_bytes']:
            raise ValueError('Signed bundle size does not match')
        if digest(temporary.read_bytes()) != recipe['signed_sha256']:
            raise ValueError('Signed bundle SHA-256 does not match')
        temporary.replace(output)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    print('Restored exact signed bundle: ' + recipe['signed_sha256'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--unsigned', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--recipe', type=Path, default=Path(__file__).with_name('SIGNED_ZIP_RECIPE.json'))
    args = parser.parse_args()
    restore(args.unsigned, args.output, args.recipe)
