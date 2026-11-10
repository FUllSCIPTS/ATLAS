# Web Technology — an illustrated, standalone course from HTTP to full stack

**ATLAS option 11.** 23 lessons in five parts plus a bridge to native apps (Part VI), a runnable full-stack application, 20 measured experiments and 28 integration tests. **Audience:** complete beginners to intermediate students; no prior web experience is assumed. **Tools:** a browser, Python 3.10+, a text editor (VS Code or similar). Every lesson stands on its own: it explains the idea, draws it, shows working code, points to the exact line in the teaching app where it is used, names the usual mistakes and ends with exercises. The four core languages — **HTML, CSS, JavaScript and SQL** — get extended deep-dive sections, a one-page quick reference and self-check questions with answers.

[Lab manual](../web_lab/README.md) · [Open the experiments in Colab](https://colab.research.google.com/github/FUllSCIPTS/ATLAS/blob/main/web_lab/Web_Technology_Colab_Labs.ipynb) · [Teaching app source](../web_lab/) · [ATLAS UML blueprint](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/docs/UML_BLUEPRINT.md) · [ATLAS Go method catalogue](../android-app/docs/ARCHITECTURE.md#complete-source-method-catalog)

> **What is real and what is teaching code.** ATLAS Go 1.2.0 is a Python/Kivy Android app that stores everything on the phone; it has no web backend. Its front end is Python and Kivy, not HTML/CSS/JavaScript — that is taught in [Kivy Front End with ATLAS Go](WEB_TECHNOLOGY_2.md). The ATLAS **server starter** (HTML, CSS, JavaScript, FastAPI gateway and services, SQL schema) lives on the [`architecture-explorer` branch](https://github.com/FUllSCIPTS/ATLAS/tree/architecture-explorer/architecture-explorer/starter). This course's **teaching app** in [`web_lab/`](../web_lab/) is a small, independent, local ride-booking site built to demonstrate every lesson. It has no authentication and must never be put on a public network.

## Contents

| Part | Lessons | Experiments |
|---|---|---|
| I. How the Web works | [1 Internet and Web](#lesson-1--the-internet-and-the-web-clients-servers-ip-tcp-and-ports) · [2 URLs and DNS](#lesson-2--urls-and-dns) · [3 HTTP](#lesson-3--http-requests-responses-methods-status-codes-and-headers) · [4 HTTPS and TLS](#lesson-4--https-and-tls) | W01, W02 |
| II. Front end | [5 HTML](#lesson-5--html-documents-elements-attributes-and-the-tree) · [6 Forms](#lesson-6--html-forms) · [7 CSS basics](#lesson-7--css-rules-selectors-specificity-and-the-cascade) · [8 Layout](#lesson-8--the-box-model-flexbox-and-grid) · [9 Responsive and accessible](#lesson-9--responsive-and-accessible-design) · [10 JavaScript](#lesson-10--javascript-the-language) · [11 DOM and events](#lesson-11--the-dom-events-and-safe-rendering) · [12 Async and fetch](#lesson-12--asynchronous-javascript-the-event-loop-promises-asyncawait-and-fetch) | W03–W06, W20 |
| III. Back end and data | [13 REST APIs](#lesson-13--apis-and-rest-design) · [14 FastAPI](#lesson-14--building-the-back-end-with-fastapi) · [15 Relational design](#lesson-15--relational-databases-tables-keys-constraints-and-normalisation) · [16 SQL](#lesson-16--sql-queries-joins-aggregation-indexes-and-injection) · [17 Transactions](#lesson-17--transactions-concurrency-and-python-with-sqlite) | W07–W13 |
| IV. Full stack | [18 Integration](#lesson-18--putting-it-together-one-request-through-every-layer) · [19 Sessions and auth](#lesson-19--state-cookies-sessions-tokens-authentication-and-authorisation) · [20 Security](#lesson-20--web-security-owasp-top-10-in-practice) · [21 Performance](#lesson-21--performance-caching-pagination-and-load) · [22 Testing](#lesson-22--testing-web-applications) · [23 Deployment](#lesson-23--deployment-and-architecture) | W14–W19 |
| V. Practice | [Run the lab](#part-v--practice) · [Experiments](#the-20-experiments) · [Plan](#12-week-teaching-plan) · [Capstone](#capstone-and-assessment) · [Quick reference](#fundamentals-quick-reference) · [Self-check](#self-check-questions) | all |
| VI. Beyond the browser | [Web → Kivy map](#web-idea--kivy-idea--where-atlas-go-uses-it) · [What is different](#what-is-genuinely-different) · [The same form, twice](#the-same-booking-form-twice) · full course: [Kivy Front End with ATLAS Go](WEB_TECHNOLOGY_2.md) | [K01–K11](../kivy_lab/README.md) |

**Fundamentals in depth.** Each core lesson ends with numbered deep-dive sections before its exercises:

| Language | Deep-dive sections |
|---|---|
| **HTML** | [5.1 From bytes to pixels](#51-from-bytes-to-pixels-how-the-browser-reads-a-page) · [5.2 Block and inline content](#52-block-and-inline-content) · [5.3 Attributes every element accepts](#53-attributes-every-element-accepts) · [5.4 Links and paths](#54-links-and-paths) · [5.5 Images, figures and media](#55-images-figures-and-media) · [5.6 The `<head>`](#56-the-head-metadata-the-user-does-not-see) · [5.7 Character references, whitespace and comments](#57-character-references-whitespace-and-comments) · [6.1 The rest of the controls](#61-the-rest-of-the-controls) · [6.2 Buttons and what "Enter" does](#62-buttons-and-what-enter-does) · [6.3 How the data is encoded](#63-how-the-data-is-encoded) · [6.4 Validation in the browser](#64-validation-in-the-browser-attributes-css-and-the-constraint-validation-api) · [6.5 Helping people (and password managers) fill forms](#65-helping-people-and-password-managers-fill-forms) |
| **CSS** | [7.1 Three places CSS can live](#71-three-places-css-can-live) · [7.2 Inheritance and the "global" keywords](#72-inheritance-and-the-global-keywords) · [7.3 More selectors](#73-more-selectors) · [7.4 Cascade layers](#74-cascade-layers-controlling-the-order-on-purpose) · [7.5 Units, colour and typography in detail](#75-units-colour-and-typography-in-detail) · [8.1 Box-model details that surprise everyone](#81-box-model-details-that-surprise-everyone) · [8.2 Positioning and stacking](#82-positioning-and-stacking) · [8.3 Flexbox in depth](#83-flexbox-in-depth) · [8.4 Grid in depth](#84-grid-in-depth) · [9.1 Mobile-first, fluid and container-aware](#91-mobile-first-fluid-and-container-aware) · [9.2 Contrast is arithmetic](#92-contrast-is-arithmetic) · [9.3 ARIA](#93-aria-when-html-is-not-enough) · [9.4 WCAG in one table](#94-wcag-in-one-table-pour) |
| **JavaScript** | [10.1 Where JavaScript runs and how to start](#101-where-javascript-runs-and-how-to-start) · [10.2 Types, truthiness and the two "nothing" values](#102-types-truthiness-and-the-two-nothing-values) · [10.3 Scope, hoisting and closures](#103-scope-hoisting-and-closures) · [10.4 Functions in depth](#104-functions-in-depth) · [10.5 Objects, classes and JSON](#105-objects-classes-and-json) · [10.6 Strings, arrays, maps and sets](#106-strings-arrays-maps-and-sets) · [10.7 Modules](#107-modules) · [10.8 Errors](#108-errors) · [11.1 Finding and walking the tree](#111-finding-and-walking-the-tree) · [11.2 Attributes versus properties](#112-attributes-versus-properties) · [11.3 Creating, moving and removing nodes efficiently](#113-creating-moving-and-removing-nodes-efficiently) · [11.4 The event object and event delegation in full](#114-the-event-object-and-event-delegation-in-full) · [11.5 Which event to use](#115-which-event-to-use) · [11.6 Remembering things in the browser](#116-remembering-things-in-the-browser) · [12.1 Predict the order](#121-predict-the-order-synchronous-code-microtasks-and-tasks) · [12.2 Promise states and combinators](#122-promise-states-and-combinators) · [12.3 Sequential versus parallel `await`](#123-sequential-versus-parallel-await) · [12.4 A robust `fetch` wrapper](#124-a-robust-fetch-wrapper) |
| **SQL** | [15.1 Vocabulary and the four sub-languages of SQL](#151-vocabulary-and-the-four-sub-languages-of-sql) · [15.2 Data types](#152-data-types-sqlite-versus-a-server-database) · [15.3 Choosing keys](#153-choosing-keys) · [15.4 What happens when the parent row is deleted?](#154-what-happens-when-the-parent-row-is-deleted) · [15.5 Changing a schema safely](#155-changing-a-schema-safely-migrations) · [15.6 From a description to a schema](#156-from-a-description-to-a-schema) · [16.1 A richer practice database](#161-a-richer-practice-database) · [16.2 The order a SELECT is evaluated in](#162-the-order-a-select-is-evaluated-in) · [16.3 Filtering, expressions and functions](#163-filtering-expressions-and-functions) · [16.4 NULL and three-valued logic](#164-null-and-three-valued-logic) · [16.5 Subqueries and common table expressions](#165-subqueries-and-common-table-expressions) · [16.6 More kinds of join](#166-more-kinds-of-join) · [16.7 Set operations](#167-set-operations) · [16.8 Window functions](#168-window-functions-aggregates-without-collapsing-rows) · [16.9 Writing data](#169-writing-data-multi-row-inserts-upserts-and-returning) · [17.1 What can go wrong without isolation](#171-what-can-go-wrong-without-isolation) · [17.2 Optimistic concurrency with a version number](#172-optimistic-concurrency-with-a-version-number) · [17.3 Savepoints](#173-savepoints-a-transaction-inside-a-transaction) · [17.4 Good habits with database connections in Python](#174-good-habits-with-database-connections-in-python) |

~~~mermaid
flowchart LR
 U["You"] --> B["Browser<br/>HTML · CSS · JavaScript"]
 B -- "HTTP request (JSON)" --> S["Server<br/>FastAPI (Python)"]
 S -- "SQL" --> D[("Database<br/>SQLite")]
 D -- "rows" --> S
 S -- "HTTP response (JSON)" --> B
 B --> U
~~~

**The teaching app at a glance** — open it with `python -m uvicorn web_lab.app:app --reload` (see [Part V](#part-v--practice)):

| Layer | File | What it teaches |
|---|---|---|
| Structure | [`static/index.html`](../web_lab/static/index.html) | semantic HTML, a labelled form, a data table, ARIA live regions |
| Presentation | [`static/style.css`](../web_lab/static/style.css) | custom properties, box model, grid, media query, focus styles |
| Behaviour | [`static/app.js`](../web_lab/static/app.js) | FormData → JSON, `fetch`, `response.ok`, safe DOM building, pagination |
| API | [`app.py`](../web_lab/app.py) | REST routes, Pydantic validation, state machine, idempotency, ETags, CORS, security headers |
| Data | `SCHEMA` in [`app.py`](../web_lab/app.py) | two tables, primary/foreign keys, CHECK/UNIQUE constraints, indexes, JOIN, GROUP BY |
| Evidence | [`tests/test_integration.py`](../web_lab/tests/test_integration.py), [`experiments.py`](../web_lab/experiments.py) | 28 tests, 20 experiments |

**Running the Python examples.** Blocks marked `python` run as written from the repository root after `pip install -r web_lab/requirements.txt`. HTML, CSS and JavaScript blocks are meant to be typed into files or the browser console.

---

# Part I — How the Web works

## Lesson 1 — The Internet and the Web: clients, servers, IP, TCP and ports

**Idea.** The **Internet** is a worldwide network of networks that moves small **packets** of data between computers identified by **IP addresses**. The **World Wide Web** is one service that runs on top of it: documents and data exchanged with the **HTTP** protocol. Email, video calls and online games are other services on the same Internet.

A **client** asks; a **server** answers. Your browser is a client; the program that sends back a page is a server. One computer can be both — in this course your laptop runs the browser *and* the server.

~~~mermaid
flowchart TB
 subgraph stack["Each message travels down the sender's layers and up the receiver's"]
 direction TB
 A["Application: HTTP — 'GET /api/rides'"] --> T["Transport: TCP — reliable, ordered byte stream to port 8000"]
 T --> N["Internet: IP — packets addressed to 127.0.0.1 or 93.184.215.14"]
 N --> L["Link: Wi-Fi / Ethernet frames"]
 end
~~~

| Term | Meaning | Example |
|---|---|---|
| IP address | where a computer is | `127.0.0.1` (your own machine), `2001:db8::1` (IPv6) |
| port | which program on that computer | 80 HTTP, 443 HTTPS, 8000 our dev server |
| TCP | reliable, ordered connection; lost packets are re-sent | used by HTTP/1.1 and HTTP/2 |
| UDP | fast, no delivery guarantee | DNS, video; HTTP/3 uses QUIC over UDP |
| packet | a small chunk of data with source and destination addresses | ≈ 1 500 bytes |
| latency | time for a round trip | 1 ms on a LAN, 20–200 ms across the world |

~~~mermaid
sequenceDiagram
 participant C as Client (browser)
 participant S as Server (port 8000)
 C->>S: SYN (open a TCP connection)
 S-->>C: SYN-ACK
 C->>S: ACK — connection established
 C->>S: HTTP request bytes
 S-->>C: HTTP response bytes
 C->>S: FIN (close)
~~~

**Try it.** Experiment **W01** opens a raw TCP socket to the teaching server and types an HTTP request by hand — no browser, no library — showing that HTTP is just text sent over TCP:

~~~python
import socket
from web_lab.experiments import live_server

with live_server() as base:                         # starts Uvicorn on 127.0.0.1:<free port>
    host, port = base.removeprefix("http://").split(":")
    with socket.create_connection((host, int(port))) as s:
        s.sendall(f"GET /api/health HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n".encode())
        reply = b""
        while chunk := s.recv(4096):
            reply += chunk
print(reply.decode()[:400])
assert reply.startswith(b"HTTP/1.1 200 OK")
~~~

**ATLAS connection.** The ATLAS server starter's [gateway](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/services/gateway.py) listens on one port and forwards requests to services on other ports — the client/server idea repeated inside the back end.

**Exercises.** (1) Why does email not count as "the Web"? (2) Look up your machine's IP address and explain why `127.0.0.1` is different.

## Lesson 2 — URLs and DNS

**A URL names a resource and says how to reach it.**

~~~text
 https://rides.example.ie:8443/api/rides?status=requested&limit=20#top
 └─┬─┘   └──────┬──────┘ └┬─┘└───┬────┘ └─────────┬────────────┘ └┬┘
 scheme       host       port  path           query            fragment
~~~

| Part | Meaning | Notes |
|---|---|---|
| scheme | protocol | `http`, `https` |
| host | server name (or IP) | resolved by DNS |
| port | which program | default 80 (http) / 443 (https) when omitted |
| path | which resource | `/api/rides`, `/static/app.js` |
| query | parameters `key=value&…` | filtering, paging; visible in logs — never put passwords here |
| fragment | position inside the page | never sent to the server |

Special characters are **percent-encoded**: a space becomes `%20` (or `+` in a query), `é` becomes `%C3%A9`.

~~~python
from urllib.parse import urlsplit, parse_qs, urlencode, quote
url = "https://rides.example.ie:8443/api/rides?status=requested&limit=20#top"
parts = urlsplit(url)
assert (parts.scheme, parts.hostname, parts.port, parts.path) == ("https", "rides.example.ie", 8443, "/api/rides")
assert parse_qs(parts.query) == {"status": ["requested"], "limit": ["20"]} and parts.fragment == "top"
assert urlencode({"pickup": "Baile Átha Cliath"}) == "pickup=Baile+%C3%81tha+Cliath"
assert quote("UCC Main Gate") == "UCC%20Main%20Gate"
~~~

In the browser, `new URLSearchParams({limit: 20, status: "requested"}).toString()` builds the same query string — [`app.js`](../web_lab/static/app.js) uses it for paging.

**DNS** (Domain Name System) turns a host name into an IP address, like a phone book. Answers are cached for a time-to-live (TTL).

~~~mermaid
sequenceDiagram
 participant B as Browser
 participant R as Resolver (your ISP / 1.1.1.1)
 participant Root as Root server
 participant TLD as .ie server
 participant Auth as example.ie name server
 B->>R: rides.example.ie?
 R->>Root: rides.example.ie?
 Root-->>R: ask the .ie servers
 R->>TLD: rides.example.ie?
 TLD-->>R: ask example.ie's name server
 R->>Auth: rides.example.ie?
 Auth-->>R: A 203.0.113.10 (TTL 300 s)
 R-->>B: 203.0.113.10 (cached for next time)
~~~

**Exercises.** (1) Split five URLs from your browser history into their parts. (2) Why is a password in a query string worse than in a POST body?

## Lesson 3 — HTTP: requests, responses, methods, status codes and headers

**Idea.** HTTP is a **request–response** protocol of plain text messages. Every exchange is independent (**stateless**): the server remembers nothing between requests unless you build that in (cookies, tokens — Lesson 19).

~~~text
POST /api/rides HTTP/1.1                    ← request line: method, path, version
Host: 127.0.0.1:8000                        ← headers: name: value
Content-Type: application/json
Content-Length: 118
                                            ← blank line ends the headers
{"passenger":"Student","pickup":"UCC","destination":"Kent Station","distance_km":4.5,"request_key":"9f1c..."}

HTTP/1.1 201 Created                        ← status line
content-type: application/json
content-security-policy: default-src 'self'; ...
server-timing: app;dur=1.42

{"id":"0b7e...","status":"requested","fare_cents":925, ...}
~~~

### Methods

| Method | Meaning | Safe (no change)? | Idempotent (repeat = same effect)? | In the teaching app |
|---|---|---|---|---|
| GET | read | yes | yes | `GET /api/rides` |
| HEAD | headers only | yes | yes | — |
| POST | create / process | no | **no** (made idempotent with a key) | `POST /api/rides` |
| PUT | replace entirely | no | yes | — |
| PATCH | change part | no | not necessarily | `PATCH /api/rides/{id}` |
| DELETE | remove | no | yes | `DELETE /api/rides/{id}` |
| OPTIONS | ask what is allowed (CORS preflight) | yes | yes | handled by CORS middleware |

### Status codes

| Code | Name | When this app sends it |
|---|---|---|
| 200 | OK | a successful GET/PATCH; a replayed POST |
| 201 | Created | a POST created a new ride |
| 204 | No Content | DELETE succeeded (empty body) |
| 304 | Not Modified | `If-None-Match` matched the current ETag |
| 400 | Bad Request | malformed request (e.g. a CORS preflight from a disallowed origin) |
| 401 / 403 | Unauthenticated / Forbidden | (would be used with login — Lesson 19) |
| 404 | Not Found | unknown ride or driver |
| 405 | Method Not Allowed | `DELETE /api/rides` (the collection) |
| 409 | Conflict | illegal state change; reused idempotency key; duplicate driver name |
| 422 | Unprocessable Content | validation failed (Pydantic) |
| 500 | Internal Server Error | a bug — never intentional |

~~~mermaid
flowchart LR
 R["status code"] --> S2["2xx success"]
 R --> S3["3xx redirect / not modified"]
 R --> S4["4xx the client must change the request"]
 R --> S5["5xx the server failed"]
~~~

### Headers you will meet

| Header | Direction | Purpose |
|---|---|---|
| `Content-Type` | both | format of the body (`application/json`, `text/html; charset=utf-8`) |
| `Accept` | request | formats the client wants |
| `Cache-Control`, `ETag`, `If-None-Match` | both | caching (Lesson 21) |
| `Cookie` / `Set-Cookie` | request / response | state (Lesson 19) |
| `Authorization` | request | credentials, e.g. `Bearer <token>` |
| `Origin`, `Access-Control-Allow-Origin` | both | CORS (Lesson 18) |
| `Content-Security-Policy`, `X-Frame-Options` | response | security (Lesson 20) |
| `X-Total-Count` | response | custom: total rows for paging (this app) |

~~~python
from fastapi.testclient import TestClient
from web_lab.app import create_app
import tempfile, pathlib

with TestClient(create_app(pathlib.Path(tempfile.mkdtemp()) / "demo.sqlite3")) as client:
    r = client.post("/api/rides", json={"passenger": "Student", "pickup": "UCC", "destination": "Kent Station",
                                        "distance_km": 4.5, "request_key": "lesson-3-key-0001"})
    print(r.status_code, r.headers["content-type"], r.json()["fare_cents"])     # 201 application/json 925
    assert client.delete("/api/rides").status_code == 405
    assert client.get("/api/rides/nope").status_code == 404
~~~

**Experiments:** **W01** shows the raw bytes and the header/body split for six resources; **W02** triggers ten different status codes from the real API.

**Developer tools.** Press F12 → **Network**, reload the teaching page, click a request: you see the method, URL, status, request and response headers, payload and timing for every request. Use it in every lesson from now on.

**Exercises.** (1) Which methods should a search engine's crawler be allowed to call, and why? (2) Explain why POST is not idempotent and how the teaching app makes it so (Lesson 13).

## Lesson 4 — HTTPS and TLS

**Idea.** Plain HTTP can be read and changed by anyone on the path (a café Wi-Fi, a compromised router). **HTTPS** is HTTP inside **TLS**, which gives **confidentiality** (encryption), **integrity** (tamper detection) and **authentication** (the server proves its identity with a certificate signed by a trusted certificate authority).

~~~mermaid
sequenceDiagram
 participant B as Browser
 participant S as rides.example.ie
 B->>S: ClientHello (TLS 1.3, ciphers, key share)
 S-->>B: ServerHello (key share) + Certificate + signature
 Note over B: verify the certificate chain to a trusted CA,<br/>check the name matches rides.example.ie
 Note over B,S: both derive the same session keys (ECDHE)
 B->>S: encrypted HTTP request
 S-->>B: encrypted HTTP response
~~~

Rules: serve every page over HTTPS; send `Strict-Transport-Security` so browsers refuse to downgrade; mark cookies `Secure`. Local development on `http://127.0.0.1` is the accepted exception — browsers treat `localhost` as a secure context.

**ATLAS connection.** The ATLAS prototype builds its own certificate authority and uses **mutual TLS** between services; certificates, signatures and post-quantum TLS are taught in the [Cryptography course](CRYPTOGRAPHY.md).

**Exercises.** (1) Open any HTTPS site, click the padlock and read its certificate chain. (2) What can an attacker on the network still see under HTTPS (hint: the host name and the timing)?

---

# Part II — Front end

## Lesson 5 — HTML documents: elements, attributes and the tree

**Idea.** HTML describes the **structure and meaning** of a page. An **element** is usually an opening tag, content and a closing tag; **attributes** add information; elements **nest** to form a tree.

~~~text
<a href="/docs" class="nav">API docs</a>
│  └─ attribute ─┘ └─ attr ┘ └content┘
└─ opening tag ──────────────┘         └ closing tag </a>
~~~

~~~html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Cork rides</title>
  <link rel="stylesheet" href="style.css">
  <script src="app.js" defer></script>
</head>
<body>
  <header><nav><a href="/">Home</a> · <a href="/docs">API</a></nav></header>
  <main>
    <h1>Book a ride</h1>
    <p>Rides cost <strong>€2.50</strong> plus <em>€1.50 per km</em>.</p>
    <ul><li>UCC</li><li>Kent Station</li></ul>
    <img src="map.png" alt="Map of Cork city centre" width="320" height="200">
    <table>
      <caption>Fares</caption>
      <thead><tr><th scope="col">km</th><th scope="col">fare</th></tr></thead>
      <tbody><tr><td>3</td><td>€7.00</td></tr></tbody>
    </table>
  </main>
  <footer>Demo only</footer>
</body>
</html>
~~~

The browser parses this into the **DOM tree** (Document Object Model):

~~~mermaid
flowchart TD
 html --> head
 html --> body
 head --> meta1["meta charset"]
 head --> title
 head --> link["link stylesheet"]
 body --> header --> nav --> a1["a Home"]
 body --> main
 main --> h1
 main --> p --> strong
 main --> ul --> li1["li UCC"]
 main --> img["img alt=..."]
 main --> table
 body --> footer
~~~

| Element group | Elements | Use |
|---|---|---|
| document | `html`, `head`, `body`, `meta`, `title`, `link`, `script` | page set-up |
| **semantic sections** | `header`, `nav`, `main`, `section`, `article`, `aside`, `footer` | meaning for screen readers and search engines |
| text | `h1`–`h6`, `p`, `strong`, `em`, `code`, `blockquote` | headings in order, paragraphs, emphasis |
| lists | `ul`, `ol`, `li`, `dl` | unordered, ordered, definition |
| links and media | `a href`, `img src alt`, `video`, `audio` | `alt` describes images for blind users |
| tables | `table`, `caption`, `thead`, `tbody`, `tr`, `th scope`, `td` | tabular data, never layout |
| forms | `form`, `label`, `input`, `select`, `textarea`, `button` | Lesson 6 |
| generic | `div` (block), `span` (inline) | only when no semantic element fits |

**Escaping.** `<`, `>` and `&` have special meaning; write `&lt;`, `&gt;`, `&amp;` to show them as text. The teaching app never needs to, because it inserts user text with `textContent` (Lesson 11).

**ATLAS connection.** The teaching page [`index.html`](../web_lab/static/index.html) uses `header`, `main`, two `section`s with `aria-labelledby`, a `table` with `caption` and `th scope`, and a `footer`. The ATLAS starter's [passenger page](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/apps/passenger/index.html) is a second real example.

**Experiment W03** parses the teaching page with Python's `html.parser`, counts the elements by tag, measures the nesting depth and checks that every form control has a label.

**Common mistakes.** Missing `<!doctype html>` (old "quirks" rendering); skipping heading levels; `<div onclick>` instead of `<button>`; images without `alt`; tables used for layout.

### 5.1 From bytes to pixels: how the browser reads a page

Understanding the browser's pipeline explains most HTML and CSS rules — why scripts go where they go, why image sizes matter and why some CSS changes are slower than others.

~~~mermaid
flowchart LR
 H["HTML bytes"] --> TK["tokens<br/>(start tag, text, end tag)"] --> DOM["DOM tree"]
 C["CSS bytes"] --> CSSOM["CSSOM<br/>(rules + computed styles)"]
 DOM --> RT["render tree<br/>(visible nodes + their styles)"]
 CSSOM --> RT
 RT --> L["layout<br/>(size and position of every box)"] --> P["paint<br/>(pixels per layer)"] --> CO["composite<br/>(layers onto the screen)"]
 JS["JavaScript"] -. "can change" .-> DOM
 JS -. "can change" .-> CSSOM
~~~

1. **Parse HTML → DOM.** The parser reads top to bottom. It is *forgiving*: unclosed tags are closed for you, and a `<p>` that meets a `<div>` is closed automatically (a paragraph may only contain inline content).
2. **Parse CSS → CSSOM.** CSS is *render-blocking*: nothing is painted until the stylesheets in `<head>` have arrived, otherwise the page would flash unstyled.
3. **Render tree.** Only visible nodes — `<head>`, and anything with `display: none`, are left out (`visibility: hidden` is kept: it still takes space).
4. **Layout** (also called *reflow*) computes every box's geometry. Changing `width`, `font-size` or adding nodes forces layout again.
5. **Paint and composite.** Changing only `color` repaints; changing only `transform` or `opacity` can skip layout *and* paint — which is why smooth animations use those two properties (Lesson 9).

**Where scripts go.** A plain `<script src>` stops the parser until the script has downloaded and run. The `defer` and `async` attributes avoid that:

| `<script …>` | Download | Runs | Keeps document order? | Typical use |
|---|---|---|---|---|
| no attribute | blocks parsing | immediately, parser waits | yes | almost never in `<head>` |
| `async` | in parallel | as soon as it arrives (pauses parsing briefly) | **no** | independent scripts (analytics) |
| `defer` | in parallel | after the whole document is parsed, before `DOMContentLoaded` | yes | page logic — the teaching app's `app.js` |
| `type="module"` | in parallel | deferred by default; strict mode; can `import` | yes | modern code split into files |

~~~mermaid
gantt
 dateFormat X
 axisFormat %s
 section plain script
 parse HTML      :0, 3
 download + run  :crit, 3, 6
 parse rest      :6, 9
 section defer
 parse HTML      :0, 7
 download        :1, 4
 run             :crit, 7, 8
 section async
 parse HTML      :0, 3
 download        :1, 3
 run             :crit, 3, 5
 parse rest      :5, 8
~~~

### 5.2 Block and inline content

| Kind | Starts on a new line? | Width | Examples | May contain |
|---|---|---|---|---|
| **block** (flow) | yes | fills the parent | `div`, `p`, `h1`–`h6`, `ul`, `section`, `form`, `table` | other blocks and inline content (except `p`, which takes inline only) |
| **inline** (phrasing) | no | fits the content | `span`, `a`, `strong`, `em`, `code`, `img`, `input`, `label` | inline content only (`a` may wrap blocks in HTML5, but never another link or button) |

Whether an element is block or inline *by default* is decided by the browser's built-in stylesheet; CSS `display` can change how it **looks** but not what it is allowed to **contain**. Writing `<p><div>…</div></p>` produces *two* paragraphs and an orphan `</p>` — open DevTools → Elements to see the repaired tree.

### 5.3 Attributes every element accepts

| Global attribute | Purpose | Example |
|---|---|---|
| `id` | unique name in the page — for `<label for>`, `#fragment` links, `getElementById` | `id="booking"` |
| `class` | space-separated style/behaviour hooks; many elements can share one | `class="panel highlight"` |
| `data-*` | custom data for scripts and CSS | `data-status="requested"` → `el.dataset.status` |
| `lang` | language of the content (pronunciation, hyphenation, spell-check) | `<html lang="en">`, `<span lang="ga">Dia duit</span>` |
| `title` | tooltip; **not** a substitute for a label | `title="Opens a map"` |
| `hidden` | not rendered and not announced | the "Load more" button until needed |
| `tabindex` | keyboard order: `0` makes a non-focusable element focusable, `-1` makes it focusable only from script | avoid positive values |
| `style` | inline CSS (highest specificity of normal rules — avoid) | `style="color: red"` |
| `aria-*`, `role` | extra meaning for assistive technology (Lesson 9.3) | `aria-live="polite"` |

**Boolean attributes** are true when present and false when absent: `<input required>`, `<button disabled>`, `<option selected>`. Writing `disabled="false"` still **disables** the element.

### 5.4 Links and paths

| `href` value | Resolves to (page at `http://127.0.0.1:8000/static/index.html`) | Kind |
|---|---|---|
| `style.css` | `http://127.0.0.1:8000/static/style.css` | relative to the current folder |
| `/docs` | `http://127.0.0.1:8000/docs` | root-relative (same host) |
| `../api/rides` | `http://127.0.0.1:8000/api/rides` | up one folder |
| `#top` | same page, element with `id="top"` | fragment |
| `https://developer.mozilla.org/` | another site | absolute |
| `mailto:office@example.ie`, `tel:+353211234567` | opens mail / phone app | other schemes |

~~~python
from urllib.parse import urljoin                # the same resolution rules the browser uses
page = "http://127.0.0.1:8000/static/index.html"
assert urljoin(page, "style.css") == "http://127.0.0.1:8000/static/style.css"
assert urljoin(page, "/docs") == "http://127.0.0.1:8000/docs"
assert urljoin(page, "../api/rides") == "http://127.0.0.1:8000/api/rides"
assert urljoin(page, "#top") == "http://127.0.0.1:8000/static/index.html#top"
assert urljoin(page, "//cdn.example.org/lib.js") == "http://cdn.example.org/lib.js"   # scheme-relative
~~~

`target="_blank"` opens a new tab; add `rel="noopener noreferrer"` for external sites so the new page cannot control yours through `window.opener` (current browsers imply `noopener`, but older ones do not). Link text should make sense on its own — screen-reader users often jump from link to link, so "API documentation" beats "click here".

### 5.5 Images, figures and media

~~~html
<figure>
  <img src="map-800.webp"
       srcset="map-400.webp 400w, map-800.webp 800w, map-1600.webp 1600w"
       sizes="(max-width: 800px) 100vw, 50vw"
       width="800" height="500" loading="lazy" decoding="async"
       alt="Map of Cork city centre with UCC and Kent Station marked">
  <figcaption>Pickup points used in the demo.</figcaption>
</figure>

<video controls width="640" preload="metadata" poster="intro.jpg">
  <source src="intro.webm" type="video/webm">
  <source src="intro.mp4" type="video/mp4">
  <track kind="captions" src="intro.en.vtt" srclang="en" label="English">
  Your browser cannot play this video. <a href="intro.mp4">Download it</a>.
</video>
~~~

| Attribute | Why |
|---|---|
| `alt` | read aloud instead of the image; shown if it fails to load. Decorative images get `alt=""` (empty, not missing) so they are skipped |
| `width`, `height` | the browser reserves the space before the file arrives — no *layout shift* while the page loads |
| `srcset` + `sizes` | the browser picks the smallest file that is sharp enough for this screen |
| `loading="lazy"` | images far below the fold are fetched only when the user scrolls near them |
| `<track kind="captions">` | captions for deaf users and for anyone watching with the sound off |

| Format | Best for | Notes |
|---|---|---|
| JPEG | photos | lossy, universal |
| PNG | screenshots, sharp edges, transparency | lossless, larger |
| WebP / AVIF | photos and graphics | 25–50 % smaller than JPEG; supported by all current browsers |
| SVG | logos, icons, diagrams | vector XML text: scales to any size, can be styled with CSS |

### 5.6 The `<head>`: metadata the user does not see

~~~html
<head>
  <meta charset="utf-8">                                    <!-- first: how to decode the bytes -->
  <meta name="viewport" content="width=device-width, initial-scale=1">   <!-- Lesson 9 -->
  <title>Book a ride — Cork rides</title>                   <!-- tab, bookmarks, search results -->
  <meta name="description" content="Book a demo ride between Cork landmarks.">   <!-- search snippet -->
  <link rel="icon" href="/favicon.svg" type="image/svg+xml">
  <link rel="canonical" href="https://rides.example.ie/book">                 <!-- the preferred URL -->
  <meta property="og:title" content="Cork rides">          <!-- preview card when the link is shared -->
  <meta property="og:image" content="https://rides.example.ie/card.png">
  <meta name="robots" content="noindex">                    <!-- keep a demo out of search engines -->
  <link rel="stylesheet" href="/static/style.css">
  <script src="/static/app.js" defer></script>
</head>
~~~

### 5.7 Character references, whitespace and comments

| Write | Shows | Why |
|---|---|---|
| `&lt;` `&gt;` | `<` `>` | would otherwise start/end a tag |
| `&amp;` | `&` | would otherwise start a reference |
| `&quot;` | `"` | inside a double-quoted attribute |
| `&nbsp;` | a space that never breaks a line | `4.5&nbsp;km` |
| `&euro;` `&copy;` `&#8364;` `&#x20AC;` | € © € € | named, decimal and hexadecimal forms |

~~~python
import html                                       # what a server-side template engine does for you
assert html.escape('<b>"Tom" & Jerry</b>') == "&lt;b&gt;&quot;Tom&quot; &amp; Jerry&lt;/b&gt;"
assert html.unescape("&euro;2.50 &copy; UCC &#x20AC;") == "€2.50 © UCC €"
~~~

**Whitespace collapses:** any run of spaces, tabs and newlines in text is shown as one space, so indenting HTML does not change the page (use CSS `white-space: pre` or `<pre>` to keep it). **Comments** `<!-- like this -->` are not displayed but **are** sent to every visitor — never put passwords, internal URLs or notes about vulnerabilities in them.

**Exercises.** (1) Build a page about your favourite Cork place with every element group above. (2) Run it through the W3C validator (validator.w3.org). (3) Write `<p>Fares<div>from €2.50</div></p>` into a page and sketch the tree DevTools shows; explain the repair. (4) Add a `figure` with a responsive `srcset` image and check in DevTools → Network which file your screen downloads.

## Lesson 6 — HTML forms

**Idea.** A form collects input. Each control needs a **`name`** (the key sent to the server), an **`id`** and a **`<label for="id">`** (clicking the label focuses the field, and screen readers read it aloud).

~~~html
<form id="booking" action="/api/rides" method="post">
  <label for="pickup">Pickup</label>
  <input id="pickup" name="pickup" required maxlength="120" list="places" autocomplete="off">
  <datalist id="places"><option value="UCC Main Gate"><option value="Kent Station"></datalist>

  <label for="distance">Distance (km)</label>
  <input id="distance" name="distance_km" type="number" min="0.1" max="200" step="0.1" required>

  <fieldset>
    <legend>Ride type</legend>
    <label><input type="radio" name="kind" value="standard" checked> Standard</label>
    <label><input type="radio" name="kind" value="comfort"> Comfort</label>
  </fieldset>

  <label><input type="checkbox" name="share" value="yes"> Share the ride</label>
  <button type="submit">Book</button>
</form>
~~~

| `type=` | Keyboard on phones / UI | Browser checks |
|---|---|---|
| `text` (default) | letters | `required`, `minlength`, `maxlength`, `pattern` |
| `email` | `@` key | must look like an email |
| `number` | number pad | `min`, `max`, `step` |
| `tel` | phone pad | `pattern` |
| `date`, `time` | date/time picker | `min`, `max` |
| `password` | hidden characters | — |
| `checkbox`, `radio` | toggle / one of a group | `required` |
| `hidden` | none | — |

**How a form is submitted without JavaScript.** With `method="get"` the browser puts the fields in the URL (`/search?pickup=UCC&kind=standard`). With `method="post"` it sends them in the body as `application/x-www-form-urlencoded` (`pickup=UCC+Main+Gate&distance_km=4.5`). Only checked checkboxes are sent at all.

**With JavaScript** (what the teaching app does) the script intercepts the submit event and sends JSON instead — Lessons 11–12.

> **Browser validation is a convenience, not security.** Anyone can open DevTools, delete `required`, or send a request with `curl`. The server must validate every field again — Lesson 14 and experiment **W07**.

**ATLAS connection.** The teaching [`index.html`](../web_lab/static/index.html) form uses `novalidate` so that *server* error messages are shown even for empty fields — a deliberate teaching choice; remove it to see the browser's own checks. The starter's [driver page](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/apps/driver/index.html) uses number and checkbox inputs.

### 6.1 The rest of the controls

~~~html
<label for="zone">Zone</label>
<select id="zone" name="zone">
  <optgroup label="City">
    <option value="mardyke">Mardyke</option>
    <option value="grand-parade" selected>Grand Parade</option>
  </optgroup>
  <optgroup label="Suburbs"><option value="douglas">Douglas</option></optgroup>
</select>

<label for="langs">Languages the driver speaks (Ctrl/Cmd-click for several)</label>
<select id="langs" name="langs" multiple size="3">
  <option>English</option><option>Irish</option><option>Polish</option>
</select>

<label for="notes">Notes for the driver</label>
<textarea id="notes" name="notes" rows="3" maxlength="300" placeholder="e.g. wheelchair access"></textarea>

<label for="tip">Tip (%)</label>
<input id="tip" name="tip" type="range" min="0" max="20" step="5" value="10">
<output for="tip" id="tip-out">10 %</output>

<label for="photo">Profile photo</label>
<input id="photo" name="photo" type="file" accept="image/png, image/jpeg">
~~~

| Control | Sends | Remember |
|---|---|---|
| `<select>` | the chosen `option`'s `value` (or its text if there is no `value`) | `selected` sets the default; `optgroup` only groups visually |
| `<select multiple>` | the same name once per chosen option: `langs=English&langs=Irish` | server must expect a list |
| `<textarea>` | its text; the default value goes **between** the tags, not in `value=` | `maxlength` counts characters |
| `range` | a number | always show the current value (`<output>`) — a slider alone is not accessible |
| `file` | the file's bytes — only with `enctype="multipart/form-data"` (6.3) | `accept` is a hint; check the type on the server |
| `search`, `url`, `color` | text, a URL, `#rrggbb` | mobile keyboards and pickers adapt |
| `disabled` control | **nothing** — disabled fields are not submitted | use `readonly` to show-but-submit |

### 6.2 Buttons and what "Enter" does

| `<button type=…>` | Inside a form it… |
|---|---|
| `submit` (**the default**) | submits the form |
| `reset` | restores the initial values (rarely wanted; easy to press by accident) |
| `button` | does nothing on its own — for JavaScript actions |

A `<button>` with no `type` inside a form **submits** it, which is why every action button in the teaching app is written `<button type="button">`. Pressing **Enter** in a text field triggers the form's first submit button — do not fight this with `keydown` handlers; listen for the `submit` event instead and keyboard users get it for free.

### 6.3 How the data is encoded

| `enctype` | Body looks like | Use |
|---|---|---|
| `application/x-www-form-urlencoded` (default for POST) | `pickup=UCC+Main+Gate&distance_km=4.5` | simple text fields |
| `multipart/form-data` | several parts separated by a boundary line, each with its own headers | **required** for file uploads |
| `application/json` | `{"pickup": "UCC Main Gate", "distance_km": 4.5}` | not available to plain HTML forms — sent by JavaScript (`fetch`), as in the teaching app |

~~~python
from urllib.parse import urlencode, parse_qs
# what the browser sends for: pickup, a checked radio, a checked checkbox, two selected options
body = urlencode([("pickup", "UCC Main Gate"), ("kind", "standard"), ("share", "yes"),
                  ("langs", "English"), ("langs", "Irish")])
assert body == "pickup=UCC+Main+Gate&kind=standard&share=yes&langs=English&langs=Irish"
assert parse_qs(body)["langs"] == ["English", "Irish"]           # repeated names become a list
assert parse_qs("pickup=UCC")  == {"pickup": ["UCC"]}             # an unchecked box is simply absent
~~~

Everything arrives as **text**: `distance_km=4.5` is the string `"4.5"`. Converting and range-checking it is the server's job (FastAPI does both from the type hint — Lesson 14).

### 6.4 Validation in the browser: attributes, CSS and the Constraint Validation API

~~~html
<label for="email">Email</label>
<input id="email" name="email" type="email" required aria-describedby="email-help email-error">
<p id="email-help" class="hint">We only use this for receipts.</p>
<p id="email-error" class="error" aria-live="polite"></p>
~~~

~~~css
input:user-invalid { border-color: var(--danger); }      /* only after the user has interacted */
input:valid        { border-color: #1f7a3a; }
~~~

~~~javascript
const email = document.querySelector("#email");
const error = document.querySelector("#email-error");
email.addEventListener("input", () => {
  if (email.value.endsWith("@example.com")) {
    email.setCustomValidity("Please use your own address, not the example domain.");  // make it invalid
  } else {
    email.setCustomValidity("");                                    // empty string = valid again
  }
  const v = email.validity;                                         // a ValidityState object
  error.textContent = v.valueMissing ? "Email is required."
                    : v.typeMismatch ? "That does not look like an email address."
                    : email.validationMessage;                      // the custom message, if any
  email.setAttribute("aria-invalid", String(!email.checkValidity()));
});
~~~

| `validity.` flag | Set when |
|---|---|
| `valueMissing` | `required` and empty |
| `typeMismatch` | not a valid `email` / `url` |
| `patternMismatch` | does not match `pattern` |
| `tooShort` / `tooLong` | breaks `minlength` / `maxlength` |
| `rangeUnderflow` / `rangeOverflow` / `stepMismatch` | breaks `min` / `max` / `step` |
| `customError` | `setCustomValidity("…")` was called with a non-empty message |

`form.checkValidity()` returns `true`/`false`; `form.reportValidity()` also shows the browser's bubbles. Accessible error messages are **text near the field**, linked with `aria-describedby`, and the field is marked `aria-invalid="true"` — colour alone is not enough.

### 6.5 Helping people (and password managers) fill forms

| Attribute | Effect | Example |
|---|---|---|
| `autocomplete` | tells the browser which saved value fits | `name`, `email`, `tel`, `street-address`, `postal-code`, `current-password`, `new-password`, `one-time-code`, `off` |
| `inputmode` | which on-screen keyboard to show without changing validation | `numeric` for a PIN, `decimal` for a distance |
| `enterkeyhint` | label of the Enter key on phones | `send`, `next`, `search` |
| `placeholder` | an **example**, shown only while empty | never a replacement for `<label>` — it disappears as soon as you type |

**Exercises.** (1) Build a sign-up form with email, phone and a password confirmation. (2) Submit it with `method="get"` and read the URL. (3) Add a `<select multiple>` and a file input; submit once with the default encoding and once with `enctype="multipart/form-data"` and compare the request bodies in DevTools. (4) Use `setCustomValidity` so the password confirmation must match, with an accessible error message linked by `aria-describedby`.

## Lesson 7 — CSS: rules, selectors, specificity and the cascade

**Idea.** CSS (Cascading Style Sheets) says how elements **look**. A **rule** is a selector plus declarations:

~~~css
.ride strong {              /* selector: <strong> inside an element with class="ride" */
  display: block;           /* declaration = property: value; */
  color: var(--ink);        /* a custom property (variable) defined in :root */
}
~~~

| Selector | Matches | Example in [`style.css`](../web_lab/static/style.css) |
|---|---|---|
| `p` | every `<p>` (type) | `label { font-weight: 650 }` |
| `.ride` | class | `.panel`, `.ride` |
| `#message` | id (one element) | `#message` |
| `[data-status="completed"]` | attribute | `.ride[data-status="completed"]` |
| `button:hover`, `:focus-visible`, `:invalid` | pseudo-class (state) | focus ring, invalid inputs |
| `::before`, `::after` | pseudo-element | `*::before` in the reset |
| `.ride strong` | descendant | |
| `.actions > button` | child | |
| `h1, h2` | group | headings |
| `*` | everything | box-sizing reset |

### The cascade: which rule wins?

When several rules set the same property on the same element, the browser decides by, in order: **importance** (`!important`), **origin** (your CSS beats the browser's defaults), **specificity**, then **source order** (later wins). Inherited values (e.g. `color`, `font-family` from `body`) apply only if no rule targets the element.

**Specificity** is a triple (ids, classes/attributes/pseudo-classes, elements/pseudo-elements), compared left to right:

| Selector | (a, b, c) | Score shown in W04 |
|---|---|---|
| `#message` | (1, 0, 0) | 100 |
| `.ride[data-status="completed"]` | (0, 2, 0) | 20 |
| `input:invalid:not(:placeholder-shown)` | (0, 2, 1) | 21 |
| `button:hover` | (0, 1, 1) | 11 |
| `.ride strong` | (0, 1, 1) | 11 |
| `label` | (0, 0, 1) | 1 |
| `*` | (0, 0, 0) | 0 |

~~~python
from web_lab.experiments import specificity
assert specificity("#message") == (1, 0, 0)
assert specificity(".ride strong") == (0, 1, 1)
assert specificity("input:invalid:not(:placeholder-shown)") == (0, 2, 1)   # :not() counts its argument only
~~~

**Units and colours.** `px` (fixed), `rem` (relative to the root font size — preferred for text and spacing), `%` (of the parent), `vw`/`vh` (of the viewport), `fr` (grid fraction). Colours: `#135da6`, `rgb(19 93 166)`, `hsl(...)`, keywords. **Custom properties** (`--brand: #135da6;` then `var(--brand)`) keep a design consistent.

**Experiment W04** extracts every selector from `style.css`, computes its specificity and ranks them.

**Common mistakes.** Fighting specificity with `!important`; styling by `id` (hard to override); forgetting that later rules win ties.

### 7.1 Three places CSS can live

~~~html
<!-- 1. external file: cached once, shared by every page (preferred) -->
<link rel="stylesheet" href="/static/style.css">

<!-- 2. internal <style> block: one page only -->
<style>
  .notice { background: #fff6d6; }
</style>

<!-- 3. inline style attribute: one element only; beats every normal rule; hard to maintain -->
<p style="color: #a32222">Server unavailable</p>
~~~

The teaching app uses only option 1 — and its Content-Security-Policy (Lesson 20) is strict enough that options 2 and 3 would be **blocked** unless the policy were loosened.

### 7.2 Inheritance and the "global" keywords

Some properties pass from parent to child automatically; most layout properties do not.

| Inherited by default | Not inherited |
|---|---|
| `color`, `font-family`, `font-size`, `font-weight`, `line-height`, `text-align`, `letter-spacing`, `visibility`, `cursor`, `list-style` | `margin`, `padding`, `border`, `background`, `width`, `height`, `display`, `position`, `box-shadow`, `opacity` |

That is why the teaching CSS sets `font-family` and `color` once on `:root` and every element follows, while each `.panel` needs its own `padding`.

| Keyword | Means |
|---|---|
| `inherit` | take the parent's computed value — e.g. `button { font: inherit; }` (form controls do *not* inherit fonts by default; the teaching CSS fixes that) |
| `initial` | the property's specification default (`display: initial` is `inline`!) |
| `unset` | `inherit` if the property normally inherits, otherwise `initial` |
| `revert` | back to the browser's own stylesheet value |

### 7.3 More selectors

| Selector | Matches | Specificity |
|---|---|---|
| `li:first-child`, `li:last-child` | first / last child of its parent | (0,1,1) |
| `tr:nth-child(2n)` / `(odd)` / `(3n+1)` | every 2nd row / odd rows / rows 1, 4, 7 … — zebra tables | (0,1,1) |
| `p:first-of-type` | the first `p` among its siblings | (0,1,1) |
| `h2 + p` | a `p` immediately after an `h2` | (0,0,2) |
| `h2 ~ p` | every `p` sibling after an `h2` | (0,0,2) |
| `a[href^="https"]`, `[href$=".pdf"]`, `[class*="btn"]` | starts with / ends with / contains | (0,1,1), (0,1,0), (0,1,0) |
| `:is(h1, h2, h3) a` | a link in any heading | the **most** specific argument: (0,0,2) |
| `:where(h1, h2, h3) a` | the same elements | **always 0** for the `:where` part: (0,0,1) — ideal for easily overridden defaults |
| `.ride:has(button.danger)` | a card that *contains* a delete button — a "parent selector" | (0,2,1) |
| `input:not([type="checkbox"])` | all inputs except checkboxes | the argument counts: (0,1,1) |

~~~css
.stats tbody tr:nth-child(odd) { background: #f7f9fd; }          /* zebra striping */
.ride:has(.danger) { border-left-style: dashed; }                 /* deletable rides look different */
a[href^="http"]:not([href*="127.0.0.1"])::after { content: " ↗"; }   /* mark external links */
:where(ul, ol)[role="list"] { list-style: none; padding: 0; }    /* zero-specificity reset */
~~~

### 7.4 Cascade layers: controlling the order on purpose

Large style sheets often end up in "specificity wars". **`@layer`** lets you declare which group of rules wins *before* specificity is even compared: later layers beat earlier ones, and rules outside any layer beat all layers.

~~~css
@layer reset, base, components, utilities;          /* order declared once, lowest priority first */

@layer reset      { *, *::before, *::after { box-sizing: border-box; } }
@layer base       { a { color: var(--brand); } }
@layer components { .panel a { color: var(--ink); } }        /* (0,1,1) */
@layer utilities  { .text-danger { color: var(--danger); } }  /* (0,1,0) but a later layer: it wins */
~~~

With `<a class="text-danger">` inside a `.panel`, the link is red even though `.panel a` is more specific, because `utilities` is a later layer.

### 7.5 Units, colour and typography in detail

| Unit | Relative to | Good for |
|---|---|---|
| `px` | a CSS pixel (≈ 1/96 inch at arm's length; not a device pixel) | borders, shadows |
| `rem` | the **root** (`html`) font size, normally 16 px | font sizes, spacing — respects the user's browser setting |
| `em` | the **current** element's font size | padding that should grow with the text of a button |
| `%` | the parent (width, padding) or the font size (`font-size`) | fluid widths |
| `vw`, `vh` | 1 % of the viewport width / height | hero sections |
| `dvh` | 1 % of the *dynamic* viewport height (excludes a phone's moving address bar) | full-height mobile layouts |
| `ch` | width of the "0" character | readable line length: `max-width: 65ch` |
| `fr` | a share of the free space in a grid | grid tracks |

~~~python
import re
def px(value: str, root=16.0, parent_font=16.0, viewport=(1280, 800)):
    """Convert a CSS length to pixels the way the browser computes it (simplified)."""
    number, unit = re.fullmatch(r"(-?[\d.]+)([a-z]+)", value).groups()
    number = float(number)
    return {"px": number, "rem": number * root, "em": number * parent_font,
            "vw": number * viewport[0] / 100, "vh": number * viewport[1] / 100}[unit]

assert px("1.5rem") == 24.0                       # 1.5 × 16
assert px("1.5em", parent_font=20) == 30.0        # em follows the element's own font size
assert px("50vw") == 640.0 and px("10vh") == 80.0
assert px("2rem", root=20) == 40.0                # a user who sets a larger default font gets larger spacing
~~~

**Colour.** `#135da6`, `rgb(19 93 166)`, `rgb(19 93 166 / 50%)` (with transparency), `hsl(210 79% 36%)` (hue, saturation, lightness — easy to make a lighter shade by raising the last number), `oklch(...)` (perceptually even), and keywords like `transparent` and `currentColor` (the element's own text colour — handy for borders and SVG icons).

**Typography.**

~~~css
:root {
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;  /* a font *stack*: first available wins */
  line-height: 1.5;                          /* unitless: scales with each element's own font size */
}
h1 { font-size: clamp(1.6rem, 1rem + 2.5vw, 2.6rem); }   /* fluid: grows with the window, within limits */
p  { max-width: 65ch; }                                   /* 45–75 characters per line reads best */

@font-face {                                 /* a self-hosted web font */
  font-family: "Atkinson";
  src: url("/static/atkinson.woff2") format("woff2");
  font-display: swap;                        /* show fallback text immediately, swap when loaded */
}
~~~

**Custom properties in depth.** They inherit like `color`, so they can be *re-scoped*: `.danger-zone { --brand: #a32222; }` turns every `var(--brand)` inside that block red. A fallback goes after a comma: `var(--accent, #135da6)`. Unlike preprocessor variables, they are live — JavaScript can change them at run time with `document.documentElement.style.setProperty("--brand", "#0a467f")`.

**Exercises.** (1) Give `#message` a colour and then try to override it with `.ride p` — explain the result. (2) Rewrite three rules using custom properties. (3) Compute the specificity of `:is(#a, .b) p`, `:where(#a) p` and `.ride:has(button.danger)` and check your answers in DevTools (hover the selector). (4) Put the teaching CSS into four `@layer`s and show that a one-class utility rule now beats `.panel a`.

## Lesson 8 — The box model, Flexbox and Grid

### The box model

Every element is a rectangle: **content**, **padding** (inside the border), **border**, **margin** (outside, transparent).

~~~mermaid
flowchart TB
 subgraph M["margin (transparent, separates boxes)"]
  subgraph B["border"]
   subgraph P["padding (takes the background colour)"]
    C["content: width × height"]
   end
  end
 end
~~~

With the default `box-sizing: content-box`, `width: 300px; padding: 20px; border: 1px` produces a 342 px-wide box. The teaching CSS sets `*, *::before, *::after { box-sizing: border-box; }` so `width` **includes** padding and border — far easier to reason about.

**`display`** decides how a box flows: `block` (new line, full width: `div`, `p`, `section`), `inline` (inside text: `span`, `a`, `strong`), `inline-block`, `none` (removed), `flex`, `grid`. **`position`**: `static` (normal), `relative` (nudge), `absolute` (relative to the nearest positioned ancestor), `fixed` (to the viewport), `sticky`.

### Flexbox — one dimension

~~~mermaid
flowchart LR
 subgraph container["display: flex  (main axis →, cross axis ↓)"]
 direction LR
 i1["item"] --- i2["item"] --- i3["item"]
 end
~~~

~~~css
.actions {                 /* the button row on each ride card */
  display: flex;
  flex-wrap: wrap;         /* move to a new line when there is no room */
  gap: 0.5rem;             /* space between items */
  align-items: center;     /* cross-axis alignment */
}
.heading { display: flex; justify-content: space-between; }   /* title left, button right */
~~~

| Property | On | Does |
|---|---|---|
| `flex-direction` | container | `row` (default) or `column` |
| `justify-content` | container | spacing along the main axis: `flex-start`, `center`, `space-between` |
| `align-items` | container | alignment on the cross axis |
| `gap` | container | space between items |
| `flex: 1` | item | grow to share free space |

### Grid — two dimensions

~~~css
.layout {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));   /* two equal columns */
  gap: 1.3rem;
}
~~~

`fr` is a fraction of the free space; `minmax(0, 1fr)` stops long words from stretching a column. Areas can be named:

~~~css
.page {
  display: grid;
  grid-template-areas: "header header" "form rides" "footer footer";
  grid-template-columns: 1fr 1fr;
}
header { grid-area: header; }
~~~

**Rule of thumb:** Flexbox for a row or column of things (toolbars, button groups); Grid for the page layout.

### 8.1 Box-model details that surprise everyone

**Margin collapsing.** Vertical margins between two blocks do not add up: the larger one wins. A `<p>` with `margin-bottom: 24px` followed by one with `margin-top: 16px` are **24 px** apart, not 40. A child's top margin can also "leak" out of a parent that has no padding or border. Margins never collapse inside flex or grid containers — one more reason the teaching CSS uses `gap`.

**Overflow.** When content is larger than its box:

| `overflow:` | Effect |
|---|---|
| `visible` (default) | spills out over neighbours |
| `hidden` | clipped |
| `auto` | scroll bars only when needed — e.g. a wide table inside `<div style="overflow-x: auto">` on phones |
| `clip` | clipped, and no scrolling even from script |

**Sizing.** `width: auto` (default for blocks) fills the parent *minus* margins; `width: 100%` plus padding can overflow under `content-box`. Prefer `max-width` (`max-width: 1150px; margin: 2rem auto` centres the teaching layout) and `min-width: 0` on flex/grid children that contain long words or code. `aspect-ratio: 16 / 9` keeps a video box in shape while it loads.

### 8.2 Positioning and stacking

~~~css
.ride { position: relative; }                 /* becomes the reference box for absolute children */
.ride .badge {
  position: absolute; top: 0.5rem; right: 0.5rem;   /* pinned to the card's top-right corner */
}
.top { position: sticky; top: 0; z-index: 10; }      /* header stays visible while the page scrolls */
.toast { position: fixed; bottom: 1rem; right: 1rem; }  /* relative to the viewport */
~~~

| `position:` | Takes space in the flow? | Offsets (`top`, `left` …) are relative to |
|---|---|---|
| `static` | yes | ignored |
| `relative` | yes (its original spot) | its own normal position |
| `absolute` | **no** | the nearest ancestor that is not `static` (else the page) |
| `fixed` | **no** | the viewport |
| `sticky` | yes | scrolls normally until it reaches the offset, then sticks inside its parent |

**`z-index`** decides which overlapping box is on top, but only *within the same stacking context*. A new context is created by, among others, a positioned element with a `z-index`, `opacity` below 1 and any `transform`. That is why `z-index: 9999` sometimes "does nothing": the element is trapped inside a parent's context that is itself underneath.

### 8.3 Flexbox in depth

`flex: 1` is shorthand for `flex-grow: 1; flex-shrink: 1; flex-basis: 0%`. The algorithm: start each item at its **basis**, then share the **free space** in proportion to `flex-grow` — or, if there is too little space, take it away in proportion to `flex-shrink × basis`.

~~~python
def flex(container, bases, grow=None, shrink=None, gap=0):
    """Final main-axis sizes of flex items (no min/max limits) — the core of the flexbox algorithm."""
    grow = grow or [0] * len(bases)
    shrink = shrink or [1] * len(bases)
    free = container - sum(bases) - gap * (len(bases) - 1)
    if free >= 0:
        total = sum(grow)
        return [b + (free * g / total if total else 0) for b, g in zip(bases, grow)]
    weights = [s * b for s, b in zip(shrink, bases)]
    return [b + free * w / sum(weights) for b, w in zip(bases, weights)]

assert flex(600, [100, 200], grow=[1, 2]) == [200, 400]       # 300 px free, shared 1 : 2
assert flex(600, [0, 0, 0], grow=[1, 1, 1]) == [200, 200, 200]  # flex: 1 on all three → equal columns
assert flex(240, [200, 200]) == [120, 120]                    # 160 px too wide, both shrink equally
assert flex(600, [100, 100], gap=16) == [100, 100]            # grow 0 (the default): items keep their size
~~~

| Need | Flex recipe |
|---|---|
| centre something both ways | `display: flex; justify-content: center; align-items: center;` |
| push the last item to the right | `margin-left: auto` on that item |
| equal columns regardless of content | `flex: 1 1 0` on each item |
| a sidebar of fixed width, main area takes the rest | sidebar `flex: 0 0 16rem`, main `flex: 1` |
| one item aligned differently | `align-self: flex-end` on that item |
| reorder visually | `order: -1` — but screen readers and Tab still follow the HTML order, so keep source order logical |

### 8.4 Grid in depth

~~~css
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(15rem, 100%), 1fr));   /* responsive, no media query */
  gap: 1rem;
}
.cards .wide { grid-column: 1 / -1; }          /* span from the first line to the last: a full-width row */
.cards .tall { grid-row: span 2; }              /* occupy two rows */
.cards { grid-auto-rows: minmax(8rem, auto); }  /* height of rows created automatically */
.center-me { display: grid; place-items: center; }   /* the shortest way to centre */
~~~

**How many columns does `auto-fit` make?** As many tracks of the minimum width as fit, counting the gaps; the `1fr` then stretches them to fill the row.

~~~python
import math
def auto_fit(width, minimum=240, gap=16):
    columns = max(1, math.floor((width + gap) / (minimum + gap)))
    return columns, (width - gap * (columns - 1)) / columns          # (count, width of each)

assert auto_fit(1100) == (4, 263.0)
assert auto_fit(1000) == (3, 322.6666666666667)
assert auto_fit(480) == (1, 480.0) and auto_fit(500) == (2, 242.0)   # the second column appears at 496 px
~~~

| Grid term | Meaning |
|---|---|
| **line** | the numbered edges between tracks (1, 2, 3 … and −1 for the last) |
| **track** | a column or row |
| **cell** / **area** | one track crossing / a rectangle of cells, optionally named |
| `grid-template-columns: 200px 1fr 2fr` | three tracks: fixed, one share, two shares |
| `auto-fill` vs `auto-fit` | both repeat as often as fits; `auto-fit` collapses empty tracks so items stretch |

**Exercises.** (1) Calculate the rendered width of a `content-box` element with width 200 px, padding 1 rem (16 px) and a 2 px border. (2) Build a three-card row with Flexbox that wraps on small screens. (3) Use the `flex()` function in 8.3 to predict the widths for a 900 px container with bases 200/300/100 and grow 1/0/2, then check in the browser. (4) Replace the teaching layout's media query with `auto-fit` and `minmax` and compare the column breakpoints with `auto_fit()`.

## Lesson 9 — Responsive and accessible design

**Responsive** pages adapt to the screen: phones (≈ 360 px wide) to desktops (≥ 1280 px).

1. Always include `<meta name="viewport" content="width=device-width, initial-scale=1">`, otherwise phones pretend to be 980 px wide and shrink the page.
2. Use fluid sizes (`%`, `fr`, `rem`, `minmax`) instead of fixed pixel widths.
3. Change the layout with **media queries** at breakpoints where the content needs it:

~~~css
@media (max-width: 800px) {
  .layout { grid-template-columns: 1fr; }   /* one column on narrow screens */
  .top { flex-direction: column; }
}
~~~

*Mobile-first* writes the narrow layout as the default and adds `@media (min-width: …)` rules for larger screens.

**Experiment W05** opens the teaching page in Chromium at nine widths and measures the number of grid columns and the panel width: 1 column up to 800 px, 2 columns from 801 px. It saves screenshots at 480 and 1280 px.

**Accessibility** means everyone can use the page — including people using screen readers, keyboards only, magnification, or with colour-vision differences. It is also a legal requirement for public-sector sites in the EU.

| Practice | In the teaching app |
|---|---|
| every input has a `<label for>` | all five fields; W03 checks it automatically |
| keyboard focus is visible | `:focus-visible { outline: 3px solid #f2b705 }` |
| status messages are announced | `<p id="message" role="status" aria-live="polite">` |
| text contrast ≥ 4.5 : 1 (WCAG AA) | dark ink `#1b2b41` on white |
| touch targets ≥ 44 × 44 px | `button { min-height: 44px }` |
| real buttons and links, not clickable `div`s | `<button type="button">` everywhere |
| tables have captions and header scopes | the summary table |
| no information by colour alone | ride status is written, and also colour-coded |

### 9.1 Mobile-first, fluid and container-aware

~~~css
/* Mobile-first: the narrow layout is the default ... */
.layout { display: grid; grid-template-columns: 1fr; gap: 1rem; padding: 0 1rem; }

/* ... and wider screens add to it */
@media (min-width: 801px) {
  .layout { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

/* Media features beyond width */
@media (prefers-color-scheme: dark) {             /* the user chose dark mode in their OS */
  :root { --page: #0f1724; --panel: #172235; --ink: #e7edf7; --line: #2a3a55; }
}
@media (prefers-reduced-motion: reduce) {         /* motion can cause nausea for some users */
  *, *::before, *::after { animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; }
}
@media (hover: none) { .tooltip-only { display: none; } }    /* touch screens cannot hover */
@media print { .top, footer, button { display: none; } }     /* a clean printout */

/* Container queries: respond to the *component's* width, not the window's */
.panel { container-type: inline-size; }
@container (min-width: 30rem) {
  .ride { display: grid; grid-template-columns: 1fr auto; }   /* card body left, actions right */
}
~~~

A media query asks "how wide is the **window**?"; a container query asks "how wide is the **box I am in**?". The second makes a component reusable: the same ride card can sit in a narrow sidebar or a wide main column and adapt in both.

**Motion.** Animate only `transform` and `opacity` (they skip layout and paint — Lesson 5.1) and always honour `prefers-reduced-motion`:

~~~css
.ride { transition: transform 150ms ease-out, box-shadow 150ms ease-out; }
.ride:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgb(0 0 0 / 0.08); }

@keyframes fade-in { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: none; } }
.ride { animation: fade-in 200ms ease-out; }
~~~

### 9.2 Contrast is arithmetic

WCAG defines contrast from the **relative luminance** of the two colours. Text needs at least **4.5 : 1** (3 : 1 for large text ≥ 24 px, or ≥ 18.66 px bold), and since WCAG 2.1 non-text parts that you need to see — input borders, focus rings, icons — need **3 : 1** against what is next to them.

~~~python
def luminance(hex_colour: str) -> float:
    r, g, b = (int(hex_colour.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4))
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in (r, g, b)]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

def contrast(a: str, b: str) -> float:
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return round((hi + 0.05) / (lo + 0.05), 2)

assert contrast("#1b2b41", "#ffffff") == 14.3     # --ink on a white panel: passes AAA (7 : 1)
assert contrast("#4b5870", "#f3f6fc") == 6.62     # --muted hint text on the page background: passes AA
assert contrast("#ffffff", "#135da6") == 6.68     # white button text on --brand: passes AA
assert contrast("#8a8a8a", "#ffffff") == 3.45     # mid grey on white: fails for normal text
assert contrast("#f2b705", "#ffffff") == 1.82     # the yellow focus ring on white: below 3 : 1 — see exercise 3
~~~

The last line is a genuine finding in the teaching CSS: the yellow focus outline is easy to see on the dark header but weak on white panels. Exercise 3 asks you to fix it.

### 9.3 ARIA: when HTML is not enough

**The first rule of ARIA is not to use it** if a native element does the job: a `<button>` is already focusable, announced as "button", and works with Enter and Space; a `<div role="button">` needs all of that rebuilt by hand. ARIA changes only what assistive technology *announces* — never how the element behaves.

| Attribute | Use | In the teaching app |
|---|---|---|
| `aria-label="…"` | a name when there is no visible text | the driver `<select>` on each card |
| `aria-labelledby="id"` | name from another element's text | each `<section>` is named by its heading |
| `aria-describedby="id"` | extra description (hints, errors) | the stats table → its caption |
| `aria-live="polite"` / `role="status"` | announce changes without moving focus | `#message`, `#rides` |
| `aria-expanded="true/false"` | state of a disclosure / menu button | — (exercise 4) |
| `aria-invalid="true"` | the field has an error | Lesson 6.4 |
| `aria-hidden="true"` | hide decorative content from screen readers (never on focusable elements) | — |

~~~html
<a class="skip-link" href="#main">Skip to main content</a>   <!-- first focusable element on the page -->

<button type="button" aria-expanded="false" aria-controls="help">How fares work</button>
<div id="help" hidden>€2.50 base fare plus €1.50 per kilometre.</div>
~~~

~~~css
.visually-hidden {            /* hidden on screen, still read aloud — for labels you cannot show */
  position: absolute; width: 1px; height: 1px; overflow: hidden;
  clip-path: inset(50%); white-space: nowrap;
}
.skip-link { position: absolute; left: -999px; }
.skip-link:focus { left: 1rem; top: 1rem; }   /* appears only when a keyboard user tabs to it */
~~~

### 9.4 WCAG in one table: POUR

| Principle | Means | Typical checks |
|---|---|---|
| **P**erceivable | content can be seen or heard by everyone | `alt` text, captions, contrast, no colour-only meaning, text resizes to 200 % |
| **O**perable | everything works with a keyboard, with enough time | logical Tab order, visible focus, no keyboard traps, skip link, 44 px targets |
| **U**nderstandable | predictable and clear | `lang`, labels, error messages that say how to fix the problem, consistent navigation |
| **R**obust | works with current and future assistive technology | valid HTML, native elements, correct ARIA names/roles/states |

**Exercises.** (1) Use only the Tab and Enter keys to book, assign and complete a ride. (2) Run Lighthouse (DevTools → Lighthouse → Accessibility) and fix one finding. (3) The focus ring `#f2b705` has 1.82 : 1 contrast against white (9.2). Choose a focus style that reaches 3 : 1 on both the white panels and the dark header, and prove it with `contrast()`. (4) Build the "How fares work" disclosure button from 9.3 so that `aria-expanded` and `hidden` stay in step, and test it with a screen reader (NVDA, VoiceOver or TalkBack).

## Lesson 10 — JavaScript: the language

**Idea.** JavaScript is the programming language of the browser. It changes the page after it has loaded and talks to servers. You can try every line below in the browser console (F12 → Console).

~~~javascript
// Values and variables
const city = "Cork";            // const: cannot be reassigned
let rides = 0;                  // let: can change
rides += 1;
const km = 4.5, fareCents = 250 + 150 * km;          // numbers are 64-bit floats
console.log(typeof city, typeof km, typeof true, typeof null, typeof undefined);  // string number boolean object undefined

// Strict equality: always use === and !==
console.log(0 == "", 0 === "", "5" == 5, "5" === 5);   // true false true false

// Template literals
console.log(`Ride in ${city}: €${(fareCents / 100).toFixed(2)}`);   // Ride in Cork: €9.25

// Functions: declaration and arrow function
function fare(distance) { return Math.round(250 + 150 * distance); }
const euros = (cents) => "€" + (cents / 100).toFixed(2);
console.log(euros(fare(4.5)));                                     // €9.25

// Objects and arrays
const ride = { pickup: "UCC", destination: "Kent", km: 4.5, tags: ["student"] };
const { pickup, km: distance } = ride;                // destructuring
const copy = { ...ride, km: 5 };                      // spread: a new object
const drivers = [{ name: "Ava", km: 2 }, { name: "Sam", km: 0.5 }, { name: "Orla", km: 6 }];
const near = drivers.filter((d) => d.km < 3).map((d) => d.name);          // ["Ava", "Sam"]
const total = drivers.reduce((sum, d) => sum + d.km, 0);                  // 8.5
const nearest = [...drivers].sort((a, b) => a.km - b.km)[0].name;         // "Sam"
console.log(pickup, distance, copy.km, near, total, nearest);

// Control flow and errors
for (const d of drivers) { if (d.km > 5) continue; console.log(d.name); }
try { JSON.parse("{bad json"); } catch (error) { console.log("caught:", error.name); }   // SyntaxError
~~~

| Python | JavaScript |
|---|---|
| `None` | `null` (and `undefined` for "never set") |
| `True` / `False` | `true` / `false` |
| `list`, `dict` | `Array`, `Object` (or `Map`) |
| `len(xs)` | `xs.length` |
| `for x in xs:` | `for (const x of xs) {}` |
| `[f(x) for x in xs if p(x)]` | `xs.filter(p).map(f)` |
| `f"{x}"` | `` `${x}` `` |
| `raise` / `try … except` | `throw` / `try … catch` |
| `import module` | `import { name } from "./module.js"` (ES modules) |

**Common mistakes.** `==` instead of `===`; `var` (function-scoped, hoisted — use `let`/`const`); sorting numbers with `.sort()` without a compare function (`[10, 9, 1].sort()` gives `[1, 10, 9]`); `0.1 + 0.2 !== 0.3` (money in integer cents, as in Python).

**Ecosystem (for later).** **npm** installs packages; **TypeScript** adds static types; **React/Vue/Svelte** build component-based interfaces; **Vite** bundles and serves them. Learn plain JavaScript first — the teaching app and the ATLAS starter use no framework.

### 10.1 Where JavaScript runs and how to start

| Environment | Has | Lacks |
|---|---|---|
| browser page (`<script>`) | the language + `document`, `window`, `fetch`, `localStorage`, events | files on disk, direct sockets |
| browser console (F12) | the same, line by line — the quickest playground | — |
| **Node.js** (`node file.js`) | the language + files, network servers, `process` | `document` (there is no page) |

Every block in 10.2–10.8 uses only the language itself, so it runs both in the console and with `node`. Start files with `"use strict";` (modules are strict automatically): it turns silent mistakes such as assigning to an undeclared variable into errors.

### 10.2 Types, truthiness and the two "nothing" values

JavaScript has seven **primitive** types — `string`, `number`, `bigint`, `boolean`, `undefined`, `null`, `symbol` — and everything else is an **object** (arrays, functions, dates, maps …). Primitives are compared by value; objects by **reference**.

~~~javascript
"use strict";
console.log([1, 2] === [1, 2]);                 // false: two different array objects
const a = [1, 2]; const b = a; b.push(3);
console.log(a);                                 // [1, 2, 3]: a and b are the same object

// Falsy values — everything else is truthy (including "0", "false", [] and {})
const falsy = [false, 0, -0, 0n, "", null, undefined, NaN];
console.log(falsy.every((v) => !v));            // true
console.log(Boolean("0"), Boolean([]), Boolean({}));   // true true true

// || falls back on ANY falsy value; ?? only on null/undefined
const tip = 0;
console.log(tip || 10, tip ?? 10);              // 10 0  — ?? keeps a legitimate 0

// Optional chaining: stop at null/undefined instead of throwing
const ride = { driver: null };
console.log(ride.driver?.name, ride.driver?.name ?? "unassigned");   // undefined unassigned

// Numbers
console.log(0.1 + 0.2, 0.1 + 0.2 === 0.3);      // 0.30000000000000004 false
console.log(Number("4.5"), Number(""), Number("4,5"), parseFloat("4.5 km"));   // 4.5 0 NaN 4.5
console.log(Number.isNaN(NaN), NaN === NaN);    // true false: NaN is not equal to itself
console.log(Number.MAX_SAFE_INTEGER, 2n ** 64n);  // 9007199254740991 18446744073709551616n
~~~

| Value | `typeof` | Meaning |
|---|---|---|
| `undefined` | `"undefined"` | never assigned: missing argument, missing property |
| `null` | `"object"` (a historic bug) | deliberately "no value" — what JSON uses |
| `NaN` | `"number"` | the result of a failed numeric operation |
| `[]` | `"object"` | use `Array.isArray(x)` to test for arrays |
| `() => 1` | `"function"` | functions are objects you can call |

### 10.3 Scope, hoisting and closures

| | `var` | `let` | `const` |
|---|---|---|---|
| scope | the whole **function** | the enclosing `{ block }` | the enclosing `{ block }` |
| use before declaration | `undefined` (hoisted) | `ReferenceError` (the "temporal dead zone") | `ReferenceError` |
| reassign | yes | yes | **no** (but an object it holds can still change) |
| redeclare in the same scope | yes | no | no |

A **closure** is a function that remembers the variables of the scope it was created in, even after that scope has finished. It is how JavaScript keeps private state.

~~~javascript
"use strict";
function makeCounter(start = 0) {
  let count = start;                         // private: nothing outside can touch it directly
  return {
    next: () => ++count,
    reset: () => { count = start; },
  };
}
const bookings = makeCounter();
bookings.next(); bookings.next();
console.log(bookings.next());                // 3

// The classic loop puzzle: var shares one variable, let makes a fresh one per iteration
const withVar = [], withLet = [];
for (var i = 0; i < 3; i++) withVar.push(() => i);
for (let j = 0; j < 3; j++) withLet.push(() => j);
console.log(withVar.map((f) => f()), withLet.map((f) => f()));   // [3, 3, 3] [0, 1, 2]

const settings = { currency: "EUR" };
settings.currency = "GBP";                   // allowed: const protects the binding, not the object
Object.freeze(settings);                     // now the object itself is read-only
~~~

### 10.4 Functions in depth

~~~javascript
"use strict";
// default and rest parameters
function fareCents(km, base = 250, ...surcharges) {
  return Math.round(base + 150 * km + surcharges.reduce((s, x) => s + x, 0));
}
console.log(fareCents(4.5), fareCents(4.5, 300), fareCents(4.5, 250, 100, 50));   // 925 975 1075

// functions are values: pass them in, return them (higher-order functions)
const withVat = (fn, rate = 0.23) => (...args) => Math.round(fn(...args) * (1 + rate));
console.log(withVat(fareCents)(4.5));                                              // 1138

// `this` depends on HOW a regular function is called; arrow functions take `this` from where they are written
const driver = {
  name: "Ava",
  greetLater() { return [1].map(function () { return this?.name; }); },   // regular: this is undefined here
  greetArrow() { return [1].map(() => this.name); },                       // arrow: this is driver
};
console.log(driver.greetLater(), driver.greetArrow());                    // [ undefined ] [ 'Ava' ]
~~~

Use arrow functions for callbacks (`.map`, `addEventListener`, `.then`); use method syntax inside objects and classes.

### 10.5 Objects, classes and JSON

~~~javascript
"use strict";
class Ride {
  static #nextId = 1;                          // private static field
  #status = "requested";                       // private instance field: not reachable from outside

  constructor(pickup, destination, km) {
    if (pickup === destination) throw new RangeError("pickup and destination must differ");
    Object.assign(this, { id: Ride.#nextId++, pickup, destination, km });
  }
  get fareCents() { return Math.round(250 + 150 * this.km); }   // a computed property
  get status() { return this.#status; }
  assign() {
    if (this.#status !== "requested") throw new Error(`cannot assign: ride is already ${this.#status}`);
    this.#status = "assigned";
    return this;                                // return this → calls can be chained
  }
  toJSON() { return { ...this, status: this.#status, fare_cents: this.fareCents }; }
}

const r = new Ride("UCC", "Kent Station", 4.5).assign();
console.log(r.status, r.fareCents);            // assigned 925
console.log(JSON.stringify(r));                // {"id":1,"pickup":"UCC","destination":"Kent Station","km":4.5,"status":"assigned","fare_cents":925}
try { r.assign(); } catch (e) { console.log(e.message); }   // cannot assign: ride is already assigned

// copies: spread is shallow; structuredClone is deep
const original = { pickup: "UCC", tags: ["student"] };
const shallow = { ...original }, deep = structuredClone(original);
original.tags.push("night");
console.log(shallow.tags, deep.tags);          // [ 'student', 'night' ] [ 'student' ]

// iterate over an object
for (const [key, value] of Object.entries({ a: 1, b: 2 })) console.log(key, value);
~~~

Classes are a tidier syntax over JavaScript's **prototype** mechanism: methods live once on `Ride.prototype` and every instance looks them up there. `JSON.stringify` drops functions, `undefined` and private fields unless you write `toJSON()`.

### 10.6 Strings, arrays, maps and sets

| Strings | Result |
|---|---|
| `"Kent Station".toLowerCase()` | `"kent station"` |
| `"  UCC ".trim()` | `"UCC"` |
| `"UCC Main Gate".includes("Main")` / `.startsWith("UCC")` | `true` / `true` |
| `"a,b,c".split(",")` / `["a","b"].join(" · ")` | `["a","b","c"]` / `"a · b"` |
| `"7".padStart(3, "0")` | `"007"` |
| `"x".repeat(3)` | `"xxx"` |
| `` `Total: ${2 + 3}` `` | `"Total: 5"` |

| Array method | Changes the original? | Returns |
|---|---|---|
| `push`, `pop`, `shift`, `unshift`, `splice`, `sort`, `reverse`, `fill` | **yes** | various |
| `map`, `filter`, `slice`, `concat`, `flat`, `toSorted`, `toReversed`, `with` | no | a new array |
| `find`, `findIndex`, `some`, `every`, `includes`, `indexOf`, `at(-1)` | no | one value |
| `reduce` | no | anything you build |

~~~javascript
"use strict";
const rides = [
  { id: "r1", driver: "Ava", status: "completed", cents: 925 },
  { id: "r2", driver: "Ava", status: "assigned",  cents: 1450 },
  { id: "r3", driver: "Sam", status: "completed", cents: 925 },
];
// "GROUP BY driver" in JavaScript — compare with the SQL in Lesson 16
const byDriver = Object.groupBy(rides, (r) => r.driver);
const totals = Object.fromEntries(
  Object.entries(byDriver).map(([name, list]) => [name, list.reduce((s, r) => s + r.cents, 0)]));
console.log(totals);                                           // { Ava: 2375, Sam: 925 }

const statuses = new Set(rides.map((r) => r.status));          // unique values
console.log([...statuses], statuses.has("cancelled"));         // [ 'completed', 'assigned' ] false

const index = new Map(rides.map((r) => [r.id, r]));            // fast lookup by key (any key type)
console.log(index.get("r3").driver, index.size);               // Sam 3

console.log(rides.at(-1).id, rides.toSorted((a, b) => b.cents - a.cents)[0].id);   // r3 r2

const euro = new Intl.NumberFormat("en-IE", { style: "currency", currency: "EUR" });
console.log(euro.format(2375 / 100));                          // €23.75
~~~

**Dates.** `new Date(2026, 10, 9)` is **9 November** — months count from 0. Store and send times as ISO-8601 UTC strings (`new Date().toISOString()` → `"2026-11-09T09:18:00.000Z"`, the same format the teaching database uses) and format them for people only at the last moment with `toLocaleString()`.

### 10.7 Modules

~~~javascript
// fares.js — a module exports what other files may use
export const BASE_CENTS = 250;
export function fareCents(km) { return Math.round(BASE_CENTS + 150 * km); }
export default function euros(cents) { return "€" + (cents / 100).toFixed(2); }
~~~

~~~javascript
// main.js
import euros, { fareCents } from "./fares.js";
console.log(euros(fareCents(4.5)));
~~~

~~~html
<script type="module" src="/static/main.js"></script>
~~~

Each module has its own scope (no accidental globals), is loaded once however many files import it, and is deferred automatically. Modules only work over `http(s)://` — opening the HTML file directly from disk (`file://`) blocks them, which is one reason this course always serves pages through Uvicorn.

### 10.8 Errors

~~~javascript
"use strict";
class ValidationError extends Error {
  constructor(field, message) { super(message); this.name = "ValidationError"; this.field = field; }
}
function parseDistance(text) {
  const km = Number(text);
  if (!Number.isFinite(km) || km <= 0 || km > 200) throw new ValidationError("distance_km", "must be 0–200 km");
  return km;
}
for (const input of ["4.5", "abc", "-1"]) {
  try {
    console.log("ok", parseDistance(input));
  } catch (error) {
    if (error instanceof ValidationError) console.log(`${error.field}: ${error.message}`);
    else throw error;                    // never swallow errors you did not expect
  } finally {
    // runs whether or not an error happened: close things, hide spinners
  }
}
// ok 4.5 · distance_km: must be 0–200 km · distance_km: must be 0–200 km
~~~

| Built-in error | Typical cause |
|---|---|
| `SyntaxError` | invalid code, or `JSON.parse` on invalid JSON |
| `ReferenceError` | using a variable that does not exist (often a typo) |
| `TypeError` | calling something that is not a function; reading a property of `undefined` |
| `RangeError` | a number outside an allowed range (`new Array(-1)`, `toFixed(200)`) |

**Exercises.** (1) Write `formatRide(ride)` returning `"UCC → Kent (4.5 km)"`. (2) Sort drivers by rating descending then distance ascending. (3) Using `makeCounter` as a model, write `makeIdGenerator(prefix)` returning `"R-001"`, `"R-002"` …. (4) Rewrite the 10.6 `totals` computation with a single `reduce` and no `Object.groupBy`. (5) Explain, with the 10.3 table, why the `var` loop prints `[3, 3, 3]`.

## Lesson 11 — The DOM, events and safe rendering

**Idea.** JavaScript sees the page as the **DOM tree** (Lesson 5) and can find, create, change and remove nodes. **Events** (`click`, `submit`, `input`, `change`, `keydown`) let code react to the user.

~~~javascript
const message = document.querySelector("#message");          // first match of a CSS selector
const cards = document.querySelectorAll(".ride");             // all matches (a NodeList)
message.textContent = "Ready";                                // set text (safe)
message.classList.add("highlight");                           // add a CSS class
const card = document.createElement("article");               // build new nodes...
card.className = "ride";
card.dataset.status = "requested";                            // data-status="requested" (used by CSS)
card.append(Object.assign(document.createElement("strong"), { textContent: "UCC → Kent" }));
document.querySelector("#rides").append(card);                // ...and insert them

document.querySelector("#booking").addEventListener("submit", (event) => {
  event.preventDefault();                       // stop the browser's own navigation
  const values = Object.fromEntries(new FormData(event.currentTarget));   // {passenger: "...", ...}
  console.log(values);
});
~~~

### Event flow: capture, target, bubble

~~~mermaid
flowchart TB
 W["window"] -->|"1 capture ↓"| D["document"] --> B["body"] --> S["section#rides"] --> A["article.ride"] --> BT["button 'Assign' (target)"]
 BT -.->|"2 bubble ↑"| A -.-> S -.-> B -.-> D
~~~

A click on a button fires on the button, then **bubbles** up through every ancestor. **Event delegation** uses this: one listener on `#rides` can handle clicks for every card, even cards added later (`event.target.closest("button")`).

### Safe rendering and XSS

Never put untrusted text into `innerHTML`: the browser parses it as HTML and may **run** it. That is **cross-site scripting (XSS)**:

~~~javascript
const name = '<img src=x onerror="alert(document.cookie)">';   // typed into the passenger field
element.innerHTML = name;     // DANGEROUS: creates an <img> whose onerror runs the script
element.textContent = name;   // SAFE: shows the characters literally
~~~

The teaching [`app.js`](../web_lab/static/app.js) builds every card with `createElement` + `textContent` through a small `element()` helper and never uses `innerHTML`.

**Experiment W06** types that exact payload into the real form in Chromium: the card shows the text and no script runs. The same string inserted with `innerHTML` runs on a page **without** a Content-Security-Policy, but is **blocked** on the teaching page because its CSP forbids inline handlers — two independent layers of defence (Lesson 20).

### 11.1 Finding and walking the tree

| API | Returns | Note |
|---|---|---|
| `document.getElementById("rides")` | one element or `null` | fastest; no `#` |
| `document.querySelector(".ride .actions")` | first match or `null` | any CSS selector |
| `document.querySelectorAll(".ride")` | a **static** `NodeList` | does not update when the page changes; has `forEach` |
| `element.children` | a **live** `HTMLCollection` of child elements | updates automatically |
| `element.parentElement`, `.nextElementSibling`, `.previousElementSibling`, `.firstElementChild` | neighbours | the `…Element…` versions skip text nodes |
| `element.closest(".ride")` | the nearest ancestor (or itself) that matches | the key to event delegation |
| `element.matches("[data-status=completed]")` | `true` / `false` | test an element against a selector |

Always handle `null`: `document.querySelector("#typo").textContent = "x"` throws `TypeError: Cannot set properties of null`. Optional chaining (`?.`) or an early `if (!el) return;` keeps scripts robust.

### 11.2 Attributes versus properties

The HTML **attribute** is the *initial* value written in the source; the DOM **property** is the *current* live value.

~~~javascript
const input = document.querySelector("#pickup");      // <input id="pickup" value="UCC Main Gate">
// the user now types "Kent Station"
input.getAttribute("value");   // "UCC Main Gate" — what the HTML said
input.value;                   // "Kent Station"  — what is in the box now
input.defaultValue;            // "UCC Main Gate" — the property mirror of the attribute

const card = document.querySelector(".ride");
card.dataset.status = "assigned";                     // writes data-status="assigned"
card.classList.toggle("highlight");                   // add if missing, remove if present
card.classList.replace("old", "new");
card.hidden = true;                                   // same as the hidden attribute
card.style.setProperty("--accent", "#1f7a3a");        // set a CSS custom property just for this card
const button = card.querySelector("button");
button.disabled = true;                               // boolean property: true/false, not a string
~~~

Prefer changing **classes** or `data-*` attributes and letting CSS decide the look (`.ride[data-status="completed"]` in `style.css`) over writing `element.style.color = …` in JavaScript: the design then stays in one file.

### 11.3 Creating, moving and removing nodes efficiently

~~~javascript
function renderRides(container, rides) {
  const fragment = document.createDocumentFragment();     // an off-screen container
  for (const ride of rides) {
    const card = document.createElement("article");
    card.className = "ride";
    card.dataset.id = ride.id;
    const title = document.createElement("strong");
    title.textContent = `${ride.pickup} → ${ride.destination}`;   // text, never HTML
    card.append(title);
    fragment.append(card);
  }
  container.replaceChildren(fragment);    // one DOM update: removes old cards, inserts all new ones
}
~~~

Each separate insertion into the live page may trigger layout (Lesson 5.1); building in a `DocumentFragment` (or an array passed to `replaceChildren(...nodes)`) and inserting once is faster and avoids flicker. Other tools: `el.remove()`, `parent.insertBefore(newNode, reference)`, `el.before()/after()/prepend()`, `el.cloneNode(true)`.

**`<template>`** holds markup that is parsed but not displayed — a safe way to keep a card's structure in HTML rather than in JavaScript:

~~~html
<template id="ride-template">
  <article class="ride"><strong class="route"></strong><p class="meta"></p></article>
</template>
~~~

~~~javascript
const tpl = document.querySelector("#ride-template");
const card = tpl.content.firstElementChild.cloneNode(true);
card.querySelector(".route").textContent = "UCC → Kent Station";   // fill with textContent: still XSS-safe
~~~

### 11.4 The event object and event delegation in full

~~~javascript
const ridesBox = document.querySelector("#rides");

ridesBox.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-action]");   // the element actually clicked, or an ancestor
  if (!button || !ridesBox.contains(button)) return;              // a click on empty space: ignore
  const card = button.closest(".ride");
  console.log(button.dataset.action, "ride", card.dataset.id);
  // event.target        → the innermost element clicked (could be text inside the button)
  // event.currentTarget → ridesBox, the element this listener is attached to
});
~~~

One listener now serves every current *and future* card, which also means no listener has to be removed when cards are re-rendered.

| Event object member | Use |
|---|---|
| `event.preventDefault()` | stop the browser's default action (submit, follow link, check box) |
| `event.stopPropagation()` | stop bubbling to ancestors (use sparingly — it breaks delegation above) |
| `event.key`, `event.code`, `event.shiftKey` | which key: `"Enter"`, `"Escape"`, `"ArrowDown"` |
| `event.isTrusted` | `true` if caused by the user, `false` if dispatched by a script |

| `addEventListener` option | Effect |
|---|---|
| `{ once: true }` | remove automatically after the first call |
| `{ passive: true }` | promise not to call `preventDefault` — scrolling stays smooth for `touchmove`/`wheel` |
| `{ capture: true }` | run during the capture phase (on the way down) |
| `{ signal: controller.signal }` | remove when an `AbortController` is aborted — handy for clean-up |

### 11.5 Which event to use

| Event | Fires when | Use for |
|---|---|---|
| `DOMContentLoaded` | HTML parsed (deferred scripts already ran) | start-up code in non-deferred scripts |
| `load` | everything, including images, has loaded | measuring, rarely needed |
| `input` | **every** change to a field's value | live previews — the teaching app's fare preview |
| `change` | the value is committed (blur, or select chosen) | filters — the status dropdown |
| `submit` | a form is submitted by button **or** Enter key | always handle forms here, not on the button's `click` |
| `click` | mouse click, tap, **and** Enter/Space on a button | buttons and links |
| `keydown` | a key is pressed | shortcuts, Escape to close dialogs |
| `focusin` / `focusout` | focus enters / leaves (these bubble; `focus`/`blur` do not) | showing help next to the active field |
| `scroll`, `resize` | many times per second | throttle or debounce them |

**Debouncing** waits until the user stops typing before doing expensive work:

~~~javascript
function debounce(fn, ms = 250) {
  let timer;
  return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), ms); };
}
document.querySelector("#distance").addEventListener("input", debounce((event) => {
  const km = Number(event.target.value);
  document.querySelector("#fare-preview").textContent =
    km > 0 ? `Estimated fare €${((250 + 150 * km) / 100).toFixed(2)}` : "";
}, 200));
~~~

### 11.6 Remembering things in the browser

| Store | Size | Lifetime | Sent to the server? | Suitable for |
|---|---|---|---|---|
| cookie | ≈ 4 KB | until expiry | **yes, every request** | session id (with `HttpOnly`) — Lesson 19 |
| `localStorage` | ≈ 5 MB per origin | until cleared | no | preferences: last filter, theme |
| `sessionStorage` | ≈ 5 MB | until the tab closes | no | an unfinished form |
| IndexedDB | large | until cleared | no | offline data, files |

~~~javascript
const filter = document.querySelector("#statusFilter");
try { filter.value = localStorage.getItem("ride-filter") ?? ""; } catch { /* storage may be blocked */ }
filter.addEventListener("change", () => {
  try { localStorage.setItem("ride-filter", filter.value); } catch { /* ignore */ }
});
~~~

Values are always **strings** (use `JSON.stringify`/`JSON.parse` for objects), and any script on the page — including one injected by an XSS bug — can read them. **Never store passwords or tokens in `localStorage`.**

**Exercises.** (1) Rewrite the action buttons with event delegation. (2) Explain why `element.innerText = x` is safe but `element.outerHTML = x` is not. (3) Rebuild `rideCard` with a `<template>` element. (4) Remember the status filter and the passenger name in `localStorage`, and make the page still work when storage is blocked (private window).

## Lesson 12 — Asynchronous JavaScript: the event loop, promises, async/await and fetch

**Idea.** JavaScript runs your code on **one thread**. Slow operations (network, timers) must not freeze the page, so they run in the background and **call back** when done. The **event loop** takes the next finished job from a queue whenever the call stack is empty.

~~~mermaid
flowchart LR
 CS["call stack<br/>(your code, one function at a time)"] -->|"fetch(), setTimeout()"| WEB["browser APIs<br/>network, timers (in parallel)"]
 WEB -->|"done: callback"| Q["task / microtask queues"]
 Q -->|"event loop: when the stack is empty"| CS
~~~

**From callbacks to promises to async/await.** A **Promise** is an object for a value that will exist later; it is *pending*, then *fulfilled* or *rejected*. `await` pauses an `async` function until the promise settles, without blocking the page.

~~~javascript
// 1. promise chain
fetch("/api/rides")
  .then((response) => response.json())
  .then((rides) => console.log(rides.length, "rides"))
  .catch((error) => console.error("network failure", error));

// 2. the same with async/await, plus the check fetch does NOT do for you
async function loadRides() {
  const response = await fetch("/api/rides?limit=20");
  if (!response.ok) {                         // fetch only rejects on NETWORK failure, not on 404/422/500
    throw new Error(`HTTP ${response.status}`);
  }
  const total = response.headers.get("X-Total-Count");
  return { rides: await response.json(), total: Number(total) };
}

// 3. sending JSON
async function book(ride) {
  const response = await fetch("/api/rides", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(ride),
  });
  const body = await response.json();
  if (!response.ok) throw new Error(JSON.stringify(body.detail));
  return body;
}

// 4. run requests in parallel, and give up after 5 seconds
async function refreshAll() {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 5000);
  try {
    const [drivers, stats] = await Promise.all([
      fetch("/api/drivers?online=true", { signal: controller.signal }).then((r) => r.json()),
      fetch("/api/stats", { signal: controller.signal }).then((r) => r.json()),
    ]);
    return { drivers, stats };
  } finally {
    clearTimeout(timer);
  }
}
~~~

**JSON** (JavaScript Object Notation) is the text format both sides speak: `JSON.stringify(obj)` → text; `JSON.parse(text)` / `response.json()` → object. It has strings, numbers, booleans, `null`, arrays and objects — no dates, no `undefined`, no comments.

**In the teaching app** the `api()` helper in [`app.js`](../web_lab/static/app.js) wraps `fetch`, checks `response.ok`, turns Pydantic's 422 list into readable text, and `refresh()` loads drivers and then rides and stats **in parallel** with `Promise.all`.

**Experiment W20** shows the same idea in Python's `asyncio`: sixteen 50 ms waits take ≈ 800 ms one after another but ≈ 50 ms with `asyncio.gather` (Python's `Promise.all`). FastAPI uses the same event-loop model on the server.

~~~python
import asyncio, time
async def wait(ms):
    await asyncio.sleep(ms / 1000)
async def main():
    t = time.perf_counter(); await asyncio.gather(*(wait(50) for _ in range(10)))
    return (time.perf_counter() - t) * 1000
elapsed = asyncio.run(main())
print(f"ten 50 ms waits together: {elapsed:.0f} ms")
assert elapsed < 200
~~~

**Common mistakes.** Forgetting `await` (you get a Promise, not data); not checking `response.ok`; `forEach` with `async` callbacks (it does not wait); unhandled rejections.

### 12.1 Predict the order: synchronous code, microtasks and tasks

The event loop has two queues. **Microtasks** (promise callbacks, `await` continuations, `queueMicrotask`) run as soon as the current script finishes — *all* of them — before the browser does anything else. **Tasks** (timers, clicks, network events) run one per loop turn, after the microtasks and usually after a repaint.

~~~javascript
"use strict";
const log = [];
log.push("1 sync start");
setTimeout(() => log.push("7 timeout (task)"), 0);
Promise.resolve().then(() => log.push("4 promise.then (microtask)"));
queueMicrotask(() => log.push("5 queueMicrotask (microtask)"));
(async () => {
  log.push("2 inside async function, before await (still sync)");
  await null;
  log.push("6 after await (microtask)");
})();
log.push("3 sync end");
setTimeout(() => console.log(log.join("\n")), 10);
// 1 sync start
// 2 inside async function, before await (still sync)
// 3 sync end
// 4 promise.then (microtask)
// 5 queueMicrotask (microtask)
// 6 after await (microtask)
// 7 timeout (task)
~~~

Two lessons follow. First, `setTimeout(fn, 0)` means "as soon as possible *after* everything queued", not "now". Second, a long synchronous loop blocks clicks, timers *and* painting — keep work per event short, or move it to a **Web Worker** (a separate thread with no DOM access).

### 12.2 Promise states and combinators

~~~mermaid
stateDiagram-v2
 [*] --> pending: new Promise / fetch()
 pending --> fulfilled: resolve(value)
 pending --> rejected: reject(error) / throw
 fulfilled --> [*]: .then(onFulfilled) / await gives the value
 rejected --> [*]: .catch(onRejected) / await throws
~~~

| Combinator | Settles when | Result | Use |
|---|---|---|---|
| `Promise.all([...])` | all fulfil, **or** the first rejects | array of values | everything is needed — the teaching app's rides + stats |
| `Promise.allSettled([...])` | all have settled | array of `{status, value \| reason}` | a dashboard where one failed panel should not blank the others |
| `Promise.race([...])` | the first settles (either way) | that value or error | timeouts |
| `Promise.any([...])` | the first **fulfils** (or all reject) | that value | try several mirrors, use the fastest that works |

~~~javascript
"use strict";
const sleep = (ms, value, fail = false) =>
  new Promise((resolve, reject) => setTimeout(() => (fail ? reject(new Error(value)) : resolve(value)), ms));

const withTimeout = (promise, ms) =>
  Promise.race([promise, sleep(ms).then(() => { throw new Error(`timed out after ${ms} ms`); })]);

(async () => {
  console.log(await Promise.all([sleep(30, "drivers"), sleep(10, "stats")]));          // [ 'drivers', 'stats' ] — input order
  const settled = await Promise.allSettled([sleep(10, "rides"), sleep(5, "stats down", true)]);
  console.log(settled.map((s) => s.status));                                           // [ 'fulfilled', 'rejected' ]
  console.log(await Promise.any([sleep(20, "mirror A"), sleep(5, "mirror B down", true), sleep(10, "mirror C")]));  // mirror C
  try { await withTimeout(sleep(100, "slow"), 20); } catch (e) { console.log(e.message); }   // timed out after 20 ms
})();
~~~

### 12.3 Sequential versus parallel `await`

~~~javascript
"use strict";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const ids = [1, 2, 3, 4];

(async () => {
  let t = Date.now();
  for (const id of ids) await sleep(50);                    // one after another: ≈ 200 ms
  const sequential = Date.now() - t;

  t = Date.now();
  await Promise.all(ids.map(() => sleep(50)));              // all at once: ≈ 50 ms
  const parallel = Date.now() - t;

  console.log({ sequential, parallel }, sequential > 3 * parallel);   // … true

  // ids.forEach(async (id) => { await sleep(50); });  ← does NOT wait: forEach ignores returned promises
})();
~~~

Use the sequential form only when each step needs the previous result (create a ride, *then* assign it). Otherwise start the requests together — but not thousands at once: browsers allow only about six simultaneous HTTP/1.1 connections per host, and the server pays for every one.

### 12.4 A robust `fetch` wrapper

~~~javascript
async function getJSON(url, { retries = 2, timeoutMs = 5000 } = {}) {
  for (let attempt = 0; ; attempt++) {
    try {
      const response = await fetch(url, { signal: AbortSignal.timeout(timeoutMs),
                                          headers: { Accept: "application/json" } });
      if (response.status >= 500 && attempt < retries) throw new Error(`HTTP ${response.status}`);  // retry server errors
      if (!response.ok) {
        const problem = await response.json().catch(() => ({}));       // error body may not be JSON
        throw Object.assign(new Error(problem.detail ?? `HTTP ${response.status}`), { status: response.status });
      }
      return await response.json();
    } catch (error) {
      if (error.status || attempt >= retries) throw error;              // 4xx: retrying will not help
      await new Promise((r) => setTimeout(r, 200 * 2 ** attempt));      // back-off: 200 ms, 400 ms, ...
    }
  }
}
~~~

It applies every rule of this lesson: a timeout, `response.ok`, retry only safe GETs and only on network or 5xx errors, exponential back-off, and errors that carry the status for the caller to show.

**Exercises.** (1) Add a loading spinner that appears while a request is in flight. (2) Retry a failed GET up to three times with exponential back-off — and explain why retrying POST needs an idempotency key. (3) Before running it, write down the order the 12.1 example will print; then run it. (4) Change `refresh()` in the teaching app to `Promise.allSettled` so that a failing `/api/stats` still lets the ride list appear, with a message for the missing panel.

---

# Part III — Back end and data

## Lesson 13 — APIs and REST design

**Idea.** An **API** (application programming interface) is a contract between programs: which requests are allowed, what they must contain and what comes back. A **REST**-style HTTP API models data as **resources** with URLs and uses the HTTP methods for actions on them.

| Action | Method and path | Success | Errors | Teaching-app route |
|---|---|---|---|---|
| list rides | `GET /api/rides?status=&limit=&offset=` | 200 + `X-Total-Count`, `ETag` | 422 bad query | `list_rides` |
| read one | `GET /api/rides/{id}` | 200 | 404 | `get_ride` |
| create | `POST /api/rides` | 201 (200 on replay) | 409, 422 | `create_ride` |
| change state | `PATCH /api/rides/{id}` | 200 | 404, 409, 422 | `update_ride` |
| delete | `DELETE /api/rides/{id}` | 204 | 404, 409 | `delete_ride` |
| list drivers | `GET /api/drivers?online=` | 200 | 422 | `list_drivers` |
| add driver | `POST /api/drivers` | 201 | 409 duplicate, 422 | `create_driver` |
| summary | `GET /api/stats` | 200 | — | `stats` |

**Design rules.** Nouns in paths, verbs in methods (`POST /api/rides`, not `/api/createRide`); plural collections; filtering, sorting and paging in the **query string**; consistent JSON error bodies; correct status codes; version the API (`/api/v2/…`) before breaking clients.

**State machines.** A ride may only move along allowed edges; anything else is `409 Conflict`. Experiment **W08** tries all 16 combinations.

~~~mermaid
stateDiagram-v2
 [*] --> requested: POST
 requested --> assigned: PATCH + driver_id
 requested --> cancelled: PATCH
 assigned --> completed: PATCH
 assigned --> cancelled: PATCH
 requested --> [*]: DELETE
 cancelled --> [*]: DELETE
 completed --> [*]
~~~

**Idempotency keys.** A phone on a train sends `POST /api/rides`; the response is lost in a tunnel; the app retries. Without care that creates **two** rides. The client generates a random `request_key` once per booking (`crypto.randomUUID()`) and sends it with every retry; the server stores it in a `UNIQUE` column and returns the existing ride (200) for a repeat, or 409 if the same key arrives with different details. Experiment **W09** fires up to 16 *simultaneous* identical requests at a live server: exactly one row is created.

~~~mermaid
sequenceDiagram
 participant App as Browser
 participant API
 participant DB
 App->>API: POST /api/rides (request_key K)
 API->>DB: INSERT ... request_key = K
 API--xApp: 201 response lost (network)
 App->>API: retry: POST /api/rides (same K)
 API->>DB: SELECT ... WHERE request_key = K
 DB-->>API: existing ride
 API-->>App: 200 + the SAME ride (no duplicate)
~~~

**OpenAPI.** FastAPI publishes the contract as machine-readable JSON at `/openapi.json` and as an interactive page at **`/docs`**, generated from the Python type hints.

**ATLAS connection.** The ATLAS starter's [`trips.py`](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/services/trips.py) defines a `Booking` model and book/status endpoints with an idempotency key; its [trip state machine](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/docs/UML_BLUEPRINT.md#trip-state-machine) is the larger version of the diagram above.

**Exercises.** (1) Design endpoints for food orders (list, create, change state, cancel). (2) Should `PATCH /api/rides/{id}` with the current status return 200 or 409? Argue both ways.

## Lesson 14 — Building the back end with FastAPI

**Idea.** A **back end** receives requests, **validates** them, applies **business rules**, reads/writes the **database** and returns a response. **FastAPI** is a Python framework that maps functions to routes and validates data from type hints using **Pydantic**. It runs on an **ASGI** server such as **Uvicorn**.

~~~python
from typing import Annotated, Literal
from fastapi import FastAPI, HTTPException, Query
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field, StringConstraints

app = FastAPI(title="Mini rides API")
RIDES: dict[int, dict] = {}                                   # in-memory "database" for this example

class RideIn(BaseModel):                                      # request body schema
    pickup: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
    distance_km: float = Field(gt=0, le=200)

@app.get("/rides")                                            # query parameters with validation
def list_rides(min_km: float = Query(default=0, ge=0)):
    return [r for r in RIDES.values() if r["distance_km"] >= min_km]

@app.get("/rides/{ride_id}")                                  # path parameter, converted to int
def get_ride(ride_id: int):
    if ride_id not in RIDES:
        raise HTTPException(status_code=404, detail="Ride not found")
    return RIDES[ride_id]

@app.post("/rides", status_code=201)                          # body parsed and validated from JSON
def create_ride(ride: RideIn):
    new_id = len(RIDES) + 1
    RIDES[new_id] = {"id": new_id, **ride.model_dump(), "fare_cents": round(250 + 150 * ride.distance_km)}
    return RIDES[new_id]

@app.patch("/rides/{ride_id}")
def set_status(ride_id: int, status: Literal["requested", "cancelled"]):
    get_ride(ride_id)["status"] = status
    return RIDES[ride_id]

client = TestClient(app)
assert client.post("/rides", json={"pickup": " UCC ", "distance_km": 4.5}).json() == \
    {"id": 1, "pickup": "UCC", "distance_km": 4.5, "fare_cents": 925}
bad = client.post("/rides", json={"pickup": "", "distance_km": -1})
assert bad.status_code == 422
print([(e["loc"], e["msg"]) for e in bad.json()["detail"]])   # every problem, with its location
assert client.get("/rides/99").status_code == 404
assert client.get("/rides?min_km=-1").status_code == 422
assert client.patch("/rides/1?status=flying").status_code == 422
~~~

**Where data comes from:**

| Python parameter | Comes from | Example |
|---|---|---|
| name in the path template `{ride_id}` | path | `/rides/7` |
| simple type not in the path | query string | `?min_km=3` |
| Pydantic model | JSON body | `{"pickup": "UCC", ...}` |
| `Header()`, `Cookie()` | headers, cookies | `If-None-Match` |
| `Depends(fn)` | another function (dependency injection) | a DB connection, the current user |

**The 422 error format.** Pydantic reports *every* problem as `{"loc": ["body", "distance_km"], "msg": "Input should be greater than 0", "type": "greater_than"}` — the teaching app's JavaScript turns these into readable text.

**Middleware** wraps every request — the teaching app adds security headers and a `Server-Timing` header in one middleware function, and FastAPI's `CORSMiddleware` handles cross-origin rules. **Lifespan** code runs once at start-up: the teaching app creates its tables there, so merely importing `app.py` creates no files (a defect of the previous version that this rewrite fixed).

**Tour of [`app.py`](../web_lab/app.py):**

| Section | What to look for |
|---|---|
| `RideCreate`, `RideUpdate`, `DriverCreate` | constrained strings, numeric ranges, a `Literal` status, a `model_validator` that rejects identical pickup and destination |
| `SCHEMA` | two tables, keys, constraints, indexes (Lessons 15–16) |
| `connection()` | one connection per request; commit on success, rollback on error (Lesson 17) |
| `create_app()` | lifespan, CORS, the security-header middleware, static files, every route |
| `update_ride` | the state machine and the online-driver check |
| `list_rides` | pagination, `X-Total-Count`, ETag and `304 Not Modified` |

**Exercises.** (1) Add `GET /api/drivers/{id}/rides` returning a driver's rides. (2) Add a dependency that rejects requests without an `X-Demo-Key` header with 401.

## Lesson 15 — Relational databases: tables, keys, constraints and normalisation

**Idea.** A **relational database** stores data in **tables**: each **row** is one record, each **column** one attribute with a type. A **primary key** identifies a row; a **foreign key** refers to a row in another table; **constraints** make the database itself reject invalid data — even if the application has a bug.

~~~mermaid
erDiagram
 DRIVERS ||--o{ RIDES : "is assigned"
 DRIVERS {
  integer id PK
  text name UK "UNIQUE"
  text zone
  real rating "CHECK 1..5"
  integer online "CHECK 0 or 1"
 }
 RIDES {
  text id PK "uuid"
  text passenger
  text pickup
  text destination
  real distance_km "CHECK 0 < km <= 200"
  integer fare_cents "CHECK >= 0"
  text status "CHECK one of 4 states"
  text request_key UK "UNIQUE idempotency key"
  integer driver_id FK "NULL until assigned"
  text created_at
 }
~~~

| Constraint | Meaning | Example in `SCHEMA` |
|---|---|---|
| `PRIMARY KEY` | unique, not null, identifies the row | `rides.id`, `drivers.id` |
| `NOT NULL` | value required | `passenger TEXT NOT NULL` |
| `UNIQUE` | no two rows share the value | `request_key`, `drivers.name` |
| `CHECK` | condition every row must satisfy | `status IN (...)`, `rating BETWEEN 1 AND 5` |
| `FOREIGN KEY … REFERENCES` | must match an existing row | `driver_id REFERENCES drivers(id) ON DELETE RESTRICT` |
| `DEFAULT` | value when none is given | `created_at DEFAULT (strftime(...))` |

> SQLite only enforces foreign keys after `PRAGMA foreign_keys=ON` on each connection — the teaching app's `connection()` does this. Experiment **W13** shows a dangling `driver_id` being rejected.

**Relationships.** one-to-many (one driver, many rides: the foreign key goes on the "many" side); many-to-many (rides ↔ promotions) needs a **join table** `ride_promotions(ride_id, promotion_id)`; one-to-one is rare.

**Normalisation** removes repeated data so one fact is stored in one place.

| Form | Rule | Bad example | Fix |
|---|---|---|---|
| 1NF | one value per cell, no repeating groups | `drivers = "Ava, Sam"` in a ride row | one row per assignment |
| 2NF | non-key columns depend on the *whole* key | `(ride_id, driver_id) → driver_zone` | move `zone` to `drivers` |
| 3NF | non-key columns depend *only* on the key | `rides.driver_name` copied into every ride | store `driver_id`; JOIN to get the name |

Copying `driver_name` into every ride means renaming a driver needs many updates, and a missed one leaves inconsistent data. The teaching schema stores `driver_id` and the API JOINs (`RIDE_SELECT`). *Denormalising* on purpose (a cached copy) is sometimes done for speed — consciously.

**ATLAS connection.** The ATLAS starter's [`schema.sql`](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/infra/schema.sql) has trips, drivers, offers, outbox, inbox and experience tables; see its [persistence model](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/docs/UML_BLUEPRINT.md#persistence-model).

### 15.1 Vocabulary and the four sub-languages of SQL

| Relational theory | SQL / everyday | Spreadsheet analogy |
|---|---|---|
| relation | table | a sheet |
| tuple | row, record | a line |
| attribute | column, field | a column header |
| domain | data type + constraints | the kind of value a column may hold |
| schema | the set of table definitions | the sheet layout |

| Sub-language | Statements | Changes |
|---|---|---|
| **DDL** — definition | `CREATE`, `ALTER`, `DROP` (tables, indexes, views) | structure |
| **DML** — manipulation | `INSERT`, `UPDATE`, `DELETE`, (`SELECT`) | rows |
| **DCL** — control | `GRANT`, `REVOKE` | who may do what (server databases only) |
| **TCL** — transactions | `BEGIN`, `COMMIT`, `ROLLBACK`, `SAVEPOINT` | when changes become permanent (Lesson 17) |

### 15.2 Data types: SQLite versus a server database

| Purpose | SQLite | PostgreSQL | Advice |
|---|---|---|---|
| whole numbers | `INTEGER` (up to 8 bytes) | `integer`, `bigint` | ids, counts, **money in cents** |
| decimals | `REAL` (8-byte float) | `double precision`; `numeric(10,2)` exact | never store money as float |
| text | `TEXT` | `text`, `varchar(n)` | enforce lengths with `CHECK` or the API |
| true/false | `INTEGER` 0/1 + `CHECK` | `boolean` | the teaching `online` column |
| dates and times | `TEXT` in ISO-8601 (`2026-11-09T09:18:00Z`) | `timestamptz` | always store UTC |
| binary | `BLOB` | `bytea` | small files; big files belong in object storage |
| identifiers | `TEXT` UUID or `INTEGER` | `uuid`, `identity` | see 15.3 |
| structured | `TEXT` + JSON functions | `jsonb` | only for data you do not query by column |

SQLite uses **type affinity**: a column's declared type is a *preference*, and it converts values when it safely can. Add `STRICT` to a table to get the rigid checking that server databases give.

~~~python
import sqlite3
db = sqlite3.connect(":memory:")
db.execute("CREATE TABLE loose(r REAL, i INTEGER, s TEXT, anything)")
db.execute("INSERT INTO loose VALUES ('4.5', '7', 42, '3')")          # strings and numbers mixed up
assert db.execute("SELECT typeof(r), typeof(i), typeof(s), typeof(anything) FROM loose").fetchone() \
    == ("real", "integer", "text", "text")                            # converted to each column's affinity

db.execute("CREATE TABLE strict_table(i INTEGER) STRICT")
try:
    db.execute("INSERT INTO strict_table VALUES ('abc')")
except sqlite3.IntegrityError as error:
    print(error)                                       # cannot store TEXT value in INTEGER column strict_table.i
~~~

### 15.3 Choosing keys

| Kind | Example | For | Against |
|---|---|---|---|
| **natural** key | an email address, a vehicle registration | already unique and meaningful | it can change; it may be personal data |
| **surrogate** integer | `drivers.id INTEGER PRIMARY KEY AUTOINCREMENT` | small, fast to index and join | guessable (`/rides/41`, `/rides/42` …), needs the database to assign it |
| **surrogate** UUID | `rides.id TEXT` = `uuid4().hex` | can be created by the client or any server; not guessable | larger index; random order |
| **composite** key | `PRIMARY KEY (ride_id, promotion_id)` | natural for join tables; prevents duplicate pairs | longer foreign keys elsewhere |

Use a surrogate primary key and, if a natural attribute must be unique, **also** add a `UNIQUE` constraint on it — as the teaching schema does with `drivers.name` and `rides.request_key`.

### 15.4 What happens when the parent row is deleted?

`ON DELETE` on a foreign key decides; the same choices exist for `ON UPDATE`.

| Action | Effect when the referenced row is deleted | Example |
|---|---|---|
| `RESTRICT` / `NO ACTION` (default) | the delete fails | a driver with rides cannot be deleted (teaching schema) |
| `CASCADE` | dependent rows are deleted too | deleting a ride removes its promotion links |
| `SET NULL` | the foreign key becomes NULL | an employee's manager leaves |
| `SET DEFAULT` | the column gets its default value | rarely used |

~~~python
import sqlite3
db = sqlite3.connect(":memory:")
db.execute("PRAGMA foreign_keys=ON")                 # FIRST, before any transaction (see the note below)
db.executescript("""
CREATE TABLE promotions(id INTEGER PRIMARY KEY, code TEXT NOT NULL UNIQUE,
                        percent INTEGER NOT NULL CHECK(percent BETWEEN 1 AND 50));
CREATE TABLE rides(id TEXT PRIMARY KEY);
CREATE TABLE ride_promotions(                        -- a many-to-many join table
  ride_id      TEXT    NOT NULL REFERENCES rides(id)      ON DELETE CASCADE,
  promotion_id INTEGER NOT NULL REFERENCES promotions(id) ON DELETE RESTRICT,
  PRIMARY KEY (ride_id, promotion_id));              -- a composite key: each pair at most once
INSERT INTO promotions VALUES (1, 'STUDENT10', 10), (2, 'NIGHT20', 20);
INSERT INTO rides VALUES ('r1'), ('r2');
INSERT INTO ride_promotions VALUES ('r1', 1), ('r1', 2), ('r2', 1);
""")
db.execute("DELETE FROM rides WHERE id = 'r1'")                         # CASCADE removes r1's two links
assert db.execute("SELECT * FROM ride_promotions").fetchall() == [("r2", 1)]
try:
    db.execute("DELETE FROM promotions WHERE id = 1")                   # still used by r2: RESTRICT
except sqlite3.IntegrityError as error:
    assert "FOREIGN KEY" in str(error)
assert db.execute("DELETE FROM promotions WHERE id = 2").rowcount == 1  # no longer used: allowed
~~~

> **A trap worth remembering.** `PRAGMA foreign_keys=ON` is silently ignored inside an open transaction, and Python's `sqlite3` opens one automatically before the first `INSERT`/`UPDATE`/`DELETE`. Set the pragma immediately after connecting — exactly where the teaching app's `connection()` does.

### 15.5 Changing a schema safely: migrations

~~~sql
ALTER TABLE drivers ADD COLUMN phone TEXT;                     -- add a column (existing rows get NULL)
ALTER TABLE drivers RENAME COLUMN zone TO home_zone;           -- rename
CREATE INDEX idx_rides_created ON rides(created_at);           -- add an index
DROP INDEX IF EXISTS idx_rides_created;                        -- and remove it
CREATE VIEW completed_rides AS                                 -- a saved query that behaves like a table
  SELECT r.id, r.fare_cents, d.name AS driver
  FROM rides r JOIN drivers d ON d.id = r.driver_id
  WHERE r.status = 'completed';
DROP TABLE IF EXISTS old_rides;                                -- irreversible: back up first
~~~

A **migration** is a numbered script that moves the schema from one version to the next (`0003_add_driver_phone.sql`). Migrations are kept in version control, applied in order by a tool (Alembic for Python, Flyway, Prisma …) and never edited once run in production. Adding a nullable column is safe; renaming or dropping one breaks any code still using the old name, so large systems do it in steps: add new → write both → move readers → drop old.

### 15.6 From a description to a schema

> *"Passengers book rides from a pickup to a destination. A driver, who works in one zone, is assigned to each ride. A ride can use several promotion codes; a code can be used on many rides."*

1. **Nouns become candidate tables:** passenger, ride, driver, zone, promotion.
2. **Facts about one thing become columns** of that thing's table: a driver's zone → `drivers.zone` (or a `zones` table if zones have facts of their own).
3. **Relationships set where keys go:** one driver – many rides → `rides.driver_id`; many rides – many promotions → a join table.
4. **Rules become constraints:** "fare cannot be negative" → `CHECK`; "a name is unique" → `UNIQUE`; "every ride has a passenger" → `NOT NULL` + foreign key.
5. **Check normal forms** (the table above) and draw the ER diagram.
6. **List the queries** the application will run and add indexes for their `WHERE`, `JOIN` and `ORDER BY` columns.

**Exercises.** (1) Add a `passengers` table and change `rides.passenger` to a foreign key. (2) Normalise a spreadsheet of orders with columns `order, customer, customer_phone, dish1, dish2, dish3`. (3) Write the migration that adds a nullable `phone` column to `drivers` and a `CHECK` that it starts with `+`. (4) Apply the six steps of 15.6 to: *"Students borrow books from branches; each copy of a book belongs to one branch; a loan records the copy, the student and the due date."*

## Lesson 16 — SQL: queries, joins, aggregation, indexes and injection

**Idea.** **SQL** (Structured Query Language) defines tables (DDL) and reads/changes rows (DML). The examples run in an in-memory SQLite database with the teaching app's own schema.

~~~python
import sqlite3
from web_lab.app import SCHEMA
db = sqlite3.connect(":memory:")
db.row_factory = sqlite3.Row
db.execute("PRAGMA foreign_keys=ON")
db.executescript(SCHEMA)                                                      # CREATE TABLE ...

db.executemany("INSERT INTO drivers(name, zone, rating, online) VALUES (?, ?, ?, ?)",
               [("Ava", "Mardyke", 4.9, 1), ("Sam", "Grand Parade", 4.7, 1), ("Orla", "Douglas", 4.8, 0)])
rides = [("r1", "Student A", "UCC", "Kent", 4.5, 925, "completed", "k-000001", 1),
         ("r2", "Student B", "UCC", "Airport", 8.0, 1450, "assigned", "k-000002", 1),
         ("r3", "Student C", "Kent", "UCC", 4.5, 925, "completed", "k-000003", 2),
         ("r4", "Student D", "City", "UCC", 2.0, 550, "requested", "k-000004", None)]
db.executemany("""INSERT INTO rides(id, passenger, pickup, destination, distance_km, fare_cents,
                  status, request_key, driver_id) VALUES (?,?,?,?,?,?,?,?,?)""", rides)

# SELECT ... WHERE ... ORDER BY ... LIMIT
cheap = db.execute("SELECT id, fare_cents FROM rides WHERE fare_cents < ? ORDER BY fare_cents LIMIT 2", (1000,))
assert [tuple(r) for r in cheap] == [("r4", 550), ("r1", 925)]

# UPDATE and DELETE always need a WHERE (or they change every row!)
db.execute("UPDATE rides SET status = 'cancelled' WHERE id = ?", ("r4",))
db.execute("DELETE FROM rides WHERE status = 'cancelled' AND driver_id IS NULL")
assert db.execute("SELECT COUNT(*) FROM rides").fetchone()[0] == 3
~~~

### JOINs

`INNER JOIN` keeps rows that match in both tables; `LEFT JOIN` keeps every row of the left table and fills NULL where there is no match.

~~~python
inner = db.execute("""SELECT d.name, r.id FROM drivers d JOIN rides r ON r.driver_id = d.id
                      ORDER BY d.name, r.id""").fetchall()
left = db.execute("""SELECT d.name, r.id FROM drivers d LEFT JOIN rides r ON r.driver_id = d.id
                     ORDER BY d.name, r.id""").fetchall()
assert [tuple(r) for r in inner] == [("Ava", "r1"), ("Ava", "r2"), ("Sam", "r3")]
assert [tuple(r) for r in left] == [("Ava", "r1"), ("Ava", "r2"), ("Orla", None), ("Sam", "r3")]
~~~

| INNER JOIN result | | LEFT JOIN result | |
|---|---|---|---|
| Ava | r1 | Ava | r1 |
| Ava | r2 | Ava | r2 |
| Sam | r3 | **Orla** | **NULL** |
| | | Sam | r3 |

### Aggregation

~~~python
per_driver = db.execute("""SELECT d.name, COUNT(r.id) AS rides, SUM(r.fare_cents) AS cents
                           FROM drivers d LEFT JOIN rides r ON r.driver_id = d.id
                           GROUP BY d.id HAVING COUNT(r.id) > 0 ORDER BY rides DESC""").fetchall()
assert [tuple(r) for r in per_driver] == [("Ava", 2, 2375), ("Sam", 1, 925)]
by_status = dict(db.execute("SELECT status, COUNT(*) FROM rides GROUP BY status").fetchall())
assert by_status == {"assigned": 1, "completed": 2}
~~~

`WHERE` filters rows **before** grouping; `HAVING` filters groups **after**. `COUNT`, `SUM`, `AVG`, `MIN`, `MAX` are aggregate functions. The teaching app's `GET /api/stats` runs both queries above; experiment **W13** charts the per-driver counts.

### Indexes

An **index** is a sorted structure (a B-tree) over one or more columns, so the database can **search** instead of **scanning** every row — the same idea as binary search in the [DSA course](DATA_STRUCTURES_ALGORITHMS.md). It costs disk space and slows writes slightly.

~~~python
plan = db.execute("EXPLAIN QUERY PLAN SELECT * FROM rides WHERE status = 'completed'").fetchall()
print(plan[0][-1])                     # SEARCH rides USING INDEX idx_rides_status (status=?)
~~~

**Experiment W11** times the same query on 1 000 → 200 000 rows with and without the index: the scan grows linearly, the indexed search stays almost flat, and `EXPLAIN QUERY PLAN` changes from `SCAN rides` to `SEARCH rides USING INDEX`.

### SQL injection — and the one rule that prevents it

Building SQL by **gluing strings** lets the input become part of the command:

~~~python
status = "x' OR '1'='1"                                                   # typed by an attacker
unsafe = f"SELECT * FROM rides WHERE status = '{status}'"                  # NEVER do this
print(unsafe)                     # SELECT * FROM rides WHERE status = 'x' OR '1'='1'
assert len(db.execute(unsafe).fetchall()) == 3                             # every row leaks
safe = db.execute("SELECT * FROM rides WHERE status = ?", (status,)).fetchall()
assert safe == []                                                          # just an odd status
~~~

**Always pass values as parameters** (`?` in sqlite3, `%s` in psycopg) — the driver sends them separately from the SQL text, so they can never change its structure. Experiment **W10** compares four attack strings; the teaching app's integration test stores `x'); DROP TABLE rides; --` as an ordinary pickup name.

### 16.1 A richer practice database

The remaining sections use eight rides so that every query has something to find. Run this block first; it uses the teaching app's real `SCHEMA`, and the fare is computed by SQL itself.

~~~python
import sqlite3
from web_lab.app import SCHEMA

def demo_db():
    db = sqlite3.connect(":memory:")
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript(SCHEMA)
    db.executemany("INSERT INTO drivers(name, zone, rating, online) VALUES (?, ?, ?, ?)",
                   [("Ava", "Mardyke", 4.9, 1), ("Sam", "Grand Parade", 4.7, 1), ("Orla", "Douglas", 4.8, 0)])
    rows = [("r1", "Aoife",   "UCC",          "Kent Station", 4.5,  "completed", 1,    "2026-11-02T08:10:00Z"),
            ("r2", "Brian",   "UCC",          "Cork Airport", 8.0,  "completed", 1,    "2026-11-02T09:00:00Z"),
            ("r3", "Ciara",   "Kent Station", "UCC",          4.5,  "completed", 2,    "2026-11-03T17:30:00Z"),
            ("r4", "Dara",    "Grand Parade", "UCC",          2.0,  "assigned",  2,    "2026-11-04T12:00:00Z"),
            ("r5", "Eimear",  "UCC",          "Douglas",      5.5,  "cancelled", None, "2026-11-05T07:45:00Z"),
            ("r6", "Finn",    "Cork Airport", "Grand Parade", 9.0,  "completed", 1,    "2026-11-06T22:15:00Z"),
            ("r7", "Gráinne", "UCC",          "Kent Station", 4.5,  "requested", None, "2026-11-07T10:05:00Z"),
            ("r8", "Aoife",   "Kent Station", "Cork Airport", 10.5, "completed", 2,    "2026-11-08T06:30:00Z")]
    db.executemany("""INSERT INTO rides(id, passenger, pickup, destination, distance_km, fare_cents,
                                        status, request_key, driver_id, created_at)
                      VALUES (?1, ?2, ?3, ?4, ?5, CAST(ROUND(250 + 150 * ?5) AS INTEGER), ?6, 'key-' || ?1, ?7, ?8)""",
                   rows)
    return db

db = demo_db()
q = lambda sql, *params: [tuple(row) for row in db.execute(sql, params)]    # run a query, return plain tuples
assert q("SELECT id, fare_cents FROM rides WHERE id IN ('r4', 'r8')") == [("r4", 550), ("r8", 1825)]
~~~

### 16.2 The order a SELECT is evaluated in

You **write** a query in one order but the database **evaluates** it in another. Most "why doesn't this work?" questions are answered by this diagram.

~~~mermaid
flowchart LR
 F["1 FROM / JOIN<br/>which rows exist"] --> W["2 WHERE<br/>keep rows"] --> G["3 GROUP BY<br/>make groups"] --> H["4 HAVING<br/>keep groups"] --> S["5 SELECT<br/>compute columns, aliases"] --> DI["6 DISTINCT"] --> O["7 ORDER BY<br/>sort"] --> L["8 LIMIT / OFFSET"]
~~~

Consequences: an alias made in `SELECT` cannot be used in `WHERE` (it does not exist yet) but can be used in `ORDER BY`; an aggregate such as `COUNT(*)` cannot appear in `WHERE` (groups do not exist yet) — that is what `HAVING` is for.

~~~python
assert q("""SELECT pickup, COUNT(*) AS n, AVG(fare_cents) AS avg_cents
            FROM rides
            WHERE status <> 'cancelled'          -- 2: rows
            GROUP BY pickup                      -- 3: groups
            HAVING COUNT(*) >= 2                 -- 4: groups
            ORDER BY avg_cents DESC              -- 7: the alias is visible here""") \
    == [("Kent Station", 2, 1375.0), ("UCC", 3, 1100.0)]
~~~

### 16.3 Filtering, expressions and functions

| Operator | Example | Matches |
|---|---|---|
| `=`, `<>` (or `!=`), `<`, `<=`, `>`, `>=` | `fare_cents >= 1000` | comparisons |
| `BETWEEN a AND b` | `distance_km BETWEEN 4 AND 6` | inclusive range |
| `IN (…)` | `status IN ('assigned', 'requested')` | any listed value |
| `LIKE` | `pickup LIKE 'Ken%'`, `code LIKE 'R_'` | `%` any characters, `_` exactly one (case-insensitive for ASCII in SQLite) |
| `IS NULL`, `IS NOT NULL` | `driver_id IS NULL` | missing values — **never** `= NULL` |
| `AND`, `OR`, `NOT` | `a OR b AND c` means `a OR (b AND c)` | use brackets to be clear |

~~~python
assert q("SELECT id FROM rides WHERE pickup LIKE 'Ken%' OR destination LIKE '%Airport' ORDER BY id") \
    == [("r2",), ("r3",), ("r8",)]
assert q("SELECT DISTINCT pickup FROM rides ORDER BY pickup") \
    == [("Cork Airport",), ("Grand Parade",), ("Kent Station",), ("UCC",)]

# CASE: if/else inside a query
assert q("""SELECT id, CASE WHEN distance_km < 3  THEN 'short'
                            WHEN distance_km <= 6 THEN 'medium'
                            ELSE 'long' END AS band
            FROM rides WHERE id IN ('r4', 'r5', 'r6') ORDER BY id""") \
    == [("r4", "short"), ("r5", "medium"), ("r6", "long")]

# Useful built-in functions
assert q("""SELECT UPPER(pickup), LENGTH(passenger), ROUND(fare_cents / 100.0, 2),
                   COALESCE(driver_id, 0), date(created_at), strftime('%H', created_at)
            FROM rides WHERE id = 'r5'""") \
    == [("UCC", 6, 10.75, 0, "2026-11-05", "07")]

# Integer division is a classic trap: 7 / 2 is 3 for two integers
assert q("SELECT 7 / 2, 7 / 2.0, 7 % 2") == [(3, 3.5, 1)]
~~~

### 16.4 NULL and three-valued logic

`NULL` means "unknown". Any comparison with an unknown is itself unknown, and `WHERE` keeps only rows that are definitely **true**.

| Expression | Result |
|---|---|
| `NULL = NULL` | `NULL` (not true!) |
| `NULL IS NULL` | `1` (true) |
| `1 + NULL`, `'a' \|\| NULL` | `NULL` |
| `COUNT(*)` vs `COUNT(col)` | all rows vs rows where `col` is not NULL |
| `COALESCE(x, y, …)` | the first non-NULL argument |

~~~python
assert q("SELECT NULL = NULL, NULL IS NULL, 1 + NULL, COALESCE(NULL, 'none')") == [(None, 1, None, "none")]
assert q("SELECT COUNT(*), COUNT(driver_id), COUNT(DISTINCT passenger) FROM rides") == [(8, 6, 7)]

# The NOT IN trap: one NULL in the list makes every comparison unknown, so NOTHING is returned
assert q("SELECT name FROM drivers WHERE id NOT IN (SELECT driver_id FROM rides)") == []
# Fixes: exclude the NULLs, or (better) use NOT EXISTS
assert q("SELECT name FROM drivers WHERE id NOT IN (SELECT driver_id FROM rides WHERE driver_id IS NOT NULL)") == [("Orla",)]
assert q("""SELECT d.name FROM drivers d
            WHERE NOT EXISTS (SELECT 1 FROM rides r WHERE r.driver_id = d.id)""") == [("Orla",)]
~~~

### 16.5 Subqueries and common table expressions

A **subquery** is a query inside another. A **CTE** (`WITH name AS (…)`) gives a subquery a name, so a long query reads top to bottom like a sequence of steps.

~~~python
# scalar subquery: compare with a single computed value
assert q("""SELECT id FROM rides
            WHERE fare_cents > (SELECT AVG(fare_cents) FROM rides) ORDER BY id""") == [("r2",), ("r6",), ("r8",)]

# CTE: step 1 earnings per driver, step 2 attach names
assert q("""WITH earnings AS (
                SELECT driver_id, SUM(fare_cents) AS cents, COUNT(*) AS trips
                FROM rides WHERE status = 'completed' GROUP BY driver_id)
            SELECT d.name, e.trips, e.cents
            FROM earnings e JOIN drivers d ON d.id = e.driver_id
            ORDER BY e.cents DESC""") == [("Ava", 3, 3975), ("Sam", 2, 2750)]

# correlated subquery: re-evaluated for each outer row
assert q("""SELECT d.name, (SELECT COUNT(*) FROM rides r WHERE r.driver_id = d.id) AS rides
            FROM drivers d ORDER BY d.id""") == [("Ava", 3), ("Sam", 3), ("Orla", 0)]
~~~

### 16.6 More kinds of join

~~~mermaid
flowchart LR
 subgraph I["INNER JOIN"]
  i1["only matching pairs"]
 end
 subgraph LJ["LEFT JOIN"]
  l1["all left rows<br/>+ matches or NULL"]
 end
 subgraph FJ["FULL OUTER JOIN"]
  f1["all rows of both<br/>NULL where unmatched"]
 end
 subgraph X["CROSS JOIN"]
  x1["every left row ×<br/>every right row"]
 end
~~~

| Join | Keeps | Typical question |
|---|---|---|
| `INNER JOIN … ON` | matching pairs only | rides *with* their driver |
| `LEFT JOIN` | every left row | every driver, with rides if any |
| `RIGHT JOIN` | every right row | (write it as a LEFT JOIN with the tables swapped) |
| `FULL OUTER JOIN` | every row of both | reconcile two lists |
| `CROSS JOIN` | every combination | a timetable of every zone × every hour |
| **self join** | a table joined to itself | passengers who booked twice |
| **anti join** (`NOT EXISTS` / `LEFT JOIN … WHERE right.id IS NULL`) | left rows with **no** match | drivers with no rides |

~~~python
# self join: pairs of rides by the same passenger (a.id < b.id avoids duplicates and self-pairs)
assert q("""SELECT a.passenger, a.id, b.id
            FROM rides a JOIN rides b ON a.passenger = b.passenger AND a.id < b.id""") == [("Aoife", "r1", "r8")]

# CROSS JOIN: every online driver × every status, then count (zero rows appear as 0 thanks to LEFT JOIN)
grid = q("""SELECT d.name, s.status, COUNT(r.id)
            FROM drivers d
            CROSS JOIN (SELECT DISTINCT status FROM rides) s
            LEFT JOIN rides r ON r.driver_id = d.id AND r.status = s.status
            WHERE d.online = 1
            GROUP BY d.name, s.status ORDER BY d.name, s.status""")
assert len(grid) == 2 * 4 and ("Sam", "assigned", 1) in grid and ("Ava", "assigned", 0) in grid
~~~

### 16.7 Set operations

| Operator | Result | Duplicates |
|---|---|---|
| `UNION` | rows in either query | removed |
| `UNION ALL` | rows in either query | kept (faster: no de-duplication) |
| `INTERSECT` | rows in both | removed |
| `EXCEPT` | rows in the first but not the second | removed |

Both queries must return the same number of columns with compatible types.

~~~python
assert q("SELECT pickup FROM rides UNION SELECT destination FROM rides ORDER BY 1") \
    == [("Cork Airport",), ("Douglas",), ("Grand Parade",), ("Kent Station",), ("UCC",)]
assert q("SELECT COUNT(*) FROM (SELECT pickup FROM rides UNION ALL SELECT destination FROM rides)") == [(16,)]
assert q("SELECT destination FROM rides EXCEPT SELECT pickup FROM rides") == [("Douglas",)]   # never a pickup
~~~

### 16.8 Window functions: aggregates without collapsing rows

`GROUP BY` turns many rows into one per group. A **window function** computes over a group (the *window*) but keeps every row — perfect for rankings, running totals and comparisons with the previous row.

~~~python
assert q("""SELECT d.name, r.id, r.fare_cents,
                   RANK()          OVER (PARTITION BY d.id ORDER BY r.fare_cents DESC) AS rank_for_driver,
                   SUM(r.fare_cents) OVER (PARTITION BY d.id ORDER BY r.created_at)    AS running_total
            FROM rides r JOIN drivers d ON d.id = r.driver_id
            WHERE r.status = 'completed'
            ORDER BY d.name, r.created_at""") == [
    ("Ava", "r1", 925, 3, 925), ("Ava", "r2", 1450, 2, 2375), ("Ava", "r6", 1600, 1, 3975),
    ("Sam", "r3", 925, 2, 925), ("Sam", "r8", 1825, 1, 2750)]

assert q("""SELECT id, ROW_NUMBER() OVER (ORDER BY created_at) AS n,
                   fare_cents - LAG(fare_cents) OVER (ORDER BY created_at) AS change
            FROM rides ORDER BY created_at LIMIT 3""") == [("r1", 1, None), ("r2", 2, 525), ("r3", 3, -525)]
~~~

| Function | Gives |
|---|---|
| `ROW_NUMBER()` | 1, 2, 3 … with no ties |
| `RANK()` / `DENSE_RANK()` | ties share a rank; `RANK` then skips (1, 1, 3), `DENSE_RANK` does not (1, 1, 2) |
| `LAG(col)` / `LEAD(col)` | the previous / next row's value |
| `SUM`, `AVG`, `COUNT` … `OVER (…)` | running or per-group totals alongside each row |
| `PARTITION BY` | restart the window for each group (like `GROUP BY`, without collapsing) |

### 16.9 Writing data: multi-row inserts, upserts and `RETURNING`

~~~python
# UPSERT: insert, or update the existing row if the unique key already exists
db.execute("""INSERT INTO drivers(name, zone, rating, online) VALUES ('Sam', 'Ballincollig', 4.8, 1)
              ON CONFLICT(name) DO UPDATE SET zone = excluded.zone, rating = excluded.rating""")
assert q("SELECT zone, rating FROM drivers WHERE name = 'Sam'") == [("Ballincollig", 4.8)]

# RETURNING: get generated values back without a second query
new_id = db.execute("INSERT INTO drivers(name, zone, rating, online) VALUES ('Niamh', 'Blackrock', 5, 1) RETURNING id").fetchone()[0]
assert q("SELECT name FROM drivers WHERE id = ?", new_id) == [("Niamh",)]
# (the id is 5, not 4: the upsert above used up a sequence number — ids can have gaps, never rely on them)

# UPDATE with a condition that protects against races (Lesson 17, exercise 2)
changed = db.execute("UPDATE rides SET status = 'assigned', driver_id = ? WHERE id = 'r7' AND status = 'requested'",
                     (new_id,)).rowcount
assert changed == 1
assert db.execute("UPDATE rides SET driver_id = 1 WHERE id = 'r7' AND status = 'requested'").rowcount == 0   # too late
~~~

**Exercises.** (1) Average fare per pickup place, only places with ≥ 2 rides. (2) Which rides have no driver? Write it with `LEFT JOIN … WHERE d.id IS NULL` and with `WHERE driver_id IS NULL`. (3) Add an index for "a driver's rides, newest first" and confirm it with `EXPLAIN QUERY PLAN`. (4) With the 16.1 database: the busiest hour of the day; each passenger's most expensive ride (use a window function); and drivers whose average fare is above the overall average (use a CTE). (5) Rewrite the 16.4 `NOT EXISTS` query as a `LEFT JOIN … IS NULL` anti-join and confirm both give the same answer.

## Lesson 17 — Transactions, concurrency and Python with SQLite

**Idea.** A **transaction** groups statements that must succeed or fail **together**. Its guarantees are **ACID**:

| Letter | Guarantee | Example |
|---|---|---|
| Atomicity | all or nothing | debit and credit both happen, or neither |
| Consistency | constraints hold before and after | no ride with `fare_cents < 0` |
| Isolation | concurrent transactions do not see each other's half-done work | two bookings with the same key |
| Durability | once committed, it survives a crash | the ride is still there after a power cut |

~~~mermaid
sequenceDiagram
 participant App
 participant DB
 App->>DB: BEGIN
 App->>DB: UPDATE ledger SET cents = cents - 550 WHERE account = 'pending'
 Note over App: crash / exception here
 App->>DB: ROLLBACK
 Note over DB: the first UPDATE is undone — the money is not lost
~~~

~~~python
import sqlite3
db = sqlite3.connect(":memory:", isolation_level=None)          # autocommit unless we BEGIN
db.execute("CREATE TABLE ledger(account TEXT PRIMARY KEY, cents INTEGER NOT NULL CHECK(cents >= 0))")
db.executemany("INSERT INTO ledger VALUES (?, ?)", [("pending", 1000), ("paid", 0)])

def pay(amount, crash=False):
    db.execute("BEGIN")
    try:
        db.execute("UPDATE ledger SET cents = cents - ? WHERE account = 'pending'", (amount,))
        if crash:
            raise RuntimeError("power cut")
        db.execute("UPDATE ledger SET cents = cents + ? WHERE account = 'paid'", (amount,))
        db.execute("COMMIT")
    except Exception:
        db.execute("ROLLBACK")
        raise

pay(300)
try:
    pay(300, crash=True)
except RuntimeError:
    pass
try:
    pay(5000)                                        # would make 'pending' negative: CHECK fails
except sqlite3.IntegrityError:
    pass
assert dict(db.execute("SELECT * FROM ledger")) == {"pending": 700, "paid": 300}
~~~

**Experiment W12** repeats the two-step update 100 times, crashing between the steps in half of the runs: without a transaction 50 ledgers lose money; with `BEGIN … COMMIT/ROLLBACK`, none do.

**In the teaching app** every request uses the `connection()` context manager: Python's `sqlite3` opens a transaction automatically before the first change; the manager calls `commit()` if the request succeeds and `rollback()` if any exception escapes. Each request gets its own connection, so one request's error cannot affect another.

**Concurrency and races.** Two requests can interleave: both check "is this idempotency key new?", both see "yes", both insert. The `UNIQUE(request_key)` constraint makes the database reject the second insert, and the app turns that `IntegrityError` into 409. **Rule: enforce invariants in the database, not only in application code.** Experiment W09 and the test `test_concurrent_retries_create_one_row` verify it.

**SQLite vs a server database.** SQLite is a library writing one file: perfect for learning, phones (ATLAS Go could use it) and small sites; one writer at a time. PostgreSQL/MySQL are separate servers for many concurrent users, with users/permissions, replication and richer types. The ATLAS starter's [`db.py`](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/packages/db.py) supports both behind one interface.

### 17.1 What can go wrong without isolation

| Anomaly | What happens | Prevented at isolation level |
|---|---|---|
| **dirty read** | T1 reads T2's change before T2 commits; T2 then rolls back | Read Committed and above |
| **non-repeatable read** | T1 reads a row twice and gets different values because T2 committed in between | Repeatable Read and above |
| **phantom** | T1 runs the same `WHERE` twice and new rows appear | Serializable (and PostgreSQL's Repeatable Read) |
| **lost update** | T1 and T2 both read 5, both write 5 + 1 = 6 — one increment disappears | Serializable, row locks, or a guarded `UPDATE` |

PostgreSQL defaults to **Read Committed**; SQLite gives **serializable** behaviour by allowing only one writer at a time. Whatever the level, the simplest defence against lost updates is to do the arithmetic **in** the database (`SET seats = seats - 1 WHERE seats > 0`) or to guard the change with the state you expect (`WHERE status = 'requested'`, Lesson 16.9) and check `rowcount`.

### 17.2 Optimistic concurrency with a version number

When two people edit the same record in a web form, neither should silently overwrite the other. Store a version and require it on update — HTTP expresses the same idea with `ETag` and `If-Match` (Lesson 21).

~~~python
import sqlite3
db = sqlite3.connect(":memory:")
db.execute("CREATE TABLE drivers(id INTEGER PRIMARY KEY, zone TEXT, version INTEGER NOT NULL DEFAULT 1)")
db.execute("INSERT INTO drivers(id, zone) VALUES (1, 'Mardyke')")

def save_zone(driver_id, zone, version_seen):
    cur = db.execute("UPDATE drivers SET zone = ?, version = version + 1 WHERE id = ? AND version = ?",
                     (zone, driver_id, version_seen))
    if cur.rowcount == 0:
        raise RuntimeError("409 Conflict: someone else changed this driver; reload and try again")

version = db.execute("SELECT version FROM drivers WHERE id = 1").fetchone()[0]   # both editors load version 1
save_zone(1, "Douglas", version)                                                  # editor A saves first: OK
try:
    save_zone(1, "Blackrock", version)                                            # editor B's copy is stale
except RuntimeError as error:
    print(error)
assert db.execute("SELECT zone, version FROM drivers").fetchone() == ("Douglas", 2)
~~~

### 17.3 Savepoints: a transaction inside a transaction

~~~python
import sqlite3
db = sqlite3.connect(":memory:", isolation_level=None)
db.execute("CREATE TABLE log(line TEXT NOT NULL)")
db.execute("BEGIN")
db.execute("INSERT INTO log VALUES ('booking received')")
db.execute("SAVEPOINT promo")
try:
    db.execute("INSERT INTO log VALUES (NULL)")          # applying the promotion fails (NOT NULL)
except sqlite3.IntegrityError:
    db.execute("ROLLBACK TO promo")                      # undo only the promotion step
db.execute("INSERT INTO log VALUES ('booked without promotion')")
db.execute("COMMIT")
assert [r[0] for r in db.execute("SELECT line FROM log")] == ["booking received", "booked without promotion"]
~~~

### 17.4 Good habits with database connections in Python

| Habit | Why |
|---|---|
| one connection (or one pooled connection) per request, closed afterwards | errors in one request cannot leave another in a half-finished transaction |
| `with` blocks / context managers for commit and rollback | no forgotten `commit()`; rollback happens even on an unexpected exception |
| parameters (`?`) for every value | SQL injection is impossible (Lesson 16) |
| `PRAGMA foreign_keys=ON` (SQLite) straight after connecting | otherwise foreign keys are not enforced (Lesson 15.4) |
| `row_factory = sqlite3.Row` | columns by name (`row["fare_cents"]`) and easy `dict(row)` for JSON |
| keep transactions short; never wait for a user or a network call inside one | locks are held until `COMMIT` |
| let the database enforce invariants (`UNIQUE`, `CHECK`, `FOREIGN KEY`) and translate `IntegrityError` into 409/422 | application checks alone lose races |

**Exercises.** (1) Make "assign driver" also set the driver offline in the same transaction. (2) What goes wrong if two drivers accept the same ride at the same moment, and how would a `WHERE status = 'requested'` in the UPDATE fix it? (3) Add a `version` column to `rides` and make `PATCH /api/rides/{id}` require `If-Match`, returning 412 Precondition Failed for a stale version. (4) Which isolation anomaly does experiment W09 guard against, and which database feature does the guarding?

---

# Part IV — Full stack

## Lesson 18 — Putting it together: one request through every layer

~~~mermaid
sequenceDiagram
 actor U as User
 participant H as HTML form (index.html)
 participant J as JavaScript (app.js)
 participant F as FastAPI (app.py)
 participant P as Pydantic
 participant D as SQLite
 U->>H: types fields, presses "Book"
 H->>J: submit event
 J->>J: preventDefault() · FormData → object · add request_key
 J->>F: POST /api/rides  Content-Type: application/json
 F->>P: validate body (RideCreate)
 P-->>F: 422 with field errors ✗  or  clean data ✓
 F->>D: BEGIN · SELECT by request_key · INSERT ... (?, ?, ...) · COMMIT
 D-->>F: new row
 F-->>J: 201 Created + JSON (+ security headers)
 J->>J: response.ok? show message
 J->>F: GET /api/drivers, then GET /api/rides + GET /api/stats in parallel
 F->>D: SELECT ... LEFT JOIN drivers ... LIMIT 20 / GROUP BY status
 F-->>J: 200 + JSON (+ X-Total-Count, ETag)
 J->>H: build cards with createElement/textContent
 H-->>U: updated list and summary
~~~

**Where does each rule live?**

| Rule | Browser | API | Database |
|---|---|---|---|
| field is required | `required` (convenience) | Pydantic `min_length=1` | `NOT NULL` |
| distance 0–200 km | `min`/`max` | `Field(gt=0, le=200)` | `CHECK` |
| pickup ≠ destination | — | `model_validator` | — |
| no duplicate booking | one `request_key` per submit | look-up before insert | `UNIQUE(request_key)` |
| legal state change | only shows legal buttons | `TRANSITIONS` table → 409 | `CHECK(status IN ...)` |
| driver exists | dropdown from `/api/drivers` | 404 if missing | `FOREIGN KEY` |

The browser shows the rule for convenience; the **server** and **database** enforce it.

### Same-origin policy and CORS

Browsers let a page read responses only from its **own origin** (scheme + host + port). The teaching page and API share `http://127.0.0.1:8000`, so no extra work is needed. A separate front-end dev server (e.g. Vite on `http://localhost:5173`) is a different origin; the API must opt in with **CORS** headers. For non-simple requests (JSON POST, PATCH, DELETE) the browser first sends an **OPTIONS preflight**:

~~~mermaid
sequenceDiagram
 participant B as Page on http://localhost:5173
 participant A as API on http://127.0.0.1:8000
 B->>A: OPTIONS /api/rides  Origin: http://localhost:5173  Access-Control-Request-Method: POST
 A-->>B: 200  Access-Control-Allow-Origin: http://localhost:5173  Access-Control-Allow-Methods: GET, POST, PATCH, DELETE
 B->>A: POST /api/rides (the real request)
 A-->>B: 201 + Access-Control-Allow-Origin
~~~

The teaching app allows exactly one development origin (`WEB_LAB_ORIGINS`, default `http://localhost:5173`); experiment **W16** shows the preflight from that origin accepted and one from `https://evil.example` refused. **CORS is not authentication** — it only controls which web pages may *read* responses in a browser; `curl` ignores it.

**Exercises.** (1) Follow one booking in DevTools → Network and match each request to a row of the sequence diagram. (2) Serve `index.html` from `python -m http.server 5173` and make it call the API on port 8000.

## Lesson 19 — State: cookies, sessions, tokens, authentication and authorisation

**Idea.** HTTP is stateless, so "who is this?" must travel with every request. **Authentication** (authn) proves *who* you are; **authorisation** (authz) decides *what you may do*. They are different checks — a signed-in passenger must still be forbidden from cancelling someone else's ride.

| Mechanism | How it works | Watch out for |
|---|---|---|
| **Session cookie** | after login the server stores a session and sets `Set-Cookie: sid=<random>; HttpOnly; Secure; SameSite=Lax`; the browser sends it back automatically | CSRF (the browser also sends it on requests triggered by other sites) — `SameSite` and CSRF tokens prevent it |
| **Bearer token** (e.g. JWT) | the client stores a signed token and sends `Authorization: Bearer <token>` | where to store it (XSS can steal tokens from `localStorage`); expiry and revocation |
| **OAuth 2 / OpenID Connect** | log in with an identity provider (Google, university SSO) | redirect URIs, PKCE |

~~~mermaid
sequenceDiagram
 participant B as Browser
 participant S as Server
 B->>S: POST /login {email, password}
 S->>S: verify PBKDF2 hash · create session sid=7f3a…
 S-->>B: 200  Set-Cookie: sid=7f3a… · HttpOnly · Secure · SameSite=Lax
 B->>S: GET /api/my-rides  Cookie: sid=7f3a…
 S->>S: look up session → user 42 · authorise: rides WHERE passenger_id = 42
 S-->>B: 200 (only user 42's rides)
~~~

A minimal, runnable illustration of a **signed** token and an authorisation dependency (teaching code — use a maintained library and HTTPS in real systems):

~~~python
import hashlib, hmac, base64, json, time
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.testclient import TestClient

SECRET = b"demo-secret-for-teaching-only"          # real secrets come from configuration, never source code

def sign(payload: dict) -> str:
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
    mac = hmac.new(SECRET, body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{mac}"

def verify(token: str) -> dict:
    body, _, mac = token.partition(".")
    expected = hmac.new(SECRET, body.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(mac, expected):       # constant-time comparison
        raise HTTPException(401, "bad token")
    data = json.loads(base64.urlsafe_b64decode(body))
    if data["exp"] < time.time():
        raise HTTPException(401, "token expired")
    return data

def current_user(authorization: str = Header(default="")) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "login required", headers={"WWW-Authenticate": "Bearer"})
    return verify(authorization.removeprefix("Bearer "))

app = FastAPI()
RIDES = {"r1": {"owner": "alice"}, "r2": {"owner": "bob"}}

@app.delete("/rides/{ride_id}", status_code=204)
def cancel(ride_id: str, user: dict = Depends(current_user)):
    if RIDES[ride_id]["owner"] != user["sub"]:       # authorisation: authenticated is not enough
        raise HTTPException(403, "not your ride")

client = TestClient(app)
alice = sign({"sub": "alice", "exp": time.time() + 600})
tampered = alice[:-1] + ("0" if alice[-1] != "0" else "1")
assert client.delete("/rides/r1").status_code == 401                                        # no token
assert client.delete("/rides/r1", headers={"Authorization": f"Bearer {tampered}"}).status_code == 401
assert client.delete("/rides/r2", headers={"Authorization": f"Bearer {alice}"}).status_code == 403
assert client.delete("/rides/r1", headers={"Authorization": f"Bearer {alice}"}).status_code == 204
~~~

**Passwords** are never stored — only a slow, salted hash (PBKDF2, bcrypt, Argon2). ATLAS Go does exactly that in [`accounts.hash_password`](https://github.com/FUllSCIPTS/ATLAS/blob/main/android-app/atlas_go/accounts.py); the [Information Security course](INFORMATION_SECURITY.md) covers password storage, lockout, SSO and Kerberos in depth.

**The teaching app has no login on purpose** — it is a single-user local demo. The capstone asks you to add one.

**Exercises.** (1) Add an expiry test for the token above. (2) Explain why `SameSite=Lax` stops a malicious page from POSTing to `/api/rides` with your cookie.

## Lesson 20 — Web security: OWASP Top 10 in practice

The **OWASP Top 10** lists the most common serious web risks. Here is each one, with what the teaching app does and what a real deployment would need.

| Risk | What goes wrong | In the teaching app | Real systems also need |
|---|---|---|---|
| A01 Broken access control | users reach data that is not theirs | *not addressed: no users* (Lesson 19 shows the pattern) | per-record authorisation checks |
| A02 Cryptographic failures | plaintext traffic or passwords | local HTTP only | HTTPS + HSTS, hashed passwords |
| A03 Injection (SQL, XSS) | input becomes code | `?` parameters everywhere (W10); `textContent` only (W06) | the same, plus output encoding in templates |
| A04 Insecure design | missing business rules | state machine, idempotency, constraints | threat modelling |
| A05 Security misconfiguration | debug pages, permissive CORS | CORS for one dev origin; security headers (W16) | review of every header and default |
| A06 Vulnerable components | old libraries | version ranges in `requirements.txt` | `pip-audit`, Dependabot |
| A07 Identification and authentication failures | weak login, no lockout | *no login* | MFA, lockout, secure sessions |
| A08 Software and data integrity failures | unsigned updates | — | signed releases (see the Cryptography course) |
| A09 Logging and monitoring failures | attacks go unnoticed | `Server-Timing` only | structured logs, alerts |
| A10 Server-side request forgery | server fetches attacker URLs | the app fetches no URLs | allow-lists for outbound requests |

**The security headers the teaching app sends on every response** (middleware in `app.py`):

| Header | Value | Protects against |
|---|---|---|
| `Content-Security-Policy` | `default-src 'self'; img-src 'self' data:; object-src 'none'; frame-ancestors 'none'` | XSS: scripts only from this site, no inline handlers, no `eval` |
| `X-Content-Type-Options` | `nosniff` | browsers guessing a file is a script |
| `X-Frame-Options` | `DENY` | click-jacking inside an invisible frame |
| `Referrer-Policy` | `no-referrer` | leaking URLs to other sites |

*A side effect worth knowing:* the strict CSP also blocks `eval`, so browser-automation code that evaluates strings fails on this page — the W19 experiment waits for CSS selectors instead.

**Defence in depth.** Experiment W06 shows two layers stopping the same XSS payload: safe DOM APIs, and — when a bug bypasses them — the CSP.

**Exercises.** (1) Remove the CSP header, repeat W06, and record what changes. (2) Add rate limiting (e.g. at most 10 bookings per minute per client) and a test for it.

## Lesson 21 — Performance: caching, pagination and load

**Measure first.** DevTools → Network shows each request's time split (DNS, connect, TLS, waiting for the server = *time to first byte*, download). `Server-Timing: app;dur=1.42` (sent by the teaching app) shows how long the Python code took.

**Pagination.** Never return an unbounded list. The teaching API takes `limit` (1–200, default 50) and `offset`, returns `X-Total-Count`, and the page shows "Load more". Experiment **W14**: response size grows linearly with the page size.

~~~mermaid
flowchart LR
 Q["GET /api/rides?limit=20&offset=40"] --> R["rows 41–60, newest first"]
 R --> H["X-Total-Count: 400 → 20 pages"]
~~~

(Offset paging gets slow and can skip rows when data changes; large systems use **keyset paging**: `WHERE created_at < :last_seen ORDER BY created_at DESC LIMIT 20`.)

**HTTP caching with validators.** The server sends an **ETag** (a fingerprint of the response). The client repeats the request with `If-None-Match: <etag>`; if nothing changed the server replies **304 Not Modified** with an empty body.

~~~mermaid
sequenceDiagram
 participant B as Browser
 participant S as Server
 B->>S: GET /api/rides
 S-->>B: 200 + body (13 KiB) + ETag: "a1b2…"
 B->>S: GET /api/rides  If-None-Match: "a1b2…"
 S-->>B: 304 Not Modified (0 bytes)
 Note over S: a ride is booked
 B->>S: GET /api/rides  If-None-Match: "a1b2…"
 S-->>B: 200 + new body + ETag: "c3d4…"
~~~

~~~python
from fastapi.testclient import TestClient
from web_lab.app import create_app
import tempfile, pathlib
with TestClient(create_app(pathlib.Path(tempfile.mkdtemp()) / "c.sqlite3")) as c:
    first = c.get("/api/rides")
    again = c.get("/api/rides", headers={"If-None-Match": first.headers["ETag"]})
    assert again.status_code == 304 and again.content == b""
~~~

`Cache-Control` sets the policy: `no-store` (never keep), `no-cache` (keep but revalidate — the teaching API), `max-age=3600` (fresh for an hour — good for versioned static files), `public`/`private`. **Experiment W15** walks through the sequence above.

**Other levers.** Database indexes (W11); fewer requests (combine, or `Promise.all` in parallel); compression (`gzip`/`br`); a CDN for static files; doing slow work in a background queue.

**Load.** **Latency** is the time per request; **throughput** is requests per second. **W17** measures latency as the table grows (in-process); **W18** fires 1–16 concurrent clients at a live Uvicorn server — throughput levels off at the single worker's capacity while median latency rises in proportion to the queue (Little's law: queue length = throughput × latency).

**Exercises.** (1) Implement keyset pagination and compare it with offset paging at offset 10 000. (2) Add `Cache-Control: max-age=31536000, immutable` to static files with a version in their file name.

## Lesson 22 — Testing web applications

~~~mermaid
flowchart BT
 U["unit tests<br/>fare_cents, specificity: milliseconds, hundreds"] --> I["API integration tests<br/>TestClient + temporary SQLite: 28 tests"]
 I --> E["browser end-to-end<br/>Playwright + Chromium: W05, W06, W19"]
 E --> M["manual and exploratory<br/>keyboard-only, screen reader, small screens"]
~~~

| Level | Tool | Example in the lab |
|---|---|---|
| unit | pytest | `test_fare_rounding` |
| API integration | FastAPI `TestClient` (in-process) + a temporary database per test | `test_full_lifecycle_with_driver_join`, `test_etag_conditional_get`, `test_cors_preflight` |
| concurrency | threads hitting the same endpoint | `test_concurrent_retries_create_one_row`, W09 |
| database rules | raw `sqlite3` against the app's file | `test_foreign_key_is_enforced_by_sqlite` |
| end-to-end | Playwright driving Chromium | W19 books, assigns, completes and deletes through the UI |
| accessibility | automated label check (W03) + Lighthouse + manual keyboard test | |
| security | injection strings, XSS payloads, header checks | W06, W10, W16 |

A Playwright end-to-end test reads like a user's actions:

~~~python
def booking_flow(page, base_url):
    page.goto(base_url + "/")
    page.fill("#pickup", "Grand Parade")
    page.click("button[type=submit]")
    page.wait_for_selector(".ride[data-status=requested]")
    page.click(".ride button:text('Assign')")
    page.wait_for_selector(".ride[data-status=assigned]")
    assert "driver" in page.inner_text(".ride p")

# Run it against a live server (needs: pip install playwright && python -m playwright install chromium):
#   from web_lab.experiments import browser_session
#   browser_session(lambda browser, base: booking_flow(browser.new_page(), base))
~~~

Run the suite with `python -m pytest -q web_lab/tests`. Each test gets a fresh temporary database through the `client` fixture, so tests never depend on each other or on your demo data. See [Python course Part II](PYTHON_PROGRAMMING.md#part-ii--software-testing-fundamentals-with-atlas-go) for testing fundamentals.

**Exercises.** (1) Write a test that pagination with `offset` beyond the total returns `[]`. (2) Write a Playwright test that the filter dropdown shows only completed rides.

## Lesson 23 — Deployment and architecture

**From laptop to server.**

| Concern | Development (this course) | Production |
|---|---|---|
| server | `uvicorn web_lab.app:app --reload` | several Uvicorn/Gunicorn workers behind a reverse proxy (nginx, Caddy) |
| transport | HTTP on 127.0.0.1 | HTTPS with automatic certificates (Let's Encrypt) |
| configuration | defaults in code | environment variables / secret store (`WEB_LAB_DB`, `WEB_LAB_ORIGINS`) |
| database | one SQLite file | PostgreSQL with backups, migrations (Alembic) |
| users | none | authentication, authorisation, rate limits |
| observability | console | structured logs, metrics, tracing, alerts |
| releases | edit and reload | CI tests → build image → deploy → health check → rollback plan |

~~~mermaid
flowchart LR
 C["Clients"] -->|HTTPS 443| P["Reverse proxy<br/>TLS, compression, static files"]
 P -->|HTTP| W1["Uvicorn worker 1"]
 P -->|HTTP| W2["Uvicorn worker 2"]
 W1 --> DB[("PostgreSQL")]
 W2 --> DB
 W1 --> Q["job queue"] --> WK["background worker"]
~~~

A container image packages the app with its exact dependencies:

~~~text
FROM python:3.12-slim
WORKDIR /srv
COPY web_lab/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY web_lab ./web_lab
ENV WEB_LAB_DB=/data/rides.sqlite3
EXPOSE 8000
CMD ["uvicorn", "web_lab.app:app", "--host", "0.0.0.0", "--port", "8000"]
~~~

**Monolith or microservices?** The teaching app is a **monolith**: one process, one database — simple to build, test and deploy. **Microservices** split features into separately deployed services that talk over the network: they scale and fail independently but add latency, partial failures and operational work. This trade-off is exactly what the ATLAS research project studies — ATLAS decides at run time which modules stay together and which run as separate services. The ATLAS server starter on the `architecture-explorer` branch has a gateway, trip and dispatch services, Kafka events and model components; see the [component and deployment boundaries](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/docs/UML_BLUEPRINT.md#component-and-deployment-boundaries) in the UML blueprint and the [ML and optimisation course](MACHINE_LEARNING_OPTIMISATION.md) for the coupling optimiser.

**ATLAS reference component map:**

| Layer | ATLAS starter file | UML section |
|---|---|---|
| HTML | [passenger/index.html](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/apps/passenger/index.html), [driver/index.html](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/apps/driver/index.html) | [Web front end](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/docs/UML_BLUEPRINT.md#web-front-end) |
| CSS | [shared/demo.css](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/apps/shared/demo.css) | Web front end |
| JavaScript | [shared/client.js](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/apps/shared/client.js) | [Generated symbol catalogue](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/docs/UML_BLUEPRINT.md#generated-symbol-catalog) |
| Gateway | [gateway.py](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/services/gateway.py) | [Component boundaries](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/docs/UML_BLUEPRINT.md#component-and-deployment-boundaries) |
| API | [trips.py](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/services/trips.py) | [Booking and dispatch types](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/docs/UML_BLUEPRINT.md#booking-and-dispatch-types) |
| Database | [db.py](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/packages/db.py), [schema.sql](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/infra/schema.sql) | [Persistence model](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/docs/UML_BLUEPRINT.md#persistence-model) |
| Android ↔ back end | — | [Connecting the Android app to the back end](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/docs/UML_BLUEPRINT.md#connecting-the-android-app-to-the-back-end) |

**Exercises.** (1) Build the container image and run it with a mounted `/data` volume. (2) List three things that break when you run two workers against one SQLite file, and how PostgreSQL avoids them.

---

# Part V — Practice

## Run the lab

~~~bash
git clone https://github.com/FUllSCIPTS/ATLAS.git && cd ATLAS
python -m pip install -r web_lab/requirements.txt
python -m uvicorn web_lab.app:app --reload          # http://127.0.0.1:8000  and  /docs
python -m pytest -q web_lab/tests                   # 28 integration tests
python -m playwright install chromium               # once, for W05, W06, W19
python -m web_lab.experiments --all                 # W01-W20 -> web_lab/results
~~~

**Suggested first hour:** open the page and DevTools side by side; book a ride and find the POST in the Network tab; read its request payload and response; open `/docs` and send an invalid booking from there; open `web_lab/data/demo.sqlite3` with `sqlite3` or DB Browser for SQLite and find your row; then read `index.html` → `style.css` → `app.js` → `app.py` in that order.

## The 20 experiments

| ID | Title | How it runs | What it shows | Lessons |
|---|---|---|---|---|
| W01 | HTTP message anatomy | raw TCP socket → live Uvicorn | header vs body bytes; the full raw exchange | 1, 3 |
| W02 | Status codes | TestClient | 200, 201, 204, 304, 404, 405, 409, 422 from real requests | 3, 13 |
| W03 | HTML as a tree | `html.parser` | element counts, nesting depth, label check | 5, 6, 9 |
| W04 | CSS specificity | parses `style.css` | specificity score per selector | 7 |
| W05 | Responsive layout | Chromium at 9 widths | grid columns and panel width vs viewport; screenshots | 8, 9 |
| W06 | XSS | Chromium | `textContent` safe; `innerHTML` runs without CSP, blocked with CSP | 11, 20 |
| W07 | Validation | TestClient | 422 for every invalid field; no bad row stored | 6, 14 |
| W08 | State machine | TestClient | 4 × 4 transition matrix of 200/409 | 13 |
| W09 | Concurrency and idempotency | threads → live server | 1 row for k simultaneous identical POSTs | 13, 17 |
| W10 | SQL injection | in-memory SQLite | rows returned by concatenated vs parameterised queries | 16 |
| W11 | Indexes | in-memory SQLite, up to 200 000 rows | scan vs index time; query plans | 16 |
| W12 | Transactions | in-memory SQLite | 100 trials: lost money without vs with a transaction | 17 |
| W13 | JOIN, GROUP BY, FK | TestClient + sqlite3 | rides per driver; LEFT JOIN NULL; FK violation | 15, 16 |
| W14 | Pagination | TestClient | bytes and time vs page size | 21 |
| W15 | ETag caching | TestClient | 200 / 304 sequence and bytes saved | 21 |
| W16 | CORS and headers | TestClient | header presence matrix; allowed vs refused origin | 18, 20 |
| W17 | Latency vs rows | TestClient | median and 95th percentile as the table grows | 21 |
| W18 | Throughput vs concurrency | threads → live server | requests/s and latency for 1–16 clients | 21, 23 |
| W19 | End-to-end UI flow | Chromium | time from click to updated DOM for six user steps; screenshots | 11, 12, 22 |
| W20 | Async waits | `asyncio` | sequential vs `gather` for 1–16 waits | 12 |

Each experiment writes `WNN.csv`, `WNN.json` and `WNN.png` (and screenshots for W05, W06, W19). Only W11, W14, W17–W20 report times; the others report counts, codes or sizes. Times depend on your machine — compare shapes, not exact values.

## 12-week teaching plan

| Week | Lessons | Lab work | Deliverable |
|---|---|---|---|
| 1 | 1–2 Internet, URLs, DNS | W01; DevTools tour | annotated raw HTTP exchange |
| 2 | 3–4 HTTP, TLS | W02 | status-code table for a site you use |
| 3 | 5–6 HTML, forms | W03 | accessible sign-up form |
| 4 | 7–8 CSS, layout | W04 | specificity puzzle; two-column page |
| 5 | 9 responsive, accessible | W05 | Lighthouse report before/after |
| 6 | 10–11 JavaScript, DOM | W06 | interactive page without `innerHTML` |
| 7 | 12 async, fetch | W20 | page that loads JSON with error handling |
| 8 | 13–14 REST, FastAPI | W07, W08 | new endpoint with tests |
| 9 | 15–16 databases, SQL | W10, W11, W13 | schema + five queries |
| 10 | 17–18 transactions, integration | W09, W12, W16 | sequence diagram of your own feature |
| 11 | 19–21 auth, security, performance | W14, W15, W17, W18 | security checklist; ETag on a new route |
| 12 | 22–23 testing, deployment | W19 | capstone demo |

## Capstone and assessment

**Capstone.** Extend the teaching app with **passenger accounts**: a `passengers` table (foreign key from rides), sign-up and login with hashed passwords, a session cookie or bearer token, `GET /api/my-rides` that returns only the caller's rides (403 otherwise), a "My rides" view in the page, keyset pagination, and at least ten new integration tests plus one Playwright test. Document the threat model and what would still be needed before public deployment.

**Assessment (100 marks):** concepts explained with diagrams 20 · correct, accessible front end 20 · API and database design with validation and constraints 20 · tests and experiments with interpreted results 20 · security and performance reasoning 10 · written report and reproducibility 10.

**Further reading:** MDN Web Docs (developer.mozilla.org) · web.dev (Google) · FastAPI tutorial (fastapi.tiangolo.com) · SQLite documentation (sqlite.org/lang.html) · OWASP Top 10 and Cheat Sheet Series · WCAG 2.2 quick reference (w3.org/WAI).

## Fundamentals quick reference

A one-page reminder of the four languages, for revision and for open-book lab sessions. Section numbers point to the full explanation.

### HTML

| Task | Write | See |
|---|---|---|
| page skeleton | `<!doctype html>` · `<html lang>` · `<meta charset>` · viewport · `<title>` | 5, 5.6 |
| page regions | `header` · `nav` · `main` (one per page) · `section` · `article` · `aside` · `footer` | 5 |
| headings | `h1` once, then `h2`, `h3` … in order, no skipped levels | 5 |
| link | `<a href="/docs">API documentation</a>` | 5.4 |
| image | `<img src alt width height loading="lazy">` | 5.5 |
| data table | `table` · `caption` · `thead`/`tbody` · `th scope="col"` | 5 |
| form field | `<label for="x">` + `<input id="x" name="x" type required>` | 6 |
| action button | `<button type="button">` (inside forms the default type is `submit`) | 6.2 |
| live message | `<p role="status" aria-live="polite">` | 9.3 |
| script | `<script src defer>` or `type="module"` | 5.1, 10.7 |
| show `<` as text | `&lt;` (or insert with `textContent`) | 5.7, 11 |

### CSS

| Task | Write | See |
|---|---|---|
| sane sizing | `*, *::before, *::after { box-sizing: border-box; }` | 8 |
| design tokens | `:root { --brand: #135da6; }` · `color: var(--brand)` | 7, 7.5 |
| row of items | `display: flex; gap: .5rem; align-items: center; flex-wrap: wrap;` | 8, 8.3 |
| page layout | `display: grid; grid-template-columns: repeat(2, minmax(0, 1fr));` | 8, 8.4 |
| responsive cards | `grid-template-columns: repeat(auto-fit, minmax(min(15rem, 100%), 1fr));` | 8.4 |
| centre anything | `display: grid; place-items: center;` | 8.4 |
| breakpoint | `@media (min-width: 801px) { … }` | 9, 9.1 |
| readable text | `line-height: 1.5; max-width: 65ch;` and contrast ≥ 4.5 : 1 | 7.5, 9.2 |
| visible focus | `:focus-visible { outline: 3px solid …; outline-offset: 2px; }` | 9 |
| who wins | `!important` › origin › **layer** › specificity (ids, classes, elements) › source order | 7, 7.4 |

### JavaScript

| Task | Write | See |
|---|---|---|
| variables | `const` by default, `let` when it must change, never `var` | 10.3 |
| compare | `===` and `!==` | 10 |
| default for missing | `value ?? fallback` · safe access `obj?.prop` | 10.2 |
| transform lists | `filter` → `map` → `reduce`; copy before sorting: `toSorted((a, b) => a - b)` | 10.6 |
| find an element | `document.querySelector("#id .class")` | 11.1 |
| change text safely | `el.textContent = userText` — never `innerHTML` with user data | 11 |
| react to the user | `form.addEventListener("submit", (e) => { e.preventDefault(); … })` | 11.4 |
| many similar buttons | one listener on the container + `event.target.closest("button")` | 11.4 |
| call the API | `const r = await fetch(url, {method, headers, body: JSON.stringify(x)}); if (!r.ok) throw …` | 12, 12.4 |
| parallel requests | `await Promise.all([a(), b()])` | 12.2 |

### SQL

| Task | Write | See |
|---|---|---|
| create a table | `CREATE TABLE t(id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, …)` | 15 |
| relate tables | `driver_id INTEGER REFERENCES drivers(id) ON DELETE RESTRICT` | 15, 15.4 |
| add rows | `INSERT INTO t(a, b) VALUES (?, ?)` — always parameters | 16 |
| read rows | `SELECT cols FROM t WHERE … ORDER BY … LIMIT …` | 16 |
| change / remove | `UPDATE t SET a = ? WHERE id = ?` · `DELETE FROM t WHERE id = ?` — never without `WHERE` | 16 |
| combine tables | `FROM a JOIN b ON b.a_id = a.id` · keep unmatched: `LEFT JOIN` | 16, 16.6 |
| summarise | `GROUP BY` + `COUNT/SUM/AVG/MIN/MAX`; filter groups with `HAVING` | 16, 16.2 |
| missing values | `IS NULL`, `COALESCE`; prefer `NOT EXISTS` over `NOT IN` | 16.4 |
| ranking, running totals | `RANK() OVER (PARTITION BY … ORDER BY …)` | 16.8 |
| insert or update | `INSERT … ON CONFLICT(key) DO UPDATE SET …` | 16.9 |
| all or nothing | `BEGIN` … `COMMIT` / `ROLLBACK` | 17 |
| make it fast | `CREATE INDEX … ON t(col)` + `EXPLAIN QUERY PLAN` | 16 |

## Self-check questions

Answer each in one or two sentences before opening the answer.

<details><summary><b>HTML 1.</b> Why should a page script use <code>defer</code> rather than sit, without it, in the <code>&lt;head&gt;</code>?</summary>

Without `defer` the parser stops at the script until it has downloaded and run, delaying everything below it, and the script cannot yet see the elements it needs. `defer` downloads in parallel and runs after the document is parsed, in order.
</details>

<details><summary><b>HTML 2.</b> An image is purely decorative. What should its <code>alt</code> be?</summary>

`alt=""` — present but empty, so screen readers skip it. A *missing* `alt` makes many screen readers read the file name instead.
</details>

<details><summary><b>HTML 3.</b> A form has a "Clear" button that keeps submitting the form. Why?</summary>

A `<button>` inside a form defaults to `type="submit"`. Write `type="button"` (or `type="reset"` if resetting is really intended).
</details>

<details><summary><b>CSS 1.</b> <code>#message</code> is red; a later rule <code>.panel p { color: blue }</code> does not change it. Why, and what is the clean fix?</summary>

The id selector's specificity (1,0,0) beats (0,1,1) whatever the order. Style with classes instead of ids, or place the rules in cascade layers — not `!important`.
</details>

<details><summary><b>CSS 2.</b> What is the rendered width of <code>width: 300px; padding: 20px; border: 1px solid</code> under <code>content-box</code> and under <code>border-box</code>?</summary>

342 px under `content-box` (300 + 2×20 + 2×1); 300 px under `border-box`, where the content shrinks to 258 px.
</details>

<details><summary><b>CSS 3.</b> When would you use Flexbox and when Grid?</summary>

Flexbox for one direction — a toolbar, a row of buttons, centring one item. Grid for two-dimensional layout — the page, a card gallery — where rows and columns must line up.
</details>

<details><summary><b>JS 1.</b> What do <code>0 || 10</code> and <code>0 ?? 10</code> return, and which suits a tip that may legitimately be 0?</summary>

`10` and `0`. `??` falls back only on `null`/`undefined`, so it keeps a real zero.
</details>

<details><summary><b>JS 2.</b> <code>fetch</code> returned a 404 but the <code>catch</code> did not run. Why?</summary>

`fetch` rejects only on network failure. Any HTTP response, including 404 and 500, fulfils the promise; you must check `response.ok` or `response.status` yourself.
</details>

<details><summary><b>JS 3.</b> In what order do these log: <code>console.log("A"); setTimeout(() => console.log("B")); Promise.resolve().then(() => console.log("C")); console.log("D");</code></summary>

A, D, C, B — synchronous code first, then all microtasks (the promise callback), then the next task (the timer).
</details>

<details><summary><b>JS 4.</b> Why is <code>el.innerHTML = userInput</code> dangerous, and what replaces it?</summary>

The browser parses the input as HTML, so markup such as an `<img onerror=…>` runs script (XSS). Use `textContent`, or build nodes with `createElement`.
</details>

<details><summary><b>SQL 1.</b> Why does <code>WHERE driver_id = NULL</code> return no rows even when some drivers are missing?</summary>

Any comparison with NULL is unknown, not true, and `WHERE` keeps only true rows. Write `WHERE driver_id IS NULL`.
</details>

<details><summary><b>SQL 2.</b> What is the difference between <code>WHERE</code> and <code>HAVING</code>?</summary>

`WHERE` filters individual rows before grouping; `HAVING` filters whole groups after `GROUP BY`, so it may use aggregates such as `COUNT(*) > 1`.
</details>

<details><summary><b>SQL 3.</b> A list of drivers "with no rides" written with <code>NOT IN (SELECT driver_id FROM rides)</code> comes back empty. Why?</summary>

Some rides have `driver_id` NULL. `x NOT IN (…, NULL)` is never true, so no row passes. Use `NOT EXISTS`, or exclude NULLs in the subquery.
</details>

<details><summary><b>SQL 4.</b> Name the one rule that prevents SQL injection.</summary>

Never build SQL by joining strings with input; pass every value as a parameter (`?` / `%s`), so it can never change the statement's structure.
</details>

<details><summary><b>Full stack.</b> The browser already checks that distance is between 0 and 200. Why does the API check again, and why does the database have a <code>CHECK</code> too?</summary>

Browser checks are a convenience — anyone can bypass them with DevTools or `curl`. The API is the real gate and gives a clear 422. The database constraint catches bugs and races in any program that writes to it, so the rule holds even if the API is wrong.
</details>

# Part VI — Beyond the browser: the ATLAS Go front end in Kivy

Everything in Part II runs in a **browser**. ATLAS Go, the phone app, has no browser and no HTML, CSS or JavaScript: its screens, map and charts are **Python**, drawn by the **Kivy** framework and packaged for Android with Buildozer. The ideas you learned in Part II still apply — a tree of elements, layout rules, events, drawing, an event loop, never blocking the UI — they just have different names. This part maps each web idea to its Kivy equivalent and to the ATLAS Go code that uses it. The full, standalone treatment is the 16-lesson course [Kivy Front End with ATLAS Go](WEB_TECHNOLOGY_2.md) and its [11 experiments](../kivy_lab/README.md).

~~~mermaid
flowchart LR
 subgraph WEB["Web front end (this course, Part II)"]
  direction TB
  H["HTML: the element tree"] --> C["CSS: layout and look"] --> J["JavaScript: events, DOM, fetch"] --> BR["the browser draws pixels"]
 end
 subgraph APP["ATLAS Go front end (Kivy)"]
  direction TB
  W["Python: the widget tree"] --> L["layouts, dp/sp, canvas"] --> E["bind, Clock, touch, threads"] --> GL["Kivy draws with OpenGL"]
 end
 WEB -. "same ideas, different names" .-> APP
~~~

## Web idea → Kivy idea → where ATLAS Go uses it

| Web (lesson in this course) | Kivy equivalent | ATLAS Go code | Learn it |
|---|---|---|---|
| HTML element tree, the DOM ([5](#lesson-5--html-documents-elements-attributes-and-the-tree), [11.1](#111-finding-and-walking-the-tree)) | widget tree: `add_widget`, `children`, `walk()` | [`AtlasGoApp.render`](../android-app/atlas_go/app.py) rebuilds each screen's tree | [Kivy 2](WEB_TECHNOLOGY_2.md#lesson-2--widgets-and-the-widget-tree) |
| page load, `DOMContentLoaded` ([5.1](#51-from-bytes-to-pixels-how-the-browser-reads-a-page)) | `App.build()` → `on_start()`; `on_pause`/`on_resume`/`on_stop` | [`build`, `on_start`, `on_pause`](../android-app/atlas_go/app.py) | [Kivy 1](WEB_TECHNOLOGY_2.md#lesson-1--how-a-kivy-app-starts-app-build-and-the-lifecycle) |
| Flexbox (`flex-direction`, `flex-grow`, `gap`, `padding`) ([8.3](#83-flexbox-in-depth)) | `BoxLayout(orientation=…)`, `size_hint`, `spacing`, `padding` | [`box`, `row`](../android-app/atlas_go/app.py) | [Kivy 3](WEB_TECHNOLOGY_2.md#lesson-3--layouts-boxlayout-size_hint-padding-spacing-and-scrolling) |
| `overflow: auto` | `ScrollView` + `bind(minimum_height=…)` | the scrolling body in [`render`](../android-app/atlas_go/app.py) | [Kivy 3](WEB_TECHNOLOGY_2.md#lesson-3--layouts-boxlayout-size_hint-padding-spacing-and-scrolling) |
| CSS `px`, `rem`, colours ([7.5](#75-units-colour-and-typography-in-detail)) | `dp()` for sizes, `sp()` for text, `get_color_from_hex` → RGBA 0–1 | the `GREEN`/`INK`/`LIME` palette in [`app.py`](../android-app/atlas_go/app.py) | [Kivy 4](WEB_TECHNOLOGY_2.md#lesson-4--units-colour-and-screen-density-dp-sp-and-hex-colours) |
| text wrapping (`width`, `overflow-wrap`) | `bind(width=…)` → `text_size`; `bind(texture_size=…)` → `height` | [`AtlasGoApp.label`](../android-app/atlas_go/app.py) | [Kivy 5](WEB_TECHNOLOGY_2.md#lesson-5--properties-and-bind-widgets-that-react) |
| `addEventListener('click', …)`, closures in loops ([10.3](#103-scope-hoisting-and-closures), [11.4](#114-the-event-object-and-event-delegation-in-full)) | `button.bind(on_release=…)`, `lambda key=key: …` | the navigation bar in [`render`](../android-app/atlas_go/app.py) | [Kivy 6](WEB_TECHNOLOGY_2.md#lesson-6--events-callbacks-and-the-android-back-key) |
| browser Back button, `history` | Android Back = key 27 on `Window.on_keyboard` | [`on_keyboard`](../android-app/atlas_go/app.py) | [Kivy 6](WEB_TECHNOLOGY_2.md#lesson-6--events-callbacks-and-the-android-back-key) |
| `<input>`, `<select>`, `<dialog>`, form validation ([6](#lesson-6--html-forms), [6.4](#64-validation-in-the-browser-attributes-css-and-the-constraint-validation-api)) | `TextInput`, `Spinner`, `Popup`; `ValueError` → dialog | [`field`, `select`, `message`, `safe`](../android-app/atlas_go/app.py) | [Kivy 7](WEB_TECHNOLOGY_2.md#lesson-7--text-input-choices-and-dialogs-textinput-spinner-popup) |
| `<canvas>` 2D drawing, `background` | `canvas.before` / `canvas` with `Color`, `Rectangle`, `Line`, `Ellipse` | [`Panel`, `RouteMap`, `OutlookChart`](../android-app/atlas_go/app.py) | [Kivy 8](WEB_TECHNOLOGY_2.md#lesson-8--drawing-on-the-canvas-instructions-canvasbefore-and-redrawing), [9](WEB_TECHNOLOGY_2.md#lesson-9--text-as-textures-and-charts-drawn-by-hand) |
| `setTimeout`, `setInterval`, `requestAnimationFrame`, the event loop ([12](#lesson-12--asynchronous-javascript-the-event-loop-promises-asyncawait-and-fetch)) | `Clock.schedule_once`, `Clock.schedule_interval`, one main loop | [`live_tick`, `lab_step`](../android-app/atlas_go/app.py), [`LiveMap._schedule`](../android-app/atlas_go/livemap.py) | [Kivy 10](WEB_TECHNOLOGY_2.md#lesson-10--the-clock-and-the-main-loop) |
| `pointerdown/move/up`, `setPointerCapture` | `on_touch_down/move/up`, `touch.grab(self)` | panning in [`LiveMap`](../android-app/atlas_go/livemap.py) | [Kivy 11](WEB_TECHNOLOGY_2.md#lesson-11--touch-input-on_touch_down-move-up-grabbing-and-clipping) |
| `fetch` + `await` never blocks the page ([12.4](#124-a-robust-fetch-wrapper)) | worker threads download; `Clock.schedule_once` hands results to the UI thread | [`TileLoader`](../android-app/atlas_go/livemap.py) | [Kivy 12](WEB_TECHNOLOGY_2.md#lesson-12--threads-and-the-ui-thread) |
| single-page app routing, re-rendering from state | `go(screen)` → `save_ui()` → `render()` | [`go`, `render`, `save_ui`](../android-app/atlas_go/app.py) | [Kivy 13](WEB_TECHNOLOGY_2.md#lesson-13--screens-as-state-one-render-instead-of-many-screens) |
| `navigator.geolocation` + permission prompt | pyjnius → Android `LocationManager`, runtime permission | [`DeviceLocation`](../android-app/atlas_go/location.py) | [Kivy 14](WEB_TECHNOLOGY_2.md#lesson-14--talking-to-android-with-pyjnius) |
| `localStorage` ([11.6](#116-remembering-things-in-the-browser)) | a JSON file in the app's private folder, written atomically | [`LocalStore.save`](../android-app/atlas_go/store.py) | [Python 14](PYTHON_PROGRAMMING.md#lesson-14--files-pathlib-json-csv-and-atomic-writes) |
| deploying a site ([23](#lesson-23--deployment-and-architecture)) | `buildozer.spec` → `.apk` / `.aab` for Google Play | [`buildozer.spec`](../android-app/buildozer.spec) | [Kivy 15](WEB_TECHNOLOGY_2.md#lesson-15--packaging-for-android-with-buildozer) |
| end-to-end browser tests ([22](#lesson-22--testing-web-applications)) | press named controls with `trigger_action`, `Window.screenshot` | [`acceptance.py`](../android-app/atlas_go/acceptance.py) | [Kivy 16](WEB_TECHNOLOGY_2.md#lesson-16--testing-a-kivy-front-end) |

## What is genuinely different

| | Web front end | ATLAS Go (Kivy) |
|---|---|---|
| Where layout and look live | separate languages: HTML structure, CSS rules that cascade | one language: each widget's size, colour and position are Python arguments; nothing cascades |
| Who draws | the browser's rendering engine | Kivy issues OpenGL drawing instructions you write yourself (canvas) |
| Accessibility | semantic HTML and ARIA give screen readers a tree for free ([9.3](#93-aria-when-html-is-not-enough)) | Kivy draws pixels, so Android's screen reader sees little; contrast and 48 dp touch targets still matter |
| Where data lives | a server and a database (Part III) | on the phone, in `state.json`; the only network traffic is map tiles |
| Concurrency | one JavaScript thread plus non-blocking `fetch` | one UI thread plus real background threads, handed back with the Clock |
| Updating | refresh the page | users install a new signed release from Google Play |

## The same booking form, twice

The web lab's form (Lesson 6, [`static/index.html`](../web_lab/static/index.html)) checks that the distance is between 0.1 and 200 km in the browser (`min`/`max`) and again on the server. In Kivy there is no server: the same rule is a Python function, and one wrapper turns its `ValueError` into a dialog — exactly how ATLAS Go's [`safe`](../android-app/atlas_go/app.py) works. This program runs as written after `pip install kivy==2.3.1`: a window opens, it checks itself and closes (on a server, run it with `xvfb-run -a`).

~~~python
from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput

def parse_distance(text):                                # the rule: plain, testable Python
    try:
        km = float(text)
    except ValueError:
        raise ValueError("Distance must be a number of kilometres, for example 4.5.") from None
    if not 0.1 <= km <= 200:                             # the same range as min="0.1" max="200"
        raise ValueError("Distance must be between 0.1 and 200 km.")
    return km

class BookingApp(App):
    def build(self):                                     # <form> … </form>
        self.form, self.popup = {}, None
        root = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(8))
        self.distance = TextInput(hint_text="Distance (km)", multiline=False, input_type="number",
                                  size_hint_y=None, height=dp(48))               # <input type="number">
        self.distance.bind(text=lambda _w, value: self.form.__setitem__("distance_km", value))
        self.pickup = Spinner(text="UCC Main Gate", values=("UCC Main Gate", "Kent Station", "Cork Airport"),
                              size_hint_y=None, height=dp(48))                   # <input list="places">
        self.pickup.bind(text=lambda _w, value: self.form.__setitem__("pickup", value))
        book = Button(text="Book demonstration ride", size_hint_y=None, height=dp(48))   # <button type="submit">
        book.bind(on_release=lambda _w: self.safe(self.book))                    # addEventListener('click')
        for w in (self.distance, self.pickup, book):
            root.add_widget(w)
        return root

    def safe(self, callback):                            # like try/catch around a fetch, shown as a <dialog>
        try:
            callback()
        except ValueError as error:
            self.message("Check your details", str(error))

    def message(self, title, text):
        self.popup = Popup(title=title, content=Label(text=text), size_hint=(0.9, None), height=dp(200))
        self.popup.open()

    def book(self):
        km = parse_distance(self.form.get("distance_km", ""))
        self.message("Booked", f"{km} km from {self.form.get('pickup', 'UCC Main Gate')}")

    def on_start(self):
        Clock.schedule_once(self.check, 0.5)

    def check(self, _dt):
        self.distance.text = "far"                       # as if typed
        self.safe(self.book)
        assert self.popup.title == "Check your details"
        self.popup.dismiss()
        self.distance.text = "250"                       # outside min/max
        self.safe(self.book)
        assert self.popup.content.text == "Distance must be between 0.1 and 200 km."
        self.popup.dismiss()
        self.distance.text, self.pickup.text = "4.5", "Kent Station"
        self.safe(self.book)
        assert self.popup.content.text == "4.5 km from Kent Station"
        print("bad input → friendly dialog; good input →", self.popup.content.text)
        self.popup.dismiss()
        self.stop()                                      # auto-close: delete this line to keep the window open

BookingApp().run()
~~~

**Exercises.** (1) Put the web lab's `index.html` form and this program side by side and match every element to its widget. (2) The web version checks the distance in the browser *and* the API; why does ATLAS Go need only one check, and what would change once an operator back end exists? (3) Build a Flexbox navigation bar of five equal buttons (Lesson 8), then the same bar as a Kivy `BoxLayout`; compare `flex: 1` with `size_hint_x=1`.

**Self-check.** *Why can a slow `fetch` not freeze a web page, but a slow download can freeze a Kivy app?* — `fetch` is non-blocking; a Kivy callback that downloads runs on the only UI thread, so the download must move to a worker thread and hand its result back with `Clock.schedule_once`. *What replaces CSS in ATLAS Go?* — keyword arguments on each widget (`size_hint_y`, `height=dp(48)`, `background_color`, `font_size=sp(14)`) plus canvas instructions for backgrounds and shapes.

---

## Audit notes

This course was rewritten in November 2026. The previous version's 30 lessons were two to four sentences each with an identical "Practice" paragraph, most concepts had no example, the lab charts W01–W04, W10 and W11 plotted constants, importing the app created a database file as a side effect, PATCH validated states by hand (undocumented in OpenAPI), and there was no coverage of raw HTTP, DNS, TLS, the box model, specificity, the event loop, joins, indexes, transactions, CORS, caching, sessions or browser testing. Every Python block in this guide now runs as part of the course checks, every JavaScript block is syntax-checked, and every diagram is rendered.

The fundamentals were expanded in November 2026 (62 deep-dive sections). Additions: the browser rendering pipeline and script loading, the content model, global attributes, link resolution, responsive images and media, document metadata and character references (HTML); every form control, encodings and the Constraint Validation API; CSS inclusion, inheritance, modern selectors (`:is`, `:where`, `:has`), cascade layers, units, colour, typography; margin collapsing, positioning and stacking, the flexbox sizing algorithm and `auto-fit` grids; mobile-first and container queries, motion, a computed WCAG contrast audit (which found the focus ring below 3 : 1 on white panels), ARIA and POUR; JavaScript types and truthiness, scope and closures, `this`, classes with private fields, collections, modules and errors; DOM traversal, attributes versus properties, fragments and templates, the event object, debouncing and browser storage; microtask/task ordering, promise combinators, sequential versus parallel `await` and a retrying `fetch`; SQL sub-languages, SQLite type affinity and `STRICT`, key choices, referential actions (and the `PRAGMA foreign_keys` transaction trap), migrations and schema design; logical evaluation order, operators and `CASE`, NULL and the `NOT IN` trap, subqueries and CTEs, self, cross and anti joins, set operations, window functions, upserts and `RETURNING`; isolation anomalies, optimistic concurrency and savepoints. Every new Python block runs with assertions against the teaching schema; every new language-only JavaScript block was executed in Node.js and the browser-API blocks were syntax-checked.
