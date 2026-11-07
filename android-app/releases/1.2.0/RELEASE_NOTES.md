# ATLAS Go 1.2.0 release notes

**Accounts for three roles.** Register as a passenger, driver or food seller, sign in, switch accounts on one phone, continue as a guest, delete your account or erase all data. Passwords are stored as salted PBKDF2-HMAC-SHA256 hashes; five wrong attempts lock sign-in for a minute. Every field is validated (email, E.164 phone, password strength, Irish vehicle registration, SPSV licence format, food business number, prices, preparation times).

**Drivers** go online, set a starting area or use their phone's location, receive ride requests chosen by ATLAS dispatch, accept or decline, and mark arrived, started and completed. Trips, fares and acceptance rate are tracked.

**Food sellers** register a kitchen, edit the menu, open or close, set a preparation time, accept orders and hand food to the courier. Orders and sales are tracked.

**Live map.** OpenStreetMap tiles with pan and zoom, cached on the phone, with an automatic offline map. Shows pickup places, moving drivers, registered drivers online, kitchens, your ride's car and route, the courier, and your location after you allow it. Rides and deliveries now move on their own (10× time-lapse) with an ETA.

**Six on-device models, all live.** Dispatch policy v1.4 now ranks registered drivers alongside the simulated fleet using their real distance, a new per-driver acceptance model and the current-hour surge forecast. Courier timing follows each seller's preparation time. *How ATLAS learns → Check all models* runs every model on the phone. Retraining with `training/export_learned.py` reproduces the bundled models byte for byte.

**Permissions:** Internet (map tiles), network state, fine and coarse location (foreground only, asked when you tap a location button). No background location, ads, analytics or payments.

Install: uninstall 1.1.0 first (different signing key). Full list: [CHANGELOG](../../CHANGELOG.md).
