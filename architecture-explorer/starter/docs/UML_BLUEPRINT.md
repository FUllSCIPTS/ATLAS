# ATLAS ride-hailing UML blueprint

Use this blueprint to reproduce or extend ATLAS end to end. It covers four layers:

- **Android app** — ATLAS Go 1.2.0, the Python/Kivy app on the `main` branch ([`android-app/`](https://github.com/FUllSCIPTS/ATLAS/tree/main/android-app)): passenger, driver and food-seller accounts, a live map with device location, solo and shared rides, food ordering from built-in and seller kitchens, stored on the device, plus six on-device models (dispatch policy, acceptance, surge outlook, supply agent, courier timing, learning lab).
- **Web front end** — the passenger and driver browser pages served by the gateway in this starter.
- **Back end** — the FastAPI gateway, trip, dispatch and model services, the event worker, Kafka, and ML training and serving.
- **Databases** — the device's `state.json` (accounts, kitchens, rides, orders) and map-tile cache, the starter's PostgreSQL (or local SQLite) schema, the Kafka event log and the model artifact volume.

The Android app has no back end today; its only network use is map tiles. Its learned policies are small constants bundled with the app, produced offline by simulations on the `main` branch; see [On-device intelligence](#on-device-intelligence-120). [Connecting the Android app to the back end](#connecting-the-android-app-to-the-back-end) maps each on-device command to the starter API, and labels the accounts, food, seller and shared-ride parts the back end does not yet implement.

[Final handover and runbook](FINAL_HANDOVER.md) · [Security and cryptography catalogue](#security-and-cryptography-catalogue) · [Runnable starter](../README.md) · [Android app source](https://github.com/FUllSCIPTS/ATLAS/tree/main/android-app) · [Android app architecture](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/docs/ARCHITECTURE.md) · [Machine-readable symbol inventory](uml-blueprint.json) · [Build specification](../../dist/build-spec.json) · [Kafka event contract](../packages/ride-event.schema.json)

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
│   ├── explorer.js
│   ├── index.html
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
| <a name="sec-pw-lab"></a>Explorer lab: PBKDF2 with the app's parameters | `secPwHash` | [architecture-explorer/dist/security.js L200](../../dist/security.js#L200) | Explorer / lab |
| <a name="sec-pw-lab-verify"></a>Explorer lab: verify_password replica | `secPwVerify` | [architecture-explorer/dist/security.js L219](../../dist/security.js#L219) | Explorer / lab |
| <a name="sec-pw-cli"></a>Command-line lab: salts, cost per guess, dictionary attack | `main` | [security_lab/password_storage_demo.py L35](https://github.com/FUllSCIPTS/ATLAS/blob/main/security_lab/password_storage_demo.py#L35) | Explorer / lab |

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
| <a name="sec-login-lab"></a>Explorer lab: LocalStore.login replica | `secLoginAttempt` | [architecture-explorer/dist/security.js L263](../../dist/security.js#L263) | Explorer / lab |

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
| <a name="sec-gw-lab"></a>Explorer lab: gateway checks step by step | `secGatewayRun` | [architecture-explorer/dist/security.js L363](../../dist/security.js#L363) | Explorer / lab |

<a name="uml-security-sso"></a>

### Security → Single sign-on

[Open in the explorer ↗](https://fullscipts.github.io/ATLAS/#security-sso)

| Concept | Function / symbol | Location | Status |
| --- | --- | --- | --- |
| <a name="sec-sso-target"></a>Where JWT validation would replace bearer keys | `proxy` | [architecture-explorer/starter/services/gateway.py L47](../services/gateway.py#L47) | Teaching extension |
| Bearer keys per actor (demo defaults) | `KEYS` | [architecture-explorer/starter/packages/config.py L13](../packages/config.py#L13) | Demo-grade |
| <a name="sec-sso-lab"></a>OIDC + PKCE flow with ES256 tokens | `secSsoNext` | [architecture-explorer/dist/security.js L416](../../dist/security.js#L416) | Explorer / lab |

<a name="uml-security-kerberos"></a>

### Security → Kerberos

[Open in the explorer ↗](https://fullscipts.github.io/ATLAS/#security-kerberos)

| Concept | Function / symbol | Location | Status |
| --- | --- | --- | --- |
| <a name="sec-krb-target"></a>What a Kerberos AP-REQ would replace in Dispatch | `internal_actor` | [architecture-explorer/starter/packages/config.py L24](../packages/config.py#L24) | Teaching extension |
| <a name="sec-krb-setup"></a>KDC database and string-to-key (PBKDF2) | `secKrbSetup` | [architecture-explorer/dist/security.js L496](../../dist/security.js#L496) | Explorer / lab |
| <a name="sec-krb-messages"></a>The six messages AS-REQ … AP-REP | `secKrbNext` | [architecture-explorer/dist/security.js L506](../../dist/security.js#L506) | Explorer / lab |
| <a name="sec-krb-ap"></a>Service checks: integrity, expiry, skew, replay cache | `secKrbVerifyAp` | [architecture-explorer/dist/security.js L579](../../dist/security.js#L579) | Explorer / lab |
| <a name="sec-krb-seal"></a>AES-256-GCM seal used for tickets | `secSeal` | [architecture-explorer/dist/security.js L82](../../dist/security.js#L82) | Explorer / lab |

<a name="uml-security-transport"></a>

### Security → mTLS & deployment

[Open in the explorer ↗](https://fullscipts.github.io/ATLAS/#security-transport)

| Concept | Function / symbol | Location | Status |
| --- | --- | --- | --- |
| <a name="sec-tls-ca"></a>Private CA, serverAuth and clientAuth certificates | `make_certs` | [prototype.zip → prototype/proto_run.py L28](https://github.com/FUllSCIPTS/ATLAS/blob/main/prototype.zip) | Implemented |
| <a name="sec-tls-client"></a>Client presents its certificate, verifies the server | `client_ctx` | [prototype.zip → prototype/proto_run.py L45](https://github.com/FUllSCIPTS/ATLAS/blob/main/prototype.zip) | Implemented |
| <a name="sec-tls-server"></a>Server requires a client certificate (CERT_REQUIRED) | `ctx.load_verify_locations(f"{certdir}/ca.crt"); ctx.verify_mode = ssl...` | [prototype.zip → prototype/module_server.py L84](https://github.com/FUllSCIPTS/ATLAS/blob/main/prototype.zip) | Implemented |
| <a name="sec-dep-headers"></a>Security headers and CSP | `securityHeaders` | [architecture-explorer/server.mjs L32](../../server.mjs#L32) | Implemented |
| <a name="sec-dep-reply"></a>Every response carries the headers | `reply` | [architecture-explorer/server.mjs L40](../../server.mjs#L40) | Implemented |
| <a name="sec-dep-loopback"></a>Listen on 127.0.0.1 only | `}).listen(port, host, () => console.log('ATLAS listening on http://${...` | [architecture-explorer/server.mjs L66](../../server.mjs#L66) | Implemented |
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
| <a name="cr-hash-cli"></a>Command-line lab: checksum collision | `section_checksum` | [security_lab/crypto_lab.py L55](https://github.com/FUllSCIPTS/ATLAS/blob/main/security_lab/crypto_lab.py#L55) | Explorer / lab |

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
| <a name="cr-pki-cli"></a>Command-line lab: certificate and pin | `section_certificate` | [security_lab/crypto_lab.py L99](https://github.com/FUllSCIPTS/ATLAS/blob/main/security_lab/crypto_lab.py#L99) | Explorer / lab |

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
| <a name="cr-sig-cli"></a>Command-line lab: textbook RSA hash-then-sign | `section_rsa` | [security_lab/crypto_lab.py L149](https://github.com/FUllSCIPTS/ATLAS/blob/main/security_lab/crypto_lab.py#L149) | Explorer / lab |

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
| <a name="cr-pqc-cli"></a>Command-line lab: Lamport one-time signature | `section_pqc` | [security_lab/crypto_lab.py L190](https://github.com/FUllSCIPTS/ATLAS/blob/main/security_lab/crypto_lab.py#L190) | Explorer / lab |

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
| Function | `read(location, main)` | — | [L164](../scripts/security_catalog.py#L164) |
| Function | `python_symbols(text)` | — | [L174](../scripts/security_catalog.py#L174) |
| Function | `locate(text, path, symbol)` | — | [L186](../scripts/security_catalog.py#L186) |
| Function | `resolve(main)` | — | [L207](../scripts/security_catalog.py#L207) |
| Function | `markdown(rows)` | — | [L239](../scripts/security_catalog.py#L239) |
| Function | `script(rows)` | — | [L262](../scripts/security_catalog.py#L262) |
| Function | `replace_block(document, content)` | — | [L270](../scripts/security_catalog.py#L270) |
| Function | `main()` | — | [L279](../scripts/security_catalog.py#L279) |

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

### `dist/explorer.js`

[Open source](../../dist/explorer.js)

| Kind | Signature | Decorators | Source |
| --- | --- | --- | --- |
| Function | `indexSystem()` | — | [L51](../../dist/explorer.js#L51) |
| Function | `indexSystem.<callback: S.links.map>(link)` | — | [L53](../../dist/explorer.js#L53) |
| Function | `indexSystem.<callback: S.folders.flatMap>(group)` | — | [L54](../../dist/explorer.js#L54) |
| Function | `indexSystem.<callback: S.folders.flatMap>.<callback: group.children.map>(entry)` | — | [L54](../../dist/explorer.js#L54) |
| Function | `$(id)` | — | [L58](../../dist/explorer.js#L58) |
| Function | `icon(name, size = 18)` | — | [L59](../../dist/explorer.js#L59) |
| Function | `<callback: document.querySelectorAll("[data-icon]").forEach>(element)` | — | [L62](../../dist/explorer.js#L62) |
| Function | `announce(message)` | — | [L64](../../dist/explorer.js#L64) |
| Function | `componentColor(id)` | — | [L68](../../dist/explorer.js#L68) |
| Function | `componentMark(id, size = 19)` | — | [L72](../../dist/explorer.js#L72) |
| Function | `viewHeading(kicker, title, detail, badge = "")` | — | [L76](../../dist/explorer.js#L76) |
| Function | `updateControls()` | — | [L80](../../dist/explorer.js#L80) |
| Function | `updateControls.<callback: Object.entries(S.scenarios).map>([id, trace])` | — | [L82](../../dist/explorer.js#L82) |
| Function | `architectureView()` | — | [L92](../../dist/explorer.js#L92) |
| Function | `architectureView.<callback: S.links.filter>({ from, to })` | — | [L95](../../dist/explorer.js#L95) |
| Function | `architectureView.<callback: trace?.steps.map>([id])` | — | [L96](../../dist/explorer.js#L96) |
| Function | `architectureView.<callback: [...visibleLinks].flatMap>({ from, to })` | — | [L98](../../dist/explorer.js#L98) |
| Function | `architectureView.<callback: Object.keys(kindLabels).flatMap>(kind)` | — | [L99](../../dist/explorer.js#L99) |
| Function | `architectureView.<callback: Object.keys(kindLabels).flatMap>.<callback: ["base", "active"].map>(tone)` | — | [L99](../../dist/explorer.js#L99) |
| Function | `architectureView.<callback: [...S.links].sort>(a, b)` | — | [L101](../../dist/explorer.js#L101) |
| Function | `architectureView.<callback: orderedLinks.map>(link)` | — | [L102](../../dist/explorer.js#L102) |
| Function | `architectureView.<callback: Object.values(S.groups).map>(group, index)` | — | [L107](../../dist/explorer.js#L107) |
| Function | `architectureView.<callback: Object.entries(S.components).map>([id, component])` | — | [L108](../../dist/explorer.js#L108) |
| Function | `architectureView.<callback: Object.entries(kindLabels).map>([kind, label])` | — | [L125](../../dist/explorer.js#L125) |
| Function | `cardsMarkup()` | — | [L128](../../dist/explorer.js#L128) |
| Function | `cardsMarkup.<callback: Object.entries(S.components).filter>([, component])` | — | [L130](../../dist/explorer.js#L130) |
| Function | `cardsMarkup.<callback: Object.entries(S.components).filter>.<callback: [component.title, component.tech, component.summary].some>(item)` | — | [L131](../../dist/explorer.js#L131) |
| Function | `cardsMarkup.<callback: matches.map>([id, component])` | — | [L132](../../dist/explorer.js#L132) |
| Function | `componentsView()` | — | [L137](../../dist/explorer.js#L137) |
| Function | `componentsView.<callback: Object.entries(S.groups).map>([id, group])` | — | [L140](../../dist/explorer.js#L140) |
| Function | `deploymentView()` | — | [L144](../../dist/explorer.js#L144) |
| Function | `deploymentView.<callback: S.zones.map>(zone, index)` | — | [L146](../../dist/explorer.js#L146) |
| Function | `deploymentView.<callback: S.zones.map>.<callback: zone.nodes.map>(id)` | — | [L146](../../dist/explorer.js#L146) |
| Function | `foldersView()` | — | [L150](../../dist/explorer.js#L150) |
| Function | `foldersView.<callback: S.folders.map>(group)` | — | [L153](../../dist/explorer.js#L153) |
| Function | `foldersView.<callback: S.folders.map>.<callback: group.children.some>(entry)` | — | [L153](../../dist/explorer.js#L153) |
| Function | `foldersView.<callback: S.folders.map>.<callback: group.children.map>(entry)` | — | [L153](../../dist/explorer.js#L153) |
| Function | `foldersView.<callback: selected.example.map>(file)` | — | [L154](../../dist/explorer.js#L154) |
| Function | `inspectorMarkup()` | — | [L157](../../dist/explorer.js#L157) |
| Function | `inspectorMarkup.<callback: S.links.filter>({ to })` | — | [L163](../../dist/explorer.js#L163) |
| Function | `inspectorMarkup.<callback: S.links.filter>({ from })` | — | [L164](../../dist/explorer.js#L164) |
| Function | `inspectorMarkup.<callback: neighbors.filter>({ rows })` | — | [L170](../../dist/explorer.js#L170) |
| Function | `inspectorMarkup.<callback: neighbors.filter(({ rows }) => rows.length).map>({ heading, rows, target })` | — | [L170](../../dist/explorer.js#L170) |
| Function | `inspectorMarkup.<callback: neighbors.filter(({ rows }) => rows.length).map>.<callback: rows.map>(link)` | — | [L170](../../dist/explorer.js#L170) |
| Function | `render()` | — | [L177](../../dist/explorer.js#L177) |
| Function | `setSystem(id, fromClick = false)` | — | [L204](../../dist/explorer.js#L204) |
| Function | `stopPlayback()` | — | [L221](../../dist/explorer.js#L221) |
| Function | `switchView(view)` | — | [L226](../../dist/explorer.js#L226) |
| Function | `applyStep(step)` | — | [L235](../../dist/explorer.js#L235) |
| Function | `setScenario(id)` | — | [L254](../../dist/explorer.js#L254) |
| Function | `playTrace()` | — | [L267](../../dist/explorer.js#L267) |
| Function | `playTrace.<callback: setInterval>()` | — | [L274](../../dist/explorer.js#L274) |
| Function | `<callback: document.addEventListener, "click">(event)` | — | [L283](../../dist/explorer.js#L283) |
| Function | `<callback: document.querySelector('[role="tablist"]').addEventListener, "keydown">(event)` | — | [L323](../../dist/explorer.js#L323) |
| Function | `<callback: $("view-content").addEventListener, "input">(event)` | — | [L335](../../dist/explorer.js#L335) |
| Function | `<callback: $("view-content").addEventListener, "toggle">(event)` | — | [L342](../../dist/explorer.js#L342) |

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
| Function | `umlTopicsSection(view, topics)` | — | [L157](../../dist/security.js#L157) |
| Function | `umlTopicsSection.<callback: topics.filter>(t)` | — | [L160](../../dist/security.js#L160) |
| Function | `umlTopicsSection.<callback: topics.filter((t) => data.topics[`${view}/${t.id}`]).map>(t)` | — | [L160](../../dist/security.js#L160) |
| Function | `umlInspector(topicKey, view, topics)` | — | [L165](../../dist/security.js#L165) |
| Function | `umlInspector.<callback: topics.filter>(t)` | — | [L169](../../dist/security.js#L169) |
| Function | `umlInspector.<callback: topics.filter((t) => data.topics[`${view}/${t.id}`]).map>(t)` | — | [L169](../../dist/security.js#L169) |
| Function | `umlInspector.<callback: ids.map>(id)` | — | [L172](../../dist/security.js#L172) |
| Function | `secOverview()` | — | [L188](../../dist/security.js#L188) |
| Function | `secOverview.<callback: Object.keys(secStatus).map>(k)` | — | [L190](../../dist/security.js#L190) |
| Function | `secOverview.<callback: secMap.map>([topic, ic, title, status, text, where])` | — | [L191](../../dist/security.js#L191) |
| Function | `async secPwHash(again = false)` | — | [L200](../../dist/security.js#L200) |
| Function | `async secPwVerify()` | — | [L219](../../dist/security.js#L219) |
| Function | `secPwVerify.<callback: Uint8Array.from>(h)` | — | [L222](../../dist/security.js#L222) |
| Function | `secPwVerify.<callback: Uint8Array.from>(h)` | — | [L225](../../dist/security.js#L225) |
| Function | `secPasswords()` | — | [L229](../../dist/security.js#L229) |
| Function | `async secLoginInit()` | — | [L255](../../dist/security.js#L255) |
| Function | `async secLoginAttempt(email, password)` | — | [L263](../../dist/security.js#L263) |
| Function | `secLogin()` | — | [L292](../../dist/security.js#L292) |
| Function | `secLogin.<callback: L.log.map>(e)` | — | [L301](../../dist/security.js#L301) |
| Function | `secLogin.<callback: L.log.map>.<callback: e.steps.map>([ok, t, d])` | — | [L301](../../dist/security.js#L301) |
| Function | `secIdentity()` | — | [L315](../../dist/security.js#L315) |
| Function | `secIdentity.<callback: stages.map>([t, c, d], i)` | — | [L326](../../dist/security.js#L326) |
| Function | `secGatewayRun(s)` | — | [L363](../../dist/security.js#L363) |
| Function | `secGatewayRun.<callback: secRoutes.find>([m, r, re])` | — | [L373](../../dist/security.js#L373) |
| Function | `secGatewayRun.<callback: Object.keys(secKeys).find>(k)` | — | [L376](../../dist/security.js#L376) |
| Function | `secGateway()` | — | [L392](../../dist/security.js#L392) |
| Function | `secGateway.<callback: Object.entries(s.headers).map>([k, v])` | — | [L396](../../dist/security.js#L396) |
| Function | `secGateway.<callback: Object.entries(secGatewayScenarios).map>([k, v])` | — | [L398](../../dist/security.js#L398) |
| Function | `secGateway.<callback: result.steps.slice(0, shown).map>([ok, t, d])` | — | [L400](../../dist/security.js#L400) |
| Function | `async secSsoNext()` | — | [L416](../../dist/security.js#L416) |
| Function | `secSsoNext.push(title, from, to, wire, checks, done = false)` | — | [L421](../../dist/security.js#L421) |
| Function | `secMessages(steps)` | — | [L472](../../dist/security.js#L472) |
| Function | `secMessages.<callback: steps.map>(m)` | — | [L473](../../dist/security.js#L473) |
| Function | `secMessages.<callback: steps.map>.<callback: m.checks.every>([ok])` | — | [L473](../../dist/security.js#L473) |
| Function | `secMessages.<callback: steps.map>.<callback: m.checks.map>([ok, t, d])` | — | [L473](../../dist/security.js#L473) |
| Function | `secSso()` | — | [L476](../../dist/security.js#L476) |
| Function | `async secKrbSetup()` | — | [L496](../../dist/security.js#L496) |
| Function | `async secKrbNext()` | — | [L506](../../dist/security.js#L506) |
| Function | `secKrbNext.kdcNow()` | — | [L511](../../dist/security.js#L511) |
| Function | `secKrbNext.appNow()` | — | [L512](../../dist/security.js#L512) |
| Function | `secKrbNext.push(title, from, to, wire, checks, done = false)` | — | [L513](../../dist/security.js#L513) |
| Function | `secKrbNext.skewOk(t)` | — | [L514](../../dist/security.js#L514) |
| Function | `secKrbNext.fail(title, from, to, wire, checks)` | — | [L515](../../dist/security.js#L515) |
| Function | `secKrbNext.<callback: Uint8Array.from>(h)` | — | [L543](../../dist/security.js#L543) |
| Function | `async secKrbVerifyAp(c, ticketBytes, authBytes)` | — | [L579](../../dist/security.js#L579) |
| Function | `secKrbVerifyAp.<callback: Uint8Array.from>(h)` | — | [L590](../../dist/security.js#L590) |
| Function | `secKrb()` | — | [L600](../../dist/security.js#L600) |
| Function | `secKrb.has(who, k)` | — | [L605](../../dist/security.js#L605) |
| Function | `secKrb.cell(ok)` | — | [L607](../../dist/security.js#L607) |
| Function | `secKrb.<callback: keyRows.map>([k, d])` | — | [L612](../../dist/security.js#L612) |
| Function | `secTransport()` | — | [L623](../../dist/security.js#L623) |
| Function | `secTransport.<callback: [
      ["Private CA", "openssl req -x509 … /CN=atlas-ca", "basicConstraints CA:TRUE, keyUsage keyCertSign, 30 days"],
      ["Server certificate", "extendedKeyUsage=serverAuth", "subjectAltName=IP:127.0.0.1 binds it to the address"],
      ["Client certificate", "extendedKeyUsage=clientAuth", "Cannot be reused as a server certificate"],
      ["Server requires a client cert", "verify_mode = ssl.CERT_REQUIRED", "No certificate from atlas-ca → handshake fails"],
      ["Client verifies the server", "create_default_context(cafile=ca.crt)", "Plus load_cert_chain to present its own identity"],
    ].map>([t, c, d], i)` | — | [L631](../../dist/security.js#L631) |
| Function | `secGaps()` | — | [L644](../../dist/security.js#L644) |
| Function | `securityInspector()` | — | [L682](../../dist/security.js#L682) |
| Function | `securityInspector.<callback: info.facts.map>([k, v])` | — | [L688](../../dist/security.js#L688) |
| Function | `securityInspector.<callback: info.files.map>([l, u])` | — | [L689](../../dist/security.js#L689) |
| Function | `securityInspector.<callback: info.questions.map>(q)` | — | [L691](../../dist/security.js#L691) |
| Function | `securityView()` | — | [L698](../../dist/security.js#L698) |
| Function | `securityView.<callback: secTopics.map>(x)` | — | [L704](../../dist/security.js#L704) |
| Function | `securityOpen(topic)` | — | [L708](../../dist/security.js#L708) |
| Function | `secSetHash()` | — | [L713](../../dist/security.js#L713) |
| Function | `async secRun(busy, task)` | — | [L717](../../dist/security.js#L717) |
| Function | `securityClick(button)` | — | [L725](../../dist/security.js#L725) |
| Function | `securityClick."pw-hash"()` | — | [L737](../../dist/security.js#L737) |
| Function | `securityClick."pw-hash".<callback: secRun, "pw">()` | — | [L737](../../dist/security.js#L737) |
| Function | `securityClick."pw-again"()` | — | [L738](../../dist/security.js#L738) |
| Function | `securityClick."pw-again".<callback: secRun, "pw">()` | — | [L738](../../dist/security.js#L738) |
| Function | `securityClick."pw-verify"()` | — | [L739](../../dist/security.js#L739) |
| Function | `securityClick."login-init"()` | — | [L740](../../dist/security.js#L740) |
| Function | `securityClick."login-wrong"()` | — | [L741](../../dist/security.js#L741) |
| Function | `securityClick."login-wrong".<callback: secRun, "login">()` | — | [L741](../../dist/security.js#L741) |
| Function | `securityClick."login-unknown"()` | — | [L742](../../dist/security.js#L742) |
| Function | `securityClick."login-unknown".<callback: secRun, "login">()` | — | [L742](../../dist/security.js#L742) |
| Function | `securityClick."login-right"()` | — | [L743](../../dist/security.js#L743) |
| Function | `securityClick."login-right".<callback: secRun, "login">()` | — | [L743](../../dist/security.js#L743) |
| Function | `securityClick."login-tick"()` | — | [L744](../../dist/security.js#L744) |
| Function | `securityClick."login-reset"()` | — | [L745](../../dist/security.js#L745) |
| Function | `securityClick."gw-step"()` | — | [L746](../../dist/security.js#L746) |
| Function | `securityClick."gw-all"()` | — | [L747](../../dist/security.js#L747) |
| Function | `securityClick."sso-next"()` | — | [L748](../../dist/security.js#L748) |
| Function | `securityClick."sso-reset"()` | — | [L749](../../dist/security.js#L749) |
| Function | `securityClick."krb-next"()` | — | [L750](../../dist/security.js#L750) |
| Function | `securityClick."krb-all"()` | — | [L751](../../dist/security.js#L751) |
| Function | `async securityClick."krb-all".<callback: secRun, "krb">()` | — | [L751](../../dist/security.js#L751) |
| Function | `securityClick."krb-reset"()` | — | [L752](../../dist/security.js#L752) |
| Function | `<callback: document.addEventListener, "input">(event)` | — | [L758](../../dist/security.js#L758) |
| Function | `<callback: document.addEventListener, "change">(event)` | — | [L763](../../dist/security.js#L763) |

### `dist/uml-catalog.js`

[Open source](../../dist/uml-catalog.js)

This file declares no functions.

### `server.mjs`

[Open source](../../server.mjs)

| Kind | Signature | Decorators | Source |
| --- | --- | --- | --- |
| Function | `async <callback: Object.entries(contentTypes).map>([file, type])` | — | [L26](../../server.mjs#L26) |
| Function | `reply(request, response, status, type, body, headers = {})` | — | [L40](../../server.mjs#L40) |
| Function | `<callback: createServer>(request, response)` | — | [L50](../../server.mjs#L50) |
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
}).listen>()` | — | [L66](../../server.mjs#L66) |

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
