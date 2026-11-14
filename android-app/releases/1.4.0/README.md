# ATLAS Go 1.4.0 downloads

Version 1.4.0 / versionCode 5 · application ID `org.atlas.mobility` · Android 8.0+ (API 26), target Android 16 (API 36) · 64-bit (arm64-v8a, x86_64).

| File | What it is |
|---|---|
| [atlas-go-1.4.0.apk in the ATLAS Go downloads folder on Google Drive](https://drive.google.com/drive/folders/1iio7hs5A7p5sM2GOh3rroG2XemnXw6KV) (request access) | Installable release APK (not debuggable), signed with APK Signature Scheme v2 and v3. Built from the tested `atlas-go-1.4.0-unsigned.aab` below with bundletool 1.18.3 (universal APK). Open the link and click **Request access**; the owner is notified by email. |
| atlas-go-1.4.0-unsigned.aab | Android App Bundle for Google Play, available from the owner on request; sign it with your upload key before uploading ([how](../../docs/GOOGLE_PLAY.md#signing-and-package-ownership)). |
| [SHA256SUMS](SHA256SUMS) | Checksums for the release APK, the AAB and the CI debug APK |
| [atlas-go-1.4.0-source.zip](https://github.com/FUllSCIPTS/ATLAS/releases/download/atlas-go-v1.4.0/atlas-go-1.4.0-source.zip) | **Source code** of 1.4.0, public under the [MIT licence](../../../LICENSE). SHA-256 `7f360bc79c49e31ffc7345e58cc537620d79270e47b58a800a7e7903b92bdc76` |
| [atlas-go-1.4.0-screenshots.zip](atlas-go-1.4.0-screenshots.zip) | The 29 screenshots taken by the Android 16 emulator acceptance run |
| [RELEASE_NOTES.md](RELEASE_NOTES.md) · [VALIDATION.md](VALIDATION.md) | What changed and how this build was checked |
| [release-manifest.xml](release-manifest.xml) · [native-alignment.txt](native-alignment.txt) · [android-ui-results.json](android-ui-results.json) · [ui-results-440x940.json](ui-results-440x940.json) · [ui-results-360x780.json](ui-results-360x780.json) | Raw evidence |

Check the downloads:

```bash
sha256sum -c SHA256SUMS --ignore-missing
# optional, with the Android SDK build tools:
apksigner verify --print-certs atlas-go-1.4.0.apk
```

APK signing certificate SHA-256: `0A:FC:FC:C6:E1:FC:B9:55:08:CD:41:C5:BC:99:41:2F:70:86:25:3A:17:42:74:02:DB:EC:BD:3B:16:A2:33:A7` (`CN=ATLAS Go Release, O=FUllSCIPTS ATLAS, C=IE`, RSA 3072).

**Upgrading:** 1.4.0 is signed with the same key as 1.3.0 and installs over it, keeping your data. From 1.2.0, uninstall first (different key; this removes its on-phone data). 1.4.0 reads 1.3.0, 1.2.0 and 1.1.0 data files.

Rides, deliveries and payments in ATLAS Go are simulated; accounts are stored only on the phone where they are created.
