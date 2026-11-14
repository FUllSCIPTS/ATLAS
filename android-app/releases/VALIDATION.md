# Verified Android handover

Application source: [cc2832b77555c839d16ce7b462d2336947a46b40](https://github.com/FUllSCIPTS/ATLAS/commit/cc2832b77555c839d16ce7b462d2336947a46b40).

Successful full build and acceptance: [GitHub Actions run](https://github.com/FUllSCIPTS/ATLAS/actions/runs/43603658108).

## Results

- 158 Python domain and persistence cases passed.
- Standard desktop UI: 305 assertions passed.
- Narrow desktop UI with font scale 1.2: 305 assertions passed.
- Android 16 emulator: 362 assertions passed; 28 actual app screenshots captured.
- APK and release AAB built for arm64-v8a and x86_64.
- Bundletool validated the release AAB.
- Release manifest checked: target API 36, non-debuggable, backups disabled, and only the declared foreground permissions (Internet and network state for map tiles; fine and coarse location, asked at run time); no background location or billing.
- Non-debuggable release variant installed and launched separately; process and fatal crash logs checked.
- PASS: 232 64-bit ELF libraries/extensions aligned to 16 KB; 2 Python data archives validated

The source, screenshots, build workflow and documentation are in this repository.
The [release](https://github.com/FUllSCIPTS/ATLAS/releases/tag/atlas-go-v1.3.0) contains the screenshot archive, checksums and evidence.
The APK and AABs are shared on request from a [restricted Google Drive folder](https://drive.google.com/drive/folders/1iio7hs5A7p5sM2GOh3rroG2XemnXw6KV).

## Public binary SHA-256

| File | SHA-256 |
|---|---|
| `atlas-go-demo.apk` | `f0094c1c688fea52c80689418f7de7d90ea38cf11d4fb43fff9a6451a1df8845` |
| `atlas-go-unsigned.aab` | `a483a87d836fc943a51f09231e00da1675eafe80d74dc7d1a59abe1060eae757` |

## Signing and Play submission

The AAB is unsigned. Sign it using the private upload-key backup handed to the owner,
or add the CI signing secrets described in [the Google Play guide](../docs/GOOGLE_PLAY.md).
The private key and password are never in the repository, logs, artifacts or release files. Store listing/account declarations,
any required closed testing, Play pre-launch checks and Google review remain owner steps.

This is an offline model: no real rides, food deliveries or payments. Its small learned policies run locally from bundled constants.
Phone hardware, accessibility and production-service checks remain outside the emulator evidence.
