"""LiveMap: a slippy map for Kivy with OpenStreetMap tiles, an offline fallback and live markers.

Tiles are fetched in background threads, cached on the device and drawn as textures. When the
network or tile server is unavailable the map draws a schematic Cork layer so markers, routes
and live positions keep working offline. Map data © OpenStreetMap contributors (ODbL); the
attribution is always drawn on the map as the tile licence requires.
"""
from __future__ import annotations

import math
import os
import queue
import threading
import time
from collections import OrderedDict
from io import BytesIO
from pathlib import Path

from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.core.text import Label as CoreLabel
from kivy.graphics import Color, Ellipse, Line, Rectangle, RoundedRectangle
from kivy.logger import Logger
from kivy.metrics import dp, sp
from kivy.uix.stencilview import StencilView
from kivy.utils import get_color_from_hex as color

from . import geo
from . import __version__

TILE_URL = os.environ.get('ATLAS_TILE_URL', 'https://tile.openstreetmap.org/{z}/{x}/{y}.png')
USER_AGENT = f'ATLASGo/{__version__} (+https://github.com/FUllSCIPTS/ATLAS)'
ATTRIBUTION = '© OpenStreetMap contributors'

KIND_COLORS = {
    'place': '#075E4A', 'driver': '#5B6D64', 'registered': '#6E56CF', 'ride': '#075E4A',
    'me': '#1A73E8', 'kitchen': '#D9822B', 'courier': '#D9822B', 'home': '#075E4A', 'rider': '#6E56CF',
}


class TileLoader:
    """Background tile fetcher with a disk cache and a small in-memory texture cache."""

    def __init__(self, cache_dir: Path, workers: int = 2, memory: int = 160):
        self.cache_dir = Path(cache_dir)
        self.requests = queue.LifoQueue()
        self.pending = set()
        self.failed = {}
        self.textures = OrderedDict()
        self.memory = memory
        self.listeners = []
        self.fail_streak = 0
        self.offline_until = 0.0
        self.loaded = 0
        self.lock = threading.Lock()
        self.session = None
        for _ in range(workers):
            threading.Thread(target=self._work, daemon=True).start()

    @property
    def offline(self) -> bool:
        return time.monotonic() < self.offline_until

    def texture(self, key):
        tex = self.textures.get(key)
        if tex is not None:
            self.textures.move_to_end(key)
            return tex
        with self.lock:
            if key in self.pending or self.failed.get(key, 0) > time.monotonic():
                return None
            self.pending.add(key)
        self.requests.put(key)
        return None

    def _path(self, key) -> Path:
        z, x, y = key
        return self.cache_dir / str(z) / str(x) / f'{y}.png'

    def _fetch(self, key) -> bytes | None:
        path = self._path(key)
        if path.exists() and path.stat().st_size > 0:
            return path.read_bytes()
        if self.offline:
            return None
        try:
            import requests
            if self.session is None:
                self.session = requests.Session()
                self.session.headers['User-Agent'] = USER_AGENT
            z, x, y = key
            reply = self.session.get(TILE_URL.format(z=z, x=x, y=y), timeout=8)
            if reply.status_code != 200 or not reply.content.startswith(b'\x89PNG'):
                raise OSError(f'tile HTTP {reply.status_code}')
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix('.tmp')
            tmp.write_bytes(reply.content)
            tmp.replace(path)
            self.fail_streak = 0
            return reply.content
        except Exception as error:  # network down, DNS, TLS, HTTP errors
            self.fail_streak += 1
            if self.fail_streak >= 3:
                self.offline_until = time.monotonic() + 45
            Logger.debug(f'ATLAS map: tile {key} unavailable ({error})')
            return None

    def _work(self):
        while True:
            key = self.requests.get()
            data = self._fetch(key)
            Clock.schedule_once(lambda _dt, key=key, data=data: self._deliver(key, data), 0)

    def _deliver(self, key, data):
        with self.lock:
            self.pending.discard(key)
        if data is None:
            self.failed[key] = time.monotonic() + (20 if not self.offline else 45)
            return
        try:
            tex = CoreImage(BytesIO(data), ext='png').texture
        except Exception:
            self.failed[key] = time.monotonic() + 300
            return
        self.textures[key] = tex
        self.loaded += 1
        while len(self.textures) > self.memory:
            self.textures.popitem(last=False)
        for listener in list(self.listeners):
            listener()


_LOADER = None


def loader(cache_dir: Path | None = None) -> TileLoader:
    global _LOADER
    if _LOADER is None:
        _LOADER = TileLoader(cache_dir or Path.home() / '.atlas-go' / 'tiles')
    return _LOADER


_LABELS = {}


def text_texture(text, size=10, shade='#182D26', bold=False):
    key = (text, size, shade, bold)
    if key not in _LABELS:
        label = CoreLabel(text=text, font_size=sp(size), color=color(shade), bold=bold)
        label.refresh()
        _LABELS[key] = label.texture
        if len(_LABELS) > 300:
            _LABELS.pop(next(iter(_LABELS)))
    return _LABELS[key]


