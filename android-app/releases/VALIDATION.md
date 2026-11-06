# Verified Android handover

Application source: [36b8a2855a5041b668df3ab2619c03abc08414a7](https://github.com/FUllSCIPTS/ATLAS/commit/36b8a2855a5041b668df3ab2619c03abc08414a7).

Successful full build and acceptance: [GitHub Actions run](https://github.com/FUllSCIPTS/ATLAS/actions/runs/42179962012).

## Results

- 68 Python domain and persistence cases passed.
- Standard desktop UI: 102 assertions passed.
- Narrow desktop UI with font scale 1.2: 102 assertions passed.
- Android 16 emulator: 131 assertions passed; fourteen actual app screenshots captured.
- APK and release AAB built for arm64-v8a and x86_64.
- Bundletool validated the release AAB.
- Release manifest checked: target API 36, non-debuggable, backups disabled, and no Internet, location or billing permissions.
- Non-debuggable release variant installed and launched separately; process and fatal crash logs checked.
- PASS: 232 64-bit ELF libraries/extensions aligned to 16 KB; 2 Python data archives validated

The source, screenshots, build workflow and documentation are in this repository.
The [release](https://github.com/FUllSCIPTS/ATLAS/releases/tag/atlas-go-v1.1.0) contains the screenshot archive, checksums and evidence.
The APK and AABs are shared on request from a [restricted Google Drive folder](https://drive.google.com/drive/folders/1iio7hs5A7p5sM2GOh3rroG2XemnXw6KV).

## Public binary SHA-256

| File | SHA-256 |
|---|---|
| `atlas-go-demo.apk` | `de65057ebfaf0a2e5009eeb8ede2cca6397bb551c1d2d8f6359a34c173440e2a` |
| `atlas-go-unsigned.aab` | `1d2e52d366ed9974624bfce030fcc41a96f417cc4b6863b16466ba7c158e3aa1` |

## Signing and Play submission

The AAB is unsigned. Sign it using the private upload-key backup handed to the owner,
or add the CI signing secrets described in [the Google Play guide](../docs/GOOGLE_PLAY.md).
The private key and password are never in the repository, logs, artifacts or release files. Store listing/account declarations,
any required closed testing, Play pre-launch checks and Google review remain owner steps.

This is an offline model: no real rides, food deliveries or payments. Its small learned policies run locally from bundled constants.
Phone hardware, accessibility and production-service checks remain outside the emulator evidence.
