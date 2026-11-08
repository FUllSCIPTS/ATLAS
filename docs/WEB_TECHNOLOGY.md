# Web Technology — an illustrated, standalone course from HTTP to full stack

**ATLAS option 11.** 23 lessons in five parts, a runnable full-stack application, 20 measured experiments and 28 integration tests. **Audience:** complete beginners to intermediate students; no prior web experience is assumed. **Tools:** a browser, Python 3.10+, a text editor (VS Code or similar). Every lesson stands on its own: it explains the idea, draws it, shows working code, points to the exact line in the teaching app where it is used, names the usual mistakes and ends with exercises.

[Lab manual](../web_lab/README.md) · [Open the experiments in Colab](https://colab.research.google.com/github/FUllSCIPTS/ATLAS/blob/main/web_lab/Web_Technology_Colab_Labs.ipynb) · [Teaching app source](../web_lab/) · [ATLAS UML blueprint](https://github.com/FUllSCIPTS/ATLAS/blob/architecture-explorer/architecture-explorer/starter/docs/UML_BLUEPRINT.md) · [ATLAS Go method catalogue](../android-app/docs/ARCHITECTURE.md#complete-source-method-catalog)

> **What is real and what is teaching code.** ATLAS Go 1.2.0 is a Python/Kivy Android app that stores everything on the phone; it has no web backend. The ATLAS **server starter** (HTML, CSS, JavaScript, FastAPI gateway and services, SQL schema) lives on the [`architecture-explorer` branch](https://github.com/FUllSCIPTS/ATLAS/tree/architecture-explorer/architecture-explorer/starter). This course's **teaching app** in [`web_lab/`](../web_lab/) is a small, independent, local ride-booking site built to demonstrate every lesson. It has no authentication and must never be put on a public network.

## Contents

| Part | Lessons | Experiments |
|---|---|---|
| I. How the Web works | [1 Internet and Web](#lesson-1--the-internet-and-the-web-clients-servers-ip-tcp-and-ports) · [2 URLs and DNS](#lesson-2--urls-and-dns) · [3 HTTP](#lesson-3--http-requests-responses-methods-status-codes-and-headers) · [4 HTTPS and TLS](#lesson-4--https-and-tls) | W01, W02 |
| II. Front end | [5 HTML](#lesson-5--html-documents-elements-attributes-and-the-tree) · [6 Forms](#lesson-6--html-forms) · [7 CSS basics](#lesson-7--css-rules-selectors-specificity-and-the-cascade) · [8 Layout](#lesson-8--the-box-model-flexbox-and-grid) · [9 Responsive and accessible](#lesson-9--responsive-and-accessible-design) · [10 JavaScript](#lesson-10--javascript-the-language) · [11 DOM and events](#lesson-11--the-dom-events-and-safe-rendering) · [12 Async and fetch](#lesson-12--asynchronous-javascript-the-event-loop-promises-asyncawait-and-fetch) | W03–W06, W20 |
| III. Back end and data | [13 REST APIs](#lesson-13--apis-and-rest-design) · [14 FastAPI](#lesson-14--building-the-back-end-with-fastapi) · [15 Relational design](#lesson-15--relational-databases-tables-keys-constraints-and-normalisation) · [16 SQL](#lesson-16--sql-queries-joins-aggregation-indexes-and-injection) · [17 Transactions](#lesson-17--transactions-concurrency-and-python-with-sqlite) | W07–W13 |
| IV. Full stack | [18 Integration](#lesson-18--putting-it-together-one-request-through-every-layer) · [19 Sessions and auth](#lesson-19--state-cookies-sessions-tokens-authentication-and-authorisation) · [20 Security](#lesson-20--web-security-owasp-top-10-in-practice) · [21 Performance](#lesson-21--performance-caching-pagination-and-load) · [22 Testing](#lesson-22--testing-web-applications) · [23 Deployment](#lesson-23--deployment-and-architecture) | W14–W19 |
| V. Practice | [Run the lab](#part-v--practice) · [Experiments](#the-20-experiments) · [Plan](#12-week-teaching-plan) · [Capstone](#capstone-and-assessment) | all |

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

**Exercises.** (1) Build a page about your favourite Cork place with every element group above. (2) Run it through the W3C validator (validator.w3.org).

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

**Exercises.** (1) Build a sign-up form with email, phone and a password confirmation. (2) Submit it with `method="get"` and read the URL.

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

**Exercises.** (1) Give `#message` a colour and then try to override it with `.ride p` — explain the result. (2) Rewrite three rules using custom properties.

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

**Exercises.** (1) Calculate the rendered width of a `content-box` element with width 200 px, padding 1 rem (16 px) and a 2 px border. (2) Build a three-card row with Flexbox that wraps on small screens.

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

**Exercises.** (1) Use only the Tab and Enter keys to book, assign and complete a ride. (2) Run Lighthouse (DevTools → Lighthouse → Accessibility) and fix one finding.

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

**Exercises.** (1) Write `formatRide(ride)` returning `"UCC → Kent (4.5 km)"`. (2) Sort drivers by rating descending then distance ascending.

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

**Exercises.** (1) Rewrite the action buttons with event delegation. (2) Explain why `element.innerText = x` is safe but `element.outerHTML = x` is not.

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

**Exercises.** (1) Add a loading spinner that appears while a request is in flight. (2) Retry a failed GET up to three times with exponential back-off — and explain why retrying POST needs an idempotency key.

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

**Exercises.** (1) Add a `passengers` table and change `rides.passenger` to a foreign key. (2) Normalise a spreadsheet of orders with columns `order, customer, customer_phone, dish1, dish2, dish3`.

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

**Exercises.** (1) Average fare per pickup place, only places with ≥ 2 rides. (2) Which rides have no driver? Write it with `LEFT JOIN … WHERE d.id IS NULL` and with `WHERE driver_id IS NULL`. (3) Add an index for "a driver's rides, newest first" and confirm it with `EXPLAIN QUERY PLAN`.

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

**Exercises.** (1) Make "assign driver" also set the driver offline in the same transaction. (2) What goes wrong if two drivers accept the same ride at the same moment, and how would a `WHERE status = 'requested'` in the UPDATE fix it?

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

## Audit notes

This course was rewritten in November 2026. The previous version's 30 lessons were two to four sentences each with an identical "Practice" paragraph, most concepts had no example, the lab charts W01–W04, W10 and W11 plotted constants, importing the app created a database file as a side effect, PATCH validated states by hand (undocumented in OpenAPI), and there was no coverage of raw HTTP, DNS, TLS, the box model, specificity, the event loop, joins, indexes, transactions, CORS, caching, sessions or browser testing. Every Python block in this guide now runs as part of the course checks, every JavaScript block is syntax-checked, and every diagram is rendered.
