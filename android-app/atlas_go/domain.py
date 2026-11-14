"""Pure Python domain rules; integer euro cents, illustrative saved routes."""
from dataclasses import dataclass

PLACES = ('UCC Campus', 'Cork City Centre', 'Kent Station', 'Cork Airport')
DISTANCES = ((0, 3, 5, 8), (3, 0, 2, 9), (5, 2, 0, 10), (8, 9, 10, 0))
RESTAURANTS = ('Green Bowl Kitchen', 'Marina Pizza', 'Spice Route')


def distance(pickup: int, destination: int) -> int:
    if not (0 <= pickup < len(PLACES) and 0 <= destination < len(PLACES)) or pickup == destination:
        raise ValueError('Choose different pickup and destination places.')
    return DISTANCES[pickup][destination]


def fare(pickup: int, destination: int, comfort: bool = False) -> int:
    return (350 + distance(pickup, destination) * 170) * (130 if comfort else 100) // 100


def money(cents: int) -> str:
    return f'€{cents // 100}.{cents % 100:02d}'


@dataclass(frozen=True)
class Dish:
    id: str
    name: str
    detail: str
    restaurant: int
    price: int


MENU = (
    Dish('bowl', 'Harvest bowl', 'Roasted veg · quinoa · tahini', 0, 1090),
    Dish('wrap', 'Falafel wrap', 'Chickpeas · salad · lemon', 0, 850),
    Dish('juice', 'Fresh orange juice', '250 ml · freshly squeezed', 0, 390),
    Dish('pizza', 'Margherita pizza', 'Tomato · mozzarella · basil', 1, 1290),
    Dish('garlic', 'Garlic flatbread', 'Herbs · garlic butter', 1, 490),
    Dish('water', 'Still water', '500 ml bottle', 1, 200),
    Dish('curry', 'Vegetable curry', 'Seasonal vegetables · rice', 2, 1190),
    Dish('dosa', 'Masala dosa', 'Potato filling · chutney', 2, 990),
    Dish('lassi', 'Mango lassi', 'Yoghurt · mango · 250 ml', 2, 450),
)
DISHES = {dish.id: dish for dish in MENU}


@dataclass
class Offer:
    """A carpool already on the road. One rider (co_rider) is in the car before you join:
    the driver picks you up next, drops co_rider at co_drop first, then drops you."""
    id: str
    driver: str
    pickup: int
    destination: int
    capacity: int
    price: int
    seats: int
    co_rider: str = ''      # rider already in the vehicle ('' for a carpool with nobody on board)
    co_from: str = ''       # zone where the driver picked that rider up (geo.ZONE_COORDS)
    co_drop: str = ''       # zone on your route where that rider gets out, before you

    def matches(self, pickup: int, destination: int, party: int) -> bool:
        return self.pickup == pickup and self.destination == destination and 1 <= party <= self.seats

    def reserve(self, party: int) -> None:
        if not 1 <= party <= self.seats:
            raise ValueError('Not enough shared seats available.')
        self.seats -= party

    def release(self, party: int) -> None:
        self.seats = min(self.capacity, self.seats + party)


@dataclass(frozen=True)
class Kitchen:
    id: int
    name: str
    cuisine: str
    place: int
    prep: int                 # kitchen's own preparation estimate, minutes
    owner: str | None = None  # seller account id; None for the built-in demo kitchens
    open: bool = True


BUILT_IN_KITCHENS = (
    Kitchen(0, RESTAURANTS[0], 'Fresh bowls & wraps', 1, 12),
    Kitchen(1, RESTAURANTS[1], 'Stone-baked pizza', 1, 15),
    Kitchen(2, RESTAURANTS[2], 'Indian comfort food', 0, 18),
)


class Catalog:
    """Built-in kitchens plus kitchens registered by food sellers on this device."""

    def __init__(self, kitchens: list | None = None):
        self.kitchens = {k.id: k for k in BUILT_IN_KITCHENS}
        self.dishes = dict(DISHES)
        self.archived = set()
        for data in kitchens or []:
            kitchen = Kitchen(int(data['id']), data['name'], data['cuisine'], int(data['place']),
                              int(data['prep']), data['owner'], bool(data.get('open', True)))
            self.kitchens[kitchen.id] = kitchen
            for dish in data.get('dishes', []):
                self.dishes[dish['id']] = Dish(dish['id'], dish['name'], dish['detail'], kitchen.id, int(dish['price']))
                if dish.get('archived'):
                    self.archived.add(dish['id'])

    def name(self, kitchen: int) -> str:
        return self.kitchens[kitchen].name if kitchen in self.kitchens else 'Closed kitchen'

    def menu(self, kitchen: int) -> list:
        return [d for d in self.dishes.values() if d.restaurant == kitchen and d.id not in self.archived]

    def listed(self) -> list:
        """Kitchens a passenger can order from: open and with at least one dish."""
        return [k for k in self.kitchens.values() if k.open and self.menu(k.id)]


DEFAULT_CATALOG = Catalog()


class Cart:
    def __init__(self, items: dict | None = None, catalog: Catalog | None = None):
        self.catalog = catalog or DEFAULT_CATALOG
        self.items = {}
        for item, quantity in (items or {}).items():
            if not isinstance(quantity, int) or not 1 <= quantity <= 10:
                raise ValueError('Invalid saved basket quantity.')
            for _ in range(quantity):
                self.add(item)

    @property
    def restaurant(self) -> int | None:
        return self.catalog.dishes[next(iter(self.items))].restaurant if self.items else None

    def add(self, item: str) -> None:
        if item not in self.catalog.dishes:
            raise ValueError('Unknown menu item.')
        if self.restaurant is not None and self.catalog.dishes[item].restaurant != self.restaurant:
            raise ValueError('Clear the basket before choosing a different restaurant.')
        quantity = self.items.get(item, 0)
        if quantity >= 10:
            raise ValueError('Maximum ten of each item.')
        self.items[item] = quantity + 1

    def remove(self, item: str) -> None:
        if item in self.items:
            self.items[item] -= 1
            if not self.items[item]:
                del self.items[item]

    def count(self) -> int:
        return sum(self.items.values())

    def subtotal(self) -> int:
        return sum(self.catalog.dishes[item].price * qty for item, qty in self.items.items())

    def total(self) -> int:
        return self.subtotal() + (250 if self.items else 0)

    def clear(self) -> None:
        self.items.clear()
