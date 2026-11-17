"""Part III, lab A19: add a feature to an app that already works. The feature is SOS.

ATLAS Go 1.6.0 added an SOS button. This lab builds the same feature a second way, on the Part III
ride-booking app (python_lab/app_integration.py), one layer at a time and WITHOUT editing that file:

    1. rules       what may happen, who may do it, what must never happen
    2. database    a migration that adds a table to a database that already holds data
    3. back end    a service with the rules (validation, ownership, one active SOS per ride, audit)
    4. API         two routes added next to the existing ones
    5. front end   a button with a confirmation step, and honest words on the screen
    6. tests       the new behaviour, and proof that the old behaviour did not move

    python python_lab/feature_flow.py          # run the lab and print every table
    python -m pytest -q python_lab/tests/test_feature_flow.py

The phone's own implementation (atlas_go.store.LocalStore.raise_sos, no server involved) is run at the
end and compared with this one: same rules, different code.
"""
from __future__ import annotations

import importlib.util
import sqlite3
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'android-app'))

_spec = importlib.util.spec_from_file_location('app_integration', ROOT / 'python_lab' / 'app_integration.py')
ai = importlib.util.module_from_spec(_spec)
sys.modules.setdefault('app_integration', ai)
_spec.loader.exec_module(ai)

EMERGENCY_NUMBER = '112'

# ---------------------------------------------------------------------------- 2. database
# CREATE ... IF NOT EXISTS lets the migration run on a fresh database and on one that already has it.
# The CHECKs are the last line of defence: they hold even if a later change forgets a rule in Python.
# The partial unique index is the rule "one active SOS per ride" written where no race can break it.
MIGRATION = """
CREATE TABLE IF NOT EXISTS sos (
    id          INTEGER PRIMARY KEY,
    ride_id     INTEGER NOT NULL REFERENCES rides(id),
    passenger   TEXT    NOT NULL,
    lat         REAL    NOT NULL CHECK (lat BETWEEN -90 AND 90),
    lon         REAL    NOT NULL CHECK (lon BETWEEN -180 AND 180),
    source      TEXT    NOT NULL CHECK (source IN ('device', 'route')),
    status      TEXT    NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'resolved')),
    raised_at   REAL    NOT NULL,
    resolved_at REAL,
    CHECK ((status = 'resolved') = (resolved_at IS NOT NULL))
);
CREATE UNIQUE INDEX IF NOT EXISTS sos_one_active ON sos(ride_id) WHERE status = 'active';
"""


def migrate(db) -> None:
    with db.lock:
        db.conn.executescript(MIGRATION)


def rows_of(db, table: str) -> list[tuple]:
    return [tuple(r) for r in db.conn.execute(f'SELECT * FROM {table} ORDER BY 1').fetchall()]


