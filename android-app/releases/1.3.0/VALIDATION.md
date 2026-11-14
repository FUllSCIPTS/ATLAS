# ATLAS Go 1.3.0 validation

Built and tested on 14 November 2026 in GitHub Actions ([run 43601749325](https://github.com/FUllSCIPTS/ATLAS/actions/runs/43601749325)) from source commit `4784c1316603961a77c21a159abf47904a8636e6` (branch `atlas-go-1.3.0`, merged to `main`). The application code in that commit is the code in this release; later commits change documentation only.

## How the binaries were built

Buildozer and python-for-android built the debug APK and the release AAB from source in CI (CPython, Kivy 2.3.1, SDL2, OpenSSL, pyjnius, requests/certifi; NDK 28c; API 36). The release APK is the universal APK that bundletool 1.18.3 produced from that tested AAB, signed with APK Signature Scheme v2 and v3.

## Results

| Check | Result |
|---|---|
| Python unit tests (`python -m pytest tests`, CI) | 158 collected: 157 passed, 1 skipped (the map-refit test needs a display; it passes under `xvfb-run`) |
| Desktop UI acceptance, 440 × 940 | 305 assertions passed, 28 screenshots ([result](ui-results-440x940.json)) |
| Desktop UI acceptance, 360 × 780, font scale 1.2 | 305 assertions passed, 28 screenshots ([result](ui-results-360x780.json)) |
| **Android 16 emulator** (API 36, Pixel 2 profile) | Debug APK installed; **362 assertions passed**, 28 OS screenshots ([result](android-ui-results.json), [screenshots](atlas-go-1.3.0-screenshots.zip)); no `FATAL EXCEPTION` in the crash log |
| Release build launch on the emulator | Non-debuggable release APK starts and stays running for 15 s; `run-as` refused (not debuggable); no crash |
| `bundletool validate` | Pass |
| Manifest (`scripts/check-manifest.py`) | Pass: 1.3.0 / 4, target 36, not debuggable, backup off, only INTERNET, ACCESS_NETWORK_STATE, ACCESS_FINE_LOCATION, ACCESS_COARSE_LOCATION ([manifest](release-manifest.xml)) |
| 16 KB native alignment | 232 libraries pass ([report](native-alignment.txt)) |
| Layer 1 unchanged | `intelligence.py` and `learned.py` byte-identical to 1.2.0 (SHA-256 checked by `tests/test_twin.py`); the six-model self-test passes |
| Layer 2 self-test | 4 of 4 pass on the phone (Twin tab → Check Layer 2) |
| Release APK | Signed v2 and v3, `versionName` 1.3.0, `versionCode` 4, not debuggable; certificate in [README.md](README.md) |

### What the Android run exercises (in addition to every 1.2.0 flow)

- A solo ride: Agent 1 rehearses Layer 1's top three drivers; the Guardian passes the driver and the price; base fare at an ordinary hour.
- A shared ride from booking to arrival: the rider already on board (Ciara), the car starting from where she boarded, the new rider's pickup, Ciara dropped first, the *Complete ride* button only after her drop-off, seats free again.
- The Twin tab: mirror and fidelity, the four Layer 2 checks, the Guardian fault drill (blocked ×4.0 → Layer 1 fallback → 500/500 re-test → handed back), Layer 2 off (booking identical to 1.2.0) and on again.
- St Patrick's Day lunchtime: a ×1.4 capped price passed by the Guardian; the driver's *Twin hint* to move towards the city centre; the kitchen's courier hint.

## Not covered here

Physical phones and tablets, real GPS fixes and the permission dialog on a device, TalkBack and accessibility review, battery and performance profiling, Play pre-launch reports and store review remain owner steps.
