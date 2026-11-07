# ATLAS Go 1.2.0 downloads

Version 1.2.0 / versionCode 3 · application ID `org.atlas.mobility` · Android 8.0+ (API 26), target Android 16 (API 36) · 64-bit (arm64-v8a, x86_64).

| File | What it is |
|---|---|
| [atlas-go-1.2.0.apk on Google Drive](https://drive.google.com/file/d/1lX5DF9e8ierusJ1OCuVHkeqeCoBgqQfq/view) (request access) | Installable release APK (not debuggable), signed with APK Signature Scheme v2 and v3. Open the link and click **Request access**; the owner is notified by email and, once approved, you download with your Google account. |
| atlas-go-1.2.0-unsigned.aab | Android App Bundle for Google Play, available from the owner on request; sign it with your upload key before uploading ([how](../../docs/GOOGLE_PLAY.md#signing-and-package-ownership)). The Android workflow also builds an AAB from this source on every push to `main`. |
| [SHA256SUMS](SHA256SUMS) | Checksums for the APK and the AAB |
| [atlas-go-1.2.0-screenshots.zip](atlas-go-1.2.0-screenshots.zip) | The 22 screenshots from the acceptance run |
| [RELEASE_NOTES.md](RELEASE_NOTES.md) · [VALIDATION.md](VALIDATION.md) | What changed and how this build was checked |
| [release-manifest.xml](release-manifest.xml) · [native-alignment.txt](native-alignment.txt) · [ui-results-440x940.json](ui-results-440x940.json) · [ui-results-360x780.json](ui-results-360x780.json) | Raw evidence |

Check the downloads:

```bash
sha256sum -c SHA256SUMS
# optional, with the Android SDK build tools:
apksigner verify --print-certs atlas-go-1.2.0.apk
```

APK signing certificate SHA-256: `BF:6A:7C:48:81:2B:11:D7:13:11:73:97:37:62:85:C3:FA:0C:88:A6:AC:69:55:33:D7:43:75:8E:BE:D9:C8:FB` (`CN=ATLAS Go Release, O=FUllSCIPTS ATLAS, C=IE`).

**Upgrading from 1.1.0:** the 1.1.0 demo APK was signed with a different (debug) key, so Android will not install 1.2.0 over it. Uninstall 1.1.0 first. 1.2.0 reads 1.1.0 data, but uninstalling removes it.

Rides, deliveries and payments in ATLAS Go are simulated; accounts are stored only on the phone where they are created.
