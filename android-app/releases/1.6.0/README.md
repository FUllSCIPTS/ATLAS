# ATLAS Go 1.6.0 downloads

Version 1.6.0 / versionCode 7 · application ID `org.atlas.mobility` · Android 8.0+ (API 26), target Android 16 (API 36) · 64-bit (arm64-v8a, x86_64).

| File | What it is |
|---|---|
| [Installable APK 1.6.0: the ATLAS Go downloads folder on Google Drive](https://drive.google.com/drive/folders/1iio7hs5A7p5sM2GOh3rroG2XemnXw6KV) (request access) | The tested 1.6.0 APK, `atlas-go-1.6.0-demo.apk` (SHA-256 below). It is the debug-signed demonstration build that the [Android workflow](https://github.com/FUllSCIPTS/ATLAS/actions/runs/44033764144) built and tested; it is **not** signed with the release key. Open the link and click **Request access**. **Status:** the folder still holds the 1.4.0 release APK until the owner uploads this file ([what the owner does](#for-the-owner)). |
| atlas-go-1.6.0-unsigned.aab | Android App Bundle for Google Play, from the same build; sign it with your upload key first ([how](../../docs/GOOGLE_PLAY.md#signing-and-package-ownership)). |
| [SHA256SUMS](SHA256SUMS) | Checksums for the APK, the AAB and the screenshots archive |
| [Source code 1.6.0](https://github.com/FUllSCIPTS/ATLAS/tree/main/android-app) | The complete source under the [MIT licence](../../../LICENSE), built from commit [7bccbf0](https://github.com/FUllSCIPTS/ATLAS/commit/7bccbf003e8f2e88681f3977f11237beeba8af25) |
| [atlas-go-1.6.0-screenshots.zip](atlas-go-1.6.0-screenshots.zip) | The 35 screenshots taken by the Android 16 emulator acceptance run |
| [RELEASE_NOTES.md](RELEASE_NOTES.md) · [VALIDATION.md](VALIDATION.md) | What changed and how this build was checked |
| [android-ui-results.json](android-ui-results.json) · [ui-results-440x940.json](ui-results-440x940.json) · [ui-results-360x780.json](ui-results-360x780.json) · [native-alignment.txt](native-alignment.txt) | Raw evidence |

SHA-256 of the files in the Drive folder:

| File | SHA-256 |
|---|---|
| `atlas-go-1.6.0-demo.apk` | `4ba860f48bb9c7322fd85f91b7c5b280f7027e471f30d5d77b36dc9abcf30bb8` |
| `atlas-go-1.6.0-unsigned.aab` | `ff4b3c2e5d936ba2a878eb2e2c80908a58f4ad8b55b29d84ad9672eae644029d` |

```bash
sha256sum -c SHA256SUMS --ignore-missing
```

**Upgrading.** The demo APK is signed with a different key from the 1.4.0 release APK, so Android will not install it over 1.4.0: uninstall 1.4.0 first (this removes its on-phone data). A release APK signed with the 1.4.0 key installs over it and keeps your data.

## For the owner

The 1.4.0 APK was signed with the owner's release key, which is not available to the build workflow. To publish a 1.6.0 release APK: sign `atlas-go-1.6.0-unsigned.aab` with your upload key and build the universal APK with bundletool ([the 1.4.0 recipe](../1.4.0/README.md)), put it in the Drive folder as `atlas-go-1.6.0.apk`, add its SHA-256 to `SHA256SUMS`, and replace the status sentence above. Until then the demo APK from the [workflow run](https://github.com/FUllSCIPTS/ATLAS/actions/runs/44033764144) (artifact `atlas-go-python-android`, available to signed-in GitHub users) is the 1.6.0 binary.

Rides, deliveries and payments in ATLAS Go are simulated; accounts are stored only on the phone where they are created.
