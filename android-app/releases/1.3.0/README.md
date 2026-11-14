# ATLAS Go 1.3.0 downloads

Version 1.3.0 / versionCode 4 · application ID `org.atlas.mobility` · Android 8.0+ (API 26), target Android 16 (API 36) · 64-bit (arm64-v8a, x86_64).

| File | What it is |
|---|---|
| [atlas-go-1.3.0.apk in the ATLAS Go downloads folder on Google Drive](https://drive.google.com/drive/folders/1iio7hs5A7p5sM2GOh3rroG2XemnXw6KV) (request access) | Installable release APK (not debuggable), signed with APK Signature Scheme v2 and v3. Built from the tested `atlas-go-1.3.0-unsigned.aab` below with bundletool 1.18.3 (universal APK). Open the link and click **Request access**; the owner is notified by email. |
| atlas-go-1.3.0-unsigned.aab | Android App Bundle for Google Play, available from the owner on request; sign it with your upload key before uploading ([how](../../docs/GOOGLE_PLAY.md#signing-and-package-ownership)). |
| [SHA256SUMS](SHA256SUMS) | Checksums for the release APK, the AAB and the CI debug APK |
| [atlas-go-1.3.0-source.zip](https://github.com/FUllSCIPTS/ATLAS/releases/download/atlas-go-v1.3.0/atlas-go-1.3.0-source.zip) | **Source code** of 1.3.0, public under the [MIT licence](../../../LICENSE). SHA-256 `4e085a2f61304859e3f1a9e3fc521fe1317791eb45956036c2cb884e985d70f8` |
| [atlas-go-1.3.0-screenshots.zip](atlas-go-1.3.0-screenshots.zip) | The 28 screenshots taken by the Android 16 emulator acceptance run |
| [RELEASE_NOTES.md](RELEASE_NOTES.md) · [VALIDATION.md](VALIDATION.md) | What changed and how this build was checked |
| [release-manifest.xml](release-manifest.xml) · [native-alignment.txt](native-alignment.txt) · [android-ui-results.json](android-ui-results.json) · [ui-results-440x940.json](ui-results-440x940.json) · [ui-results-360x780.json](ui-results-360x780.json) | Raw evidence |

Check the downloads:

```bash
sha256sum -c SHA256SUMS --ignore-missing
# optional, with the Android SDK build tools:
apksigner verify --print-certs atlas-go-1.3.0.apk
```

APK signing certificate SHA-256: `0A:FC:FC:C6:E1:FC:B9:55:08:CD:41:C5:BC:99:41:2F:70:86:25:3A:17:42:74:02:DB:EC:BD:3B:16:A2:33:A7` (`CN=ATLAS Go Release, O=FUllSCIPTS ATLAS, C=IE`, RSA 3072).

**Upgrading from 1.2.0:** this APK is signed with a different key from the 1.2.0 APK, so Android will not install it over 1.2.0. Uninstall 1.2.0 first (this removes its on-phone data). 1.3.0 reads 1.2.0 and 1.1.0 data files.

Rides, deliveries and payments in ATLAS Go are simulated; accounts are stored only on the phone where they are created.
