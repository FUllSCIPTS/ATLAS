# Verified Android handover

Application source: [024b328fed69ffcd3058ae559d9e7e6a59dee4b8](https://github.com/FUllSCIPTS/ATLAS/commit/024b328fed69ffcd3058ae559d9e7e6a59dee4b8).

Successful full build and acceptance: [GitHub Actions run](https://github.com/FUllSCIPTS/ATLAS/actions/runs/41996737984).

## Results

- 40 Python domain and persistence cases passed.
- Standard desktop UI: 88 assertions passed.
- Narrow desktop UI with font scale 1.2: 88 assertions passed.
- Android 16 emulator: 112 assertions passed; twelve actual app screenshots captured.
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
| `atlas-go-demo.apk` | `867fc0646a113ce79bbdc43aba2ca1ecf540c27812bb41626f5f34b5e9eee731` |
| `atlas-go-unsigned.aab` | `4887149df14fc81662a6ade71bc83a38b24861ba4fcb45fd87974264d4017b40` |

## Signing and Play submission

The AAB is unsigned. Sign it using the private upload-key backup handed to the owner,
then follow [the Google Play guide](../docs/GOOGLE_PLAY.md).
The private key and password are never in GitHub. Store listing/account declarations,
any required closed testing, Play pre-launch checks and Google review remain owner steps.

This is an offline model: no real rides, food deliveries, payments or mobile ML inference.
Phone hardware, accessibility and production-service checks remain outside the emulator evidence.

## Completed owner signing

The owner’s `atlas-go-play.aab` was signed locally with the existing private upload key. The JAR signature and bundle structure were verified, and all 70 application payload entries are identical to the tested build. The signed bundle is supplied privately; public CI artifacts remain reproducible unsigned outputs.

- SHA-256: `9932955f7b078a939f67964d83dc86fa5bdaa2a0c294adf34316dbcebdec216a`
- Upload certificate SHA-256: `059076082129b3ed2f08c5b88a207bdebf2bba88304c0821b77d128c034944d7`
- [Machine-readable signing record](SIGNED_VALIDATION.json)

No private keystore, password or encrypted private-key backup was published.
