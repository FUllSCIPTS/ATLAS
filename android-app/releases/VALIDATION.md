# Verified Android handover

Application source: [622f054a912cf01923dc925e2fccb2c93a8c20a3](https://github.com/FUllSCIPTS/ATLAS/commit/622f054a912cf01923dc925e2fccb2c93a8c20a3).

Successful full build and acceptance: [GitHub Actions run](https://github.com/FUllSCIPTS/ATLAS/actions/runs/42171204725).

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
| `atlas-go-demo.apk` | `e249564301c6beaf939e4204baecc4fade24a603bc7bf5dac16621b3a82e6da2` |
| `atlas-go-unsigned.aab` | `5a7d43b9dc4d2413b7ad02bfd31ed311d7109430d3a97c945adc1a00de1541b7` |

## Signing and Play submission

The AAB is unsigned. Sign it using the private upload-key backup handed to the owner,
then follow [the Google Play guide](../docs/GOOGLE_PLAY.md).
The private key and password are never in GitHub. Store listing/account declarations,
any required closed testing, Play pre-launch checks and Google review remain owner steps.

This is an offline model: no real rides, food deliveries or payments. Its small learned policies run locally from bundled constants.
Phone hardware, accessibility and production-service checks remain outside the emulator evidence.