# ---------------------------------------------------------------------------- 3. back end
class SosService:
    """The SOS rules. It shares the ride service's database and trace; it changes nothing in it."""

    def __init__(self, rides: 'ai.RideService', clock=time.time):
        self.rides, self.db, self.trace, self.clock = rides, rides.db, rides.trace, clock

    def _check_point(self, body) -> tuple[float, float, str]:
        if not isinstance(body, dict):
            raise ai.ValidationError('body', 'a JSON object is required')
        values = []
        for name, low, high in (('lat', -90, 90), ('lon', -180, 180)):
            v = body.get(name)
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not low <= v <= high:
                raise ai.ValidationError(name, f'a number from {low} to {high} is required')
            values.append(float(v))
        source = body.get('source', 'route')
        if source not in ('device', 'route'):
            raise ai.ValidationError('source', "'device' or 'route'")
        return values[0], values[1], source

    def _own_ride(self, ride_id: int, passenger) -> dict:
        ride = self.rides.get_ride(ride_id)
        # Stand-in for the session: the phone uses the signed-in account, this lab uses the name on the ride.
        if not isinstance(passenger, str) or passenger != ride['passenger']:
            raise ai.Forbidden('only the passenger of this ride can do that')
        return ride

    def raise_sos(self, ride_id: int, body) -> tuple[dict, bool]:
        """Returns (sos, created). Raising it twice for one ride returns the first record."""
        self.trace.hop('service', 'validate, check ride, insert SOS')
        lat, lon, source = self._check_point(body)
        ride = self._own_ride(ride_id, (body or {}).get('passenger'))
        with self.db.transaction():
            if ride['status'] != 'assigned':           # state may have changed since the read above
                ride = self.rides.get_ride(ride_id)
            if ride['status'] != 'assigned':
                raise ai.Conflict(f'SOS is available during a ride. In an emergency call {EMERGENCY_NUMBER}.')
            active = self.db.query("SELECT * FROM sos WHERE ride_id = ? AND status = 'active'", (ride_id,))
            if active:
                return active[0], False
            try:
                cur = self.db.execute(
                    'INSERT INTO sos (ride_id, passenger, lat, lon, source, raised_at) VALUES (?, ?, ?, ?, ?, ?)',
                    (ride_id, ride['passenger'], lat, lon, source, self.clock()))
            except sqlite3.IntegrityError:             # the unique index caught a race the SELECT missed
                return self.db.query("SELECT * FROM sos WHERE ride_id = ? AND status = 'active'", (ride_id,))[0], False
            self.db.execute('INSERT INTO audit (ride_id, action) VALUES (?, ?)', (ride_id, 'sos'))
            return self.db.query('SELECT * FROM sos WHERE id = ?', (cur.lastrowid,))[0], True

    def get(self, sos_id: int) -> dict:
        rows = self.db.query('SELECT * FROM sos WHERE id = ?', (sos_id,))
        if not rows:
            raise ai.NotFound(f'SOS {sos_id} does not exist')
        return rows[0]

    def resolve(self, sos_id: int, body) -> dict:
        """'I am safe'. The phone asks for the account password here; the lab asks for the passenger's name."""
        self.trace.hop('service', 'check owner, end SOS')
        sos = self.get(sos_id)
        self._own_ride(sos['ride_id'], (body or {}).get('passenger'))
        with self.db.transaction():
            if self.get(sos_id)['status'] != 'active':
                raise ai.Conflict('this SOS has already ended')
            self.db.execute("UPDATE sos SET status = 'resolved', resolved_at = ? WHERE id = ?", (self.clock(), sos_id))
            self.db.execute('INSERT INTO audit (ride_id, action) VALUES (?, ?)', (sos['ride_id'], 'sos-ended'))
        return self.get(sos_id)


# ---------------------------------------------------------------------------- 4. API
def add_sos_routes(server: 'ai.ApiServer', sos: SosService) -> None:
    """Added routes are matched before the built-in ones, and the existing ones are not touched."""
    def create(m, q, b, h):
        record, created = sos.raise_sos(int(m[1]), b)
        return (201 if created else 200), record, {'Idempotent-Replay': 'false' if created else 'true'}
    server.add_route('POST', r'/api/rides/(\d+)/sos', create)
    server.add_route('POST', r'/api/sos/(\d+)/resolve', lambda m, q, b, h: (200, sos.resolve(int(m[1]), b)))
    server.add_route('GET', r'/api/sos/(\d+)', lambda m, q, b, h: (200, sos.get(int(m[1]))))


