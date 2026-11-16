# ATLAS Go changelog

## 1.5.0 (versionCode 6) — 16 November 2026

### Added
- **Bank payments** (`atlas_go/payments.py`) for the three kinds of account, with a sandbox bank (IBANs are validated for real; no money moves).
  - **Passengers** link a bank account in **You → Bank & payments**: account holder, IBAN (country, length and mod-97 check digits verified), a SEPA Direct Debit mandate to tick, and the password again. Rides, shared rides and food orders can then be paid **by bank** or with the demo checkout (*Pay with* on the booking and basket screens). The bank is asked when you book (*authorised*), the money is taken when you arrive or the food is delivered (*captured*), and cancelling releases it (*voided*). A declined payment books nothing.
  - **Drivers and food sellers** link the account they are paid to, see a **balance** on their home screen and in Bank & payments, and **pay it out** to their bank (password required). A ride pays the driver the fare minus a 15 % ATLAS fee; a food order pays the seller the food total minus 10 % (the €2.50 delivery fee stays with ATLAS).
  - The full IBAN is used once and never saved: the phone keeps the holder, country, bank and last four characters (`IE29 •••• 5678`) and the mandate reference.
  - A double-entry ledger is derived from the payment and payout records; `LocalStore.validate` refuses a saved file whose ledger does not balance, whose payouts exceed earnings, or whose bookings and payments disagree.
- **ATLAS server with PostgreSQL** ([`server/`](server/README.md)): FastAPI + psycopg 3. Registration and sign-in for passengers, drivers and sellers (PBKDF2 at 600,000 iterations, uniform sign-in errors, lockout, hashed session tokens), bank accounts (the IBAN goes to the bank provider and only a token, the last four characters and a keyed fingerprint are stored), payments priced by the server from the booking, an append-only double-entry ledger guarded by database triggers, payouts under a row lock, account erasure, an outbox and an audit log. 59 tests run against a real PostgreSQL.
- **Connecting the app to the server** (`atlas_go/backend.py`): enter the server address in **You → Bank & payments → ATLAS server** and connect the account with your password (registration connects automatically once an address is saved). Bank accounts are then linked on the server first; captured payments are copied to it in the background with the payment's own id as the `Idempotency-Key`, so a lost reply never charges twice; payouts are made on the server first. Without a server address nothing is sent and the app works exactly as before.
- Screens: *Bank & payments* (all roles), the *Pay with* card on ride, shared-ride and basket screens, payment status on rides, orders and Activity, and a balance card for drivers and sellers.

### Changed
- `LocalStore.book` and `LocalStore.checkout` take `pay_by_bank`; completing, cancelling and delivering move the payment through its states. `delete_account` is refused while a balance is waiting to be paid out, and removes the passenger from their payment records.
- `state.json` adds `payments`, `payouts` and `server_url`; accounts may hold `bank` and `server`.
- Privacy notice (in the app and in `docs/PRIVACY.md`) covers bank details and the optional server.
- 244 unit tests (71 new); the desktop acceptance run has 353 assertions and 32 screenshots (39 and 3 new).

### Unchanged
- `intelligence.py` and `learned.py` are still byte-identical to 1.2.0; Layer 1's loop and Layer 2's twin are untouched. With no bank account linked, booking behaves exactly as in 1.4.0.
- Android permissions are the same four; payments add none.

### Compatibility
- 1.4.0, 1.3.0, 1.2.0 and 1.1.0 `state.json` files load unchanged (no payments, no server).
- Bank payments are a sandbox for the app's own rides and food (physical services), not Google Play billing.

## 1.4.0 (versionCode 5) — 14 November 2026

