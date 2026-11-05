"""Local JSON persistence; no live services, payments or model inference."""
import json
import os
from pathlib import Path
from time import time_ns
from .domain import Cart, Offer, distance, fare, PLACES


class LocalStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.reset(save=False)
        if self.path.exists():
            self.load()

    def reset(self, save: bool = True) -> None:
        self.cart = Cart()
        self.history = []
        self.ride = None
        self.order = None
        self.ui = {}
        self.offers = [
            Offer('pool-1', 'Alex · Electric hatchback', 0, 1, 3, 490, 3),
            Offer('pool-2', 'Sam · Hybrid sedan', 0, 1, 2, 590, 2),
            Offer('pool-3', 'Jordan · Electric sedan', 1, 3, 3, 990, 3),
            Offer('pool-4', 'Taylor · Hybrid hatchback', 2, 0, 2, 690, 2),
        ]
        if save:
            self.save()

    def load(self) -> None:
        try:
            data = json.loads(self.path.read_text(encoding='utf-8'))
            self.validate(data)
            self.cart = Cart(data.get('cart', {}))
            self.history = data.get('history', [])
            self.ride, self.order = data.get('ride'), data.get('order')
            self.ui = data.get('ui', {})
            for offer in self.offers:
                seats = data.get('seats', {}).get(offer.id, offer.capacity)
                offer.seats = max(0, min(offer.capacity, int(seats)))
            if not isinstance(self.history, list) or not isinstance(self.ui, dict):
                raise ValueError('Invalid local state.')
        except (ValueError, TypeError, KeyError, AttributeError):
            # Preserve unreadable data for diagnostics; start a clean local demo.
            self.path.replace(self.path.with_suffix('.invalid.json'))
            self.reset()

    @staticmethod
    def validate(data: dict) -> None:
        """Reject structurally damaged state before screens read its fields."""
        if not isinstance(data, dict):
            raise ValueError('State must be an object.')
        if not isinstance(data.get('history', []), list) or not isinstance(data.get('ui', {}), dict):
            raise ValueError('Invalid history or screen state.')
        if not isinstance(data.get('seats', {}), dict):
            raise ValueError('Invalid seat state.')
        records = list(data.get('history', []))
        records += [data[k] for k in ('ride','order') if data.get(k) is not None]
        for record in records:
            if not isinstance(record, dict):
                raise ValueError('Invalid booking record.')
            if not isinstance(record.get('id'), str) or type(record.get('fare')) is not int or record['fare'] < 0:
                raise ValueError('Invalid booking identity or total.')
            if type(record.get('stage')) is not int or record['stage'] not in range(3):
                raise ValueError('Invalid booking stage.')
            if 'restaurant' in record:
                if record['restaurant'] not in range(3) or record.get('address') not in range(len(PLACES)):
                    raise ValueError('Invalid food route.')
                if not isinstance(record.get('items'), dict) or not record['items']:
                    raise ValueError('Invalid food items.')
                Cart(record['items'])
            else:
                distance(record.get('pickup', -1), record.get('destination', -1))
                if record.get('party') not in (1, 2) or not isinstance(record.get('driver'), str):
                    raise ValueError('Invalid rider or driver.')
                if type(record.get('shared')) is not bool:
                    raise ValueError('Invalid ride kind.')
                if record['shared'] and record.get('offer') not in ('pool-1','pool-2','pool-3','pool-4'):
                    raise ValueError('Invalid shared offer.')
        ui = data.get('ui', {})
        for key, bound in {'pickup':4, 'destination':4, 'restaurant':3, 'address':4}.items():
            if key in ui and (type(ui[key]) is not int or ui[key] not in range(bound)):
                ui.pop(key)
        if ui.get('party', 1) not in (1,2):
            ui.pop('party')
        if 'comfort' in ui and type(ui['comfort']) is not bool:
            ui.pop('comfort')
        if ui.get('screen', 'home') not in ('home','ride','share','food','menu','cart','active_ride','active_order','activity','profile','privacy'):
            ui.pop('screen')

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = dict(cart=self.cart.items, history=self.history, ride=self.ride,
                       order=self.order, seats={o.id: o.seats for o in self.offers}, ui=self.ui)
        temporary = self.path.with_suffix('.tmp')
        with temporary.open('w', encoding='utf-8') as stream:
            json.dump(payload, stream, ensure_ascii=False)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(self.path)

    def book(self, pickup: int, destination: int, comfort: bool = False,
             offer_id: str | None = None, party: int = 1) -> None:
        if self.ride:
            raise ValueError('Finish or cancel your active ride first.')
        distance(pickup, destination)
        if party not in (1, 2):
            raise ValueError('Choose one or two seats.')
        offer = next((o for o in self.offers if o.id == offer_id), None)
        if offer_id and (not offer or not offer.matches(pickup, destination, party)):
            raise ValueError('This shared ride does not match your route or seats.')
        if offer:
            offer.reserve(party)
        self.ride = dict(id=f'R-{time_ns()}', pickup=pickup, destination=destination,
                         shared=bool(offer), party=party, offer=offer_id,
                         driver=offer.driver if offer else 'Morgan · ATLAS demo driver',
                         fare=offer.price * party if offer else fare(pickup, destination, comfort), stage=0)
        self.save()

    def advance_ride(self, cancel: bool = False) -> None:
        if not self.ride:
            return
        if cancel or self.ride['stage'] == 2:
            if cancel and self.ride['shared']:
                next(o for o in self.offers if o.id == self.ride['offer']).release(self.ride['party'])
            self.ride['status'] = 'Cancelled' if cancel else 'Completed'
            self.history.append(self.ride)
            self.ride = None
        else:
            self.ride['stage'] += 1
        self.save()

    def checkout(self, address: int) -> None:
        if self.order:
            raise ValueError('Complete the active food order first.')
        if address not in range(len(PLACES)):
            raise ValueError('Choose a delivery place.')
        if not self.cart.items:
            raise ValueError('Add food to your basket first.')
        self.order = dict(id=f'F-{time_ns()}', restaurant=self.cart.restaurant,
                          address=address, fare=self.cart.total(), items=self.cart.items.copy(), stage=0)
        self.cart.clear()
        self.save()

    def advance_order(self) -> None:
        if not self.order:
            return
        if self.order['stage'] == 2:
            self.order['status'] = 'Delivered'
            self.history.append(self.order)
            self.order = None
        else:
            self.order['stage'] += 1
        self.save()
