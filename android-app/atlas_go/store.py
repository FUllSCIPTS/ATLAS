"""Local JSON persistence and business rules: accounts, rides, food orders, seller kitchens,
bank payments and payouts.

Learned policies run locally (intelligence.py); the UI passes their answers in as plain values.
Bank payments (payments.py, 1.5.0) use the sandbox bank on the phone and are copied to the
PostgreSQL server when the account is connected (backend.py). Every command validates, mutates,
writes the file atomically, and restores the previous in-memory state if the write fails.
"""
from copy import deepcopy
import json
import os
import time
from pathlib import Path
from time import time_ns
from . import accounts as acc
from . import geo
from . import payments as pay
from . import safety
from . import twin as layer2
from .domain import Cart, Catalog, Offer, distance, fare, PLACES

SCREENS = ('welcome', 'login', 'register', 'home', 'ride', 'share', 'food', 'menu', 'cart', 'active_ride',
           'active_order', 'activity', 'profile', 'privacy', 'intelligence', 'map', 'driver', 'seller',
           'seller_menu', 'account', 'twin', 'wallet', 'sos', 'safety')
OFFER_IDS = ('pool-1', 'pool-2', 'pool-3', 'pool-4')
FIRST_SELLER_KITCHEN = 3
MAX_DISHES = 30


def _priced(base: int, multiplier: float) -> int:
    """Fare in cents after a capped Layer 2 price multiplier, rounded to 10 cents."""
    return base if multiplier == 1.0 else int(round(base * multiplier / 10.0)) * 10


def _is_point(value) -> bool:
    return isinstance(value, list) and len(value) == 2 and all(type(v) in (int, float) for v in value) \
        and geo.valid_point(value)


class LocalStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.failures = {}          # email -> [count, locked_until]; memory only
        self.reset(save=False, preserve_diagnostic=True)
        if self.path.exists():
            self.load()

    # ------------------------------------------------------------------ lifecycle
    def reset(self, save: bool = True, preserve_diagnostic: bool = False) -> None:
        before = self.snapshot() if save and hasattr(self, 'cart') else None
        self.accounts = []
        self.kitchens = []
        self.session = None
        self.guest = False
        self.catalog = Catalog()
        self.cart = Cart(catalog=self.catalog)
        self.history = []
        self.ride = None
        self.order = None
        self.ui = {}
        self.twin = layer2.default_state()     # Layer 2 (1.3.0): on/off, agent status, Guardian log
        self.payments = []                     # bank payments (1.5.0): authorised, captured, voided
        self.payouts = []                      # payouts to drivers' and sellers' bank accounts
        self.server_url = ''                   # ATLAS server (PostgreSQL back end); '' = this phone only
        self.prebooks = []                     # pre-booked rides (1.6.0): scheduled, dispatched, cancelled, missed
        self.sos = []                          # SOS events (1.6.0): where and when help was asked for
        self.offers = [
            # Each carpool already carries one rider, who is dropped before you (see geo.last_stage).
            Offer('pool-1', 'Alex · Electric hatchback', 0, 1, 3, 490, 3, 'Ciara', 'Bishopstown', 'Grand Parade'),
            Offer('pool-2', 'Sam · Hybrid sedan', 0, 1, 2, 590, 2, 'Daniel', 'Wilton', 'Mardyke'),
            Offer('pool-3', 'Jordan · Electric sedan', 1, 3, 3, 990, 3, 'Méabh', 'MacCurtain St', 'Douglas'),
            Offer('pool-4', 'Taylor · Hybrid hatchback', 2, 0, 2, 690, 2, 'Fionn', 'Montenotte', 'Grand Parade'),
        ]
        if save:
            self.commit(before)
            if not preserve_diagnostic:
                self.path.with_suffix('.invalid.json').unlink(missing_ok=True)

    def load(self) -> None:
        try:
            data = json.loads(self.path.read_text(encoding='utf-8'))
            self.validate(data)
            self.accounts = data.get('accounts', [])
            self.kitchens = data.get('kitchens', [])
            self.catalog = Catalog(self.kitchens)
            self.session = data.get('session')
            self.guest = bool(data.get('guest', False))
            self.cart = Cart(data.get('cart', {}), self.catalog)
            self.history = data.get('history', [])
            self.ride, self.order = data.get('ride'), data.get('order')
            self.ui = data.get('ui', {})
            # 1.2.0 files have no Layer 2 state; a damaged one is reset on its own (rides are kept).
            twin = data.get('twin')
            self.twin = twin if layer2.valid_state(twin) else layer2.default_state()
            # 1.4.0 and earlier files have no payments, payouts or server link.
            self.payments = data.get('payments', [])
            self.payouts = data.get('payouts', [])
            self.server_url = data.get('server_url', '')
            # 1.5.0 and earlier files have no pre-booked rides or SOS events.
            self.prebooks = data.get('prebooks', [])
            self.sos = data.get('sos', [])
            for offer in self.offers:
                seats = data.get('seats', {}).get(offer.id, offer.capacity)
                offer.seats = max(0, min(offer.capacity, int(seats)))
            if self.session is not None and self.account(self.session) is None:
                self.session = None
        except (ValueError, TypeError, KeyError, AttributeError):
            # Preserve unreadable data for diagnostics; start a clean local state.
            self.path.replace(self.path.with_suffix('.invalid.json'))
            self.reset(preserve_diagnostic=True)

    @staticmethod
    def validate(data: dict) -> None:
        """Reject structurally damaged state before screens read its fields."""
        if not isinstance(data, dict):
            raise ValueError('State must be an object.')
        if not isinstance(data.get('history', []), list) or not isinstance(data.get('ui', {}), dict):
            raise ValueError('Invalid history or screen state.')
        if not isinstance(data.get('seats', {}), dict):
            raise ValueError('Invalid seat state.')
        accounts = data.get('accounts', [])
        if not isinstance(accounts, list):
            raise ValueError('Invalid accounts.')
        ids, emails = set(), set()
        for a in accounts:
            if not isinstance(a, dict) or not isinstance(a.get('id'), str) or not a['id'].startswith('U-'):
                raise ValueError('Invalid account identity.')
            if a.get('role') not in acc.ROLES or a['id'] in ids:
                raise ValueError('Invalid account role.')
            for key in ('name', 'email', 'phone', 'salt', 'hash'):
                if not isinstance(a.get(key), str) or not a[key]:
                    raise ValueError('Invalid account field.')
            if a['email'] in emails or type(a.get('iterations')) is not int or a['iterations'] < 1000:
                raise ValueError('Invalid account credentials.')
            if 'bank' in a and not pay.valid_bank(a['bank'], a['role']):
                raise ValueError('Invalid linked bank account.')
            link = a.get('server')
            if link is not None and (not isinstance(link, dict) or
                                     not all(isinstance(link.get(k), str) and link[k] for k in ('id', 'token'))):
                raise ValueError('Invalid server link.')
            if 'trusted' in a and not safety.valid_trusted(a['trusted']):
                raise ValueError('Invalid trusted contact.')
            ids.add(a['id'])
            emails.add(a['email'])
            if a['role'] == 'driver':
                d = a.get('driver')
                if not isinstance(d, dict) or not all(isinstance(d.get(k), str) for k in ('vehicle', 'plate', 'licence')):
                    raise ValueError('Invalid driver profile.')
                if d.get('seats') not in range(1, 9) or type(d.get('online')) is not bool or d.get('base') not in range(len(PLACES)):
                    raise ValueError('Invalid driver status.')
                for key in ('offered', 'accepted', 'earnings', 'trips'):
                    if type(d.get(key, 0)) is not int or d.get(key, 0) < 0:
                        raise ValueError('Invalid driver counters.')
                if d.get('accepted', 0) > d.get('offered', 0):
                    raise ValueError('Invalid driver acceptance history.')
                if d.get('location') is not None and not _is_point(d['location']):
                    raise ValueError('Invalid driver location.')
        kitchens = data.get('kitchens', [])
        if not isinstance(kitchens, list):
            raise ValueError('Invalid kitchens.')
        kitchen_ids = {0, 1, 2}
        for k in kitchens:
            if not isinstance(k, dict) or type(k.get('id')) is not int or k['id'] < FIRST_SELLER_KITCHEN or k['id'] in kitchen_ids:
                raise ValueError('Invalid kitchen identity.')
            if not all(isinstance(k.get(f), str) and k[f] for f in ('name', 'cuisine', 'registration')):
                raise ValueError('Invalid kitchen details.')
            if not isinstance(k.get('owner'), str) or k.get('place') not in range(len(PLACES)):
                raise ValueError('Invalid kitchen owner or place.')
            if type(k.get('prep')) is not int or not 5 <= k['prep'] <= 90 or type(k.get('open', True)) is not bool:
                raise ValueError('Invalid kitchen preparation time.')
            dishes = k.get('dishes', [])
            if not isinstance(dishes, list) or len(dishes) > MAX_DISHES:
                raise ValueError('Invalid kitchen menu.')
            for d in dishes:
                if not isinstance(d, dict) or not isinstance(d.get('id'), str) or not d['id'].startswith(f"k{k['id']}-"):
                    raise ValueError('Invalid dish identity.')
                if not isinstance(d.get('name'), str) or not isinstance(d.get('detail'), str):
                    raise ValueError('Invalid dish text.')
                if type(d.get('price')) is not int or not 50 <= d['price'] <= 20000:
                    raise ValueError('Invalid dish price.')
            for key in ('orders', 'sales'):
                if type(k.get(key, 0)) is not int or k.get(key, 0) < 0:
                    raise ValueError('Invalid kitchen counters.')
            kitchen_ids.add(k['id'])
        catalog = Catalog(kitchens)
        if data.get('session') is not None and data['session'] not in ids:
            raise ValueError('Invalid session.')
        if type(data.get('guest', False)) is not bool:
            raise ValueError('Invalid guest flag.')
        Cart(data.get('cart', {}), catalog)
        payments, payouts = data.get('payments', []), data.get('payouts', [])
        if not isinstance(payments, list) or not isinstance(payouts, list) or \
                not all(pay.valid_payment(p) for p in payments) or not all(pay.valid_payout(o) for o in payouts):
            raise ValueError('Invalid payment or payout.')
        paid = {p['id']: p for p in payments}
        if len(paid) != len(payments) or len({o['id'] for o in payouts}) != len(payouts):
            raise ValueError('Duplicate payment or payout.')
        lines = pay.entries(payments, payouts)
        if not pay.balanced(lines) or any(pay.balance(lines, pay.payable(o['account'])) < 0 for o in payouts):
            raise ValueError('The payment ledger does not balance.')
        if not isinstance(data.get('server_url', ''), str):
            raise ValueError('Invalid server address.')
        prebooks, events = data.get('prebooks', []), data.get('sos', [])
        if not isinstance(prebooks, list) or not all(safety.valid_prebook(p, OFFER_IDS) for p in prebooks) or \
                len({p['id'] for p in prebooks}) != len(prebooks):
            raise ValueError('Invalid pre-booked ride.')
        if any(p['status'] == 'scheduled' and p['account'] not in ids for p in prebooks):
            raise ValueError('A pre-booked ride belongs to no account.')
        held = {}
        for p in prebooks:
            if p['status'] == 'scheduled' and p['offer']:
                held[p['offer']] = held.get(p['offer'], 0) + p['party']
        capacity = {'pool-1': 3, 'pool-2': 2, 'pool-3': 3, 'pool-4': 2}
        seats = data.get('seats', {})
        if any(n > capacity[o] - min(capacity[o], max(0, int(seats.get(o, capacity[o])))) for o, n in held.items()):
            raise ValueError('Pre-booked seats are not held.')
        if not isinstance(events, list) or not all(safety.valid_sos(e) for e in events) or \
                len({e['id'] for e in events}) != len(events):
            raise ValueError('Invalid SOS record.')
        records = list(data.get('history', []))
        active = [data[k] for k in ('ride', 'order') if data.get(k) is not None]
        records += active
        for record in records:
            if not isinstance(record, dict):
                raise ValueError('Invalid booking record.')
            if record.get('payment') is not None:
                # A booking paid by bank points at its payment, and the two must tell the same story.
                payment = paid.get(record['payment'])
                expected = ('authorised',) if any(record is r for r in active) else \
                    ('voided',) if record.get('status') == 'Cancelled' else ('captured', 'refunded')
                if payment is None or payment['ref'] != record.get('id') or payment['status'] not in expected \
                        or payment['amount'] != record.get('fare'):
                    raise ValueError('Booking and payment do not match.')
            if not isinstance(record.get('id'), str) or type(record.get('fare')) is not int or record['fare'] < 0:
                raise ValueError('Invalid booking identity or total.')
            if type(record.get('stage')) is not int or record['stage'] not in range(4):
                raise ValueError('Invalid booking stage.')
            if 'restaurant' in record and record['stage'] > 2:
                raise ValueError('Invalid order stage.')
            if record.get('passenger') is not None and not isinstance(record['passenger'], str):
                raise ValueError('Invalid passenger.')
            if type(record.get('pending', False)) is not bool:
                raise ValueError('Invalid pending flag.')
            live = record.get('live')
            if live is not None and (not isinstance(live, dict) or type(live.get('t')) not in (int, float)):
                raise ValueError('Invalid live journey.')
            if 'restaurant' in record:
                if record['restaurant'] not in kitchen_ids or record.get('address') not in range(len(PLACES)):
                    raise ValueError('Invalid food route.')
                if not isinstance(record.get('items'), dict) or not record['items']:
                    raise ValueError('Invalid food items.')
                Cart(record['items'], catalog)
                courier = record.get('courier')
                if courier is not None and (not isinstance(courier, dict) or
                                            any(type(v) is not int or v < 0 for v in courier.values())):
                    raise ValueError('Invalid courier plan.')
                if live is not None and not _is_point(live.get('kitchen')):
                    raise ValueError('Invalid kitchen location.')
            else:
                distance(record.get('pickup', -1), record.get('destination', -1))
                if record.get('party') not in (1, 2) or not isinstance(record.get('driver'), str):
                    raise ValueError('Invalid rider or driver.')
                if type(record.get('shared')) is not bool:
                    raise ValueError('Invalid ride kind.')
                if record['shared'] and record.get('offer') not in OFFER_IDS:
                    raise ValueError('Invalid shared offer.')
                co = record.get('co')
                if co is not None:
                    if not record['shared'] or not isinstance(co, dict) or not _is_point(co.get('point')):
                        raise ValueError('Invalid rider already on board.')
                    if not all(isinstance(co.get(k), str) and co[k] for k in ('name', 'drop')) or \
                            type(co.get('dropped')) is not bool:
                        raise ValueError('Invalid rider already on board.')
                    # The earlier rider is dropped exactly when your journey enters its last leg.
                    if co['dropped'] != (record['stage'] == 3 or record.get('status') == 'Completed'):
                        raise ValueError('The earlier rider must be dropped before you.')
                if record['stage'] > geo.last_stage(record):
                    raise ValueError('Invalid booking stage.')
                if not isinstance(record.get('why', ''), str):
                    raise ValueError('Invalid dispatch explanation.')
                surge = record.get('surge', 1.0)
                if type(surge) not in (int, float) or not 1.0 <= surge <= layer2.PRICE_CAP:
                    raise ValueError('Invalid price multiplier.')
                if record.get('twin') is not None and not isinstance(record['twin'], dict):
                    raise ValueError('Invalid twin record.')
                if not isinstance(record.get('prebook', ''), str):
                    raise ValueError('Invalid pre-booking reference.')
                if record.get('driver_id') is not None and not isinstance(record['driver_id'], str):
                    raise ValueError('Invalid driver account.')
                if live is not None and not _is_point(live.get('start')):
                    raise ValueError('Invalid driver start.')
        ui = data.get('ui', {})
        for key, bound in {'pickup': 4, 'destination': 4, 'address': 4}.items():
            if key in ui and (type(ui[key]) is not int or ui[key] not in range(bound)):
                ui.pop(key)
        if 'restaurant' in ui and ui['restaurant'] not in kitchen_ids:
            ui.pop('restaurant')
        if ui.get('party', 1) not in (1, 2):
            ui.pop('party')
        if 'comfort' in ui and type(ui['comfort']) is not bool:
            ui.pop('comfort')
        if 'outlook_day' in ui and (type(ui['outlook_day']) is not int or not -400 <= ui['outlook_day'] <= 400):
            ui.pop('outlook_day')
        if ui.get('screen', 'home') not in SCREENS:
            ui.pop('screen')

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = dict(cart=self.cart.items, history=self.history, ride=self.ride, order=self.order,
                       seats={o.id: o.seats for o in self.offers}, ui=self.ui, accounts=self.accounts,
                       kitchens=self.kitchens, session=self.session, guest=self.guest, twin=self.twin,
                       payments=self.payments, payouts=self.payouts, server_url=self.server_url,
                       prebooks=self.prebooks, sos=self.sos)
        temporary = self.path.with_suffix('.tmp')
        with temporary.open('w', encoding='utf-8') as stream:
            json.dump(payload, stream, ensure_ascii=False)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(self.path)

    def snapshot(self):
        return deepcopy((self.cart, self.history, self.ride, self.order, self.ui, self.offers,
                         self.accounts, self.kitchens, self.session, self.guest, self.twin,
                         self.payments, self.payouts, self.server_url, self.prebooks, self.sos))

    def _restore(self, before) -> None:
        (self.cart, self.history, self.ride, self.order, self.ui, self.offers,
         self.accounts, self.kitchens, self.session, self.guest, self.twin,
         self.payments, self.payouts, self.server_url, self.prebooks, self.sos) = before
        self.catalog = Catalog(self.kitchens)
        self.cart.catalog = self.catalog

    def commit(self, before) -> None:
        try:
            self.save()
        except OSError:
            if before is not None:
                self._restore(before)
            raise

    def _refresh_catalog(self) -> None:
        self.catalog = Catalog(self.kitchens)
        self.cart.catalog = self.catalog

    # ------------------------------------------------------------------ accounts
    def account(self, account_id: str | None) -> dict | None:
        return next((a for a in self.accounts if a['id'] == account_id), None)

    @property
    def user(self) -> dict | None:
        return self.account(self.session)

    @property
    def role(self) -> str:
        return self.user['role'] if self.user else 'passenger'

    @property
    def signed_in(self) -> bool:
        return self.user is not None or self.guest

    def register(self, role: str, name: str, email: str, phone: str, password: str, *,
                 vehicle: str = '', plate: str = '', licence: str = '', seats='4', base: int = 1,
                 kitchen: str = '', cuisine: str = '', registration: str = '', place: int = 1,
                 prep='15', now: float | None = None) -> dict:
        if role not in acc.ROLES:
            raise ValueError('Choose passenger, driver or food seller.')
        name, email, phone = acc.clean_name(name), acc.clean_email(email), acc.clean_phone(phone)
        acc.check_password(password)
        if any(a['email'] == email for a in self.accounts):
            raise ValueError('An account with this email already exists on this device. Sign in instead.')
        account = dict(id=f'U-{time_ns()}', role=role, name=name, email=email, phone=phone,
                       created=int(now if now is not None else time.time()), **acc.hash_password(password))
        new_kitchen = None
        if role == 'driver':
            account['driver'] = dict(vehicle=acc.clean_name(vehicle, 'Vehicle', 3, 40), plate=acc.clean_plate(plate),
                                     licence=acc.clean_licence(licence), seats=acc.parse_int(seats, 'Seats', 1, 8),
                                     base=self._place(base), online=False, offered=0, accepted=0, earnings=0,
                                     trips=0, location=None)
        elif role == 'seller':
            new_kitchen = dict(id=max([k['id'] for k in self.kitchens] + [FIRST_SELLER_KITCHEN - 1]) + 1,
                               owner=account['id'], name=acc.clean_name(kitchen, 'Kitchen name', 2, 40),
                               cuisine=acc.clean_name(cuisine, 'Cuisine', 3, 40),
                               registration=acc.clean_business(registration), place=self._place(place),
                               prep=acc.parse_int(prep, 'Preparation time', 5, 90), open=True, dishes=[],
                               orders=0, sales=0)
            if any(k['name'].lower() == new_kitchen['name'].lower() for k in self.kitchens) or \
                    new_kitchen['name'].lower() in (n.name.lower() for n in Catalog().kitchens.values()):
                raise ValueError('A kitchen with this name already exists.')
            account['seller'] = dict(kitchen=new_kitchen['id'])
        before = self.snapshot()
        self.accounts.append(account)
        if new_kitchen:
            self.kitchens.append(new_kitchen)
            self._refresh_catalog()
        self.session, self.guest = account['id'], False
        self.commit(before)
        return account

    @staticmethod
    def _place(value) -> int:
        if type(value) is not int or value not in range(len(PLACES)):
            raise ValueError('Choose one of the saved places.')
        return value

    def login(self, email: str, password: str, now: float | None = None) -> dict:
        now = time.time() if now is None else now
        email = (email or '').strip().lower()
        count, until = self.failures.get(email, [0, 0])
        if until > now:
            raise ValueError(f'Too many attempts. Try again in {int(until - now) + 1} seconds.')
        account = next((a for a in self.accounts if a['email'] == email), None)
        if account is None or not acc.verify_password(password or '', account):
            count += 1
            self.failures[email] = [0, now + acc.LOCKOUT_SECONDS] if count >= acc.MAX_FAILED_LOGINS else [count, 0]
            raise ValueError('Email or password is not correct.')
        self.failures.pop(email, None)
        before = self.snapshot()
        self.session, self.guest = account['id'], False
        self.commit(before)
        return account

    def continue_as_guest(self) -> None:
        before = self.snapshot()
        self.session, self.guest = None, True
        self.commit(before)

    def logout(self) -> None:
        before = self.snapshot()
        # Drivers stay online after signing out so passengers on this phone can still be matched;
        # they go offline with the Go offline button.
        self.session, self.guest = None, False
        self.commit(before)

    def delete_account(self, password: str) -> None:
        user = self.user
        if not user:
            raise ValueError('Sign in first.')
        if not acc.verify_password(password or '', user):
            raise ValueError('Password is not correct.')
        if self.ride and user['id'] in (self.ride.get('passenger'), self.ride.get('driver_id')):
            raise ValueError('Finish or cancel the active ride first.')
        mine = self.kitchen_of(user)
        if self.order and (self.order.get('passenger') == user['id'] or (mine and self.order['restaurant'] == mine['id'])):
            raise ValueError('Complete the active food order first.')
        if pay.wallet(user['id'], self.payments, self.payouts)['balance'] > 0:
            raise ValueError('Pay out your balance to your bank account first.')
        before = self.snapshot()
        self.accounts = [a for a in self.accounts if a['id'] != user['id']]
        for payment in self.payments:
            if payment['payer'] == user['id']:
                payment['payer'] = 'deleted'         # the amounts stay for the ledger; the person does not
        if mine:
            # Keep the kitchen record so past orders still show its name, but close it.
            mine['open'] = False
            mine['owner'] = 'deleted'
            mine['registration'] = 'REMOVED'
            self._refresh_catalog()
        for record in self.history:
            if record.get('passenger') == user['id']:
                record['passenger'] = 'deleted'
        for p in self.prebooks:
            if p['account'] == user['id'] and p['status'] == 'scheduled':
                self._release_prebook(p)
        self.prebooks = [p for p in self.prebooks if p['account'] != user['id']]
        self.sos = [e for e in self.sos if e.get('account') != user['id']]      # where they asked for help goes with them
        self.session = None
        self.commit(before)

    # ------------------------------------------------------------------ drivers
    def online_drivers(self) -> list[dict]:
        busy = self.ride.get('driver_id') if self.ride else None
        return [a for a in self.accounts if a['role'] == 'driver' and a['driver']['online'] and a['id'] != busy]

    def driver_position(self, account: dict):
        d = account['driver']
        return tuple(d['location']) if d.get('location') else geo.PLACE_COORDS[d['base']]

    def set_online(self, online: bool, base: int | None = None) -> None:
        user = self.user
        if not user or user['role'] != 'driver':
            raise ValueError('Only drivers can go online.')
        before = self.snapshot()
        user['driver']['online'] = bool(online)
        if base is not None:
            user['driver']['base'] = self._place(base)
        self.commit(before)

    def update_location(self, point) -> None:
        """Latest device position for a signed-in driver (kept on this device only)."""
        user = self.user
        if not user or user['role'] != 'driver' or not geo.valid_point(point):
            return
        before = self.snapshot()
        user['driver']['location'] = [round(float(point[0]), 6), round(float(point[1]), 6)]
        self.commit(before)

    def driver_job(self) -> dict | None:
        user = self.user
        if user and self.ride and self.ride.get('driver_id') == user['id']:
            return self.ride
        return None

    def driver_respond(self, accept: bool, fallback: dict | None = None, now: float | None = None) -> None:
        """Registered driver accepts or declines the pending request. On decline the UI passes the
        next driver chosen by the dispatch policy as fallback=dict(driver, why, start, driver_id)."""
        job = self.driver_job()
        if not job or not job.get('pending'):
            raise ValueError('There is no ride request waiting for you.')
        if not accept and not fallback:
            raise ValueError('No other driver is available.')
        now = time.time() if now is None else now
        before = self.snapshot()
        d = self.user['driver']
        d['offered'] += 1
        if accept:
            d['accepted'] += 1
            job['pending'] = False
            job['live'] = dict(start=list(self.driver_position(self.user)), t=now)
        else:
            job.setdefault('declined', []).append(self.user['id'])
            job.update(driver=fallback['driver'], why=fallback['why'], driver_id=fallback.get('driver_id'),
                       pending=bool(fallback.get('driver_id')))
            job['live'] = dict(start=list(fallback['start']), t=now)
        self.commit(before)

    def driver_advance(self, now: float | None = None) -> None:
        job = self.driver_job()
        if not job or job.get('pending'):
            raise ValueError('Accept a ride request first.')
        self._advance_ride(now=now)

    # ------------------------------------------------------------------ rides
    def book(self, pickup: int, destination: int, comfort: bool = False,
             offer_id: str | None = None, party: int = 1,
             driver: str | None = None, why: str | None = None,
             driver_id: str | None = None, start=None, now: float | None = None,
             multiplier: float = 1.0, twin: dict | None = None, log=(), pay_by_bank: bool = False) -> None:
        if self.ride:
            raise ValueError('Finish or cancel your active ride first.')
        if self.user and self.user['role'] != 'passenger':
            raise ValueError('Sign in as a passenger (or continue as a guest) to book rides.')
        distance(pickup, destination)
        if party not in (1, 2):
            raise ValueError('Choose one or two seats.')
        offer = next((o for o in self.offers if o.id == offer_id), None)
        if offer_id and (not offer or not offer.matches(pickup, destination, party)):
            raise ValueError('This shared ride does not match your route or seats.')
        if type(multiplier) not in (int, float) or not 1.0 <= multiplier <= layer2.PRICE_CAP:
            raise ValueError('Prices are capped at twice the base fare.')
        if driver_id is not None:
            account = self.account(driver_id)
            if not account or account['role'] != 'driver' or not account['driver']['online']:
                raise ValueError('That driver is no longer online.')
        now = time.time() if now is None else now
        ride_id = f'R-{time_ns()}'
        amount = offer.price * party if offer else _priced(fare(pickup, destination, comfort), multiplier)
        details = dict(offer=offer_id, party=party) if offer else \
            dict(pickup=pickup, destination=destination, comfort=bool(comfort), multiplier=float(multiplier))
        # Authorise before anything changes: a declined payment must leave no reservation behind.
        payment = self._authorise('shared' if offer else 'ride', ride_id, amount, details, now) if pay_by_bank else None
        before = self.snapshot()
        co = None
        if offer:
            offer.reserve(party)
            if offer.co_rider:
                # The car is already carrying offer.co_rider: it comes from where they boarded.
                start = geo.ZONE_COORDS[offer.co_from]
                co = dict(name=offer.co_rider, boarded=offer.co_from, drop=offer.co_drop,
                          point=list(geo.ZONE_COORDS[offer.co_drop]), dropped=False)
            else:
                start = (geo.PLACE_COORDS[pickup][0] - 0.004, geo.PLACE_COORDS[pickup][1] - 0.006)
        elif start is None:
            start = (geo.PLACE_COORDS[pickup][0] + 0.006, geo.PLACE_COORDS[pickup][1] + 0.008)
        self.ride = dict(id=ride_id, pickup=pickup, destination=destination,
                         shared=bool(offer), party=party, offer=offer_id,
                         driver=offer.driver if offer else (driver or 'Morgan · ATLAS demo driver'),
                         fare=amount,
                         stage=0,
                         passenger=self.session, driver_id=None if offer else driver_id,
                         pending=bool(driver_id) and not offer,
                         live=dict(start=[round(start[0], 6), round(start[1], 6)], t=now))
        if why and not offer:
            self.ride['why'] = why
        if co:
            self.ride['co'] = co
        if not offer and multiplier != 1.0:
            self.ride['surge'] = round(float(multiplier), 2)
        if twin and not offer:
            self.ride['twin'] = dict(twin)
        if payment:
            self.payments.append(payment)
            self.ride['payment'] = payment['id']
        self._log(log)
        self.commit(before)

    def _advance_ride(self, cancel: bool = False, now: float | None = None) -> None:
        now = time.time() if now is None else now
        before = self.snapshot()
        ride = self.ride
        last = geo.last_stage(ride)
        if cancel or ride['stage'] == last:
            if not cancel and geo.has_co_rider(ride) and not ride['co']['dropped']:
                raise ValueError('The rider who was already in the car is dropped first.')
            if ride['shared']:
                # The seats are free again once you leave the car, whether you cancel or arrive.
                next(o for o in self.offers if o.id == ride['offer']).release(ride['party'])
            ride['status'] = 'Cancelled' if cancel else 'Completed'
            ride['pending'] = False
            if ride.get('payment'):
                # Cancelled: release the authorisation. Completed: capture it for the driver.
                pay.move(self.payment(ride['payment']), 'voided' if cancel else 'captured', now,
                         payee=None if cancel else (ride.get('driver_id') or 'fleet'))
            if not cancel and ride.get('driver_id'):
                driver = self.account(ride['driver_id'])
                if driver:
                    driver['driver']['earnings'] += ride['fare']
                    driver['driver']['trips'] += 1
                    driver['driver']['location'] = [*geo.PLACE_COORDS[ride['destination']]]
            self.history.append(ride)
            self.ride = None
        else:
            ride['stage'] += 1
            ride['live']['t'] = now
            if geo.has_co_rider(ride) and ride['stage'] == 3:
                ride['co']['dropped'] = True      # earlier rider leaves the car before your last leg
        self.commit(before)

    def advance_ride(self, cancel: bool = False, now: float | None = None) -> None:
        if not self.ride:
            return
        if not cancel and self.ride.get('driver_id') and self.ride.get('pending'):
            raise ValueError('The driver has not accepted this ride yet.')
        self._advance_ride(cancel, now)

    # ------------------------------------------------------------------ Layer 2 (twin) state
    def _log(self, entries) -> None:
        for e in entries:
            self.twin['log'].append(dict(e))
            self.twin['checks'] += e['result'] in ('passed', 'blocked')
            self.twin['blocks'] += e['result'] == 'blocked'
        del self.twin['log'][:-layer2.LOG_LIMIT]

    def twin_record(self, entries, status: dict | None = None) -> None:
        """Append Guardian log entries (and optionally agent status) in one saved step."""
        before = self.snapshot()
        self._log(entries)
        if status:
            if set(status) - {'dispatch', 'pricing'} or any(v not in ('active', 'retesting') for v in status.values()):
                raise ValueError('Unknown agent status.')
            self.twin['status'].update(status)
        self.commit(before)

    def set_layer2(self, enabled: bool) -> None:
        before = self.snapshot()
        self.twin['enabled'] = bool(enabled)
        self._log([layer2.entry('Guardian', 'Layer 2 switched ' + ('on' if enabled else 'off') +
                                ('' if enabled else ' · Layer 1 serves every ride'), 'info')])
        self.commit(before)

    # ------------------------------------------------------------------ food
    def kitchen_of(self, account: dict | None) -> dict | None:
        if not account or account['role'] != 'seller':
            return None
        return next((k for k in self.kitchens if k['id'] == account['seller']['kitchen']), None)

    def kitchen_prep(self, kitchen: int) -> int:
        return self.catalog.kitchens[kitchen].prep

    def _my_kitchen(self) -> dict:
        kitchen = self.kitchen_of(self.user)
        if not kitchen:
            raise ValueError('Sign in as a food seller first.')
        return kitchen

    def add_dish(self, name: str, detail: str, price: str) -> str:
        kitchen = self._my_kitchen()
        live = [d for d in kitchen['dishes'] if not d.get('archived')]
        if len(kitchen['dishes']) >= MAX_DISHES or len(live) >= 20:
            raise ValueError('A kitchen can list up to 20 dishes.')
        name = acc.clean_name(name, 'Dish name', 2, 40)
        detail = acc.clean_name(detail, 'Description', 3, 60)
        cents = acc.parse_price(price)
        if any(d['name'].lower() == name.lower() and not d.get('archived') for d in kitchen['dishes']):
            raise ValueError('This dish is already on your menu.')
        before = self.snapshot()
        dish_id = f"k{kitchen['id']}-{len(kitchen['dishes']) + 1}"
        kitchen['dishes'].append(dict(id=dish_id, name=name, detail=detail, price=cents))
        self._refresh_catalog()
        self.commit(before)
        return dish_id

    def archive_dish(self, dish_id: str) -> None:
        kitchen = self._my_kitchen()
        dish = next((d for d in kitchen['dishes'] if d['id'] == dish_id), None)
        if not dish:
            raise ValueError('Unknown dish.')
        before = self.snapshot()
        dish['archived'] = True
        if dish_id in self.cart.items:
            self.cart.items.pop(dish_id)
        self._refresh_catalog()
        self.commit(before)

    def update_kitchen(self, open_: bool | None = None, prep=None) -> None:
        kitchen = self._my_kitchen()
        before = self.snapshot()
        if open_ is not None:
            kitchen['open'] = bool(open_)
        if prep is not None:
            kitchen['prep'] = acc.parse_int(prep, 'Preparation time', 5, 90)
        self._refresh_catalog()
        self.commit(before)

    def update_cart(self, operation: str, item: str | None = None) -> None:
        before = self.snapshot()
        if operation == 'add':
            if item in self.catalog.archived:
                raise ValueError('This dish is no longer available.')
            if item in self.catalog.dishes and not self.catalog.kitchens[self.catalog.dishes[item].restaurant].open:
                raise ValueError('This kitchen is closed right now.')
            self.cart.add(item)
        elif operation == 'remove':
            self.cart.remove(item)
        elif operation == 'clear':
            self.cart.clear()
        else:
            raise ValueError('Unknown basket operation.')
        self.commit(before)

    def checkout(self, address: int, courier: dict | None = None, now: float | None = None,
                 pay_by_bank: bool = False) -> None:
        if self.order:
            raise ValueError('Complete the active food order first.')
        if self.user and self.user['role'] != 'passenger':
            raise ValueError('Sign in as a passenger (or continue as a guest) to order food.')
        if address not in range(len(PLACES)):
            raise ValueError('Choose a delivery place.')
        if not self.cart.items:
            raise ValueError('Add food to your basket first.')
        kitchen = self.catalog.kitchens[self.cart.restaurant]
        if not kitchen.open:
            raise ValueError('This kitchen is closed right now.')
        now = time.time() if now is None else now
        order_id = f'F-{time_ns()}'
        payment = self._authorise('food', order_id, self.cart.total(),
                                  dict(kitchen=kitchen.id, items=self.cart.items.copy()), now) if pay_by_bank else None
        before = self.snapshot()
        point = geo.KITCHEN_COORDS[kitchen.id] if kitchen.id < len(geo.KITCHEN_COORDS) else \
            (geo.PLACE_COORDS[kitchen.place][0] + 0.0012, geo.PLACE_COORDS[kitchen.place][1] - 0.0016)
        self.order = dict(id=order_id, restaurant=self.cart.restaurant,
                          address=address, fare=self.cart.total(), items=self.cart.items.copy(), stage=0,
                          passenger=self.session, pending=kitchen.owner is not None,
                          live=dict(kitchen=[point[0], point[1]], t=now))
        if courier:
            self.order['courier'] = dict(courier)
        if payment:
            self.payments.append(payment)
            self.order['payment'] = payment['id']
        self.cart.clear()
        self.commit(before)

    def seller_order(self) -> dict | None:
        kitchen = self.kitchen_of(self.user)
        if kitchen and self.order and self.order['restaurant'] == kitchen['id']:
            return self.order
        return None

    def seller_accept(self, now: float | None = None) -> None:
        order = self.seller_order()
        if not order or not order.get('pending'):
            raise ValueError('There is no new order waiting for you.')
        before = self.snapshot()
        order['pending'] = False
        order['live']['t'] = time.time() if now is None else now
        self.commit(before)

    def seller_ready(self, now: float | None = None) -> None:
        order = self.seller_order()
        if not order or order.get('pending') or order['stage'] != 0:
            raise ValueError('Accept the order and prepare it first.')
        self._advance_order(now)

    def _advance_order(self, now: float | None = None) -> None:
        now = time.time() if now is None else now
        before = self.snapshot()
        order = self.order
        if order['stage'] == 2:
            order['status'] = 'Delivered'
            mine = next((k for k in self.kitchens if k['id'] == order['restaurant']), None)
            if mine:
                mine['orders'] = mine.get('orders', 0) + 1
                mine['sales'] = mine.get('sales', 0) + order['fare'] - 250
            if order.get('payment'):
                owner = mine.get('owner') if mine else None
                pay.move(self.payment(order['payment']), 'captured', now,
                         payee=owner if owner and self.account(owner) else f"kitchen-{order['restaurant']}")
            self.history.append(order)
            self.order = None
        else:
            order['stage'] += 1
            order.setdefault('live', dict(kitchen=list(geo.KITCHEN_COORDS[0]), t=now))['t'] = now
        self.commit(before)

    def advance_order(self, now: float | None = None) -> None:
        if not self.order:
            return
        if self.order.get('pending'):
            raise ValueError('The kitchen has not accepted this order yet.')
        if self.order['stage'] == 0 and self.order['restaurant'] >= FIRST_SELLER_KITCHEN and \
                not (self.user and self.kitchen_of(self.user) and self.seller_order()):
            raise ValueError('The kitchen marks the food ready for the courier.')
        self._advance_order(now)

    # ------------------------------------------------------------------ live progress
    def tick(self, now: float | None = None) -> bool:
        """Advance simulated journeys whose time-lapse leg has finished. Registered drivers and
        sellers advance their own stages. Returns True when something changed."""
        now = time.time() if now is None else now
        changed = False
        ride = self.ride
        if ride and not ride.get('pending') and not ride.get('driver_id') and ride.get('live'):
            _, progress = geo.ride_position(ride, now)
            if progress >= 1.0:
                self._advance_ride(now=now)
                changed = True
        order = self.order
        if order and not order.get('pending') and order.get('live'):
            seller_stage = order['stage'] == 0 and order['restaurant'] >= FIRST_SELLER_KITCHEN
            if not seller_stage:
                _, progress = geo.order_position(order, now, self.kitchen_prep(order['restaurant']))
                if progress >= 1.0:
                    self._advance_order(now)
                    changed = True
        late = [p for p in self.prebooks if p['status'] == 'scheduled' and now > p['when'] + safety.GRACE]
        if late:
            before = self.snapshot()
            for p in late:        # nobody was signed in to take the ride: free the seats, say so in Activity
                self._release_prebook(p)
                p['status'], p['reason'] = 'missed', 'The pickup time passed while this account was signed out or busy.'
            self.commit(before)
            changed = True
        return changed

    # ------------------------------------------------------------------ pre-booked rides (1.6.0)
    def _release_prebook(self, p: dict) -> None:
        if p['offer']:
            next(o for o in self.offers if o.id == p['offer']).release(p['party'])

    def my_prebooks(self, upcoming: bool = True) -> list[dict]:
        """The signed-in account's pre-booked rides: upcoming ones soonest first, or finished ones newest first."""
        mine = [p for p in self.prebooks if p['account'] == self.session and (p['status'] == 'scheduled') == upcoming]
        return sorted(mine, key=lambda p: p['when'], reverse=not upcoming)

    def prebook(self, pickup: int, destination: int, when: float, comfort: bool = False,
                offer_id: str | None = None, party: int = 1, pay_by_bank: bool = False,
                now: float | None = None) -> dict:
        """Reserve a ride for later. A solo ride is fixed at today's ordinary fare (no busy-time price);
        a shared ride holds its seats from now. The driver is chosen, and a bank payment authorised,
        when the ride is dispatched (dispatch_prebook), 10 minutes before the pickup time."""
        user = self.user
        if not user:
            raise ValueError('Create an account or sign in to pre-book a ride.')
        if user['role'] != 'passenger':
            raise ValueError('Sign in as a passenger to pre-book rides.')
        now = time.time() if now is None else now
        when = safety.check_when(when, now)
        distance(pickup, destination)
        if party not in (1, 2):
            raise ValueError('Choose one or two seats.')
        offer = next((o for o in self.offers if o.id == offer_id), None)
        if offer_id and (not offer or not offer.matches(pickup, destination, party)):
            raise ValueError('This shared ride does not match your route or seats.')
        if len(self.my_prebooks()) >= safety.MAX_PREBOOKS:
            raise ValueError('You can hold three pre-booked rides at a time. Cancel one first.')
        if any(abs(p['when'] - when) < 1800 for p in self.my_prebooks()):
            raise ValueError('You already have a ride pre-booked within 30 minutes of that time.')
        if pay_by_bank and 'bank' not in user:
            raise ValueError('Link a bank account in You > Bank & payments to pay by bank.')
        before = self.snapshot()
        if offer:
            offer.reserve(party)
        record = dict(id=f'B-{time_ns()}', account=user['id'], pickup=pickup, destination=destination,
                      comfort=bool(comfort) and not offer, offer=offer_id, party=party, when=when,
                      fare=offer.price * party if offer else fare(pickup, destination, comfort),
                      pay_by_bank=bool(pay_by_bank), status='scheduled', created=int(now))
        self.prebooks.append(record)
        self.commit(before)
        return record

    def _own_prebook(self, prebook_id: str) -> dict:
        p = next((p for p in self.prebooks if p['id'] == prebook_id and p['account'] == self.session
                  and self.session is not None), None)
        if not p or p['status'] != 'scheduled':
            raise ValueError('This pre-booked ride is no longer scheduled.')
        return p

    def cancel_prebook(self, prebook_id: str) -> None:
        self._own_prebook(prebook_id)
        before = self.snapshot()
        p = self._own_prebook(prebook_id)
        self._release_prebook(p)
        p['status'] = 'cancelled'
        self._trim_prebooks()
        self.commit(before)

    def _trim_prebooks(self) -> None:
        finished = [p for p in self.prebooks if p['status'] != 'scheduled']
        for p in sorted(finished, key=lambda p: p['when'])[:max(0, len(finished) - safety.KEEP_FINISHED)]:
            self.prebooks.remove(p)

    def due_prebook(self, now: float | None = None) -> dict | None:
        """The signed-in passenger's next pre-booked ride if it is time to send a driver, else None."""
        now = time.time() if now is None else now
        if self.ride or not self.user:
            return None
        due = [p for p in self.my_prebooks() if now >= p['when'] - safety.DISPATCH_LEAD]
        return due[0] if due else None

    def dispatch_prebook(self, prebook_id: str, now: float | None = None, **choice) -> bool:
        """Turn a pre-booked ride into the active ride through the ordinary book() path, at the fare
        fixed when it was pre-booked. choice carries the dispatch decision (driver, why, driver_id,
        start, twin, log). Returns False, and marks the pre-booking failed, if the ride cannot be
        booked (for example the bank declines): the held seats are released and nothing is charged."""
        now = time.time() if now is None else now
        self._own_prebook(prebook_id)
        if self.ride:
            raise ValueError('Finish or cancel your active ride first.')
        before = self.snapshot()
        p = self._own_prebook(prebook_id)
        self._release_prebook(p)                      # book() reserves the same seats again
        p['status'] = 'dispatched'
        try:
            self.book(p['pickup'], p['destination'], p['comfort'], offer_id=p['offer'], party=p['party'],
                      now=now, pay_by_bank=p['pay_by_bank'], **choice)
        except ValueError as error:
            self._restore(before)                     # exactly as it was before this attempt
            before = self.snapshot()
            p = self._own_prebook(prebook_id)
            self._release_prebook(p)
            p['status'], p['reason'] = 'failed', str(error)[:140]
            self.commit(before)
            return False
        self.ride['prebook'] = p['id']
        p['ride'] = self.ride['id']
        self._trim_prebooks()
        self.commit(before)
        return True

    # ------------------------------------------------------------------ SOS and trusted contact (1.6.0)
    def set_trusted(self, name: str, phone: str) -> dict | None:
        """Save (or, with both fields empty, remove) the person an SOS message is addressed to."""
        user = self.user
        if not user:
            raise ValueError('Create an account or sign in to save a trusted contact.')
        contact = None
        if (name or '').strip() or (phone or '').strip():
            contact = dict(name=acc.clean_name(name, 'Contact name'), phone=acc.clean_phone(phone))
            if not contact['phone']:
                raise ValueError('Enter the contact\'s mobile number.')
        before = self.snapshot()
        if contact:
            user['trusted'] = contact
        else:
            user.pop('trusted', None)
        self.commit(before)
        return contact

    def sos_ride(self) -> dict | None:
        """The active ride the current session is in, as passenger (or guest) or as its driver."""
        ride = self.ride
        if not ride:
            return None
        if ride.get('driver_id') is not None and ride['driver_id'] == self.session:
            return ride
        return ride if ride.get('passenger') == self.session and self.role == 'passenger' else None

    def active_sos(self) -> dict | None:
        return next((e for e in reversed(self.sos) if e['status'] == 'active' and e.get('account') == self.session), None)

    def raise_sos(self, now: float | None = None, point=None) -> dict:
        """Record an SOS for the ride in progress: who, which ride, when and where (the phone's own
        position when it has one, otherwise the car's position on the route). Raising it twice for
        one ride returns the same event. It alerts nobody by itself: the screen that follows offers
        112 and the trusted contact."""
        ride = self.sos_ride()
        if not ride:
            raise ValueError('SOS is available during a ride. In an emergency call 112.')
        now = time.time() if now is None else now
        existing = self.active_sos()
        if existing and existing['ride'] == ride['id']:
            return existing
        device = _is_point(list(point)) if point is not None else False
        where = point if device else geo.ride_position(ride, now)[0]
        before = self.snapshot()
        event = dict(id=f'S-{time_ns()}', account=self.session, ride=ride['id'],
                     role='driver' if ride.get('driver_id') == self.session and self.session else 'passenger',
                     at=int(now), point=[round(where[0], 5), round(where[1], 5)],
                     source='device' if device else 'route', status='active', shared=False)
        self.sos.append(event)
        self.sos = self.sos[-20:]
        self.commit(before)
        return event

    def _own_sos(self, sos_id: str) -> dict:
        event = next((e for e in self.sos if e['id'] == sos_id and e.get('account') == self.session), None)
        if not event:
            raise ValueError('SOS record not found.')
        return event

    def mark_sos_shared(self, sos_id: str) -> None:
        self._own_sos(sos_id)
        before = self.snapshot()
        self._own_sos(sos_id)['shared'] = True
        self.commit(before)

    def resolve_sos(self, sos_id: str, password: str = '', now: float | None = None) -> None:
        """End an SOS ("I am safe"). An account must give its password, so that someone else holding
        the unlocked phone cannot quietly switch it off."""
        event = self._own_sos(sos_id)
        if event['status'] != 'active':
            raise ValueError('This SOS has already ended.')
        if self.user and not acc.verify_password(password or '', self.user):
            raise ValueError('Password is not correct.')
        before = self.snapshot()
        event = self._own_sos(sos_id)
        event['status'], event['resolved'] = 'resolved', int(time.time() if now is None else now)
        self.commit(before)

    def my_sos(self) -> list[dict]:
        return [e for e in reversed(self.sos) if e.get('account') == self.session]

    # ------------------------------------------------------------------ bank payments (1.5.0)
    def payment(self, payment_id: str) -> dict | None:
        return next((p for p in self.payments if p['id'] == payment_id), None)

    def _step_up(self, password: str) -> dict:
        """Money settings need the password again, even inside a signed-in session."""
        user = self.user
        if not user:
            raise ValueError('Create an account or sign in to use bank payments.')
        if not acc.verify_password(password or '', user):
            raise ValueError('Password is not correct.')
        return user

    def _authorise(self, kind: str, ref: str, amount: int, details: dict, now: float) -> dict:
        user = self.user
        if not user or user['role'] != 'passenger' or 'bank' not in user:
            raise ValueError('Link a bank account in You > Bank & payments to pay by bank.')
        return pay.new_payment(f'P-{time_ns()}', kind, ref, user['id'], amount, user['bank'], now, details)

    def _open_payment(self, user: dict) -> bool:
        return any(p['status'] == 'authorised' and p['payer'] == user['id'] for p in self.payments)

    def link_bank(self, password: str, holder: str, iban: str, consent: bool = False,
                  now: float | None = None, mandate_id: str | None = None) -> dict:
        """Link (or replace) the signed-in account's bank account. Passengers sign a Direct Debit
        mandate and pay from it; drivers and sellers are paid out to it. The IBAN is checked and then
        dropped: only the holder, country and last four characters are saved."""
        user = self._step_up(password)
        if self._open_payment(user):
            raise ValueError('Finish or cancel the booking you are paying for first.')
        record = pay.bank_record(user['role'], holder, iban, consent, time.time() if now is None else now, mandate_id)
        before = self.snapshot()
        user['bank'] = record
        self.commit(before)
        return record

    def unlink_bank(self, password: str) -> None:
        user = self._step_up(password)
        if 'bank' not in user:
            raise ValueError('No bank account is linked.')
        if self._open_payment(user):
            raise ValueError('Finish or cancel the booking you are paying for first.')
        before = self.snapshot()
        del user['bank']
        self.commit(before)

    def wallet(self) -> dict:
        """Earned, paid out and available balance of the signed-in driver or seller, plus the amount
        of the trip or order in progress."""
        user = self.user
        if not user or user['role'] not in ('driver', 'seller'):
            raise ValueError('Only drivers and food sellers have a balance.')
        view = pay.wallet(user['id'], self.payments, self.payouts)
        job = self.driver_job() if user['role'] == 'driver' else self.seller_order()
        payment = self.payment(job['payment']) if job and job.get('payment') else None
        view['pending'] = payment['payee_net'] if payment and payment['status'] == 'authorised' else 0
        return view

    def request_payout(self, password: str, now: float | None = None, payout_id: str | None = None) -> dict:
        """Pay the whole available balance to the linked bank account. A failed payout (closed
        account) is recorded and leaves the balance untouched."""
        user = self._step_up(password)
        if user['role'] not in ('driver', 'seller'):
            raise ValueError('Only drivers and food sellers can be paid out.')
        if 'bank' not in user:
            raise ValueError('Link the bank account you want to be paid to first.')
        amount = pay.wallet(user['id'], self.payments, self.payouts)['balance']
        if amount < pay.MIN_PAYOUT:
            raise ValueError('You need at least €1.00 to pay out.')
        closed = pay.sandbox_outcome(user['bank']['last4'], 0) == 'account_closed'
        before = self.snapshot()
        payout = dict(id=payout_id or f'O-{time_ns()}', account=user['id'], amount=amount, last4=user['bank']['last4'],
                      status='failed' if closed else 'paid', created=int(time.time() if now is None else now),
                      synced=False)
        self.payouts.append(payout)
        self.commit(before)
        return payout

    def my_payments(self) -> list[dict]:
        """Payments the signed-in account made or received, newest first."""
        me = self.session
        return [p for p in reversed(self.payments) if me and me in (p['payer'], p['payee'])]

    def my_payouts(self) -> list[dict]:
        return [o for o in reversed(self.payouts) if o['account'] == self.session]

    # ------------------------------------------------------------------ ATLAS server link (1.5.0)
    def set_server(self, url: str) -> None:
        from .backend import clean_url
        before = self.snapshot()
        self.server_url = clean_url(url)
        self.commit(before)

    def connect(self, server_id: str, token: str) -> None:
        """Remember the signed-in account's server identity and session token."""
        user = self.user
        if not user or not isinstance(server_id, str) or not isinstance(token, str) or not server_id or not token:
            raise ValueError('The server did not return an account.')
        before = self.snapshot()
        user['server'] = dict(id=server_id, token=token)
        self.commit(before)

    def disconnect(self) -> None:
        before = self.snapshot()
        if self.user:
            self.user.pop('server', None)
        self.commit(before)

    def server_payee(self, payment: dict) -> tuple[bool, str | None]:
        """(ready, server account id): house payees need no account; a registered payee must be connected."""
        if payment['payee'] in pay.HOUSE_PAYEES:
            return True, None
        link = (self.account(payment['payee']) or {}).get('server')
        return bool(link), link['id'] if link else None

    def unsynced(self) -> list[dict]:
        """Captured payments not yet on the server whose payer (and payee, if registered) is connected."""
        ready = []
        for p in self.payments:
            payer = self.account(p['payer'])
            if p['status'] == 'captured' and not p['synced'] and payer and payer.get('server') and \
                    self.server_payee(p)[0]:
                ready.append(p)
        return ready

    def mark_synced(self, record_id: str, server_id: str | None = None, error: str | None = None) -> None:
        record = self.payment(record_id) or next((o for o in self.payouts if o['id'] == record_id), None)
        if record is None:
            return
        before = self.snapshot()
        if error:
            record['error'] = str(error)[:160]
        else:
            record['synced'] = True
            record.pop('error', None)
            if server_id:
                record['server'] = str(server_id)
        self.commit(before)

    # ------------------------------------------------------------------ views
    def my_history(self) -> list[dict]:
        user = self.user
        if user and user['role'] == 'driver':
            return [r for r in self.history if r.get('driver_id') == user['id']]
        if user and user['role'] == 'seller':
            kitchen = self.kitchen_of(user)
            return [r for r in self.history if kitchen and r.get('restaurant') == kitchen['id']]
        me = self.session
        return [r for r in self.history if r.get('passenger') == me]

