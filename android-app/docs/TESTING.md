# Testing and release evidence

The delivered application is an offline Python/Kivy model. Tests exercise simulated local bookings and ordering; they do not contact live drivers, restaurants, payments, maps, backend services or ML models.

## Automated coverage

| Check | Coverage |
|---|---|
| 40 Python regression cases | Every saved route, Go/Comfort fare symmetry, invalid routes, seat matching and limits, cancellation, basket arithmetic, quantity limits, restaurant isolation, active booking constraints, food/ride coexistence, all persisted journey stages, malformed state recovery, reset and failed-storage rollback |
| Standard screen configuration | 88 assertions through real Kivy button press/release events and spinner callbacks; 440 × 940 desktop viewport |
| Narrow screen and larger text | Same 88 assertions at 360 × 780 with font scale 1.2; control dimensions and twelve framebuffer images verified |
| Android 16 emulator | Installed Python APK runs the interaction suite, writes results and twelve actual app screenshots; fatal crash log checked |
| Release bundle | Bundletool format validation, target SDK, non-debuggable flag, backup disabled and absence of Internet/location/billing permissions |
| Native runtime | Every packaged 64-bit ELF load segment checked for alignment of at least 16 KB |
| Release launch | A non-debuggable APK made from the AAB is installed and launched separately; process survival and fatal crash log checked |

The Android debug driver is enabled only when Android marks the APK debuggable and an explicit test launch intent is supplied. The release variant ignores this switch. The UI driver dispatches real Kivy control events; it is not an OS-level touch, TalkBack or physical-device certification.

## Bugs fixed during this handover

- Desktop startup no longer depends on a pre-existing configuration directory.
- Preview geometry is configured before the graphics surface is created, preventing clipped/black upper screen regions.
- Android uses system screenshots with an acknowledgement handshake; in-app OpenGL readback had produced black capture regions on the emulator.
- Screenshot filenames are normalized, so documentation links point to the real captures.
- Invalid saved booking stages and out-of-range form values recover without crashing the UI.
- Booking, shared-seat, basket and checkout changes roll back in memory if persistence fails.
- Reset removes the quarantined invalid-state file as well as current demo history.
- Android system-bar spacing prevents status and gesture controls from overlapping the app header and navigation.
- Bottom navigation remains readable on a narrow screen with increased text size.
- Android packaging installs the libtool/libltdl development dependencies needed by the Python runtime.
- CI screenshots, results and sample data are excluded from the packaged application.

## Reproduce

```bash
pip install -r requirements-dev.txt
python -m pytest tests
ATLAS_UI_TEST=1 ATLAS_DATA_DIR="$PWD/local-data" python main.py
python scripts/verify-acceptance.py local-data/test-output
```

For a second desktop configuration, set `ATLAS_PREVIEW_SIZE=360x780` and `KIVY_METRICS_FONTSCALE=1.2`, using a fresh data/output directory. The GitHub workflow defines the Linux/Android build environment and runs the full checks. Keep acceptance directories outside release source or excluded in `buildozer.spec`.

See [release validation](../releases/VALIDATION.md) for the exact source revision, successful run, binary checksums and artifact URLs.

## Remaining release work

Physical Android phone/tablet testing, TalkBack and switch-access review, large font settings beyond the tested configuration, battery/performance profiling, Play pre-launch reports, developer identity/listing declarations and any account-specific testing requirements remain owner checks. The model does not provide production transport or food services. Google Play review is a separate process; passing these tests does not guarantee acceptance.
