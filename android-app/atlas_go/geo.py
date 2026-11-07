"""Cork geography, Web-Mercator tile maths and live-journey positions. Pure Python, no I/O.

Coordinates are approximate public landmarks used for illustration. Movement between
points is a straight line at a constant speed shown in time-lapse; there is no routing
engine, traffic model or turn-by-turn navigation.
"""
from __future__ import annotations

import math

# (lat, lon) for domain.PLACES, in the same order
PLACE_COORDS = (
    (51.8935, -8.4921),   # UCC Campus
    (51.8985, -8.4716),   # Cork City Centre (St Patrick's Street)
    (51.9017, -8.4582),   # Kent Station
    (51.8466, -8.4917),   # Cork Airport
)
CORK = (51.8960, -8.4700)

# Approximate centres of the neighbourhoods named by the simulated driver pools
ZONE_COORDS = {
    'Mardyke': (51.8978, -8.4880), 'Western Road': (51.8946, -8.4895), 'City Centre': (51.8986, -8.4730),
    'Douglas': (51.8770, -8.4360), 'Oliver Plunkett St': (51.8976, -8.4702), 'Grand Parade': (51.8970, -8.4760),
    'MacCurtain St': (51.9020, -8.4700), 'South Mall': (51.8968, -8.4690), 'Kent Station': (51.9017, -8.4582),
    'Lower Glanmire Rd': (51.9030, -8.4520), 'Montenotte': (51.9065, -8.4520), 'Blackpool': (51.9150, -8.4730),
    'Airport rank': (51.8470, -8.4910), 'Ballygarvan': (51.8300, -8.4630), 'Frankfield': (51.8640, -8.4560),
}

# Built-in kitchens (domain.RESTAURANTS order)
KITCHEN_COORDS = ((51.8990, -8.4760), (51.8985, -8.4420), (51.8962, -8.4850))

TIME_LAPSE = 10          # live journeys run ten times faster than real time
SPEED_KMH = 25.0         # average urban speed used for straight-line legs
BOARD_SECONDS = 8        # time-lapse seconds the driver waits at pickup
ARRIVE_SECONDS = 6       # time-lapse seconds for the courier's last stage
MIN_LEG_SECONDS = 6


def haversine_km(a, b) -> float:
    lat1, lon1, lat2, lon2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371.0088 * math.asin(min(1.0, math.sqrt(h)))


def eta_minutes(a, b) -> int:
    """Whole minutes to drive a straight line at SPEED_KMH (real time, not time-lapse); at least 1."""
    return max(1, round(haversine_km(a, b) / SPEED_KMH * 60))


def leg_seconds(a, b) -> float:
    """Time-lapse seconds the live map takes to animate one leg."""
    return max(MIN_LEG_SECONDS, haversine_km(a, b) / SPEED_KMH * 3600 / TIME_LAPSE)


def lerp(a, b, f: float):
    f = max(0.0, min(1.0, f))
    return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)


def nearest_place(point) -> tuple[int, float]:
    """Index of the closest saved place and the distance to it in km."""
    best = min(range(len(PLACE_COORDS)), key=lambda i: haversine_km(point, PLACE_COORDS[i]))
    return best, haversine_km(point, PLACE_COORDS[best])


def valid_point(point) -> bool:
    try:
        lat, lon = float(point[0]), float(point[1])
    except (TypeError, ValueError, IndexError):
        return False
    return len(point) == 2 and -85.0 <= lat <= 85.0 and -180.0 <= lon <= 180.0


def zone_drift(zone: str, now: float, phase: float = 0.0):
    """Idle driver wandering a few hundred metres around a zone centre (deterministic in time)."""
    lat, lon = ZONE_COORDS.get(zone, CORK)
    angle = now / 40.0 + phase
    return (lat + 0.0018 * math.sin(angle), lon + 0.0029 * math.cos(angle * 0.8))


# --------------------------------------------------------------------------- Web Mercator

TILE_PX = 256
MIN_ZOOM, MAX_ZOOM = 3, 18


def world_px(lat: float, lon: float, zoom: float) -> tuple[float, float]:
    """Global pixel coordinates (origin top-left) at a zoom level, 256-pixel tiles."""
    lat = max(-85.05112878, min(85.05112878, lat))
    scale = TILE_PX * 2 ** zoom
    x = (lon + 180.0) / 360.0 * scale
    s = math.sin(math.radians(lat))
    y = (0.5 - math.log((1 + s) / (1 - s)) / (4 * math.pi)) * scale
    return x, y


