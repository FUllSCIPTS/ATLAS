# ATLAS Go privacy notice

Effective: 7 November 2026. Applies to ATLAS Go Android version 1.2.0 (`org.atlas.mobility`). Maintainer: FUllSCIPTS / ATLAS. Contact: [ATLAS issue tracker](https://github.com/FUllSCIPTS/ATLAS/issues). Do not put personal information in a public issue.

ATLAS Go lets people create passenger, driver and food-seller accounts on their phone, book simulated rides, run a simulated kitchen and follow journeys on a live map. Rides, deliveries and payments are simulated. No operator back end is connected: nothing you enter is sent to the maintainer or any other party, apart from the map-tile requests described below.

## Data stored on the phone

| Data | Why | Where |
|---|---|---|
| Name, email, mobile number, role | Your account and sign-in | Private app storage |
| Password | Sign-in | Never stored; only a random salt and a PBKDF2-HMAC-SHA256 hash |
| Driver: vehicle, registration, SPSV licence number, seats, starting area, trips, fares, acceptance counts | Driver profile and ATLAS dispatch | Private app storage |
| Driver: last phone location (only after you tap *Use my phone location* or *Me* on the map and allow it) | Distance to pickups for dispatch | Private app storage, overwritten by each new fix |
| Seller: kitchen name, cuisine, food business registration number, location, preparation time, menu, orders and sales | Kitchen profile and orders | Private app storage |
| Rides, food orders, basket, shared-seat reservations, screen choices | The app's features and your activity | Private app storage |
| Map tiles | Faster maps, offline use | App cache |

Licence and registration numbers are checked for format only; they are not verified with any authority.

## Location

The app asks for location permission only when you tap **Me** on the map, **Pick up near my location** or **Use my phone location**, and uses location only while the app is open (no background location). It shows your blue dot, picks the nearest pickup point and, for a signed-in driver, positions you for dispatch. Location is not sent anywhere. You can refuse or later revoke the permission in Android settings; the map and booking keep working.

## Map tiles

The live map downloads map images from OpenStreetMap's tile servers (`tile.openstreetmap.org`). As with any website, those servers receive your IP address, the app's name and version, and the map area being viewed. Their privacy policy applies: <https://osmfoundation.org/wiki/Privacy_Policy>. Map data © OpenStreetMap contributors, available under the Open Database Licence.

## Not collected

No payments or card data, contacts, camera, microphone, advertising identifiers, analytics or third-party tracking SDKs. Android backup is disabled for this app.

## Learning on the phone

Surge outlooks, driver choice, acceptance estimates and courier timing come from small models learned offline in a simulated city and bundled with the app. The per-driver acceptance estimate uses that driver's accept/decline counts on the phone. The learning lab retrains a sandbox copy on the phone and never changes dispatch. None of this leaves the phone.

## Retention and deletion

Data stays until you delete it. **You → Delete my account** (with your password) removes your profile; your past rides stay in the phone's history without your name, and a seller's kitchen is closed and its registration number removed. **You → Erase all data on this phone** removes every account, ride, order and kitchen. Clearing app storage in Android settings or uninstalling also removes everything.

## Changes

Connecting an operator back end, payments, identity checks, analytics or a different map provider changes these facts. Update this notice, the Play Data safety form and the in-app notice before distributing such a version.
