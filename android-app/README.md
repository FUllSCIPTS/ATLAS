# ATLAS Go — Android app (version 1.6.0)

**README option 4:** a Python/Kivy Android app for Cork with three kinds of account — **passengers**, **drivers** and **food sellers** — a **live map**, solo and shared rides, food ordering, **bank payments and payouts** (new in 1.5.0), an optional **PostgreSQL back end** (new in 1.5.0), on-device ATLAS intelligence (Layer 1: learned dispatch, acceptance, surge outlook, supply boost, courier timing, a learning lab and the live LSTM → RL loop) and a digital twin of Cork with three agents on top (Layer 2).

ATLAS Go works entirely on the phone: accounts, rides, orders, kitchens and payments are stored in private app storage, and several accounts can live on one phone. From 1.5.0 an account can also be **connected to an ATLAS server**, which keeps accounts, bank mandates, payments and payouts in PostgreSQL ([`server/`](server/README.md)). Rides and deliveries are simulated. Bank payments use a **sandbox bank**: IBANs are checked for real, but no bank is contacted and no money moves (see [What "production ready" covers](#what-production-ready-covers)).

- **Source code 1.6.0, open under the [MIT licence](../LICENSE):** browse it here in [`android-app/`](.) — app in [`atlas_go/`](atlas_go/), server in [`server/`](server/)
- **Installable APK:** the latest APK in the [ATLAS Go downloads folder on Google Drive](https://drive.google.com/drive/folders/1iio7hs5A7p5sM2GOh3rroG2XemnXw6KV) (request access) is **1.4.0** (SHA-256 `f0a6d6472c2e0aeec3b3770e112cbd0d4a474f66e3810886f89ec0498ee50977`). The 1.5.0 APK is built and tested by the [Android workflow](../.github/workflows/atlas-android.yml) on every push; the owner uploads it to Drive after reviewing that run. 1.5.0 reads 1.4.0 data.
- [1.4.0 release page](releases/1.4.0/README.md) · earlier: [1.3.0](releases/1.3.0/README.md) · [1.2.0](releases/1.2.0/README.md)
- [User guide with screenshots of every screen](docs/USER_GUIDE.md)
- [What changed in 1.6.0](CHANGELOG.md)
- [Folder hierarchy, classes and integration blueprint](docs/ARCHITECTURE.md) · [UML blueprint catalogue](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/docs/UML_BLUEPRINT.md#android-app-atlas-go)
- [Privacy notice](docs/PRIVACY.md) · [Testing](docs/TESTING.md) · [Build, signing and Google Play](docs/GOOGLE_PLAY.md)
- [▶ Demo video with the digital twin and multi-agent layer (7 min 39 s, version 1.3)](docs/video/atlas-go-demo-v1.3-twin.mp4) · [demo of 1.1.0 (4 min 52 s)](docs/video/atlas-go-demo.mp4)

## What's new in 1.6.0 — pre-booked rides and SOS

| Asked of the app | 1.5.0 | 1.6.0 |
|---|---|---|
| Pre-book an ordinary ride | Not implemented (rides start at once) | **Implemented:** choose a pickup time 15 minutes to 7 days ahead; the fare is fixed at the ordinary fare; a driver is chosen 10 minutes before pickup |
| Pre-book a shared ride | Not implemented | **Implemented:** one or two seats are held from the moment you pre-book and released if you cancel |
| SOS | Not implemented | **Implemented:** a red SOS button during a ride for passengers and drivers; it records ride, time and place and offers one tap to call 112 and one tap to text a trusted contact |

**Pre-booking.** The ride and shared-ride screens have a **When** choice. With a later time the button becomes **Pre-book ride** or **Pre-book seat**. Upcoming pre-bookings (at most three per account) are listed on Home and Activity and can be cancelled free of charge. Ten minutes before the pickup time the pre-booking goes through the ordinary booking path: the dispatch policy picks the driver, and if you chose to pay by bank the bank is asked then. A declined payment marks the pre-booking *failed* and charges nothing. The app must be open and signed in around the pickup time; a pre-booking that cannot start within 30 minutes is marked *missed*.

**SOS.** During a ride the passenger (guest or account) and the registered driver have **SOS · emergency help**. After a confirmation it records where and when, and opens the Emergency screen: **Call 112** opens the phone's dialler with the number filled in, and **Message my trusted contact** opens the messaging app with your name, route, driver, time and a map link. You place the call and send the text yourself, so the app needs no call or SMS permission. Ending an SOS needs the account password. ATLAS Go has no control room, and the screen says so: nobody is alerted until you call or send. Save the trusted contact in **You → Safety & SOS**.

| Pre-book a ride | Pre-booked rides in Activity | SOS |
|---|---|---|
| <img src="docs/screenshots/34-prebook-ride.png" width="180" alt="Ride screen with When set to In 1 hour and a Pre-book ride button"> | <img src="docs/screenshots/35-prebooked-rides.png" width="180" alt="Activity listing a pre-booked ordinary ride and a pre-booked shared ride"> | <img src="docs/screenshots/36-sos.png" width="180" alt="Emergency screen: Call 112, message the trusted contact, recorded position"> |

Source: [`atlas_go/safety.py`](atlas_go/safety.py), the *pre-booked rides* and *SOS* sections of [`atlas_go/store.py`](atlas_go/store.py) and [`atlas_go/app.py`](atlas_go/app.py), and [`tests/test_prebook_sos.py`](tests/test_prebook_sos.py).

## What's new in 1.5.0 — bank payments and a PostgreSQL back end

| Asked of the app | 1.4.0 | 1.5.0 |
|---|---|---|
| User registration (passenger, driver, food seller) | On the phone | On the phone **and**, when connected, on the server (`POST /v1/accounts`) |
| Bank payment option for passengers | Not implemented (payments simulated) | **Implemented (sandbox bank):** link an IBAN with a Direct Debit mandate; pay rides, shared rides and food by bank |
| Bank payment option for drivers | Not implemented | **Implemented (sandbox bank):** fare minus the 15 % ATLAS fee is credited; balance paid out to the driver's IBAN |
| Bank payment option for food sellers | Not implemented | **Implemented (sandbox bank):** food total minus 10 % is credited; balance paid out to the seller's IBAN |
| Back end using PostgreSQL | Not implemented (one `state.json` per phone) | **Implemented:** [`server/`](server/README.md) — accounts, sessions, bank accounts, payments, ledger, payouts, outbox and audit log in PostgreSQL |

**On the phone.** *You → Bank & payments* links a bank account: the IBAN is checked (country, length, mod-97 check digits), the passenger ticks the mandate, and the password is asked again. Booking screens then offer **Pay with: Bank account IE29 •••• 5678 / Demo · no charge**. The payment is *authorised* at booking, *captured* on arrival or delivery, and *voided* on cancel. Drivers and sellers see their balance and **Pay out** to their bank. Only the holder, country and last four characters of the IBAN are saved.

**On the server.** The phone never sends an amount: it sends the booking (route, option, busy-time multiplier, or dishes and quantities) and the server prices it with the same `atlas_go/payments.py` rules. Each payment carries the phone's payment id as its `Idempotency-Key`. PostgreSQL triggers make the ledger append-only and refuse a transaction whose debits and credits differ.

| Link a bank account | Pay by bank | Driver balance and payout |
|---|---|---|
| <img src="docs/screenshots/31-bank-link.png" width="180" alt="Bank and payments: link an IBAN with a Direct Debit mandate"> | <img src="docs/screenshots/32-pay-by-bank.png" width="180" alt="Booking a ride with Pay with: bank account"> | <img src="docs/screenshots/33-driver-payout.png" width="180" alt="Driver balance and payout to a bank account"> |

```bash
# a local server and a phone preview connected to it (two terminals, from android-app/)
python -m pip install -r server/requirements.txt -r requirements-dev.txt
DATABASE_URL=postgresql://USER:PASSWORD@127.0.0.1:5432/atlas ATLAS_BANK_PEPPER=$(python -c "import secrets; print(secrets.token_hex(32))") \
  python -m uvicorn --factory server.app:from_env --port 8080
ATLAS_API_URL=http://127.0.0.1:8080 python main.py      # then You → Bank & payments → Connect this account
```

## What's new in 1.4.0 — the Layer 1 live loop

**LSTM predicts demand → RL agent chooses actions → actual outcomes are recorded → both models are periodically updated and validated** — now running on the phone (`atlas_go/loop.py`, pure Python).

| Component | 1.3.0 | 1.4.0 | 1.6.0 |
|---|---|---|---|
| LSTM training implementation | Present (`training/city_sim.py`) | Present; plus `training/export_lstm.py` for the on-device LSTM | Unchanged |
| RL agent training implementation | Present (`training/city_sim.py`, `training/rl_sim.py`) | Present; plus the forecast-aware supply agent | Unchanged |
| RL experience used to train the LSTM | Connected (simulation) | Connected, offline **and** on the phone | Unchanged |
| LSTM forecast feature in dispatch | Represented (fixed hourly tables) | **Live**: the LSTM's next-hour forecast is the dispatch surge feature | Unchanged |
| Live LSTM inference feeding the on-device RL agent | Not implemented | **Implemented**: every city hour, 24 h window → 6 h forecast → agent's state | Unchanged |
| Continuous online LSTM–RL retraining | Not implemented | **Implemented**: agent hourly (challenger), LSTM output layer nightly; champion/challenger validation on held-out hours | Unchanged |

**App components, 1.3.0 → 1.6.0**

| Component | 1.3.0 | 1.4.0 | 1.6.0 |
|---|---|---|---|
| User registration (passenger, driver, food seller) | On the phone | On the phone | On the phone and, when connected, on the server (since 1.5.0) |
| Bank payment option for passengers, drivers and food sellers | Not implemented | Not implemented | **Implemented** (sandbox bank, since 1.5.0): pay by bank, balances, payouts |
| Back end using PostgreSQL | Not implemented | Not implemented | **Implemented** (since 1.5.0): [`server/`](server/README.md), optional |
| Pre-book an ordinary ride | Not implemented | Not implemented | **Implemented**: 15 minutes to 7 days ahead, fare fixed, driver chosen 10 minutes before pickup |
| Pre-book a shared ride | Not implemented | Not implemented | **Implemented**: seats held from the moment you pre-book |
| SOS during a ride, trusted contact | Not implemented | Not implemented | **Implemented**: records ride, time and place; opens the dialler on 112 and a text to your contact; no new permission |
| Android permissions | 4 | 4 | 4 |


Held-out simulation (Jul–Dec 2026): next-hour forecast error 9.3 %; supply cost −18 % against the 1.2 calendar agent. Intelligence → **Live loop** shows the forecast, the agent's decision, the model versions and each night's accept/reject; **Run 7 city days** runs a week of the loop.

<img src="docs/screenshots/30-live-loop.png" width="200" alt="Live loop card">

## What's new in 1.3.0

| Area | What works |
|---|---|
| Two layers | **Layer 1** is the 1.2.0 intelligence, unchanged (`intelligence.py` and `learned.py` are byte-identical and a test checks it). **Layer 2** (`twin.py`) sits on top and only reads Layer 1's forecast, ranking and cost model. Switch Layer 2 off in the Twin tab and the app behaves exactly as 1.2.0. |
| Digital twin | Mirrors every driver, the active car and the courier with a fidelity score, and foresees the next 30 minutes per pickup place from Layer 1's surge outlook. |
| Agent 1 · Dispatch | Rehearses Layer 1's top three drivers 200 times each in the twin (rider wait, declines, riders left waiting if a busy area loses its last car) and sends the lowest total wait. Riders see *Rehearsed in the city twin* and *Twin-tested*. |
| Agent 2 · Pricing + moves | Rehearses three plans per area every five minutes; capped surge (never above ×2.0, ×1.0 at ordinary times). Drivers get a *Twin hint* (move, stay or no move needed); kitchens get the courier's twin ETA and when to start cooking. |
| Agent 3 · Guardian | Checks every decision against hard limits and a 250 ms budget, blocks anything unsafe (e.g. a ×4 price), falls back to Layer 1, re-tests the agent 500 times in the twin and hands control back. **Twin tab:** mirror, foresight, both layers, Guardian log, *Run Guardian fault drill*, *Check Layer 2*. |
| Shared rides | Each shared car already has a rider on board. The new rider waits while the driver comes with that rider, boards, and is **dropped only after the earlier rider's drop-off** — shown as a stop checklist and on the map, and enforced by the app. Seats are released on arrival as well as on cancel. |

| Twin-tested ride | Shared car: earlier rider first | Twin tab | Guardian log | Driver twin hint |
|---|---|---|---|---|
| <img src="docs/screenshots/04-ride-live.png" width="150"> | <img src="docs/screenshots/25-shared-co-drop.png" width="150"> | <img src="docs/screenshots/26-twin-tab.png" width="150"> | <img src="docs/screenshots/27-guardian-log.png" width="150"> | <img src="docs/screenshots/29-driver-twin-hint.png" width="150"> |

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

`python training/export_lstm.py` (development only, needs numpy) trains the on-device LSTM and the forecast-aware supply agent and rewrites `atlas_go/lstm_weights.py` (reproducible byte for byte). `python training/export_learned.py` (development only, needs numpy) retrains the dispatch and courier policies and the two-year city simulation and rewrites `atlas_go/learned.py`. For 1.2.0 this was re-run and reproduced the bundled file byte for byte. The training data is synthetic; the models are illustrative, not measurements of real riders, drivers or kitchens.

## Try the three roles on one phone

1. **Create an account → Driver.** Choose *UCC Campus* as the starting area, create the account and tap **Go online**. Sign out (You → Sign out); the driver stays online for dispatch.
2. **Create an account → Food seller.** Register a kitchen, open **Menu** and add a dish. Sign out.
3. **Create an account → Passenger.** Book a ride from UCC Campus: ATLAS picks your registered driver (nearest, likely to accept). Then order the seller's dish from **Food**. Sign out.
4. **Sign in as the driver** to accept the request and drive the trip. **Sign in as the seller** to accept the order and mark it ready. **Sign in as the passenger** to follow the courier on the live map until delivery.

## What "production ready" covers

Done: input validation on every form, hashed passwords with lockout, crash-safe atomic storage with validation and quarantine of damaged files, rollback when a write fails, migration of earlier data, runtime location permission (foreground only), a non-debuggable release build signed with APK Signature Scheme v2/v3, 16 KB native alignment for Android 15+, privacy notice and account deletion; and in 1.5.0 the payment lifecycle, ledger and payout rules on the phone, and a PostgreSQL server for accounts, bank details, payments and payouts with its own tests.

Still needed before carrying real passengers or food — these are business and infrastructure steps, not app code:

- **Matching between phones.** The 1.5.0 server holds accounts and money, but rides and orders are still per phone: a passenger on one phone cannot yet be matched to a driver on another. That needs the trip and dispatch services of the [`architecture-explorer` starter](https://github.com/FUllSCIPTS/ATLAS/tree/architecture-explorer/architecture-explorer/starter) behind the same accounts.
- **Scheduling on a server.** Pre-booked rides are dispatched by the app on the passenger's phone, so it must be open around the pickup time. A real service schedules them on the server, reminds the passenger with a push notification and assigns a driver even when the phone is off.
- **A monitored SOS.** SOS records the event and helps the user call 112 and text a trusted contact. A real service adds a staffed safety line or a partner monitoring centre, live trip sharing from the server, and a procedure agreed with the emergency services.
- **Verification.** SPSV licences, vehicle registrations and food business registrations are format-checked only. A real launch needs NTA licence checks, insurance, and food-business registration with the competent authority.
- **A licensed payment provider.** The bank is a sandbox. Real debits and payouts need a PSD2 provider (SEPA Direct Debit or open-banking payments) behind `server/bank.py`, strong customer authentication at mandate set-up, handling of returned debits and refunds, and reconciliation ([what that involves](server/README.md#before-real-money)).
- **TLS for the server.** The app refuses plain `http://` except to a local test machine; deploy the server behind HTTPS.
- **Map tiles.** The default tile server is OpenStreetMap's community server, which suits light use only. A production launch should use a commercial tile provider (`ATLAS_TILE_URL` changes the source).
- **Store review and physical-device testing.** See [Testing](docs/TESTING.md) and [Google Play](docs/GOOGLE_PLAY.md).

## Run from source

Desktop preview needs Python 3.12+; Android packaging uses Buildozer and python-for-android on Linux/WSL.

```bash
cd android-app
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest tests                       # 244 tests (one needs a display: xvfb-run)
ATLAS_TEST_DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5432/postgres python -m pytest server/tests   # 59 server tests on PostgreSQL
python main.py                               # desktop preview
ATLAS_FAKE_GPS=51.8990,-8.4700 python main.py  # preview with a simulated location
ATLAS_CLOCK=2027-03-17T13:00 python main.py     # preview the twin at a busy time (St Patrick's Day)
# Android packages (Linux, after installing build prerequisites):
buildozer android debug
buildozer android release
```

Pushing to `main` runs the [Android workflow](../.github/workflows/atlas-android.yml): unit tests, two desktop UI acceptance runs, Buildozer APK/AAB builds, bundle validation and the Android 16 emulator click-through with screenshots. Changes to the server or the shared rules also run the [server workflow](../.github/workflows/atlas-server.yml) against PostgreSQL 16. When the upload-key secrets are configured, the release workflow signs the AAB with the owner's upload key.

## Validation

| Check | 1.6.0 (run for this change, 17 November 2026) | 1.5.0 |
|---|---|---|
| Python unit tests | 300 (299 passed + 1 display-only test skipped without a display) | 244 |
| Desktop UI acceptance, 440 × 940 and 360 × 780 at font scale 1.2 | 412 assertions and 35 screenshots in each | 353 and 32 |
| Server tests on PostgreSQL 16 | 59 passed (server unchanged in 1.6.0) | 59 passed, including a six-way idempotency race, a four-way payout race, the ledger triggers and the least-privilege role |
| Connected mode | Not re-run for 1.6.0 (the server and `backend.py` are unchanged) | The Kivy screens against a live server: 71 assertions |
| **Android 16 emulator (CI)** | 483 assertions, 35 OS screenshots, no crash ([run](https://github.com/FUllSCIPTS/ATLAS/actions/runs/44033764144), [evidence](releases/VALIDATION.md)) | 418 assertions, 32 OS screenshots, no crash |
| Release bundle, 16 KB alignment, APK signature | validated in the same run: AAB checked by bundletool, 232 libraries 16 KB-aligned, release variant installed and launched | validated in the 1.5.0 run |
| Live loop and held-out simulation | Unchanged code and results | Unchanged code and results |

The Docker files in `server/` were written but not run for this change (no Docker daemon was available); the server was started from the same file set the image copies and tested against PostgreSQL 16 directly.
