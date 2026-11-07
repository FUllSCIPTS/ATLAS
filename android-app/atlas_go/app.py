"""Python/Kivy screens for ATLAS Go: passengers, drivers and food sellers, live map and on-device ATLAS intelligence."""
import datetime as dt
import math
import os
import time
from pathlib import Path
from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import Label as CoreLabel
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, Rectangle, Line, Ellipse
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex as color, platform
from .domain import PLACES, distance, fare, money
from .store import LocalStore
from .location import DeviceLocation
from . import accounts as acc
from . import geo
from . import intelligence as ai
from . import livemap
from . import learned
from . import __version__

GREEN = color('#075E4A')
INK = color('#182D26')
MUTED = color('#5B6D64')
LIME = color('#DFFF73')
BG = color('#F6F7F2')
WHITE = color('#FFFFFF')
PALE = color('#E8F1E1')
VIOLET = color('#6E56CF')
LILAC = color('#EEEAFB')
SURGE = color('#D9822B')


class Panel(BoxLayout):
    def __init__(self, fill=WHITE, radius=20, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*fill)
            self.rectangle = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(radius)])
        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *_):
        self.rectangle.pos, self.rectangle.size = self.pos, self.size


class RouteMap(Widget):
    """Decorative route illustration for the hero cards (the live map is livemap.LiveMap)."""
    def __init__(self, **kwargs):
        super().__init__(size_hint_y=None, height=dp(135), **kwargs)
        self.bind(pos=self.draw, size=self.draw)

    def draw(self, *_):
        self.canvas.clear()
        x, y, w, h = self.x, self.y, self.width, self.height
        with self.canvas:
            Color(*color('#E7EEDC'))
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(15)])
            Color(*color('#D6E2C7'))
            for i in range(6):
                RoundedRectangle(pos=(x + i*w/6, y+h*.12), size=(w*.09,h*.78), radius=[dp(7)])
            Color(*color('#A9D0C6'))
            Line(points=[x+w*.66,y,x+w*.83,y+h], width=dp(10))
            Color(*WHITE)
            for i in range(4):
                Line(points=[x,y+h*(.13+i*.23),x+w,y+h*(.22+i*.23)], width=dp(5))
            Line(points=[x+w*.23,y,x+w*.16,y+h], width=dp(5))
            Line(points=[x+w*.48,y,x+w*.54,y+h], width=dp(5))
            Color(*GREEN)
            Line(points=[x+w*.19,y+h*.24,x+w*.48,y+h*.3,x+w*.51,y+h*.66,x+w*.8,y+h*.72], width=dp(3))
            for px, py in ((.19,.24),(.8,.72)):
                Ellipse(pos=(x+w*px-dp(9),y+h*py-dp(9)),size=(dp(18),dp(18)))
            Color(*LIME)
            for px, py in ((.19,.24),(.8,.72)):
                Ellipse(pos=(x+w*px-dp(3),y+h*py-dp(3)),size=(dp(6),dp(6)))


def _text(canvas_text, size, shade):
    label = CoreLabel(text=canvas_text, font_size=sp(size), color=shade)
    label.refresh()
    return label.texture


def dashed(points, dash, gap, width):
    """Dashed straight line drawn as separate segments (Kivy's dash style is not rendered on Android)."""
    (x0, y0), (x1, y1) = points
    length = math.hypot(x1 - x0, y1 - y0)
    if length <= 0:
        return
    ux, uy = (x1 - x0) / length, (y1 - y0) / length
    pos = 0.0
    while pos < length:
        end = min(length, pos + dash)
        Line(points=[x0 + ux * pos, y0 + uy * pos, x0 + ux * end, y0 + uy * end], width=width)
        pos = end + gap


class OutlookChart(Widget):
    """24 hourly bars of expected requests; surge hours in orange, agent's extra drivers in violet."""
    def __init__(self, hours, now=None, **kwargs):
        super().__init__(size_hint_y=None, height=dp(150), **kwargs)
        self.hours, self.now = hours, now
        self.bind(pos=self.draw, size=self.draw)

    def draw(self, *_):
        self.canvas.clear()
        x, y, w, h = self.x, self.y, self.width, self.height
        top = max(max(o.expected for o in self.hours), max(o.ordinary for o in self.hours), 1)
        base_y, chart_h = y + dp(30), h - dp(38)
        slot = w / 24
        with self.canvas:
            Color(*PALE)
            RoundedRectangle(pos=(x, y + dp(26)), size=(w, h - dp(26)), radius=[dp(10)])
            for o in self.hours:
                bx = x + o.hour * slot + slot * .15
                bh = chart_h * o.expected / top
                Color(*(SURGE if o.surge else GREEN))
                RoundedRectangle(pos=(bx, base_y), size=(slot * .7, max(dp(1), bh)), radius=[dp(2)])
                Color(*MUTED)
                oy = base_y + chart_h * o.ordinary / top
                Line(points=[bx - slot * .05, oy, bx + slot * .75, oy], width=dp(.8))
                if o.boost > 0:
                    Color(*VIOLET)
                    RoundedRectangle(pos=(bx, y + dp(18)), size=(slot * .7, dp(3) + dp(5) * min(1.0, o.boost)), radius=[dp(1)])
            if self.now is not None:
                Color(*INK)
                nx = x + (self.now + .5) * slot
                dashed(((nx, base_y), (nx, y + h - dp(4))), dp(4), dp(3), dp(1))
            for hr in (0, 6, 12, 18):
                tex = _text(f'{hr:02d}:00', 9, MUTED)
                Color(1, 1, 1, 1)
                Rectangle(texture=tex, pos=(x + hr * slot, y), size=tex.size)


class Bar(Widget):
    def __init__(self, fraction, shade=VIOLET, **kwargs):
        super().__init__(size_hint_y=None, height=dp(10), **kwargs)
        self.fraction, self.shade = max(0.0, min(1.0, fraction)), shade
        self.bind(pos=self.draw, size=self.draw)

    def draw(self, *_):
        self.canvas.clear()
        with self.canvas:
            Color(*PALE)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(5)])
            Color(*self.shade)
            RoundedRectangle(pos=self.pos, size=(max(dp(6), self.width * self.fraction), self.height), radius=[dp(5)])


class LearningCurve(Widget):
    """Waiting cost per ride as the sandbox policy trains (log-scale episodes; up is better)."""
    def __init__(self, **kwargs):
        super().__init__(size_hint_y=None, height=dp(170), **kwargs)
        self.curve, self.nearest, self.approved = [], None, None
        self.bind(pos=self.draw, size=self.draw)

    def update(self, curve, nearest, approved):
        self.curve, self.nearest, self.approved = list(curve), nearest, approved
        self.draw()

    def draw(self, *_):
        self.canvas.clear()
        x, y, w, h = self.x + dp(8), self.y + dp(20), self.width - dp(16), self.height - dp(30)
        lo, hi = 4.5, 10.5  # minutes of waiting cost; lower cost is drawn higher

        def px(ep):
            return x + w * math.log10(max(1, ep)) / math.log10(learned.TRAINING_EPISODES)

        def py(cost):
            return y + h * (hi - max(lo, min(hi, cost))) / (hi - lo)
        with self.canvas:
            Color(*PALE)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
            if self.nearest is not None:
                Color(*MUTED)
                dashed(((x, py(self.nearest)), (x + w, py(self.nearest))), dp(6), dp(4), dp(1.2))
                Color(*VIOLET)
                dashed(((x, py(self.approved)), (x + w, py(self.approved))), dp(2), dp(3), dp(1.2))
            if len(self.curve) > 1:
                Color(*GREEN)
                pts = []
                for ep, cost in self.curve:
                    pts += [px(ep), py(cost)]
                Line(points=pts, width=dp(1.8))
            for ep, name in ((1, '1'), (100, '100'), (1000, '1k'), (learned.TRAINING_EPISODES, '30k')):
                tex = _text(name, 9, MUTED)
                Color(1, 1, 1, 1)
                Rectangle(texture=tex, pos=(min(px(ep), x + w - tex.size[0]), self.y + dp(3)), size=tex.size)