### Added
- **Layer 1 live loop** (`atlas_go/loop.py`): *LSTM predicts demand → RL supply agent acts → outcomes are recorded → both models are updated and validated*, running on the phone in pure Python.
  - **Live LSTM inference.** A compact LSTM (24 hours in, 16 hidden units, 1–6 hours out) runs every city hour on the last 24 hours of served trips, unserved requests, supply boosts and the calendar. Its pure-Python forecast matches the training model to within 2 × 10⁻⁶.
  - **The RL agent acts on the forecast.** The supply agent's state is the calendar context *and the LSTM's forecast level* for the coming hour (8 levels); it chooses how many extra drivers to add (0–150 %).
  - **Outcomes are recorded** in an experience log on the phone (14 days): demand, served, unserved, idle drivers, the forecast that was made and the LSTM's hidden state.
  - **Continuous, validated retraining.** Every hour the agent's challenger Q-table learns with hindsight from the log; every night the LSTM's output layer is refitted on the logged hidden states and the demand that followed. Each challenger replaces the champion only if it does better on held-out data (LSTM: weighted error on the last 24 hours; agent: cost replayed over the last 7 days). Versions and every accept/reject are shown.
  - The live LSTM forecast now feeds the dispatch policy's *area surge* feature for registered drivers (previously the fixed hourly outlook), the driver's *When to drive* card and the Twin tab.
