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

The owner receives a separate signed handover containing `atlas-go.apk`, `atlas-go-play.aab`, checksums and documentation. Its upload-key backup is delivered privately, never in this public repository. Back up the key before using this package ID in Play Console.

Version 1.0.0 / versionCode 1. Application ID `org.atlas.mobility`. Android 8.0+ / target Android 16. The AAB is for Play Console → Internal testing; it cannot be installed by tapping it. If the application ID is already taken, change it and rebuild before first publication.

See [validation evidence](VALIDATION.md), [screen guide](../docs/USER_GUIDE.md), and [Google Play instructions](../docs/GOOGLE_PLAY.md).