def from_world_px(x: float, y: float, zoom: float) -> tuple[float, float]:
    scale = TILE_PX * 2 ** zoom
    lon = x / scale * 360.0 - 180.0
    n = math.pi - 2 * math.pi * y / scale
    lat = math.degrees(math.atan(math.sinh(n)))
    return lat, lon


def tile_range(center, zoom: int, width_px: float, height_px: float):
    """Tiles (x, y) covering a viewport of the given size in 256-pixel units, centred on center."""
    cx, cy = world_px(center[0], center[1], zoom)
    n = 2 ** zoom
    x0, x1 = int(math.floor((cx - width_px / 2) / TILE_PX)), int(math.floor((cx + width_px / 2) / TILE_PX))
    y0, y1 = int(math.floor((cy - height_px / 2) / TILE_PX)), int(math.floor((cy + height_px / 2) / TILE_PX))
    return [(x % n, y) for y in range(max(0, y0), min(n - 1, y1) + 1) for x in range(x0, x1 + 1)]


def fit_zoom(points, width_px: float, height_px: float, padding: float = 0.2) -> tuple[tuple[float, float], int]:
    """Centre and largest whole zoom that shows every point inside the viewport."""
    pts = [p for p in points if valid_point(p)] or [CORK]
    lat_c = (max(p[0] for p in pts) + min(p[0] for p in pts)) / 2
    lon_c = (max(p[1] for p in pts) + min(p[1] for p in pts)) / 2
    for zoom in range(16, MIN_ZOOM - 1, -1):
        xs, ys = zip(*(world_px(p[0], p[1], zoom) for p in pts))
        if (max(xs) - min(xs)) <= width_px * (1 - padding) and (max(ys) - min(ys)) <= height_px * (1 - padding):
            return (lat_c, lon_c), zoom
    return (lat_c, lon_c), MIN_ZOOM


# --------------------------------------------------------------------------- live journeys

def ride_legs(ride: dict):
    live = ride['live']
    pickup, dest = PLACE_COORDS[ride['pickup']], PLACE_COORDS[ride['destination']]
    return tuple(live['start']), pickup, dest


def ride_position(ride: dict, now: float):
    """Where the ride's car is now, and how far through the current stage it is (0-1)."""
    start, pickup, dest = ride_legs(ride)
    t = max(0.0, now - ride['live']['t'])
    if ride.get('pending'):
        return start, 0.0
    if ride['stage'] == 0:
        f = t / leg_seconds(start, pickup)
        return lerp(start, pickup, f), min(1.0, f)
    if ride['stage'] == 1:
        return pickup, min(1.0, t / BOARD_SECONDS)
    f = t / leg_seconds(pickup, dest)
    return lerp(pickup, dest, f), min(1.0, f)


def ride_eta_text(ride: dict, now: float) -> str:
    start, pickup, dest = ride_legs(ride)
    t = max(0.0, now - ride['live']['t'])
    if ride.get('pending'):
        return 'Waiting for the driver to accept'
    if ride['stage'] == 0:
        left = max(0.0, leg_seconds(start, pickup) - t) * TIME_LAPSE / 60
        return f'Driver arrives in about {max(1, math.ceil(left))} min'
    if ride['stage'] == 1:
        return 'Driver is at the pickup point'
    left = max(0.0, leg_seconds(pickup, dest) - t) * TIME_LAPSE / 60
    return f'About {max(1, math.ceil(left))} min to your destination'


def order_position(order: dict, now: float, prep_minutes: int):
    """Courier position for an order (None while the kitchen is still preparing) and stage progress."""
    live = order['live']
    kitchen, home = tuple(live['kitchen']), PLACE_COORDS[order['address']]
    t = max(0.0, now - live['t'])
    if order['stage'] == 0:
        return None, min(1.0, t / max(MIN_LEG_SECONDS, prep_minutes * 60 / TIME_LAPSE))
    if order['stage'] == 1:
        f = t / leg_seconds(kitchen, home)
        return lerp(kitchen, home, f), min(1.0, f)
    return home, min(1.0, t / ARRIVE_SECONDS)
