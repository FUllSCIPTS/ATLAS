# ATLAS Go 1.2.0 validation

Built and checked on 7 November 2026 from the source in this commit (parent `041f315`).

## How the binaries were built

The native runtime (CPython 3.14, Kivy 2.3.1, SDL2, OpenSSL, pyjnius, requests/certifi and the python-for-android Java bootstrap) is the one Buildozer built in CI for the 1.1.0 release bundle (`atlas-go-unsigned.aab`, SHA-256 `478d8143a5e851984837424de34769de072440a249ef1bab157a17647060b2cb`). For 1.2.0 the app's Python sources were compiled the way python-for-android does (CPython 3.14, `-OO`, legacy `.pyc`) into `assets/private.tar`, and the bundle manifest was updated (versionCode 3, versionName 1.2.0, permissions, optional location hardware). bundletool 1.18.3 validated the bundle and produced the signed universal APK from it. The native libraries are byte-identical to 1.1.0.

A clean rebuild from source with Buildozer happens automatically in GitHub Actions when this commit is pushed to `main` (`.github/workflows/atlas-android.yml`), which also runs the Android 16 emulator acceptance and, with the upload-key secrets configured, signs the AAB with the owner's upload key.

## Results

| Check | Result |
|---|---|
| Python unit tests (`python -m pytest tests`) | 117 passed |
| Desktop UI acceptance, 440 × 940 | 247 assertions passed, 22 screenshots ([result](ui-results-440x940.json)) |
| Desktop UI acceptance, 360 × 780, font scale 1.2 | 247 assertions passed, 22 screenshots ([result](ui-results-360x780.json)) |
| Live map against a local tile server | 12 tiles fetched, cached and drawn at the correct positions; `User-Agent: ATLASGo/1.2.0`; GPS dot and nearest-pickup text shown; drag-to-pan moves the view |
| Model retraining | `training/export_learned.py` output identical to the bundled `atlas_go/learned.py` |
| On-device model self-test | 6 of 6 pass (also run from the packaged bytecode) |
| `bundletool validate` | Pass |
| Manifest (`scripts/check-manifest.py`) | Pass: 1.2.0 / 3, target 36, not debuggable, backup off, only INTERNET, ACCESS_NETWORK_STATE, ACCESS_FINE_LOCATION, ACCESS_COARSE_LOCATION ([manifest](release-manifest.xml)) |
| 16 KB native alignment | 232 libraries pass ([report](native-alignment.txt)) |
| Packaged bytecode | Loads and runs on CPython 3.14: accounts, store, geo and all six models; UI modules unmarshal; every Kivy/pyjnius/android/requests module they import is in the APK's Python bundle |
| APK signature | v2 and v3 verified; certificate SHA-256 in [README.md](README.md) |

## Not covered here

The Android emulator and physical-device runs (real location permission dialog, GPS fixes, OpenStreetMap downloads on a phone, touch and keyboard behaviour) were not available in the environment that produced this build; they run in CI on push. TalkBack and accessibility review, tablets, battery and performance profiling, Play pre-launch reports and store review remain owner steps.
