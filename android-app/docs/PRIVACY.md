# ATLAS Go privacy notice

Effective: 16 November 2026. Applies to ATLAS Go Android version 1.5.0 (`org.atlas.mobility`). Maintainer: FUllSCIPTS / ATLAS. Contact: [ATLAS issue tracker](https://github.com/FUllSCIPTS/ATLAS/issues). Do not put personal information in a public issue.

ATLAS Go lets people create passenger, driver and food-seller accounts on their phone, book simulated rides, run a simulated kitchen, follow journeys on a live map and, from 1.5.0, pay and be paid through a **sandbox bank** (no real bank is contacted and no money moves). By default nothing you enter leaves the phone, apart from the map-tile requests described below. If **you** enter the address of an ATLAS server and connect your account, the data listed under [ATLAS server](#atlas-server-only-if-you-connect) is sent to that server. The maintainer of this project operates no such server; whoever runs the server you connect to is the controller of the data it holds.

## Data stored on the phone

| Data | Why | Where |
|---|---|---|
| Name, email, mobile number, role | Your account and sign-in | Private app storage |
| Password | Sign-in | Never stored; only a random salt and a PBKDF2-HMAC-SHA256 hash |
| Driver: vehicle, registration, SPSV licence number, seats, starting area, trips, fares, acceptance counts | Driver profile and ATLAS dispatch | Private app storage |
| Driver: last phone location (only after you tap *Use my phone location* or *Me* on the map and allow it) | Distance to pickups for dispatch | Private app storage, overwritten by each new fix |
| Seller: kitchen name, cuisine, food business registration number, location, preparation time, menu, orders and sales | Kitchen profile and orders | Private app storage |
| Rides, food orders, basket, shared-seat reservations, screen choices | The app's features and your activity | Private app storage |
| Bank account, if you link one: account holder, country, bank, **last four characters** of the IBAN; for passengers the Direct Debit mandate reference, version and date | Paying by bank (passengers); being paid out (drivers, sellers) | Private app storage. The full IBAN is checked when you type it and is **not stored** |
| Bank payments and payouts: booking reference, amount, fee split, status, last four characters | Your payment history, a driver's or seller's balance | Private app storage |
| Server address and, for a connected account, its server id and session token | Sending your payments to the server you chose | Private app storage |
| Map tiles | Faster maps, offline use | App cache |

Licence and registration numbers are checked for format only; they are not verified with any authority.

## Location

The app asks for location permission only when you tap **Me** on the map, **Pick up near my location** or **Use my phone location**, and uses location only while the app is open (no background location). It shows your blue dot, picks the nearest pickup point and, for a signed-in driver, positions you for dispatch. Location is not sent anywhere. You can refuse or later revoke the permission in Android settings; the map and booking keep working.

## Map tiles

The live map downloads map images from OpenStreetMap's tile servers (`tile.openstreetmap.org`). As with any website, those servers receive your IP address, the app's name and version, and the map area being viewed. Their privacy policy applies: <https://osmfoundation.org/wiki/Privacy_Policy>. Map data © OpenStreetMap contributors, available under the Open Database Licence.

## Bank details

Linking, replacing or removing a bank account and paying out a balance ask for your password again. You type the IBAN once; the app verifies its country, length and check digits and then discards it, keeping only what a receipt would show. The sandbox bank decides approvals from those last four characters; no bank, payment provider or card network is contacted. No card numbers are requested anywhere in the app.

## ATLAS server, only if you connect

Nothing is sent to a server unless you enter a server address in **You → Bank & payments** and tap **Connect this account** (accounts registered after an address is saved connect automatically; **Disconnect this phone** stops it). The app accepts only `https://` addresses, except a test server on the same machine. A connected account sends:

| Sent to the server you chose | When | Kept there as |
|---|---|---|
| Name, email, mobile number, role; a driver's vehicle, registration, SPSV licence number and seats; a seller's kitchen and menu | When you connect | Account, driver profile, kitchen and dishes rows in PostgreSQL |
| Your password | When you connect, link or remove a bank account, pay out or delete the server account | Never stored: a salted PBKDF2-HMAC-SHA256 hash (600,000 iterations) |
| Account holder and IBAN | When you link a bank account | The IBAN is passed to the bank provider (a sandbox here) and not stored; the server keeps the holder, country, last four characters, the provider's token and a keyed fingerprint |
| For each bank payment: what was booked (route and option, or dishes and quantities), the booking reference and who is paid | After the payment is captured | Payment, ledger and audit rows. The server computes the amount itself |
| Payout requests | When you pay out | Payout, ledger and audit rows |

Rides and orders themselves, your location, map activity and the on-device models are **not** sent. Deleting the server account (`DELETE /v1/accounts/me`, with your password) erases your name, email, phone, password hash, bank holder and profile there, ends your sessions and keeps the payment and ledger rows under an anonymous id, as accounting rules require. **Delete my account** in the app removes the account from the phone; it does not contact the server.

## Not collected

No card data, contacts, camera, microphone, advertising identifiers, analytics or third-party tracking SDKs. Android backup is disabled for this app.

## Learning on the phone

Surge outlooks, driver choice, acceptance estimates and courier timing come from small models learned offline in a simulated city and bundled with the app. The per-driver acceptance estimate uses that driver's accept/decline counts on the phone. The learning lab retrains a sandbox copy on the phone and never changes dispatch. None of this leaves the phone.

## Retention and deletion

Data stays until you delete it. **You → Delete my account** (with your password) removes your profile and linked bank details; your past rides and payments stay on the phone without your identity, and a seller's kitchen is closed and its registration number removed. A driver or seller must pay out any balance first. **You → Erase all data on this phone** removes every account, ride, order and kitchen. Clearing app storage in Android settings or uninstalling also removes everything.

## Changes

Connecting a real payment provider, identity checks, analytics, a different map provider, or operating a server for other people changes these facts. Update this notice, the Play Data safety form and the in-app notice before distributing such a version.
