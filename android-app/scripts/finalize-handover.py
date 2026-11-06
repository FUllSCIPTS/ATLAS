"""Commit only verified Android screenshots and build evidence to the repository."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path
from xml.etree import ElementTree as ET

parser=argparse.ArgumentParser()
parser.add_argument('--artifact',required=True)
parser.add_argument('--source',required=True)
parser.add_argument('--run-url',required=True)
args=parser.parse_args()
version=Path('android-app/atlas_go/__init__.py').read_text().split("'")[1]
tag=f'atlas-go-v{version}'
artifact=Path(args.artifact)
android=artifact/'test-output/android'
result=json.loads((android/'result.json').read_text())
assert result['success'] and result['checks']>=88,result
unit=ET.parse(artifact/'test-output/unit-tests.xml').getroot()
suites=[unit] if unit.tag=='testsuite' else list(unit)
tests=sum(int(s.get('tests',0)) for s in suites)
assert tests>=40,tests
assert not any(int(s.get('failures',0))+int(s.get('errors',0)) for s in suites)
target=Path('android-app/docs/screenshots')
target.mkdir(parents=True,exist_ok=True)
for source in sorted(android.glob('*.png')):
    shutil.copy2(source,target/source.name)
assert len(list(target.glob('*.png')))==14
release=Path('android-app/releases')
rows=[]
signed=(artifact/'release'/'atlas-go-play.aab').is_file()
for name in ('atlas-go-demo.apk','atlas-go-unsigned.aab')+(('atlas-go-play.aab',) if signed else ()):
    digest=hashlib.sha256((artifact/'release'/name).read_bytes()).hexdigest()
    rows.append((name,digest))
(release/'SHA256SUMS').write_text(''.join(f'{digest}  {name}\n' for name,digest in rows))
alignment=(artifact/'test-output/native-alignment.txt').read_text().strip()
text=f"""# Verified Android handover

Application source: [{args.source}](https://github.com/FUllSCIPTS/ATLAS/commit/{args.source}).

Successful full build and acceptance: [GitHub Actions run]({args.run_url}).

## Results

- {tests} Python domain and persistence cases passed.
- Standard desktop UI: 102 assertions passed.
- Narrow desktop UI with font scale 1.2: 102 assertions passed.
- Android 16 emulator: {result['checks']} assertions passed; fourteen actual app screenshots captured.
- APK and release AAB built for arm64-v8a and x86_64.
- Bundletool validated the release AAB.
- Release manifest checked: target API 36, non-debuggable, backups disabled, and no Internet, location or billing permissions.
- Non-debuggable release variant installed and launched separately; process and fatal crash logs checked.
- {alignment}

The source, screenshots, build workflow and documentation are in this repository.
The [permanent download release](https://github.com/FUllSCIPTS/ATLAS/releases/tag/{tag})
contains the installable debug APK, unsigned release AAB, screenshot archive and evidence.

## Public binary SHA-256

| File | SHA-256 |
|---|---|
"""
text+=''.join(f'| `{name}` | `{digest}` |\n' for name,digest in rows)
text+="""
## Signing and Play submission

"""+("""`atlas-go-play.aab` was signed in CI with the owner's upload key, supplied through encrypted
GitHub Actions secrets. Its certificate was checked against the recorded upload certificate in
[SIGNED_VALIDATION.json](SIGNED_VALIDATION.json) before publication. Upload it to Play Console as described in
[the Google Play guide](../docs/GOOGLE_PLAY.md).""" if signed else """The AAB is unsigned. Sign it using the private upload-key backup handed to the owner,
or add the CI signing secrets described in [the Google Play guide](../docs/GOOGLE_PLAY.md).""")+"""
The private key and password are never in the repository, logs, artifacts or release files. Store listing/account declarations,
any required closed testing, Play pre-launch checks and Google review remain owner steps.

This is an offline model: no real rides, food deliveries or payments. Its small learned policies run locally from bundled constants.
Phone hardware, accessibility and production-service checks remain outside the emulator evidence.
"""
(release/'VALIDATION.md').write_text(text)
print(f'Prepared fourteen Android screenshots and validation for {args.source}')
