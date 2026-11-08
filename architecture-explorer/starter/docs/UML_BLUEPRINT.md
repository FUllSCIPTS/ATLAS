# ATLAS ride-hailing UML blueprint

Use this blueprint to reproduce or extend ATLAS end to end. It covers four layers:

- **Android app** — ATLAS Go 1.2.0, the Python/Kivy app on the `main` branch ([`android-app/`](https://github.com/FUllSCIPTS/ATLAS/tree/main/android-app)): passenger, driver and food-seller accounts, a live map with device location, solo and shared rides, food ordering from built-in and seller kitchens, stored on the device, plus six on-device models (dispatch policy, acceptance, surge outlook, supply agent, courier timing, learning lab).
- **Web front end** — the passenger and driver browser pages served by the gateway in this starter.
- **Back end** — the FastAPI gateway, trip, dispatch and model services, the event worker, Kafka, and ML training and serving.
- **Databases** — the device's `state.json` (accounts, kitchens, rides, orders) and map-tile cache, the starter's PostgreSQL (or local SQLite) schema, the Kafka event log and the model artifact volume.

The Android app has no back end today; its only network use is map tiles. Its learned policies are small constants bundled with the app, produced offline by simulations on the `main` branch; see [On-device intelligence](#on-device-intelligence-120). [Connecting the Android app to the back end](#connecting-the-android-app-to-the-back-end) maps each on-device command to the starter API, and labels the accounts, food, seller and shared-ride parts the back end does not yet implement.

[Final handover and runbook](FINAL_HANDOVER.md) · [Security and cryptography catalogue](#security-and-cryptography-catalogue) · [Machine learning and optimisation catalogue](#machine-learning-and-optimisation-catalogue) · [Data structures and algorithms catalogue](#data-structures-and-algorithms-catalogue) · [Runnable starter](../README.md) · [Android app source](https://github.com/FUllSCIPTS/ATLAS/tree/main/android-app) · [Android app architecture](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/docs/ARCHITECTURE.md) · [Machine-readable symbol inventory](uml-blueprint.json) · [Build specification](../../dist/build-spec.json) · [Kafka event contract](../packages/ride-event.schema.json)

## Start from the implementation

Clone the branch and run the unmodified starter before changing contracts or behavior.

```bash
git clone --branch architecture-explorer --single-branch https://github.com/FUllSCIPTS/ATLAS.git
cd ATLAS/architecture-explorer/starter
docker compose up -d --build
docker compose exec -T gateway python -m tests.smoke
docker compose exec -T gateway python -m tests.policy
docker compose exec -T -e KAFKA_BOOTSTRAP=kafka:9092 gateway python -m tests.replay
```

The [local SQLite quickstart](../README.md#start-locally-without-docker) runs the same business handlers without a broker. The full Compose run is the acceptance check for the PostgreSQL and Kafka deployment.

## System overview: apps, front end, back end and databases

```mermaid
flowchart TD
    subgraph Clients["Apps and front end"]
        A["ATLAS Go 1.2.0 Android app<br/>passenger · driver · seller<br/>Python · Kivy · main branch"]
        W1["Passenger web page<br/>apps/passenger"]
        W2["Driver web page<br/>apps/driver"]
    end
    subgraph Backend["Back end · this branch"]
        G["Gateway · :8000<br/>bearer keys · route allowlist"]
        T["Trip API"]
        D["Dispatch API"]
        E["Event worker<br/>outbox relay and consumer"]
        M["Model serving API"]
        R["RL watcher"]
    end
    subgraph Data["Databases and stores"]
        S[("state.json<br/>accounts · rides · orders · kitchens<br/>on the device")]
        OSM[("OpenStreetMap tiles<br/>cached on the device")]
        LP[("learned.py<br/>bundled RL policies · read-only")]
        P[("PostgreSQL · or SQLite locally<br/>trips · drivers · offers · outbox · inbox · experience")]
        K[("Kafka topic<br/>atlas.ride.v1")]
        V[("Artifact volume<br/>models · features · policies")]
    end
    A --> S
    A --> LP
    A -. "map tiles · HTTPS" .-> OSM
    A -. "planned · RemoteRepository over HTTPS" .-> G
    W1 --> G
    W2 --> G
    G --> T
    G --> D
    T --> P
    D --> P
    E --> P
    E <--> K
    E --> M
    M --> V
    E --> V
    R --> P
    R --> V
```

| Layer | Component | Technology | Stores data in | Status |
| --- | --- | --- | --- | --- |
| App | ATLAS Go Android app 1.2.0 (versionCode 3) | Python 3.14 on device, Kivy 2.3.1, pyjnius, requests, Buildozer / python-for-android, API 36, min API 26 | `state.json` in app-private storage (accounts with PBKDF2 hashes, kitchens, rides, orders); tile cache; learned constants in `learned.py` | Accounts, rides and orders on one phone; payments and journeys simulated; live map online with offline fallback; [1.2.0 downloads](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/releases/1.2.0/README.md) |
| Front end | Passenger page | HTML + [`apps/shared/client.js`](../apps/shared/client.js) | Browser memory only | Runs against the gateway |
| Front end | Driver page | HTML + the same client script | Browser memory only | Runs against the gateway |
| Back end | Gateway | FastAPI, httpx | None | Runs |
| Back end | Trip and Dispatch APIs | FastAPI, Pydantic | PostgreSQL / SQLite | Runs; ride hailing only |
| Back end | Event worker | Python, Kafka client | PostgreSQL, Kafka, artifact volume | Runs |
| Back end | Model API and RL watcher | PyTorch LSTM, scikit-learn, batch Q-learning | Artifact volume, PostgreSQL | Runs |
| Back end | Accounts, food, seller and shared-ride services | — | — | Not implemented; [proposed contract](#proposed-back-end-extensions-for-the-android-app) |

## Folder hierarchy

All checked-in files under `architecture-explorer/`, including the runnable starter, the published explorer assets and the self-host server. Runtime data, trained artifacts and virtual environments are excluded from the source inventory. The research materials at the repository root are separate from this application.

<!-- BEGIN GENERATED TREE -->

```text
architecture-explorer/
├── deploy/
│   └── atlas-explorer.service
├── dist/
│   ├── atlas-go.js
│   ├── atlas.js
│   ├── atlas.svg
│   ├── build-spec.json
│   ├── build.html
│   ├── build.js
│   ├── crypto.js
│   ├── dsa.js
│   ├── explorer.js
│   ├── index.html
│   ├── ml.js
│   ├── ride-event.schema.json
│   ├── security.js
│   ├── styles.css
│   └── uml-catalog.js
├── starter/
│   ├── apps/
│   │   ├── driver/
│   │   │   └── index.html
│   │   ├── passenger/
│   │   │   └── index.html
│   │   └── shared/
│   │       ├── client.js
│   │       └── demo.css
│   ├── docs/
│   │   ├── FINAL_HANDOVER.md
│   │   ├── UML_BLUEPRINT.md
│   │   └── uml-blueprint.json
│   ├── infra/
│   │   └── schema.sql
│   ├── ml/
│   │   ├── discrete.py
│   │   ├── forecast.py
│   │   ├── registry.py
│   │   ├── rl.py
│   │   ├── serve.py
│   │   └── train.py
│   ├── packages/
│   │   ├── config.py
│   │   ├── db.py
│   │   └── ride-event.schema.json
│   ├── scripts/
│   │   ├── generate_blueprint.py
│   │   ├── initialize.sh
│   │   ├── local.sh
│   │   └── security_catalog.py
│   ├── services/
│   │   ├── dispatch.py
│   │   ├── gateway.py
│   │   └── trips.py
│   ├── tests/
│   │   ├── policy.py
│   │   ├── replay.py
│   │   └── smoke.py
│   ├── workers/
│   │   └── events.py
│   ├── .dockerignore
│   ├── .gitignore
│   ├── Dockerfile
│   ├── README.md
│   ├── compose.yaml
│   └── requirements.txt
├── README.md
└── server.mjs
```

<!-- END GENERATED TREE -->

## Android app (ATLAS Go)

The Android app lives on the `main` branch at [`android-app/`](https://github.com/FUllSCIPTS/ATLAS/tree/main/android-app). This section describes version **1.2.0** (versionCode 3), which adds passenger, driver and food-seller accounts, a live map with device location, time-lapse live journeys, and connects all six on-device models to those flows. Every screen, rule, storage operation and test is Python. Accounts and bookings live on one phone; the only network traffic is map tiles from OpenStreetMap. [1.2.0 changelog](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/CHANGELOG.md) · [app architecture](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/docs/ARCHITECTURE.md) · [downloads and SHA256SUMS](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/releases/1.2.0/README.md).

```text
android-app/
├── main.py                 Entry point; sets the desktop preview size, starts AtlasGoApp
├── buildozer.spec          1.2.0 / versionCode 3; API 36, min API 26; arm64-v8a + x86_64;
│                           INTERNET, ACCESS_NETWORK_STATE, ACCESS_FINE/COARSE_LOCATION (foreground)
├── CHANGELOG.md
├── atlas_go/
│   ├── __init__.py         Version (1.2.0)
│   ├── accounts.py         Roles, field validation, PBKDF2-HMAC-SHA256 hashing          (new)
│   ├── domain.py           Places, fares, Dish, Offer, Kitchen, Catalog, Cart
│   ├── geo.py              Cork coordinates, Web-Mercator tiles, live journey positions  (new)
│   ├── store.py            LocalStore: accounts, sessions, rides, orders, kitchens, tick()
│   ├── intelligence.py     Calendar, outlook, dispatch, acceptance, courier, LearningLab, self_test
│   ├── learned.py          Learned constants exported from the simulations (generated, read-only)
│   ├── livemap.py          LiveMap widget, TileLoader (threads, disk cache, offline layer) (new)
│   ├── location.py         DeviceLocation: runtime permission, LocationManager via pyjnius (new)
│   ├── app.py              AtlasGoApp and widgets: role-aware Kivy screens
│   └── acceptance.py       Debug-only UI click-through and screenshot capture
├── tests/                  117 tests: domain, intelligence, accounts/geo, roles
├── training/               Development-only simulations and exporter (numpy; excluded from the APK)
├── scripts/                Emulator acceptance, signing, manifest and alignment checks
├── docs/                   User guide, architecture, privacy, Play handover, 22 screenshots, video
└── releases/1.2.0/         APK, unsigned AAB, SHA256SUMS, release notes, validation
```

### App layers

```mermaid
flowchart LR
    U["AtlasGoApp<br/>passenger · driver · seller screens"] --> L["LocalStore<br/>commands · validation · rollback · tick()"]
    U --> MAP["LiveMap<br/>tiles · markers · routes"]
    U --> LOC["DeviceLocation<br/>permission · fixes"]
    U --> AI["intelligence.py<br/>dispatch · acceptance · outlook · courier · lab · self_test"]
    MAP --> TL["TileLoader<br/>2 threads · disk cache"]
    TL -. "HTTPS GET /{z}/{x}/{y}.png" .-> OSM[("OpenStreetMap tile server")]
    TL --> TC[("tiles/ cache")]
    L --> ACC["accounts.py<br/>validate · hash · verify"]
    L --> DM["domain.py<br/>Catalog · Cart · Offer · fares"]
    L --> GEO["geo.py<br/>live positions"]
    MAP --> GEO
    L --> J[("state.json<br/>app-private storage")]
    AI --> LC[("learned.py<br/>bundled constants")]
    TR["training/<br/>simulations · dev only"] -. "export_learned.py" .-> LC
    X["Acceptance<br/>debug builds only"] --> U
```

The UI changes state only through `LocalStore` commands; each validates, mutates, writes the file atomically and restores the previous in-memory state if the write fails. Once a second `AtlasGoApp.live_tick` calls `LocalStore.tick(now)`, which advances simulated journeys whose time-lapse leg has finished and refreshes the map layers. Journeys handled by a registered driver or seller move only when that account acts. `intelligence.py` and `geo.py` are pure Python without I/O.

### App class diagram

```mermaid
classDiagram
    class App
    class BoxLayout
    class Widget
    class StencilView
    class AtlasGoApp {
        +LocalStore store
        +TileLoader tiles
        +DeviceLocation gps
        +str screen
        +str reg_role
        +dict form
        +LiveMap live_map
        +bool live_paused
        +LearningLab lab
        +list models
        +build()
        +render()
        +go(screen)
        +nav_items() tuple
        +home_screen() str
        +live_tick(dt)
        +refresh_live()
        +map_layers(screen) tuple
        +locate()
        +welcome() login() register()
        +submit_login() submit_register()
        +logout() delete_account(password)
        +home() ride(shared) map_screen()
        +registered_candidates(pickup) list
        +pick_driver(pickup, exclude) tuple
        +book_solo() book_shared(offer_id) redispatch()
        +active_ride() next_ride() cancel_ride()
        +driver() job_accept() job_decline() job_next()
        +seller() seller_menu() add_dish()
        +food() menu() cart() checkout() active_order() next_order()
        +activity() profile() privacy() reset()
        +intelligence() check_models() lab_train()
    }
    class LiveMap {
        +tuple center_point
        +int zoom
        +bool interactive
        +list markers
        +list routes
        +set_view(center, zoom)
        +zoom_by(step)
        +fit(points, padding)
        +set_layers(markers, routes, accuracy)
        +to_screen(point) tuple
        +to_point(x, y) tuple
        +draw()
    }
    class TileLoader {
        +Path cache_dir
        +OrderedDict textures
        +bool offline
        +texture(key)
    }
    class DeviceLocation {
        +tuple point
        +float accuracy
        +bool available
        +start()
        +stop()
    }
    class LocalStore {
        +list accounts
        +str session
        +bool guest
        +list kitchens
        +Catalog catalog
        +Cart cart
        +list history
        +dict ride
        +dict order
        +list offers
        +register(role, name, email, phone, password, ...) dict
        +login(email, password, now) dict
        +logout() continue_as_guest()
        +delete_account(password)
        +online_drivers() list
        +driver_position(account) tuple
        +set_online(online, base)
        +update_location(point)
        +driver_job() dict
        +driver_respond(accept, fallback, now)
        +driver_advance(now)
        +book(pickup, destination, comfort, offer_id, party, driver, why, driver_id, start, now)
        +advance_ride(cancel, now)
        +kitchen_of(account) dict
        +add_dish(name, detail, price) str
        +archive_dish(dish_id)
        +update_kitchen(open_, prep)
        +update_cart(operation, item)
        +checkout(address, courier, now)
        +seller_order() dict
        +seller_accept(now) seller_ready(now)
        +advance_order(now)
        +tick(now) bool
        +my_history() list
        +validate(data)$
    }
    class Catalog {
        +dict kitchens
        +dict dishes
        +set archived
        +name(kitchen) str
        +menu(kitchen) list
        +listed() list
    }
    class Kitchen {
        +int id
        +str name
        +str cuisine
        +int place
        +int prep
        +str owner
        +bool open
    }
    class Cart {
        +dict items
        +Catalog catalog
        +restaurant() int
        +add(item) remove(item) clear()
        +count() subtotal() total()
    }
    class Dish {
        +str id
        +str name
        +str detail
        +int restaurant
        +int price
    }
    class Offer {
        +matches(pickup, destination, party) bool
        +reserve(party)
        +release(party)
    }
    class Candidate {
        +str name
        +str zone
        +int eta
        +float accept
        +float surge
        +bool last
        +str account
        +features() list
    }
    class LearningLab {
        +reset()
        +train(episodes, lr)
        +result() dict
    }
    class Panel
    class RouteMap
    class OutlookChart
    class Bar
    class LearningCurve
    App <|-- AtlasGoApp
    StencilView <|-- LiveMap
    BoxLayout <|-- Panel
    Widget <|-- RouteMap
    Widget <|-- OutlookChart
    Widget <|-- Bar
    Widget <|-- LearningCurve
    AtlasGoApp --> LocalStore
    AtlasGoApp --> LiveMap
    AtlasGoApp --> DeviceLocation
    AtlasGoApp --> LearningLab
    AtlasGoApp ..> Candidate : ranks
    LiveMap --> TileLoader
    LocalStore --> Catalog
    LocalStore --> Cart
    LocalStore "1" --> "4" Offer
    Catalog --> Kitchen
    Catalog --> Dish
    Cart --> Catalog
```

Module functions: `accounts` — `hash_password`, `verify_password`, `clean_name`, `clean_email`, `clean_phone`, `check_password`, `clean_plate`, `clean_licence`, `clean_business`, `parse_int`, `parse_price`, `public_view`. `geo` — `haversine_km`, `eta_minutes`, `leg_seconds`, `lerp`, `nearest_place`, `valid_point`, `zone_drift`, `world_px`, `from_world_px`, `tile_range`, `fit_zoom`, `ride_legs`, `ride_position`, `ride_eta_text`, `order_position`. `intelligence` (new in 1.2.0) — `surge_level`, `acceptance`, `registered_candidate`, `self_test`; `rank`/`choose` take `extra` candidates and `exclude` account ids; `courier_plan` takes a `prep` time. The full generated list is in [ARCHITECTURE.md](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/docs/ARCHITECTURE.md#complete-source-method-catalog).

### Screen navigation

```mermaid
stateDiagram-v2
    [*] --> welcome : no session
    [*] --> home : passenger or guest
    [*] --> driver : driver signed in
    [*] --> seller : seller signed in
    welcome --> register : Create an account
    welcome --> login : Sign in
    welcome --> home : Continue as guest
    welcome --> privacy
    register --> home : passenger created
    register --> driver : driver created
    register --> seller : seller created
    login --> home
    login --> driver
    login --> seller
    state "Passenger" as P {
        home --> ride
        home --> share
        home --> food
        home --> map
        ride --> active_ride : book_solo
        share --> active_ride : book_shared
        food --> menu
        menu --> cart
        cart --> active_order : checkout
        active_ride --> activity : completed / cancelled
        active_order --> activity : delivered
    }
    state "Driver" as D {
        driver --> driver : accept · decline · arrived · start · complete
    }
    state "Seller" as S {
        seller --> seller_menu : Edit menu
        seller --> seller : accept order · food ready
    }
    home --> profile : You
    driver --> profile : You
    seller --> profile : You
    profile --> welcome : Sign out · Delete account · Erase all
    profile --> intelligence : How ATLAS learns
    profile --> privacy
```

Bottom bar by role — passenger/guest: Home · Map · Food · Activity · You; driver: Drive · Map · Trips · You; seller: Kitchen · Menu · Orders · You. `render()` redirects a role away from screens it may not use.

### On-device ride and order lifecycles

```mermaid
stateDiagram-v2
    state "Ride" as R {
        [*] --> pending : book with a registered driver
        [*] --> on_the_way : book with a simulated driver or shared offer
        pending --> on_the_way : driver accepts
        pending --> pending : driver declines · next registered driver
        pending --> on_the_way : declines · next simulated driver
        on_the_way --> at_pickup : car reaches pickup (tick) · or driver taps Arrived
        at_pickup --> on_your_way : 8 s time-lapse wait (tick) · or driver taps Start
        on_your_way --> Completed : car reaches destination (tick) · or driver taps Complete
        pending --> Cancelled
        on_the_way --> Cancelled
        at_pickup --> Cancelled
        on_your_way --> Cancelled
    }
    state "Food order" as F {
        [*] --> waiting_for_kitchen : seller kitchen
        [*] --> preparing : built-in kitchen
        waiting_for_kitchen --> preparing : seller accepts
        preparing --> courier_on_the_way : prep time elapsed (tick) · or seller taps Ready
        courier_on_the_way --> arriving : courier reaches address (tick)
        arriving --> Delivered : 6 s (tick)
    }
```

`stage` stays 0..2 as in 1.1.0; `pending` marks the waiting states. Legs are straight lines at 25 km/h played 10× faster (`geo.leg_seconds`). *Skip to next stage* still advances simulated journeys by hand. On completion a registered driver's `earnings` and `trips` increase; on delivery a seller kitchen's `orders` and `sales` (food total without the €2.50 delivery fee) increase.

### On-device data model (`state.json`)

One JSON document in app-private storage, saved via `state.tmp` + `fsync` + atomic replace. `LocalStore.validate` checks every field before a screen reads it; damaged files are kept as `state.invalid.json`. All 1.2.0 fields are optional, so a 1.1.0 file loads unchanged. Map tiles are cached separately under `tiles/{z}/{x}/{y}.png`.

```mermaid
erDiagram
    STATE ||--o{ ACCOUNT : "accounts"
    STATE ||--o| ACCOUNT : "session"
    STATE ||--o{ KITCHEN : "kitchens (sellers)"
    STATE ||--|| CART : "cart"
    STATE ||--o| RIDE : "ride (active)"
    STATE ||--o| ORDER : "order (active)"
    STATE ||--o{ HISTORY_RECORD : "history"
    STATE ||--o{ SEATS : "seats per offer"
    STATE ||--|| UI : "ui"
    ACCOUNT ||--o| DRIVER_PROFILE : "driver"
    ACCOUNT ||--o| SELLER_LINK : "seller"
    SELLER_LINK ||--|| KITCHEN : "kitchen id"
    KITCHEN ||--o{ KITCHEN_DISH : "dishes"
    RIDE }o--o| ACCOUNT : "passenger, driver_id"
    ORDER }o--o| ACCOUNT : "passenger"
    ORDER }o--|| KITCHEN : "restaurant"
    ORDER ||--o| COURIER_PLAN : "courier"
    STATE {
        array accounts
        string session "account id or null"
        bool guest
        array kitchens
        object cart
        array history
        object ride
        object order
        object seats
        object ui
    }
    ACCOUNT {
        string id "U- plus nanosecond timestamp"
        string role "passenger, driver, seller"
        string name
        string email "unique, lower case"
        string phone "E.164"
        string salt "16 random bytes, hex"
        string hash "PBKDF2-HMAC-SHA256, hex"
        int iterations "200000"
        int created "epoch seconds"
    }
    DRIVER_PROFILE {
        string vehicle
        string plate "Irish format, e.g. 241-C-1234"
        string licence "SPSV number, format-checked"
        int seats "1..8"
        int base "0..3 PLACES"
        bool online
        int offered
        int accepted "<= offered"
        int earnings "cents"
        int trips
        array location "lat, lon or null"
    }
    SELLER_LINK {
        int kitchen
    }
    KITCHEN {
        int id ">= 3; 0..2 are built in"
        string owner "account id or deleted"
        string name "unique"
        string cuisine
        string registration "food business number"
        int place "0..3"
        int prep "5..90 minutes"
        bool open
        int orders
        int sales "cents"
    }
    KITCHEN_DISH {
        string id "k<kitchen>-<n>"
        string name
        string detail
        int price "50..20000 cents"
        bool archived
    }
    RIDE {
        string id "R- plus nanosecond timestamp"
        int pickup
        int destination
        bool shared
        int party
        string offer
        string driver "display name"
        string driver_id "registered driver or null"
        bool pending "waiting for driver"
        array declined "account ids"
        string passenger "account id, null for guest"
        string why "dispatch explanation"
        object live "start lat-lon, t stage start"
        int fare "cents"
        int stage "0..2"
        string status "Completed or Cancelled"
    }
    ORDER {
        string id "F- plus nanosecond timestamp"
        int restaurant "kitchen id"
        int address
        object items
        int fare "cents incl. 250 delivery"
        string passenger
        bool pending "waiting for seller"
        object live "kitchen lat-lon, t"
        object courier
        int stage "0..2"
        string status "Delivered"
    }
    COURIER_PLAN {
        int prep
        int travel
        int dispatch_after
        int arrive
        int courier_wait
        int naive_wait
    }
    UI {
        string screen
        int pickup
        int destination
        int party
        bool comfort
        int restaurant
        int address
        int outlook_day
        string reg_role
    }
```

Account deletion removes the account, replaces its id in history with `deleted`, and closes the seller's kitchen (owner `deleted`, registration removed) so past orders keep a name. Sign-in failures are counted in memory only (five failures → 60-second lock).

### Registration and sign-in

```mermaid
sequenceDiagram
    actor User
    participant UI as AtlasGoApp
    participant Store as LocalStore
    participant Acc as accounts.py
    participant File as state.json
    User->>UI: Create account (role, details, password, consent)
    UI->>UI: check consent and password confirmation
    UI->>Store: register(role, name, email, phone, password, role fields)
    Store->>Acc: clean_name, clean_email, clean_phone, check_password
    Store->>Acc: clean_plate, clean_licence, parse_int (driver) or clean_business, parse_int (seller)
    Store->>Store: reject duplicate email or kitchen name
    Store->>Acc: hash_password(password) → salt, hash, iterations
    Store->>File: save() accounts (+ kitchen) and session
    Store-->>UI: account → driver, seller or home screen
    User->>UI: Sign in
    UI->>Store: login(email, password)
    Store->>Store: lockout check
    Store->>Acc: verify_password (constant-time compare)
    Store->>File: save() session
```

### Ride with a registered driver on the same phone

```mermaid
sequenceDiagram
    actor Passenger
    actor Driver
    participant UI as AtlasGoApp
    participant AI as intelligence.py
    participant Store as LocalStore
    participant Map as LiveMap
    Driver->>UI: Go online (starting area or phone location)
    UI->>Store: set_online(True, base) · update_location(point)
    Passenger->>UI: Book ride
    UI->>Store: online_drivers()
    UI->>AI: registered_candidate(account, position, pickup, surge_level(now), last)
    UI->>AI: choose(pickup, extra=[registered], exclude=declined)
    AI-->>UI: chosen candidate and explanation
    UI->>Store: book(..., driver_id, start)
    Store-->>UI: ride pending
    Driver->>UI: Sign in · Accept
    UI->>Store: driver_respond(True) · offered+1, accepted+1
    loop Every second
        UI->>Store: tick(now)
        UI->>Map: set_layers(car = geo.ride_position(ride, now), routes)
    end
    Driver->>UI: Arrived · Start trip · Complete trip
    UI->>Store: driver_advance() × 3
    Store-->>UI: history + driver earnings and trips
```

If the driver declines, `job_decline` asks `choose` again with that driver excluded and passes the result to `driver_respond(False, fallback)`.

### Food order from a seller kitchen

```mermaid
sequenceDiagram
    actor Seller
    actor Passenger
    participant UI as AtlasGoApp
    participant AI as intelligence.py
    participant Store as LocalStore
    Seller->>UI: Add dish (name, detail, price)
    UI->>Store: add_dish() → Catalog lists the open kitchen
    Passenger->>UI: Add dish, check out
    UI->>AI: courier_plan(kitchen, prep=kitchen.prep)
    UI->>Store: update_cart('add', dish) · checkout(address, courier)
    Store-->>UI: order pending (seller kitchen)
    Seller->>UI: Accept and start cooking · Food is ready
    UI->>Store: seller_accept() · seller_ready()
    loop Every second
        UI->>Store: tick(now) moves the courier to the address, then delivers
    end
    Store-->>UI: history + kitchen orders and sales
```

### Live map and location

```mermaid
sequenceDiagram
    actor User
    participant UI as AtlasGoApp
    participant Loc as DeviceLocation
    participant Android as LocationManager
    participant Map as LiveMap
    participant Tiles as TileLoader
    participant OSM as Tile server
    User->>UI: Open Map
    UI->>Map: LiveMap(interactive) · set_layers(places, drivers, kitchens, ride, courier)
    Map->>Tiles: texture(z, x, y) for visible tiles
    Tiles->>Tiles: disk cache hit?
    Tiles->>OSM: GET /{z}/{x}/{y}.png (worker thread, User-Agent ATLASGo/1.2.0)
    OSM-->>Tiles: PNG → cache → texture on main thread
    Tiles-->>Map: redraw
    Note over Map,Tiles: 3 failures → offline for 45 s, schematic Cork layer drawn
    User->>UI: Me
    UI->>Loc: start()
    Loc->>Android: request ACCESS_FINE/COARSE_LOCATION (first time)
    Android-->>Loc: onLocationChanged(lat, lon, accuracy)
    Loc-->>UI: on_location → blue dot · driver position saved
```

### On-device intelligence (1.2.0)

The models run on the phone in pure Python from constants that simulations produced offline; no numpy or model files are packaged. All training data is synthetic; holiday dates follow Ireland's real public-holiday rules. `training/export_learned.py` reproduced the bundled `learned.py` byte for byte for 1.2.0.

```mermaid
flowchart LR
    subgraph Dev["Development only · android-app/training"]
        RS["rl_sim.py<br/>REINFORCE dispatch · Q-learning courier"]
        CS["city_sim.py<br/>2 simulated years of Cork · holidays<br/>supply agent · LSTM"]
        EX["export_learned.py"]
    end
    subgraph APK["Inside the app"]
        LC[("learned.py<br/>RIDE_WEIGHTS · COURIER_DELAY<br/>BASE_DEMAND · SURGE_RATIO · BOOST")]
        AI["intelligence.py"]
        ACM["acceptance(offered, accepted)<br/>Beta(9,1) posterior"]
        SL["surge_level(day, hour)"]
        LAB["LearningLab<br/>sandbox · never dispatches"]
        ST["self_test()"]
    end
    RS --> EX
    CS --> EX
    EX --> LC
    LC --> AI
    ACM --> AI
    SL --> AI
    AI --> UIs["Ride dispatch card · driver requests · courier timing ·<br/>seller prep · outlook · when to drive"]
    LAB --> UIs
    ST --> UIs
```

| Model | Learned by | Constant / function | Used on |
| --- | --- | --- | --- |
| Dispatch policy v1.4 | REINFORCE over four features (closer ETA, likely to accept, keep the last car in a surging area, avoid surging areas); delayed reward | `RIDE_WEIGHTS`, `rank`, `choose`, `explain` | Ride screen; `book_solo` and `redispatch`; driver decline hand-over. Registered online drivers join the simulated pool |
| Acceptance model | Beta(9, 1) prior updated by each registered driver's accept/decline counts | `acceptance` | `accept` feature of registered drivers; driver *Your week* card |
| Surge outlook | Demand ratio per calendar context and hour from two simulated years | `BASE_DEMAND`, `SURGE_RATIO`, `outlook`, `day_summary`, `surge_level` | Intelligence, home and driver cards; current-hour `surge` feature for registered drivers; busy-period notice on fares |
| Supply agent | Learned extra-driver boost per context, weekday type and hour | `BOOST` | Violet outlook marks; *when to drive* |
| Courier timing | Q-learning from kitchen slack to dispatch delay; margin extrapolated beyond the table | `COURIER_DELAY`, `courier_plan(kitchen, prep)` | Basket, order and seller screens; stored as `order.courier` |
| Learning lab | Retrains a dispatch policy from zero (30,000 simulated rides) | `LearningLab` | Intelligence screen; compared with the nearest-driver rule and v1.4 |

`self_test()` runs each model on known inputs (for example: UCC pickup chooses Morgan to protect Mardyke's last car; St Patrick's Day surges and an ordinary Wednesday does not; the lab improves after 3,000 rides). The Intelligence screen's **Check all models** shows the results; the unit tests require all six to pass.

These roles mirror the back-end ML: the dispatch policy corresponds to the RL agent and approved policy in [`ml/rl.py`](../ml/rl.py) and [`ml/registry.py`](../ml/registry.py), the outlook to the LSTM in [`ml/forecast.py`](../ml/forecast.py), and the acceptance model to the discrete model in [`ml/discrete.py`](../ml/discrete.py). When the app is connected, server-approved policies should replace the bundled constants, which remain the offline fallback.

## Component and deployment boundaries

Only the gateway is published on the host loopback interface in the starter. The trip, dispatch and model APIs run on the internal network. The same event worker performs outbox relay and event consumption in this demo.

```mermaid
flowchart TD
    B["Passenger and driver browsers"] --> G["Gateway · host port 8000"]
    G --> T["Trip API"]
    G --> D["Dispatch API"]
    T --> P["PostgreSQL"]
    D --> P
    E["Event worker"] --> P
    E --> K["Kafka · atlas.ride.v1"]
    K --> E
    E --> M["Model serving API"]
    E --> A["Feature and artifact volume"]
    M --> A
    R["RL watcher"] --> P
    R --> A
    I["Initialize schema and models"] --> P
    I --> A
```

| Owner | Responsibility | Code |
| --- | --- | --- |
| Gateway | Serve browser pages, verify demo bearer keys, forward only allowlisted routes, attach internal identity | [services/gateway.py](../services/gateway.py) |
| Trip API | Create and read rider trips, validate driver milestones, update trip state | [services/trips.py](../services/trips.py) |
| Dispatch API | Track availability and offers, reserve a driver atomically on acceptance | [services/dispatch.py](../services/dispatch.py) |
| Event worker | Publish acknowledged outbox events, deduplicate consumption, create offers, apply assignment and collect learning features | [workers/events.py](../workers/events.py) |
| Model API | Load versioned artifacts and score candidates with demand, acceptance, anomaly and policy signals | [ml/serve.py](../ml/serve.py) |
| RL watcher | Train candidates from completed rides. Review and approval run as separate commands. | [ml/rl.py](../ml/rl.py) |

### Web front end

The gateway serves two static pages and one shared script. Both pages call the gateway only; the browser never reaches the internal services.

| Page | Route | Uses |
| --- | --- | --- |
| Passenger | `/` and `/passenger` → [`apps/passenger/index.html`](../apps/passenger/index.html) | `POST /v1/rider/trips` with an `Idempotency-Key`, then polls `GET /v1/rider/trips/{id}` |
| Driver | `/driver` → [`apps/driver/index.html`](../apps/driver/index.html) | `PUT /v1/driver/availability`, `GET /v1/driver/offers`, `POST /v1/driver/offers/{id}/accept`, `POST /v1/driver/trips/{id}/milestones` |
| Shared | `/assets/client.js` → [`apps/shared/client.js`](../apps/shared/client.js) | `request()` adds the role's demo bearer key; `refresh()` polls and renders; form handlers for booking and telemetry |

The Android app plays the same role as the passenger page. When connected, it must use the same `/v1/rider/...` routes through the gateway (see below).

## Class diagrams

The diagrams show classes declared by the starter. Inherited library methods are supplied by their base classes. Full type annotations, defaults, decorators and source lines are in the [generated symbol catalog](#generated-symbol-catalog).

### Booking and dispatch types

```mermaid
classDiagram
    class BaseModel
    class Booking {
        +str pickup
        +str destination
        +Literal zone
    }
    class Milestone {
        +Literal status
    }
    class Telemetry {
        +bool online
        +float distance_km
        +float speed_kph
    }
    BaseModel <|-- Booking
    BaseModel <|-- Milestone
    BaseModel <|-- Telemetry
```

### Scoring types and LSTM

```mermaid
classDiagram
    class BaseModel
    class Candidate {
        +str driver_id
        +float distance_km
        +float speed_kph
    }
    class ScoringRequest {
        +Literal zone
        +list~Candidate~ drivers
    }
    class TorchModule
    class DemandLSTM {
        +LSTM recurrent
        +Linear output
        +__init__()
        +forward(values)
    }
    BaseModel <|-- Candidate
    BaseModel <|-- ScoringRequest
    ScoringRequest "1" *-- "1..20" Candidate : contains
    TorchModule <|-- DemandLSTM
```

### Database adapter

```mermaid
classDiagram
    class DB {
        +connection
        +__init__(connection)
        +run(query, *args)
    }
    class DBAPIConnection
    DB --> DBAPIConnection : wraps
```

`TorchModule` and `DBAPIConnection` represent external dependencies. The connection is either `sqlite3.Connection` or a Psycopg connection. The starter's service modules use functions and route decorators. Their signatures appear in the catalog.

## Persistence model

Cardinalities and key markers reflect the actual database constraints in [infra/schema.sql](../infra/schema.sql). `trips.driver_id` is a nullable text field. The assignment handler supplies its value.

```mermaid
erDiagram
    TRIPS ||--o| OFFERS : has
    DRIVERS ||--o{ OFFERS : receives
    TRIPS o|--o{ DRIVERS : "referenced by active_trip"
    TRIPS ||--o{ OUTBOX : emits
    TRIPS ||--o| EXPERIENCE : produces
    TRIPS {
        text id PK
        text rider_id
        text request_key
        text pickup
        text destination
        text zone
        text status
        text driver_id
        bigint created_at
    }
    DRIVERS {
        text id PK
        integer online
        real distance_km
        real speed_kph
        text active_trip FK
    }
    OFFERS {
        text trip_id PK, FK
        text driver_id FK
        text state
        integer action
        integer bucket
        text policy_version
        text model_version
        real forecast
        real acceptance
        integer anomaly_flag
    }
    OUTBOX {
        bigint seq PK
        text event_id UK
        text trip_id FK
        text event_type
        bigint occurred_at
        text body
        integer sent
    }
    INBOX {
        text event_id PK
    }
    EXPERIENCE {
        text trip_id PK, FK
        integer state
        integer action
        real reward
        text policy_version
        bigint occurred_at
    }
```

The compound unique key `trips(rider_id, request_key)` makes booking retries idempotent. The inbox primary key prevents duplicate event side effects. One offer and one learning record are stored per trip. The `pending_outbox(sent, seq)` index supports the relay.

### Databases at a glance

| Store | Owner | Engine | Holds | Durability |
| --- | --- | --- | --- | --- |
| `state.json` | Android app | JSON file, atomic replace | Basket, active ride and order (with dispatch explanation and courier plan), history, shared-seat counts, screen state | On the device only; deleted by Reset or uninstall |
| `learned.py` | Android app (generated by `training/export_learned.py`) | Python constants inside the APK | Dispatch weights, courier-delay table, hourly demand and surge profiles, supply boosts | Read-only; changes only with a new app version |
| `atlas` database | Trip, Dispatch, event worker, RL watcher | PostgreSQL in Compose; SQLite in the local quickstart | `trips`, `drivers`, `offers`, `outbox`, `inbox`, `experience` ([schema](../infra/schema.sql)) | Transactional; outbox and inbox give at-least-once delivery without duplicate effects |
| `atlas.ride.v1` | Event worker | Kafka | Ride events keyed by trip ID ([schema](../packages/ride-event.schema.json)) | Broker log; consumer offsets committed after database effects |
| Artifact volume | Model API, worker, RL watcher | Files | Versioned models, manifest, demand features, candidate and active policies | Atomic active-policy pointer |

The device file and the server database share no schema today. The server is the future source of truth; the device would keep only a cache and screen state.

## Trip state machine

```mermaid
stateDiagram-v2
    [*] --> requested : Idempotent booking
    requested --> assigned : Assignment confirmation consumed
    assigned --> picked_up : Assigned driver submits pickup
    picked_up --> completed : Assigned driver submits completion
    completed --> [*]
```

| Transition or action | Durable effect |
| --- | --- |
| Create booking | Insert trip and `trip.requested` outbox row in one transaction. Same key and body returns the existing trip. Different body with the same key yields `409`. |
| Create offer | Score online, unreserved drivers. Insert one offer and `dispatch.offer.created`. |
| Accept offer | Check driver ownership and availability. Update the offer, reserve the driver, and insert `dispatch.assignment.confirmed` in one transaction. |
| Apply assignment | Conditionally move `requested` to `assigned` and emit `trip.assigned`. |
| Pick up | Check driver and prior state. Move `assigned` to `picked_up` and emit `trip.picked_up`. |
| Complete | Move `picked_up` to `completed`, release the driver's reservation, and emit `trip.completed`. |
| Process completion | Join the offer's original state, action and policy version to the terminal reward. Insert one experience row. |

## Sequence diagrams

### Passenger booking

```mermaid
sequenceDiagram
    participant Passenger
    participant Gateway
    participant Trip
    participant Store
    Passenger->>Gateway: POST booking and idempotency key
    Gateway->>Trip: Forward authorized rider request
    Trip->>Store: Commit trip and trip.requested outbox row
    Store-->>Trip: Created or existing trip
    Trip-->>Gateway: 202 and trip snapshot
    Gateway-->>Passenger: 202 and trip ID
    Passenger->>Gateway: Poll trip status
```

### Event delivery and offer creation

```mermaid
sequenceDiagram
    participant Store
    participant Worker
    participant Kafka
    participant Models
    Worker->>Store: Read first unsent outbox row
    Worker->>Kafka: Publish event with trip ID key
    Kafka-->>Worker: Broker acknowledgement
    Worker->>Store: Mark event sent
    Kafka->>Worker: Deliver trip.requested
    Worker->>Store: Deduplicate event and read eligible drivers
    Worker->>Models: POST candidate list and zone
    Models-->>Worker: Forecast, scores, flags and versions
    Worker->>Store: Commit offer, inbox key and new outbox row
    Worker->>Kafka: Commit consumer offset
```

If a relay crashes after the broker acknowledgement and before marking the event sent, the next attempt can publish the same event again. The inbox deduplication is in the same transaction as the event's database effects. The SQLite profile drives these handlers directly from the outbox.

### Driver acceptance and completion

```mermaid
sequenceDiagram
    participant Driver
    participant Gateway
    participant Dispatch
    participant Worker
    participant Trip
    Driver->>Gateway: Poll offers and accept an offer
    Gateway->>Dispatch: Forward authenticated driver actions
    Dispatch-->>Gateway: 202 after reservation and outbox commit
    Dispatch-->>Worker: Assignment event via outbox and Kafka
    Worker-->>Trip: Apply assignment to shared trip storage
    Driver->>Gateway: Submit pickup and completion
    Gateway->>Trip: Forward driver milestone requests
    Trip-->>Worker: Completion event via outbox and Kafka
```

The worker applies assignment in the shared database. The diagram's dashed message to Trip represents that logical ownership boundary. There is no worker-to-Trip HTTP request.

### Training, serving and approval

```mermaid
flowchart TD
    S["Seeded training data"] --> T["Train LSTM, acceptance and anomaly models"]
    T --> M["Versioned model files and manifest"]
    M --> I["Model serving API"]
    E["Committed ride events"] --> F["Demand buckets and terminal experiences"]
    F --> I
    F --> Q["Batch Q-learning candidate"]
    Q --> G{"Explicit approval and holdout checks"}
    G -->|Pass| P["Atomic active-policy pointer"]
    P --> I
    G -->|Reject| B["Keep current policy"]
```

The LSTM reads 12 five-minute counts. Logistic regression and Isolation Forest read distance and speed. The RL state is forecast bucket `0` below 8 or `1` at least 8. Action `0` ranks by distance and action `1` ranks by acceptance probability. The policy watcher creates candidates after at least 80 completed outcomes. Training does not activate candidates. Inference uses an approved strategy only when `ATLAS_POLICY_ENABLED=1`. Rollback restores the nearest-driver baseline.

## Connecting the Android app to the back end

This section is a design for the next step. None of it is implemented yet: in 1.2.0 the Android app's only network calls are map-tile downloads.

### Repository boundary

Introduce a repository interface in the app. Keep `LocalStore` as the offline demo implementation and add a `RemoteRepository` that calls the gateway over HTTPS. Run network calls off Kivy's main thread and apply results back on it.

```mermaid
classDiagram
    class PassengerRepository {
        <<interface>>
        +book(pickup, destination, comfort, offer_id, party)
        +ride_status(trip_id)
        +cancel_ride(trip_id)
        +shared_offers(pickup, destination, party)
        +restaurants()
        +menu(restaurant_id)
        +checkout(basket, address)
        +order_status(order_id)
        +history()
        +register(role, profile, password)
        +login(email, password)
        +delete_account(password)
    }
    class DriverRepository {
        <<interface>>
        +set_online(online, location)
        +offers()
        +respond(trip_id, accept)
        +advance(trip_id)
    }
    class SellerRepository {
        <<interface>>
        +kitchen()
        +add_dish(name, detail, price)
        +archive_dish(dish_id)
        +update_kitchen(open, prep)
        +accept_order(order_id)
        +ready(order_id)
    }
    class LocalStore {
        offline demo · state.json
    }
    class RemoteRepository {
        +str base_url
        +TokenStore tokens
        +HttpClient http
    }
    class TokenStore {
        Android Keystore-backed
    }
    class AtlasGoApp
    PassengerRepository <|.. LocalStore
    PassengerRepository <|.. RemoteRepository
    DriverRepository <|.. LocalStore
    DriverRepository <|.. RemoteRepository
    SellerRepository <|.. LocalStore
    SellerRepository <|.. RemoteRepository
    AtlasGoApp --> PassengerRepository
    RemoteRepository --> TokenStore
```

### Command-to-API map

| App action | `LocalStore` today | Back end today | Gap to close |
| --- | --- | --- | --- |
| Book a solo ride | `book(pickup, destination, comfort)` | `POST /v1/rider/trips` with `Idempotency-Key`; body `pickup`, `destination`, `zone` | Map place indexes to place names and a zone (`cork-centre` or `cork-north`); add fare quote and comfort option on the server |
| Watch a ride | `advance_ride()` on button press | `GET /v1/rider/trips/{id}` polling | Map server status to app stages: `requested` → finding a driver, `assigned` → driver confirmed, `picked_up` → on your way, `completed` → completed. The server has no separate "at pickup" status |
| Driver gets the pickup location | Simulated driver name | Worker creates an offer; driver page polls `GET /v1/driver/offers` and accepts | Driver app shows pickup text only; add GPS coordinates and routing as a separate extension |
| Cancel a ride | `advance_ride(cancel=True)` | Not available | Add a cancel route and a `cancelled` trip status |
| Shared ride | `Offer.matches`, `reserve`, `release` | Not available | [Proposed shared-ride API](#proposed-back-end-extensions-for-the-android-app) |
| Food menu, basket, checkout, tracking | `Cart`, `checkout`, `advance_order` | Not available | [Proposed food API](#proposed-back-end-extensions-for-the-android-app) |
| Activity | `history` in `state.json` | Not available | Add `GET /v1/rider/history` |
| Identity | `register`, `login`, `logout`, `delete_account`; PBKDF2 hashes on the phone; guest mode | Demo bearer keys per role | Server accounts for passenger, driver and seller roles; email/phone verification; tokens in Android Keystore; hashing moves to the server (Argon2id or PBKDF2) |
| Driver online and location | `set_online`, `update_location` (local) | Driver page polls offers | `POST /v1/driver/availability` with location while online |
| Driver accepts and drives | `driver_respond`, `driver_advance` | `POST /v1/driver/offers/{id}/accept`, completion routes | Add decline (re-match), arrived and start-trip milestones |
| Seller kitchen and menu | `add_dish`, `archive_dish`, `update_kitchen` | Not available | [Proposed seller API](#proposed-back-end-extensions-for-the-android-app) |
| Seller order handling | `seller_accept`, `seller_ready` | Not available | Proposed seller API; emits `food.order.accepted`, `food.order.ready` |
| Live positions | `geo.ride_position`, `geo.order_position` (time-lapse) | Not available | Server-sent driver/courier positions; routing provider for real routes and ETAs |
| Driver choice and explanation | `intelligence.choose(pickup, extra, exclude)` with bundled `RIDE_WEIGHTS`; registered drivers scored with `acceptance` and `surge_level` | Dispatch ranks candidates with model scores and the approved RL policy | Return the ranked candidates and a reason with the assignment, pinned to the policy version |
| Surge outlook | `intelligence.day_summary(day)` from bundled profiles | LSTM demand forecast in the model API | Add a read-only `GET /v1/rider/outlook?date=` backed by the forecaster |
| Courier timing | `intelligence.courier_plan(kitchen, prep)` | Not available | Part of the proposed food API: courier dispatch time decided by the server |
| Learning lab | `LearningLab` on the device | Not applicable | Stays a local sandbox; never sends results or dispatches |

### Connected booking sequence

```mermaid
sequenceDiagram
    actor Passenger
    participant App as AtlasGoApp
    participant Repo as RemoteRepository
    participant Gateway
    participant Trip
    participant DB as PostgreSQL
    Passenger->>App: Book ride
    App->>Repo: book(...) on a background thread
    Repo->>Gateway: POST /v1/rider/trips · Bearer token · Idempotency-Key
    Gateway->>Trip: Forward with internal rider identity
    Trip->>DB: Insert trip and trip.requested outbox row
    Trip-->>Gateway: 202 trip snapshot
    Gateway-->>Repo: 202 trip ID
    Repo-->>App: Show "requested" on the main thread
    loop Until completed
        Repo->>Gateway: GET /v1/rider/trips/{id}
        Gateway-->>Repo: status and driver_id
        Repo-->>App: Update stage
    end
```

Retries must reuse the same idempotency key, so a lost response never books twice. The phone never connects to Kafka, the database or the model API directly.

### Proposed back-end extensions for the Android app

These tables and routes are a proposal to support the app's accounts, driver, seller, food and shared-ride features (the fields mirror 1.2.0's `state.json`). They are not in [`infra/schema.sql`](../infra/schema.sql) and no service implements them.

```mermaid
erDiagram
    ACCOUNTS ||--o| DRIVER_PROFILES : "driver role"
    ACCOUNTS ||--o| RESTAURANTS : "seller owns"
    ACCOUNTS {
        text id PK
        text role "passenger, driver, seller"
        text email UK
        text phone
        text password_hash
        integer verified
        bigint created_at
    }
    DRIVER_PROFILES {
        text account_id PK, FK
        text vehicle
        text plate
        text spsv_licence
        integer seats
        integer verified "operator checked"
        integer online
        double lat
        double lon
        integer offered
        integer accepted
    }
    RESTAURANTS ||--o{ MENU_ITEMS : offers
    RESTAURANTS ||--o{ FOOD_ORDERS : receives
    FOOD_ORDERS ||--|{ ORDER_ITEMS : contains
    MENU_ITEMS ||--o{ ORDER_ITEMS : "ordered as"
    FOOD_ORDERS ||--o{ OUTBOX : emits
    SHARED_OFFERS ||--o{ SEAT_RESERVATIONS : holds
    TRIPS ||--o| SEAT_RESERVATIONS : "shared trip"
    RESTAURANTS {
        text id PK
        text owner_id FK "seller account; null for partner kitchens"
        text registration "food business number"
        integer prep_minutes
        text name
        text place
        integer delivery_fee_cents
        integer open
    }
    MENU_ITEMS {
        text id PK
        text restaurant_id FK
        text name
        text detail
        integer price_cents
        integer available
    }
    FOOD_ORDERS {
        text id PK
        text rider_id
        text request_key
        text restaurant_id FK
        text address
        text status "placed, preparing, collected, delivered, cancelled"
        text courier_id
        integer total_cents
        bigint created_at
    }
    ORDER_ITEMS {
        text order_id PK, FK
        text item_id PK, FK
        integer quantity "1 to 10"
        integer unit_price_cents
    }
    SHARED_OFFERS {
        text id PK
        text driver_id FK
        text pickup
        text destination
        integer capacity
        integer seats_left
        integer price_cents
        bigint departs_at
    }
    SEAT_RESERVATIONS {
        text offer_id PK, FK
        text trip_id PK, FK
        integer party "1 or 2"
    }
```

Rules carried over from the app: `UNIQUE (rider_id, request_key)` on `food_orders`; one restaurant per order; at most ten of each item; prices copied into `order_items` at checkout; seat reservation as one conditional update (`seats_left = seats_left - party WHERE seats_left >= party`) in the same transaction as its outbox row; cancellation returns seats. Totals and seat counts are decided by the server, never by the phone.

| Proposed route | Purpose |
| --- | --- |
| `GET /v1/rider/restaurants` · `GET /v1/rider/restaurants/{id}/menu` | Restaurant list and menu with server prices |
| `POST /v1/rider/orders` (`Idempotency-Key`) · `GET /v1/rider/orders/{id}` | Checkout and order tracking (`food.order.placed` … `food.order.delivered` events) |
| `POST /v1/courier/orders/{id}/milestones` | Courier collects at the restaurant and delivers to the address |
| `GET /v1/rider/shared-offers?pickup=&destination=&party=` · `POST /v1/rider/shared-offers/{id}/reserve` | Shared-ride search and atomic seat reservation |
| `POST /v1/rider/trips/{id}/cancel` | Ride cancellation; releases driver and seats |
| `GET /v1/rider/history` | Activity screen |
| `POST /v1/accounts` · `POST /v1/sessions` · `DELETE /v1/accounts/me` | Registration for the three roles, sign-in, account deletion |
| `POST /v1/driver/availability` · `POST /v1/driver/offers/{id}/decline` · `POST /v1/driver/trips/{id}/milestones` | Online/offline with location; decline and re-match; arrived, started, completed |
| `GET/PUT /v1/seller/kitchen` · `POST /v1/seller/menu-items` · `DELETE /v1/seller/menu-items/{id}` | Kitchen profile, open/closed, preparation time, menu |
| `POST /v1/seller/orders/{id}/accept` · `POST /v1/seller/orders/{id}/ready` | Seller order handling; the server then schedules the courier from the courier-timing policy |

Each new route must be added to the gateway's `ROUTES` allowlist with its role.

## Rebuild checklist

1. Run the [starter smoke and policy checks](../README.md#start-with-postgresql-and-kafka) against the existing code. Use the request paths and payloads in the [API contract](../README.md#api-and-data-contracts) as the compatibility baseline.
2. Implement changes through existing boundaries. Preserve rider and driver ownership, transactional state and outbox writes, deduplication, the state machine, model versions and explicit policy approval.
3. Test one complete ride, a booking retry with the same key, a forbidden offer acceptance, an invalid state transition, model outputs and one terminal experience. Run `tests.replay` against the configured Kafka broker before claiming deployment readiness.
4. Treat GPS, routing, offer expiry and re-matching, cancellations, payments, production identity and representative training data as separately scoped extensions.
5. For the Android app, run `python -m pytest tests` in `android-app/` on the `main` branch (117 cases in 1.2.0), the desktop acceptance run (247 assertions, 22 screenshots) and the emulator acceptance workflow before and after changes. After changing a simulation in `training/`, run `python training/export_learned.py` and commit the regenerated `atlas_go/learned.py`. When connecting it to the back end, add the repository interface first, keep `LocalStore` passing its tests, and test `RemoteRepository` against a staging gateway.
6. Regenerate the blueprint after changing code. Commit the updated generated sections and JSON with the source changes.

From `starter/`, use Python 3.12 and Node.js with npm. The generator uses the Python standard library and the pinned Acorn parser for JavaScript.

```bash
python scripts/generate_blueprint.py
python scripts/generate_blueprint.py --check
```

The JSON includes relative paths, source hashes, imports, class bases, attributes, method signatures, module functions, nested functions, callbacks, decorators and source lines. The application catalog covers the starter and its tests. The supporting catalog covers the explorer, Node static server and blueprint generator. The [handover runbook](FINAL_HANDOVER.md) specifies exact API responses, environment variables, model artifacts and acceptance steps.

## Security and cryptography catalogue

<!-- BEGIN SECURITY CATALOG -->

Every concept in the Architecture Explorer's **Security** and **Cryptography** tabs, linked to the
function, constant or file that implements it. Each row has a stable anchor that the explorer links to.
Status: **Implemented** (in the code), **Demo-grade** (implemented with deliberately simple choices),
**Teaching extension** (not in ATLAS; shows where a standard protocol would attach) or **Explorer / lab**
(teaching code in the explorer or `security_lab/`). Generated by `scripts/security_catalog.py`.

<a name="uml-security-passwords"></a>

### Security → Password storage

[Open in the explorer ↗](https://fullscipts.github.io/ATLAS/#security-passwords)

| Concept | Function / symbol | Location | Status |
| --- | --- | --- | --- |
| <a name="sec-pw-params"></a>Work factor and lockout limits | `PBKDF2_ITERATIONS` | [android-app/atlas_go/accounts.py L16](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/accounts.py#L16) | Implemented |
| <a name="sec-pw-hash"></a>Hash a password (salt + PBKDF2-HMAC-SHA256) | `hash_password` | [android-app/atlas_go/accounts.py L27](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/accounts.py#L27) | Implemented |
| <a name="sec-pw-verify"></a>Verify a password (constant-time compare) | `verify_password` | [android-app/atlas_go/accounts.py L33](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/accounts.py#L33) | Implemented |
| <a name="sec-pw-policy"></a>Password policy (8–128, letter + digit) | `check_password` | [android-app/atlas_go/accounts.py L72](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/accounts.py#L72) | Implemented |
| <a name="sec-pw-public"></a>Strip salt and hash before display | `public_view` | [android-app/atlas_go/accounts.py L124](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/accounts.py#L124) | Implemented |
| <a name="sec-pw-register"></a>Store only {salt, hash, iterations} at registration | `LocalStore.register` | [android-app/atlas_go/store.py L260](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py#L260) | Implemented |
| <a name="sec-pw-test"></a>Test: same password, different salts and hashes | `test_password_hash_roundtrip_and_salt` | [android-app/tests/test_accounts_geo.py L9](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/tests/test_accounts_geo.py#L9) | Implemented |
| <a name="sec-pw-lab"></a>Explorer lab: PBKDF2 with the app's parameters | `secPwHash` | [architecture-explorer/dist/security.js L204](../../dist/security.js#L204) | Explorer / lab |
| <a name="sec-pw-lab-verify"></a>Explorer lab: verify_password replica | `secPwVerify` | [architecture-explorer/dist/security.js L223](../../dist/security.js#L223) | Explorer / lab |
| <a name="sec-pw-cli"></a>Command-line lab runner: all 20 experiments and 5 study paths | `if __name__ == '__main__':` | [security_lab/password_storage_demo.py L37](https://github.com/FUllSCIPTS/ATLAS/blob/main/security_lab/password_storage_demo.py#L37) | Explorer / lab |
| <a name="sec-pw-cli-a"></a>Lab A: what the app stores (experiments 1-8) | `exp_record` | [security_lab/lab_a_password_storage.py L38](https://github.com/FUllSCIPTS/ATLAS/blob/main/security_lab/lab_a_password_storage.py#L38) | Explorer / lab |
| <a name="sec-pw-cli-common"></a>Lab helpers, experiment registry and command line | `main` | [security_lab/lab_common.py L144](https://github.com/FUllSCIPTS/ATLAS/blob/main/security_lab/lab_common.py#L144) | Explorer / lab |

<a name="uml-security-login"></a>

### Security → Login & lockout

[Open in the explorer ↗](https://fullscipts.github.io/ATLAS/#security-login)

| Concept | Function / symbol | Location | Status |
| --- | --- | --- | --- |
| <a name="sec-login"></a>Sign in, 5 failures → 60 s lockout, generic error | `LocalStore.login` | [android-app/atlas_go/store.py L304](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py#L304) | Implemented |
| <a name="sec-login-failures"></a>Failure counter kept in memory only | `self.failures = {}          # email -> [count, locked_until]; memory ...` | [android-app/atlas_go/store.py L33](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py#L33) | Implemented |
| <a name="sec-login-session"></a>Session validated on load (must name an account) | `LocalStore.validate` | [android-app/atlas_go/store.py L86](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py#L86) | Implemented |
| <a name="sec-login-guest"></a>Guest mode (no identity, least privilege) | `LocalStore.continue_as_guest` | [android-app/atlas_go/store.py L321](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py#L321) | Implemented |
| <a name="sec-login-logout"></a>Sign out | `LocalStore.logout` | [android-app/atlas_go/store.py L326](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py#L326) | Implemented |
| <a name="sec-login-clear"></a>Clear the password field after submit | `AtlasGoApp.submit_login` | [android-app/atlas_go/app.py L613](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/app.py#L613) | Implemented |
| Verify a password (constant-time compare) | `verify_password` | [android-app/atlas_go/accounts.py L33](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/accounts.py#L33) | Implemented |
| <a name="sec-login-lab"></a>Explorer lab: LocalStore.login replica | `secLoginAttempt` | [architecture-explorer/dist/security.js L267](../../dist/security.js#L267) | Explorer / lab |
| <a name="sec-pw-cli-c"></a>Lab C: sign-in defences (experiments 12-15) | `exp_lockout` | [security_lab/lab_c_signin_defences.py L28](https://github.com/FUllSCIPTS/ATLAS/blob/main/security_lab/lab_c_signin_defences.py#L28) | Explorer / lab |
| <a name="sec-pw-cli-d"></a>Lab D: integrity, sessions and lifecycle (experiments 16-20) | `exp_sessions` | [security_lab/lab_d_integrity_lifecycle.py L34](https://github.com/FUllSCIPTS/ATLAS/blob/main/security_lab/lab_d_integrity_lifecycle.py#L34) | Explorer / lab |

<a name="uml-security-identity"></a>

### Security → Identity & roles

[Open in the explorer ↗](https://fullscipts.github.io/ATLAS/#security-identity)

| Concept | Function / symbol | Location | Status |
| --- | --- | --- | --- |
| Store only {salt, hash, iterations} at registration | `LocalStore.register` | [android-app/atlas_go/store.py L260](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py#L260) | Implemented |
| <a name="sec-id-email"></a>Identity proofing: email format | `clean_email` | [android-app/atlas_go/accounts.py L53](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/accounts.py#L53) | Implemented |
| <a name="sec-id-phone"></a>Identity proofing: phone normalised to E.164 | `clean_phone` | [android-app/atlas_go/accounts.py L60](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/accounts.py#L60) | Implemented |
| <a name="sec-id-licence"></a>Driver licence number (self-declared) | `clean_licence` | [android-app/atlas_go/accounts.py L88](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/accounts.py#L88) | Implemented |
| <a name="sec-id-business"></a>Food-business number (self-declared) | `clean_business` | [android-app/atlas_go/accounts.py L95](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/accounts.py#L95) | Implemented |
| <a name="sec-id-delete"></a>De-provision with re-authentication, anonymise history | `LocalStore.delete_account` | [android-app/atlas_go/store.py L333](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py#L333) | Implemented |
| <a name="sec-rbac-screens"></a>RBAC layer 1: screen allow-list per role | `AtlasGoApp.render` | [android-app/atlas_go/app.py L422](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/app.py#L422) | Implemented |
| <a name="sec-rbac-online"></a>RBAC layer 2: only drivers go online | `LocalStore.set_online` | [android-app/atlas_go/store.py L367](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py#L367) | Implemented |
| <a name="sec-rbac-location"></a>RBAC layer 2: only drivers share location | `LocalStore.update_location` | [android-app/atlas_go/store.py L377](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py#L377) | Implemented |
| <a name="sec-rbac-respond"></a>RBAC layer 2: a driver answers only their own job | `LocalStore.driver_respond` | [android-app/atlas_go/store.py L392](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py#L392) | Implemented |
| <a name="sec-rbac-book"></a>RBAC layer 2: only passengers or guests book | `LocalStore.book` | [android-app/atlas_go/store.py L422](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py#L422) | Implemented |
| <a name="sec-rbac-checkout"></a>RBAC layer 2: only passengers or guests order food | `LocalStore.checkout` | [android-app/atlas_go/store.py L557](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py#L557) | Implemented |
| <a name="sec-rbac-kitchen"></a>RBAC layer 2: a seller edits only their own kitchen | `LocalStore._my_kitchen` | [android-app/atlas_go/store.py L496](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py#L496) | Implemented |
| <a name="sec-pw-cli-b"></a>Lab B: registration and identity (experiments 9-11) | `exp_validation` | [security_lab/lab_b_registration_identity.py L28](https://github.com/FUllSCIPTS/ATLAS/blob/main/security_lab/lab_b_registration_identity.py#L28) | Explorer / lab |
| Lab D: integrity, sessions and lifecycle (experiments 16-20) | `exp_sessions` | [security_lab/lab_d_integrity_lifecycle.py L34](https://github.com/FUllSCIPTS/ATLAS/blob/main/security_lab/lab_d_integrity_lifecycle.py#L34) | Explorer / lab |

<a name="uml-security-gateway"></a>

### Security → Gateway auth

[Open in the explorer ↗](https://fullscipts.github.io/ATLAS/#security-gateway)

| Concept | Function / symbol | Location | Status |
| --- | --- | --- | --- |
| <a name="sec-gw-routes"></a>Route allow-list (method, role, regex) | `ROUTES` | [architecture-explorer/starter/services/gateway.py L15](../services/gateway.py#L15) | Demo-grade |
| <a name="sec-gw-proxy"></a>Authenticate, check role, assert identity, forward | `proxy` | [architecture-explorer/starter/services/gateway.py L47](../services/gateway.py#L47) | Demo-grade |
| <a name="sec-gw-keys"></a>Bearer keys per actor (demo defaults) | `KEYS` | [architecture-explorer/starter/packages/config.py L13](../packages/config.py#L13) | Demo-grade |
| <a name="sec-gw-equal"></a>Timing-safe comparison (hmac.compare_digest) | `equal` | [architecture-explorer/starter/packages/config.py L20](../packages/config.py#L20) | Demo-grade |
| <a name="sec-gw-internal"></a>Service re-check: internal token and actor role | `internal_actor` | [architecture-explorer/starter/packages/config.py L24](../packages/config.py#L24) | Demo-grade |
| <a name="sec-gw-trips"></a>Trip Service accepts only gateway-asserted riders | `book` | [architecture-explorer/starter/services/trips.py L32](../services/trips.py#L32) | Demo-grade |
| <a name="sec-gw-dispatch"></a>Dispatch Service accepts only gateway-asserted drivers | `offers` | [architecture-explorer/starter/services/dispatch.py L35](../services/dispatch.py#L35) | Demo-grade |
| <a name="sec-gw-lab"></a>Explorer lab: gateway checks step by step | `secGatewayRun` | [architecture-explorer/dist/security.js L367](../../dist/security.js#L367) | Explorer / lab |

<a name="uml-security-sso"></a>

### Security → Single sign-on

[Open in the explorer ↗](https://fullscipts.github.io/ATLAS/#security-sso)

| Concept | Function / symbol | Location | Status |
| --- | --- | --- | --- |
| <a name="sec-sso-target"></a>Where JWT validation would replace bearer keys | `proxy` | [architecture-explorer/starter/services/gateway.py L47](../services/gateway.py#L47) | Teaching extension |
| Bearer keys per actor (demo defaults) | `KEYS` | [architecture-explorer/starter/packages/config.py L13](../packages/config.py#L13) | Demo-grade |
| <a name="sec-sso-lab"></a>OIDC + PKCE flow with ES256 tokens | `secSsoNext` | [architecture-explorer/dist/security.js L420](../../dist/security.js#L420) | Explorer / lab |

<a name="uml-security-kerberos"></a>

### Security → Kerberos

[Open in the explorer ↗](https://fullscipts.github.io/ATLAS/#security-kerberos)

| Concept | Function / symbol | Location | Status |
| --- | --- | --- | --- |
| <a name="sec-krb-target"></a>What a Kerberos AP-REQ would replace in Dispatch | `internal_actor` | [architecture-explorer/starter/packages/config.py L24](../packages/config.py#L24) | Teaching extension |
| <a name="sec-krb-setup"></a>KDC database and string-to-key (PBKDF2) | `secKrbSetup` | [architecture-explorer/dist/security.js L500](../../dist/security.js#L500) | Explorer / lab |
| <a name="sec-krb-messages"></a>The six messages AS-REQ … AP-REP | `secKrbNext` | [architecture-explorer/dist/security.js L510](../../dist/security.js#L510) | Explorer / lab |
| <a name="sec-krb-ap"></a>Service checks: integrity, expiry, skew, replay cache | `secKrbVerifyAp` | [architecture-explorer/dist/security.js L583](../../dist/security.js#L583) | Explorer / lab |
| <a name="sec-krb-seal"></a>AES-256-GCM seal used for tickets | `secSeal` | [architecture-explorer/dist/security.js L82](../../dist/security.js#L82) | Explorer / lab |

<a name="uml-security-transport"></a>

### Security → mTLS & deployment

[Open in the explorer ↗](https://fullscipts.github.io/ATLAS/#security-transport)

| Concept | Function / symbol | Location | Status |
| --- | --- | --- | --- |
| <a name="sec-tls-ca"></a>Private CA, serverAuth and clientAuth certificates | `make_certs` | [prototype.zip → prototype/proto_run.py L28](https://github.com/FUllSCIPTS/ATLAS/blob/main/prototype.zip) | Implemented |
| <a name="sec-tls-client"></a>Client presents its certificate, verifies the server | `client_ctx` | [prototype.zip → prototype/proto_run.py L45](https://github.com/FUllSCIPTS/ATLAS/blob/main/prototype.zip) | Implemented |
| <a name="sec-tls-server"></a>Server requires a client certificate (CERT_REQUIRED) | `ctx.load_verify_locations(f"{certdir}/ca.crt"); ctx.verify_mode = ssl...` | [prototype.zip → prototype/module_server.py L84](https://github.com/FUllSCIPTS/ATLAS/blob/main/prototype.zip) | Implemented |
| <a name="sec-dep-headers"></a>Security headers and CSP | `securityHeaders` | [architecture-explorer/server.mjs L33](../../server.mjs#L33) | Implemented |
| <a name="sec-dep-reply"></a>Every response carries the headers | `reply` | [architecture-explorer/server.mjs L41](../../server.mjs#L41) | Implemented |
| <a name="sec-dep-loopback"></a>Listen on 127.0.0.1 only | `}).listen(port, host, () => console.log('ATLAS listening on http://${...` | [architecture-explorer/server.mjs L67](../../server.mjs#L67) | Implemented |
| <a name="sec-dep-systemd"></a>systemd sandbox (DynamicUser, ProtectSystem) | `DynamicUser=yes` | [architecture-explorer/deploy/atlas-explorer.service L10](../../deploy/atlas-explorer.service#L10) | Implemented |
| <a name="cr-sig-sign"></a>Sign the bundle: jarsigner SHA256withRSA, then verify | `main` | [android-app/scripts/sign-release.py L8](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/scripts/sign-release.py#L8) | Implemented |

<a name="uml-security-gaps"></a>

### Security → Gaps & exercises

[Open in the explorer ↗](https://fullscipts.github.io/ATLAS/#security-gaps)

| Concept | Function / symbol | Location | Status |
| --- | --- | --- | --- |
| Work factor and lockout limits | `PBKDF2_ITERATIONS` | [android-app/atlas_go/accounts.py L16](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/accounts.py#L16) | Implemented |
| Failure counter kept in memory only | `self.failures = {}          # email -> [count, locked_until]; memory ...` | [android-app/atlas_go/store.py L33](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py#L33) | Implemented |
| Bearer keys per actor (demo defaults) | `KEYS` | [architecture-explorer/starter/packages/config.py L13](../packages/config.py#L13) | Demo-grade |
| Service re-check: internal token and actor role | `internal_actor` | [architecture-explorer/starter/packages/config.py L24](../packages/config.py#L24) | Demo-grade |
| Driver licence number (self-declared) | `clean_licence` | [android-app/atlas_go/accounts.py L88](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/accounts.py#L88) | Implemented |
| Authenticate, check role, assert identity, forward | `proxy` | [architecture-explorer/starter/services/gateway.py L47](../services/gateway.py#L47) | Demo-grade |

<a name="uml-crypto-hashes"></a>

### Cryptography → Hashes & checksums

[Open in the explorer ↗](https://fullscipts.github.io/ATLAS/#crypto-hashes)

| Concept | Function / symbol | Location | Status |
| --- | --- | --- | --- |
| <a name="cr-hash-sums"></a>Release SHA256SUMS written by CI | `sha256sum release/*.apk release/*.aab > release/SHA256SUMS` | [.github/workflows/atlas-android.yml L100](https://github.com/FUllSCIPTS/ATLAS/blob/main/.github/workflows/atlas-android.yml#L100) | Implemented |
| <a name="cr-hash-handover"></a>Release SHA256SUMS for hand-over | `digest=hashlib.sha256((artifact/'release'/name).read_bytes()).hexdige...` | [android-app/scripts/finalize-handover.py L37](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/scripts/finalize-handover.py#L37) | Implemented |
| <a name="cr-hash-pin-tool"></a>Pinned build tool (bundletool SHA-256) | `echo 'a099cfa1543f55593bc2ed16a70a7c67fe54b1747bb7301f37fdfd6d91028e2...` | [.github/workflows/atlas-android.yml L66](https://github.com/FUllSCIPTS/ATLAS/blob/main/.github/workflows/atlas-android.yml#L66) | Implemented |
| <a name="cr-hash-record"></a>Signed bundle must equal the recorded SHA-256 | `assert actual == record['sha256'], 'Signed bundle does not match sign...` | [.github/workflows/publish-signed-android.yml L55](https://github.com/FUllSCIPTS/ATLAS/blob/main/.github/workflows/publish-signed-android.yml#L55) | Implemented |
| <a name="cr-hash-restore"></a>Restore signed bundle; both hashes must match | `restore` | [android-app/releases/restore-signed-bundle.py L22](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/releases/restore-signed-bundle.py#L22) | Implemented |
| <a name="cr-hash-inventory"></a>SHA-256 of every source file in the blueprint | `inventory` | [architecture-explorer/starter/scripts/generate_blueprint.py L204](../scripts/generate_blueprint.py#L204) | Implemented |
| <a name="cr-hash-checksum"></a>Non-cryptographic state checksum | `PaymentModule.checksum` | [prototype.zip → prototype/module_server.py L36](https://github.com/FUllSCIPTS/ATLAS/blob/main/prototype.zip) | Implemented |
| <a name="cr-hash-c3"></a>Recovery class C3: checksum mismatch → restore | `elif cls == "C3":     # checksum mismatch -> Tier-2 (p=.8) or Tier-3 ...` | [run_recovery_mc.py L31](https://github.com/FUllSCIPTS/ATLAS/blob/main/run_recovery_mc.py#L31) | Implemented |
| <a name="cr-hash-lab-avalanche"></a>Explorer lab: avalanche effect | `crUpdateAvalanche` | [architecture-explorer/dist/crypto.js L105](../../dist/crypto.js#L105) | Explorer / lab |
| <a name="cr-hash-lab-file"></a>Explorer lab: hash a download, compare with SHA256SUMS | `crHashFile` | [architecture-explorer/dist/crypto.js L98](../../dist/crypto.js#L98) | Explorer / lab |
| <a name="cr-hash-lab-checksum"></a>Explorer lab: checksum vs SHA-256 | `crChecksum` | [architecture-explorer/dist/crypto.js L118](../../dist/crypto.js#L118) | Explorer / lab |
| <a name="cr-hash-cli"></a>Lab A: hashing and integrity (experiments 1-7) | `exp_basics` | [security_lab/crypto_a_hashing.py L45](https://github.com/FUllSCIPTS/ATLAS/blob/main/security_lab/crypto_a_hashing.py#L45) | Explorer / lab |
| <a name="cr-hash-cli-checksum"></a>Lab A4: forging the prototype checksum | `exp_checksum` | [security_lab/crypto_a_hashing.py L129](https://github.com/FUllSCIPTS/ATLAS/blob/main/security_lab/crypto_a_hashing.py#L129) | Explorer / lab |
| <a name="cr-hash-cli-crc"></a>Lab A5: forging CRC32 | `crc32_forge` | [security_lab/crypto_a_hashing.py L149](https://github.com/FUllSCIPTS/ATLAS/blob/main/security_lab/crypto_a_hashing.py#L149) | Explorer / lab |
| <a name="cr-hash-cli-release"></a>Lab A6-A7: verify releases and CI pins | `exp_release` | [security_lab/crypto_a_hashing.py L181](https://github.com/FUllSCIPTS/ATLAS/blob/main/security_lab/crypto_a_hashing.py#L181) | Explorer / lab |
| <a name="cr-mac-cli"></a>Lab B: MACs, key derivation, randomness (experiments 8-10) | `exp_length_extension` | [security_lab/crypto_b_mac_kdf_random.py L95](https://github.com/FUllSCIPTS/ATLAS/blob/main/security_lab/crypto_b_mac_kdf_random.py#L95) | Explorer / lab |
| <a name="cr-mac-cli-pbkdf2"></a>Lab B9: PBKDF2 by hand, matching accounts.py | `pbkdf2_sha256` | [security_lab/crypto_b_mac_kdf_random.py L128](https://github.com/FUllSCIPTS/ATLAS/blob/main/security_lab/crypto_b_mac_kdf_random.py#L128) | Explorer / lab |
| <a name="cr-cli-runner"></a>Crypto lab runner: 20 experiments, 5 study paths | `if __name__ == '__main__':` | [security_lab/crypto_lab.py L39](https://github.com/FUllSCIPTS/ATLAS/blob/main/security_lab/crypto_lab.py#L39) | Explorer / lab |

<a name="uml-crypto-pki"></a>

### Cryptography → PKI & certificates

[Open in the explorer ↗](https://fullscipts.github.io/ATLAS/#crypto-pki)

| Concept | Function / symbol | Location | Status |
| --- | --- | --- | --- |
| <a name="cr-pki-ca"></a>Private CA for mutual TLS | `make_certs` | [prototype.zip → prototype/proto_run.py L28](https://github.com/FUllSCIPTS/ATLAS/blob/main/prototype.zip) | Implemented |
| <a name="cr-pki-client"></a>Client context: trust anchor + client certificate | `client_ctx` | [prototype.zip → prototype/proto_run.py L45](https://github.com/FUllSCIPTS/ATLAS/blob/main/prototype.zip) | Implemented |
| <a name="cr-pki-server"></a>Server: CERT_REQUIRED against ca.crt | `ctx.load_verify_locations(f"{certdir}/ca.crt"); ctx.verify_mode = ssl...` | [prototype.zip → prototype/module_server.py L84](https://github.com/FUllSCIPTS/ATLAS/blob/main/prototype.zip) | Implemented |
| <a name="cr-pki-webpki"></a>Web PKI: HTTPS tile download verified with certifi | `TileLoader._fetch` | [android-app/atlas_go/livemap.py L80](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/livemap.py#L80) | Implemented |
| <a name="cr-pki-cert"></a>Upload certificate (RSA-4096, self-signed) | — | [android-app/releases/upload-certificate.pem L1](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/releases/upload-certificate.pem#L1) | Implemented |
| <a name="cr-pki-pin"></a>Certificate pinning: SHA-256 of the DER certificate | `certificate_sha256` | [android-app/scripts/ci-sign-bundle.py L29](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/scripts/ci-sign-bundle.py#L29) | Implemented |
| <a name="cr-pki-pin-ci"></a>Publish workflow re-checks the pin | `assert fingerprint == record['upload_certificate_sha256'], 'Upload ce...` | [.github/workflows/publish-signed-android.yml L60](https://github.com/FUllSCIPTS/ATLAS/blob/main/.github/workflows/publish-signed-android.yml#L60) | Implemented |
| <a name="cr-pki-lab-pin"></a>Explorer lab: recompute the real pin | `crPin` | [architecture-explorer/dist/crypto.js L158](../../dist/crypto.js#L158) | Explorer / lab |
| <a name="cr-pki-lab-issue"></a>Explorer lab: issue a certificate | `crIssue` | [architecture-explorer/dist/crypto.js L176](../../dist/crypto.js#L176) | Explorer / lab |
| <a name="cr-pki-lab-verify"></a>Explorer lab: chain, CA flag, validity, EKU checks | `crVerifyCert` | [architecture-explorer/dist/crypto.js L196](../../dist/crypto.js#L196) | Explorer / lab |
| <a name="cr-pki-cli"></a>Lab C: certificates and PKI (experiments 11-14) | `exp_fingerprint` | [security_lab/crypto_c_pki.py L84](https://github.com/FUllSCIPTS/ATLAS/blob/main/security_lab/crypto_c_pki.py#L84) | Explorer / lab |
| <a name="cr-pki-cli-der"></a>Lab C12-C13: parse the DER, verify the self-signature | `parse_certificate` | [security_lab/crypto_c_pki.py L53](https://github.com/FUllSCIPTS/ATLAS/blob/main/security_lab/crypto_c_pki.py#L53) | Explorer / lab |
| <a name="cr-pki-cli-ca"></a>Lab C14: private CA chain validation | `validate` | [security_lab/crypto_c_pki.py L178](https://github.com/FUllSCIPTS/ATLAS/blob/main/security_lab/crypto_c_pki.py#L178) | Explorer / lab |
| <a name="cr-cli-common"></a>Crypto lab helpers: toy RSA, PKCS#1 v1.5, DER reader | `emsa_pkcs1_v15` | [security_lab/crypto_common.py L143](https://github.com/FUllSCIPTS/ATLAS/blob/main/security_lab/crypto_common.py#L143) | Explorer / lab |

<a name="uml-crypto-signatures"></a>

### Cryptography → Digital signatures

[Open in the explorer ↗](https://fullscipts.github.io/ATLAS/#crypto-signatures)

| Concept | Function / symbol | Location | Status |
| --- | --- | --- | --- |
| Sign the bundle: jarsigner SHA256withRSA, then verify | `main` | [android-app/scripts/sign-release.py L8](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/scripts/sign-release.py#L8) | Implemented |
| <a name="cr-sig-ci"></a>CI signing with the upload key from encrypted secrets | `main` | [android-app/scripts/ci-sign-bundle.py L37](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/scripts/ci-sign-bundle.py#L37) | Implemented |
| Certificate pinning: SHA-256 of the DER certificate | `certificate_sha256` | [android-app/scripts/ci-sign-bundle.py L29](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/scripts/ci-sign-bundle.py#L29) | Implemented |
| <a name="cr-sig-apk"></a>APK Signature Scheme v2/v3; verify with apksigner | `apksigner verify --print-certs atlas-go-1.2.0.apk` | [android-app/releases/1.2.0/README.md L19](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/releases/1.2.0/README.md?plain=1#L19) | Implemented |
| <a name="cr-sig-lab-keys"></a>Explorer lab: generate ECDSA or RSA key pair | `crSigKeys` | [architecture-explorer/dist/crypto.js L270](../../dist/crypto.js#L270) | Explorer / lab |
| <a name="cr-sig-lab-sign"></a>Explorer lab: hash-then-sign | `crSigSign` | [architecture-explorer/dist/crypto.js L282](../../dist/crypto.js#L282) | Explorer / lab |
| <a name="cr-sig-lab-verify"></a>Explorer lab: verify, tamper, wrong key | `crSigVerify` | [architecture-explorer/dist/crypto.js L293](../../dist/crypto.js#L293) | Explorer / lab |
| <a name="cr-sig-cli"></a>Lab D: digital signatures (experiments 15-17) | `exp_textbook` | [security_lab/crypto_d_signatures.py L33](https://github.com/FUllSCIPTS/ATLAS/blob/main/security_lab/crypto_d_signatures.py#L33) | Explorer / lab |
| <a name="cr-sig-cli-jar"></a>Lab D17: JAR signing and verification | `jar_verify` | [security_lab/crypto_d_signatures.py L107](https://github.com/FUllSCIPTS/ATLAS/blob/main/security_lab/crypto_d_signatures.py#L107) | Explorer / lab |

<a name="uml-crypto-pqc"></a>

### Cryptography → Post-quantum

[Open in the explorer ↗](https://fullscipts.github.io/ATLAS/#crypto-pqc)

| Concept | Function / symbol | Location | Status |
| --- | --- | --- | --- |
| Web PKI: HTTPS tile download verified with certifi | `TileLoader._fetch` | [android-app/atlas_go/livemap.py L80](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/livemap.py#L80) | Implemented |
| Private CA for mutual TLS | `make_certs` | [prototype.zip → prototype/proto_run.py L28](https://github.com/FUllSCIPTS/ATLAS/blob/main/prototype.zip) | Implemented |
| Sign the bundle: jarsigner SHA256withRSA, then verify | `main` | [android-app/scripts/sign-release.py L8](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/scripts/sign-release.py#L8) | Implemented |
| <a name="cr-pqc-lab-keys"></a>Lamport keys from SHA-256 only | `crLamportKeys` | [architecture-explorer/dist/crypto.js L328](../../dist/crypto.js#L328) | Explorer / lab |
| <a name="cr-pqc-lab-sign"></a>Lamport sign: reveal one secret per hash bit | `crLamportSign` | [architecture-explorer/dist/crypto.js L338](../../dist/crypto.js#L338) | Explorer / lab |
| <a name="cr-pqc-lab-verify"></a>Lamport verify | `crLamportVerify` | [architecture-explorer/dist/crypto.js L342](../../dist/crypto.js#L342) | Explorer / lab |
| <a name="cr-pqc-lab-forge"></a>Forgery after key reuse | `crLamportForge` | [architecture-explorer/dist/crypto.js L355](../../dist/crypto.js#L355) | Explorer / lab |
| <a name="cr-pqc-cli"></a>Lab E: post-quantum (experiments 18-20) | `exp_lamport` | [security_lab/crypto_e_post_quantum.py L52](https://github.com/FUllSCIPTS/ATLAS/blob/main/security_lab/crypto_e_post_quantum.py#L52) | Explorer / lab |
| <a name="cr-pqc-cli-forge"></a>Lab E19: forging after Lamport key reuse | `exp_lamport_reuse` | [security_lab/crypto_e_post_quantum.py L78](https://github.com/FUllSCIPTS/ATLAS/blob/main/security_lab/crypto_e_post_quantum.py#L78) | Explorer / lab |
| <a name="cr-pqc-cli-hybrid"></a>Lab E20: toy LWE KEM in a hybrid with DH | `exp_lwe_hybrid` | [security_lab/crypto_e_post_quantum.py L160](https://github.com/FUllSCIPTS/ATLAS/blob/main/security_lab/crypto_e_post_quantum.py#L160) | Explorer / lab |

<a name="uml-crypto-gaps"></a>

### Cryptography → Gaps & exercises

[Open in the explorer ↗](https://fullscipts.github.io/ATLAS/#crypto-gaps)

| Concept | Function / symbol | Location | Status |
| --- | --- | --- | --- |
| Non-cryptographic state checksum | `PaymentModule.checksum` | [prototype.zip → prototype/module_server.py L36](https://github.com/FUllSCIPTS/ATLAS/blob/main/prototype.zip) | Implemented |
| Release SHA256SUMS written by CI | `sha256sum release/*.apk release/*.aab > release/SHA256SUMS` | [.github/workflows/atlas-android.yml L100](https://github.com/FUllSCIPTS/ATLAS/blob/main/.github/workflows/atlas-android.yml#L100) | Implemented |
| Upload certificate (RSA-4096, self-signed) | — | [android-app/releases/upload-certificate.pem L1](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/releases/upload-certificate.pem#L1) | Implemented |
| Web PKI: HTTPS tile download verified with certifi | `TileLoader._fetch` | [android-app/atlas_go/livemap.py L80](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/livemap.py#L80) | Implemented |
| Service re-check: internal token and actor role | `internal_actor` | [architecture-explorer/starter/packages/config.py L24](../packages/config.py#L24) | Demo-grade |

<!-- END SECURITY CATALOG -->

## Machine learning and optimisation catalogue

<!-- BEGIN ML CATALOG -->

Every concept in the Architecture Explorer's **ML & Optimisation** tab, linked to the function, constant or
file that implements it, starting with the paper's coupling optimiser (`Sim.bip`). Each row has a stable anchor
that the explorer links to. Status: **Paper (research code)** (`atlas_sim.zip` and `run_*.py` on `main`, as
evaluated in the article), **App / starter (synthetic data)** (ATLAS Go or the server starter, trained on
simulations) or **Explorer / lab** (teaching code in the explorer or `ml_lab/`). Teaching guide:
[docs/MACHINE_LEARNING_OPTIMISATION.md](https://github.com/FUllSCIPTS/ATLAS/blob/main/docs/MACHINE_LEARNING_OPTIMISATION.md).
Generated by `scripts/security_catalog.py`.

<a name="uml-ml-optimizer"></a>

### ML & Optimisation → Coupling BIP (the paper's optimiser)

[Open in the explorer ↗](https://fullscipts.github.io/ATLAS/#ml-optimizer)

| Concept | Function / symbol | Location | Status |
| --- | --- | --- | --- |
| <a name="ml-bip-modules"></a>Six modules: visit ratio and service demand | `VISIT` | [atlas_sim.zip → atlas_sim/traffic.py L13](https://github.com/FUllSCIPTS/ATLAS/blob/main/atlas_sim.zip) | Paper (research code) |
| <a name="ml-bip-params"></a>Objective weights, constraint limits, risk model | `class Params:` | [atlas_sim.zip → atlas_sim/cluster.py L21](https://github.com/FUllSCIPTS/ATLAS/blob/main/atlas_sim.zip) | Paper (research code) |
| <a name="ml-bip-model"></a>Predict latency, cost, risk, availability of all 2^n configurations | `Sim.eval_all` | [atlas_sim.zip → atlas_sim/cluster.py L166](https://github.com/FUllSCIPTS/ATLAS/blob/main/atlas_sim.zip) | Paper (research code) |
| <a name="ml-bip-ref"></a>Same model for one configuration (reference point L0, C0) | `Sim.eval_config` | [atlas_sim.zip → atlas_sim/cluster.py L146](https://github.com/FUllSCIPTS/ATLAS/blob/main/atlas_sim.zip) | Paper (research code) |
| <a name="ml-bip-solve"></a>Solve the BIP: objective J, constraints, argmin over all configurations | `Sim.bip` | [atlas_sim.zip → atlas_sim/cluster.py L191](https://github.com/FUllSCIPTS/ATLAS/blob/main/atlas_sim.zip) | Paper (research code) |
| <a name="ml-bip-loop"></a>Decision epoch: forecast, anomaly score, BIP, overrides, hysteresis | `Sim.run` | [atlas_sim.zip → atlas_sim/cluster.py L280](https://github.com/FUllSCIPTS/ATLAS/blob/main/atlas_sim.zip) | Paper (research code) |
| <a name="ml-bip-apply"></a>Apply: dual-run extraction, merge back | `Sim.apply` | [atlas_sim.zip → atlas_sim/cluster.py L218](https://github.com/FUllSCIPTS/ATLAS/blob/main/atlas_sim.zip) | Paper (research code) |
| <a name="ml-bip-fsm"></a>Ablation baseline: fixed load thresholds | `Sim.fsm_thresholds` | [atlas_sim.zip → atlas_sim/cluster.py L386](https://github.com/FUllSCIPTS/ATLAS/blob/main/atlas_sim.zip) | Paper (research code) |
| <a name="ml-bip-lab"></a>Explorer lab: Sim.eval_all + Sim.bip replica | `mlBipSolve` | [architecture-explorer/dist/ml.js L169](../../dist/ml.js#L169) | Explorer / lab |
| <a name="ml-bip-lab-eval"></a>Explorer lab: one configuration's latency, cost, risk | `mlEvalConfig` | [architecture-explorer/dist/ml.js L147](../../dist/ml.js#L147) | Explorer / lab |
| <a name="ml-bip-cli"></a>Command-line lab: load sweep with the real Sim.bip | `section_bip` | [ml_lab/ml_optimisation_lab.py L67](https://github.com/FUllSCIPTS/ATLAS/blob/main/ml_lab/ml_optimisation_lab.py#L67) | Explorer / lab |
| <a name="ml-bip-cli-inside"></a>Command-line lab: every configuration at one load | `section_inside` | [ml_lab/ml_optimisation_lab.py L86](https://github.com/FUllSCIPTS/ATLAS/blob/main/ml_lab/ml_optimisation_lab.py#L86) | Explorer / lab |
| <a name="ml-bip-cli-anomaly"></a>Command-line lab: anomaly score raises crash risk | `section_anomaly` | [ml_lab/ml_optimisation_lab.py L106](https://github.com/FUllSCIPTS/ATLAS/blob/main/ml_lab/ml_optimisation_lab.py#L106) | Explorer / lab |
| <a name="ml-x-opt-runner"></a>Optimisation lab runner: 20 experiments, 7 study paths | `main` | [ml_lab/optimisation/run_optimisation.py L39](https://github.com/FUllSCIPTS/ATLAS/blob/main/ml_lab/optimisation/run_optimisation.py#L39) | Explorer / lab |
| <a name="ml-x-opt-ga"></a>OPT 17: genetic algorithm vs Sim.bip | `evolve` | [ml_lab/optimisation/opt17_genetic_algorithm.py L18](https://github.com/FUllSCIPTS/ATLAS/blob/main/ml_lab/optimisation/opt17_genetic_algorithm.py#L18) | Explorer / lab |
| <a name="ml-x-opt-pareto"></a>OPT 20: latency-cost Pareto front of the couplings | `pareto_ranks` | [ml_lab/optimisation/opt20_multi_objective_pareto.py L17](https://github.com/FUllSCIPTS/ATLAS/blob/main/ml_lab/optimisation/opt20_multi_objective_pareto.py#L17) | Explorer / lab |
| <a name="ml-x-opt-cores"></a>OPT 04: KKT core allocation across the six modules | `main` | [ml_lab/optimisation/opt04_constrained_core_allocation.py L17](https://github.com/FUllSCIPTS/ATLAS/blob/main/ml_lab/optimisation/opt04_constrained_core_allocation.py#L17) | Explorer / lab |
| <a name="ml-x-opt-dpscale"></a>OPT 14: DP replica schedule with switching costs | `main` | [ml_lab/optimisation/opt14_dp_autoscaling_schedule.py L16](https://github.com/FUllSCIPTS/ATLAS/blob/main/ml_lab/optimisation/opt14_dp_autoscaling_schedule.py#L16) | Explorer / lab |

<a name="uml-ml-solvers"></a>

### ML & Optimisation → Solvers

[Open in the explorer ↗](https://fullscipts.github.io/ATLAS/#ml-solvers)

| Concept | Function / symbol | Location | Status |
| --- | --- | --- | --- |
| Solve the BIP: objective J, constraints, argmin over all configurations | `Sim.bip` | [atlas_sim.zip → atlas_sim/cluster.py L191](https://github.com/FUllSCIPTS/ATLAS/blob/main/atlas_sim.zip) | Paper (research code) |
| <a name="ml-sol-instance"></a>Random linearised BIP instances, n = 6 ... 500 | `instance` | [run_bip_timing.py L15](https://github.com/FUllSCIPTS/ATLAS/blob/main/run_bip_timing.py#L15) | Paper (research code) |
| <a name="ml-sol-lpround"></a>LP relaxation + risk-aware rounding + greedy repair | `lp_round` | [run_bip_timing.py L31](https://github.com/FUllSCIPTS/ATLAS/blob/main/run_bip_timing.py#L31) | Paper (research code) |
| <a name="ml-sol-milp"></a>Branch-and-bound (HiGHS via scipy.optimize.milp) | `m = milp(f, constraints=LinearConstraint(A, -np.inf, ub), integrality...` | [run_bip_timing.py L60](https://github.com/FUllSCIPTS/ATLAS/blob/main/run_bip_timing.py#L60) | Paper (research code) |
| <a name="ml-sol-model"></a>Nonlinear model used to judge every method | `model` | [run_round2.py L36](https://github.com/FUllSCIPTS/ATLAS/blob/main/run_round2.py#L36) | Paper (research code) |
| <a name="ml-sol-solveall"></a>Exact enumeration vs linearised BIP vs LP method | `solve_all` | [run_round2.py L86](https://github.com/FUllSCIPTS/ATLAS/blob/main/run_round2.py#L86) | Paper (research code) |
| <a name="ml-sol-repair"></a>Phase 3: verify on the nonlinear model, greedy flips | `repair` | [run_round2.py L67](https://github.com/FUllSCIPTS/ATLAS/blob/main/run_round2.py#L67) | Paper (research code) |
| <a name="ml-sol-refined"></a>Sequential linearisation | `solve_refined` | [run_round2.py L381](https://github.com/FUllSCIPTS/ATLAS/blob/main/run_round2.py#L381) | Paper (research code) |
| <a name="ml-sol-local"></a>1-flip local search on the nonlinear objective | `local_search` | [run_round2.py L364](https://github.com/FUllSCIPTS/ATLAS/blob/main/run_round2.py#L364) | Paper (research code) |
| <a name="ml-sol-lab"></a>Explorer lab: enumerate 2^n in the browser | `mlEnumerateTiming` | [architecture-explorer/dist/ml.js L248](../../dist/ml.js#L248) | Explorer / lab |
| <a name="ml-sol-cli"></a>Command-line lab: enumeration vs branch-and-bound vs LP | `section_solvers` | [ml_lab/ml_optimisation_lab.py L126](https://github.com/FUllSCIPTS/ATLAS/blob/main/ml_lab/ml_optimisation_lab.py#L126) | Explorer / lab |
| <a name="ml-x-opt-bb"></a>OPT 08: branch-and-bound by hand on the coupling BIP | `branch_and_bound` | [ml_lab/optimisation/opt08_branch_and_bound.py L19](https://github.com/FUllSCIPTS/ATLAS/blob/main/ml_lab/optimisation/opt08_branch_and_bound.py#L19) | Explorer / lab |
| <a name="ml-x-opt-tabu"></a>OPT 15: local search and tabu search on a 60-module BIP | `tabu` | [ml_lab/optimisation/opt15_local_search_tabu.py L40](https://github.com/FUllSCIPTS/ATLAS/blob/main/ml_lab/optimisation/opt15_local_search_tabu.py#L40) | Explorer / lab |
| <a name="ml-x-opt-lp"></a>OPT 05-06: LP, duality and shadow prices | `solve` | [ml_lab/optimisation/opt05_linear_programming_transport.py L26](https://github.com/FUllSCIPTS/ATLAS/blob/main/ml_lab/optimisation/opt05_linear_programming_transport.py#L26) | Explorer / lab |
| <a name="ml-x-opt-sa"></a>OPT 16: simulated annealing | `anneal` | [ml_lab/optimisation/opt16_simulated_annealing.py L18](https://github.com/FUllSCIPTS/ATLAS/blob/main/ml_lab/optimisation/opt16_simulated_annealing.py#L18) | Explorer / lab |
| <a name="ml-x-opt-gd"></a>OPT 01-03: gradient descent, Adam, Newton and BFGS | `optimise` | [ml_lab/optimisation/opt02_momentum_and_adam.py L31](https://github.com/FUllSCIPTS/ATLAS/blob/main/ml_lab/optimisation/opt02_momentum_and_adam.py#L31) | Explorer / lab |

<a name="uml-ml-forecasting"></a>

### ML & Optimisation → Forecasting

[Open in the explorer ↗](https://fullscipts.github.io/ATLAS/#ml-forecasting)

| Concept | Function / symbol | Location | Status |
| --- | --- | --- | --- |
| <a name="ml-fc-trace"></a>Paper traffic model: daily, weekly, noise, flash sales | `ecommerce_trace` | [atlas_sim.zip → atlas_sim/traffic.py L17](https://github.com/FUllSCIPTS/ATLAS/blob/main/atlas_sim.zip) | Paper (research code) |
| <a name="ml-fc-lstm"></a>LSTM / Bi-LSTM forecaster (2 x 128, dropout 0.2) | `class LSTMForecaster(nn.Module):` | [atlas_sim.zip → atlas_sim/forecast.py L11](https://github.com/FUllSCIPTS/ATLAS/blob/main/atlas_sim.zip) | Paper (research code) |
| <a name="ml-fc-train"></a>Training: Adam, gradient clipping, early stopping | `train` | [atlas_sim.zip → atlas_sim/forecast.py L51](https://github.com/FUllSCIPTS/ATLAS/blob/main/atlas_sim.zip) | Paper (research code) |
| <a name="ml-fc-ar"></a>Baseline: Ridge autoregression | `fit_ar` | [atlas_sim.zip → atlas_sim/forecast.py L117](https://github.com/FUllSCIPTS/ATLAS/blob/main/atlas_sim.zip) | Paper (research code) |
| <a name="ml-fc-naive"></a>Baseline: seasonal naive | `seasonal_naive` | [atlas_sim.zip → atlas_sim/forecast.py L106](https://github.com/FUllSCIPTS/ATLAS/blob/main/atlas_sim.zip) | Paper (research code) |
| <a name="ml-fc-run"></a>Experiment: 3 seeds, horizons 5, 15, 60 min | `H` | [run_forecast.py L14](https://github.com/FUllSCIPTS/ATLAS/blob/main/run_forecast.py#L14) | Paper (research code) |
| <a name="ml-fc-starter"></a>Starter DemandLSTM trained with Adam | `train` | [architecture-explorer/starter/ml/forecast.py L20](../ml/forecast.py#L20) | App / starter (synthetic data) |
| <a name="ml-fc-app"></a>App LSTM in numpy with a hand-written Adam step | `LSTM.step` | [android-app/training/city_sim.py L214](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/training/city_sim.py#L214) | App / starter (synthetic data) |
| Decision epoch: forecast, anomaly score, BIP, overrides, hysteresis | `Sim.run` | [atlas_sim.zip → atlas_sim/cluster.py L280](https://github.com/FUllSCIPTS/ATLAS/blob/main/atlas_sim.zip) | Paper (research code) |
| <a name="ml-fc-lab"></a>Explorer lab: AR forecaster, gradient descent vs Adam | `mlTrainForecaster` | [architecture-explorer/dist/ml.js L306](../../dist/ml.js#L306) | Explorer / lab |
| <a name="ml-fc-cli"></a>Command-line lab: gradient descent vs Adam vs least squares | `section_training` | [ml_lab/ml_optimisation_lab.py L157](https://github.com/FUllSCIPTS/ATLAS/blob/main/ml_lab/ml_optimisation_lab.py#L157) | Explorer / lab |
| <a name="ml-x-ml-runner"></a>ML lab runner: 20 experiments, 7 study paths | `main` | [ml_lab/machine_learning/run_ml.py L39](https://github.com/FUllSCIPTS/ATLAS/blob/main/ml_lab/machine_learning/run_ml.py#L39) | Explorer / lab |
| <a name="ml-x-ml-hw"></a>ML 16: Holt-Winters and forecasting baselines | `holt_winters` | [ml_lab/machine_learning/ml16_time_series_forecasting.py L16](https://github.com/FUllSCIPTS/ATLAS/blob/main/ml_lab/machine_learning/ml16_time_series_forecasting.py#L16) | Explorer / lab |
| <a name="ml-x-ml-cv"></a>ML 11: time-series cross-validation and leakage | `main` | [ml_lab/machine_learning/ml11_cross_validation_leakage.py L18](https://github.com/FUllSCIPTS/ATLAS/blob/main/ml_lab/machine_learning/ml11_cross_validation_leakage.py#L18) | Explorer / lab |
| <a name="ml-x-ml-drift"></a>ML 17: concept drift and online learning | `main` | [ml_lab/machine_learning/ml17_concept_drift_online.py L16](https://github.com/FUllSCIPTS/ATLAS/blob/main/ml_lab/machine_learning/ml17_concept_drift_online.py#L16) | Explorer / lab |
| <a name="ml-x-opt-bo"></a>OPT 19: Bayesian optimisation of the forecaster | `main` | [ml_lab/optimisation/opt19_bayesian_optimisation.py L45](https://github.com/FUllSCIPTS/ATLAS/blob/main/ml_lab/optimisation/opt19_bayesian_optimisation.py#L45) | Explorer / lab |

<a name="uml-ml-anomaly"></a>

### ML & Optimisation → Isolation Forest

[Open in the explorer ↗](https://fullscipts.github.io/ATLAS/#ml-anomaly)

| Concept | Function / symbol | Location | Status |
| --- | --- | --- | --- |
| <a name="ml-an-telemetry"></a>Telemetry and injected fault types | `telemetry` | [atlas_sim.zip → atlas_sim/traffic.py L100](https://github.com/FUllSCIPTS/ATLAS/blob/main/atlas_sim.zip) | Paper (research code) |
| <a name="ml-an-fit"></a>Fit on unlabelled telemetry (100 trees, 256 samples) | `m = IsolationForest(n_estimators=100, max_samples=256, contamination=...` | [run_anomaly.py L66](https://github.com/FUllSCIPTS/ATLAS/blob/main/run_anomaly.py#L66) | Paper (research code) |
| <a name="ml-an-run"></a>Isolation Forest, normalised score (paper experiment) | `norm_score` | [run_anomaly.py L55](https://github.com/FUllSCIPTS/ATLAS/blob/main/run_anomaly.py#L55) | Paper (research code) |
| <a name="ml-an-score"></a>Score inside the simulator; blame a module | `Sim.score` | [atlas_sim.zip → atlas_sim/cluster.py L395](https://github.com/FUllSCIPTS/ATLAS/blob/main/atlas_sim.zip) | Paper (research code) |
| <a name="ml-an-fast"></a>Path-length scorer re-implemented for one row | `FastIForest.score_samples` | [atlas_sim.zip → atlas_sim/cluster.py L523](https://github.com/FUllSCIPTS/ATLAS/blob/main/atlas_sim.zip) | Paper (research code) |
| Solve the BIP: objective J, constraints, argmin over all configurations | `Sim.bip` | [atlas_sim.zip → atlas_sim/cluster.py L191](https://github.com/FUllSCIPTS/ATLAS/blob/main/atlas_sim.zip) | Paper (research code) |
| <a name="ml-an-starter"></a>Starter: acceptance model + driver Isolation Forest | `train` | [architecture-explorer/starter/ml/discrete.py L8](../ml/discrete.py#L8) | App / starter (synthetic data) |
| <a name="ml-an-serve"></a>Starter: anomaly flag per driver in the scoring API | `score` | [architecture-explorer/starter/ml/serve.py L48](../ml/serve.py#L48) | App / starter (synthetic data) |
| <a name="ml-an-lab"></a>Explorer lab: grow an Isolation Forest | `mlForestGrow` | [architecture-explorer/dist/ml.js L392](../../dist/ml.js#L392) | Explorer / lab |
| <a name="ml-an-cli"></a>Command-line lab: Isolation Forest on paper telemetry | `section_iforest` | [ml_lab/ml_optimisation_lab.py L212](https://github.com/FUllSCIPTS/ATLAS/blob/main/ml_lab/ml_optimisation_lab.py#L212) | Explorer / lab |
| <a name="ml-x-ml-detect"></a>ML 15: z-score, Mahalanobis, Isolation Forest, LOF | `main` | [ml_lab/machine_learning/ml15_anomaly_detection.py L18](https://github.com/FUllSCIPTS/ATLAS/blob/main/ml_lab/machine_learning/ml15_anomaly_detection.py#L18) | Explorer / lab |
| <a name="ml-x-ml-pca"></a>ML 14: PCA reconstruction error | `main` | [ml_lab/machine_learning/ml14_pca.py L17](https://github.com/FUllSCIPTS/ATLAS/blob/main/ml_lab/machine_learning/ml14_pca.py#L17) | Explorer / lab |
| <a name="ml-x-ml-logit"></a>ML 03: logistic regression from scratch | `sigmoid` | [ml_lab/machine_learning/ml03_logistic_regression.py L16](https://github.com/FUllSCIPTS/ATLAS/blob/main/ml_lab/machine_learning/ml03_logistic_regression.py#L16) | Explorer / lab |
| <a name="ml-x-ml-ens"></a>ML 07: forests and boosting | `main` | [ml_lab/machine_learning/ml07_ensembles.py L18](https://github.com/FUllSCIPTS/ATLAS/blob/main/ml_lab/machine_learning/ml07_ensembles.py#L18) | Explorer / lab |
| <a name="ml-x-ml-nn"></a>ML 09: neural network with backpropagation | `main` | [ml_lab/machine_learning/ml09_neural_network_backprop.py L17](https://github.com/FUllSCIPTS/ATLAS/blob/main/ml_lab/machine_learning/ml09_neural_network_backprop.py#L17) | Explorer / lab |

<a name="uml-ml-rl"></a>

### ML & Optimisation → Reinforcement learning

[Open in the explorer ↗](https://fullscipts.github.io/ATLAS/#ml-rl)

| Concept | Function / symbol | Location | Status |
| --- | --- | --- | --- |
| <a name="ml-rl-ride"></a>Ride dispatch: REINFORCE training | `train_ride` | [android-app/training/rl_sim.py L42](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/training/rl_sim.py#L42) | App / starter (synthetic data) |
| <a name="ml-rl-weights"></a>Approved dispatch weights (policy v1.4) | `RIDE_WEIGHTS` | [android-app/atlas_go/learned.py L13](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/learned.py#L13) | App / starter (synthetic data) |
| <a name="ml-rl-rank"></a>Dispatch: softmax over candidate drivers | `rank` | [android-app/atlas_go/intelligence.py L266](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py#L266) | App / starter (synthetic data) |
| <a name="ml-rl-learnlab"></a>On-device learning lab (REINFORCE, sandbox) | `LearningLab.train` | [android-app/atlas_go/intelligence.py L415](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py#L415) | App / starter (synthetic data) |
| <a name="ml-rl-food"></a>Courier timing: tabular Q-learning | `train_food` | [android-app/training/rl_sim.py L88](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/training/rl_sim.py#L88) | App / starter (synthetic data) |
| <a name="ml-rl-courier"></a>Courier plan from the learned Q-table | `courier_plan` | [android-app/atlas_go/intelligence.py L336](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py#L336) | App / starter (synthetic data) |
| <a name="ml-rl-accept"></a>Acceptance: Beta(9, 1) posterior mean | `acceptance` | [android-app/atlas_go/intelligence.py L292](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py#L292) | App / starter (synthetic data) |
| <a name="ml-rl-supply"></a>Driver supply agent with hindsight updates | `run_rl` | [android-app/training/city_sim.py L152](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/training/city_sim.py#L152) | App / starter (synthetic data) |
| <a name="ml-rl-bandit"></a>Starter: action values per demand bucket | `fit` | [architecture-explorer/starter/ml/rl.py L32](../ml/rl.py#L32) | App / starter (synthetic data) |
| <a name="ml-rl-approve"></a>Starter: held-out approval gate before activation | `approve` | [architecture-explorer/starter/ml/rl.py L51](../ml/rl.py#L51) | App / starter (synthetic data) |
| <a name="ml-rl-lab"></a>Explorer lab: REINFORCE (LearningLab.train port) | `mlRlTrain` | [architecture-explorer/dist/ml.js L460](../../dist/ml.js#L460) | Explorer / lab |
| <a name="ml-rl-cli"></a>Command-line lab: REINFORCE and Q-learning | `section_rl` | [ml_lab/ml_optimisation_lab.py L234](https://github.com/FUllSCIPTS/ATLAS/blob/main/ml_lab/ml_optimisation_lab.py#L234) | Explorer / lab |
| <a name="ml-x-ml-q"></a>ML 20: Q-learning the courier table | `main` | [ml_lab/machine_learning/ml20_q_learning_courier.py L22](https://github.com/FUllSCIPTS/ATLAS/blob/main/ml_lab/machine_learning/ml20_q_learning_courier.py#L22) | Explorer / lab |
| <a name="ml-x-ml-bandit"></a>ML 19: epsilon-greedy, UCB1, Thompson | `simulate` | [ml_lab/machine_learning/ml19_bandits.py L18](https://github.com/FUllSCIPTS/ATLAS/blob/main/ml_lab/machine_learning/ml19_bandits.py#L18) | Explorer / lab |
| <a name="ml-x-ml-rank"></a>ML 18: learning to rank dispatch candidates | `main` | [ml_lab/machine_learning/ml18_learning_to_rank.py L20](https://github.com/FUllSCIPTS/ATLAS/blob/main/ml_lab/machine_learning/ml18_learning_to_rank.py#L20) | Explorer / lab |
| <a name="ml-x-opt-es"></a>OPT 18: ES, DE and PSO tune the dispatch weights | `dispatch_objective` | [ml_lab/optimisation/opt18_evolution_strategies_de_pso.py L22](https://github.com/FUllSCIPTS/ATLAS/blob/main/ml_lab/optimisation/opt18_evolution_strategies_de_pso.py#L22) | Explorer / lab |

<a name="uml-ml-evaluation"></a>

### ML & Optimisation → Tuning & evaluation

[Open in the explorer ↗](https://fullscipts.github.io/ATLAS/#ml-evaluation)

| Concept | Function / symbol | Location | Status |
| --- | --- | --- | --- |
| <a name="ml-ev-tune"></a>Grid search on validation seeds | `tune` | [run_cluster.py L110](https://github.com/FUllSCIPTS/ATLAS/blob/main/run_cluster.py#L110) | Paper (research code) |
| <a name="ml-ev-grid"></a>ATLAS tuning grid | `"atlas": [dict(switch_pen=a, rho_max=b, hpa_target=c) for a in (.02, ...` | [run_cluster.py L165](https://github.com/FUllSCIPTS/ATLAS/blob/main/run_cluster.py#L165) | Paper (research code) |
| <a name="ml-ev-ablation"></a>Ablation: remove one component at a time | `if "ablation" in which:` | [run_cluster.py L209](https://github.com/FUllSCIPTS/ATLAS/blob/main/run_cluster.py#L209) | Paper (research code) |
| <a name="ml-ev-compare"></a>Paired Wilcoxon test + rank-biserial effect size | `compare` | [run_cluster.py L134](https://github.com/FUllSCIPTS/ATLAS/blob/main/run_cluster.py#L134) | Paper (research code) |
| <a name="ml-ev-holm"></a>Holm-Bonferroni correction | `holm` | [run_cluster.py L145](https://github.com/FUllSCIPTS/ATLAS/blob/main/run_cluster.py#L145) | Paper (research code) |
| <a name="ml-ev-stat"></a>Mean, SD, 95 % t-interval over 30 runs | `stat_block` | [run_cluster.py L120](https://github.com/FUllSCIPTS/ATLAS/blob/main/run_cluster.py#L120) | Paper (research code) |
| <a name="ml-ev-boot"></a>Block bootstrap CI for forecast errors | `block_bootstrap_ci` | [atlas_sim.zip → atlas_sim/forecast.py L139](https://github.com/FUllSCIPTS/ATLAS/blob/main/atlas_sim.zip) | Paper (research code) |
| Ablation baseline: fixed load thresholds | `Sim.fsm_thresholds` | [atlas_sim.zip → atlas_sim/cluster.py L386](https://github.com/FUllSCIPTS/ATLAS/blob/main/atlas_sim.zip) | Paper (research code) |
| <a name="ml-x-ml-metrics"></a>ML 10: metrics under class imbalance | `main` | [ml_lab/machine_learning/ml10_metrics_and_imbalance.py L18](https://github.com/FUllSCIPTS/ATLAS/blob/main/ml_lab/machine_learning/ml10_metrics_and_imbalance.py#L18) | Explorer / lab |
| <a name="ml-x-ml-bv"></a>ML 02: bias, variance and ridge | `main` | [ml_lab/machine_learning/ml02_bias_variance_regularisation.py L18](https://github.com/FUllSCIPTS/ATLAS/blob/main/ml_lab/machine_learning/ml02_bias_variance_regularisation.py#L18) | Explorer / lab |

<a name="uml-ml-gaps"></a>

### ML & Optimisation → Gaps & exercises

[Open in the explorer ↗](https://fullscipts.github.io/ATLAS/#ml-gaps)

| Concept | Function / symbol | Location | Status |
| --- | --- | --- | --- |
| Six modules: visit ratio and service demand | `VISIT` | [atlas_sim.zip → atlas_sim/traffic.py L13](https://github.com/FUllSCIPTS/ATLAS/blob/main/atlas_sim.zip) | Paper (research code) |
| Solve the BIP: objective J, constraints, argmin over all configurations | `Sim.bip` | [atlas_sim.zip → atlas_sim/cluster.py L191](https://github.com/FUllSCIPTS/ATLAS/blob/main/atlas_sim.zip) | Paper (research code) |
| Objective weights, constraint limits, risk model | `class Params:` | [atlas_sim.zip → atlas_sim/cluster.py L21](https://github.com/FUllSCIPTS/ATLAS/blob/main/atlas_sim.zip) | Paper (research code) |
| Training: Adam, gradient clipping, early stopping | `train` | [atlas_sim.zip → atlas_sim/forecast.py L51](https://github.com/FUllSCIPTS/ATLAS/blob/main/atlas_sim.zip) | Paper (research code) |
| On-device learning lab (REINFORCE, sandbox) | `LearningLab.train` | [android-app/atlas_go/intelligence.py L415](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py#L415) | App / starter (synthetic data) |
| Starter: action values per demand bucket | `fit` | [architecture-explorer/starter/ml/rl.py L32](../ml/rl.py#L32) | App / starter (synthetic data) |

<!-- END ML CATALOG -->

## Data structures and algorithms catalogue

<!-- BEGIN DSA CATALOG -->

Every concept in the Architecture Explorer's **Data Structures** tab, linked to the function, constant or file
that implements it. Status: **Implemented** (the idea runs in ATLAS Go), **Related** (the app does something
similar without this exact structure) or **Explorer / lab** (the course implementation in `dsa_lab/experiments.py`
on `main`, or the explorer's own port in `dist/dsa.js`). Teaching guide:
[docs/DATA_STRUCTURES_ALGORITHMS.md](https://github.com/FUllSCIPTS/ATLAS/blob/main/docs/DATA_STRUCTURES_ALGORITHMS.md).
Generated by `scripts/security_catalog.py`.

<a name="uml-dsa-complexity"></a>

### Data Structures → Complexity

[Open in the explorer ↗](https://fullscipts.github.io/ATLAS/#dsa-complexity)

| Concept | Function / symbol | Location | Status |
| --- | --- | --- | --- |
| <a name="dsa-app-online"></a>Linear scan: drivers that are online | `LocalStore.online_drivers` | [android-app/atlas_go/store.py L359](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py#L359) | Implemented |
| <a name="dsa-app-history"></a>Linear scan: the user's ride and order history | `LocalStore.my_history` | [android-app/atlas_go/store.py L653](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py#L653) | Implemented |
| <a name="dsa-app-distances"></a>2-D table lookup DISTANCES[pickup][destination] | `DISTANCES` | [android-app/atlas_go/domain.py L5](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/domain.py#L5) | Implemented |
| <a name="dsa-app-nearest"></a>Minimum selection: nearest saved place | `nearest_place` | [android-app/atlas_go/geo.py L60](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/geo.py#L60) | Implemented |
| <a name="dsa-app-tiles"></a>Grid indexing: tiles that cover the view | `tile_range` | [android-app/atlas_go/geo.py L105](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/geo.py#L105) | Implemented |
| <a name="dsa-app-book"></a>ADT operation: book a ride | `LocalStore.book` | [android-app/atlas_go/store.py L422](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py#L422) | Implemented |
| <a name="dsa-app-checkout"></a>ADT operation: check out a cart | `LocalStore.checkout` | [android-app/atlas_go/store.py L557](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py#L557) | Implemented |
| <a name="dsa-lab-linear"></a>Linear search with a comparison count | `linear_search` | [dsa_lab/experiments.py L41](https://github.com/FUllSCIPTS/ATLAS/blob/main/dsa_lab/experiments.py#L41) | Explorer / lab |
| <a name="dsa-lab-binary"></a>Binary search with a comparison count | `binary_search` | [dsa_lab/experiments.py L51](https://github.com/FUllSCIPTS/ATLAS/blob/main/dsa_lab/experiments.py#L51) | Explorer / lab |
| <a name="dsa-lab-dynarray"></a>Dynamic array: growth policy and copies | `DynamicArray.append` | [dsa_lab/experiments.py L267](https://github.com/FUllSCIPTS/ATLAS/blob/main/dsa_lab/experiments.py#L267) | Explorer / lab |
| <a name="dsa-lab-runner"></a>Experiment runner E01-E30 | `run_experiment` | [dsa_lab/experiments.py L2137](https://github.com/FUllSCIPTS/ATLAS/blob/main/dsa_lab/experiments.py#L2137) | Explorer / lab |

<a name="uml-dsa-lists"></a>

### Data Structures → Linked lists (all four kinds)

[Open in the explorer ↗](https://fullscipts.github.io/ATLAS/#dsa-lists)

| Concept | Function / symbol | Location | Status |
| --- | --- | --- | --- |
| <a name="dsa-lab-sll-popback"></a>Singly linked list: pop_back walks to the predecessor | `SinglyLinkedList.pop_back` | [dsa_lab/experiments.py L379](https://github.com/FUllSCIPTS/ATLAS/blob/main/dsa_lab/experiments.py#L379) | Explorer / lab |
| <a name="dsa-lab-dll-unlink"></a>Doubly linked list: unlink a known node | `DoublyLinkedList.unlink` | [dsa_lab/experiments.py L485](https://github.com/FUllSCIPTS/ATLAS/blob/main/dsa_lab/experiments.py#L485) | Explorer / lab |
| <a name="dsa-lab-csll"></a>Circular singly linked list: tail only, head = tail.next | `class CircularSinglyLinkedList:` | [dsa_lab/experiments.py L543](https://github.com/FUllSCIPTS/ATLAS/blob/main/dsa_lab/experiments.py#L543) | Explorer / lab |
| <a name="dsa-lab-csll-rotate"></a>Circular singly list: rotate by moving the tail | `CircularSinglyLinkedList.rotate` | [dsa_lab/experiments.py L589](https://github.com/FUllSCIPTS/ATLAS/blob/main/dsa_lab/experiments.py#L589) | Explorer / lab |
| <a name="dsa-lab-cdll"></a>Circular doubly linked list with a sentinel | `class CircularDoublyLinkedList:` | [dsa_lab/experiments.py L655](https://github.com/FUllSCIPTS/ATLAS/blob/main/dsa_lab/experiments.py#L655) | Explorer / lab |
| <a name="dsa-lab-cdll-insert"></a>Sentinel list: insert_after, the only insertion primitive | `CircularDoublyLinkedList.insert_after` | [dsa_lab/experiments.py L673](https://github.com/FUllSCIPTS/ATLAS/blob/main/dsa_lab/experiments.py#L673) | Explorer / lab |
| <a name="dsa-lab-cdll-rotate"></a>Sentinel list: rotate by moving the sentinel | `CircularDoublyLinkedList.rotate` | [dsa_lab/experiments.py L712](https://github.com/FUllSCIPTS/ATLAS/blob/main/dsa_lab/experiments.py#L712) | Explorer / lab |
| <a name="dsa-lab-josephus"></a>Josephus problem on a circular singly list | `josephus_circular` | [dsa_lab/experiments.py L772](https://github.com/FUllSCIPTS/ATLAS/blob/main/dsa_lab/experiments.py#L772) | Explorer / lab |
| <a name="dsa-lab-floyd"></a>Floyd's tortoise and hare: mu and lambda | `floyd_cycle` | [dsa_lab/experiments.py L874](https://github.com/FUllSCIPTS/ATLAS/blob/main/dsa_lab/experiments.py#L874) | Explorer / lab |
| <a name="dsa-x-lists"></a>Explorer: draw a list by walking its pointers | `dsaListSvg` | [architecture-explorer/dist/dsa.js L285](../../dist/dsa.js#L285) | Explorer / lab |
| <a name="dsa-x-csll"></a>Explorer: circular singly list (port) | `class DsaCircularSingly {` | [architecture-explorer/dist/dsa.js L234](../../dist/dsa.js#L234) | Explorer / lab |
| <a name="dsa-x-cdll"></a>Explorer: circular doubly list with sentinel (port) | `class DsaCircularDoubly {` | [architecture-explorer/dist/dsa.js L253](../../dist/dsa.js#L253) | Explorer / lab |
| <a name="dsa-x-josephus"></a>Explorer: Josephus step | `dsaJosStep` | [architecture-explorer/dist/dsa.js L360](../../dist/dsa.js#L360) | Explorer / lab |
| <a name="dsa-x-floyd"></a>Explorer: tortoise and hare step | `dsaFloydStep` | [architecture-explorer/dist/dsa.js L432](../../dist/dsa.js#L432) | Explorer / lab |

<a name="uml-dsa-queues"></a>

### Data Structures → Stacks, queues & LRU

[Open in the explorer ↗](https://fullscipts.github.io/ATLAS/#dsa-queues)

| Concept | Function / symbol | Location | Status |
| --- | --- | --- | --- |
| <a name="dsa-app-fare"></a>Fare rule evaluated with a stack in the explorer | `fare` | [android-app/atlas_go/domain.py L15](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/domain.py#L15) | Implemented |
| <a name="dsa-app-lifo"></a>LIFO work queue: newest tile request first | `self.requests = queue.LifoQueue()` | [android-app/atlas_go/livemap.py L46](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/livemap.py#L46) | Implemented |
| <a name="dsa-app-lru-hit"></a>LRU cache hit: move_to_end on the OrderedDict | `TileLoader.texture` | [android-app/atlas_go/livemap.py L64](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/livemap.py#L64) | Implemented |
| <a name="dsa-app-lru-evict"></a>LRU eviction: popitem(last=False) past 160 tiles | `self.textures.popitem(last=False)` | [android-app/atlas_go/livemap.py L128](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/livemap.py#L128) | Implemented |
| <a name="dsa-lab-postfix"></a>Stack: evaluate a postfix expression | `evaluate_postfix` | [dsa_lab/experiments.py L969](https://github.com/FUllSCIPTS/ATLAS/blob/main/dsa_lab/experiments.py#L969) | Explorer / lab |
| <a name="dsa-lab-ring"></a>Ring buffer: enqueue at (front + count) % capacity | `RingBuffer.enqueue` | [dsa_lab/experiments.py L922](https://github.com/FUllSCIPTS/ATLAS/blob/main/dsa_lab/experiments.py#L922) | Explorer / lab |
| <a name="dsa-lab-lru"></a>LRU cache: dict + circular doubly list | `LRUCache.get` | [dsa_lab/experiments.py L828](https://github.com/FUllSCIPTS/ATLAS/blob/main/dsa_lab/experiments.py#L828) | Explorer / lab |
| Circular doubly linked list with a sentinel | `class CircularDoublyLinkedList:` | [dsa_lab/experiments.py L655](https://github.com/FUllSCIPTS/ATLAS/blob/main/dsa_lab/experiments.py#L655) | Explorer / lab |
| <a name="dsa-x-ring"></a>Explorer: ring buffer | `dsaRingOp` | [architecture-explorer/dist/dsa.js L480](../../dist/dsa.js#L480) | Explorer / lab |
| <a name="dsa-x-lru"></a>Explorer: LRU cache | `dsaLruGet` | [architecture-explorer/dist/dsa.js L517](../../dist/dsa.js#L517) | Explorer / lab |

<a name="uml-dsa-hashing"></a>

### Data Structures → Hash tables

[Open in the explorer ↗](https://fullscipts.github.io/ATLAS/#dsa-hashing)

| Concept | Function / symbol | Location | Status |
| --- | --- | --- | --- |
| <a name="dsa-app-dishes"></a>Hash table: dish id to Dish | `DISHES` | [android-app/atlas_go/domain.py L43](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/domain.py#L43) | Implemented |
| <a name="dsa-app-cart"></a>Hash table: cart quantities per dish | `Cart.add` | [android-app/atlas_go/domain.py L130](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/domain.py#L130) | Implemented |
| <a name="dsa-app-menu"></a>Linear filter: a kitchen's menu | `Catalog.menu` | [android-app/atlas_go/domain.py L105](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/domain.py#L105) | Implemented |
| <a name="dsa-lab-chain"></a>Hash table with separate chaining and resizing | `ChainHash.put` | [dsa_lab/experiments.py L1021](https://github.com/FUllSCIPTS/ATLAS/blob/main/dsa_lab/experiments.py#L1021) | Explorer / lab |
| <a name="dsa-lab-probe"></a>Open addressing: linear probing | `OpenAddressHash.put` | [dsa_lab/experiments.py L1137](https://github.com/FUllSCIPTS/ATLAS/blob/main/dsa_lab/experiments.py#L1137) | Explorer / lab |
| <a name="dsa-lab-tomb"></a>Open addressing: delete with a tombstone | `OpenAddressHash.delete` | [dsa_lab/experiments.py L1169](https://github.com/FUllSCIPTS/ATLAS/blob/main/dsa_lab/experiments.py#L1169) | Explorer / lab |
| <a name="dsa-x-hash"></a>Explorer: chaining and probing table | `dsaHashPut` | [architecture-explorer/dist/dsa.js L579](../../dist/dsa.js#L579) | Explorer / lab |

<a name="uml-dsa-trees"></a>

### Data Structures → Trees & heaps

[Open in the explorer ↗](https://fullscipts.github.io/ATLAS/#dsa-trees)

| Concept | Function / symbol | Location | Status |
| --- | --- | --- | --- |
| <a name="dsa-app-pools"></a>Drivers and pickup minutes used by the heap and sorting labs | `DRIVER_POOLS` | [android-app/atlas_go/intelligence.py L250](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py#L250) | Implemented |
| <a name="dsa-app-rank"></a>Sorting: rank candidates with sorted() | `rank` | [android-app/atlas_go/intelligence.py L266](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py#L266) | Implemented |
| <a name="dsa-app-choose"></a>Selection: take the best candidate; min for the nearest | `choose` | [android-app/atlas_go/intelligence.py L277](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py#L277) | Implemented |
| <a name="dsa-lab-bstdel"></a>BST delete: the three cases | `bst_delete` | [dsa_lab/experiments.py L1239](https://github.com/FUllSCIPTS/ATLAS/blob/main/dsa_lab/experiments.py#L1239) | Explorer / lab |
| <a name="dsa-lab-avl"></a>AVL insert with the four rotations | `avl_insert` | [dsa_lab/experiments.py L1400](https://github.com/FUllSCIPTS/ATLAS/blob/main/dsa_lab/experiments.py#L1400) | Explorer / lab |
| <a name="dsa-lab-traversal"></a>Level-order traversal with a queue | `levelorder_queue` | [dsa_lab/experiments.py L1327](https://github.com/FUllSCIPTS/ATLAS/blob/main/dsa_lab/experiments.py#L1327) | Explorer / lab |
| <a name="dsa-lab-heap"></a>Binary min-heap: sift up | `MinHeap.push` | [dsa_lab/experiments.py L1474](https://github.com/FUllSCIPTS/ATLAS/blob/main/dsa_lab/experiments.py#L1474) | Explorer / lab |
| <a name="dsa-lab-trie"></a>Trie: prefix query | `Trie.starts_with` | [dsa_lab/experiments.py L1554](https://github.com/FUllSCIPTS/ATLAS/blob/main/dsa_lab/experiments.py#L1554) | Explorer / lab |
| <a name="dsa-x-avl"></a>Explorer: AVL insert | `dsaAvlInsert` | [architecture-explorer/dist/dsa.js L664](../../dist/dsa.js#L664) | Explorer / lab |
| <a name="dsa-x-heap"></a>Explorer: driver min-heap | `dsaHeapPush` | [architecture-explorer/dist/dsa.js L704](../../dist/dsa.js#L704) | Explorer / lab |

<a name="uml-dsa-graphs"></a>

### Data Structures → Graphs

[Open in the explorer ↗](https://fullscipts.github.io/ATLAS/#dsa-graphs)

| Concept | Function / symbol | Location | Status |
| --- | --- | --- | --- |
| <a name="dsa-app-zones"></a>Zone coordinates: the graph lab's vertices | `ZONE_COORDS` | [android-app/atlas_go/geo.py L21](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/geo.py#L21) | Implemented |
| <a name="dsa-app-haversine"></a>Great-circle distance: the graph lab's edge weights | `haversine_km` | [android-app/atlas_go/geo.py L39](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/geo.py#L39) | Implemented |
| <a name="dsa-app-legs"></a>Straight-line trip legs (no road graph) | `ride_legs` | [android-app/atlas_go/geo.py L128](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/geo.py#L128) | Related (similar code, not this exact structure) |
| <a name="dsa-lab-bfs"></a>Breadth-first search | `bfs` | [dsa_lab/experiments.py L1609](https://github.com/FUllSCIPTS/ATLAS/blob/main/dsa_lab/experiments.py#L1609) | Explorer / lab |
| <a name="dsa-lab-dfs"></a>Depth-first search | `dfs` | [dsa_lab/experiments.py L1597](https://github.com/FUllSCIPTS/ATLAS/blob/main/dsa_lab/experiments.py#L1597) | Explorer / lab |
| <a name="dsa-lab-dijkstra"></a>Dijkstra with a binary heap | `dijkstra` | [dsa_lab/experiments.py L1646](https://github.com/FUllSCIPTS/ATLAS/blob/main/dsa_lab/experiments.py#L1646) | Explorer / lab |
| <a name="dsa-lab-kruskal"></a>Kruskal minimum spanning tree with union-find | `kruskal` | [dsa_lab/experiments.py L1773](https://github.com/FUllSCIPTS/ATLAS/blob/main/dsa_lab/experiments.py#L1773) | Explorer / lab |
| <a name="dsa-lab-topo"></a>Topological sort (Kahn) | `topo_sort_kahn` | [dsa_lab/experiments.py L1689](https://github.com/FUllSCIPTS/ATLAS/blob/main/dsa_lab/experiments.py#L1689) | Explorer / lab |
| <a name="dsa-x-graph"></a>Explorer: BFS, DFS, Dijkstra and Prim frames | `dsaGraphFrames` | [architecture-explorer/dist/dsa.js L775](../../dist/dsa.js#L775) | Explorer / lab |

<a name="uml-dsa-sorting"></a>

### Data Structures → Sorting & searching

[Open in the explorer ↗](https://fullscipts.github.io/ATLAS/#dsa-sorting)

| Concept | Function / symbol | Location | Status |
| --- | --- | --- | --- |
| Sorting: rank candidates with sorted() | `rank` | [android-app/atlas_go/intelligence.py L266](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py#L266) | Implemented |
| Drivers and pickup minutes used by the heap and sorting labs | `DRIVER_POOLS` | [android-app/atlas_go/intelligence.py L250](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py#L250) | Implemented |
| <a name="dsa-lab-insertion"></a>Insertion sort with counts | `insertion_sort` | [dsa_lab/experiments.py L112](https://github.com/FUllSCIPTS/ATLAS/blob/main/dsa_lab/experiments.py#L112) | Explorer / lab |
| <a name="dsa-lab-merge"></a>Merge sort with counts | `merge_sort` | [dsa_lab/experiments.py L127](https://github.com/FUllSCIPTS/ATLAS/blob/main/dsa_lab/experiments.py#L127) | Explorer / lab |
| <a name="dsa-lab-quick"></a>Quick sort, random pivot (Lomuto) | `quick_sort_inplace` | [dsa_lab/experiments.py L162](https://github.com/FUllSCIPTS/ATLAS/blob/main/dsa_lab/experiments.py#L162) | Explorer / lab |
| <a name="dsa-lab-heapsort"></a>Heap sort | `heap_sort` | [dsa_lab/experiments.py L186](https://github.com/FUllSCIPTS/ATLAS/blob/main/dsa_lab/experiments.py#L186) | Explorer / lab |
| <a name="dsa-lab-stable"></a>Count stability violations | `stability_violations` | [dsa_lab/experiments.py L226](https://github.com/FUllSCIPTS/ATLAS/blob/main/dsa_lab/experiments.py#L226) | Explorer / lab |
| <a name="dsa-lab-first"></a>First occurrence (bisect_left) | `first_occurrence` | [dsa_lab/experiments.py L66](https://github.com/FUllSCIPTS/ATLAS/blob/main/dsa_lab/experiments.py#L66) | Explorer / lab |
| <a name="dsa-x-sort"></a>Explorer: counting sorts | `dsaSortRun` | [architecture-explorer/dist/dsa.js L870](../../dist/dsa.js#L870) | Explorer / lab |

<a name="uml-dsa-design"></a>

### Data Structures → Algorithm design

[Open in the explorer ↗](https://fullscipts.github.io/ATLAS/#dsa-design)

| Concept | Function / symbol | Location | Status |
| --- | --- | --- | --- |
| <a name="dsa-app-validate"></a>Invariant check on saved state | `LocalStore.validate` | [android-app/atlas_go/store.py L86](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py#L86) | Implemented |
| <a name="dsa-app-selftest"></a>Self-test of the on-device models | `self_test` | [android-app/atlas_go/intelligence.py L459](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py#L459) | Implemented |
| <a name="dsa-app-advance"></a>State machine: advance a ride | `LocalStore.advance_ride` | [android-app/atlas_go/store.py L480](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py#L480) | Related (similar code, not this exact structure) |
| <a name="dsa-lab-fib"></a>Fibonacci with a memo: call count | `fib_memo_calls` | [dsa_lab/experiments.py L1797](https://github.com/FUllSCIPTS/ATLAS/blob/main/dsa_lab/experiments.py#L1797) | Explorer / lab |
| <a name="dsa-lab-knapsack"></a>0/1 knapsack by dynamic programming | `knapsack_01` | [dsa_lab/experiments.py L1819](https://github.com/FUllSCIPTS/ATLAS/blob/main/dsa_lab/experiments.py#L1819) | Explorer / lab |
| <a name="dsa-lab-queens"></a>N queens by backtracking | `n_queens` | [dsa_lab/experiments.py L1837](https://github.com/FUllSCIPTS/ATLAS/blob/main/dsa_lab/experiments.py#L1837) | Explorer / lab |
| <a name="dsa-lab-selftest"></a>Self-test of every structure's invariants | `self_test` | [dsa_lab/experiments.py L2469](https://github.com/FUllSCIPTS/ATLAS/blob/main/dsa_lab/experiments.py#L2469) | Explorer / lab |
| <a name="dsa-x-knapsack"></a>Explorer: knapsack table | `dsaKnapsack` | [architecture-explorer/dist/dsa.js L950](../../dist/dsa.js#L950) | Explorer / lab |

<a name="uml-dsa-gaps"></a>

### Data Structures → Experiments & exercises

[Open in the explorer ↗](https://fullscipts.github.io/ATLAS/#dsa-gaps)

| Concept | Function / symbol | Location | Status |
| --- | --- | --- | --- |
| Linear scan: the user's ride and order history | `LocalStore.my_history` | [android-app/atlas_go/store.py L653](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/store.py#L653) | Implemented |
| Sorting: rank candidates with sorted() | `rank` | [android-app/atlas_go/intelligence.py L266](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/intelligence.py#L266) | Implemented |
| Minimum selection: nearest saved place | `nearest_place` | [android-app/atlas_go/geo.py L60](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/geo.py#L60) | Implemented |
| Straight-line trip legs (no road graph) | `ride_legs` | [android-app/atlas_go/geo.py L128](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/geo.py#L128) | Related (similar code, not this exact structure) |
| LIFO work queue: newest tile request first | `self.requests = queue.LifoQueue()` | [android-app/atlas_go/livemap.py L46](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/livemap.py#L46) | Implemented |
| Experiment runner E01-E30 | `run_experiment` | [dsa_lab/experiments.py L2137](https://github.com/FUllSCIPTS/ATLAS/blob/main/dsa_lab/experiments.py#L2137) | Explorer / lab |

<!-- END DSA CATALOG -->

## Generated symbol catalog

<!-- BEGIN GENERATED CATALOG -->

### `apps/shared/client.js`

[Open source](../apps/shared/client.js)

| Kind | Signature | Decorators | Source |
| --- | --- | --- | --- |
| Function | `async request(path, method = "GET", data, idempotencyKey)` | — | [L8](../apps/shared/client.js#L8) |
| Function | `async refresh()` | — | [L20](../apps/shared/client.js#L20) |
| Function | `refresh.<callback: offers.map>(offer)` | — | [L31](../apps/shared/client.js#L31) |
| Function | `async refresh.<callback: offers.map>.button.onclick()` | — | [L43](../apps/shared/client.js#L43) |
| Function | `async <callback: document.getElementById("booking")?.addEventListener, "submit">(event)` | — | [L59](../apps/shared/client.js#L59) |
| Function | `async <callback: document.getElementById("telemetry")?.addEventListener, "submit">(event)` | — | [L72](../apps/shared/client.js#L72) |

### `ml/discrete.py`

[Open source](../ml/discrete.py)

| Kind | Signature | Decorators | Source |
| --- | --- | --- | --- |
| Function | `train(directory)` | — | [L8](../ml/discrete.py#L8) |

### `ml/forecast.py`

[Open source](../ml/forecast.py)

**Class `DemandLSTM`** · bases `nn.Module` · [L9](../ml/forecast.py#L9)

- Instance attribute `self.recurrent = nn.LSTM(1, 12, batch_first=True)`
- Instance attribute `self.output = nn.Linear(12, 1)`

| Kind | Signature | Decorators | Source |
| --- | --- | --- | --- |
| Function | `train(directory)` | — | [L20](../ml/forecast.py#L20) |
| Function | `load(directory)` | — | [L44](../ml/forecast.py#L44) |
| Function | `predict(model, counts)` | — | [L51](../ml/forecast.py#L51) |
| Method | `DemandLSTM.__init__(self)` | — | [L10](../ml/forecast.py#L10) |
| Method | `DemandLSTM.forward(self, values)` | — | [L15](../ml/forecast.py#L15) |

### `ml/registry.py`

[Open source](../ml/registry.py)

| Kind | Signature | Decorators | Source |
| --- | --- | --- | --- |
| Function | `read_json(path, default=None)` | — | [L10](../ml/registry.py#L10) |
| Function | `write_json(path, value)` | — | [L17](../ml/registry.py#L17) |

### `ml/rl.py`

[Open source](../ml/rl.py)

| Kind | Signature | Decorators | Source |
| --- | --- | --- | --- |
| Function | `current_policy()` | — | [L15](../ml/rl.py#L15) |
| Function | `fixture()` | — | [L19](../ml/rl.py#L19) |
| Function | `experiences()` | — | [L25](../ml/rl.py#L25) |
| Function | `fit(samples, source)` | — | [L32](../ml/rl.py#L32) |
| Function | `fit.<lambda@39:40>(action)` | — | [L39](../ml/rl.py#L39) |
| Function | `approve(version, allow_demo=False)` | — | [L51](../ml/rl.py#L51) |
| Function | `watch(seconds)` | — | [L70](../ml/rl.py#L70) |
| Function | `main()` | — | [L81](../ml/rl.py#L81) |

### `ml/serve.py`

[Open source](../ml/serve.py)

**Class `Candidate`** · bases `BaseModel` · [L16](../ml/serve.py#L16)

- Declared field `driver_id: str`
- Declared field `distance_km: float = Field(ge=0, le=50)`
- Declared field `speed_kph: float = Field(ge=0, le=250)`

This class uses inherited methods.

**Class `ScoringRequest`** · bases `BaseModel` · [L22](../ml/serve.py#L22)

- Declared field `zone: Literal['cork-centre', 'cork-north']`
- Declared field `drivers: list[Candidate] = Field(min_length=1, max_length=20)`

This class uses inherited methods.

| Kind | Signature | Decorators | Source |
| --- | --- | --- | --- |
| Function | `models(version)` | `lru_cache(maxsize=2)` | [L28](../ml/serve.py#L28) |
| Function | `active()` | — | [L33](../ml/serve.py#L33) |
| Function | `health()` | `app.get('/healthz')` | [L41](../ml/serve.py#L41) |
| Function | `score(payload: ScoringRequest)` | `app.post('/internal/v1/score')` | [L48](../ml/serve.py#L48) |

### `ml/train.py`

[Open source](../ml/train.py)

| Kind | Signature | Decorators | Source |
| --- | --- | --- | --- |
| Function | `train()` | — | [L8](../ml/train.py#L8) |

### `packages/config.py`

[Open source](../packages/config.py)

| Kind | Signature | Decorators | Source |
| --- | --- | --- | --- |
| Function | `equal(left, right)` | — | [L20](../packages/config.py#L20) |
| Function | `internal_actor(request: Request, role: str) -> str` | — | [L24](../packages/config.py#L24) |

### `packages/db.py`

[Open source](../packages/db.py)

**Class `DB`** · bases none · [L14](../packages/db.py#L14)

- Instance attribute `self.connection = connection`

| Kind | Signature | Decorators | Source |
| --- | --- | --- | --- |
| Function | `database()` | `contextmanager` | [L23](../packages/db.py#L23) |
| Function | `migrate()` | — | [L45](../packages/db.py#L45) |
| Function | `emit(db, trip_id, event_type, **body)` | — | [L57](../packages/db.py#L57) |
| Function | `envelope(row)` | — | [L62](../packages/db.py#L62) |
| Method | `DB.__init__(self, connection)` | — | [L15](../packages/db.py#L15) |
| Method | `DB.run(self, query, *args)` | — | [L18](../packages/db.py#L18) |

### `scripts/initialize.sh`

[Open source](../scripts/initialize.sh)

This file declares no functions.

### `scripts/local.sh`

[Open source](../scripts/local.sh)

| Kind | Signature | Decorators | Source |
| --- | --- | --- | --- |
| Function | `start()` | — | [L13](../scripts/local.sh#L13) |
| Function | `cleanup()` | — | [L17](../scripts/local.sh#L17) |

### `scripts/security_catalog.py`

[Open source](../scripts/security_catalog.py)

| Kind | Signature | Decorators | Source |
| --- | --- | --- | --- |
| Function | `read(location, main)` | — | [L407](../scripts/security_catalog.py#L407) |
| Function | `python_symbols(text)` | — | [L417](../scripts/security_catalog.py#L417) |
| Function | `locate(text, path, symbol)` | — | [L429](../scripts/security_catalog.py#L429) |
| Function | `resolve(main)` | — | [L450](../scripts/security_catalog.py#L450) |
| Function | `markdown(rows, views, intro)` | — | [L483](../scripts/security_catalog.py#L483) |
| Function | `script(rows)` | — | [L504](../scripts/security_catalog.py#L504) |
| Function | `replace_block(document, content, name)` | — | [L512](../scripts/security_catalog.py#L512) |
| Function | `main()` | — | [L521](../scripts/security_catalog.py#L521) |

### `services/dispatch.py`

[Open source](../services/dispatch.py)

**Class `Telemetry`** · bases `BaseModel` · [L12](../services/dispatch.py#L12)

- Declared field `online: bool`
- Declared field `distance_km: float = Field(ge=0, le=50)`
- Declared field `speed_kph: float = Field(ge=0, le=250)`

This class uses inherited methods.

| Kind | Signature | Decorators | Source |
| --- | --- | --- | --- |
| Function | `health()` | `app.get('/healthz')` | [L19](../services/dispatch.py#L19) |
| Function | `availability(request: Request, payload: Telemetry)` | `app.put('/v1/driver/availability')` | [L26](../services/dispatch.py#L26) |
| Function | `offers(request: Request)` | `app.get('/v1/driver/offers')` | [L35](../services/dispatch.py#L35) |
| Function | `accept(request: Request, trip_id: UUID)` | `app.post('/v1/driver/offers/{trip_id}/accept', status_code=202)` | [L47](../services/dispatch.py#L47) |

### `services/gateway.py`

[Open source](../services/gateway.py)

| Kind | Signature | Decorators | Source |
| --- | --- | --- | --- |
| Function | `health()` | `app.get('/healthz')` | [L26](../services/gateway.py#L26) |
| Function | `passenger()` | `app.get('/')`, `app.get('/passenger')` | [L37](../services/gateway.py#L37) |
| Function | `driver()` | `app.get('/driver')` | [L42](../services/gateway.py#L42) |
| Function | `async proxy(request: Request, role: str, path: str)` | `app.api_route('/v1/{role}/{path:path}', methods=['GET', 'POST', 'PUT'])` | [L47](../services/gateway.py#L47) |

### `services/trips.py`

[Open source](../services/trips.py)

**Class `Booking`** · bases `BaseModel` · [L14](../services/trips.py#L14)

- Declared field `pickup: str = Field(min_length=1, max_length=120, pattern='\\S')`
- Declared field `destination: str = Field(min_length=1, max_length=120, pattern='\\S')`
- Declared field `zone: Literal['cork-centre', 'cork-north']`

This class uses inherited methods.

**Class `Milestone`** · bases `BaseModel` · [L20](../services/trips.py#L20)

- Declared field `status: Literal['picked_up', 'completed']`

This class uses inherited methods.

| Kind | Signature | Decorators | Source |
| --- | --- | --- | --- |
| Function | `health()` | `app.get('/healthz')` | [L25](../services/trips.py#L25) |
| Function | `book(request: Request, payload: Booking, idempotency_key: Annotated[str, Header(min_length=1, max_length=128)])` | `app.post('/v1/rider/trips', status_code=202)` | [L32](../services/trips.py#L32) |
| Function | `public_trip(row)` | — | [L48](../services/trips.py#L48) |
| Function | `status(request: Request, trip_id: UUID)` | `app.get('/v1/rider/trips/{trip_id}')` | [L53](../services/trips.py#L53) |
| Function | `milestone(request: Request, trip_id: UUID, payload: Milestone)` | `app.post('/v1/driver/trips/{trip_id}/milestones')` | [L63](../services/trips.py#L63) |

### `tests/policy.py`

[Open source](../tests/policy.py)

| Kind | Signature | Decorators | Source |
| --- | --- | --- | --- |
| Function | `reject(action, expected)` | — | [L9](../tests/policy.py#L9) |
| Function | `<lambda@21:12>()` | — | [L21](../tests/policy.py#L21) |
| Function | `<lambda@28:12>()` | — | [L28](../tests/policy.py#L28) |

### `tests/replay.py`

[Open source](../tests/replay.py)

| Kind | Signature | Decorators | Source |
| --- | --- | --- | --- |
| Function | `completed_event(trip_id)` | — | [L13](../tests/replay.py#L13) |
| Function | `snapshot(trip_id, event_id)` | — | [L20](../tests/replay.py#L20) |
| Function | `replay_over_kafka(event, bootstrap)` | — | [L31](../tests/replay.py#L31) |
| Function | `replay_over_kafka.<lambda@38:34>(error, message)` | — | [L38](../tests/replay.py#L38) |
| Function | `main()` | — | [L58](../tests/replay.py#L58) |

### `tests/smoke.py`

[Open source](../tests/smoke.py)

| Kind | Signature | Decorators | Source |
| --- | --- | --- | --- |
| Function | `until(check, label, timeout=45)` | — | [L16](../tests/smoke.py#L16) |
| Function | `api(method, path, actor='rider-a', *, expected=200, key=None, body=None)` | — | [L28](../tests/smoke.py#L28) |
| Function | `check()` | — | [L37](../tests/smoke.py#L37) |
| Function | `check.<lambda@38:11>()` | — | [L38](../tests/smoke.py#L38) |
| Function | `check.<lambda@39:11>()` | — | [L39](../tests/smoke.py#L39) |
| Function | `check.offer_for_trip()` | — | [L49](../tests/smoke.py#L49) |
| Function | `check.<lambda@64:11>()` | — | [L64](../tests/smoke.py#L64) |
| Function | `check.learned()` | — | [L71](../tests/smoke.py#L71) |

### `workers/events.py`

[Open source](../workers/events.py)

| Kind | Signature | Decorators | Source |
| --- | --- | --- | --- |
| Function | `choose(candidates, zone)` | — | [L17](../workers/events.py#L17) |
| Function | `choose.<lambda@33:38>(d)` | — | [L33](../workers/events.py#L33) |
| Function | `choose.<lambda@36:38>(d)` | — | [L36](../workers/events.py#L36) |
| Function | `apply(event)` | — | [L41](../workers/events.py#L41) |
| Function | `update_features()` | — | [L76](../workers/events.py#L76) |
| Function | `next_event()` | — | [L90](../workers/events.py#L90) |
| Function | `mark_sent(event)` | — | [L96](../workers/events.py#L96) |
| Function | `local_tick()` | — | [L101](../workers/events.py#L101) |
| Function | `kafka_loop()` | — | [L111](../workers/events.py#L111) |
| Function | `kafka_loop.<lambda@122:46>(error, _)` | — | [L122](../workers/events.py#L122) |

<!-- END GENERATED CATALOG -->


## Generated supporting source catalog

These are the explorer, Node static server and blueprint generator symbols. GitHub Pages publishes the same static explorer assets without the Node process. The ride-hailing starter runs separately.

<!-- BEGIN GENERATED SUPPORT -->

### `dist/atlas-go.js`

[Open source](../../dist/atlas-go.js)

This file declares no functions.

### `dist/atlas.js`

[Open source](../../dist/atlas.js)

This file declares no functions.

### `dist/build.js`

[Open source](../../dist/build.js)

| Kind | Signature | Decorators | Source |
| --- | --- | --- | --- |
| Function | `async <callback: copy.addEventListener, "click">()` | — | [L5](../../dist/build.js#L5) |

### `dist/crypto.js`

[Open source](../../dist/crypto.js)

| Kind | Signature | Decorators | Source |
| --- | --- | --- | --- |
| Function | `<callback: crTopics.map>(t)` | — | [L34](../../dist/crypto.js#L34) |
| Function | `crB64ToBytes(b64)` | — | [L53](../../dist/crypto.js#L53) |
| Function | `crB64ToBytes.<callback: Uint8Array.from>(c)` | — | [L53](../../dist/crypto.js#L53) |
| Function | `async crDigest(alg, data)` | — | [L54](../../dist/crypto.js#L54) |
| Function | `crBits(hex)` | — | [L55](../../dist/crypto.js#L55) |
| Function | `crBits.<callback: [...hex].flatMap>(h)` | — | [L55](../../dist/crypto.js#L55) |
| Function | `crButton(action, label, { primary = false, iconName = "", disabled = false } = {})` | — | [L57](../../dist/crypto.js#L57) |
| Function | `crField(name, label, hint = "")` | — | [L61](../../dist/crypto.js#L61) |
| Function | `crSelect(name, label, options, value)` | — | [L65](../../dist/crypto.js#L65) |
| Function | `crSelect.<callback: options.map>([v, l])` | — | [L66](../../dist/crypto.js#L66) |
| Function | `crOverview()` | — | [L82](../../dist/crypto.js#L82) |
| Function | `crOverview.<callback: Object.keys(secStatus).map>(k)` | — | [L84](../../dist/crypto.js#L84) |
| Function | `crOverview.<callback: crMap.map>([topic, ic, title, status, text, where])` | — | [L85](../../dist/crypto.js#L85) |
| Function | `async crHashFile(file)` | — | [L98](../../dist/crypto.js#L98) |
| Function | `crHashFile.<callback: CR_PUBLISHED.find>([h])` | — | [L101](../../dist/crypto.js#L101) |
| Function | `async crUpdateAvalanche()` | — | [L105](../../dist/crypto.js#L105) |
| Function | `crUpdateAvalanche.<callback: ba.filter>(bit, i)` | — | [L110](../../dist/crypto.js#L110) |
| Function | `crUpdateAvalanche.<callback: ba.map>(bit, i)` | — | [L113](../../dist/crypto.js#L113) |
| Function | `async crChecksum()` | — | [L118](../../dist/crypto.js#L118) |
| Function | `crChecksum.c(s)` | — | [L121](../../dist/crypto.js#L121) |
| Function | `async crChecksum.h(s)` | — | [L122](../../dist/crypto.js#L122) |
| Function | `crHashes()` | — | [L126](../../dist/crypto.js#L126) |
| Function | `crHashes.<callback: CR_PUBLISHED.map>([h, n, v])` | — | [L134](../../dist/crypto.js#L134) |
| Function | `async crHashesAfterRender()` | — | [L146](../../dist/crypto.js#L146) |
| Function | `async crPin()` | — | [L158](../../dist/crypto.js#L158) |
| Function | `async crIssue(issuer, tbs)` | — | [L176](../../dist/crypto.js#L176) |
| Function | `async crPkiSetup()` | — | [L185](../../dist/crypto.js#L185) |
| Function | `async crVerifyCert(cert, issuerCert, trusted, wantEku)` | — | [L196](../../dist/crypto.js#L196) |
| Function | `crB64Hex(hex)` | — | [L209](../../dist/crypto.js#L209) |
| Function | `crB64Hex.<callback: Uint8Array.from>(h)` | — | [L209](../../dist/crypto.js#L209) |
| Function | `async crPkiRun()` | — | [L211](../../dist/crypto.js#L211) |
| Function | `crPki()` | — | [L231](../../dist/crypto.js#L231) |
| Function | `async crSigKeys()` | — | [L270](../../dist/crypto.js#L270) |
| Function | `async crSigSign()` | — | [L282](../../dist/crypto.js#L282) |
| Function | `async crSigVerify(kind)` | — | [L293](../../dist/crypto.js#L293) |
| Function | `crSignatures()` | — | [L305](../../dist/crypto.js#L305) |
| Function | `crSignatures.<callback: Object.entries(CR_SIG_ALGS).map>([k, v])` | — | [L308](../../dist/crypto.js#L308) |
| Function | `crSignatures.<callback: S.results.map>([ok, t, d])` | — | [L313](../../dist/crypto.js#L313) |
| Function | `crSignatures.<callback: [
    ["Build and test", "atlas-android.yml", "Unsigned AAB; SHA-256 recorded"],
    ["Sign", "jarsigner -sigalg SHA256withRSA -digestalg SHA-256", "RSA-4096 upload key from a PKCS#12 keystore; passwords passed by env name"],
    ["Verify", "jarsigner -verify", "Run immediately after signing"],
    ["Pin check", "SHA-256(certificate) == pinned", "Any other key fails the job"],
    ["Distribute", "APK v2 + v3, SHA256SUMS", "User runs apksigner verify --print-certs"],
  ].map>([t, c, d], i)` | — | [L320](../../dist/crypto.js#L320) |
| Function | `async crLamportKeys()` | — | [L328](../../dist/crypto.js#L328) |
| Function | `crLamportKeys.<callback: pk.flatMap>([a, b])` | — | [L335](../../dist/crypto.js#L335) |
| Function | `async crMsgBits(text)` | — | [L337](../../dist/crypto.js#L337) |
| Function | `async crLamportSign(text)` | — | [L338](../../dist/crypto.js#L338) |
| Function | `crLamportSign.<callback: bits.map>(b, i)` | — | [L340](../../dist/crypto.js#L340) |
| Function | `async crLamportVerify(text, sig)` | — | [L342](../../dist/crypto.js#L342) |
| Function | `crLamportKnown()` | — | [L350](../../dist/crypto.js#L350) |
| Function | `crLamportKnown.<callback: Array.from>()` | — | [L351](../../dist/crypto.js#L351) |
| Function | `crLamportKnown.<callback: s.bits.forEach>(b, i)` | — | [L352](../../dist/crypto.js#L352) |
| Function | `async crLamportForge()` | — | [L355](../../dist/crypto.js#L355) |
| Function | `crLamportForge.<callback: bits.every>(b, i)` | — | [L361](../../dist/crypto.js#L361) |
| Function | `crLamportForge.<callback: bits.map>(b, i)` | — | [L362](../../dist/crypto.js#L362) |
| Function | `crLamportForge.<callback: bits.map>.<callback: cr.lamport.signs.find>(s)` | — | [L362](../../dist/crypto.js#L362) |
| Function | `crPqc()` | — | [L370](../../dist/crypto.js#L370) |
| Function | `crPqc.<callback: known.filter>([a, b])` | — | [L373](../../dist/crypto.js#L373) |
| Function | `crPqc.<callback: known.filter>([a, b])` | — | [L374](../../dist/crypto.js#L374) |
| Function | `crPqc.<callback: sizes.map>([n, pk, sg, tone])` | — | [L385](../../dist/crypto.js#L385) |
| Function | `crPqc.<callback: known.map>([a, b])` | — | [L391](../../dist/crypto.js#L391) |
| Function | `crGaps()` | — | [L401](../../dist/crypto.js#L401) |
| Function | `cryptoInspector()` | — | [L433](../../dist/crypto.js#L433) |
| Function | `cryptoInspector.<callback: info.facts.map>([k, v])` | — | [L439](../../dist/crypto.js#L439) |
| Function | `cryptoInspector.<callback: info.files.map>([l, u])` | — | [L440](../../dist/crypto.js#L440) |
| Function | `cryptoInspector.<callback: info.questions.map>(q)` | — | [L442](../../dist/crypto.js#L442) |
| Function | `cryptoView()` | — | [L449](../../dist/crypto.js#L449) |
| Function | `cryptoView.<callback: crTopics.map>(x)` | — | [L454](../../dist/crypto.js#L454) |
| Function | `cryptoOpen(topic)` | — | [L458](../../dist/crypto.js#L458) |
| Function | `crSetHash()` | — | [L463](../../dist/crypto.js#L463) |
| Function | `async crRun(busy, task)` | — | [L467](../../dist/crypto.js#L467) |
| Function | `cryptoClick(button)` | — | [L475](../../dist/crypto.js#L475) |
| Function | `cryptoClick.swap()` | — | [L487](../../dist/crypto.js#L487) |
| Function | `cryptoClick.pin()` | — | [L488](../../dist/crypto.js#L488) |
| Function | `cryptoClick."pki-run"()` | — | [L489](../../dist/crypto.js#L489) |
| Function | `cryptoClick."pki-reset"()` | — | [L490](../../dist/crypto.js#L490) |
| Function | `async cryptoClick."pki-reset".<callback: crRun, "pki">()` | — | [L490](../../dist/crypto.js#L490) |
| Function | `cryptoClick."sig-keys"()` | — | [L491](../../dist/crypto.js#L491) |
| Function | `cryptoClick."sig-sign"()` | — | [L492](../../dist/crypto.js#L492) |
| Function | `cryptoClick."sig-v-ok"()` | — | [L493](../../dist/crypto.js#L493) |
| Function | `cryptoClick."sig-v-ok".<callback: crRun, "sig">()` | — | [L493](../../dist/crypto.js#L493) |
| Function | `cryptoClick."sig-v-edited"()` | — | [L494](../../dist/crypto.js#L494) |
| Function | `cryptoClick."sig-v-edited".<callback: crRun, "sig">()` | — | [L494](../../dist/crypto.js#L494) |
| Function | `cryptoClick."sig-v-wrongkey"()` | — | [L495](../../dist/crypto.js#L495) |
| Function | `cryptoClick."sig-v-wrongkey".<callback: crRun, "sig">()` | — | [L495](../../dist/crypto.js#L495) |
| Function | `cryptoClick."sig-v-flip"()` | — | [L496](../../dist/crypto.js#L496) |
| Function | `cryptoClick."sig-v-flip".<callback: crRun, "sig">()` | — | [L496](../../dist/crypto.js#L496) |
| Function | `cryptoClick."lam-keys"()` | — | [L497](../../dist/crypto.js#L497) |
| Function | `cryptoClick."lam-sign"()` | — | [L498](../../dist/crypto.js#L498) |
| Function | `async cryptoClick."lam-sign".<callback: crRun, "lam">()` | — | [L498](../../dist/crypto.js#L498) |
| Function | `cryptoClick."lam-verify"()` | — | [L499](../../dist/crypto.js#L499) |
| Function | `async cryptoClick."lam-verify".<callback: crRun, "lam">()` | — | [L499](../../dist/crypto.js#L499) |
| Function | `cryptoClick."lam-forge"()` | — | [L500](../../dist/crypto.js#L500) |
| Function | `<callback: document.addEventListener, "input">(event)` | — | [L506](../../dist/crypto.js#L506) |
| Function | `<callback: document.addEventListener, "change">(event)` | — | [L513](../../dist/crypto.js#L513) |
| Function | `<callback: document.addEventListener, "change">.<callback: crRun, "file">()` | — | [L515](../../dist/crypto.js#L515) |

### `dist/dsa.js`

[Open source](../../dist/dsa.js)

**Class `DsaNode`** · bases none · [L204](../../dist/dsa.js#L204)

**Class `DsaSingly`** · bases none · [L207](../../dist/dsa.js#L207)

**Class `DsaDoubly`** · bases none · [L223](../../dist/dsa.js#L223)

**Class `DsaCircularSingly`** · bases none · [L234](../../dist/dsa.js#L234)

**Class `DsaCircularDoubly`** · bases none · [L253](../../dist/dsa.js#L253)

**Class `DsaTNode`** · bases none · [L652](../../dist/dsa.js#L652)

| Kind | Signature | Decorators | Source |
| --- | --- | --- | --- |
| Function | `dsaSlug(n)` | — | [L40](../../dist/dsa.js#L40) |
| Function | `dsaLesson(n, label = `Lesson ${n}`)` | — | [L41](../../dist/dsa.js#L41) |
| Function | `dsaLessons(...ns)` | — | [L42](../../dist/dsa.js#L42) |
| Function | `dsaLessons.<callback: ns.map>(n)` | — | [L42](../../dist/dsa.js#L42) |
| Function | `<callback: dsaTopics.map>(t)` | — | [L62](../../dist/dsa.js#L62) |
| Function | `dsaChip(status)` | — | [L64](../../dist/dsa.js#L64) |
| Function | `dsaButton(action, label, { primary = false, iconName = "", disabled = false } = {})` | — | [L70](../../dist/dsa.js#L70) |
| Function | `dsaSelect(name, label, options, value)` | — | [L74](../../dist/dsa.js#L74) |
| Function | `dsaSelect.<callback: options.map>([v, l])` | — | [L75](../../dist/dsa.js#L75) |
| Function | `dsaRange(name, label, min, max, step, value)` | — | [L78](../../dist/dsa.js#L78) |
| Function | `dsaPills(items)` | — | [L82](../../dist/dsa.js#L82) |
| Function | `dsaPills.<callback: items.map>([text, tone = ""])` | — | [L83](../../dist/dsa.js#L83) |
| Function | `dsaOps(lines)` | — | [L86](../../dist/dsa.js#L86) |
| Function | `dsaOps.<callback: lines.map>(l)` | — | [L87](../../dist/dsa.js#L87) |
| Function | `dsaLog(entries)` | — | [L90](../../dist/dsa.js#L90) |
| Function | `dsaLog.<callback: entries.slice(-6).reverse().map>(e)` | — | [L92](../../dist/dsa.js#L92) |
| Function | `dsaSvg(w, h, label, body, cls = "")` | — | [L97](../../dist/dsa.js#L97) |
| Function | `dsaText(x, y, t, cls = "", anchor = "middle")` | — | [L98](../../dist/dsa.js#L98) |
| Function | `dsaOverview()` | — | [L140](../../dist/dsa.js#L140) |
| Function | `dsaOverview.<callback: Object.keys(dsaStatus).map>(k)` | — | [L142](../../dist/dsa.js#L142) |
| Function | `dsaOverview.<callback: dsaMap.map>([topic, ic, title, status, text, where])` | — | [L143](../../dist/dsa.js#L143) |
| Function | `dsaOverview.<callback: DSA_ATLAS.map>([idea, st, code, file])` | — | [L144](../../dist/dsa.js#L144) |
| Function | `dsaOverview.<callback: DSA_LESSONS.map>(title, i)` | — | [L145](../../dist/dsa.js#L145) |
| Function | `dsaOverview.<callback: DSA_LESSONS.map>.<callback: dsaTopics.find>(t)` | — | [L146](../../dist/dsa.js#L146) |
| Function | `dsaCountSearch(n)` | — | [L153](../../dist/dsa.js#L153) |
| Function | `dsaCountSearch.<callback: Array.from>(_, i)` | — | [L154](../../dist/dsa.js#L154) |
| Function | `dsaDuration(sec)` | — | [L163](../../dist/dsa.js#L163) |
| Function | `dsaDuration.<callback: units.find>([d])` | — | [L166](../../dist/dsa.js#L166) |
| Function | `dsaComplexity()` | — | [L170](../../dist/dsa.js#L170) |
| Function | `dsaComplexity.<callback: sizes.map>(n)` | — | [L172](../../dist/dsa.js#L172) |
| Function | `dsaComplexity.<callback: sizes.map>.<callback: Array.from>()` | — | [L174](../../dist/dsa.js#L174) |
| Function | `dsaComplexity.fmt(v)` | — | [L181](../../dist/dsa.js#L181) |
| Function | `dsaComplexity.<callback: rows.map>(r)` | — | [L184](../../dist/dsa.js#L184) |
| Function | `dsaComplexity.<callback: rows.map>(r)` | — | [L185](../../dist/dsa.js#L185) |
| Function | `dsaComplexity.<callback: rows.map>(r)` | — | [L186](../../dist/dsa.js#L186) |
| Function | `dsaComplexity.<callback: rows.map>(r)` | — | [L187](../../dist/dsa.js#L187) |
| Function | `dsaComplexity.<callback: rows.filter>(r, i)` | — | [L190](../../dist/dsa.js#L190) |
| Function | `dsaComplexity.<callback: rows.filter((r, i) => i % 3 === 0 \|\| r.n === 4096).map>(r)` | — | [L190](../../dist/dsa.js#L190) |
| Function | `dsaComplexity.<callback: growth.map>([name, v])` | — | [L193](../../dist/dsa.js#L193) |
| Function | `make()` | — | [L273](../../dist/dsa.js#L273) |
| Function | `make()` | — | [L274](../../dist/dsa.js#L274) |
| Function | `make()` | — | [L275](../../dist/dsa.js#L275) |
| Function | `make()` | — | [L276](../../dist/dsa.js#L276) |
| Function | `dsaListNew(kind = dsa.listKind)` | — | [L279](../../dist/dsa.js#L279) |
| Function | `dsaListSvg(L, kind, mark)` | — | [L285](../../dist/dsa.js#L285) |
| Function | `dsaListSvg.<callback: cells.map>(_, i)` | — | [L289](../../dist/dsa.js#L289) |
| Function | `dsaListSvg.<callback: cells.map>(c, i)` | — | [L292](../../dist/dsa.js#L292) |
| Function | `dsaListSvg.arrow(x1, y1, x2, y2, cls = "", m = "dsa-ah")` | — | [L294](../../dist/dsa.js#L294) |
| Function | `dsaListSvg.<callback: cells.forEach>(c, i)` | — | [L295](../../dist/dsa.js#L295) |
| Function | `dsaListSvg.<callback: cells.forEach>(c, i)` | — | [L303](../../dist/dsa.js#L303) |
| Function | `dsaListSvg.label(node, text, dy = 0)` | — | [L322](../../dist/dsa.js#L322) |
| Function | `dsaListOp(op)` | — | [L331](../../dist/dsa.js#L331) |
| Function | `dsaJosNew()` | — | [L355](../../dist/dsa.js#L355) |
| Function | `dsaJosStep()` | — | [L360](../../dist/dsa.js#L360) |
| Function | `dsaJosFormula(n, k)` | — | [L370](../../dist/dsa.js#L370) |
| Function | `dsaJosListShifts(n, k)` | — | [L371](../../dist/dsa.js#L371) |
| Function | `dsaJosListShifts.<callback: Array.from>(_, i)` | — | [L371](../../dist/dsa.js#L371) |
| Function | `dsaJosSvg()` | — | [L373](../../dist/dsa.js#L373) |
| Function | `dsaJosSvg.<callback: J.ring.nodes().map>(x)` | — | [L374](../../dist/dsa.js#L374) |
| Function | `dsaJosSvg.pos(v)` | — | [L375](../../dist/dsa.js#L375) |
| Function | `dsaJosSvg.<callback: live.forEach>(node)` | — | [L378](../../dist/dsa.js#L378) |
| Function | `dsaLists()` | — | [L397](../../dist/dsa.js#L397) |
| Function | `dsaLists.<callback: L.nodes().map>(x)` | — | [L401](../../dist/dsa.js#L401) |
| Function | `dsaLists.<callback: Object.entries(DSA_KINDS).map>([id, x])` | — | [L404](../../dist/dsa.js#L404) |
| Function | `dsaLists.<callback: [5, 6, 7, 8, 9, 10, 12, 16].map>(v)` | — | [L413](../../dist/dsa.js#L413) |
| Function | `dsaLists.<callback: [2, 3, 4, 5].map>(v)` | — | [L413](../../dist/dsa.js#L413) |
| Function | `dsaFloydNew(mu = dsa.floyd?.mu ?? 3, lam = dsa.floyd?.lam ?? 5)` | — | [L427](../../dist/dsa.js#L427) |
| Function | `dsaFloydNew.<callback: Array.from>(_, i)` | — | [L428](../../dist/dsa.js#L428) |
| Function | `dsaFloydNew.<callback: nodes.forEach>(n, i)` | — | [L429](../../dist/dsa.js#L429) |
| Function | `dsaFloydStep()` | — | [L432](../../dist/dsa.js#L432) |
| Function | `dsaFloydSvg()` | — | [L446](../../dist/dsa.js#L446) |
| Function | `dsaFloydSvg.pos(i)` | — | [L448](../../dist/dsa.js#L448) |
| Function | `dsaFloydSvg.pos.<callback: () => { const a = Math.PI + ((i - F.mu) / F.lam) * 2 * Math.PI; return [cx + R * Math.cos(a), Y + R * Math.sin(a)]; }>()` | — | [L448](../../dist/dsa.js#L448) |
| Function | `dsaFloydSvg.<callback: F.nodes.forEach>(n)` | — | [L450](../../dist/dsa.js#L450) |
| Function | `dsaFloydSvg.<callback: F.nodes.forEach>(n)` | — | [L451](../../dist/dsa.js#L451) |
| Function | `dsaFloydSvg.tag(node, t, dy, cls)` | — | [L452](../../dist/dsa.js#L452) |
| Function | `dsaFloyd()` | — | [L456](../../dist/dsa.js#L456) |
| Function | `dsaFloyd.<callback: [0, 1, 2, 3, 4, 5].map>(v)` | — | [L460](../../dist/dsa.js#L460) |
| Function | `dsaFloyd.<callback: [1, 2, 3, 4, 5, 6, 7].map>(v)` | — | [L460](../../dist/dsa.js#L460) |
| Function | `dsaFloyd.<callback: F.log.slice(-4).reverse().map>(l)` | — | [L464](../../dist/dsa.js#L464) |
| Function | `dsaPostfixTrace()` | — | [L470](../../dist/dsa.js#L470) |
| Function | `dsaRingNew(cap = 8)` | — | [L479](../../dist/dsa.js#L479) |
| Function | `dsaRingOp(op)` | — | [L480](../../dist/dsa.js#L480) |
| Function | `dsaRingSvg()` | — | [L498](../../dist/dsa.js#L498) |
| Function | `dsaRingSvg.p(r, a)` | — | [L503](../../dist/dsa.js#L503) |
| Function | `dsaRingSvg.mark(i, t, cls, rr)` | — | [L509](../../dist/dsa.js#L509) |
| Function | `dsaLruNew()` | — | [L516](../../dist/dsa.js#L516) |
| Function | `dsaLruGet(key)` | — | [L517](../../dist/dsa.js#L517) |
| Function | `dsaQueues()` | — | [L530](../../dist/dsa.js#L530) |
| Function | `dsaQueues.<callback: Array.from>(_, i)` | — | [L534](../../dist/dsa.js#L534) |
| Function | `dsaQueues.<callback: C.list.nodes().map>(x)` | — | [L535](../../dist/dsa.js#L535) |
| Function | `dsaQueues.<callback: frames.map>([t, a, s])` | — | [L538](../../dist/dsa.js#L538) |
| Function | `dsaQueues.<callback: DSA_TILES.map>(k)` | — | [L549](../../dist/dsa.js#L549) |
| Function | `dsaHashOf(key)` | — | [L571](../../dist/dsa.js#L571) |
| Function | `dsaHashNew()` | — | [L573](../../dist/dsa.js#L573) |
| Function | `dsaHashNew.<callback: Array.from>()` | — | [L573](../../dist/dsa.js#L573) |
| Function | `dsaHashResize(H, m)` | — | [L574](../../dist/dsa.js#L574) |
| Function | `dsaHashResize.<callback: H.slots.filter>(s)` | — | [L575](../../dist/dsa.js#L575) |
| Function | `dsaHashResize.<callback: Array.from>()` | — | [L576](../../dist/dsa.js#L576) |
| Function | `dsaHashPut(H, key, quiet = false)` | — | [L579](../../dist/dsa.js#L579) |
| Function | `dsaHashDelete(H)` | — | [L593](../../dist/dsa.js#L593) |
| Function | `dsaHashDelete.<callback: H.slots.filter>(s)` | — | [L594](../../dist/dsa.js#L594) |
| Function | `dsaHashStats(H)` | — | [L601](../../dist/dsa.js#L601) |
| Function | `dsaHashStats.<callback: H.slots.filter>(s)` | — | [L602](../../dist/dsa.js#L602) |
| Function | `dsaHashStats.<callback: H.slots.filter>(s)` | — | [L610](../../dist/dsa.js#L610) |
| Function | `dsaHashSvg(H)` | — | [L613](../../dist/dsa.js#L613) |
| Function | `dsaHashSvg.<callback: H.chains[i].forEach>(k, j)` | — | [L620](../../dist/dsa.js#L620) |
| Function | `dsaHashing()` | — | [L630](../../dist/dsa.js#L630) |
| Function | `dsaHashing.<callback: [5, 7, 8, 11, 13].map>(v)` | — | [L635](../../dist/dsa.js#L635) |
| Function | `dsaHashing.<callback: theory.map>(t)` | — | [L638](../../dist/dsa.js#L638) |
| Function | `dsaH(n)` | — | [L653](../../dist/dsa.js#L653) |
| Function | `dsaUpd(n)` | — | [L654](../../dist/dsa.js#L654) |
| Function | `dsaBstInsert(n, k)` | — | [L655](../../dist/dsa.js#L655) |
| Function | `dsaRotR(y, log, tag)` | — | [L656](../../dist/dsa.js#L656) |
| Function | `dsaRotL(x, log, tag)` | — | [L657](../../dist/dsa.js#L657) |
| Function | `dsaRebalance(n, log)` | — | [L658](../../dist/dsa.js#L658) |
| Function | `dsaAvlInsert(n, k, log)` | — | [L664](../../dist/dsa.js#L664) |
| Function | `dsaMin(n)` | — | [L665](../../dist/dsa.js#L665) |
| Function | `dsaDelete(n, k, avl, info, log)` | — | [L666](../../dist/dsa.js#L666) |
| Function | `dsaTreeKeys(n, out = [])` | — | [L677](../../dist/dsa.js#L677) |
| Function | `dsaPre(n, out = [])` | — | [L678](../../dist/dsa.js#L678) |
| Function | `dsaPost(n, out = [])` | — | [L679](../../dist/dsa.js#L679) |
| Function | `dsaLevel(n)` | — | [L680](../../dist/dsa.js#L680) |
| Function | `dsaCount(n)` | — | [L681](../../dist/dsa.js#L681) |
| Function | `dsaSearchSteps(n, k)` | — | [L682](../../dist/dsa.js#L682) |
| Function | `<callback: Array.from>(_, i)` | — | [L685](../../dist/dsa.js#L685) |
| Function | `<callback: () => { const g = mlRng(7), a = Array.from({ length: 15 }, (_, i) => i + 1); for (let i = a.length - 1; i > 0; i--) { const j = g.int(i + 1); [a[i], a[j]] = [a[j], a[i]]; } return a; }>()` | — | [L686](../../dist/dsa.js#L686) |
| Function | `<callback: () => { const g = mlRng(7), a = Array.from({ length: 15 }, (_, i) => i + 1); for (let i = a.length - 1; i > 0; i--) { const j = g.int(i + 1); [a[i], a[j]] = [a[j], a[i]]; } return a; }>.<callback: Array.from>(_, i)` | — | [L686](../../dist/dsa.js#L686) |
| Function | `dsaTreeNew()` | — | [L689](../../dist/dsa.js#L689) |
| Function | `dsaTreeInsert()` | — | [L690](../../dist/dsa.js#L690) |
| Function | `dsaTreeSvg(root, title, hot)` | — | [L692](../../dist/dsa.js#L692) |
| Function | `dsaTreeSvg.<callback: keys.map>(k, i)` | — | [L693](../../dist/dsa.js#L693) |
| Function | `dsaTreeSvg.walk(n, d)` | — | [L696](../../dist/dsa.js#L696) |
| Function | `dsaHeapNew()` | — | [L702](../../dist/dsa.js#L702) |
| Function | `dsaLess(x, y)` | — | [L703](../../dist/dsa.js#L703) |
| Function | `dsaHeapPush(quiet)` | — | [L704](../../dist/dsa.js#L704) |
| Function | `dsaHeapPop()` | — | [L710](../../dist/dsa.js#L710) |
| Function | `dsaHeapSvg()` | — | [L715](../../dist/dsa.js#L715) |
| Function | `dsaHeapSvg.pos(i)` | — | [L718](../../dist/dsa.js#L718) |
| Function | `dsaHeapSvg.<callback: a.forEach>(_, i)` | — | [L719](../../dist/dsa.js#L719) |
| Function | `dsaHeapSvg.<callback: a.forEach>([name, eta], i)` | — | [L720](../../dist/dsa.js#L720) |
| Function | `dsaHeapSvg.<callback: a.forEach>([name, eta], i)` | — | [L722](../../dist/dsa.js#L722) |
| Function | `dsaTrie(prefix)` | — | [L727](../../dist/dsa.js#L727) |
| Function | `dsaTrie.collect(m)` | — | [L731](../../dist/dsa.js#L731) |
| Function | `dsaTrie.<callback: DSA_TRIE_WORDS.reduce>(s, w)` | — | [L732](../../dist/dsa.js#L732) |
| Function | `dsaTrees()` | — | [L735](../../dist/dsa.js#L735) |
| Function | `dsaTrees.<callback: present.map>(k)` | — | [L739](../../dist/dsa.js#L739) |
| Function | `dsaTrees.<callback: present.map>(k)` | — | [L739](../../dist/dsa.js#L739) |
| Function | `dsaTrees.<callback: Object.entries(DSA_TREE_INPUTS).map>([id, x])` | — | [L742](../../dist/dsa.js#L742) |
| Function | `dsaTrees.<callback: present.map>(k)` | — | [L742](../../dist/dsa.js#L742) |
| Function | `dsaTrees.<callback: T.rot.map>(r)` | — | [L747](../../dist/dsa.js#L747) |
| Function | `dsaTrees.<callback: ["C", "Co", "Cork", "M", "Ma", "B", "K", "S", "Do", "Z"].map>(v)` | — | [L759](../../dist/dsa.js#L759) |
| Function | `dsaTrees.<callback: trie.matches.map>(m)` | — | [L761](../../dist/dsa.js#L761) |
| Function | `dsaHaversine(a, b)` | — | [L767](../../dist/dsa.js#L767) |
| Function | `<callback: () => { // undirected: every zone to its 3 nearest zones, weight = Haversine km
  const n = DSA_ZONES.length, adj = Array.from({ length: n }, () => new Map());
  for (let i = 0; i < n; i++) DSA_ZONES.map((z, j) => [j, dsaHaversine(DSA_ZONES[i], z)]).filter(([j]) => j !== i).sort((a, b) => a[1] - b[1]).slice(0, 3).forEach(([j, d]) => { const w = Math.round(d * 100) / 100; adj[i].set(j, w); adj[j].set(i, w); });
  const edges = []; adj.forEach((m, i) => m.forEach((w, j) => { if (i < j) edges.push([i, j, w]); }));
  return { n, adj: adj.map((m) => [...m.entries()].sort((a, b) => a[0] - b[0])), edges };
}>()` | — | [L768](../../dist/dsa.js#L768) |
| Function | `<callback: () => { // undirected: every zone to its 3 nearest zones, weight = Haversine km
  const n = DSA_ZONES.length, adj = Array.from({ length: n }, () => new Map());
  for (let i = 0; i < n; i++) DSA_ZONES.map((z, j) => [j, dsaHaversine(DSA_ZONES[i], z)]).filter(([j]) => j !== i).sort((a, b) => a[1] - b[1]).slice(0, 3).forEach(([j, d]) => { const w = Math.round(d * 100) / 100; adj[i].set(j, w); adj[j].set(i, w); });
  const edges = []; adj.forEach((m, i) => m.forEach((w, j) => { if (i < j) edges.push([i, j, w]); }));
  return { n, adj: adj.map((m) => [...m.entries()].sort((a, b) => a[0] - b[0])), edges };
}>.<callback: Array.from>()` | — | [L769](../../dist/dsa.js#L769) |
| Function | `<callback: () => { // undirected: every zone to its 3 nearest zones, weight = Haversine km
  const n = DSA_ZONES.length, adj = Array.from({ length: n }, () => new Map());
  for (let i = 0; i < n; i++) DSA_ZONES.map((z, j) => [j, dsaHaversine(DSA_ZONES[i], z)]).filter(([j]) => j !== i).sort((a, b) => a[1] - b[1]).slice(0, 3).forEach(([j, d]) => { const w = Math.round(d * 100) / 100; adj[i].set(j, w); adj[j].set(i, w); });
  const edges = []; adj.forEach((m, i) => m.forEach((w, j) => { if (i < j) edges.push([i, j, w]); }));
  return { n, adj: adj.map((m) => [...m.entries()].sort((a, b) => a[0] - b[0])), edges };
}>.<callback: DSA_ZONES.map>(z, j)` | — | [L770](../../dist/dsa.js#L770) |
| Function | `<callback: () => { // undirected: every zone to its 3 nearest zones, weight = Haversine km
  const n = DSA_ZONES.length, adj = Array.from({ length: n }, () => new Map());
  for (let i = 0; i < n; i++) DSA_ZONES.map((z, j) => [j, dsaHaversine(DSA_ZONES[i], z)]).filter(([j]) => j !== i).sort((a, b) => a[1] - b[1]).slice(0, 3).forEach(([j, d]) => { const w = Math.round(d * 100) / 100; adj[i].set(j, w); adj[j].set(i, w); });
  const edges = []; adj.forEach((m, i) => m.forEach((w, j) => { if (i < j) edges.push([i, j, w]); }));
  return { n, adj: adj.map((m) => [...m.entries()].sort((a, b) => a[0] - b[0])), edges };
}>.<callback: DSA_ZONES.map((z, j) => [j, dsaHaversine(DSA_ZONES[i], z)]).filter>([j])` | — | [L770](../../dist/dsa.js#L770) |
| Function | `<callback: () => { // undirected: every zone to its 3 nearest zones, weight = Haversine km
  const n = DSA_ZONES.length, adj = Array.from({ length: n }, () => new Map());
  for (let i = 0; i < n; i++) DSA_ZONES.map((z, j) => [j, dsaHaversine(DSA_ZONES[i], z)]).filter(([j]) => j !== i).sort((a, b) => a[1] - b[1]).slice(0, 3).forEach(([j, d]) => { const w = Math.round(d * 100) / 100; adj[i].set(j, w); adj[j].set(i, w); });
  const edges = []; adj.forEach((m, i) => m.forEach((w, j) => { if (i < j) edges.push([i, j, w]); }));
  return { n, adj: adj.map((m) => [...m.entries()].sort((a, b) => a[0] - b[0])), edges };
}>.<callback: DSA_ZONES.map((z, j) => [j, dsaHaversine(DSA_ZONES[i], z)]).filter(([j]) => j !== i).sort>(a, b)` | — | [L770](../../dist/dsa.js#L770) |
| Function | `<callback: () => { // undirected: every zone to its 3 nearest zones, weight = Haversine km
  const n = DSA_ZONES.length, adj = Array.from({ length: n }, () => new Map());
  for (let i = 0; i < n; i++) DSA_ZONES.map((z, j) => [j, dsaHaversine(DSA_ZONES[i], z)]).filter(([j]) => j !== i).sort((a, b) => a[1] - b[1]).slice(0, 3).forEach(([j, d]) => { const w = Math.round(d * 100) / 100; adj[i].set(j, w); adj[j].set(i, w); });
  const edges = []; adj.forEach((m, i) => m.forEach((w, j) => { if (i < j) edges.push([i, j, w]); }));
  return { n, adj: adj.map((m) => [...m.entries()].sort((a, b) => a[0] - b[0])), edges };
}>.<callback: DSA_ZONES.map((z, j) => [j, dsaHaversine(DSA_ZONES[i], z)]).filter(([j]) => j !== i).sort((a, b) => a[1] - b[1]).slice(0, 3).forEach>([j, d])` | — | [L770](../../dist/dsa.js#L770) |
| Function | `<callback: () => { // undirected: every zone to its 3 nearest zones, weight = Haversine km
  const n = DSA_ZONES.length, adj = Array.from({ length: n }, () => new Map());
  for (let i = 0; i < n; i++) DSA_ZONES.map((z, j) => [j, dsaHaversine(DSA_ZONES[i], z)]).filter(([j]) => j !== i).sort((a, b) => a[1] - b[1]).slice(0, 3).forEach(([j, d]) => { const w = Math.round(d * 100) / 100; adj[i].set(j, w); adj[j].set(i, w); });
  const edges = []; adj.forEach((m, i) => m.forEach((w, j) => { if (i < j) edges.push([i, j, w]); }));
  return { n, adj: adj.map((m) => [...m.entries()].sort((a, b) => a[0] - b[0])), edges };
}>.<callback: adj.forEach>(m, i)` | — | [L771](../../dist/dsa.js#L771) |
| Function | `<callback: () => { // undirected: every zone to its 3 nearest zones, weight = Haversine km
  const n = DSA_ZONES.length, adj = Array.from({ length: n }, () => new Map());
  for (let i = 0; i < n; i++) DSA_ZONES.map((z, j) => [j, dsaHaversine(DSA_ZONES[i], z)]).filter(([j]) => j !== i).sort((a, b) => a[1] - b[1]).slice(0, 3).forEach(([j, d]) => { const w = Math.round(d * 100) / 100; adj[i].set(j, w); adj[j].set(i, w); });
  const edges = []; adj.forEach((m, i) => m.forEach((w, j) => { if (i < j) edges.push([i, j, w]); }));
  return { n, adj: adj.map((m) => [...m.entries()].sort((a, b) => a[0] - b[0])), edges };
}>.<callback: adj.forEach>.<callback: m.forEach>(w, j)` | — | [L771](../../dist/dsa.js#L771) |
| Function | `<callback: () => { // undirected: every zone to its 3 nearest zones, weight = Haversine km
  const n = DSA_ZONES.length, adj = Array.from({ length: n }, () => new Map());
  for (let i = 0; i < n; i++) DSA_ZONES.map((z, j) => [j, dsaHaversine(DSA_ZONES[i], z)]).filter(([j]) => j !== i).sort((a, b) => a[1] - b[1]).slice(0, 3).forEach(([j, d]) => { const w = Math.round(d * 100) / 100; adj[i].set(j, w); adj[j].set(i, w); });
  const edges = []; adj.forEach((m, i) => m.forEach((w, j) => { if (i < j) edges.push([i, j, w]); }));
  return { n, adj: adj.map((m) => [...m.entries()].sort((a, b) => a[0] - b[0])), edges };
}>.<callback: adj.map>(m)` | — | [L772](../../dist/dsa.js#L772) |
| Function | `<callback: () => { // undirected: every zone to its 3 nearest zones, weight = Haversine km
  const n = DSA_ZONES.length, adj = Array.from({ length: n }, () => new Map());
  for (let i = 0; i < n; i++) DSA_ZONES.map((z, j) => [j, dsaHaversine(DSA_ZONES[i], z)]).filter(([j]) => j !== i).sort((a, b) => a[1] - b[1]).slice(0, 3).forEach(([j, d]) => { const w = Math.round(d * 100) / 100; adj[i].set(j, w); adj[j].set(i, w); });
  const edges = []; adj.forEach((m, i) => m.forEach((w, j) => { if (i < j) edges.push([i, j, w]); }));
  return { n, adj: adj.map((m) => [...m.entries()].sort((a, b) => a[0] - b[0])), edges };
}>.<callback: adj.map>.<callback: [...m.entries()].sort>(a, b)` | — | [L772](../../dist/dsa.js#L772) |
| Function | `dsaGraphFrames(algo, src, dst)` | — | [L775](../../dist/dsa.js#L775) |
| Function | `dsaGraphFrames.name(i)` | — | [L776](../../dist/dsa.js#L776) |
| Function | `dsaGraphFrames.<callback: pq.sort>(a, b)` | — | [L798](../../dist/dsa.js#L798) |
| Function | `dsaGraphFrames.<callback: pq.filter>([, v])` | — | [L801](../../dist/dsa.js#L801) |
| Function | `dsaGraphFrames.<callback: pq.filter(([, v]) => !done.has(v)).map>([, v])` | — | [L801](../../dist/dsa.js#L801) |
| Function | `dsaGraphNew()` | — | [L816](../../dist/dsa.js#L816) |
| Function | `dsaGraphSvg(F)` | — | [L820](../../dist/dsa.js#L820) |
| Function | `dsaGraphSvg.P(i)` | — | [L821](../../dist/dsa.js#L821) |
| Function | `dsaGraphSvg.<callback: (F.tree \|\| []).map>([u, v])` | — | [L822](../../dist/dsa.js#L822) |
| Function | `dsaGraphSvg.<callback: F.prev.forEach>(p, v)` | — | [L825](../../dist/dsa.js#L825) |
| Function | `dsaGraphSvg.<callback: DSA_ZONES.forEach>(z, i)` | — | [L832](../../dist/dsa.js#L832) |
| Function | `dsaGraphs()` | — | [L843](../../dist/dsa.js#L843) |
| Function | `dsaGraphs.name(i)` | — | [L845](../../dist/dsa.js#L845) |
| Function | `dsaGraphs.<callback: DSA_ZONES.map>(z, i)` | — | [L846](../../dist/dsa.js#L846) |
| Function | `dsaGraphs.<callback: DSA_GRAPH.adj.map>(nb, i)` | — | [L860](../../dist/dsa.js#L860) |
| Function | `dsaGraphs.<callback: DSA_GRAPH.adj.map>.<callback: nb.map>([v, w])` | — | [L860](../../dist/dsa.js#L860) |
| Function | `dsaSortRun(algo, input, trace = null)` | — | [L870](../../dist/dsa.js#L870) |
| Function | `dsaSortRun.key(v)` | — | [L871](../../dist/dsa.js#L871) |
| Function | `dsaSortRun.lt(x, y, i, j)` | — | [L873](../../dist/dsa.js#L873) |
| Function | `dsaSortRun.swap(i, j)` | — | [L874](../../dist/dsa.js#L874) |
| Function | `dsaSortRun.put(i, v)` | — | [L875](../../dist/dsa.js#L875) |
| Function | `dsaSortRun.go(lo, hi)` | — | [L880](../../dist/dsa.js#L880) |
| Function | `dsaSortRun.sift(s, end)` | — | [L882](../../dist/dsa.js#L882) |
| Function | `dsaSortRun.<callback: a.slice().sort>(x, y)` | — | [L883](../../dist/dsa.js#L883) |
| Function | `dsaSortRun.<callback: out.forEach>(v, i)` | — | [L883](../../dist/dsa.js#L883) |
| Function | `dsaSortCount(algo, data)` | — | [L886](../../dist/dsa.js#L886) |
| Function | `dsaSortInput(n, order)` | — | [L889](../../dist/dsa.js#L889) |
| Function | `dsaSortInput.<callback: Array.from>()` | — | [L891](../../dist/dsa.js#L891) |
| Function | `dsaSortInput.<callback: Array.from>()` | — | [L891](../../dist/dsa.js#L891) |
| Function | `dsaSortInput.<callback: base.sort>(x, y)` | — | [L892](../../dist/dsa.js#L892) |
| Function | `dsaSortInput.<callback: base.sort>(x, y)` | — | [L893](../../dist/dsa.js#L893) |
| Function | `dsaSortInput.<callback: base.sort>(x, y)` | — | [L894](../../dist/dsa.js#L894) |
| Function | `dsaTraceNew()` | — | [L898](../../dist/dsa.js#L898) |
| Function | `dsaTraceNew.<callback: Array.from>()` | — | [L899](../../dist/dsa.js#L899) |
| Function | `dsaBars(F)` | — | [L905](../../dist/dsa.js#L905) |
| Function | `dsaBars.<callback: F.a.map>(v, i)` | — | [L907](../../dist/dsa.js#L907) |
| Function | `dsaStability(algo)` | — | [L910](../../dist/dsa.js#L910) |
| Function | `dsaStability.<callback: DSA_DRIVERS.map>(d, i)` | — | [L911](../../dist/dsa.js#L911) |
| Function | `dsaBinarySearch(a, x)` | — | [L916](../../dist/dsa.js#L916) |
| Function | `dsaSorting()` | — | [L922](../../dist/dsa.js#L922) |
| Function | `dsaSorting.<callback: DSA_SORTS.map>([id, label, big, stable])` | — | [L924](../../dist/dsa.js#L924) |
| Function | `dsaSorting.<callback: DSA_DRIVERS.map>(d)` | — | [L925](../../dist/dsa.js#L925) |
| Function | `dsaSorting.<callback: DSA_DRIVERS.map((d) => d[1]).sort>(x, y)` | — | [L925](../../dist/dsa.js#L925) |
| Function | `dsaSorting.<callback: results.map>(r)` | — | [L926](../../dist/dsa.js#L926) |
| Function | `dsaSorting.<callback: [16, 64, 128, 512, 2048].map>(v)` | — | [L928](../../dist/dsa.js#L928) |
| Function | `dsaSorting.<callback: results.map>(r)` | — | [L929](../../dist/dsa.js#L929) |
| Function | `dsaSorting.<callback: results.map>(r)` | — | [L931](../../dist/dsa.js#L931) |
| Function | `dsaSorting.<callback: DSA_SORTS.filter>(s)` | — | [L933](../../dist/dsa.js#L933) |
| Function | `dsaSorting.<callback: DSA_SORTS.filter((s) => s[0] !== "builtin").map>([id, l])` | — | [L933](../../dist/dsa.js#L933) |
| Function | `dsaSorting.<callback: ["merge", "insertion", "selection", "heap", "builtin"].map>(id)` | — | [L939](../../dist/dsa.js#L939) |
| Function | `dsaSorting.<callback: ["merge", "insertion", "selection", "heap", "builtin"].map>.<callback: DSA_SORTS.find>(x)` | — | [L939](../../dist/dsa.js#L939) |
| Function | `dsaSorting.<callback: ["merge", "insertion", "selection", "heap", "builtin"].map>.<callback: s.order.map>([nm, e])` | — | [L939](../../dist/dsa.js#L939) |
| Function | `dsaSorting.<callback: Array.from>(_, i)` | — | [L941](../../dist/dsa.js#L941) |
| Function | `dsaSorting.<callback: etas.map>(v, i)` | — | [L942](../../dist/dsa.js#L942) |
| Function | `dsaSorting.<callback: etas.map>.<callback: bs.steps.some>(s)` | — | [L942](../../dist/dsa.js#L942) |
| Function | `dsaSorting.<callback: bs.steps.map>([lo, hi, mid, v], i)` | — | [L943](../../dist/dsa.js#L943) |
| Function | `dsaKnapsack(cap)` | — | [L950](../../dist/dsa.js#L950) |
| Function | `dsaKnapsack.<callback: Array.from>()` | — | [L951](../../dist/dsa.js#L951) |
| Function | `dsaKnapsack.greedy(keyFn)` | — | [L954](../../dist/dsa.js#L954) |
| Function | `dsaKnapsack.greedy.<callback: DSA_ITEMS.map>(it, i)` | — | [L954](../../dist/dsa.js#L954) |
| Function | `dsaKnapsack.greedy.<callback: DSA_ITEMS.map((it, i) => [i, keyFn(it)]).sort>(a, b)` | — | [L954](../../dist/dsa.js#L954) |
| Function | `dsaKnapsack.greedy.<callback: DSA_ITEMS.map((it, i) => [i, keyFn(it)]).sort((a, b) => b[1] - a[1]).forEach>([i])` | — | [L954](../../dist/dsa.js#L954) |
| Function | `dsaKnapsack.<callback: greedy>(it)` | — | [L955](../../dist/dsa.js#L955) |
| Function | `dsaKnapsack.<callback: greedy>(it)` | — | [L955](../../dist/dsa.js#L955) |
| Function | `dsaFib(n)` | — | [L957](../../dist/dsa.js#L957) |
| Function | `dsaFib.f(m)` | — | [L957](../../dist/dsa.js#L957) |
| Function | `dsaFib.g(m)` | — | [L957](../../dist/dsa.js#L957) |
| Function | `dsaQueens(n)` | — | [L958](../../dist/dsa.js#L958) |
| Function | `dsaQueens.place(r)` | — | [L958](../../dist/dsa.js#L958) |
| Function | `dsaDesign()` | — | [L960](../../dist/dsa.js#L960) |
| Function | `dsaDesign.money(c)` | — | [L961](../../dist/dsa.js#L961) |
| Function | `dsaDesign.<callback: [5, 10, 15, 20, 25, 30, 40].map>(n)` | — | [L962](../../dist/dsa.js#L962) |
| Function | `dsaDesign.<callback: [4, 5, 6, 7, 8, 9, 10, 12].map>(v)` | — | [L969](../../dist/dsa.js#L969) |
| Function | `dsaDesign.<callback: Array.from>(_, c)` | — | [L970](../../dist/dsa.js#L970) |
| Function | `dsaDesign.<callback: ks.T.map>(row, i)` | — | [L970](../../dist/dsa.js#L970) |
| Function | `dsaDesign.<callback: ks.T.map>.<callback: row.map>(v)` | — | [L970](../../dist/dsa.js#L970) |
| Function | `dsaDesign.<callback: ks.take.map>(i)` | — | [L972](../../dist/dsa.js#L972) |
| Function | `dsaDesign.<callback: ks.byRatio.got.map>(i)` | — | [L973](../../dist/dsa.js#L973) |
| Function | `dsaDesign.<callback: ks.byValue.got.map>(i)` | — | [L974](../../dist/dsa.js#L974) |
| Function | `dsaDesign.<callback: [4, 5, 6, 7, 8, 9, 10].map>(v)` | — | [L977](../../dist/dsa.js#L977) |
| Function | `dsaDesign.<callback: Array.from>(_, i)` | — | [L978](../../dist/dsa.js#L978) |
| Function | `dsaTopicLink(id, k)` | — | [L994](../../dist/dsa.js#L994) |
| Function | `dsaGaps()` | — | [L996](../../dist/dsa.js#L996) |
| Function | `dsaGaps.<callback: DSA_EXPERIMENTS.map>([id, flag, q, topic])` | — | [L998](../../dist/dsa.js#L998) |
| Function | `dsaGaps.<callback: DSA_EXERCISES.map>([text, topic], i)` | — | [L999](../../dist/dsa.js#L999) |
| Function | `dsaInspector()` | — | [L1025](../../dist/dsa.js#L1025) |
| Function | `dsaInspector.<callback: info.facts.map>([k, v])` | — | [L1030](../../dist/dsa.js#L1030) |
| Function | `dsaInspector.<callback: t.lessons.map>(n)` | — | [L1031](../../dist/dsa.js#L1031) |
| Function | `dsaInspector.<callback: info.files.map>([l, u])` | — | [L1032](../../dist/dsa.js#L1032) |
| Function | `dsaInspector.<callback: info.questions.map>(x)` | — | [L1034](../../dist/dsa.js#L1034) |
| Function | `lists()` | — | [L1038](../../dist/dsa.js#L1038) |
| Function | `dsaView()` | — | [L1040](../../dist/dsa.js#L1040) |
| Function | `dsaView.<callback: dsaTopics.map>(x)` | — | [L1043](../../dist/dsa.js#L1043) |
| Function | `dsaOpen(topic)` | — | [L1047](../../dist/dsa.js#L1047) |
| Function | `dsaSetHash()` | — | [L1052](../../dist/dsa.js#L1052) |
| Function | `dsaClick(button)` | — | [L1056](../../dist/dsa.js#L1056) |
| Function | `<callback: document.addEventListener, "input">(event)` | — | [L1105](../../dist/dsa.js#L1105) |
| Function | `<callback: document.addEventListener, "change">(event)` | — | [L1112](../../dist/dsa.js#L1112) |
| Method | `DsaNode.constructor(v)` | — | [L204](../../dist/dsa.js#L204) |
| Method | `DsaSingly.constructor()` | — | [L208](../../dist/dsa.js#L208) |
| Method | `DsaSingly.pushFront(v)` | — | [L209](../../dist/dsa.js#L209) |
| Method | `DsaSingly.pushBack(v)` | — | [L210](../../dist/dsa.js#L210) |
| Method | `DsaSingly.popFront()` | — | [L211](../../dist/dsa.js#L211) |
| Method | `DsaSingly.popBack()` | — | [L212](../../dist/dsa.js#L212) |
| Method | `DsaSingly.nodes()` | — | [L218](../../dist/dsa.js#L218) |
| Method | `DsaSingly.validate()` | — | [L219](../../dist/dsa.js#L219) |
| Method | `DsaDoubly.constructor()` | — | [L224](../../dist/dsa.js#L224) |
| Method | `DsaDoubly.pushFront(v)` | — | [L225](../../dist/dsa.js#L225) |
| Method | `DsaDoubly.pushBack(v)` | — | [L226](../../dist/dsa.js#L226) |
| Method | `DsaDoubly.popFront()` | — | [L227](../../dist/dsa.js#L227) |
| Method | `DsaDoubly.popBack()` | — | [L228](../../dist/dsa.js#L228) |
| Method | `DsaDoubly.nodes()` | — | [L229](../../dist/dsa.js#L229) |
| Method | `DsaDoubly.validate()` | — | [L230](../../dist/dsa.js#L230) |
| Method | `DsaCircularSingly.constructor()` | — | [L235](../../dist/dsa.js#L235) |
| Method | `DsaCircularSingly.head()` | — | [L236](../../dist/dsa.js#L236) |
| Method | `DsaCircularSingly.pushFront(v)` | — | [L237](../../dist/dsa.js#L237) |
| Method | `DsaCircularSingly.pushBack(v)` | — | [L238](../../dist/dsa.js#L238) |
| Method | `DsaCircularSingly.popFront()` | — | [L239](../../dist/dsa.js#L239) |
| Method | `DsaCircularSingly.popBack()` | — | [L240](../../dist/dsa.js#L240) |
| Method | `DsaCircularSingly.rotate(k)` | — | [L247](../../dist/dsa.js#L247) |
| Method | `DsaCircularSingly.nodes()` | — | [L248](../../dist/dsa.js#L248) |
| Method | `DsaCircularSingly.validate()` | — | [L249](../../dist/dsa.js#L249) |
| Method | `DsaCircularDoubly.constructor()` | — | [L254](../../dist/dsa.js#L254) |
| Method | `DsaCircularDoubly.insertAfter(node, v, where)` | — | [L255](../../dist/dsa.js#L255) |
| Method | `DsaCircularDoubly.unlink(node)` | — | [L256](../../dist/dsa.js#L256) |
| Method | `DsaCircularDoubly.pushFront(v)` | — | [L257](../../dist/dsa.js#L257) |
| Method | `DsaCircularDoubly.pushBack(v)` | — | [L258](../../dist/dsa.js#L258) |
| Method | `DsaCircularDoubly.popFront()` | — | [L259](../../dist/dsa.js#L259) |
| Method | `DsaCircularDoubly.popBack()` | — | [L260](../../dist/dsa.js#L260) |
| Method | `DsaCircularDoubly.rotate(k)` | — | [L261](../../dist/dsa.js#L261) |
| Method | `DsaCircularDoubly.nodes()` | — | [L268](../../dist/dsa.js#L268) |
| Method | `DsaCircularDoubly.validate()` | — | [L269](../../dist/dsa.js#L269) |
| Method | `DsaTNode.constructor(k)` | — | [L652](../../dist/dsa.js#L652) |

### `dist/explorer.js`

[Open source](../../dist/explorer.js)

| Kind | Signature | Decorators | Source |
| --- | --- | --- | --- |
| Function | `indexSystem()` | — | [L53](../../dist/explorer.js#L53) |
| Function | `indexSystem.<callback: S.links.map>(link)` | — | [L55](../../dist/explorer.js#L55) |
| Function | `indexSystem.<callback: S.folders.flatMap>(group)` | — | [L56](../../dist/explorer.js#L56) |
| Function | `indexSystem.<callback: S.folders.flatMap>.<callback: group.children.map>(entry)` | — | [L56](../../dist/explorer.js#L56) |
| Function | `$(id)` | — | [L60](../../dist/explorer.js#L60) |
| Function | `icon(name, size = 18)` | — | [L61](../../dist/explorer.js#L61) |
| Function | `<callback: document.querySelectorAll("[data-icon]").forEach>(element)` | — | [L64](../../dist/explorer.js#L64) |
| Function | `announce(message)` | — | [L66](../../dist/explorer.js#L66) |
| Function | `componentColor(id)` | — | [L70](../../dist/explorer.js#L70) |
| Function | `componentMark(id, size = 19)` | — | [L74](../../dist/explorer.js#L74) |
| Function | `viewHeading(kicker, title, detail, badge = "")` | — | [L78](../../dist/explorer.js#L78) |
| Function | `updateControls()` | — | [L82](../../dist/explorer.js#L82) |
| Function | `updateControls.<callback: Object.entries(S.scenarios).map>([id, trace])` | — | [L84](../../dist/explorer.js#L84) |
| Function | `architectureView()` | — | [L94](../../dist/explorer.js#L94) |
| Function | `architectureView.<callback: S.links.filter>({ from, to })` | — | [L97](../../dist/explorer.js#L97) |
| Function | `architectureView.<callback: trace?.steps.map>([id])` | — | [L98](../../dist/explorer.js#L98) |
| Function | `architectureView.<callback: [...visibleLinks].flatMap>({ from, to })` | — | [L100](../../dist/explorer.js#L100) |
| Function | `architectureView.<callback: Object.keys(kindLabels).flatMap>(kind)` | — | [L101](../../dist/explorer.js#L101) |
| Function | `architectureView.<callback: Object.keys(kindLabels).flatMap>.<callback: ["base", "active"].map>(tone)` | — | [L101](../../dist/explorer.js#L101) |
| Function | `architectureView.<callback: [...S.links].sort>(a, b)` | — | [L103](../../dist/explorer.js#L103) |
| Function | `architectureView.<callback: orderedLinks.map>(link)` | — | [L104](../../dist/explorer.js#L104) |
| Function | `architectureView.<callback: Object.values(S.groups).map>(group, index)` | — | [L109](../../dist/explorer.js#L109) |
| Function | `architectureView.<callback: Object.entries(S.components).map>([id, component])` | — | [L110](../../dist/explorer.js#L110) |
| Function | `architectureView.<callback: Object.entries(kindLabels).map>([kind, label])` | — | [L127](../../dist/explorer.js#L127) |
| Function | `cardsMarkup()` | — | [L130](../../dist/explorer.js#L130) |
| Function | `cardsMarkup.<callback: Object.entries(S.components).filter>([, component])` | — | [L132](../../dist/explorer.js#L132) |
| Function | `cardsMarkup.<callback: Object.entries(S.components).filter>.<callback: [component.title, component.tech, component.summary].some>(item)` | — | [L133](../../dist/explorer.js#L133) |
| Function | `cardsMarkup.<callback: matches.map>([id, component])` | — | [L134](../../dist/explorer.js#L134) |
| Function | `componentsView()` | — | [L139](../../dist/explorer.js#L139) |
| Function | `componentsView.<callback: Object.entries(S.groups).map>([id, group])` | — | [L142](../../dist/explorer.js#L142) |
| Function | `deploymentView()` | — | [L146](../../dist/explorer.js#L146) |
| Function | `deploymentView.<callback: S.zones.map>(zone, index)` | — | [L148](../../dist/explorer.js#L148) |
| Function | `deploymentView.<callback: S.zones.map>.<callback: zone.nodes.map>(id)` | — | [L148](../../dist/explorer.js#L148) |
| Function | `foldersView()` | — | [L152](../../dist/explorer.js#L152) |
| Function | `foldersView.<callback: S.folders.map>(group)` | — | [L155](../../dist/explorer.js#L155) |
| Function | `foldersView.<callback: S.folders.map>.<callback: group.children.some>(entry)` | — | [L155](../../dist/explorer.js#L155) |
| Function | `foldersView.<callback: S.folders.map>.<callback: group.children.map>(entry)` | — | [L155](../../dist/explorer.js#L155) |
| Function | `foldersView.<callback: selected.example.map>(file)` | — | [L156](../../dist/explorer.js#L156) |
| Function | `inspectorMarkup()` | — | [L159](../../dist/explorer.js#L159) |
| Function | `inspectorMarkup.<callback: S.links.filter>({ to })` | — | [L165](../../dist/explorer.js#L165) |
| Function | `inspectorMarkup.<callback: S.links.filter>({ from })` | — | [L166](../../dist/explorer.js#L166) |
| Function | `inspectorMarkup.<callback: neighbors.filter>({ rows })` | — | [L172](../../dist/explorer.js#L172) |
| Function | `inspectorMarkup.<callback: neighbors.filter(({ rows }) => rows.length).map>({ heading, rows, target })` | — | [L172](../../dist/explorer.js#L172) |
| Function | `inspectorMarkup.<callback: neighbors.filter(({ rows }) => rows.length).map>.<callback: rows.map>(link)` | — | [L172](../../dist/explorer.js#L172) |
| Function | `render()` | — | [L179](../../dist/explorer.js#L179) |
| Function | `setSystem(id, fromClick = false)` | — | [L206](../../dist/explorer.js#L206) |
| Function | `stopPlayback()` | — | [L223](../../dist/explorer.js#L223) |
| Function | `switchView(view)` | — | [L228](../../dist/explorer.js#L228) |
| Function | `applyStep(step)` | — | [L239](../../dist/explorer.js#L239) |
| Function | `setScenario(id)` | — | [L258](../../dist/explorer.js#L258) |
| Function | `playTrace()` | — | [L271](../../dist/explorer.js#L271) |
| Function | `playTrace.<callback: setInterval>()` | — | [L278](../../dist/explorer.js#L278) |
| Function | `<callback: document.addEventListener, "click">(event)` | — | [L287](../../dist/explorer.js#L287) |
| Function | `<callback: document.querySelector('[role="tablist"]').addEventListener, "keydown">(event)` | — | [L329](../../dist/explorer.js#L329) |
| Function | `<callback: $("view-content").addEventListener, "input">(event)` | — | [L341](../../dist/explorer.js#L341) |
| Function | `<callback: $("view-content").addEventListener, "toggle">(event)` | — | [L348](../../dist/explorer.js#L348) |

### `dist/ml.js`

[Open source](../../dist/ml.js)

| Kind | Signature | Decorators | Source |
| --- | --- | --- | --- |
| Function | `<callback: mlTopics.map>(t)` | — | [L34](../../dist/ml.js#L34) |
| Function | `mlChip(status)` | — | [L36](../../dist/ml.js#L36) |
| Function | `mlRng(seed)` | — | [L43](../../dist/ml.js#L43) |
| Function | `mlRng.uniform()` | — | [L45](../../dist/ml.js#L45) |
| Function | `mlRng.normal()` | — | [L46](../../dist/ml.js#L46) |
| Function | `mlRng.range(lo, hi)` | — | [L47](../../dist/ml.js#L47) |
| Function | `mlRng.int(n)` | — | [L47](../../dist/ml.js#L47) |
| Function | `mlButton(action, label, { primary = false, iconName = "", disabled = false } = {})` | — | [L60](../../dist/ml.js#L60) |
| Function | `mlSelect(name, label, options, value)` | — | [L64](../../dist/ml.js#L64) |
| Function | `mlSelect.<callback: options.map>([v, l])` | — | [L65](../../dist/ml.js#L65) |
| Function | `mlRange(name, label, min, max, step, value, shown)` | — | [L68](../../dist/ml.js#L68) |
| Function | `mlChart(series, { logX = false, logY = false, xLabel = "", yLabel = "", height = 170, hlines = [], vline = null } = {})` | — | [L73](../../dist/ml.js#L73) |
| Function | `mlChart.<callback: series.flatMap>(s)` | — | [L75](../../dist/ml.js#L75) |
| Function | `mlChart.<callback: hlines.map>(h)` | — | [L75](../../dist/ml.js#L75) |
| Function | `mlChart.fx(x)` | — | [L76](../../dist/ml.js#L76) |
| Function | `mlChart.fy(y)` | — | [L76](../../dist/ml.js#L76) |
| Function | `mlChart.<callback: series.flatMap>(s)` | — | [L77](../../dist/ml.js#L77) |
| Function | `mlChart.<callback: series.flatMap>.<callback: s.points.map>(p)` | — | [L77](../../dist/ml.js#L77) |
| Function | `mlChart.<callback: all.map>(p)` | — | [L77](../../dist/ml.js#L77) |
| Function | `mlChart.sx(x)` | — | [L81](../../dist/ml.js#L81) |
| Function | `mlChart.sy(y)` | — | [L82](../../dist/ml.js#L82) |
| Function | `mlChart.fmt(v)` | — | [L83](../../dist/ml.js#L83) |
| Function | `mlChart.<callback: [0, 0.25, 0.5, 0.75, 1].map>(f)` | — | [L84](../../dist/ml.js#L84) |
| Function | `mlChart.<callback: [0, 0.25, 0.5, 0.75, 1].map((f) => y0 + pad + f * (y1 - y0 - 2 * pad)).map>(v)` | — | [L84](../../dist/ml.js#L84) |
| Function | `mlChart.<callback: series.flatMap>(s)` | — | [L85](../../dist/ml.js#L85) |
| Function | `mlChart.<callback: series.flatMap>.<callback: s.points.map>(p)` | — | [L85](../../dist/ml.js#L85) |
| Function | `mlChart.<callback: [...new Set(series.flatMap((s) => s.points.map((p) => p[0])))].filter>(v)` | — | [L85](../../dist/ml.js#L85) |
| Function | `mlChart.<callback: [0, 0.25, 0.5, 0.75, 1].map>(f)` | — | [L85](../../dist/ml.js#L85) |
| Function | `mlChart.<callback: ticksY.map>(v)` | — | [L87](../../dist/ml.js#L87) |
| Function | `mlChart.<callback: ticksX.map>(v)` | — | [L88](../../dist/ml.js#L88) |
| Function | `mlChart.<callback: hlines.map>(h)` | — | [L91](../../dist/ml.js#L91) |
| Function | `mlChart.<callback: series.map>(s)` | — | [L93](../../dist/ml.js#L93) |
| Function | `mlChart.<callback: series.map>.<callback: s.points.map>(p)` | — | [L93](../../dist/ml.js#L93) |
| Function | `mlLegend(items)` | — | [L97](../../dist/ml.js#L97) |
| Function | `mlLegend.<callback: items.map>([cls, text])` | — | [L98](../../dist/ml.js#L98) |
| Function | `mlOverview()` | — | [L112](../../dist/ml.js#L112) |
| Function | `mlOverview.<callback: Object.keys(mlStatus).map>(k)` | — | [L114](../../dist/ml.js#L114) |
| Function | `mlOverview.<callback: mlMap.map>([topic, ic, title, status, text, where])` | — | [L115](../../dist/ml.js#L115) |
| Function | `mlOverview.<callback: [
      ["Forecast", "λ* = max(load, LSTM 5-min forecast)", "Plan for the load that is coming"],
      ["Score", "Isolation Forest on telemetry", "Blame the module whose demand deviates most"],
      ["Optimise", "Sim.bip over 2⁶ = 64 configurations", "min J subject to utilisation, SLA, replicas, availability"],
      ["Override", "score ≥ 0.9 → all loose; ≥ 0.7 → isolate blamed module", "Safety rules around the optimiser"],
      ["Hysteresis", "merge back only after 300 s", "Stop the optimiser oscillating"],
      ["Apply", "dual-run while pods start (8–30 s)", "40 ms state hand-over, measured in the prototype"],
    ].map>([t, c, s], i)` | — | [L123](../../dist/ml.js#L123) |
| Function | `mlEvalConfig(c, lam, pCrash)` | — | [L147](../../dist/ml.js#L147) |
| Function | `mlEvalConfig.<callback: c.map>(x)` | — | [L149](../../dist/ml.js#L149) |
| Function | `mlEvalConfig.<callback: v.map>(vi, i)` | — | [L155](../../dist/ml.js#L155) |
| Function | `mlEvalConfig.<callback: reps.reduce>(s, r)` | — | [L157](../../dist/ml.js#L157) |
| Function | `mlEvalConfig.<callback: c.reduce>(s, x)` | — | [L157](../../dist/ml.js#L157) |
| Function | `mlEvalConfig.<callback: v.filter>(_, i)` | — | [L158](../../dist/ml.js#L158) |
| Function | `mlBipSolve(lam, a, anomModule, now, hybrid = true)` | — | [L169](../../dist/ml.js#L169) |
| Function | `mlBipSolve.<callback: Array.from>(_, i)` | — | [L176](../../dist/ml.js#L176) |
| Function | `mlBipSolve.<callback: c.reduce>(x, y)` | — | [L177](../../dist/ml.js#L177) |
| Function | `mlBipSolve.<callback: c.reduce>(x, ci, i)` | — | [L180](../../dist/ml.js#L180) |
| Function | `mlBipSolve.<callback: m.reps.some>(r)` | — | [L183](../../dist/ml.js#L183) |
| Function | `mlBipSolve.<callback: rows.filter>(r)` | — | [L188](../../dist/ml.js#L188) |
| Function | `mlAfterOverrides(choice, a, anomModule)` | — | [L191](../../dist/ml.js#L191) |
| Function | `mlShape(c)` | — | [L197](../../dist/ml.js#L197) |
| Function | `mlShape.<callback: c.reduce>(x, y)` | — | [L197](../../dist/ml.js#L197) |
| Function | `mlConfigChips(c, now = null)` | — | [L199](../../dist/ml.js#L199) |
| Function | `mlConfigChips.<callback: ML_SERVICES.map>(name, i)` | — | [L200](../../dist/ml.js#L200) |
| Function | `mlOptimizer()` | — | [L203](../../dist/ml.js#L203) |
| Function | `mlOptimizer.<callback: res.rows.filter>(r)` | — | [L208](../../dist/ml.js#L208) |
| Function | `mlOptimizer.<callback: res.rows.filter((r) => r.ok).sort>(x, y)` | — | [L208](../../dist/ml.js#L208) |
| Function | `mlOptimizer.<callback: res.rows.find>(r)` | — | [L209](../../dist/ml.js#L209) |
| Function | `mlOptimizer.<callback: res.rows.find>(r)` | — | [L209](../../dist/ml.js#L209) |
| Function | `mlOptimizer.fmtRow(r)` | — | [L210](../../dist/ml.js#L210) |
| Function | `mlOptimizer.<callback: Array.from>(_, i)` | — | [L212](../../dist/ml.js#L212) |
| Function | `mlOptimizer.<callback: loads.map>(lam)` | — | [L213](../../dist/ml.js#L213) |
| Function | `mlOptimizer.<callback: ML_SERVICES.map>(name, i)` | — | [L216](../../dist/ml.js#L216) |
| Function | `mlOptimizer.<callback: ML_SERVICES.map>.<callback: sweep.map>(c, j)` | — | [L216](../../dist/ml.js#L216) |
| Function | `mlOptimizer.<callback: [1000, 2500, 5000, 7500, 10000].map>(l)` | — | [L217](../../dist/ml.js#L217) |
| Function | `mlOptimizer.<callback: ML_SERVICES.map>(s, i)` | — | [L230](../../dist/ml.js#L230) |
| Function | `mlOptimizer.<callback: [["latency", best.parts.lat], ["cost", best.parts.cost], ["risk", best.parts.risk], ["switching", best.parts.sw]].map>([k, v])` | — | [L235](../../dist/ml.js#L235) |
| Function | `mlOptimizer.<callback: extremes.filter>(r)` | — | [L237](../../dist/ml.js#L237) |
| Function | `mlEnumerateTiming(n, seed = n)` | — | [L248](../../dist/ml.js#L248) |
| Function | `mlEnumerateTiming.u(lo, hi)` | — | [L249](../../dist/ml.js#L249) |
| Function | `mlEnumerateTiming.<callback: lm.map>(_, i)` | — | [L252](../../dist/ml.js#L252) |
| Function | `mlEnumerateTiming.<callback: ln.map>(x, i)` | — | [L253](../../dist/ml.js#L253) |
| Function | `mlEnumerateTiming.<callback: kp.map>(x, i)` | — | [L253](../../dist/ml.js#L253) |
| Function | `mlEnumerateTiming.<callback: pr.map>(x, i)` | — | [L253](../../dist/ml.js#L253) |
| Function | `mlEnumerateTiming.<callback: A[0].reduce>(s, x)` | — | [L254](../../dist/ml.js#L254) |
| Function | `mlEnumerateTiming.<callback: A[1].reduce>(s, x)` | — | [L254](../../dist/ml.js#L254) |
| Function | `mlEnumerateTiming.<callback: A[2].reduce>(s, x)` | — | [L254](../../dist/ml.js#L254) |
| Function | `mlEnumerateTiming.<callback: A[3].reduce>(s, x)` | — | [L254](../../dist/ml.js#L254) |
| Function | `mlEnumerateTiming.<callback: bestK.toString(2).split("").filter>(x)` | — | [L262](../../dist/ml.js#L262) |
| Function | `mlSolvers()` | — | [L265](../../dist/ml.js#L265) |
| Function | `mlSolvers.<callback: ML_TIMING.filter>(r)` | — | [L267](../../dist/ml.js#L267) |
| Function | `mlSolvers.<callback: ML_TIMING.filter((r) => r[1] != null).map>(r)` | — | [L267](../../dist/ml.js#L267) |
| Function | `mlSolvers.<callback: ML_TIMING.map>(r)` | — | [L268](../../dist/ml.js#L268) |
| Function | `mlSolvers.<callback: ML_TIMING.map>(r)` | — | [L269](../../dist/ml.js#L269) |
| Function | `mlSolvers.<callback: ML_TIMING.map>(r)` | — | [L281](../../dist/ml.js#L281) |
| Function | `mlSolvers.<callback: [6, 10, 14, 18, 20].map>(n)` | — | [L284](../../dist/ml.js#L284) |
| Function | `mlSolvers.<callback: ml.enum.map>(e)` | — | [L286](../../dist/ml.js#L286) |
| Function | `mlTrace(days, seed = 2026)` | — | [L291](../../dist/ml.js#L291) |
| Function | `mlTrainForecaster(optimiser, lr, { lags = 30, days = 21, maxEpochs = 120, patience = 10 } = {})` | — | [L306](../../dist/ml.js#L306) |
| Function | `mlTrainForecaster.<callback: Array.from>(x)` | — | [L308](../../dist/ml.js#L308) |
| Function | `mlTrainForecaster.<callback: y.map>(x)` | — | [L311](../../dist/ml.js#L311) |
| Function | `mlTrainForecaster.<callback: idx.filter>(t)` | — | [L313](../../dist/ml.js#L313) |
| Function | `mlTrainForecaster.<callback: idx.filter>(t)` | — | [L313](../../dist/ml.js#L313) |
| Function | `mlTrainForecaster.<callback: idx.filter>(t)` | — | [L313](../../dist/ml.js#L313) |
| Function | `mlTrainForecaster.predict(w, t)` | — | [L314](../../dist/ml.js#L314) |
| Function | `mlTrainForecaster.mse(w, set)` | — | [L315](../../dist/ml.js#L315) |
| Function | `mlTrainForecaster.mse.<callback: set.reduce>(s, t)` | — | [L315](../../dist/ml.js#L315) |
| Function | `mlTrainForecaster.back(x)` | — | [L335](../../dist/ml.js#L335) |
| Function | `mlTrainForecaster.mae(fn)` | — | [L337](../../dist/ml.js#L337) |
| Function | `mlTrainForecaster.mae.<callback: te.reduce>(s, t)` | — | [L337](../../dist/ml.js#L337) |
| Function | `mlTrainForecaster.<callback: te.slice(-1440).filter>(_, i)` | — | [L338](../../dist/ml.js#L338) |
| Function | `mlTrainForecaster.<callback: mae>(t)` | — | [L341](../../dist/ml.js#L341) |
| Function | `mlTrainForecaster.<callback: mae>(t)` | — | [L341](../../dist/ml.js#L341) |
| Function | `mlTrainForecaster.<callback: mae>(t)` | — | [L341](../../dist/ml.js#L341) |
| Function | `mlTrainForecaster.<callback: day.map>(t)` | — | [L342](../../dist/ml.js#L342) |
| Function | `mlForecasting()` | — | [L346](../../dist/ml.js#L346) |
| Function | `mlForecasting.<callback: fc.gd.curve.filter>(p)` | — | [L357](../../dist/ml.js#L357) |
| Function | `mlForecasting.<callback: fc.adam.curve.filter>(p)` | — | [L357](../../dist/ml.js#L357) |
| Function | `mlForecasting.<callback: [{ points: fc.gd.curve.filter((p) => p[1] < 5), cls: "s1" }, { points: fc.adam.curve.filter((p) => p[1] < 5), cls: "s3" }].filter>(x)` | — | [L357](../../dist/ml.js#L357) |
| Function | `mlForecasting.<callback: [["gradient descent", fc.gd], ["Adam", fc.adam]].map>([name, r])` | — | [L359](../../dist/ml.js#L359) |
| Function | `mlForecasting.<callback: fc.adam.day.map>(p)` | — | [L362](../../dist/ml.js#L362) |
| Function | `mlForecasting.<callback: fc.adam.day.map>(p)` | — | [L362](../../dist/ml.js#L362) |
| Function | `mlForecasting.<callback: [{ points: fc.adam.day.map((p) => [p[0], p[1]]), cls: "s0" }, { points: fc.adam.day.map((p) => [p[0], p[2]]), cls: "s3" }].filter>()` | — | [L362](../../dist/ml.js#L362) |
| Function | `mlDrivers(subtle = false, seed = 11)` | — | [L372](../../dist/ml.js#L372) |
| Function | `mlC(n)` | — | [L379](../../dist/ml.js#L379) |
| Function | `mlTree(points, depth, maxDepth, g)` | — | [L381](../../dist/ml.js#L381) |
| Function | `mlTree.<callback: points.map>(p)` | — | [L383](../../dist/ml.js#L383) |
| Function | `mlTree.<callback: points.filter>(p)` | — | [L386](../../dist/ml.js#L386) |
| Function | `mlTree.<callback: points.filter>(p)` | — | [L386](../../dist/ml.js#L386) |
| Function | `mlPath(node, x, depth = 0)` | — | [L389](../../dist/ml.js#L389) |
| Function | `mlForestGrow(nTrees, subtle = false)` | — | [L392](../../dist/ml.js#L392) |
| Function | `mlForestGrow.score(x)` | — | [L399](../../dist/ml.js#L399) |
| Function | `mlForestGrow.score.<callback: trees.reduce>(s, tr)` | — | [L399](../../dist/ml.js#L399) |
| Function | `mlForestGrow.<callback: data.train.map(score).sort>(a, b)` | — | [L400](../../dist/ml.js#L400) |
| Function | `mlForestGrow.<callback: data.test.map>(x)` | — | [L402](../../dist/ml.js#L402) |
| Function | `mlForestGrow.<callback: data.odd.map>(x)` | — | [L402](../../dist/ml.js#L402) |
| Function | `mlForestGrow.<callback: pts.filter>(p)` | — | [L403](../../dist/ml.js#L403) |
| Function | `mlForestGrow.<callback: pts.filter>(p)` | — | [L403](../../dist/ml.js#L403) |
| Function | `mlForestGrow.<callback: pts.filter>(p)` | — | [L405](../../dist/ml.js#L405) |
| Function | `mlForestGrow.depthOf(x)` | — | [L406](../../dist/ml.js#L406) |
| Function | `mlForestGrow.depthOf.<callback: trees.reduce>(s, tr)` | — | [L406](../../dist/ml.js#L406) |
| Function | `mlForestGrow.<callback: flagged.filter>(p)` | — | [L407](../../dist/ml.js#L407) |
| Function | `mlForestGrow.<callback: flagged.filter>(p)` | — | [L407](../../dist/ml.js#L407) |
| Function | `mlForestGrow.<callback: flagged.filter>(p)` | — | [L407](../../dist/ml.js#L407) |
| Function | `mlAnomaly()` | — | [L410](../../dist/ml.js#L410) |
| Function | `mlAnomaly.<callback: () => {
    const W = 560, H = 230, P = { l: 46, r: 12, t: 10, b: 30 }, sx = (v) => P.l + (v / 36) * (W - P.l - P.r), sy = (v) => H - P.b - (v / 210) * (H - P.t - P.b);
    return `<svg class="ml-chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="Driver telemetry coloured by anomaly score">
      ${[0, 50, 100, 150, 200].map((v) => `<line class="grid" x1="${P.l}" x2="${W - P.r}" y1="${sy(v)}" y2="${sy(v)}"/><text class="tick" x="${P.l - 6}" y="${sy(v) + 3}" text-anchor="end">${v}</text>`).join("")}
      ${[0, 10, 20, 30].map((v) => `<text class="tick" x="${sx(v)}" y="${H - P.b + 13}" text-anchor="middle">${v}</text>`).join("")}
      <text class="axis" x="${(W + P.l) / 2}" y="${H - 3}" text-anchor="middle">distance to pickup (km)</text><text class="axis" x="10" y="${(H - P.b) / 2}" transform="rotate(-90 10 ${(H - P.b) / 2})" text-anchor="middle">speed (km/h)</text>
      ${F.pts.map((p) => `<circle cx="${sx(p.x[0]).toFixed(1)}" cy="${sy(p.x[1]).toFixed(1)}" r="${p.y ? 3.4 : 2.6}" class="${p.s > F.threshold ? "flag" : "ok"}${p.y ? " odd" : ""}" style="opacity:${(0.35 + 0.65 * Math.min(1, Math.max(0, (p.s - 0.35) / 0.4))).toFixed(2)}"><title>${p.x[0].toFixed(1)} km, ${p.x[1].toFixed(0)} km/h: score ${p.s.toFixed(3)}</title></circle>`).join("")}
    </svg>`;
  }>()` | — | [L412](../../dist/ml.js#L412) |
| Function | `mlAnomaly.<callback: () => {
    const W = 560, H = 230, P = { l: 46, r: 12, t: 10, b: 30 }, sx = (v) => P.l + (v / 36) * (W - P.l - P.r), sy = (v) => H - P.b - (v / 210) * (H - P.t - P.b);
    return `<svg class="ml-chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="Driver telemetry coloured by anomaly score">
      ${[0, 50, 100, 150, 200].map((v) => `<line class="grid" x1="${P.l}" x2="${W - P.r}" y1="${sy(v)}" y2="${sy(v)}"/><text class="tick" x="${P.l - 6}" y="${sy(v) + 3}" text-anchor="end">${v}</text>`).join("")}
      ${[0, 10, 20, 30].map((v) => `<text class="tick" x="${sx(v)}" y="${H - P.b + 13}" text-anchor="middle">${v}</text>`).join("")}
      <text class="axis" x="${(W + P.l) / 2}" y="${H - 3}" text-anchor="middle">distance to pickup (km)</text><text class="axis" x="10" y="${(H - P.b) / 2}" transform="rotate(-90 10 ${(H - P.b) / 2})" text-anchor="middle">speed (km/h)</text>
      ${F.pts.map((p) => `<circle cx="${sx(p.x[0]).toFixed(1)}" cy="${sy(p.x[1]).toFixed(1)}" r="${p.y ? 3.4 : 2.6}" class="${p.s > F.threshold ? "flag" : "ok"}${p.y ? " odd" : ""}" style="opacity:${(0.35 + 0.65 * Math.min(1, Math.max(0, (p.s - 0.35) / 0.4))).toFixed(2)}"><title>${p.x[0].toFixed(1)} km, ${p.x[1].toFixed(0)} km/h: score ${p.s.toFixed(3)}</title></circle>`).join("")}
    </svg>`;
  }>.sx(v)` | — | [L413](../../dist/ml.js#L413) |
| Function | `mlAnomaly.<callback: () => {
    const W = 560, H = 230, P = { l: 46, r: 12, t: 10, b: 30 }, sx = (v) => P.l + (v / 36) * (W - P.l - P.r), sy = (v) => H - P.b - (v / 210) * (H - P.t - P.b);
    return `<svg class="ml-chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="Driver telemetry coloured by anomaly score">
      ${[0, 50, 100, 150, 200].map((v) => `<line class="grid" x1="${P.l}" x2="${W - P.r}" y1="${sy(v)}" y2="${sy(v)}"/><text class="tick" x="${P.l - 6}" y="${sy(v) + 3}" text-anchor="end">${v}</text>`).join("")}
      ${[0, 10, 20, 30].map((v) => `<text class="tick" x="${sx(v)}" y="${H - P.b + 13}" text-anchor="middle">${v}</text>`).join("")}
      <text class="axis" x="${(W + P.l) / 2}" y="${H - 3}" text-anchor="middle">distance to pickup (km)</text><text class="axis" x="10" y="${(H - P.b) / 2}" transform="rotate(-90 10 ${(H - P.b) / 2})" text-anchor="middle">speed (km/h)</text>
      ${F.pts.map((p) => `<circle cx="${sx(p.x[0]).toFixed(1)}" cy="${sy(p.x[1]).toFixed(1)}" r="${p.y ? 3.4 : 2.6}" class="${p.s > F.threshold ? "flag" : "ok"}${p.y ? " odd" : ""}" style="opacity:${(0.35 + 0.65 * Math.min(1, Math.max(0, (p.s - 0.35) / 0.4))).toFixed(2)}"><title>${p.x[0].toFixed(1)} km, ${p.x[1].toFixed(0)} km/h: score ${p.s.toFixed(3)}</title></circle>`).join("")}
    </svg>`;
  }>.sy(v)` | — | [L413](../../dist/ml.js#L413) |
| Function | `mlAnomaly.<callback: () => {
    const W = 560, H = 230, P = { l: 46, r: 12, t: 10, b: 30 }, sx = (v) => P.l + (v / 36) * (W - P.l - P.r), sy = (v) => H - P.b - (v / 210) * (H - P.t - P.b);
    return `<svg class="ml-chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="Driver telemetry coloured by anomaly score">
      ${[0, 50, 100, 150, 200].map((v) => `<line class="grid" x1="${P.l}" x2="${W - P.r}" y1="${sy(v)}" y2="${sy(v)}"/><text class="tick" x="${P.l - 6}" y="${sy(v) + 3}" text-anchor="end">${v}</text>`).join("")}
      ${[0, 10, 20, 30].map((v) => `<text class="tick" x="${sx(v)}" y="${H - P.b + 13}" text-anchor="middle">${v}</text>`).join("")}
      <text class="axis" x="${(W + P.l) / 2}" y="${H - 3}" text-anchor="middle">distance to pickup (km)</text><text class="axis" x="10" y="${(H - P.b) / 2}" transform="rotate(-90 10 ${(H - P.b) / 2})" text-anchor="middle">speed (km/h)</text>
      ${F.pts.map((p) => `<circle cx="${sx(p.x[0]).toFixed(1)}" cy="${sy(p.x[1]).toFixed(1)}" r="${p.y ? 3.4 : 2.6}" class="${p.s > F.threshold ? "flag" : "ok"}${p.y ? " odd" : ""}" style="opacity:${(0.35 + 0.65 * Math.min(1, Math.max(0, (p.s - 0.35) / 0.4))).toFixed(2)}"><title>${p.x[0].toFixed(1)} km, ${p.x[1].toFixed(0)} km/h: score ${p.s.toFixed(3)}</title></circle>`).join("")}
    </svg>`;
  }>.<callback: [0, 50, 100, 150, 200].map>(v)` | — | [L415](../../dist/ml.js#L415) |
| Function | `mlAnomaly.<callback: () => {
    const W = 560, H = 230, P = { l: 46, r: 12, t: 10, b: 30 }, sx = (v) => P.l + (v / 36) * (W - P.l - P.r), sy = (v) => H - P.b - (v / 210) * (H - P.t - P.b);
    return `<svg class="ml-chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="Driver telemetry coloured by anomaly score">
      ${[0, 50, 100, 150, 200].map((v) => `<line class="grid" x1="${P.l}" x2="${W - P.r}" y1="${sy(v)}" y2="${sy(v)}"/><text class="tick" x="${P.l - 6}" y="${sy(v) + 3}" text-anchor="end">${v}</text>`).join("")}
      ${[0, 10, 20, 30].map((v) => `<text class="tick" x="${sx(v)}" y="${H - P.b + 13}" text-anchor="middle">${v}</text>`).join("")}
      <text class="axis" x="${(W + P.l) / 2}" y="${H - 3}" text-anchor="middle">distance to pickup (km)</text><text class="axis" x="10" y="${(H - P.b) / 2}" transform="rotate(-90 10 ${(H - P.b) / 2})" text-anchor="middle">speed (km/h)</text>
      ${F.pts.map((p) => `<circle cx="${sx(p.x[0]).toFixed(1)}" cy="${sy(p.x[1]).toFixed(1)}" r="${p.y ? 3.4 : 2.6}" class="${p.s > F.threshold ? "flag" : "ok"}${p.y ? " odd" : ""}" style="opacity:${(0.35 + 0.65 * Math.min(1, Math.max(0, (p.s - 0.35) / 0.4))).toFixed(2)}"><title>${p.x[0].toFixed(1)} km, ${p.x[1].toFixed(0)} km/h: score ${p.s.toFixed(3)}</title></circle>`).join("")}
    </svg>`;
  }>.<callback: [0, 10, 20, 30].map>(v)` | — | [L416](../../dist/ml.js#L416) |
| Function | `mlAnomaly.<callback: () => {
    const W = 560, H = 230, P = { l: 46, r: 12, t: 10, b: 30 }, sx = (v) => P.l + (v / 36) * (W - P.l - P.r), sy = (v) => H - P.b - (v / 210) * (H - P.t - P.b);
    return `<svg class="ml-chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="Driver telemetry coloured by anomaly score">
      ${[0, 50, 100, 150, 200].map((v) => `<line class="grid" x1="${P.l}" x2="${W - P.r}" y1="${sy(v)}" y2="${sy(v)}"/><text class="tick" x="${P.l - 6}" y="${sy(v) + 3}" text-anchor="end">${v}</text>`).join("")}
      ${[0, 10, 20, 30].map((v) => `<text class="tick" x="${sx(v)}" y="${H - P.b + 13}" text-anchor="middle">${v}</text>`).join("")}
      <text class="axis" x="${(W + P.l) / 2}" y="${H - 3}" text-anchor="middle">distance to pickup (km)</text><text class="axis" x="10" y="${(H - P.b) / 2}" transform="rotate(-90 10 ${(H - P.b) / 2})" text-anchor="middle">speed (km/h)</text>
      ${F.pts.map((p) => `<circle cx="${sx(p.x[0]).toFixed(1)}" cy="${sy(p.x[1]).toFixed(1)}" r="${p.y ? 3.4 : 2.6}" class="${p.s > F.threshold ? "flag" : "ok"}${p.y ? " odd" : ""}" style="opacity:${(0.35 + 0.65 * Math.min(1, Math.max(0, (p.s - 0.35) / 0.4))).toFixed(2)}"><title>${p.x[0].toFixed(1)} km, ${p.x[1].toFixed(0)} km/h: score ${p.s.toFixed(3)}</title></circle>`).join("")}
    </svg>`;
  }>.<callback: F.pts.map>(p)` | — | [L418](../../dist/ml.js#L418) |
| Function | `mlFeatures(c)` | — | [L441](../../dist/ml.js#L441) |
| Function | `mlScore(c, w)` | — | [L442](../../dist/ml.js#L442) |
| Function | `mlScore.<callback: mlFeatures(c).reduce>(s, f, i)` | — | [L442](../../dist/ml.js#L442) |
| Function | `mlExpectedCost(c)` | — | [L443](../../dist/ml.js#L443) |
| Function | `mlCandidates(g)` | — | [L449](../../dist/ml.js#L449) |
| Function | `mlCandidates.<callback: Array.from>()` | — | [L449](../../dist/ml.js#L449) |
| Function | `mlSoftmax(scores)` | — | [L450](../../dist/ml.js#L450) |
| Function | `mlSoftmax.<callback: scores.map>(s)` | — | [L450](../../dist/ml.js#L450) |
| Function | `mlSoftmax.<callback: ex.reduce>(a, b)` | — | [L450](../../dist/ml.js#L450) |
| Function | `mlSoftmax.<callback: ex.map>(e)` | — | [L450](../../dist/ml.js#L450) |
| Function | `mlRlNew()` | — | [L452](../../dist/ml.js#L452) |
| Function | `mlRlNew.<callback: Array.from>()` | — | [L453](../../dist/ml.js#L453) |
| Function | `mlRlNew.evalPolicy(w, greedy)` | — | [L454](../../dist/ml.js#L454) |
| Function | `mlRlNew.evalPolicy.<callback: test.reduce>(s, cs)` | — | [L454](../../dist/ml.js#L454) |
| Function | `mlRlNew.evalPolicy.<callback: test.reduce>.<callback: cs.map>(c)` | — | [L454](../../dist/ml.js#L454) |
| Function | `mlRlNew.evalPolicy.<callback: test.reduce>.<callback: cs.reduce>(t, c, i)` | — | [L454](../../dist/ml.js#L454) |
| Function | `mlRlNew.<callback: test.reduce>(s, cs)` | — | [L455](../../dist/ml.js#L455) |
| Function | `mlRlNew.<callback: test.reduce>.<callback: cs.reduce>(b, c)` | — | [L455](../../dist/ml.js#L455) |
| Function | `mlRlTrain(state, episodes, lr = 0.004)` | — | [L460](../../dist/ml.js#L460) |
| Function | `mlRlTrain.<callback: phi.map>(f)` | — | [L464](../../dist/ml.js#L464) |
| Function | `mlRlTrain.<callback: phi.map>.<callback: f.reduce>(s, x, i)` | — | [L464](../../dist/ml.js#L464) |
| Function | `mlRlTrain.<callback: [0, 1, 2, 3].map>(k)` | — | [L469](../../dist/ml.js#L469) |
| Function | `mlRlTrain.<callback: [0, 1, 2, 3].map>.<callback: p.reduce>(s, pi, i)` | — | [L469](../../dist/ml.js#L469) |
| Function | `mlRl()` | — | [L477](../../dist/ml.js#L477) |
| Function | `mlRl.<callback: ML_POOL.map>([name, zone, eta, accept, surge, last])` | — | [L480](../../dist/ml.js#L480) |
| Function | `mlRl.<callback: pool.map>(c)` | — | [L481](../../dist/ml.js#L481) |
| Function | `mlRl.<callback: pool.map>(c)` | — | [L481](../../dist/ml.js#L481) |
| Function | `mlRl.<callback: S.w.map>(x)` | — | [L491](../../dist/ml.js#L491) |
| Function | `mlRl.<callback: pool.map>(c, i)` | — | [L496](../../dist/ml.js#L496) |
| Function | `mlRl.<callback: Object.entries(ML_COURIER).sort>(a, b)` | — | [L499](../../dist/ml.js#L499) |
| Function | `mlRl.<callback: Object.entries(ML_COURIER).sort((a, b) => a[0] - b[0]).map>([s, d])` | — | [L499](../../dist/ml.js#L499) |
| Function | `mlEvaluation()` | — | [L512](../../dist/ml.js#L512) |
| Function | `mlEvaluation.<callback: ML_ABLATION.map>([n, p99, sla, cost, tr], i)` | — | [L520](../../dist/ml.js#L520) |
| Function | `mlGaps()` | — | [L532](../../dist/ml.js#L532) |
| Function | `mlInspector()` | — | [L564](../../dist/ml.js#L564) |
| Function | `mlInspector.<callback: info.facts.map>([k, v])` | — | [L569](../../dist/ml.js#L569) |
| Function | `mlInspector.<callback: info.files.map>([l, u])` | — | [L570](../../dist/ml.js#L570) |
| Function | `mlInspector.<callback: info.questions.map>(q)` | — | [L572](../../dist/ml.js#L572) |
| Function | `mlView()` | — | [L579](../../dist/ml.js#L579) |
| Function | `mlView.<callback: mlTopics.map>(x)` | — | [L582](../../dist/ml.js#L582) |
| Function | `mlOpen(topic)` | — | [L586](../../dist/ml.js#L586) |
| Function | `mlSetHash()` | — | [L591](../../dist/ml.js#L591) |
| Function | `mlRun(busy, task)` | — | [L595](../../dist/ml.js#L595) |
| Function | `mlRun.<callback: setTimeout>()` | — | [L598](../../dist/ml.js#L598) |
| Function | `mlClick(button)` | — | [L605](../../dist/ml.js#L605) |
| Function | `mlClick.<callback: mlRun, "enum">()` | — | [L622](../../dist/ml.js#L622) |
| Function | `mlClick.<callback: mlRun, "enum">.<callback: ml.enum.filter>(e)` | — | [L622](../../dist/ml.js#L622) |
| Function | `mlClick.<callback: mlRun, "enum">.<callback: ml.enum.filter((e) => e.n !== n).concat(mlEnumerateTiming(n)).sort>(x, y)` | — | [L622](../../dist/ml.js#L622) |
| Function | `mlClick.<callback: mlRun, "fc">()` | — | [L623](../../dist/ml.js#L623) |
| Function | `mlClick.<callback: mlRun, "forest">()` | — | [L624](../../dist/ml.js#L624) |
| Function | `mlClick.<callback: mlRun, "rl">()` | — | [L626](../../dist/ml.js#L626) |
| Function | `<callback: document.addEventListener, "input">(event)` | — | [L631](../../dist/ml.js#L631) |
| Function | `<callback: document.addEventListener, "change">(event)` | — | [L638](../../dist/ml.js#L638) |

### `dist/security.js`

[Open source](../../dist/security.js)

| Kind | Signature | Decorators | Source |
| --- | --- | --- | --- |
| Function | `<callback: secTopics.map>(t)` | — | [L42](../../dist/security.js#L42) |
| Function | `secHex(buf)` | — | [L58](../../dist/security.js#L58) |
| Function | `secHex.<callback: [...new Uint8Array(buf)].map>(b)` | — | [L58](../../dist/security.js#L58) |
| Function | `secRand(n)` | — | [L59](../../dist/security.js#L59) |
| Function | `secShort(h, n = 24)` | — | [L60](../../dist/security.js#L60) |
| Function | `secB64u(bytes)` | — | [L61](../../dist/security.js#L61) |
| Function | `secFromB64u(text)` | — | [L62](../../dist/security.js#L62) |
| Function | `secFromB64u.<callback: Uint8Array.from>(c)` | — | [L62](../../dist/security.js#L62) |
| Function | `secEsc(text)` | — | [L63](../../dist/security.js#L63) |
| Function | `secEsc.<callback: String(text).replace, /[&<>"']/g>(c)` | — | [L63](../../dist/security.js#L63) |
| Function | `secClock(ms)` | — | [L64](../../dist/security.js#L64) |
| Function | `async secPbkdf2(password, salt, iterations, hash = "SHA-256", bits = 256)` | — | [L66](../../dist/security.js#L66) |
| Function | `async secSha256(bytes)` | — | [L71](../../dist/security.js#L71) |
| Function | `secEqual(a, b)` | — | [L75](../../dist/security.js#L75) |
| Function | `async secSeal(keyBytes, object)` | — | [L82](../../dist/security.js#L82) |
| Function | `async secOpen(keyBytes, sealed)` | — | [L91](../../dist/security.js#L91) |
| Function | `async secFingerprint(bytes)` | — | [L97](../../dist/security.js#L97) |
| Function | `secChip(status)` | — | [L100](../../dist/security.js#L100) |
| Function | `secCode(text)` | — | [L106](../../dist/security.js#L106) |
| Function | `secCheck(ok, text, detail = "")` | — | [L108](../../dist/security.js#L108) |
| Function | `secField(name, label, type = "text", hint = "")` | — | [L112](../../dist/security.js#L112) |
| Function | `secButton(action, label, { primary = false, iconName = "", disabled = false } = {})` | — | [L116](../../dist/security.js#L116) |
| Function | `secSelect(name, options, value)` | — | [L120](../../dist/security.js#L120) |
| Function | `secSelect.<callback: options.map>([v, l])` | — | [L121](../../dist/security.js#L121) |
| Function | `secTable(head, rows, cls = "")` | — | [L124](../../dist/security.js#L124) |
| Function | `secTable.<callback: head.map>(h)` | — | [L125](../../dist/security.js#L125) |
| Function | `secTable.<callback: rows.map>(r)` | — | [L125](../../dist/security.js#L125) |
| Function | `secTable.<callback: rows.map>.<callback: r.map>(c, i)` | — | [L125](../../dist/security.js#L125) |
| Function | `secLink(label, url)` | — | [L128](../../dist/security.js#L128) |
| Function | `secSection(kicker, title, body)` | — | [L130](../../dist/security.js#L130) |
| Function | `umlData()` | — | [L136](../../dist/security.js#L136) |
| Function | `umlHref(anchor)` | — | [L137](../../dist/security.js#L137) |
| Function | `umlChip(anchor, label = "UML catalogue")` | — | [L139](../../dist/security.js#L139) |
| Function | `umlSection(topicKey)` | — | [L144](../../dist/security.js#L144) |
| Function | `umlSection.<callback: ids.map>(id)` | — | [L149](../../dist/security.js#L149) |
| Function | `umlCatalogueName(view)` | — | [L157](../../dist/security.js#L157) |
| Function | `umlCatalogueAnchor(view)` | — | [L158](../../dist/security.js#L158) |
| Function | `umlTopicsSection(view, topics)` | — | [L161](../../dist/security.js#L161) |
| Function | `umlTopicsSection.<callback: topics.filter>(t)` | — | [L164](../../dist/security.js#L164) |
| Function | `umlTopicsSection.<callback: topics.filter((t) => data.topics[`${view}/${t.id}`]).map>(t)` | — | [L164](../../dist/security.js#L164) |
| Function | `umlInspector(topicKey, view, topics)` | — | [L169](../../dist/security.js#L169) |
| Function | `umlInspector.<callback: topics.filter>(t)` | — | [L173](../../dist/security.js#L173) |
| Function | `umlInspector.<callback: topics.filter((t) => data.topics[`${view}/${t.id}`]).map>(t)` | — | [L173](../../dist/security.js#L173) |
| Function | `umlInspector.<callback: ids.map>(id)` | — | [L176](../../dist/security.js#L176) |
| Function | `secOverview()` | — | [L192](../../dist/security.js#L192) |
| Function | `secOverview.<callback: Object.keys(secStatus).map>(k)` | — | [L194](../../dist/security.js#L194) |
| Function | `secOverview.<callback: secMap.map>([topic, ic, title, status, text, where])` | — | [L195](../../dist/security.js#L195) |
| Function | `async secPwHash(again = false)` | — | [L204](../../dist/security.js#L204) |
| Function | `async secPwVerify()` | — | [L223](../../dist/security.js#L223) |
| Function | `secPwVerify.<callback: Uint8Array.from>(h)` | — | [L226](../../dist/security.js#L226) |
| Function | `secPwVerify.<callback: Uint8Array.from>(h)` | — | [L229](../../dist/security.js#L229) |
| Function | `secPasswords()` | — | [L233](../../dist/security.js#L233) |
| Function | `async secLoginInit()` | — | [L259](../../dist/security.js#L259) |
| Function | `async secLoginAttempt(email, password)` | — | [L267](../../dist/security.js#L267) |
| Function | `secLogin()` | — | [L296](../../dist/security.js#L296) |
| Function | `secLogin.<callback: L.log.map>(e)` | — | [L305](../../dist/security.js#L305) |
| Function | `secLogin.<callback: L.log.map>.<callback: e.steps.map>([ok, t, d])` | — | [L305](../../dist/security.js#L305) |
| Function | `secIdentity()` | — | [L319](../../dist/security.js#L319) |
| Function | `secIdentity.<callback: stages.map>([t, c, d], i)` | — | [L330](../../dist/security.js#L330) |
| Function | `secGatewayRun(s)` | — | [L367](../../dist/security.js#L367) |
| Function | `secGatewayRun.<callback: secRoutes.find>([m, r, re])` | — | [L377](../../dist/security.js#L377) |
| Function | `secGatewayRun.<callback: Object.keys(secKeys).find>(k)` | — | [L380](../../dist/security.js#L380) |
| Function | `secGateway()` | — | [L396](../../dist/security.js#L396) |
| Function | `secGateway.<callback: Object.entries(s.headers).map>([k, v])` | — | [L400](../../dist/security.js#L400) |
| Function | `secGateway.<callback: Object.entries(secGatewayScenarios).map>([k, v])` | — | [L402](../../dist/security.js#L402) |
| Function | `secGateway.<callback: result.steps.slice(0, shown).map>([ok, t, d])` | — | [L404](../../dist/security.js#L404) |
| Function | `async secSsoNext()` | — | [L420](../../dist/security.js#L420) |
| Function | `secSsoNext.push(title, from, to, wire, checks, done = false)` | — | [L425](../../dist/security.js#L425) |
| Function | `secMessages(steps)` | — | [L476](../../dist/security.js#L476) |
| Function | `secMessages.<callback: steps.map>(m)` | — | [L477](../../dist/security.js#L477) |
| Function | `secMessages.<callback: steps.map>.<callback: m.checks.every>([ok])` | — | [L477](../../dist/security.js#L477) |
| Function | `secMessages.<callback: steps.map>.<callback: m.checks.map>([ok, t, d])` | — | [L477](../../dist/security.js#L477) |
| Function | `secSso()` | — | [L480](../../dist/security.js#L480) |
| Function | `async secKrbSetup()` | — | [L500](../../dist/security.js#L500) |
| Function | `async secKrbNext()` | — | [L510](../../dist/security.js#L510) |
| Function | `secKrbNext.kdcNow()` | — | [L515](../../dist/security.js#L515) |
| Function | `secKrbNext.appNow()` | — | [L516](../../dist/security.js#L516) |
| Function | `secKrbNext.push(title, from, to, wire, checks, done = false)` | — | [L517](../../dist/security.js#L517) |
| Function | `secKrbNext.skewOk(t)` | — | [L518](../../dist/security.js#L518) |
| Function | `secKrbNext.fail(title, from, to, wire, checks)` | — | [L519](../../dist/security.js#L519) |
| Function | `secKrbNext.<callback: Uint8Array.from>(h)` | — | [L547](../../dist/security.js#L547) |
| Function | `async secKrbVerifyAp(c, ticketBytes, authBytes)` | — | [L583](../../dist/security.js#L583) |
| Function | `secKrbVerifyAp.<callback: Uint8Array.from>(h)` | — | [L594](../../dist/security.js#L594) |
| Function | `secKrb()` | — | [L604](../../dist/security.js#L604) |
| Function | `secKrb.has(who, k)` | — | [L609](../../dist/security.js#L609) |
| Function | `secKrb.cell(ok)` | — | [L611](../../dist/security.js#L611) |
| Function | `secKrb.<callback: keyRows.map>([k, d])` | — | [L616](../../dist/security.js#L616) |
| Function | `secTransport()` | — | [L627](../../dist/security.js#L627) |
| Function | `secTransport.<callback: [
      ["Private CA", "openssl req -x509 … /CN=atlas-ca", "basicConstraints CA:TRUE, keyUsage keyCertSign, 30 days"],
      ["Server certificate", "extendedKeyUsage=serverAuth", "subjectAltName=IP:127.0.0.1 binds it to the address"],
      ["Client certificate", "extendedKeyUsage=clientAuth", "Cannot be reused as a server certificate"],
      ["Server requires a client cert", "verify_mode = ssl.CERT_REQUIRED", "No certificate from atlas-ca → handshake fails"],
      ["Client verifies the server", "create_default_context(cafile=ca.crt)", "Plus load_cert_chain to present its own identity"],
    ].map>([t, c, d], i)` | — | [L635](../../dist/security.js#L635) |
| Function | `secGaps()` | — | [L648](../../dist/security.js#L648) |
| Function | `securityInspector()` | — | [L686](../../dist/security.js#L686) |
| Function | `securityInspector.<callback: info.facts.map>([k, v])` | — | [L692](../../dist/security.js#L692) |
| Function | `securityInspector.<callback: info.files.map>([l, u])` | — | [L693](../../dist/security.js#L693) |
| Function | `securityInspector.<callback: info.questions.map>(q)` | — | [L695](../../dist/security.js#L695) |
| Function | `securityView()` | — | [L702](../../dist/security.js#L702) |
| Function | `securityView.<callback: secTopics.map>(x)` | — | [L708](../../dist/security.js#L708) |
| Function | `securityOpen(topic)` | — | [L712](../../dist/security.js#L712) |
| Function | `secSetHash()` | — | [L717](../../dist/security.js#L717) |
| Function | `async secRun(busy, task)` | — | [L721](../../dist/security.js#L721) |
| Function | `securityClick(button)` | — | [L729](../../dist/security.js#L729) |
| Function | `securityClick."pw-hash"()` | — | [L741](../../dist/security.js#L741) |
| Function | `securityClick."pw-hash".<callback: secRun, "pw">()` | — | [L741](../../dist/security.js#L741) |
| Function | `securityClick."pw-again"()` | — | [L742](../../dist/security.js#L742) |
| Function | `securityClick."pw-again".<callback: secRun, "pw">()` | — | [L742](../../dist/security.js#L742) |
| Function | `securityClick."pw-verify"()` | — | [L743](../../dist/security.js#L743) |
| Function | `securityClick."login-init"()` | — | [L744](../../dist/security.js#L744) |
| Function | `securityClick."login-wrong"()` | — | [L745](../../dist/security.js#L745) |
| Function | `securityClick."login-wrong".<callback: secRun, "login">()` | — | [L745](../../dist/security.js#L745) |
| Function | `securityClick."login-unknown"()` | — | [L746](../../dist/security.js#L746) |
| Function | `securityClick."login-unknown".<callback: secRun, "login">()` | — | [L746](../../dist/security.js#L746) |
| Function | `securityClick."login-right"()` | — | [L747](../../dist/security.js#L747) |
| Function | `securityClick."login-right".<callback: secRun, "login">()` | — | [L747](../../dist/security.js#L747) |
| Function | `securityClick."login-tick"()` | — | [L748](../../dist/security.js#L748) |
| Function | `securityClick."login-reset"()` | — | [L749](../../dist/security.js#L749) |
| Function | `securityClick."gw-step"()` | — | [L750](../../dist/security.js#L750) |
| Function | `securityClick."gw-all"()` | — | [L751](../../dist/security.js#L751) |
| Function | `securityClick."sso-next"()` | — | [L752](../../dist/security.js#L752) |
| Function | `securityClick."sso-reset"()` | — | [L753](../../dist/security.js#L753) |
| Function | `securityClick."krb-next"()` | — | [L754](../../dist/security.js#L754) |
| Function | `securityClick."krb-all"()` | — | [L755](../../dist/security.js#L755) |
| Function | `async securityClick."krb-all".<callback: secRun, "krb">()` | — | [L755](../../dist/security.js#L755) |
| Function | `securityClick."krb-reset"()` | — | [L756](../../dist/security.js#L756) |
| Function | `<callback: document.addEventListener, "input">(event)` | — | [L762](../../dist/security.js#L762) |
| Function | `<callback: document.addEventListener, "change">(event)` | — | [L767](../../dist/security.js#L767) |

### `dist/uml-catalog.js`

[Open source](../../dist/uml-catalog.js)

This file declares no functions.

### `server.mjs`

[Open source](../../server.mjs)

| Kind | Signature | Decorators | Source |
| --- | --- | --- | --- |
| Function | `async <callback: Object.entries(contentTypes).map>([file, type])` | — | [L27](../../server.mjs#L27) |
| Function | `reply(request, response, status, type, body, headers = {})` | — | [L41](../../server.mjs#L41) |
| Function | `<callback: createServer>(request, response)` | — | [L51](../../server.mjs#L51) |
| Function | `<callback: createServer((request, response) => {
  if (request.method !== "GET" && request.method !== "HEAD") {
    return reply(request, response, 405, textType, "Method not allowed\n", { Allow: "GET, HEAD" });
  }

  const path = request.url.split("?", 1)[0];
  if (path === "/healthz") {
    return reply(request, response, 200, textType, "ok\n");
  }

  const asset = assets.get(path === "/" ? "/index.html" : path);
  if (!asset) {
    return reply(request, response, 404, textType, "Not found\n");
  }

  reply(request, response, 200, asset.type, asset.body);
}).listen>()` | — | [L67](../../server.mjs#L67) |

### `starter/scripts/generate_blueprint.py`

[Open source](../../starter/scripts/generate_blueprint.py)

| Kind | Signature | Decorators | Source |
| --- | --- | --- | --- |
| Function | `attr(node)` | — | [L20](../../starter/scripts/generate_blueprint.py#L20) |
| Function | `instance_attrs(node)` | — | [L29](../../starter/scripts/generate_blueprint.py#L29) |
| Function | `python_inventory(source)` | — | [L47](../../starter/scripts/generate_blueprint.py#L47) |
| Function | `python_inventory.walk(node, owner='', parent_class=None)` | — | [L51](../../starter/scripts/generate_blueprint.py#L51) |
| Function | `javascript_inventory(path)` | — | [L92](../../starter/scripts/generate_blueprint.py#L92) |
| Function | `javascript_inventory.segment(node)` | — | [L101](../../starter/scripts/generate_blueprint.py#L101) |
| Function | `javascript_inventory.callable_name(node, parent)` | — | [L104](../../starter/scripts/generate_blueprint.py#L104) |
| Function | `javascript_inventory.walk(node, owner='', parent=None, parent_class=None)` | — | [L121](../../starter/scripts/generate_blueprint.py#L121) |
| Function | `shell_inventory(source)` | — | [L161](../../starter/scripts/generate_blueprint.py#L161) |
| Function | `files(root)` | — | [L170](../../starter/scripts/generate_blueprint.py#L170) |
| Function | `folder_tree(paths, root_name)` | — | [L182](../../starter/scripts/generate_blueprint.py#L182) |
| Function | `folder_tree.visit(directory, prefix)` | — | [L192](../../starter/scripts/generate_blueprint.py#L192) |
| Function | `folder_tree.visit.<lambda@193:49>(item)` | — | [L193](../../starter/scripts/generate_blueprint.py#L193) |
| Function | `inventory(root, paths)` | — | [L204](../../starter/scripts/generate_blueprint.py#L204) |
| Function | `blueprint()` | — | [L220](../../starter/scripts/generate_blueprint.py#L220) |
| Function | `code(value)` | — | [L241](../../starter/scripts/generate_blueprint.py#L241) |
| Function | `symbol_rows(symbols, link, kind)` | — | [L245](../../starter/scripts/generate_blueprint.py#L245) |
| Function | `catalog_text(modules, relative)` | — | [L252](../../starter/scripts/generate_blueprint.py#L252) |
| Function | `replace_block(document, name, content)` | — | [L280](../../starter/scripts/generate_blueprint.py#L280) |
| Function | `main()` | — | [L289](../../starter/scripts/generate_blueprint.py#L289) |

<!-- END GENERATED SUPPORT -->
