# Build and Google Play handover

This release is a Python/Kivy, offline **demonstration app**. The owner’s [signed `atlas-go-play.aab`](https://drive.google.com/file/d/1-R9rmDFDw9I-X9T3qE15qdI3P5SlU_s2/view) is shared on request from Google Drive and ready for an internal-test upload. It is not already on Google Play, and approval is not guaranteed. Do not describe it as providing actual rides or deliveries.

## Build tools

Application screens, domain rules, persistence and tests are written in Python. Buildozer and python-for-android package the interpreter and Kivy runtime for Android. Their generated Android scaffolding and native libraries are tooling dependencies; there is no hand-written Java application module in this project.

Desktop preview: Python 3.12, `pip install -r requirements-dev.txt`, then `python main.py`. Domain tests: `python -m pytest tests`.

Android builds use Linux/WSL2, Buildozer revision `76bac28545c66bbcc671d49aca553a747d69608e`, p4a revision `1c9a4b4f817847bd8505d972d1a0e6f965929a88`, API 36, minimum API 26 and NDK 28c. Both arm64-v8a for phones and x86_64 for emulator validation are packaged. Install JDK 17, build-essential, git, zip, unzip, autoconf, libtool, libtool-bin, libltdl-dev, pkg-config, zlib1g-dev, libncurses-dev, cmake, libffi-dev, libssl-dev, automake, autopoint and gettext. See the exact commands in `.github/workflows/atlas-android.yml`.

```bash
pip install 'git+https://github.com/kivy/buildozer@76bac28545c66bbcc671d49aca553a747d69608e' 'Cython==0.29.34' setuptools legacy-cgi
buildozer android debug
buildozer android release
```

`bin/` contains the debug APK and unsigned release AAB. The workflow runs Python domain and desktop interaction tests, Android builds and Android 16 UI acceptance. It also captures twelve real framebuffer screenshots. Native libraries must pass the 16 KB page-size checks before a Play upload; this is included in release verification.

## Signing and package ownership

The owner’s [signed `atlas-go-play.aab`](https://drive.google.com/file/d/1-R9rmDFDw9I-X9T3qE15qdI3P5SlU_s2/view) has been verified. Its signature details and SHA-256 are recorded in [SIGNED_VALIDATION.json](../releases/SIGNED_VALIDATION.json). The installable debug APK and unsigned release AAB are in the same [restricted Drive folder](https://drive.google.com/drive/folders/1iio7hs5A7p5sM2GOh3rroG2XemnXw6KV); downloads require approved access. CI builds them from this source, so anyone can also reproduce them. The owner receives the dedicated upload keystore and password in a separate private backup. The signed download can be uploaded as supplied. Sign a rebuilt or unsigned AAB locally using the command below. The private key and password are never committed here. Keep at least two secure backups. Enrol in Play App Signing so Google holds the distribution signing key. Use the same upload key for subsequent bundles unless you perform a Console upload-key reset.

Before first upload, decide whether to keep `org.atlas.mobility`. Application IDs must be available in Play and cannot be changed for the same listed app. Change `package.name` and `package.domain` in `buildozer.spec` and rebuild if needed. Increment the Buildozer `version` and `android.numeric_version` for future Play updates.

To sign a rebuilt bundle locally:

```bash
buildozer android release
export ATLAS_UPLOAD_KEYSTORE=/absolute/private/path/atlas-upload.p12
export ATLAS_UPLOAD_ALIAS=atlas-upload
# Read the password privately in your shell; do not put it into a Git file.
read -rs ATLAS_UPLOAD_PASSWORD; export ATLAS_UPLOAD_PASSWORD
python scripts/sign-release.py bin/*release.aab releases/atlas-go-play.aab
unset ATLAS_UPLOAD_PASSWORD
```

`sign-release.py` uses JDK `jarsigner`, verifies the signature and does not print the password. The default build does not use the debug key for release. Never place the private key/password into Actions artifacts, logs, source, issue comments or the public repository; encrypted Actions secrets (below) are the only place in GitHub for them. An APK for direct installation must additionally be signed using Android SDK `apksigner`; the public demo APK is already signed for installation; an owner-key release APK can be generated from the signed AAB using bundletool.

### Sign automatically in CI (optional)

The release workflow can sign each tested build for you, so every passing build on `main` also produces a signed `atlas-go-play.aab` for you. The key stays in GitHub's encrypted Actions secrets; it is never written to the repository, logs, artifacts or release files.

1. Make a base64 copy of the keystore on your own computer (it prints nothing secret to the screen):
   - macOS/Linux: `base64 < atlas-upload.p12 | tr -d '\n' > keystore.b64`
   - Windows PowerShell: `[Convert]::ToBase64String([IO.File]::ReadAllBytes("atlas-upload.p12")) | Set-Content keystore.b64`
2. In GitHub open **Settings → Secrets and variables → Actions → New repository secret** and add three secrets:

   | Name | Value |
   |---|---|
   | `ATLAS_UPLOAD_KEYSTORE_BASE64` | the contents of `keystore.b64` |
   | `ATLAS_UPLOAD_ALIAS` | the key alias (for example `atlas-upload`) |
   | `ATLAS_UPLOAD_PASSWORD` | the keystore/key password |

3. Delete `keystore.b64` from your computer.
4. Re-run the latest successful **ATLAS Python Android acceptance** run, or push a change under `android-app/atlas_go`. The publish workflow then signs the tested AAB with [`scripts/ci-sign-bundle.py`](../scripts/ci-sign-bundle.py), checks that its certificate matches `upload_certificate_sha256` in [SIGNED_VALIDATION.json](../releases/SIGNED_VALIDATION.json), and keeps it for two days as the `atlas-go-play-signed` artifact of that publish run. Download it from there and add it to the restricted Drive folder; app files are not attached to public releases. In a public repository, run artifacts can be downloaded by any signed-in GitHub user while they exist, which is why they are kept for only two days. A different key fails the job before anything is published. Without the secrets, builds publish unsigned exactly as before.

To stop CI signing, delete the three secrets. If the key is ever exposed, delete them and request an upload-key reset in Play Console.

## Console steps the owner must finish

1. Use your verified Google Play developer account. Create an app using a truthful name and select **App**, free or paid according to your distribution plan. This demo contains no payment collection.
2. Create an **Internal testing** release, enable Play App Signing, and upload `atlas-go-play.aab`. Review Play's bundle analysis and pre-launch/device reports before broader distribution.
3. Supply your real developer/support contact information and complete the account's identity, organisation/device verification and any testing requirements shown in Console. These cannot be completed from a source repository.
4. Supply a public privacy policy URL. The [versioned policy](PRIVACY.md) is complete for this offline binary; host the same text on your developer website if Console requires it. It must remain readable without login. Add any real support email required by Console yourself.
5. Complete Data safety based on the actual binary: no collection or sharing by this offline app, no ads, no login/account creation, no payment or location permissions. Follow the Console questionnaire wording; reassess every answer if a network SDK or backend is added.
6. Complete the content-rating questionnaire, target-audience declaration, app access declaration (all features accessible without credentials), and any other applicable declarations. Do not select child-directed distribution without reviewing its requirements.
7. Add the screenshots and store graphics below. State clearly that rides, restaurant ordering and tracking are simulations. Do not imply an affiliation with Uber or real Cork restaurants.
8. Fix every blocking Console validation or pre-launch issue. Move from internal to closed/production testing only after your account's requirements are satisfied. Submit for review when ready; upload preparation is not publication.

## Suggested honest listing

Name: **ATLAS Go — Mobility Demo**

Short description: **Explore simulated rides, shared journeys and food ordering in one offline app.**

Full description:

> Explore a Python-powered Android model of a mobility and food application. Preview solo ride fares, join shared journeys with seat availability, browse illustrative restaurant menus, build a basket, and step through simulated ride and delivery tracking. View local activity history and reset demo data whenever you like. Works offline, with no login, ads, location tracking or payment information. All bookings, drivers, restaurants, routes and deliveries are demonstrations. ATLAS Go does not arrange transport or deliver food.

## Listing assets

- `docs/play-assets/icon-512.png`: original 512 × 512 app icon.
- `docs/play-assets/feature-1024x500.png`: original 1024 × 500 feature graphic.
- `docs/screenshots/01-home.png` through `12-privacy.png`: 9:16 portrait phone screenshots from the Android 16 emulator. The capture verifier checks Play dimension/aspect limits; see [the eight-image listing selection and alt text](play-assets/SCREENSHOTS.md). Use the Home, Ride, Share, Food and Basket images for the listing.
- In-app icon: original image `assets/icon.png`.

## Release verification

Check the [download checksums](../releases/SHA256SUMS), [release validation](../releases/VALIDATION.md), and the owner's [signed-bundle record](../releases/SIGNED_VALIDATION.json). Download the APK/AAB files and SHA256SUMS from the same release; check them in the download directory. The signed AAB must also pass signature verification:

```bash
sha256sum -c SHA256SUMS
jarsigner -verify atlas-go-play.aab
```

The Android test device is an emulator. See [the testing report](TESTING.md) for the exact scope and fixes. Physical-device testing, accessibility review with TalkBack, larger font sizes, tablets/foldables, process termination and production security review remain owner release checks. The UI supports scrolling and saves its screen/form selections on navigation and pause, but the emulator run does not prove compatibility with every Android device.

## Official references

Requirements checked 5 November 2026; recheck before uploading:

- [Google Play target API requirements](https://developer.android.com/google/play/requirements/target-sdk): new Android phone apps target API 36 or higher from 31 August 2026.
- [Sign your app and upload key handling](https://developer.android.com/studio/publish/app-signing).
- [Prepare and roll out a release](https://support.google.com/googleplay/android-developer/answer/9859348).
- [Preview assets and screenshots](https://support.google.com/googleplay/android-developer/answer/9866151).
- [Data safety information](https://support.google.com/googleplay/android-developer/answer/10787469).

For a real mobility business, complete the backend, dispatch, merchant, payments, safety, support and operational work in [ARCHITECTURE.md](ARCHITECTURE.md) before changing the demo claim.

## Process limits

Use the existing verified build for signing-only handovers. Native Android CI caches its toolchain, cancels superseded runs on the same branch, and has a 45-minute total limit. Publication has a 10-minute limit. Documentation and signing records do not require another native compilation.