class AtlasGoApp(App):
    title = 'ATLAS Go'

    def build(self):
        Window.clearcolor = BG
        Window.softinput_mode = 'below_target'
        Window.bind(on_keyboard=self.on_keyboard)
        data_dir = os.environ.get('ATLAS_DATA_DIR') or (self.user_data_dir if platform == 'android' else str(Path.home()/'.atlas-go'))
        self.data_dir = Path(data_dir)
        self.store = LocalStore(self.data_dir / 'state.json')
        self.tiles = livemap.loader(self.data_dir / 'tiles')
        self.gps = DeviceLocation(self.on_location, self.on_location_status)
        self.gps_status = ''
        ui = self.store.ui
        self.screen = ui.get('screen', 'home') if self.store.signed_in else 'welcome'
        self.pickup = ui.get('pickup', 0)
        self.destination = ui.get('destination', 1)
        self.party = ui.get('party', 1)
        self.comfort = ui.get('comfort', False)
        self.restaurant = ui.get('restaurant', 0)
        self.address = ui.get('address', 0)
        self.outlook_day = ui.get('outlook_day', 0)
        self.reg_role = ui.get('reg_role', 'passenger') if ui.get('reg_role') in acc.ROLES else 'passenger'
        self.form = {}
        self.lab = None
        self.models = None
        self.controls = {}
        self.live_map = None
        self.live_label = None
        self.live_paused = False
        self.container = BoxLayout(orientation='vertical')
        self.render()
        Clock.schedule_interval(self.live_tick, 1.0)
        return self.container

    def on_start(self):
        self.configure_system_bars()
        # Debug-only Python UI acceptance. The signed release ignores this intent.
        enabled = platform != 'android' and os.environ.get('ATLAS_UI_TEST') == '1'
        if platform == 'android':
            from jnius import autoclass
            activity = autoclass('org.kivy.android.PythonActivity').mActivity
            debuggable = bool(activity.getApplicationInfo().flags & 2)
            enabled = debuggable and activity.getIntent().getBooleanExtra('atlas_acceptance', False)
        if enabled:
            from .acceptance import Acceptance
            self.acceptance = Acceptance(self)
            Clock.schedule_once(self.acceptance.start, 1.5)

    def configure_system_bars(self, _dt=0):
        if platform != 'android':
            return
        from android.runnable import run_on_ui_thread
        from jnius import autoclass

        @run_on_ui_thread
        def read_insets():
            try:
                activity = autoclass('org.kivy.android.PythonActivity').mActivity
                sdk = int(autoclass('android.os.Build$VERSION').SDK_INT)
                window = activity.getWindow()
                decor = window.getDecorView()
                decor.setSystemUiVisibility(decor.getSystemUiVisibility() | 8192 | 16)
                if sdk >= 30:
                    controller = window.getInsetsController()
                    if controller is not None:
                        controller.setSystemBarsAppearance(24,24)
                insets = decor.getRootWindowInsets()
                if insets is None:
                    raise RuntimeError('System insets are not attached yet')
                if sdk >= 30:
                    types = autoclass('android.view.WindowInsets$Type')
                    bars = insets.getInsets(types.systemBars() | types.displayCutout())
                    bounds = (int(bars.left),int(bars.top),int(bars.right),int(bars.bottom))
                else:
                    bounds = (insets.getSystemWindowInsetLeft(),insets.getSystemWindowInsetTop(),
                              insets.getSystemWindowInsetRight(),insets.getSystemWindowInsetBottom())
                decor_height = int(decor.getHeight())
                Clock.schedule_once(lambda _dt:self.apply_system_insets(bounds,decor_height,sdk),0)
            except Exception:
                from kivy.logger import Logger
                Logger.exception('ATLAS: system inset query failed; applying safe portrait spacing')
                Clock.schedule_once(lambda _dt:setattr(self.container,'padding',(0,dp(40),0,dp(24))),0)
        read_insets()

    def apply_system_insets(self, bounds, decor_height, sdk):
        # Android 15+ draws into system-bar areas. Older fitted windows already
        # exclude them, so add padding only when their viewport fills the decor.
        self.container.padding = bounds if sdk >= 35 or abs(Window.height-decor_height)<=dp(2) else (0,0,0,0)

    def on_resume(self):
        Clock.schedule_once(self.configure_system_bars,.2)

    def save_ui(self):
        self.store.ui = {key: getattr(self, key) for key in ('screen','pickup','destination','party','comfort',
                                                             'restaurant','address','outlook_day','reg_role')}
        self.store.save()

    def today(self):
        override = os.environ.get('ATLAS_TODAY')
        return dt.date.fromisoformat(override) if override else dt.date.today()

    def on_pause(self):
        self.gps.stop()
        self.save_ui()
        return True

    def on_stop(self):
        self.gps.stop()
        self.save_ui()

    def home_screen(self):
        return {'driver': 'driver', 'seller': 'seller'}.get(self.store.role, 'home')

    def on_keyboard(self, _window, key, *_args):
        if key != 27:
            return False
        if self.screen in ('login', 'register') and not self.store.signed_in:
            self.go('welcome')
            return True
        if self.screen not in (self.home_screen(), 'welcome'):
            self.go(self.home_screen() if self.store.signed_in else 'welcome')
            return True
        return False

    # ------------------------------------------------------------------ building blocks
    def box(self, parent, fill=WHITE, padding=17):
        box = Panel(fill=fill, orientation='vertical', size_hint_y=None,
                    padding=dp(padding), spacing=dp(9))
        box.bind(minimum_height=box.setter('height'))
        parent.add_widget(box)
        return box

    def label(self, parent, text, size=15, shade=INK, bold=False):
        item = Label(text=text, font_size=sp(size), color=shade, bold=bold,
                     size_hint_y=None, halign='left', valign='middle', line_height=1.12)
        item.bind(width=lambda widget, value: setattr(widget, 'text_size', (value,None)))
        item.bind(texture_size=lambda widget, value: setattr(widget, 'height', value[1]+dp(3)))
        parent.add_widget(item)
        return item

    def gap(self, parent, height=6):
        parent.add_widget(Widget(size_hint_y=None, height=dp(height)))

    def button(self, parent, text, key, callback, primary=True, height=48):
        item = Button(text=text, size_hint_y=None, height=dp(height),
                      font_size=sp(14), bold=True, color=WHITE if primary else GREEN,
                      background_normal='', background_down='',
                      background_color=GREEN if primary else PALE,
                      padding=(dp(10),dp(6)))
        item.bind(width=lambda widget, value: setattr(widget, 'text_size',(value-dp(14),None)))
        item.bind(on_release=lambda _widget: self.safe(callback))
        self.controls[key] = item
        parent.add_widget(item)
        return item

    def row(self, parent, height=48):
        line = BoxLayout(size_hint_y=None, height=dp(height), spacing=dp(8))
        parent.add_widget(line)
        return line

    def field(self, parent, title, key, hint='', password=False, numeric=False):
        self.label(parent, title, 11, MUTED, True)
        item = TextInput(text=self.form.get(key, ''), hint_text=hint, password=password, multiline=False,
                         size_hint_y=None, height=dp(48), font_size=sp(15), padding=(dp(12), dp(13)),
                         background_normal='', background_active='', background_color=PALE,
                         foreground_color=INK, cursor_color=GREEN, write_tab=False,
                         input_type='number' if numeric else ('mail' if 'email' in key else 'text'))
        item.bind(text=lambda _w, value, key=key: self.form.__setitem__(key, value))
        self.controls[key] = item
        parent.add_widget(item)
        return item

    def safe(self, callback):
        try:
            callback()
        except (ValueError, OSError) as error:
            self.message('Check your details', str(error))

    def message(self, title, description, confirm=None, password=False):
        content = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(12))
        label = Label(text=description, color=INK, halign='left')
        label.bind(size=lambda widget,value: setattr(widget,'text_size',value))
        content.add_widget(label)
        secret = None
        if password:
            secret = TextInput(password=True, multiline=False, size_hint_y=None, height=dp(48), hint_text='Password',
                               background_normal='', background_active='', background_color=PALE, foreground_color=INK)
            self.controls['dialog_password'] = secret
            content.add_widget(secret)
        popup = Popup(title=title, content=content, size_hint=(.9,None), height=dp(320 if password else 260),
                      background='', background_color=WHITE, title_color=GREEN, separator_color=GREEN)
        def done():
            popup.dismiss()
            if confirm:
                confirm(secret.text) if password else confirm()
        self.button(content,'Confirm' if confirm else 'OK','dialog_confirm',done)
        if confirm:
            self.button(content,'Keep current data' if not password else 'Cancel','dialog_cancel',popup.dismiss,False)
        popup.open()

    def title_block(self, eyebrow, heading, description):
        self.label(self.body,eyebrow.upper(),11,GREEN,True)
        self.label(self.body,heading,29,INK,True)
        self.label(self.body,description,13,MUTED)
        self.gap(self.body,3)

    def go(self, screen):
        self.screen = screen
        self.save_ui()
        self.render()

    def nav_items(self):
        role = self.store.role
        if not self.store.signed_in:
            return ()
        if role == 'driver':
            return (('driver','Drive'),('map','Map'),('activity','Trips'),('profile','You'))
        if role == 'seller':
            return (('seller','Kitchen'),('seller_menu','Menu'),('activity','Orders'),('profile','You'))
        return (('home','Home'),('map','Map'),('food','Food'),('activity','Activity'),('profile','You'))

    def render(self):
        self.controls = {}
        if self.live_map is not None:
            self.live_map.detach()
        self.live_map, self.live_label = None, None
        self.container.clear_widgets()
        if not self.store.signed_in and self.screen not in ('welcome','login','register','privacy'):
            self.screen = 'welcome'
        allowed = {'driver': ('driver','map','activity','profile','privacy','intelligence','account'),
                   'seller': ('seller','seller_menu','activity','profile','privacy','intelligence','account')}
        if self.store.user and self.store.role in allowed and self.screen not in allowed[self.store.role]:
            self.screen = self.home_screen()
        if self.store.user and self.store.role == 'passenger' and self.screen in ('driver','seller','seller_menu'):
            self.screen = 'home'
        header = BoxLayout(size_hint_y=None,height=dp(58),padding=(dp(21),dp(5)),spacing=dp(8))
        self.label(header,'ATLAS Go',23,GREEN,True)
        user = self.store.user
        tag = (acc.ROLE_TITLES[user['role']] if user else 'GUEST' if self.store.guest else 'WELCOME').upper()
        badge = Label(text=tag,size_hint_x=None,width=dp(110),font_size=sp(10),bold=True,color=GREEN)
        header.add_widget(badge)
        self.container.add_widget(header)
        self.scroll = ScrollView(do_scroll_x=False,bar_width=dp(3))
        self.body = BoxLayout(orientation='vertical',size_hint_y=None,padding=(dp(21),dp(12),dp(21),dp(24)),spacing=dp(12))
        self.body.bind(minimum_height=self.body.setter('height'))
        self.scroll.add_widget(self.body)
        self.container.add_widget(self.scroll)
        screens = {'welcome':self.welcome,'login':self.login,'register':self.register,
                   'home':self.home,'ride':lambda:self.ride(False),'share':lambda:self.ride(True),
                   'food':self.food,'menu':self.menu,'cart':self.cart,'active_ride':self.active_ride,
                   'active_order':self.active_order,'activity':self.activity,'profile':self.profile,'privacy':self.privacy,
                   'intelligence':self.intelligence,'map':self.map_screen,'driver':self.driver,
                   'seller':self.seller,'seller_menu':self.seller_menu,'account':self.profile}
        screens.get(self.screen,self.home)()
        items = self.nav_items()
        if items:
            nav = BoxLayout(size_hint_y=None,height=dp(62),padding=dp(7),spacing=dp(4))
            for key, name in items:
                button = self.button(nav,name,'nav_'+key,lambda key=key:self.go(key),False)
                button.size_hint_y = 1
                button.font_size = sp(11)
                button.padding = (0,0)
                button.bind(width=lambda widget,value:setattr(widget,'text_size',(value-dp(4),None)))
                button.background_color = LIME if self.screen == key else WHITE
            self.container.add_widget(nav)

    # ------------------------------------------------------------------ live updates
    def live_tick(self, _dt):
        if self.live_paused:
            return
        try:
            changed = self.store.tick()
        except OSError:
            return
        if changed and self.screen in ('active_ride','active_order','driver','seller','map','home','activity'):
            self.render()
            return
        self.refresh_live()

    def refresh_live(self):
        if self.live_map is not None:
            markers, routes = self.map_layers(self.screen)
            accuracy = (self.gps.point, self.gps.accuracy or 30) if self.gps.point else None
            self.live_map.set_layers(markers, routes, accuracy)
        if self.live_label is not None:
            self.live_label.text = self.live_text()

    def live_text(self):
        now = time.time()
        if self.screen in ('active_ride','driver') and self.store.ride:
            return geo.ride_eta_text(self.store.ride, now)
        if self.screen == 'active_order' and self.store.order:
            order = self.store.order
            if order.get('pending'):
                return 'Waiting for the kitchen to accept'
            pos, progress = geo.order_position(order, now, self.store.kitchen_prep(order['restaurant']))
            if order['stage'] == 0:
                return f'Kitchen is cooking · {round(progress*100)}% of the preparation time'
            return 'Courier is riding to you' if order['stage'] == 1 else 'Courier is at your door'
        if self.screen == 'map':
            parts = []
            if self.tiles.offline:
                parts.append('Map tiles offline · showing the schematic map')
            if self.gps_status:
                parts.append(self.gps_status)
            elif self.gps.point:
                place, km = geo.nearest_place(self.gps.point)
                parts.append(f'You are {km:.1f} km from {PLACES[place]}')
            return ' · '.join(parts) or 'Live · drivers update every second'
        return ''

    def map_layers(self, screen):
        now = time.time()
        markers, routes = [], []
        ride, order = self.store.ride, self.store.order
        if screen == 'map':
            for i, name in enumerate(PLACES):
                markers.append(dict(kind='place', point=geo.PLACE_COORDS[i], label=name))
            seen = set()
            for p, pool in enumerate(ai.DRIVER_POOLS):
                for k, c in enumerate(pool):
                    if c.name in seen:
                        continue
                    seen.add(c.name)
                    markers.append(dict(kind='driver', point=geo.zone_drift(c.zone, now, p*1.7+k), label=''))
            for account in self.store.online_drivers():
                markers.append(dict(kind='registered', point=self.store.driver_position(account),
                                    label=account['name'].split()[0]+' · online'))
            for kitchen in self.store.catalog.listed():
                point = geo.KITCHEN_COORDS[kitchen.id] if kitchen.id < 3 else \
                    (geo.PLACE_COORDS[kitchen.place][0]+0.0012, geo.PLACE_COORDS[kitchen.place][1]-0.0016)
                markers.append(dict(kind='kitchen', point=point, label=kitchen.name))
        if ride and screen in ('map','active_ride','driver'):
            car, _ = geo.ride_position(ride, now)
            start, pickup, dest = geo.ride_legs(ride)
            if screen != 'map':
                markers += [dict(kind='home', point=pickup, label='Pickup · '+PLACES[ride['pickup']]),
                            dict(kind='place', point=dest, label=PLACES[ride['destination']])]
            routes.append(([pickup, dest], '#075E4A', False))
            if ride['stage'] == 0:
                routes.append(([car, pickup], '#6E56CF', True))
            markers.append(dict(kind='ride', point=car, label=ride['driver'].split(' · ')[0]))
        if order and screen in ('map','active_order'):
            pos, _ = geo.order_position(order, now, self.store.kitchen_prep(order['restaurant']))
            kitchen = tuple(order['live']['kitchen'])
            home = geo.PLACE_COORDS[order['address']]
            if screen != 'map':
                markers += [dict(kind='kitchen', point=kitchen, label=self.store.catalog.name(order['restaurant'])),
                            dict(kind='home', point=home, label='You · '+PLACES[order['address']])]
            routes.append(([kitchen, home], '#D9822B', True))
            if pos is not None:
                markers.append(dict(kind='courier', point=pos, label='Courier'))
        if self.gps.point:
            markers.append(dict(kind='me', point=self.gps.point, label='You'))
        return markers, routes

    def add_map(self, parent, height, interactive=False, fit=None):
        self.live_map = livemap.LiveMap(size_hint_y=None, height=dp(height), interactive=interactive, tile_loader=self.tiles)
        parent.add_widget(self.live_map)
        markers, routes = self.map_layers(self.screen)
        self.live_map.set_layers(markers, routes, (self.gps.point, self.gps.accuracy or 30) if self.gps.point else None)
        if fit:
            self.live_map.fit(fit)
        return self.live_map

    def on_location(self, point, accuracy):
        self.gps_status = ''
        self.store.update_location(point)
        self.refresh_live()

    def on_location_status(self, text):
        self.gps_status = text
        self.refresh_live()

    def locate(self):
        if not self.gps.available:
            self.message('Location', 'Your location is available when the app runs on an Android phone.')
            return
        self.gps.start()
        if self.gps.point and self.live_map is not None:
            self.live_map.set_view(self.gps.point, max(self.live_map.zoom, 15))
        self.refresh_live()

    # ------------------------------------------------------------------ welcome and accounts
    def welcome(self):
        self.title_block('Cork, Ireland','Your city. One app.','Rides, shared journeys and local food, with ATLAS intelligence on your phone.')
        hero = self.box(self.body,GREEN)
        self.label(hero,'MOVE TOGETHER',10,LIME,True)
        self.label(hero,'Ride, drive or sell food.\nOne account each.',25,WHITE,True)
        self.label(hero,'Passengers book rides and order food. Drivers go online and accept trips. '
                        'Food sellers list their kitchen and menu.',13,WHITE)
        hero.add_widget(RouteMap())
        self.button(self.body,'Create an account','welcome_register',lambda:self.go('register'))
        self.button(self.body,'Sign in','welcome_login',lambda:self.go('login'),False)
        self.button(self.body,'Continue as a guest passenger','welcome_guest',self.guest,False)
        self.button(self.body,'Privacy notice','welcome_privacy',lambda:self.go('privacy'),False)
        self.label(self.body,'Accounts are stored securely on this phone. Rides, deliveries and payments are '
                             'simulated until ATLAS Go is connected to an operator back end.',12,MUTED)

    def guest(self):
        self.store.continue_as_guest()
        self.go('home')

    def login(self):
        self.title_block('Welcome back','Sign in','Use the email and password you registered on this phone.')
        card = self.box(self.body)
        self.field(card,'EMAIL','login_email','name@example.ie')
        self.field(card,'PASSWORD','login_password','Your password',password=True)
        self.button(card,'Sign in','login_submit',self.submit_login)
        self.button(self.body,'Create an account','login_register',lambda:self.go('register'),False)
        self.button(self.body,'Back','login_back',lambda:self.go('welcome'),False)

    def submit_login(self):
        self.store.login(self.form.get('login_email',''), self.form.get('login_password',''))
        self.form.pop('login_password', None)
        self.go(self.home_screen())

    def set_reg_role(self, role):
        self.reg_role = role
        self.go('register')

    def register(self):
        self.title_block('Join ATLAS Go','Create your account','Choose how you will use ATLAS Go. You can create more accounts later.')
        roles = self.row(self.body,48)
        for role in acc.ROLES:
            b = self.button(roles,{'seller':'Seller'}.get(role,acc.ROLE_TITLES[role]),'reg_role_'+role,lambda r=role:self.set_reg_role(r),False)
            b.font_size = sp(12)
            b.background_color = LIME if self.reg_role == role else WHITE
        card = self.box(self.body)
        self.label(card,'YOUR DETAILS',10,GREEN,True)
        self.field(card,'FULL NAME','reg_name','Aoife Murphy')
        self.field(card,'EMAIL','reg_email','name@example.ie')
        self.field(card,'MOBILE','reg_phone','087 123 4567')
        self.field(card,'PASSWORD (8+ CHARACTERS, A LETTER AND A NUMBER)','reg_password','Create a password',password=True)
        self.field(card,'CONFIRM PASSWORD','reg_confirm','Repeat the password',password=True)
        if self.reg_role == 'driver':
            car = self.box(self.body)
            self.label(car,'VEHICLE AND LICENCE',10,GREEN,True)
            self.field(car,'VEHICLE (MAKE, MODEL, COLOUR)','reg_vehicle','Toyota Corolla · silver')
            self.field(car,'REGISTRATION','reg_plate','241-C-1234')
            self.field(car,'SPSV DRIVER LICENCE NUMBER','reg_licence','A12345')
            self.field(car,'PASSENGER SEATS','reg_seats','4',numeric=True)
            self.select(car,'USUAL STARTING AREA',PLACES,self.form.get('reg_base',1),'reg_base',
                        lambda v:self.form.__setitem__('reg_base',v))
            self.label(car,'Licence and registration are checked for format only. An operator must verify '
                           'documents before real passengers are carried.',11,MUTED)
        elif self.reg_role == 'seller':
            shop = self.box(self.body)
            self.label(shop,'YOUR KITCHEN',10,GREEN,True)
            self.field(shop,'KITCHEN NAME','reg_kitchen','Lee Side Bakery')
            self.field(shop,'CUISINE','reg_cuisine','Bakery & coffee')
            self.field(shop,'FOOD BUSINESS REGISTRATION NUMBER','reg_business','FBO-12345')
            self.field(shop,'TYPICAL PREPARATION TIME (MINUTES)','reg_prep','15',numeric=True)
            self.select(shop,'KITCHEN LOCATION',PLACES,self.form.get('reg_place',1),'reg_place',
                        lambda v:self.form.__setitem__('reg_place',v))
            self.label(shop,'Add dishes after registering. The registration number is self-declared and not verified.',11,MUTED)
        agree = self.button(self.body,('[x] ' if self.form.get('reg_agree') else '[  ] ')+'I have read the privacy notice',
                            'reg_agree',self.toggle_agree,False)
        agree.background_color = LIME if self.form.get('reg_agree') else WHITE
        self.button(self.body,'Create '+acc.ROLE_TITLES[self.reg_role].lower()+' account','register_submit',self.submit_register)
        self.button(self.body,'I already have an account','reg_login',lambda:self.go('login'),False)

    def toggle_agree(self):
        self.form['reg_agree'] = not self.form.get('reg_agree')
        self.render()

    def submit_register(self):
        f = self.form
        if not f.get('reg_agree'):
            raise ValueError('Please read and accept the privacy notice first.')
        if f.get('reg_password','') != f.get('reg_confirm',''):
            raise ValueError('The two passwords do not match.')
        self.store.register(self.reg_role, f.get('reg_name',''), f.get('reg_email',''), f.get('reg_phone',''),
                            f.get('reg_password',''), vehicle=f.get('reg_vehicle',''), plate=f.get('reg_plate',''),
                            licence=f.get('reg_licence',''), seats=f.get('reg_seats','4') or '4', base=f.get('reg_base',1),
                            kitchen=f.get('reg_kitchen',''), cuisine=f.get('reg_cuisine',''),
                            registration=f.get('reg_business',''), place=f.get('reg_place',1),
                            prep=f.get('reg_prep','15') or '15')
        self.form = {}
        self.go(self.home_screen())

    def logout(self):
        self.gps.stop()
        self.store.logout()
        self.form = {}
        self.go('welcome')

    def delete_account(self, password):
        self.store.delete_account(password)
        self.form = {}
        self.go('welcome')

    # ------------------------------------------------------------------ passenger home
    def home(self):
        user = self.store.user
        first = user['name'].split()[0] if user else None
        self.title_block('Cork, Ireland',f'Hi {first}.' if first else 'Your city. One app.','Go somewhere good. Bring someone along.')
        hero = self.box(self.body,GREEN)
        self.label(hero,'MOVE TOGETHER',10,LIME,True)
        self.label(hero,'A little less driving.\nA lot more living.',25,WHITE,True)
        self.label(hero,'Rides, shared journeys and local food.',13,WHITE)
        hero.add_widget(RouteMap())
        quick = BoxLayout(size_hint_y=None,height=dp(54),spacing=dp(8))
        self.body.add_widget(quick)
        for name, key in (('Ride','ride'),('Share ride','share'),('Food','food')):
            self.button(quick,name,'home_'+key,lambda key=key:self.go(key),key=='ride',54)
        self.button(self.body,'Live map · drivers, kitchens and you','home_map',lambda:self.go('map'),False)
        today = ai.day_summary(self.today())
        smart = self.box(self.body,LILAC)
        self.label(smart,'TODAY IN CORK · ATLAS INTELLIGENCE',10,VIOLET,True)
        self.label(smart,today['title'],19,INK,True)
        self.label(smart,today['text'],13,MUTED)
        self.button(smart,'How ATLAS learns >','home_learn',lambda:self.go('intelligence'),False)
        self.label(self.body,'Made for your everyday',20,INK,True)
        share = self.box(self.body,color('#E9F1DA'))
        self.label(share,'SHARED RIDES · FROM €4.90 / SEAT',10,GREEN,True)
        self.label(share,'Same direction? Share the journey.',19,INK,True)
        self.label(share,'Choose a route, check seats and join a carpool.',13,MUTED)
        self.button(share,'Find a shared ride >','home_pool',lambda:self.go('share'),False)
        food = self.box(self.body)
        self.label(food,'Something delicious is nearby.',19,INK,True)
        count = len(self.store.catalog.listed())
        self.label(food,f'{count} kitchens · bowls, pizza, comfort food and local sellers',13,MUTED)
        self.button(food,'Explore food >','home_eat',lambda:self.go('food'),False)
        if self.store.ride:
            self.button(self.body,'View active ride','home_active_ride',lambda:self.go('active_ride'))
        if self.store.order:
            self.button(self.body,'Track food order','home_active_order',lambda:self.go('active_order'))
        self.label(self.body,'Rides, deliveries and payments are simulated · no real charges.',12,MUTED)

    def select(self, parent, title, values, value, key, callback):
        self.label(parent,title,11,MUTED,True)
        spinner = Spinner(text=values[value],values=values,size_hint_y=None,height=dp(48),
                          background_normal='',background_color=PALE,color=INK,font_size=sp(14))
        spinner.bind(text=lambda _widget, text:callback(list(values).index(text)))
        self.controls[key] = spinner
        parent.add_widget(spinner)

    def update_selection(self, field, value):
        setattr(self,field,value)
        self.save_ui()
        Clock.schedule_once(lambda _dt:self.render(),0)

    # ------------------------------------------------------------------ map
    def map_screen(self):
        self.scroll.do_scroll_y = False
        self.label(self.body,'LIVE MAP · CORK',11,GREEN,True)
        height = max(260, (Window.height - self.container.padding[1] - self.container.padding[3]) / dp(1) - 330)
        self.add_map(self.body, height, interactive=True)
        self.live_map.set_view(zoom=14)
        if self.store.ride or self.store.order:
            points = [geo.ride_position(self.store.ride, time.time())[0]] if self.store.ride else []
            if self.store.order:
                points.append(geo.PLACE_COORDS[self.store.order['address']])
            self.live_map.set_view(points[0], 14)
        tools = self.row(self.body,48)
        self.button(tools,'-','map_zoom_out',lambda:self.live_map.zoom_by(-1),False)
        self.button(tools,'+','map_zoom_in',lambda:self.live_map.zoom_by(1),False)
        self.button(tools,'Me','map_locate',self.locate,False)
        self.button(tools,'Cork','map_cork',lambda:self.live_map.set_view(geo.CORK, 13),False)
        self.live_label = self.label(self.body,self.live_text(),12,INK,True)
        self.label(self.body,'Green: pickup places · grey: drivers nearby · violet: registered drivers online · '
                             'orange: kitchens and couriers · blue: you. Straight-line routes, 10× time-lapse.',11,MUTED)

    # ------------------------------------------------------------------ rides
    def ride(self, shared=False):
        self.title_block('More company. Less cost.' if shared else "Let's get moving",
                         'Share the journey' if shared else 'Where are we going?',
                         'Carpools on the same route with available seats' if shared else 'Book a ride between saved places.')
        route = self.box(self.body)
        self.select(route,'PICKUP',PLACES,self.pickup,'pickup',lambda v:self.update_selection('pickup',v))
        self.select(route,'DESTINATION',PLACES,self.destination,'destination',lambda v:self.update_selection('destination',v))
        if self.gps.available:
            self.button(route,'Pick up near my location','ride_locate',self.pickup_here,False)
        if shared:
            self.select(route,'SEATS NEEDED',('1 seat','2 seats'),self.party-1,'party',lambda v:self.update_selection('party',v+1))
        else:
            self.select(route,'RIDE OPTION',('ATLAS Go · everyday value','ATLAS Comfort · extra space'),int(self.comfort),'vehicle',lambda v:self.update_selection('comfort',bool(v)))
        self.button(route,'Find matching rides' if shared else 'Update estimate','find_pool' if shared else 'estimate',lambda:self.render())
        if self.pickup == self.destination:
            self.label(self.body,'Choose two different places to continue.',15,MUTED)
            return
        if not shared:
            preview = self.box(self.body)
            self.label(preview,'ATLAS Comfort' if self.comfort else 'ATLAS Go',21,INK,True)
            chosen, _why, _start = self.pick_driver(self.pickup)
            self.label(preview,f'Pickup in about {chosen.eta} min · {distance(self.pickup,self.destination)} km route',12,MUTED)
            self.label(preview,money(fare(self.pickup,self.destination,self.comfort)),31,GREEN,True)
            surge = ai.surge_level(self.today(), dt.datetime.now().hour)
            self.label(preview,'Estimated total · simulated payment' + (f' · busy period ({round(surge*100)}% surge forecast)' if surge >= .2 else ''),12,MUTED)
            self.button(preview,'Book ride','book_ride',self.book_solo)
            self.dispatch_card()
        else:
            found = [o for o in self.store.offers if o.matches(self.pickup,self.destination,self.party)]
            for offer in found:
                card = self.box(self.body)
                self.label(card,offer.driver,17,INK,True)
                self.label(card,f'Leaves in 8 min · {offer.seats} seats available',12,MUTED)
                self.label(card,f'{money(offer.price)} per seat',23,GREEN,True)
                self.label(card,f'Total for {self.party}: {money(offer.price*self.party)}',13,MUTED)
                self.button(card,'Join shared ride','join_'+offer.id,lambda o=offer:self.book_shared(o.id))
            if not found:
                card = self.box(self.body)
                self.label(card,'No matching rides right now',20,INK,True)
                self.label(card,'Try UCC Campus > Cork City Centre with one or two seats.',14,MUTED)

    def pickup_here(self):
        self.gps.start()
        if not self.gps.point:
            self.message('Finding your location', self.gps_status or 'Allow location access, then try again in a few seconds.')
            return
        place, km = geo.nearest_place(self.gps.point)
        self.pickup = place
        self.save_ui()
        self.render()
        self.message('Pickup set', f'Nearest pickup point: {PLACES[place]} ({km:.1f} km from you).')

    def registered_candidates(self, pickup):
        hour = dt.datetime.now().hour
        surge = ai.surge_level(self.today(), hour)
        online = self.store.online_drivers()
        point = geo.PLACE_COORDS[pickup]
        return [ai.registered_candidate(a, self.store.driver_position(a), point, surge, len(online) == 1 and surge >= .5)
                for a in online]

    def pick_driver(self, pickup, exclude=()):
        chosen, why = ai.choose(pickup, extra=self.registered_candidates(pickup), exclude=exclude)
        if chosen.account:
            start = self.store.driver_position(self.store.account(chosen.account))
        else:
            start = geo.zone_drift(chosen.zone, time.time())
        return chosen, why, start

    def dispatch_card(self):
        extra = self.registered_candidates(self.pickup)
        chosen, why = ai.choose(self.pickup, extra=extra)
        card = self.box(self.body,LILAC)
        self.label(card,f'ATLAS PICKS YOUR DRIVER · POLICY {learned.POLICY_VERSION}',10,VIOLET,True)
        for candidate, probability in ai.rank(self.pickup, extra=extra)[:5]:
            mark = '>' if candidate == chosen else ' '
            self.label(card,f'{mark} {candidate.name} · {candidate.zone}',15,INK,candidate == chosen)
            self.label(card,f'{candidate.eta} min away · {round(candidate.accept*100)}% likely to accept · '
                            f'area surge {round(candidate.surge*100)}%' + (' · last free car' if candidate.last else ''),11,MUTED)
        self.label(card,why,13,INK)
        self.label(card,'Learned by reinforcement learning in a simulated city. Registered drivers who are online '
                        'on this phone compete with the simulated fleet.',11,MUTED)

    def book_solo(self):
        chosen, why, start = self.pick_driver(self.pickup)
        label = f'{chosen.name} · ' + ('registered driver' if chosen.account else 'ATLAS demo driver')
        self.store.book(self.pickup,self.destination,self.comfort,driver=label,why=why,
                        driver_id=chosen.account or None,start=start)
        self.go('active_ride')

    def book_shared(self, offer_id):
        self.store.book(self.pickup,self.destination,offer_id=offer_id,party=self.party)
        self.go('active_ride')

    def active_ride(self):
        ride = self.store.ride
        if not ride:
            self.screen = 'activity'
            self.activity()
            return
        self.title_block('Booking confirmed',"You're sharing this ride" if ride['shared'] else 'Your ride is booked',
                         'Live map · simulated journey')
        start, pickup, dest = geo.ride_legs(ride)
        self.add_map(self.body, 230, fit=[start, pickup, dest])
        self.live_label = self.label(self.body,self.live_text(),14,VIOLET,True)
        card = self.box(self.body)
        stage = ('Waiting for driver',) if ride.get('pending') else ('Driver on the way','Driver at pickup','On your way')
        self.label(card,stage[0] if ride.get('pending') else stage[ride['stage']],23,GREEN,True)
        self.label(card,ride['driver'],17,INK,True)
        self.label(card,f"{PLACES[ride['pickup']]} > {PLACES[ride['destination']]}",14,MUTED)
        self.label(card,f"{money(ride['fare'])} · {ride['party']} seat(s)",25,INK,True)
        self.label(card,'Reference '+ride['id'],10,MUTED)
        if ride.get('why'):
            why = self.box(self.body,LILAC)
            self.label(why,'WHY THIS DRIVER',10,VIOLET,True)
            self.label(why,ride['why'],13,INK)
        if ride.get('driver_id'):
            if ride.get('pending'):
                self.label(self.body,'This driver is registered on this phone. Sign in as the driver to accept, '
                                     'or ask ATLAS for another driver.',13,MUTED)
                self.button(self.body,'Choose another driver','ride_redispatch',self.redispatch,False)
            else:
                self.label(self.body,'Your driver updates the trip from the driver app.',13,MUTED)
            self.button(self.body,'Switch account','ride_switch',self.logout,False)
        else:
            self.label(self.body,'The journey moves on its own. Skip ahead to jump to the next stage.',13,MUTED)
            self.button(self.body,'Complete ride' if ride['stage']==2 else 'Skip to next stage','ride_next',self.next_ride)
        self.button(self.body,'Cancel ride','ride_cancel',lambda:self.message('Cancel this ride?','Your reserved shared seats will be released.',self.cancel_ride),False)

    def redispatch(self):
        ride = self.store.ride
        exclude = [ride['driver_id']] + ride.get('declined', [])
        chosen, why, start = self.pick_driver(ride['pickup'], exclude=exclude)
        before = self.store.snapshot()
        ride.setdefault('declined', []).append(ride['driver_id'])
        ride.update(driver=f'{chosen.name} · ' + ('registered driver' if chosen.account else 'ATLAS demo driver'),
                    why=why, driver_id=chosen.account or None, pending=bool(chosen.account),
                    live=dict(start=[start[0], start[1]], t=time.time()))
        self.store.commit(before)
        self.render()

    def next_ride(self):
        self.store.advance_ride()
        self.go('active_ride' if self.store.ride else 'activity')

    def cancel_ride(self):
        self.store.advance_ride(cancel=True)
        self.go(self.home_screen() if self.store.role == 'driver' else 'activity')

    # ------------------------------------------------------------------ driver
    def driver(self):
        user = self.store.user
        d = user['driver']
        self.title_block('Driver','Ready when you are, '+user['name'].split()[0]+'.',
                         f"{d['vehicle']} · {d['plate']} · {d['seats']} seats")
        status = self.box(self.body, GREEN if d['online'] else WHITE)
        self.label(status,'YOU ARE ONLINE' if d['online'] else 'YOU ARE OFFLINE',11,LIME if d['online'] else GREEN,True)
        self.label(status,'Passengers on this phone can be matched to you.' if d['online'] else
                   'Go online to receive ride requests from ATLAS dispatch.',15,WHITE if d['online'] else INK)
        self.button(status,'Go offline' if d['online'] else 'Go online','driver_online',
                    lambda:(self.store.set_online(not d['online']),self.render()),not d['online'])
        self.select(status,'STARTING AREA',PLACES,d['base'],'driver_base',
                    lambda v:(self.store.set_online(d['online'],v),Clock.schedule_once(lambda _dt:self.render(),0)))
        self.button(status,'Use my phone location','driver_locate',self.locate,False)
        job = self.store.driver_job()
        if job:
            card = self.box(self.body,LILAC)
            if job.get('pending'):
                self.label(card,'NEW RIDE REQUEST',10,VIOLET,True)
                self.label(card,f"{PLACES[job['pickup']]} > {PLACES[job['destination']]}",19,INK,True)
                eta = geo.eta_minutes(self.store.driver_position(user), geo.PLACE_COORDS[job['pickup']])
                self.label(card,f"{money(job['fare'])} · pickup about {eta} min away",15,INK)
                if job.get('why'):
                    self.label(card,'ATLAS chose you: '+job['why'],12,MUTED)
                row = self.row(card,48)
                self.button(row,'Accept','job_accept',self.job_accept)
                self.button(row,'Decline','job_decline',self.job_decline,False)
            else:
                self.label(card,'CURRENT TRIP',10,VIOLET,True)
                self.label(card,f"{PLACES[job['pickup']]} > {PLACES[job['destination']]} · {money(job['fare'])}",17,INK,True)
                start, pickup, dest = geo.ride_legs(job)
                self.add_map(card, 200, fit=[start, pickup, dest])
                self.live_label = self.label(card,self.live_text(),13,VIOLET,True)
                self.button(card,('I have arrived at pickup','Start trip','Complete trip')[job['stage']],'job_next',self.job_next)
        stats = self.box(self.body)
        self.label(stats,'YOUR WEEK',10,GREEN,True)
        rate = ai.acceptance(d['offered'], d['accepted'])
        self.label(stats,f"{d['trips']} trips · {money(d['earnings'])} fares",21,INK,True)
        self.label(stats,f"Requests accepted {d['accepted']} of {d['offered']} · ATLAS expects you to accept {round(rate*100)}%",13,MUTED)
        today = ai.day_summary(self.today())
        smart = self.box(self.body,LILAC)
        self.label(smart,'WHEN TO DRIVE · ATLAS OUTLOOK',10,VIOLET,True)
        self.label(smart,today['title'],17,INK,True)
        self.label(smart,today['text'],13,MUTED)
        self.label(smart,today['agent'],13,VIOLET)

    def job_accept(self):
        self.store.driver_respond(True)
        self.render()

    def job_decline(self):
        job = self.store.driver_job()
        exclude = [self.store.user['id']] + job.get('declined', [])
        chosen, why, start = self.pick_driver(job['pickup'], exclude=exclude)
        self.store.driver_respond(False, fallback=dict(
            driver=f'{chosen.name} · ' + ('registered driver' if chosen.account else 'ATLAS demo driver'),
            why=why, start=start, driver_id=chosen.account or None))
        self.render()

    def job_next(self):
        self.store.driver_advance()
        self.render()

    # ------------------------------------------------------------------ seller
    def seller(self):
        kitchen = self.store.kitchen_of(self.store.user)
        self.title_block('Food seller',kitchen['name'],f"{kitchen['cuisine']} · near {PLACES[kitchen['place']]}")
        card = self.box(self.body, GREEN if kitchen['open'] else WHITE)
        live = [x for x in kitchen['dishes'] if not x.get('archived')]
        listed = kitchen['open'] and live
        self.label(card,'OPEN · LISTED FOR PASSENGERS' if listed else 'OPEN · ADD A DISH TO BE LISTED' if kitchen['open'] else 'CLOSED',
                   11,LIME if kitchen['open'] else GREEN,True)
        self.label(card,f"{len(live)} dishes · ready in about {kitchen['prep']} min",15,WHITE if kitchen['open'] else INK)
        self.button(card,'Close kitchen' if kitchen['open'] else 'Open kitchen','kitchen_open',
                    lambda:(self.store.update_kitchen(open_=not kitchen['open']),self.render()),not kitchen['open'])
        self.button(card,'Edit menu','kitchen_menu',lambda:self.go('seller_menu'),False)
        order = self.store.seller_order()
        if order:
            box = self.box(self.body,LILAC)
            self.label(box,'NEW ORDER' if order.get('pending') else 'CURRENT ORDER',10,VIOLET,True)
            for item, quantity in order['items'].items():
                self.label(box,f"{quantity} × {self.store.catalog.dishes[item].name}",16,INK,True)
            self.label(box,f"Deliver to {PLACES[order['address']]} · food {money(order['fare']-250)}",13,MUTED)
            if order.get('courier'):
                self.label(box,ai.courier_text(order['courier']),12,INK)
            if order.get('pending'):
                self.button(box,'Accept and start cooking','order_accept',lambda:(self.store.seller_accept(),self.render()))
            elif order['stage'] == 0:
                self.button(box,'Food is ready for the courier','order_ready',lambda:(self.store.seller_ready(),self.render()))
            else:
                self.label(box,'Courier is delivering this order.' if order['stage']==1 else 'Courier is at the door.',14,VIOLET,True)
        prep = self.box(self.body)
        self.label(prep,'PREPARATION TIME',10,GREEN,True)
        self.form.setdefault('kitchen_prep',str(kitchen['prep']))
        self.field(prep,'MINUTES FROM ACCEPTING TO READY','kitchen_prep','15',numeric=True)
        self.button(prep,'Save preparation time','kitchen_prep_save',
                    lambda:(self.store.update_kitchen(prep=self.form.get('kitchen_prep')),self.render()),False)
        plan = ai.courier_plan(kitchen['id'], prep=kitchen['prep'])
        self.label(prep,'COURIER TIMING · LEARNED',10,VIOLET,True)
        self.label(prep,ai.courier_text(plan),13,INK)
        stats = self.box(self.body)
        self.label(stats,'SALES',10,GREEN,True)
        self.label(stats,f"{kitchen.get('orders',0)} orders delivered · {money(kitchen.get('sales',0))} food sales",19,INK,True)
        self.label(stats,'Registration '+kitchen['registration']+' · self-declared',11,MUTED)

    def seller_menu(self):
        kitchen = self.store.kitchen_of(self.store.user)
        self.title_block('Your menu',kitchen['name'],'Passengers see dishes as soon as you add them.')
        live = [x for x in kitchen['dishes'] if not x.get('archived')]
        if not live:
            self.label(self.body,'No dishes yet. Add your first one below.',15,MUTED)
        for dish in live:
            card = self.box(self.body)
            self.label(card,dish['name'],19,INK,True)
            self.label(card,dish['detail'],13,MUTED)
            self.label(card,money(dish['price']),20,GREEN,True)
            self.button(card,'Remove from menu','archive_'+dish['id'],lambda i=dish['id']:(self.store.archive_dish(i),self.render()),False)
        add = self.box(self.body,LILAC)
        self.label(add,'ADD A DISH',10,VIOLET,True)
        self.field(add,'DISH NAME','dish_name','Sourdough toastie')
        self.field(add,'SHORT DESCRIPTION','dish_detail','Cheddar · red onion · rocket')
        self.field(add,'PRICE (€)','dish_price','8.50')
        self.button(add,'Add dish','dish_add',self.add_dish)

    def add_dish(self):
        self.store.add_dish(self.form.get('dish_name',''), self.form.get('dish_detail',''), self.form.get('dish_price',''))
        for key in ('dish_name','dish_detail','dish_price'):
            self.form.pop(key, None)
        self.render()

    # ------------------------------------------------------------------ food
    def food(self):
        self.title_block('Good food. Close by.','What are you craving?','Cork kitchens · deliveries and payments are simulated')
        descriptions = ('Fresh bowls & wraps · 20–30 min','Stone-baked favourites · 25–35 min','Indian comfort food · 25–40 min')
        marks = ('FRESH & COLOURFUL','SLICE OF HAPPINESS','WARM & SPICED')
        fills = ('#E4EFCC','#F6E4C8','#F0DECF')
        for kitchen in self.store.catalog.listed():
            index = kitchen.id
            card = self.box(self.body)
            banner = self.box(card,color(fills[index] if index < 3 else '#E9E4F7'),20)
            self.label(banner,marks[index] if index < 3 else 'LOCAL SELLER · '+kitchen.cuisine.upper(),17,GREEN if index < 3 else VIOLET,True)
            self.label(card,kitchen.name,21,INK,True)
            self.label(card,descriptions[index] if index < 3 else f'{kitchen.cuisine} · ready in about {kitchen.prep} min · near {PLACES[kitchen.place]}',13,MUTED)
            self.label(card,'€2.50 delivery · simulated order',11,MUTED)
            self.button(card,'View menu >','restaurant_'+str(index),lambda i=index:self.open_menu(i),False)
        self.button(self.body,f'Basket ({self.store.cart.count()})','food_cart',lambda:self.go('cart'))

    def open_menu(self, restaurant):
        self.restaurant = restaurant
        self.go('menu')

    def menu(self):
        if self.restaurant not in self.store.catalog.kitchens:
            self.restaurant = 0
        self.title_block('The menu',self.store.catalog.name(self.restaurant),'Choose your favourites. Add up to ten of each item.')
        for dish in self.store.catalog.menu(self.restaurant):
            card = self.box(self.body)
            self.label(card,dish.name,21,INK,True)
            self.label(card,dish.detail,13,MUTED)
            self.label(card,money(dish.price),22,GREEN,True)
            self.button(card,'Add to basket +','add_'+dish.id,lambda item=dish.id:self.add_food(item),False)
        self.button(self.body,f'View basket · {self.store.cart.count()} items','menu_cart',lambda:self.go('cart'))
        self.button(self.body,'All restaurants','menu_back',lambda:self.go('food'),False)

    def add_food(self, item):
        self.store.update_cart('add',item)
        self.render()

    def remove_food(self, item):
        self.store.update_cart('remove',item)
        self.render()

    def clear_cart(self):
        self.store.update_cart('clear')
        self.render()

    def cart(self):
        self.title_block('Your basket','A good choice.','Simulated checkout · no payment information required')
        if not self.store.cart.items:
            self.label(self.body,'Your basket is empty. Find something you love.',16,MUTED)
            self.button(self.body,'Browse food','empty_food',lambda:self.go('food'))
            return
        card = self.box(self.body)
        rid = self.store.cart.restaurant
        self.label(card,self.store.catalog.name(rid),20,INK,True)
        for item, quantity in self.store.cart.items.items():
            dish = self.store.catalog.dishes[item]
            self.label(card,f'{quantity} × {dish.name}   {money(dish.price*quantity)}',16,INK,True)
            self.button(card,'Remove one '+dish.name,'remove_'+item,lambda item=item:self.remove_food(item),False)
        self.label(card,'Food subtotal: '+money(self.store.cart.subtotal()),14,MUTED)
        self.label(card,'Delivery: €2.50',14,MUTED)
        self.label(card,'Total  '+money(self.store.cart.total()),28,GREEN,True)
        plan = ai.courier_plan(rid, prep=self.store.kitchen_prep(rid))
        timing = self.box(self.body,LILAC)
        self.label(timing,'COURIER TIMING · LEARNED',10,VIOLET,True)
        self.label(timing,ai.courier_text(plan),13,INK)
        self.select(self.body,'DELIVER TO',PLACES,self.address,'delivery_address',lambda v:self.update_selection('address',v))
        self.button(self.body,'Place order','checkout',self.checkout)
        self.button(self.body,'Clear basket','clear_cart',self.clear_cart,False)

    def checkout(self):
        restaurant = self.store.cart.restaurant
        plan = ai.courier_plan(restaurant, prep=self.store.kitchen_prep(restaurant)) if restaurant is not None else None
        self.store.checkout(self.address, plan)
        self.go('active_order')

    def active_order(self):
        order = self.store.order
        if not order:
            self.screen = 'activity'
            self.activity()
            return
        self.title_block('Order confirmed','Good food is coming.','Live map · simulated kitchen and courier')
        self.add_map(self.body, 210, fit=[tuple(order['live']['kitchen']), geo.PLACE_COORDS[order['address']]])
        self.live_label = self.label(self.body,self.live_text(),14,VIOLET,True)
        card = self.box(self.body,color('#E4EFCC'))
        stage = 'Waiting for the kitchen' if order.get('pending') else \
            ('Kitchen is preparing','Courier is on the way','Arriving at your door')[order['stage']]
        self.label(card,stage,25,GREEN,True)
        self.label(card,self.store.catalog.name(order['restaurant']),20,INK,True)
        self.label(card,'Deliver to '+PLACES[order['address']],14,MUTED)
        self.label(card,money(order['fare']),30,INK,True)
        for item,quantity in order['items'].items():
            self.label(card,f'{quantity} × {self.store.catalog.dishes[item].name}',15,INK)
        self.label(card,'Reference '+order['id'],10,MUTED)
        if order.get('courier'):
            timing = self.box(self.body,LILAC)
            self.label(timing,'COURIER TIMING · LEARNED',10,VIOLET,True)
            self.label(timing,ai.courier_text(order['courier']),13,INK)
        seller_kitchen = order['restaurant'] >= 3
        if seller_kitchen and (order.get('pending') or order['stage'] == 0):
            self.label(self.body,'A local seller on this phone prepares this order. Sign in as the seller to accept it and mark it ready.',13,MUTED)
            self.button(self.body,'Switch account','order_switch',self.logout,False)
        else:
            self.label(self.body,'The order moves on its own. Skip ahead to jump to the next stage.',13,MUTED)
            self.button(self.body,'Mark order delivered' if order['stage']==2 else 'Skip to next stage','order_next',self.next_order)

    def next_order(self):
        self.store.advance_order()
        self.go('active_order' if self.store.order else 'activity')

    # ------------------------------------------------------------------ activity and profile
    def activity(self):
        role = self.store.role
        self.title_block('All in one place',{'driver':'Your trips','seller':'Your orders'}.get(role,'Your activity'),
                         'Saved on this device for the signed-in account.')
        if self.store.ride and role == 'passenger':
            self.button(self.body,'Active ride · view journey','activity_ride',lambda:self.go('active_ride'))
        if self.store.order and role == 'passenger':
            self.button(self.body,'Active food order · track','activity_order',lambda:self.go('active_order'))
        records = self.store.my_history()
        if not records:
            self.label(self.body,'Your story starts here.' + (' Try a ride or a food order.' if role == 'passenger' else ''),16,MUTED)
        for record in reversed(records):
            is_food = 'restaurant' in record
            card = self.box(self.body)
            self.label(card,'Food · '+self.store.catalog.name(record['restaurant']) if is_food else 'Shared ride' if record['shared'] else 'ATLAS ride',19,INK,True)
            self.label(card,record['status']+' · '+money(record['fare']),17,GREEN,True)
            route = 'To '+PLACES[record['address']] if is_food else PLACES[record['pickup']]+' > '+PLACES[record['destination']]
            self.label(card,route,13,MUTED)
            self.label(card,record['id'],10,MUTED)

    def profile(self):
        user = self.store.user
        self.title_block('Your space',f"Hello, {user['name'].split()[0]}." if user else 'Hello, explorer.',
                         f'ATLAS Go · v{__version__}')
        card = self.box(self.body)
        if user:
            self.label(card,acc.ROLE_TITLES[user['role']].upper()+' ACCOUNT',11,GREEN,True)
            self.label(card,user['name'],25,INK,True)
            self.label(card,user['email'],14,MUTED)
            phone = user['phone']
            self.label(card,phone[:4]+'•'*max(0,len(phone)-8)+phone[-4:],14,MUTED)
            self.label(card,'Member since '+dt.date.fromtimestamp(user['created']).strftime('%d %b %Y'),12,MUTED)
            self.button(self.body,'Sign out','logout',self.logout,False)
        else:
            self.label(card,'GUEST PASSENGER',11,GREEN,True)
            self.label(card,'Cork, Ireland · EUR',14,MUTED)
            self.label(card,'Create an account to save your trips under your name, or to drive or sell food.',15,MUTED)
            self.button(self.body,'Create an account','profile_register',lambda:(self.store.logout(),self.go('register')))
            self.button(self.body,'Sign in','profile_login',lambda:(self.store.logout(),self.go('login')),False)
        self.button(self.body,'How ATLAS learns','profile_learn',lambda:self.go('intelligence'),False)
        self.button(self.body,'Privacy & how this app works','privacy',lambda:self.go('privacy'),False)
        if user:
            self.button(self.body,'Delete my account','delete_account',lambda:self.message('Delete your account?',
                        'Enter your password. Your profile is removed from this phone; past trips stay anonymised.',
                        self.delete_account,password=True),False)
        self.button(self.body,'Erase all data on this phone','reset',lambda:self.message('Erase everything?','Delete all accounts, rides, orders, kitchens and the basket on this phone.',self.reset),False)
        self.label(self.body,'Project help: github.com/FUllSCIPTS/ATLAS/issues\nATLAS Go does not provide emergency transport or live customer support.',13,MUTED)

    def reset(self):
        self.gps.stop()
        self.store.reset()
        self.pickup,self.destination,self.party,self.restaurant,self.address,self.comfort = 0,1,1,0,0,False
        self.outlook_day, self.lab, self.models, self.form, self.reg_role = 0, None, None, {}, 'passenger'
        self.go('welcome')

    def privacy(self):
        self.title_block('Transparent by design','Your data. Your device.','Privacy notice · effective 7 November 2026')
        for heading,description in (
            ('Accounts stay on this phone','Your name, email, mobile number and role details are stored in private app storage. '
             'Passwords are never stored: only a salted PBKDF2-SHA256 hash. There is no server account, advertising or analytics.'),
            ('Location, only when you ask','Location is used only after you tap Me on the map, Pick up near my location or Use my phone '
             'location, and only after you allow it. It is used on this phone to show the blue dot, pick the nearest pickup point '
             'and position a signed-in driver for dispatch. It is not sent anywhere.'),
            ('Map tiles','The live map downloads map images from OpenStreetMap\'s tile servers, which receive your IP address and '
             'the map area being viewed, as any website would. Tiles are cached on this phone. Map data © OpenStreetMap contributors.'),
            ('Simulated service','Rides, deliveries and payments are simulated. Driver licences, vehicle registrations and food '
             'business numbers are checked for format only, not verified. No real driver, kitchen or courier is contacted.'),
            ('Delete whenever you like','You > Delete my account removes your profile. You > Erase all data removes everything. '
             'Clearing app storage or uninstalling also removes everything. Android backup is disabled.'),
            ('Learning, on this device only','Surge outlooks, driver choice, acceptance estimates and courier timing come from '
             'small models learned offline in a simulated city and bundled with the app. The learning lab retrains a sandbox copy '
             'on this phone and never changes how rides are dispatched.'),
            ('About this project','Maintainer: FUllSCIPTS / ATLAS on GitHub. Questions: github.com/FUllSCIPTS/ATLAS/issues. '
             'Do not post personal details publicly.')):
            card = self.box(self.body)
            self.label(card,heading,21,INK,True)
            self.label(card,description,15,MUTED)
        if not self.store.signed_in:
            self.button(self.body,'Back','privacy_back',lambda:self.go('welcome'),False)

    # ------------------------------------------------------------------ ATLAS intelligence
    def shift_outlook(self, days):
        self.outlook_day = max(-400, min(400, self.outlook_day + days))
        self.go('intelligence')

    def check_models(self):
        self.models = ai.self_test(self.today())
        self.render()

    def intelligence(self):
        today = self.today()
        self.title_block('ATLAS intelligence','How ATLAS learns',
                         'Learned in a simulated Cork · runs on this device · nothing is sent anywhere')
        models = self.box(self.body)
        self.label(models,'MODELS IN THIS APP',10,VIOLET,True)
        results = {name: (ok, detail) for name, ok, detail in (self.models or [])}
        for name, method in ai.MODELS:
            state = results.get(name)
            mark = '' if state is None else ('PASS · ' if state[0] else 'FAIL · ')
            self.label(models,mark+name,15,INK if state is None or state[0] else SURGE,True)
            self.label(models,state[1] if state else method,12,MUTED)
        self.button(models,'Check all models' if self.models is None else 'Check again','models_check',self.check_models,False)
        day = today + dt.timedelta(days=self.outlook_day)
        summary = ai.day_summary(day)
        card = self.box(self.body)
        self.label(card,'SURGE OUTLOOK',10,VIOLET,True)
        self.label(card,day.strftime('%a %d %b %Y') + (' · today' if day == today else ''),13,MUTED)
        self.label(card,summary['title'],21,INK,True)
        card.add_widget(OutlookChart(summary['hours'], now=dt.datetime.now().hour if day == today else None))
        self.label(card,'Bars: expected ride requests per hour. Orange: surge. Grey ticks: an ordinary '
                        + day.strftime('%A') + '. Violet: extra drivers the agent sends ahead.',11,MUTED)
        self.label(card,summary['text'],14,INK,True)
        self.label(card,summary['agent'],13,VIOLET)
        row = BoxLayout(size_hint_y=None,height=dp(48),spacing=dp(8))
        card.add_widget(row)
        self.button(row,'< Previous day','outlook_prev',lambda:self.shift_outlook(-1),False)
        self.button(row,'Next day >','outlook_next',lambda:self.shift_outlook(1),False)
        if self.outlook_day:
            self.button(card,'Back to today','outlook_today',lambda:self.shift_outlook(-self.outlook_day),False)

        coming = self.box(self.body)
        self.label(coming,'COMING UP · IRISH HOLIDAYS & CORK EVENTS',10,VIOLET,True)
        for event in ai.upcoming(today, limit=5):
            self.label(coming,event['date'].strftime('%a %d %b') + ' · ' + event['title'],15,INK,True)
            self.label(coming,event['text'],12,MUTED)
        self.label(coming,'Public-holiday dates are computed for any year. Matches and storms are not on the '
                          'calendar; in the reference design the live forecaster picks them up.',11,MUTED)

        policy = self.box(self.body)
        self.label(policy,f'WHO GETS YOUR RIDE · POLICY {learned.POLICY_VERSION}',10,VIOLET,True)
        self.label(policy,f'Trained over {learned.TRAINING_EPISODES:,} simulated rides. Reward arrives late: '
                          'pickup time, cancellations and the shortage a choice causes elsewhere.',13,MUTED)
        names = {2: 'Keep the last car in an area about to surge', 0: 'A closer driver',
                 1: 'A driver who will accept', 3: 'Avoid busy areas in general'}
        top = max(learned.RIDE_WEIGHTS)
        for index in (2, 0, 1, 3):
            self.label(policy,names[index],13,INK)
            policy.add_widget(Bar(learned.RIDE_WEIGHTS[index] / top))

        timing = self.box(self.body)
        self.label(timing,'WHEN TO SEND THE COURIER',10,VIOLET,True)
        for kitchen in self.store.catalog.listed():
            plan = ai.courier_plan(kitchen.id, prep=kitchen.prep)
            self.label(timing,kitchen.name,15,INK,True)
            self.label(timing,f"Ready in ~{plan['prep']} min · send courier after {plan['dispatch_after']} min · "
                              f"counter wait {plan['courier_wait']} min (not {plan['naive_wait']})",12,MUTED)

        lab = self.box(self.body,LILAC)
        self.label(lab,'LEARNING LAB · SANDBOX',10,VIOLET,True)
        self.label(lab,'Watch a new dispatch policy learn from zero on this phone.',17,INK,True)
        self.lab_curve = LearningCurve()
        lab.add_widget(self.lab_curve)
        self.lab_status = self.label(lab,'',13,INK)
        self.label(lab,'Green: the new policy. Grey dashes: "send the nearest driver". Violet dots: approved '
                       f'policy {learned.POLICY_VERSION}. Higher means less waiting.',11,MUTED)
        self.button(lab,'Train 30,000 simulated rides','lab_train',self.lab_train)
        self.label(lab,'Sandbox only: this candidate is never used to dispatch rides. In the reference design a '
                       'policy is replayed, shadow-tested and approved on the server before dispatch loads it.',11,MUTED)
        self.lab_refresh()

    def lab_refresh(self):
        if self.lab is None:
            self.lab_status.text = 'Not trained yet. Training takes a few seconds.'
            self.lab_curve.update([], None, None)
            return
        result = self.lab.result()
        self.lab_curve.update(self.lab.curve, result['nearest'], result['approved'])
        if self.lab.done:
            self.lab_status.text = (f"Done: {result['episodes']:,} rides. Waiting cost per ride "
                                    f"{result['candidate']:.1f} min, vs {result['nearest']:.1f} for the nearest-driver "
                                    f"rule and {result['approved']:.1f} for approved {learned.POLICY_VERSION}.")
            if 'lab_train' in self.controls:
                self.controls['lab_train'].text = 'Train again from zero'
        else:
            self.lab_status.text = f"Training… {result['episodes']:,} rides · behaviour cost {result['behaviour']:.1f} min"

    def lab_train(self):
        if getattr(self, '_lab_event', None):
            return
        if self.lab is None:
            self.lab = ai.LearningLab()
        elif self.lab.done:
            self.lab.reset()
        self._lab_event = Clock.schedule_interval(self.lab_step, 0)

    def lab_step(self, _dt):
        self.lab.train(1500)
        if self.screen == 'intelligence':
            self.lab_refresh()
        if self.lab.done:
            self._lab_event = None
            return False
