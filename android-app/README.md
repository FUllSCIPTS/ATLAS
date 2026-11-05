# ATLAS Go — Android model application

**README option 4:** a Python/Kivy Android passenger app for solo rides, shared rides and food ordering, with interactive Python screens and local persistence.

This is a fully runnable **offline demonstration**, not a transport operator. All drivers, restaurants, distances, bookings, payments and tracking stages are simulated. No backend, ML inference, real dispatch, real delivery or payment gateway is connected. The ATLAS architecture and Python service starter remain separate references on the `architecture-explorer` branch.

- [Installable APK and upload bundle](releases/README.md)
- [User guide with real Android screenshots](docs/USER_GUIDE.md)
- [Build, signing and Google Play submission](docs/GOOGLE_PLAY.md)
- [Folder hierarchy, classes and integration blueprint](docs/ARCHITECTURE.md)
- [Privacy notice](docs/PRIVACY.md)
- [Testing scope and fixes](docs/TESTING.md)
- [Automated Android acceptance workflow](https://github.com/FUllSCIPTS/ATLAS/actions/workflows/atlas-android.yml)

## What works

| Area | Working interaction |
|---|---|
| Home | Dashboard with Ride, Share ride and Food entry points and five persistent navigation tabs |
| Solo ride | Pickup/destination selection, Go/Comfort fare estimate, confirmation, simulated progress and cancellation |
| Shared ride | Exact route matching, one/two-seat party selection, capacity validation, reservation and cancellation releasing seats |
| Food | Three restaurants, nine menu items, quantity controls, one-restaurant basket and delivery address |
| Checkout | Exact cent-based totals, delivery fee, simulated order and delivery stages |
| Activity | Completed/cancelled rides and delivered food orders saved across restarts |
| Profile | In-app privacy notice and deletion/reset of all local demo data |

Shared rides are ATLAS carpool bookings: a passenger joins a pre-seeded driver offer on the same route. They do not expose passenger-created public ride listings, dynamic detours or real rider matching. No claim is made about the availability of other companies' services.

## Run from source

For desktop preview, install Python 3.12 and the dependencies below. Android packaging uses Buildozer and python-for-android on Linux/WSL. There are no Java application source files; Android SDK/JDK tooling is used by the packaging tools.

```bash
cd android-app
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest tests
python main.py
# Android package on Linux, after installing build prerequisites:
buildozer android debug
buildozer android release
```

Windows: desktop preview runs directly with Python; Android packaging uses WSL2. See [the packaging guide](docs/GOOGLE_PLAY.md). The workflow pins Buildozer and python-for-android source revisions, API 36 and NDK 28c. Build dependencies require an internet connection; installed demo flows do not.

The owner’s signed `atlas-go-play.aab` has been supplied separately and verified. See [the signed-bundle record](releases/SIGNED_VALIDATION.json). Public CI downloads remain unsigned for reproducible builds. The existing private upload key is retained privately for future updates.

## Validation

The GitHub workflow runs Python domain tests, desktop UI acceptance, APK/AAB builds and actual UI interactions on an Android 16 emulator. It captures twelve screenshots from the Python app and rejects test failures or fatal crash logs. Release evidence and SHA-256 checksums accompany the binaries. No live service, payment, real location or ML accuracy is tested by this workflow.

This is an educational model suitable for an explicitly labelled demo/test distribution. Store acceptance and any later public service launch require the account owner's Console declarations, testing requirements, rights review and service integrations.
