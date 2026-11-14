# Verified Android handover

Application source: [8c9a1cdea645a67916e68cfbee87d2733a6dcdd0](https://github.com/FUllSCIPTS/ATLAS/commit/8c9a1cdea645a67916e68cfbee87d2733a6dcdd0).

Successful full build and acceptance: [GitHub Actions run](https://github.com/FUllSCIPTS/ATLAS/actions/runs/43607382926).

## Results

- 173 Python domain and persistence cases passed.
- Standard desktop UI: 314 assertions passed.
- Narrow desktop UI with font scale 1.2: 314 assertions passed.
- Android 16 emulator: 373 assertions passed; 29 actual app screenshots captured.
- APK and release AAB built for arm64-v8a and x86_64.
- Bundletool validated the release AAB.
- Release manifest checked: target API 36, non-debuggable, backups disabled, and only the declared foreground permissions (Internet and network state for map tiles; fine and coarse location, asked at run time); no background location or billing.
- Non-debuggable release variant installed and launched separately; process and fatal crash logs checked.
- PASS: 232 64-bit ELF libraries/extensions aligned to 16 KB; 2 Python data archives validated

The source, screenshots, build workflow and documentation are in this repository.
The [release](https://github.com/FUllSCIPTS/ATLAS/releases/tag/atlas-go-v1.4.0) contains the screenshot archive, checksums and evidence.
The APK and AABs are shared on request from a [restricted Google Drive folder](https://drive.google.com/drive/folders/1iio7hs5A7p5sM2GOh3rroG2XemnXw6KV).

## Public binary SHA-256

| File | SHA-256 |
|---|---|
| `atlas-go-demo.apk` | `d3a5b1696287c3f36ca6c1509c7c5d8c11ce032dca5d2efe1b29b569895ba252` |
| `atlas-go-unsigned.aab` | `a613b0cd3970d715d5945aa31f159a08d83b1f451cd3ff7fc3376306b4e104f6` |

## Signing and Play submission

The AAB is unsigned. Sign it using the private upload-key backup handed to the owner,
or add the CI signing secrets described in [the Google Play guide](../docs/GOOGLE_PLAY.md).
The private key and password are never in the repository, logs, artifacts or release files. Store listing/account declarations,
any required closed testing, Play pre-launch checks and Google review remain owner steps.

This is an offline model: no real rides, food deliveries or payments. Its small learned policies run locally from bundled constants.
Phone hardware, accessibility and production-service checks remain outside the emulator evidence.
