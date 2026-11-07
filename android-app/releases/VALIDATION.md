# Verified Android handover

Application source: [25de7acc28d1ddcaecbdb05622f8dcd3e54cdade](https://github.com/FUllSCIPTS/ATLAS/commit/25de7acc28d1ddcaecbdb05622f8dcd3e54cdade).

Successful full build and acceptance: [GitHub Actions run](https://github.com/FUllSCIPTS/ATLAS/actions/runs/42348945608).

## Results

- 117 Python domain and persistence cases passed.
- Standard desktop UI: 247 assertions passed.
- Narrow desktop UI with font scale 1.2: 247 assertions passed.
- Android 16 emulator: 292 assertions passed; 22 actual app screenshots captured.
- APK and release AAB built for arm64-v8a and x86_64.
- Bundletool validated the release AAB.
- Release manifest checked: target API 36, non-debuggable, backups disabled, and only the declared foreground permissions (Internet and network state for map tiles; fine and coarse location, asked at run time); no background location or billing.
- Non-debuggable release variant installed and launched separately; process and fatal crash logs checked.
- PASS: 232 64-bit ELF libraries/extensions aligned to 16 KB; 2 Python data archives validated

The source, screenshots, build workflow and documentation are in this repository.
The [release](https://github.com/FUllSCIPTS/ATLAS/releases/tag/atlas-go-v1.2.0) contains the screenshot archive, checksums and evidence.
The APK and AABs are shared on request from a [restricted Google Drive folder](https://drive.google.com/drive/folders/1iio7hs5A7p5sM2GOh3rroG2XemnXw6KV).

## Public binary SHA-256

| File | SHA-256 |
|---|---|
| `atlas-go-demo.apk` | `eaefd2ca3d357e072502deedc378bded7df2c936ee54c708d3ab2e90b9818370` |
| `atlas-go-unsigned.aab` | `132a083e7f97219d8ce8616eae12e3f3aeecb37a85d6136a1a538121a7d114c7` |

## Signing and Play submission

The AAB is unsigned. Sign it using the private upload-key backup handed to the owner,
or add the CI signing secrets described in [the Google Play guide](../docs/GOOGLE_PLAY.md).
The private key and password are never in the repository, logs, artifacts or release files. Store listing/account declarations,
any required closed testing, Play pre-launch checks and Google review remain owner steps.

This is an offline model: no real rides, food deliveries or payments. Its small learned policies run locally from bundled constants.
Phone hardware, accessibility and production-service checks remain outside the emulator evidence.
