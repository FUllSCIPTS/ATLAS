# Android downloads

Source, tests and documentation are stored in `android-app/`. The app files (APK and AABs) are shared from a [restricted Google Drive folder](https://drive.google.com/drive/folders/1iio7hs5A7p5sM2GOh3rroG2XemnXw6KV). Downloads of the app files are by request: open a link, click **Request access** in Google Drive, and the owner is notified by email; once approved, you download with your own Google account. Release notes, checksums and test evidence stay public on the repository's releases: [ATLAS Go 1.1.0](https://github.com/FUllSCIPTS/ATLAS/releases/tag/atlas-go-v1.1.0) and [ATLAS Go 1.0.0](https://github.com/FUllSCIPTS/ATLAS/releases/tag/atlas-go-v1.0.0).

| Download | Purpose |
|---|---|
| [atlas-go-play.aab](https://drive.google.com/file/d/1-R9rmDFDw9I-X9T3qE15qdI3P5SlU_s2/view) (request access) | Version 1.0.0: verified owner-signed bundle for Play Console internal testing |
| [atlas-go-demo.apk](https://drive.google.com/file/d/1Opq40u1TQt3Dhx28sE6ninG84Q91PRzL/view) (request access) | Version 1.1.0: installable debug demonstration for Android phones/emulators |
| [atlas-go-unsigned.aab](https://drive.google.com/file/d/1eVyVzPYEgckDlQ-Awe0sXGzfsqOtAngE/view) (request access) | Version 1.1.0: reproducible unsigned release bundle; sign before uploading |
| [atlas-go-screenshots.zip](https://github.com/FUllSCIPTS/ATLAS/releases/download/atlas-go-v1.1.0/atlas-go-screenshots.zip) | Fourteen actual Android app screenshots (1.1.0) |
| [SHA256SUMS](https://github.com/FUllSCIPTS/ATLAS/releases/download/atlas-go-v1.1.0/SHA256SUMS) | Checksums for the 1.1.0 APK and unsigned AAB ([1.0.0 checksums](https://github.com/FUllSCIPTS/ATLAS/releases/download/atlas-go-v1.0.0/SHA256SUMS) include the signed AAB) |
| [SIGNED_VALIDATION.json](SIGNED_VALIDATION.json) | Signing result, source revision, binary SHA-256 and certificate fingerprint |
| [upload-certificate.pem](upload-certificate.pem) | Public upload certificate; contains no private key |
| [android-ui-results.json](https://github.com/FUllSCIPTS/ATLAS/releases/download/atlas-go-v1.1.0/android-ui-results.json) | Android interaction test results |
| [native-alignment.txt](https://github.com/FUllSCIPTS/ATLAS/releases/download/atlas-go-v1.1.0/native-alignment.txt) | 16 KB native-library checks |

The signed bundle's signature and bundle structure were verified, and all 70 application payload entries match the tested unsigned build. The downloaded AAB must match the SHA-256 in [the signing record](SIGNED_VALIDATION.json).

The owner retains a separate private upload-key backup containing the keystore and its credentials. The signed AAB and public certificate do not expose that private key. Keep the key for signing future updates; the unsigned variant needs a signature before upload. See [the signing instructions](../docs/GOOGLE_PLAY.md).

Current version 1.1.0 / versionCode 2 (the signed bundle above is 1.0.0 / versionCode 1). Application ID `org.atlas.mobility`. 64-bit Android 8.0+ / target Android 16. The AAB is for Play Console → Internal testing; it cannot be installed by tapping it. All rides, deliveries and payments are simulated. If the application ID is already taken, change it and rebuild before first publication.

The lightweight [verification workflow](../../.github/workflows/publish-signed-android.yml) restores this exact signed file from the tested unsigned build and public ZIP/signature metadata. It checks the input and output hashes and verifies the JAR signature and certificate, and publishes only the signing record and public certificate; the signed AAB itself is shared on request. It cannot sign a changed build and uses no private upload key. [SIGNED_ZIP_RECIPE.json](SIGNED_ZIP_RECIPE.json) contains public archive metadata and signature bytes only.

See [validation evidence](VALIDATION.md), [screen guide](../docs/USER_GUIDE.md), and [Google Play instructions](../docs/GOOGLE_PLAY.md).
