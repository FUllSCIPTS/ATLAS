# Android downloads

Source, tests and documentation are stored in `android-app/`. All binaries and evidence are attached to the repository's [ATLAS Go release](https://github.com/FUllSCIPTS/ATLAS/releases/tag/atlas-go-v1.0.0).

| Download | Purpose |
|---|---|
| [atlas-go-play.aab](https://github.com/FUllSCIPTS/ATLAS/releases/download/atlas-go-v1.0.0/atlas-go-play.aab) | Verified owner-signed bundle for Play Console internal testing |
| [atlas-go-demo.apk](https://github.com/FUllSCIPTS/ATLAS/releases/download/atlas-go-v1.0.0/atlas-go-demo.apk) | Installable debug demonstration for Android phones/emulators |
| [atlas-go-unsigned.aab](https://github.com/FUllSCIPTS/ATLAS/releases/download/atlas-go-v1.0.0/atlas-go-unsigned.aab) | Reproducible unsigned release bundle; sign before uploading this variant |
| [atlas-go-screenshots.zip](https://github.com/FUllSCIPTS/ATLAS/releases/download/atlas-go-v1.0.0/atlas-go-screenshots.zip) | Twelve actual Android app screenshots |
| [SHA256SUMS](https://github.com/FUllSCIPTS/ATLAS/releases/download/atlas-go-v1.0.0/SHA256SUMS) | Checksums for the signed AAB, unsigned AAB and APK |
| [SIGNED_VALIDATION.json](SIGNED_VALIDATION.json) | Signing result, source revision, binary SHA-256 and certificate fingerprint |
| [upload-certificate.pem](upload-certificate.pem) | Public upload certificate; contains no private key |
| [android-ui-results.json](https://github.com/FUllSCIPTS/ATLAS/releases/download/atlas-go-v1.0.0/android-ui-results.json) | Android interaction test results |
| [native-alignment.txt](https://github.com/FUllSCIPTS/ATLAS/releases/download/atlas-go-v1.0.0/native-alignment.txt) | 16 KB native-library checks |

The signed bundle's signature and bundle structure were verified, and all 70 application payload entries match the tested unsigned build. The downloaded AAB must match the SHA-256 in [the signing record](SIGNED_VALIDATION.json).

The owner retains a separate private upload-key backup containing the keystore and its credentials. The signed AAB and public certificate do not expose that private key. Keep the key for signing future updates; the unsigned variant needs a signature before upload. See [the signing instructions](../docs/GOOGLE_PLAY.md).

Version 1.0.0 / versionCode 1. Application ID `org.atlas.mobility`. 64-bit Android 8.0+ / target Android 16. The AAB is for Play Console → Internal testing; it cannot be installed by tapping it. All rides, deliveries and payments are simulated. If the application ID is already taken, change it and rebuild before first publication.

The lightweight [publication workflow](../../.github/workflows/publish-signed-android.yml) restores this exact signed file from the tested unsigned release and public ZIP/signature metadata. It checks the input and output hashes and verifies the JAR signature and certificate before uploading. It cannot sign a changed build and uses no private upload key. [SIGNED_ZIP_RECIPE.json](SIGNED_ZIP_RECIPE.json) contains public archive metadata and signature bytes only.

See [validation evidence](VALIDATION.md), [screen guide](../docs/USER_GUIDE.md), and [Google Play instructions](../docs/GOOGLE_PLAY.md).
