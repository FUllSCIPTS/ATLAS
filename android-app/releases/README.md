# Android downloads

The final handover places the tested APK, upload-key-signed Android App Bundle, checksums and build evidence in this folder.

- `atlas-go.apk`: release APK for direct Android installation (allow installation from the browser/file manager when prompted).
- `atlas-go-play.aab`: signed release bundle for **Play Console → Internal testing**. An AAB cannot be installed by tapping it.
- `SHA256SUMS`: binary checksums.
- `VALIDATION.md`: source commit, successful CI run and test evidence.

Version 1.0.0 / versionCode 1. Application ID `org.atlas.mobility`. Android 8.0+ / target Android 16. Demo only: no real rides, deliveries or charges.

The upload key and its credentials are delivered privately, never included in this public repository. Back them up before using this package ID in Play Console. If the ID is already taken, change it and rebuild before first publication.
