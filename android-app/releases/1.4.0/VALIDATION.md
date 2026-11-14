# ATLAS Go 1.4.0 validation

Built and tested on 14 November 2026 in GitHub Actions ([run 43605521786](https://github.com/FUllSCIPTS/ATLAS/actions/runs/43605521786)) from source commit on branch `atlas-go-1.4.0` (merged to `main`). Later commits change documentation only.

## How the binaries were built

Buildozer and python-for-android built the debug APK and the release AAB from source in CI. The release APK is the universal APK that bundletool 1.18.3 produced from that tested AAB, signed with APK Signature Scheme v2 and v3 using the same key as 1.3.0.

## Results

| Check | Result |
|---|---|
| Python unit tests (CI) | 173 collected: 172 passed, 1 skipped (the map-refit test needs a display; it passes under `xvfb-run`) |
| Desktop UI acceptance, 440 × 940 | 314 assertions passed, 29 screenshots ([result](ui-results-440x940.json)) |
| Desktop UI acceptance, 360 × 780, font scale 1.2 | 314 assertions passed, 29 screenshots ([result](ui-results-360x780.json)) |
| **Android 16 emulator** (API 36) | Debug APK: **373 assertions passed**, 29 OS screenshots ([result](android-ui-results.json), [screenshots](atlas-go-1.4.0-screenshots.zip)); no `FATAL EXCEPTION` |
| Release build launch on the emulator | Non-debuggable release APK starts and stays running; no crash |
| `bundletool validate` · manifest · 16 KB alignment | Pass · 1.4.0 / 5, target 36, not debuggable, backup off, same four permissions ([manifest](release-manifest.xml)) · 232 libraries ([report](native-alignment.txt)) |
| Live LSTM on the phone | Pure-Python forecast equals the numpy training model to 2 × 10⁻⁶ (self-check run on the emulator) |
| Live loop on the phone | Seven city days on the emulator: 168 hours forecast → act → record, 7 nightly updates with held-out validation, state persisted; both loop self-checks pass |
| Training reproducibility | `training/export_lstm.py` rewrites `atlas_go/lstm_weights.py` byte for byte |
| Held-out simulation (Jul–Dec 2026) | Next-hour forecast error 9.3 % (surge recall 0.81, precision 0.65); supply cost 29,896 vs 36,343 for the 1.2 calendar agent (−18 %) and 52,965 with no boost |
| Release APK | Signed v2 + v3 (certificate as 1.3.0), `versionName` 1.4.0, `versionCode` 5, not debuggable |

## Not covered here

The city is simulated. In a live deployment the loop would read real completed and unserved requests from an operator back end. Only the LSTM's output layer is retrained on the phone; its recurrent weights are retrained offline with `training/export_lstm.py`. Physical-device testing, accessibility review, battery profiling and Play review remain owner steps.
