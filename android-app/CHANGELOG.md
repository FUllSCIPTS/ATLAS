# ATLAS Go changelog

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