- `training/export_lstm.py` trains the compact LSTM on the 1.2 agent's experience log (city_sim "model B": RL experience → LSTM training data) and the forecast-aware supply agent, evaluates both on the held-out second half of 2026 and writes `atlas_go/lstm_weights.py`. Re-running it reproduces the file byte for byte.
- Intelligence screen: **Live loop** card (next-hour and 6-hour forecast, the agent's decision, model versions, nightly update results), **Run 7 city days** and **Check the loop** (2 self-checks).

### Results (simulation)
- Held-out Jul–Dec 2026: LSTM next-hour error 9.3 % (surge recall 0.81, precision 0.65); supply cost (unserved + 0.25 × idle) 29,896 for the LSTM-informed agent vs 36,343 for the 1.2 calendar agent (−18 %) and 52,965 with no boost; unserved requests −18 %.
- On the phone, over four simulated periods (Jazz weekend, St Patrick's Day, Christmas, February), the running loop's cost is lower than the 1.2 calendar agent's (a unit test checks it).

### Unchanged
- `intelligence.py` and `learned.py` (the 1.2 learned tables) are still byte-identical; the loop is new code that reads them. Layer 2 is unchanged.
- The full LSTM (recurrent weights) is retrained offline with `training/export_lstm.py`; on the phone only its output layer is retrained.

## 1.3.0 (versionCode 4) — 14 November 2026

### Added
- **Layer 2: the city twin** (`atlas_go/twin.py`). A digital twin of Cork mirrors the drivers, the active car and the courier (with a fidelity score) and foresees the next 30 minutes per pickup place from Layer 1's surge outlook. Three agents work on top of Layer 1:
  - **Agent 1 · Dispatch** takes Layer 1's top three drivers and rehearses each one 200 times in the twin (rider wait, declines, and the riders left waiting if a busy area loses its last free car); the lowest total wait is sent.
  - **Agent 2 · Pricing and repositioning** rehearses three plans per area every five minutes (keep prices; surge only; small surge plus moving idle cars) with a ×2.0 cap, and gives drivers a *Twin hint* (move, stay or no move needed).
  - **Agent 3 · Guardian** checks every decision: Layer 1's top three only, no driver who declined or went offline, pickup not far beyond Layer 1's, a 250 ms time budget, price between ×1.0 and ×2.0 and at most +0.5 above the twin's expectation. Blocked decisions fall back to Layer 1 (driver and base price); a blocked agent is re-tested with 500 rollouts in the twin before control is handed back. Every check is kept in a Guardian log on the phone.
- Passenger: *Price check · Layer 2* card, *Agent 1 · rehearsed in the city twin* card, and a *Twin-tested* reason on the booked ride.
- Driver: *Twin hint · Agent 2* card with *Show me on the map*. Kitchen: *Twin hint* with the courier's arrival and when to start cooking.
- **Twin tab** for every role: mirror and live map, 30-minute foresight per place, Layer 1 and Layer 2 status, Guardian log, **Run Guardian fault drill**, **Check Layer 2** (4 self-checks) and a switch to turn Layer 2 off (the app then behaves exactly as 1.2.0).
- Home card *New in 1.3 · City twin*; privacy notice section on the twin.

### Changed
- **Shared rides follow the stop order of a shared car.** Each carpool already carries a rider. The driver comes from where that rider boarded; the new rider waits (*Please wait · Ciara is in the car*), boards, and is dropped **only after** the earlier rider's drop-off: driver on the way → at your pickup → dropping the earlier rider → your drop-off. The order is shown as a checklist on the ride screen and on the map, enforced by the store (completing early is refused) and checked when the saved file is loaded.
- Shared seats are released when the ride is completed, not only when it is cancelled.
- Ride and twin maps refit after layout: on phones they were fitted at Kivy's default 100 × 100 size and showed the whole county.
- Solo fares can include a capped busy-time price (×1.0 to ×2.0, rounded to 10 cents) when Layer 2 is on and the Guardian passes it.
- Bottom navigation adds **Twin** (passenger: 6 tabs; driver and seller: 5).
- The app clock can be pinned (`ATLAS_CLOCK=2027-03-17T13:00`) for repeatable previews; the acceptance run pins it.

### Unchanged
- Layer 1 — `intelligence.py` and `learned.py` — is byte-identical to 1.2.0 (a unit test checks the SHA-256 of both files).

### Compatibility
- 1.2.0 and 1.1.0 `state.json` files load unchanged; Layer 2 starts switched on with an empty log. A shared ride saved by 1.2.0 finishes with the old three stages.
- Signed with a different key from the 1.2.0 Drive APK: uninstall 1.2.0 before installing the 1.3.0 APK.

## 1.2.0 (versionCode 3) — 7 November 2026

### Added
- Accounts for passengers, drivers and food sellers, with a welcome screen, registration, sign-in, sign-out, guest mode, account deletion and erase-all.
- Salted PBKDF2-HMAC-SHA256 password hashing (200,000 iterations) and a 60-second lock after five failed sign-ins.
- Validation of names, emails, phone numbers (E.164), passwords, Irish vehicle registrations, SPSV licence numbers, food business numbers, prices and preparation times.
- Driver app: go online/offline, starting area, phone location, ride requests with accept/decline, arrived/start/complete, trips, fares and acceptance rate, and an ATLAS *when to drive* card.
- Food seller app: kitchen profile, open/close, preparation time, menu editor, order acceptance, ready-for-courier, orders and sales.
- Live map (`livemap.py`): OpenStreetMap tiles with disk cache, drag to pan, zoom controls and double tap, automatic schematic offline map, attribution, and markers for places, moving drivers, registered drivers, kitchens, the active car and route, the courier and the user's location.
- Device location (`location.py`) through Android `LocationManager`, requested at run time and only when the user taps a location button.
- Time-lapse live journeys (`geo.py`): rides and deliveries move on their own; ride and order screens embed the live map with an ETA.
- Acceptance model per registered driver; surge level for the current hour as a live dispatch feature; courier timing for any preparation time; on-device *Check all models* self-test.
- 49 new unit tests (117 in total) and a 247-assertion UI acceptance run covering every role across accounts.

### Changed
- Dispatch ranks registered online drivers together with the simulated fleet; declined requests go to the next-best driver.
- Food catalog includes seller kitchens; courier plans use each kitchen's preparation time.
- Bottom navigation depends on the role (passenger: Home, Map, Food, Activity, You; driver: Drive, Map, Trips, You; seller: Kitchen, Menu, Orders, You).
- Android permissions: `INTERNET`, `ACCESS_NETWORK_STATE`, `ACCESS_FINE_LOCATION`, `ACCESS_COARSE_LOCATION` (foreground only). Location hardware is declared optional.
- Privacy notice rewritten for accounts, location and map tiles.

### Compatibility
- 1.1.0 `state.json` files load unchanged; existing history appears for the guest passenger.
- The 1.2.0 APK in this release is signed with a new release key. Uninstall 1.1.0 before installing it (Android refuses an update signed with a different key). Play builds signed with the owner's upload key are not affected.
