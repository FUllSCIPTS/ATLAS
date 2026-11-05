# Android downloads

Source, tests and documentation are stored in `android-app/`. Downloadable binaries are attached to the repository's [ATLAS Go release](https://github.com/FUllSCIPTS/ATLAS/releases/tag/atlas-go-v1.0.0).

| Download | Purpose |
|---|---|
| `atlas-go-demo.apk` | Installable debug demonstration for Android phones/emulators; no real rides, deliveries or charges |
| `atlas-go-unsigned.aab` | Reproducible release bundle; sign with your upload key before Play Console upload |
| `atlas-go-screenshots.zip` | Twelve screenshots from the Python application running on Android |
| `SHA256SUMS` | Public download checksums |
| `android-ui-results.json` | Android interaction test results |
| `native-alignment.txt` | 16 KB native-library checks |

The owner has received the signed `atlas-go-play.aab` separately. Its signature was verified, bundletool validated it, and all 70 application payload entries match the tested unsigned build. See [the signed-bundle record](SIGNED_VALIDATION.json).

The owner receives a separate private upload-key backup containing the keystore and its credentials. It is never included in this public repository. The public AAB requires that key's signature before Play Console upload. Follow the signing commands in the Google Play guide and keep two secure key backups.

Version 1.0.0 / versionCode 1. Application ID `org.atlas.mobility`. 64-bit Android 8.0+ / target Android 16. The AAB is for Play Console → Internal testing; it cannot be installed by tapping it. If the application ID is already taken, change it and rebuild before first publication.

See [validation evidence](VALIDATION.md), [screen guide](../docs/USER_GUIDE.md), and [Google Play instructions](../docs/GOOGLE_PLAY.md).