# ---------------------------------------------------------------------------- 5. front end
class SosScreen(ai.RideScreen):
    """The ride screen with one more button. Everything it already did, it still does."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.confirming = False
        self.sos: dict | None = None
        self.sos_button = ai.Button('SOS · emergency help', self._on_sos, self.trace)
        self.resolve_button = ai.Button('I am safe · end SOS', self._on_safe, self.trace)

    def _on_sos(self, ride: dict):
        # Step 1 asks; step 2 sends. A button that can summon help must not fire from a stray tap.
        if not self.confirming:
            self.confirming = True
            self.banner = 'Raise an SOS? Tap again to confirm.'
            self.trace.hop('event handler', 'ask for confirmation (no request sent)')
            return None
        self.confirming = False
        self._handler('send the SOS')
        self.sos_button.enabled = False
        try:
            resp = self.client.post(f"/api/rides/{ride['id']}/sos",
                                    {'passenger': ride['passenger'], 'lat': 51.8985, 'lon': -8.4756, 'source': 'route'})
        finally:
            self.sos_button.enabled = True
        if resp.ok:
            self.sos = resp.body
            # The honest sentence matters as much as the request: nobody is alerted by this app.
            self.banner = f'SOS recorded. Call {EMERGENCY_NUMBER} now - this app alerts nobody by itself.'
            self.trace.hop('event handler', 'show the emergency panel')
        else:
            self._show_error(resp)
        return resp

    def _on_safe(self, ride: dict):
        self._handler('end the SOS')
        resp = self.client.post(f"/api/sos/{self.sos['id']}/resolve", {'passenger': ride['passenger']})
        if resp.ok:
            self.sos, self.banner = None, 'SOS ended.'
        else:
            self._show_error(resp)
        return resp


class SosApp(ai.App):
    """The Part III app with the SOS feature added behind a migration."""

    def __init__(self, drivers=3, rides=0, assigned=True, **options):
        self.trace = ai.Trace()
        self.db = ai.Database(self.trace)
        self.service = ai.RideService(self.db, self.trace)
        self.service.seed(drivers, rides, assigned)
        migrate(self.db)
        self.sos = SosService(self.service)
        self.server = ai.ApiServer(self.service, self.trace).start()
        add_sos_routes(self.server, self.sos)
        self.client = ai.ApiClient(self.server.url, self.trace)
        self.screen = SosScreen(self.client, self.trace, **options)


# ---------------------------------------------------------------------------- the lab
def table(title, rows):
    print(f'\n{title}')
    widths = [max(len(str(r[i])) for r in rows) for i in range(len(rows[0]))]
    for n, r in enumerate(rows):
        print('  ' + '  '.join(str(c).ljust(widths[i]) for i, c in enumerate(r)))
        if n == 0:
            print('  ' + '  '.join('-' * w for w in widths))


def lab19() -> dict:
    """A19 - Adding SOS to a working app: database, back end, API, front end, tests."""
    out = {}
    # ---- 2. the migration touches nothing that was already there
    plain = ai.Database()
    ai.RideService(plain, ai.Trace()).seed(3, 4, True)
    before = {t: rows_of(plain, t) for t in ('drivers', 'rides', 'audit')}
    migrate(plain)
    migrate(plain)                                         # twice: a migration must be safe to repeat
    after = {t: rows_of(plain, t) for t in ('drivers', 'rides', 'audit')}
    table('A19.1  Migration on a database that already holds data',
          [('table', 'rows before', 'rows after', 'unchanged')] +
          [(t, len(before[t]), len(after[t]), before[t] == after[t]) for t in before] +
          [('sos (new)', 'absent', len(rows_of(plain, 'sos')), 'empty')])
    assert all(before[t] == after[t] for t in before)
    # ---- the database refuses what the service forgot to check
    rejected = []
    for label, sql in (('latitude 91', "INSERT INTO sos (ride_id, passenger, lat, lon, source, raised_at) VALUES (1,'x',91,0,'route',0)"),
                       ('resolved with no time', "INSERT INTO sos (ride_id, passenger, lat, lon, source, status, raised_at) VALUES (1,'x',1,1,'route','resolved',0)"),
                       ('unknown ride', "INSERT INTO sos (ride_id, passenger, lat, lon, source, raised_at) VALUES (999,'x',1,1,'route',0)")):
        try:
            plain.execute(sql)
            rejected.append((label, 'ACCEPTED'))
        except sqlite3.IntegrityError as exc:
            rejected.append((label, 'refused: ' + str(exc).split(':')[0][:40]))
    table('A19.2  What the database refuses by itself', [('bad row', 'result')] + rejected)
    assert all(r[1].startswith('refused') for r in rejected)
    plain.close()

    # ---- 3-5. one click, through every layer
    with SosApp(drivers=3, rides=3) as app:
        ride = app.service.get_ride(1)
        app.trace.clear()
        app.screen.sos_button.click(ride)
        first_banner = app.screen.banner
        app.screen.sos_button.click(ride)
        layers = [layer for _, layer, _ in app.trace.hops]
        table('A19.3  One SOS tap, traced', [('step', 'layer', 'what')] + [(i + 1, layer, what) for i, (_, layer, what) in enumerate(app.trace.hops)][:14])
        print(f"\n  first tap: {first_banner!r}\n  second tap: {app.screen.banner!r}")
        assert layers[0] == 'UI button' and 'database' in layers and app.client.requests == 1
        out['banner'] = app.screen.banner

        # ---- 6. the rules, one request each
        ride = app.service.get_ride(3)                 # a fresh ride: ride 1 already has the SOS from the tap above
        passenger, other = ride['passenger'], 'Somebody Else'
        point = {'passenger': passenger, 'lat': 51.9, 'lon': -8.47, 'source': 'device'}
        cases = []

        def call(label, path, body, method='POST'):
            resp = app.client.request(method, path, body)
            cases.append((label, resp.status, resp.headers.get('Idempotent-Replay', '')))
            return resp
        queued = app.service.create_ride({'passenger': 'Brian', 'pickup': 'UCC', 'destination': 'Kent Station', 'distance_km': 3})[0]
        call('ride not started (requested)', f"/api/rides/{queued['id']}/sos", {**point, 'passenger': 'Brian'})
        call('someone else raises it', f"/api/rides/{ride['id']}/sos", {**point, 'passenger': other})
        call('latitude 200', f"/api/rides/{ride['id']}/sos", {**point, 'lat': 200})
        call('latitude as text', f"/api/rides/{ride['id']}/sos", {**point, 'lat': '51.9'})
        call('unknown ride', '/api/rides/999/sos', point)
        created = call('the passenger raises it', f"/api/rides/{ride['id']}/sos", point)
        call('same again (replay)', f"/api/rides/{ride['id']}/sos", point)
        call('someone else ends it', f"/api/sos/{created.body['id']}/resolve", {'passenger': other})
        call('the passenger ends it', f"/api/sos/{created.body['id']}/resolve", {'passenger': passenger})
        call('end it twice', f"/api/sos/{created.body['id']}/resolve", {'passenger': passenger})
        table('A19.4  The rules, one request each', [('request', 'status', 'Idempotent-Replay')] + cases)
        statuses = [c[1] for c in cases]
        assert statuses == [409, 403, 422, 422, 404, 201, 200, 403, 200, 409]
        assert app.db.count('sos', f"ride_id = {ride['id']}") == 1 and app.db.count('audit', f"ride_id = {ride['id']} AND action LIKE 'sos%'") == 2
        out['statuses'] = statuses

        # ---- four taps at the same instant: one row
        other_ride = app.service.get_ride(2)
        gate, answers = threading.Barrier(4), []

        def tap():
            gate.wait()
            answers.append(app.client.post(f"/api/rides/{other_ride['id']}/sos", {**point, 'passenger': other_ride['passenger']}).status)
        threads = [threading.Thread(target=tap) for _ in range(4)]
        [t.start() for t in threads]
        [t.join() for t in threads]
        table('A19.5  Four taps at once', [('status', 'count')] + [(s, answers.count(s)) for s in sorted(set(answers))])
        assert sorted(answers) == [200, 200, 200, 201] and app.db.count('sos', f'ride_id = {other_ride["id"]}') == 1
        out['race'] = sorted(answers)

        # ---- the old features still do what they did
        app.screen.form.update(passenger='Aoife', pickup='UCC', destination='Cork Airport', km='5.8')
        booked = app.screen.book_button.click().result()
        assert booked.status == 201 and booked.body['fare_cents'] == ai.fare_cents(5.8)
        listing = app.client.get('/api/rides?limit=3')
        assert listing.status == 200 and 'X-Total-Count' in listing.headers
        print(f"\n  existing features: Book -> {booked.status} fare {booked.body['fare_cents']}; list -> {listing.status}")

    # ---- the phone's own version of the same rules
    from atlas_go.store import LocalStore                                    # noqa: E402
    with tempfile.TemporaryDirectory() as folder:
        store = LocalStore(Path(folder) / 'state.json')
        store.register('passenger', 'Aoife Rider', 'a@atlas.ie', '085 111 2233', 'ride2026x')
        rows = []
        try:
            store.raise_sos(now=1.0)
            rows.append(('no ride', 'ACCEPTED'))
        except ValueError as exc:
            rows.append(('no ride', 'refused'))
        store.book(0, 2, now=1.0)
        first = store.raise_sos(now=2.0, point=(51.9, -8.47))
        again = store.raise_sos(now=3.0)
        rows += [('first SOS', first['status']), ('second SOS, same ride', 'same record' if again is first else 'NEW RECORD')]
        try:
            store.resolve_sos(first['id'], 'wrong-pass1')
            rows.append(('end with a wrong password', 'ACCEPTED'))
        except ValueError:
            rows.append(('end with a wrong password', 'refused'))
        store.resolve_sos(first['id'], 'ride2026x', now=4.0)
        rows.append(('end with the password', store.sos[0]['status']))
        table('A19.6  The same rules on the phone (LocalStore, no server)', [('situation', 'result')] + rows)
        assert [r[1] for r in rows] == ['refused', 'active', 'same record', 'refused', 'resolved']
        out['phone'] = [r[1] for r in rows]
    return out


def main() -> int:
    print(lab19.__doc__)
    lab19()
    print('\nLab A19 ran and its internal assertions passed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