class LiveMap(StencilView):
    """Pan with a finger (when interactive), zoom with the +/- controls or a double tap."""

    def __init__(self, center=geo.CORK, zoom=13, interactive=True, tile_loader=None, **kwargs):
        super().__init__(**kwargs)
        self.center_point = tuple(center)
        self.zoom = int(zoom)
        self.interactive = interactive
        self.tiles = tile_loader or loader()
        self.markers = []
        self.routes = []
        self.accuracy = None
        self.follow = None
        self.tile_dp = dp(200)
        self._drag = None
        self.tiles.listeners.append(self._schedule)
        self._redraw_event = None
        self.bind(pos=self._schedule, size=self._schedule)

    # ------------------------------------------------------------------ public API
    def set_view(self, center=None, zoom=None):
        if center is not None and geo.valid_point(center):
            self.center_point = (float(center[0]), float(center[1]))
        if zoom is not None:
            self.zoom = max(geo.MIN_ZOOM, min(geo.MAX_ZOOM, int(zoom)))
        self._schedule()

    def zoom_by(self, step: int):
        self.set_view(zoom=self.zoom + step)

    def fit(self, points, padding=0.3):
        if not self.width or not self.height:
            Clock.schedule_once(lambda _dt: self.fit(points, padding), 0)
            return
        scale = 256 / self.tile_dp
        center, zoom = geo.fit_zoom(points, self.width * scale, self.height * scale, padding)
        self.set_view(center, min(zoom, 16))

    def set_layers(self, markers=(), routes=(), accuracy=None):
        """markers: dicts(kind, point, label=''); routes: (points, hex colour, dashed)."""
        self.markers, self.routes, self.accuracy = list(markers), list(routes), accuracy
        self._schedule()

    def detach(self):
        if self._schedule in self.tiles.listeners:
            self.tiles.listeners.remove(self._schedule)

    # ------------------------------------------------------------------ projection
    def _scale(self):
        return self.tile_dp / geo.TILE_PX

    def to_screen(self, point):
        s = self._scale()
        cx, cy = geo.world_px(self.center_point[0], self.center_point[1], self.zoom)
        px, py = geo.world_px(point[0], point[1], self.zoom)
        return self.center_x + (px - cx) * s, self.center_y - (py - cy) * s

    def to_point(self, x, y):
        s = self._scale()
        cx, cy = geo.world_px(self.center_point[0], self.center_point[1], self.zoom)
        return geo.from_world_px(cx + (x - self.center_x) / s, cy - (y - self.center_y) / s, self.zoom)

    # ------------------------------------------------------------------ touch
    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        if super().on_touch_down(touch):
            return True
        if not self.interactive:
            return False
        if touch.is_double_tap:
            self.set_view(self.to_point(*touch.pos), self.zoom + 1)
            return True
        touch.grab(self)
        self._drag = touch.pos
        self.follow = None
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is not self:
            return super().on_touch_move(touch)
        s = self._scale()
        cx, cy = geo.world_px(self.center_point[0], self.center_point[1], self.zoom)
        dx, dy = touch.pos[0] - self._drag[0], touch.pos[1] - self._drag[1]
        self._drag = touch.pos
        self.center_point = geo.from_world_px(cx - dx / s, cy + dy / s, self.zoom)
        self._schedule()
        return True

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            self._drag = None
            return True
        return super().on_touch_up(touch)

    # ------------------------------------------------------------------ drawing
    def _schedule(self, *_):
        if self._redraw_event is None:
            self._redraw_event = Clock.schedule_once(self.draw, 0)

    def visible_tiles(self):
        scale = 256 / self.tile_dp
        return geo.tile_range(self.center_point, self.zoom, self.width * scale + 2, self.height * scale + 2)

    def draw(self, *_):
        self._redraw_event = None
        if self.width < 10 or self.height < 10:
            return
        self.canvas.clear()
        s = self._scale()
        size = geo.TILE_PX * s
        cx, cy = geo.world_px(self.center_point[0], self.center_point[1], self.zoom)
        shown = 0
        with self.canvas:
            Color(*color('#E7EEDC'))
            Rectangle(pos=self.pos, size=self.size)
            for x, y in self.visible_tiles():
                tex = self.tiles.texture((self.zoom, x, y))
                n = 2 ** self.zoom
                wx = x * geo.TILE_PX
                # keep wrapped tiles next to the view centre
                while wx - cx > n * geo.TILE_PX / 2:
                    wx -= n * geo.TILE_PX
                while cx - wx > n * geo.TILE_PX / 2:
                    wx += n * geo.TILE_PX
                sx = self.center_x + (wx - cx) * s
                sy = self.center_y - (y * geo.TILE_PX - cy) * s - size
                if tex is not None:
                    Color(1, 1, 1, 1)
                    Rectangle(texture=tex, pos=(sx, sy), size=(size, size))
                    shown += 1
            if not shown:
                self._schematic()
            for points, shade, dashed in self.routes:
                self._route(points, shade, dashed)
            if self.accuracy and self.accuracy[0] is not None:
                point, metres = self.accuracy
                mx, my = self.to_screen(point)
                metres_per_px = 156543.03392 * math.cos(math.radians(point[0])) / 2 ** self.zoom
                r = max(dp(8), metres / metres_per_px * s)
                Color(0.10, 0.45, 0.91, 0.15)
                Ellipse(pos=(mx - r, my - r), size=(2 * r, 2 * r))
            for marker in self.markers:
                self._marker(marker)
            tex = text_texture(ATTRIBUTION, 9, '#182D26')
            Color(1, 1, 1, .85)
            Rectangle(pos=(self.right - tex.size[0] - dp(8), self.y), size=(tex.size[0] + dp(8), tex.size[1] + dp(2)))
            Color(1, 1, 1, 1)
            Rectangle(texture=tex, pos=(self.right - tex.size[0] - dp(4), self.y + dp(1)), size=tex.size)
            if not shown:
                note = text_texture('Offline map · tiles load when online', 10, '#5B6D64', True)
                Color(1, 1, 1, .9)
                RoundedRectangle(pos=(self.x + dp(8), self.top - note.size[1] - dp(12)),
                                 size=(note.size[0] + dp(12), note.size[1] + dp(6)), radius=[dp(6)])
                Color(1, 1, 1, 1)
                Rectangle(texture=note, pos=(self.x + dp(14), self.top - note.size[1] - dp(9)), size=note.size)
        self.tiles_shown = shown

    def _schematic(self):
        """Offline layer: a 1 km grid, the River Lee's channels (approximate) and the saved places."""
        Color(*color('#D6E2C7'))
        lat0, lon0 = self.to_point(self.x, self.y)
        lat1, lon1 = self.to_point(self.right, self.top)
        step_lat, step_lon = 0.009, 0.0145
        lat = math.floor(lat0 / step_lat) * step_lat
        while lat <= lat1:
            y = self.to_screen((lat, lon0))[1]
            Line(points=[self.x, y, self.right, y], width=dp(.7))
            lat += step_lat
        lon = math.floor(lon0 / step_lon) * step_lon
        while lon <= lon1:
            x = self.to_screen((lat0, lon))[0]
            Line(points=[x, self.y, x, self.top], width=dp(.7))
            lon += step_lon
        Color(*color('#A9D0C6'))
        for channel in (((51.8960, -8.5050), (51.8968, -8.4890), (51.8995, -8.4760), (51.9003, -8.4690),
                         (51.8990, -8.4600), (51.9010, -8.4450), (51.9000, -8.4200), (51.8960, -8.3900)),
                        ((51.8968, -8.4890), (51.8955, -8.4790), (51.8963, -8.4690), (51.8990, -8.4600))):
            pts = []
            for p in channel:
                pts += self.to_screen(p)
            Line(points=pts, width=dp(5))

    def _route(self, points, shade, dashed):
        pts = []
        for p in points:
            pts += self.to_screen(p)
        Color(*color(shade))
        if not dashed:
            Line(points=pts, width=dp(3))
            return
        for (x0, y0), (x1, y1) in zip(zip(pts[0::2], pts[1::2]), zip(pts[2::2], pts[3::2])):
            length = math.hypot(x1 - x0, y1 - y0)
            pos = 0.0
            while length and pos < length:
                end = min(length, pos + dp(7))
                Line(points=[x0 + (x1 - x0) * pos / length, y0 + (y1 - y0) * pos / length,
                             x0 + (x1 - x0) * end / length, y0 + (y1 - y0) * end / length], width=dp(2))
                pos = end + dp(5)

    def _marker(self, marker):
        x, y = self.to_screen(marker['point'])
        if not (self.x - dp(40) <= x <= self.right + dp(40) and self.y - dp(40) <= y <= self.top + dp(40)):
            return
        kind = marker.get('kind', 'place')
        shade = color(KIND_COLORS.get(kind, '#075E4A'))
        r = dp({'driver': 6, 'registered': 8, 'ride': 10, 'me': 7, 'courier': 9}.get(kind, 8))
        Color(1, 1, 1, 1)
        Ellipse(pos=(x - r - dp(2), y - r - dp(2)), size=(2 * r + dp(4), 2 * r + dp(4)))
        Color(*shade)
        if kind == 'kitchen':
            RoundedRectangle(pos=(x - r, y - r), size=(2 * r, 2 * r), radius=[dp(3)])
        else:
            Ellipse(pos=(x - r, y - r), size=(2 * r, 2 * r))
        if kind in ('ride', 'place', 'home'):
            Color(*color('#DFFF73'))
            Ellipse(pos=(x - r / 3, y - r / 3), size=(2 * r / 3, 2 * r / 3))
        label = marker.get('label')
        if label:
            tex = text_texture(label, 10, '#182D26', kind in ('ride', 'place', 'home', 'kitchen', 'rider'))
            Color(1, 1, 1, .88)
            RoundedRectangle(pos=(x + r + dp(2), y - tex.size[1] / 2 - dp(1)),
                             size=(tex.size[0] + dp(8), tex.size[1] + dp(2)), radius=[dp(4)])
            Color(1, 1, 1, 1)
            Rectangle(texture=tex, pos=(x + r + dp(6), y - tex.size[1] / 2), size=tex.size)
