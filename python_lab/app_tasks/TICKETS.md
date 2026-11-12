# App-building tasks — ten tickets, 100 points

You join the team behind the ride-booking app in [`../app_integration.py`](../app_integration.py) (Part III of the course). Each ticket below is written the way a real team writes one: a user story, the contract, numbered **acceptance criteria (AC)**, non-functional requirements, and a definition of done. Every AC is checked by an automated acceptance test named `test_acN_...` in [`tests/`](tests/), so you can see which criterion fails.

**Workflow (same as a real sprint):**

1. Read the ticket. Write down what the user does, which HTTP calls happen, which tables change.
2. Implement `install_tNN(app)` (and any helper the ticket names) in [`starter.py`](starter.py). Don't edit `app_integration.py`. Your code plugs into the running app through its extension points.
3. Run the grader: `python python_lab/app_tasks/grade.py --task 1` (one ticket) or `python python_lab/app_tasks/grade.py` (all).
4. Read the failing AC, fix, re-run. When everything passes, check the definition of done by hand (it's what a code reviewer would ask about).

| # | Ticket | Points | Skills | Depends on |
|---|---|---:|---|---|
| T01 | Delete a cancelled ride | 8 | DELETE, 204, foreign keys, transaction, UI update | — |
| T02 | Available-drivers dropdown | 8 | read model, one query, dependent UI state | — |
| T03 | Accounts, login and sessions | 15 | password hashing, tokens, expiry, 401, no user enumeration | — |
| T04 | Protect the API with roles | 12 | middleware, 401 vs 403, server-side trust | T03 |
| T05 | Rate-limit bookings | 10 | sliding window, 429 + Retry-After, thread safety, injected clock | — |
| T06 | CSV export | 10 | file download, RFC 4180, formula injection, JOIN | — |
| T07 | Schema migration and ratings | 12 | `PRAGMA user_version`, ALTER TABLE, CHECK, race-free update | — |
| T08 | Ignore out-of-order search responses | 8 | async UI, request sequencing | — |
| T09 | Sorting and filtering without SQL injection | 8 | whitelists, bound parameters, pagination totals | — |
| T10 | Transactional outbox and delivery worker | 9 | events in the same transaction, retries, exactly-once | — |

## Extension points you will use

| You need to… | Use |
|---|---|
| add an endpoint | `app.server.add_route(method, regex, fn)`. `fn(match, query, body, headers)` returns `(status, payload)` or `(status, payload, extra_headers)`. `match[1]` is the first regex group, `query` is `parse_qs` output (`{"status": ["cancelled"]}`, blank values kept), `body` is the parsed JSON (or `None`), `headers.get("Authorization")`. `payload` may be a dict/list (sent as JSON), `ai.RawBody(text, content_type)` (anything else), or `None` with status 204 |
| refuse a request | `raise ai.ValidationError(field, message)` → 422 · `ai.NotFound` → 404 · `ai.Conflict` → 409 · `ai.Unauthorized` → 401 + `WWW-Authenticate: Bearer` · `ai.Forbidden` → 403 · `ai.TooManyRequests(message, retry_after_seconds)` → 429 + `Retry-After`. Any other exception becomes a 500 with a reference number |
| run code before every route (middleware) | `app.server.before_request.append(hook)`. `hook(request)` gets `request.method`, `.path`, `.query`, `.headers`, `.body` (the same dict the route will receive), `.client` (IP), `.state` (a dict for you) and may raise any error above |
| query / change data | `app.db.query(sql, params) -> list[dict]`, `app.db.execute(sql, params) -> cursor`, `with app.db.transaction(): ...` (BEGIN … COMMIT, ROLLBACK on exception), `app.db.count(table, where)`. For DDL use `with app.db.lock: app.db.conn.executescript(sql)` |
| react to every ride write | `app.service.write_hooks.append(f)`. `f(db, event, ride)` runs **inside** the write's transaction for `ride.created`, `ride.assigned`, `ride.completed`, `ride.cancelled` |
| reuse business logic | `app.service.get_ride(id)` (raises `NotFound`), `app.service._invalidate()` (clears the stats cache) |
| add a button | `screen.my_button = ai.Button("Label", handler, app.trace)`, then `screen.my_button.click(*args)` calls `handler(*args)` |
| inside a handler | `screen._handler("what")` (trace), `screen.client.get/post/patch/request(...)` → `Response(status, body, headers)`, `screen._upsert(ride)`, `screen._show_error(resp)` (sets `screen.banner` from `ai.user_message`), `screen.table`, `screen.banner`, `screen._pool.submit(...)`, `screen._pending`, `screen._ui_lock` |
| send a header on every request | `screen.client.default_headers["Authorization"] = "Bearer ..."` |

---

<a id="t01"></a>
## T01 — Delete a cancelled ride (8 points)

**User story.** As a dispatcher, I want to delete rides that were cancelled, so that the list only shows real work.

**Contract.** `DELETE /api/rides/{id}` → `204 No Content` (empty body) · `404` if the ride does not exist · `409` if it is not cancelled.

**Acceptance criteria**

1. Deleting a **cancelled** ride returns 204 with no body, and removes the ride **and its audit rows**. A later `GET /api/rides/{id}` is 404.
2. Deleting a ride that does not exist returns 404.
3. A `requested`, `assigned` or `completed` ride returns 409. Its error message contains the word `cancelled`, and the ride is unchanged.
4. Deleting the same ride twice: the second call is 404.
5. Screen: `screen.delete_button.click(ride_id)` removes the row from `screen.table` **only after** a 204, and sets `screen.banner` to `Deleted ride {id}`.
6. Screen: on 409 the row stays and the banner is the standard error message (`screen._show_error`), which starts with `Not saved` and mentions `cancelled`.
7. A ride with several audit rows can still be deleted. The server never answers 500.

**Non-functional.** One transaction for the whole delete. Remember the `FOREIGN KEY` from `audit.ride_id` to `rides.id`.
**Definition of done.** All ACs pass. The stats cache is cleared after a delete. No change to `app_integration.py`.

---

<a id="t02"></a>
## T02 — Available-drivers dropdown (8 points)

**User story.** As a dispatcher, I want a dropdown of drivers who can take a job right now, so that I never assign a busy or offline driver.

**Contract.** `GET /api/drivers/available` → `200 [{"id": 1, "name": "Niamh"}, ...]`.

**Acceptance criteria**

1. The list contains only drivers who are online and not busy, as objects with exactly `id` and `name`, sorted by name (then id).
2. The endpoint runs **exactly one** `SELECT`.
3. A driver disappears from the list when assigned and comes back after the ride is completed.
4. Screen: `screen.available_button.click()` fills `screen.driver_options` with `(id, name)` tuples in the same order. If `screen.selected_driver` is no longer in the list, it becomes the first id (or `None` if the list is empty). After `install_t02` both attributes exist (`[]` and `None`).
5. Screen: `screen.assign_selected_button.click(ride_id)` assigns `screen.selected_driver`. On success it updates the row (`screen._upsert`), clears the banner and **reloads the dropdown**.
6. If no driver is selected, the click sends **no request**, returns `None` and sets the banner to `No drivers available`.

**Definition of done.** No N+1 queries. The UI never offers a driver the server would reject.

---

<a id="t03"></a>
## T03 — Accounts, login and sessions (15 points)

**User story.** As a passenger, I want my own account, so that only I can see and change my bookings.

**Signature.** `install_t03(app, clock=time.time)`: use `clock()` for every expiry decision (tests pass a fake clock).

**Contract**

| Request | Success | Errors |
|---|---|---|
| `POST /api/register {"username", "password"}` | `201 {"id", "username", "role": "passenger"}` | 422 (`field`), 409 duplicate |
| `POST /api/login {"username", "password"}` | `200 {"token", "expires_in": 3600}` | 401 `{"error": "invalid username or password"}` |
| `GET /api/me` with `Authorization: Bearer <token>` | `200 {"id", "username", "role"}` | 401 |
| `POST /api/logout` with the token | `204` | 401 |

**Acceptance criteria**

1. Register returns 201 with **exactly** `id`, `username`, `role`. The role is always `passenger`, even if the body says otherwise.
2. Validation, checked in this order, returns 422 with `field`:
   - `username` must be a string of 3–20 letters, digits or `_`;
   - `password` must be a string of at least 10 characters that is not equal to the username (ignoring case).
3. Usernames are unique **ignoring case**: `AOIFE` after `aoife` is 409.
4. Passwords are never stored. The table `users` has columns `salt` (≥ 16 random bytes, different per user) and `pw_hash` = `hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)`, where your module defines `PBKDF2_ITERATIONS >= 100_000`.
5. Login returns a token (`secrets.token_urlsafe(32)`) and `expires_in` 3600. `/api/me` with that token returns the user.
6. A wrong password, an unknown user and an SQL-injection username all get the **identical** 401 body, so nobody can tell which usernames exist.
7. Every login creates a new token. The table `sessions` stores only `token_hash` = SHA-256 hex of the token, never the token itself.
8. Missing, malformed (anything other than `Bearer <token>`, case-sensitive), unknown or expired tokens all get 401 with `WWW-Authenticate: Bearer`.
9. A session is valid while `clock() < login time + 3600`.
10. Logout makes that token unusable. Other sessions of the same user keep working.
11. `create_user(app, username, password, role="passenger")` exists for server-side use (e.g. creating a dispatcher). It applies the same validation and returns `{"id", "username", "role"}`.
12. Screen: `screen.login_button.click(username, password)`:
    - on 200: sets `client.default_headers["Authorization"]`, sets `screen.user` from `/api/me`, and sets the banner to `Signed in as <username>`;
    - on 401: sets the banner to `Invalid username or password` and leaves no header.

    `screen.logout_button.click()` calls logout, removes the header, sets `screen.user = None` and the banner to `Signed out`. `screen.user` starts as `None`.

**Hints.** Compare hashes with `hmac.compare_digest`. A `current_user(app, headers)` helper that returns the user or raises `ai.Unauthorized` will be reused in T04.

---

<a id="t04"></a>
## T04 — Protect the API with roles (12 points, needs T03)

**User story.** As the operator, I want only signed-in users to use the API, and only dispatchers to run operations, so that passengers cannot assign drivers or read business statistics.

**Rules**

- **Public:** `GET /`, `GET /api/health`, `POST /api/register`, `POST /api/login`. Everything else needs a valid token, otherwise 401.
- **Dispatcher-only:** `POST /api/rides/{id}/assign`, `POST /api/rides/{id}/complete`, `GET /api/stats`, `DELETE /api/rides/{id}`. For a passenger these return 403.
- A passenger's booking is always in their own name: the server replaces `passenger` with their username. Dispatchers may book for anyone.

**Acceptance criteria**

1. Every protected route returns 401 with `WWW-Authenticate: Bearer` when there is no token.
2. Public routes still work without a token.
3. Passengers get 403 on dispatcher-only routes, and nothing changes in the database.
4. Dispatchers can assign, complete and read stats.
5. A passenger booking with `"passenger": "Somebody Else"` is stored under the passenger's username. A dispatcher's booking keeps the name sent.
6. A logged-out token is rejected (401).
7. The role is read from the database on **every** request: a user demoted in the database gets 403 on their next request with the same token.
8. Screen: an unauthenticated load shows `Please sign in.`, and a passenger trying to assign sees `You are not allowed to do that.` (both already provided by `ai.user_message`).

**Definition of done.** One middleware (`app.server.before_request`), no copy-pasted checks in routes. 401 means "who are you?", 403 means "I know who you are, and no".

---

<a id="t05"></a>
## T05 — Rate-limit bookings (10 points)

**User story.** As the operator, I want to stop a script from flooding us with bookings, so that real users are not slowed down.

**Signature.** `install_t05(app, limit=5, window=60.0, clock=time.monotonic)`

**Acceptance criteria**

1. The 6th `POST /api/rides` from the same client within the window gets 429, with header `Retry-After: 60` and body `retry_after: 60`. Only 5 rides are stored.
2. **Sliding window.** An attempt made at time *t* counts while `clock() < t + window`. `Retry-After` is `ceil(oldest_counted + window - now)` (minimum 1).
3. Each client has its own budget. The client key is the full `Authorization` header if it starts with `Bearer `, otherwise the client IP.
4. Only `POST /api/rides` is limited. GETs and other POSTs are not.
5. Every attempt counts, **including invalid ones** (422). Requests refused with 429 are **not** counted, so hammering the API does not extend the wait.
6. Under 20 concurrent requests from one client, exactly 5 succeed (no race between "check" and "record").
7. Screen: a refused booking shows `Too many requests - try again in 60 s.` (from `ai.user_message`).

**Hints.** A `deque` of timestamps per key, protected by a `threading.Lock`.

---

<a id="t06"></a>
## T06 — CSV export (10 points)

**User story.** As an accountant, I want to download rides as a CSV file, so that I can open them in a spreadsheet.

**Contract.** `GET /api/rides/export.csv[?status=…]` → `200`, `Content-Type: text/csv; charset=utf-8`, `Content-Disposition: attachment; filename="rides.csv"`.

**Acceptance criteria**

1. The headers are exactly as in the contract.
2. The first row is `id,passenger,pickup,destination,distance_km,fare_eur,status,driver`, then one row per ride in id order. `fare_eur` has two decimals (`13.36`).
3. RFC 4180: lines end with `\r\n`, and values with commas or quotes are quoted correctly (use the `csv` module).
4. `driver` is the driver's name (empty if none), produced with **one** `SELECT` (a JOIN).
5. Spreadsheet formula injection is neutralised: any text cell that starts with `=`, `+`, `-`, `@`, tab or carriage return gets a leading `'`.
6. `?status=` must be one of the four statuses, otherwise 422 with `field: status`. A filter with no matches returns only the header row.
7. Screen: `screen.export_button.click(status=None)` stores `screen.download = (filename_from_Content-Disposition, csv_text)`. `screen.download` starts as `None`.

---

<a id="t07"></a>
## T07 — Schema migration and ratings (12 points)

**User story.** As a passenger, I want to rate a finished ride from 1 to 5 stars, so that good drivers get noticed.

**Module-level names.** `MIGRATIONS` (a list of SQL strings; migration 1 adds `rating INTEGER CHECK (rating BETWEEN 1 AND 5)` to `rides`) and `migrate(db, migrations=None) -> int`. `install_t07(app)` runs `migrate(app.db)` and adds the routes.

**Contract.** `POST /api/rides/{id}/rate {"stars": 1-5}` → `200 <ride with rating>` · `GET /api/drivers/{id}/rating` → `{"driver_id", "average", "count"}`.

**Acceptance criteria**

1. `migrate` applies only the migrations after `PRAGMA user_version`, sets `user_version` to the number applied in total, returns how many ran (0 the second time), and keeps existing data.
2. Each migration runs in its own transaction **together with** its `user_version` update. If migration *n* fails, the error is raised and `user_version` stays at *n − 1*.
3. The database itself rejects a rating outside 1–5 (`CHECK`).
4. A completed ride can be rated. The response includes `"rating"`.
5. `stars` must be an integer from 1 to 5 (not `True`, `"5"` or `4.5`), otherwise 422 with `field: stars`. This is checked first.
6. Unknown ride: 404. Ride not completed: 409 with `completed` in the message. Already rated: 409 with `already` in the message, and the first rating is kept.
7. Eight simultaneous ratings of one ride: exactly one 200, the rest 409.
8. Driver rating: `average` is rounded to 2 decimals, or `null` with `count` 0 when there are no ratings. 404 for an unknown driver.

**Hint for AC7.** Do it in one statement: `UPDATE … WHERE id = ? AND status = 'completed' AND rating IS NULL`, then look at `rowcount`.

---

<a id="t08"></a>
## T08 — Ignore out-of-order search responses (8 points)

**User story.** As a dispatcher typing in the search box, I want the results to always match what I typed last, even when the network is slow.

**Acceptance criteria**

1. `screen.live_search_button.click(text)` returns a **Future** immediately, without waiting for the network.
   - It submits the work with `screen._pool.submit` and appends the Future to `screen._pending`, so that `screen.wait()` waits for it.
   - It sets `screen.search_status = "Searching..."` before returning.
   - When the newest response arrives, `screen.search_status` becomes `"<total> results"`.
   - The request is `GET /api/rides?q=<text>&limit=100` (URL-encoded).
2. If an older request answers **after** a newer one, its response is ignored: `screen.table` shows the newest results, and `screen.stale_responses_ignored` (starts at 0) goes up by one.
3. Responses that arrive in order are all applied.
4. An error from a stale request is ignored (the banner stays empty). An error from the newest request is shown with `screen._show_error` and clears `search_status`.
5. After four quick searches with decreasing delays, the screen shows the last search, and three responses were ignored.

**Hint.** Give each click a sequence number. When a response arrives, apply it only if its number is still the latest (check under `screen._ui_lock`).

---

<a id="t09"></a>
## T09 — Sorting and filtering without SQL injection (8 points)

**User story.** As a dispatcher, I want to sort and filter the ride list, so that I can find expensive or pending rides quickly.

**Contract.** `GET /api/rides/query?sort=&order=&status=&min_fare=&max_fare=&limit=` → `{"items": [...], "total": n}`.

| Parameter | Allowed | Default |
|---|---|---|
| `sort` | `id`, `fare_cents`, `distance_km`, `passenger` | `id` |
| `order` | `asc`, `desc` | `asc` |
| `status` | comma-separated list of the four statuses (none empty) | all |
| `min_fare`, `max_fare` | integers 0 – 10 000 000, `min_fare <= max_fare` | none |
| `limit` | 1 – 100 | 20 |

**Acceptance criteria**

1. With no parameters: id ascending, 20 items, and `total` = all rides.
2. Sorting matches a reference sort in Python, with ties broken by `id` in the same direction.
3. Filters combine (AND). Fare bounds are inclusive.
4. `total` counts **all** matches, not just the page.
5. Any invalid parameter gives 422 naming that parameter in `field` (`min_fare` when min > max), and the database is untouched. The tests include real injection attempts such as `sort=id;DROP TABLE rides`.
6. User values reach SQLite only as **bound parameters** through `app.db.query(sql, params)`. Column names and `ASC`/`DESC` come only from your whitelist.

---

<a id="t10"></a>
## T10 — Transactional outbox and delivery worker (9 points)

**User story.** As a passenger, I want a notification for every change to my ride, and never a notification for a change that didn't happen.

**Module-level names.** `install_t10(app)` and `deliver_outbox(app, send, max_attempts=5) -> {"delivered": n, "failed": n, "dead": n}`.

**Acceptance criteria**

1. Every ride write records one event in a table `outbox`, in order:
   - event types: `ride.created`, `ride.assigned`, `ride.completed`, `ride.cancelled`;
   - columns: `id`, `event`, `ride_id`, `payload`, `status` (`pending` / `delivered` / `dead`, default `pending`), `attempts` (default 0), `last_error`.
2. `payload` is JSON with exactly `id`, `status`, `passenger`, `fare_cents`, `driver_id`, as they are **after** the write.
3. The event is written **in the same transaction** as the change, using `app.service.write_hooks`. If the write rolls back (a later hook fails, or an assignment crashes), there is no event.
4. `deliver_outbox` calls `send(event)` for each pending event in id order:
   - each event is `{"id", "event", "ride_id", "payload": dict}`;
   - each successful send marks the event `delivered`;
   - running it again sends nothing.
5. When `send` raises, the event stays `pending`, `attempts` goes up by one, and `last_error` contains the exception message. It is retried on the next run.
6. When `attempts` reaches `max_attempts`, the event becomes `dead` and is never sent again. The returned counts say how many were delivered, failed (still pending) or died **in this run**.
7. Calling `install_t10` twice does not record events twice.

**Why it matters.** Sending an e-mail inside a transaction that later rolls back tells the customer something that never happened. Writing the event in the same transaction, and sending it afterwards, is the *transactional outbox* pattern.
