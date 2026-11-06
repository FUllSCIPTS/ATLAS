# Verified Android handover

Application source: [95f381146b057ea3862ebc524320e0c9aeace85f](https://github.com/FUllSCIPTS/ATLAS/commit/95f381146b057ea3862ebc524320e0c9aeace85f).

Successful full build and acceptance: [GitHub Actions run](https://github.com/FUllSCIPTS/ATLAS/actions/runs/42169139079).

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
The [permanent download release](https://github.com/FUllSCIPTS/ATLAS/releases/tag/atlas-go-v1.1.0)
contains the installable debug APK, unsigned release AAB, screenshot archive and evidence.

## Public binary SHA-256

| File | SHA-256 |
|---|---|
| `atlas-go-demo.apk` | `6d9095b9aa9b01524cb906cc03083be865ff2ebabc2277bd7c82578a562f7735` |
| `atlas-go-unsigned.aab` | `6dce80690ece009a234a2678fb70ae458c5a88e38be3e3db62e8b1586995eb0c` |

## Signing and Play submission

The AAB is unsigned. Sign it using the private upload-key backup handed to the owner,
then follow [the Google Play guide](../docs/GOOGLE_PLAY.md).
The private key and password are never in GitHub. Store listing/account declarations,
any required closed testing, Play pre-launch checks and Google review remain owner steps.

This is an offline model: no real rides, food deliveries or payments. Its small learned policies run locally from bundled constants.
Phone hardware, accessibility and production-service checks remain outside the emulator evidence.
