# ATLAS Go changelog

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
