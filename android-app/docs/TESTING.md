# Testing and release evidence (1.3.0)

ATLAS Go 1.3.0 is a Python/Kivy app with on-phone accounts, a live map and simulated rides and deliveries. Tests exercise local accounts, bookings, ordering, seller and driver workflows, live progress and every bundled model. They do not contact live drivers, restaurants, payments, back-end services or ML services; the map-tile path is tested against a local stand-in tile server.

## Automated coverage

| Check | Coverage |
|---|---|
| 158 Python unit tests | 1.3.0 adds 41: the ride map refitting after layout (needs a display: run under `xvfb-run`, otherwise skipped); Layer 1 source byte-identical to 1.2.0 and unchanged answers after Layer 2 runs; foresight from the outlook (including across midnight); Agent 1 limited to Layer 1's top three, deterministic and within the time budget; Agent 2 prices capped, stable and ×1.0 at ordinary times; driver and kitchen hints; Guardian price and dispatch limits (cap, floor, NaN, wrong type, outsider, declined, offline, slow); 500-rollout re-test and the fault drill end to end; Layer 2 on/off/re-testing; priced booking persistence; bounded log; damaged or missing `twin` state; mirror fidelity; the four Layer 2 self-checks; and for shared rides the rider on board on every route, the four-stage order, refusal to drop the new rider early, quarantine of a file with the wrong order, restart at every stage, seats released on arrival and cancel, live positions on each leg, the time-lapse running through all four stages, and 1.2.0 shared rides finishing with three stages. The 117 cases from 1.2.0: the 68 earlier cases (holidays, outlooks, dispatch, courier timing, learning lab, fares, seats, basket, persistence, recovery, rollback) plus: password hashing and verification, sign-in lockout, email/phone/password/plate/licence/business/price validation, registration rules per role, driver accept/decline/advance with earnings and acceptance counts, seller menus, open/closed kitchens, order acceptance and ready-for-courier, time-based live progress for rides and orders, account deletion and anonymisation, quarantine of nine kinds of damaged account/kitchen state, loading 1.1.0 files, Web-Mercator maths against the OSM formula, live positions, registered-driver dispatch, the acceptance model, surge level, courier timing for any preparation time, and the six-model self-test |
| Standard screen configuration | 305 assertions through real Kivy control events at 440 × 940 (1.3.0 adds: twin-tested booking and Guardian checks; a full shared ride with the earlier rider dropped first; the Twin tab, Layer 2 self-checks, fault drill and Layer 2 off/on; a capped busy-time price; the driver twin hint and kitchen hint; 28 screenshots). From 1.2.0: guest rides, shared rides and food; live map and zoom; a journey advancing on its own; the model check; driver, seller and passenger registration with an invalid-email retry; a registered driver chosen by the policy, accepting and completing the trip; a seller accepting an order and handing it to the courier; wrong-password refusal; account deletion; erase-all; 22 screenshots |
| Narrow screen and larger text | The same 305 assertions at 360 × 780 with font scale 1.2 |
| Live map | Tiles fetched from a local tile server, decoded, cached on disk and drawn at the right positions (Cork centre = tile 13/3903/2709); User-Agent header checked; offline schematic layer when tiles are unavailable; drag-to-pan through Kivy's touch pipeline; simulated GPS fix and nearest-pickup text |
| Model retraining | `training/export_learned.py` reproduces `atlas_go/learned.py` byte for byte |
| Release bundle | bundletool validation; manifest: version 1.3.0 / code 4, target 36, not debuggable, backup off, exactly INTERNET, ACCESS_NETWORK_STATE, ACCESS_FINE_LOCATION, ACCESS_COARSE_LOCATION, no background location; location hardware optional |
| Native runtime | All 232 packaged 64-bit ELF libraries aligned to 16 KB |
| Packaged code | The APK's compiled modules load and run on CPython 3.14 (accounts, store, geo, all six models); every Kivy, pyjnius, android and requests module the UI imports is present in the APK's Python bundle |
| APK signature | APK Signature Scheme v2 and v3 verified |
| Android 16 emulator (CI) | On push, the workflow installs the debug APK, runs the same interaction suite on the emulator, captures the screenshots, checks the crash log, then launches a non-debuggable release APK |

The Android debug driver is enabled only when Android marks the APK debuggable and an explicit test launch intent is supplied. The release variant ignores this switch.

## Bugs fixed during this handover

1.3.0:
- On phones the ride map was fitted before layout (at Kivy's default 100 × 100) and showed the whole county; it now refits once the real size is known, until the user pans or zooms.
- Shared seats stayed reserved after a completed shared ride; they are now released on arrival as well as on cancel.
- The acceptance run used the real clock, so prices and surge features could change with the time of day; it now pins an ordinary hour and a busy hour.

1.2.0:
- A ride-request decline without a fallback driver counted as an offer before failing; validation now happens first.
- The app's driver-picking method was named `dispatch`, which shadowed Kivy's event dispatcher and crashed start-up; renamed `pick_driver`.
- Courier timing for kitchens slower than the trained range kept the courier waiting at the counter; the table's edge margin is now extrapolated.
- Registration tabs and map buttons no longer break words on narrow screens with large text.

1.1.0 and earlier:

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

For 1.3.0 the Android 16 emulator run was executed in GitHub Actions before release (see the release validation). Real GPS fixes and the location permission dialog, real OpenStreetMap tile downloads on a phone, physical Android phone/tablet testing, TalkBack and switch-access review, large font settings beyond the tested configuration, battery/performance profiling, Play pre-launch reports, developer identity/listing declarations and any account-specific testing requirements remain owner checks. The model does not provide production transport or food services. Google Play review is a separate process; passing these tests does not guarantee acceptance.
