# ATLAS Go — Android app (version 1.2.0)

**README option 4:** a Python/Kivy Android app for Cork with three kinds of account — **passengers**, **drivers** and **food sellers** — a **live map**, solo and shared rides, food ordering, and on-device ATLAS intelligence (learned dispatch, acceptance, surge outlook, supply boost, courier timing and a learning lab).

ATLAS Go 1.2.0 runs entirely on the phone. Accounts, rides, orders and kitchens are stored in private app storage. Several accounts can live on one phone, so a passenger can book a ride that a driver account on the same phone accepts, and order from a kitchen that a seller account on the same phone runs. Rides, deliveries and payments are simulated; no operator back end, payment provider or identity check is connected yet (see [What "production ready" covers](#what-production-ready-covers)).

- [Installable APK 1.2.0 on Google Drive — request access](https://drive.google.com/file/d/1lX5DF9e8ierusJ1OCuVHkeqeCoBgqQfq/view): open the link, click **Request access**; the owner approves by email
- **Source code, open under the [MIT licence](../LICENSE):** browse it here in [`android-app/`](.) or [download atlas-go-1.2.0-source.zip](https://github.com/FUllSCIPTS/ATLAS/releases/download/atlas-go-v1.2.0/atlas-go-1.2.0-source.zip) (SHA-256 `b6339df38ed47b5126306e57aa29e72227796c558a26cfae8b7b224f0e4d9fcb`)
- [1.2.0 release page: SHA256SUMS, release notes and validation](releases/1.2.0/README.md)
- [User guide with screenshots of every screen](docs/USER_GUIDE.md)
- [What changed in 1.2.0](CHANGELOG.md)
- [Folder hierarchy, classes and integration blueprint](docs/ARCHITECTURE.md) · [UML blueprint catalogue](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/docs/UML_BLUEPRINT.md#android-app-atlas-go)
- [Privacy notice](docs/PRIVACY.md) · [Testing](docs/TESTING.md) · [Build, signing and Google Play](docs/GOOGLE_PLAY.md)
- [▶ Demo video of 1.1.0 (4 min 52 s)](docs/video/atlas-go-demo.mp4)

## What's new in 1.2.0

| Area | What works |
|---|---|
| Accounts | Welcome screen with **Create an account**, **Sign in** and **Continue as a guest passenger**. Passwords are stored only as salted PBKDF2-HMAC-SHA256 hashes (200,000 iterations); five wrong passwords lock sign-in for 60 seconds. Email, Irish/international mobile numbers (normalised to E.164) and password strength are validated. **Delete my account** (password confirmation) and **Erase all data** are in You. |
| Passenger registration | Name, email, mobile and password. History, rides and orders belong to the signed-in passenger. |
| Driver registration | Vehicle, Irish registration (e.g. `241-C-1234`), SPSV driver licence number, seats and usual starting area. Drivers go online/offline, use their phone location, receive ride requests from ATLAS dispatch, accept or decline, then mark *arrived*, *start trip* and *complete trip*. Trips, fares and acceptance rate are tracked. |
| Food seller registration | Kitchen name, cuisine, food business registration number, location and preparation time. Sellers add and remove dishes (prices in euro, stored as cents), open or close the kitchen, accept orders and mark food ready for the courier. Orders and sales are tracked. Open kitchens with dishes appear in Food for passengers. |
| Live map | OpenStreetMap tiles with pan (drag), zoom (+/−, double tap) and an on-device tile cache; a schematic Cork map takes over automatically when offline. Shows pickup places, nearby drivers moving in real time, registered drivers who are online, kitchens, the active ride's car and route, the courier, and **your location** (blue dot with accuracy) after you allow it. |
| Live journeys | Rides and deliveries now move on their own in a 10× time-lapse: the car drives to the pickup, waits, then drives to the destination; the courier waits for the kitchen, then rides to you. The ride and order screens embed the live map with an ETA. *Skip to next stage* still jumps ahead. |
| ATLAS intelligence | All six models are wired into the live flows and can be checked on the phone (**How ATLAS learns → Check all models**). Registered drivers compete with the simulated fleet in the dispatch policy, using their real distance to the pickup, a per-driver acceptance model that learns from their accept/decline history, and the surge forecast for the current hour. Courier timing uses each seller's own preparation time. |

### Models in the app

| Model | Method | Used for |
|---|---|---|
| Dispatch policy v1.4 | REINFORCE softmax over four driver features, 30,000 simulated rides | Choosing and explaining the driver for every solo ride, including registered drivers |
| Acceptance model | Beta(9, 1) prior updated with each registered driver's accept/decline history | The *likely to accept* feature for registered drivers |
| Surge outlook | Hourly demand learned from two simulated years of Cork with Ireland's public holidays | Intelligence screen, home and driver cards, the *area surge* dispatch feature, busy-period notice on fares |
| Supply agent | Learned extra-driver boost per calendar context and hour | Violet marks on the outlook; *when to drive* advice for drivers |
| Courier timing | Q-learning table from kitchen slack to dispatch delay (extrapolated beyond the trained range for slow kitchens) | Basket, order and seller screens; saved with each order |
| Learning lab | On-device REINFORCE retraining from zero (sandbox) | Intelligence screen; never dispatches |

`python training/export_learned.py` (development only, needs numpy) retrains the dispatch and courier policies and the two-year city simulation and rewrites `atlas_go/learned.py`. For 1.2.0 this was re-run and reproduced the bundled file byte for byte. The training data is synthetic; the models are illustrative, not measurements of real riders, drivers or kitchens.

## Try the three roles on one phone

1. **Create an account → Driver.** Choose *UCC Campus* as the starting area, create the account and tap **Go online**. Sign out (You → Sign out); the driver stays online for dispatch.
2. **Create an account → Food seller.** Register a kitchen, open **Menu** and add a dish. Sign out.
3. **Create an account → Passenger.** Book a ride from UCC Campus: ATLAS picks your registered driver (nearest, likely to accept). Then order the seller's dish from **Food**. Sign out.
4. **Sign in as the driver** to accept the request and drive the trip. **Sign in as the seller** to accept the order and mark it ready. **Sign in as the passenger** to follow the courier on the live map until delivery.

## What "production ready" covers

Done in this release: input validation on every form, hashed passwords with lockout, crash-safe atomic storage with validation and quarantine of damaged files, rollback when a write fails, migration of 1.1.0 data, runtime location permission (foreground only), a non-debuggable release build signed with APK Signature Scheme v2/v3, 16 KB native alignment for Android 15+, privacy notice and account deletion, and 117 unit tests plus 247 UI assertions in two screen configurations.

Still needed before carrying real passengers or food — these are business and infrastructure steps, not app code:

- **Operator back end.** Accounts and bookings are per phone. Real matching between different phones needs the ATLAS server (the [`architecture-explorer` starter](https://github.com/FUllSCIPTS/ATLAS/tree/architecture-explorer/architecture-explorer/starter) has trip, dispatch and model services; food and accounts APIs are proposed in the UML blueprint).
- **Verification.** SPSV licences, vehicle registrations and food business registrations are format-checked only. A real launch needs NTA licence checks, insurance, and food-business registration with the competent authority.
- **Payments.** All fares and totals are simulated. A payment provider (PSD2/SCA) is required.
- **Map tiles.** The default tile server is OpenStreetMap's community server, which suits light use only. A production launch should use a commercial tile provider (`ATLAS_TILE_URL` changes the source).
- **Store review and physical-device testing.** See [Testing](docs/TESTING.md) and [Google Play](docs/GOOGLE_PLAY.md).

## Run from source

Desktop preview needs Python 3.12+; Android packaging uses Buildozer and python-for-android on Linux/WSL.

```bash
cd android-app
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest tests                       # 117 tests
python main.py                               # desktop preview
ATLAS_FAKE_GPS=51.8990,-8.4700 python main.py  # preview with a simulated location
# Android packages (Linux, after installing build prerequisites):
buildozer android debug
buildozer android release
```

Pushing to `main` runs the [Android workflow](../.github/workflows/atlas-android.yml): unit tests, two desktop UI acceptance runs, Buildozer APK/AAB builds, bundle validation and the Android 16 emulator click-through with screenshots. When the upload-key secrets are configured, the release workflow signs the AAB with the owner's upload key.

## Validation

| Check | Result (1.2.0) |
|---|---|
| Python unit tests | 117 passed |
| Desktop UI acceptance, 440 × 940 | 247 assertions, 22 screenshots |
| Desktop UI acceptance, 360 × 780 at font scale 1.2 | 247 assertions, 22 screenshots |
| Model retraining | `export_learned.py` reproduces `learned.py` byte for byte |
| Packaged bytecode | The APK's compiled modules run on CPython 3.14 (domain, accounts, store, geo, all six models) |
| Release bundle | bundletool validation, manifest check (version 1.2.0 / code 3, not debuggable, backup off, foreground-only permissions), 232 native libraries aligned to 16 KB |
| APK signature | APK Signature Scheme v2 and v3 verified |

The Android 16 emulator run happens in GitHub Actions after the code is pushed; it was not available in the environment that produced this release. Details: [releases/1.2.0/VALIDATION.md](releases/1.2.0/VALIDATION.md).
