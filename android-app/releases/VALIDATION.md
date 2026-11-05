# Verified Android handover

Application source: [913639ad97ea5ec7d53b2296765c7dbdce65d97c](https://github.com/FUllSCIPTS/ATLAS/commit/913639ad97ea5ec7d53b2296765c7dbdce65d97c).

Successful full build and acceptance: [GitHub Actions run](https://github.com/FUllSCIPTS/ATLAS/actions/runs/42076570795).

## Results

- 68 Python domain and persistence cases passed.
- Standard desktop UI: 102 assertions passed.
- Narrow desktop UI with font scale 1.2: 102 assertions passed.
- Android 16 emulator: 130 assertions passed; fourteen actual app screenshots captured.
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
| `atlas-go-demo.apk` | `bc8dedc6777a969ad27f8184c101447a656136b1430139a77d95c9f88e31f2cb` |
| `atlas-go-unsigned.aab` | `5d98956cb511dc288f92c3665b27b965b1ff3988bd75143fc6b024adec4691ba` |

## Signing and Play submission

The AAB is unsigned. Sign it using the private upload-key backup handed to the owner,
then follow [the Google Play guide](../docs/GOOGLE_PLAY.md).
The private key and password are never in GitHub. Store listing/account declarations,
any required closed testing, Play pre-launch checks and Google review remain owner steps.

This is an offline model: no real rides, food deliveries or payments. Its small learned policies run locally from bundled constants.
Phone hardware, accessibility and production-service checks remain outside the emulator evidence.
