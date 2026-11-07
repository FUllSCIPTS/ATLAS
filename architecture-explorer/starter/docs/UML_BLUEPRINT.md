# ATLAS ride-hailing UML blueprint

Use this blueprint to reproduce or extend ATLAS end to end. It covers four layers:

- **Android app** — ATLAS Go 1.2.0, the Python/Kivy app on the `main` branch ([`android-app/`](https://github.com/FUllSCIPTS/ATLAS/tree/main/android-app)): passenger, driver and food-seller accounts, a live map with device location, solo and shared rides, food ordering from built-in and seller kitchens, stored on the device, plus six on-device models (dispatch policy, acceptance, surge outlook, supply agent, courier timing, learning lab).
- **Web front end** — the passenger and driver browser pages served by the gateway in this starter.
- **Back end** — the FastAPI gateway, trip, dispatch and model services, the event worker, Kafka, and ML training and serving.
- **Databases** — the device's `state.json` (accounts, kitchens, rides, orders) and map-tile cache, the starter's PostgreSQL (or local SQLite) schema, the Kafka event log and the model artifact volume.

The Android app has no back end today; its only network use is map tiles. Its learned policies are small constants bundled with the app, produced offline by simulations on the `main` branch; see [On-device intelligence](#on-device-intelligence-120). [Connecting the Android app to the back end](#connecting-the-android-app-to-the-back-end) maps each on-device command to the starter API, and labels the accounts, food, seller and shared-ride parts the back end does not yet implement.

[Final handover and runbook](FINAL_HANDOVER.md) · [Runnable starter](../README.md) · [Android app source](https://github.com/FUllSCIPTS/ATLAS/tree/main/android-app) · [Android app architecture](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/docs/ARCHITECTURE.md) · [Machine-readable symbol inventory](uml-blueprint.json) · [Build specification](../../dist/build-spec.json) · [Kafka event contract](../packages/ride-event.schema.json)

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
│   ├── explorer.js
│   ├── index.html
│   ├── ride-event.schema.json
│   └── styles.css
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
│   │   └── local.sh
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

### `dist/explorer.js`

[Open source](../../dist/explorer.js)

| Kind | Signature | Decorators | Source |
| --- | --- | --- | --- |
| Function | `indexSystem()` | — | [L48](../../dist/explorer.js#L48) |
| Function | `indexSystem.<callback: S.links.map>(link)` | — | [L50](../../dist/explorer.js#L50) |
| Function | `indexSystem.<callback: S.folders.flatMap>(group)` | — | [L51](../../dist/explorer.js#L51) |
| Function | `indexSystem.<callback: S.folders.flatMap>.<callback: group.children.map>(entry)` | — | [L51](../../dist/explorer.js#L51) |
| Function | `$(id)` | — | [L55](../../dist/explorer.js#L55) |
| Function | `icon(name, size = 18)` | — | [L56](../../dist/explorer.js#L56) |
| Function | `<callback: document.querySelectorAll("[data-icon]").forEach>(element)` | — | [L59](../../dist/explorer.js#L59) |
| Function | `announce(message)` | — | [L61](../../dist/explorer.js#L61) |
| Function | `componentColor(id)` | — | [L65](../../dist/explorer.js#L65) |
| Function | `componentMark(id, size = 19)` | — | [L69](../../dist/explorer.js#L69) |
| Function | `viewHeading(kicker, title, detail, badge = "")` | — | [L73](../../dist/explorer.js#L73) |
| Function | `updateControls()` | — | [L77](../../dist/explorer.js#L77) |
| Function | `updateControls.<callback: Object.entries(S.scenarios).map>([id, trace])` | — | [L79](../../dist/explorer.js#L79) |
| Function | `architectureView()` | — | [L89](../../dist/explorer.js#L89) |
| Function | `architectureView.<callback: S.links.filter>({ from, to })` | — | [L92](../../dist/explorer.js#L92) |
| Function | `architectureView.<callback: trace?.steps.map>([id])` | — | [L93](../../dist/explorer.js#L93) |
| Function | `architectureView.<callback: [...visibleLinks].flatMap>({ from, to })` | — | [L95](../../dist/explorer.js#L95) |
| Function | `architectureView.<callback: Object.keys(kindLabels).flatMap>(kind)` | — | [L96](../../dist/explorer.js#L96) |
| Function | `architectureView.<callback: Object.keys(kindLabels).flatMap>.<callback: ["base", "active"].map>(tone)` | — | [L96](../../dist/explorer.js#L96) |
| Function | `architectureView.<callback: [...S.links].sort>(a, b)` | — | [L98](../../dist/explorer.js#L98) |
| Function | `architectureView.<callback: orderedLinks.map>(link)` | — | [L99](../../dist/explorer.js#L99) |
| Function | `architectureView.<callback: Object.values(S.groups).map>(group, index)` | — | [L104](../../dist/explorer.js#L104) |
| Function | `architectureView.<callback: Object.entries(S.components).map>([id, component])` | — | [L105](../../dist/explorer.js#L105) |
| Function | `architectureView.<callback: Object.entries(kindLabels).map>([kind, label])` | — | [L122](../../dist/explorer.js#L122) |
| Function | `cardsMarkup()` | — | [L125](../../dist/explorer.js#L125) |
| Function | `cardsMarkup.<callback: Object.entries(S.components).filter>([, component])` | — | [L127](../../dist/explorer.js#L127) |
| Function | `cardsMarkup.<callback: Object.entries(S.components).filter>.<callback: [component.title, component.tech, component.summary].some>(item)` | — | [L128](../../dist/explorer.js#L128) |
| Function | `cardsMarkup.<callback: matches.map>([id, component])` | — | [L129](../../dist/explorer.js#L129) |
| Function | `componentsView()` | — | [L134](../../dist/explorer.js#L134) |
| Function | `componentsView.<callback: Object.entries(S.groups).map>([id, group])` | — | [L137](../../dist/explorer.js#L137) |
| Function | `deploymentView()` | — | [L141](../../dist/explorer.js#L141) |
| Function | `deploymentView.<callback: S.zones.map>(zone, index)` | — | [L143](../../dist/explorer.js#L143) |
| Function | `deploymentView.<callback: S.zones.map>.<callback: zone.nodes.map>(id)` | — | [L143](../../dist/explorer.js#L143) |
| Function | `foldersView()` | — | [L147](../../dist/explorer.js#L147) |
| Function | `foldersView.<callback: S.folders.map>(group)` | — | [L150](../../dist/explorer.js#L150) |
| Function | `foldersView.<callback: S.folders.map>.<callback: group.children.some>(entry)` | — | [L150](../../dist/explorer.js#L150) |
| Function | `foldersView.<callback: S.folders.map>.<callback: group.children.map>(entry)` | — | [L150](../../dist/explorer.js#L150) |
| Function | `foldersView.<callback: selected.example.map>(file)` | — | [L151](../../dist/explorer.js#L151) |
| Function | `inspectorMarkup()` | — | [L154](../../dist/explorer.js#L154) |
| Function | `inspectorMarkup.<callback: S.links.filter>({ to })` | — | [L160](../../dist/explorer.js#L160) |
| Function | `inspectorMarkup.<callback: S.links.filter>({ from })` | — | [L161](../../dist/explorer.js#L161) |
| Function | `inspectorMarkup.<callback: neighbors.filter>({ rows })` | — | [L167](../../dist/explorer.js#L167) |
| Function | `inspectorMarkup.<callback: neighbors.filter(({ rows }) => rows.length).map>({ heading, rows, target })` | — | [L167](../../dist/explorer.js#L167) |
| Function | `inspectorMarkup.<callback: neighbors.filter(({ rows }) => rows.length).map>.<callback: rows.map>(link)` | — | [L167](../../dist/explorer.js#L167) |
| Function | `render()` | — | [L174](../../dist/explorer.js#L174) |
| Function | `setSystem(id, fromClick = false)` | — | [L201](../../dist/explorer.js#L201) |
| Function | `stopPlayback()` | — | [L218](../../dist/explorer.js#L218) |
| Function | `switchView(view)` | — | [L223](../../dist/explorer.js#L223) |
| Function | `applyStep(step)` | — | [L229](../../dist/explorer.js#L229) |
| Function | `setScenario(id)` | — | [L248](../../dist/explorer.js#L248) |
| Function | `playTrace()` | — | [L261](../../dist/explorer.js#L261) |
| Function | `playTrace.<callback: setInterval>()` | — | [L268](../../dist/explorer.js#L268) |
| Function | `<callback: document.addEventListener, "click">(event)` | — | [L277](../../dist/explorer.js#L277) |
| Function | `<callback: document.querySelector('[role="tablist"]').addEventListener, "keydown">(event)` | — | [L315](../../dist/explorer.js#L315) |
| Function | `<callback: $("view-content").addEventListener, "input">(event)` | — | [L327](../../dist/explorer.js#L327) |
| Function | `<callback: $("view-content").addEventListener, "toggle">(event)` | — | [L334](../../dist/explorer.js#L334) |

### `server.mjs`

[Open source](../../server.mjs)

| Kind | Signature | Decorators | Source |
| --- | --- | --- | --- |
| Function | `async <callback: Object.entries(contentTypes).map>([file, type])` | — | [L23](../../server.mjs#L23) |
| Function | `reply(request, response, status, type, body, headers = {})` | — | [L37](../../server.mjs#L37) |
| Function | `<callback: createServer>(request, response)` | — | [L47](../../server.mjs#L47) |
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
}).listen>()` | — | [L63](../../server.mjs#L63) |

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
