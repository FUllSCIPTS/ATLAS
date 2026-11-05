# Verified Android handover

Application source: [7c75873d9296c734799b35d9d8b524b6e8c87785](https://github.com/FUllSCIPTS/ATLAS/commit/7c75873d9296c734799b35d9d8b524b6e8c87785).

Successful full build and acceptance: [GitHub Actions run](https://github.com/FUllSCIPTS/ATLAS/actions/runs/41992777003).

## Results

- 40 Python domain and persistence cases passed.
- Standard desktop UI: 88 assertions passed.
- Narrow desktop UI with font scale 1.2: 88 assertions passed.
- Android 16 emulator: 88 assertions passed; twelve actual app screenshots captured.
- APK and release AAB built for arm64-v8a and x86_64.
- Bundletool validated the release AAB.
- Release manifest checked: target API 36, non-debuggable, backups disabled, and no Internet, location or billing permissions.
- Non-debuggable release variant installed and launched separately; process and fatal crash logs checked.
- PASS: 232 64-bit ELF libraries/extensions aligned to 16 KB; 2 Python data archives validated

The source, screenshots, build workflow and documentation are in this repository.
The [permanent download release](https://github.com/FUllSCIPTS/ATLAS/releases/tag/atlas-go-v1.0.0)
contains the installable debug APK, unsigned release AAB, screenshot archive and evidence.

## Public binary SHA-256

| File | SHA-256 |
|---|---|
| `atlas-go-demo.apk` | `e9704237b0218ad87a52ae212ebab7a177f7359a0c4d499fe0fae6c6d33a5f71` |
| `atlas-go-unsigned.aab` | `896f87bf73b224f4ddc371b60dedb6b81e9ddd0c8bc33e218843e9ecffdef12b` |

## Signing and Play submission

The AAB is unsigned. Sign it using the private upload-key backup handed to the owner,
then follow [the Google Play guide](../docs/GOOGLE_PLAY.md).
The private key and password are never in GitHub. Store listing/account declarations,
any required closed testing, Play pre-launch checks and Google review remain owner steps.

This is an offline model: no real rides, food deliveries, payments or mobile ML inference.
Phone hardware, accessibility and production-service checks remain outside the emulator evidence.
