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
from . import twin as layer2
from . import loop as live
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
CYAN = color('#0E7A8C')
ICE = color('#DFF3F6')
AMBER = color('#FFF4DC')
ROSE = color('#FDECEF')
RED = color('#C8324E')


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
        self.loop = live.Loop(self.data_dir / 'loop.json')     # Layer 1 live loop: LSTM -> RL -> outcomes -> update
        self._loop_view = None
        self.loop_checks = None
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

    def now_dt(self):
        """City clock. Acceptance runs pin it (clock_override) so prices and forecasts are repeatable;
        ATLAS_CLOCK=2027-03-17T13:00 does the same for a desktop preview."""
        if getattr(self, 'clock_override', None) is not None:
            return self.clock_override
        override = os.environ.get('ATLAS_CLOCK')
        return dt.datetime.fromisoformat(override) if override else dt.datetime.now()

    def today(self):
        override = os.environ.get('ATLAS_TODAY')
        if override and getattr(self, 'clock_override', None) is None:
            return dt.date.fromisoformat(override)
        return self.now_dt().date()

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
            return (('driver','Drive'),('map','Map'),('activity','Trips'),('twin','Twin'),('profile','You'))
        if role == 'seller':
            return (('seller','Kitchen'),('seller_menu','Menu'),('activity','Orders'),('twin','Twin'),('profile','You'))
        return (('home','Home'),('map','Map'),('food','Food'),('activity','Activity'),('twin','Twin'),('profile','You'))

    def render(self):
        self.controls = {}
        self.shown = {}
        if self.live_map is not None:
            self.live_map.detach()
        self.live_map, self.live_label = None, None
        self.container.clear_widgets()
        if not self.store.signed_in and self.screen not in ('welcome','login','register','privacy'):
            self.screen = 'welcome'
        allowed = {'driver': ('driver','map','activity','profile','privacy','intelligence','account','twin'),
                   'seller': ('seller','seller_menu','activity','profile','privacy','intelligence','account','twin')}
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
                   'seller':self.seller,'seller_menu':self.seller_menu,'account':self.profile,'twin':self.twin_screen}
        screens.get(self.screen,self.home)()
        items = self.nav_items()
        if items:
            nav = BoxLayout(size_hint_y=None,height=dp(62),padding=dp(7),spacing=dp(4))
            for key, name in items:
                button = self.button(nav,name,'nav_'+key,lambda key=key:self.go(key),False)
                button.size_hint_y = 1
                button.font_size = sp(11 if len(items) < 6 else 10)
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
        if changed and self.screen in ('active_ride','active_order','driver','seller','map','home','activity','twin'):
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
        if self.screen in ('map','twin'):
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
        if screen in ('map','twin'):
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
        if ride and screen in ('map','active_ride','driver','twin'):
            car, _ = geo.ride_position(ride, now)
            start, pickup, dest = geo.ride_legs(ride)
            if screen not in ('map','twin'):
                markers += [dict(kind='home', point=pickup, label='Pickup · '+PLACES[ride['pickup']]),
                            dict(kind='place', point=dest, label=PLACES[ride['destination']])]
            if geo.has_co_rider(ride):
                drop = geo.co_drop_point(ride)
                co = ride['co']
                markers.append(dict(kind='rider', point=drop,
                                    label=co['name']+(' dropped' if co['dropped'] else ' gets out')+' · '+co['drop']))
                routes.append(([pickup, drop, dest], '#075E4A', False))
            else:
                routes.append(([pickup, dest], '#075E4A', False))
            if ride['stage'] == 0:
                routes.append(([car, pickup], '#6E56CF', True))
            markers.append(dict(kind='ride', point=car, label=ride['driver'].split(' · ')[0]))
        if order and screen in ('map','active_order','twin'):
            pos, _ = geo.order_position(order, now, self.store.kitchen_prep(order['restaurant']))
            kitchen = tuple(order['live']['kitchen'])
            home = geo.PLACE_COORDS[order['address']]
            if screen not in ('map','twin'):
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
        twin_box = self.box(self.body,ICE)
        self.label(twin_box,'NEW IN 1.3 · CITY TWIN',10,CYAN,True)
        self.label(twin_box,'Every ride is rehearsed before it is sent.',17,INK,True)
        self.label(twin_box,'A digital twin of Cork plays the next 30 minutes; three agents work on top of '
                            'the learned models and a Guardian checks every decision.',13,MUTED)
        self.button(twin_box,'Open the Twin tab >','home_twin',lambda:self.go('twin'),False)
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
            decision = self.decide(self.pickup)
            chosen = decision['choice']
            base = fare(self.pickup,self.destination,self.comfort)
            price = self.store_price(base, decision['multiplier'])
            self.label(preview,f'Pickup in about {chosen.eta} min · {distance(self.pickup,self.destination)} km route',12,MUTED)
            self.label(preview,money(price),31,GREEN,True)
            surge = self.live_surge()
            self.label(preview,'Estimated total · simulated payment' + (f' · busy period ({round(surge*100)}% surge forecast)' if surge >= .2 else ''),12,MUTED)
            self.button(preview,'Book ride','book_ride',self.book_solo)
            self.price_card(decision, base)
            self.twin_card(decision)
            self.dispatch_card()
        else:
            found = [o for o in self.store.offers if o.matches(self.pickup,self.destination,self.party)]
            for offer in found:
                card = self.box(self.body)
                self.label(card,offer.driver,17,INK,True)
                self.label(card,f'On the road now · {offer.seats} seats free',12,MUTED)
                if offer.co_rider:
                    order = self.box(card,LILAC,12)
                    self.label(order,'WHO GETS OUT FIRST',10,VIOLET,True)
                    self.label(order,f'{offer.co_rider} is already in the car (picked up at {offer.co_from}). '
                                     f'The driver picks you up next, drops {offer.co_rider} at {offer.co_drop}, '
                                     f'then takes you to {PLACES[offer.destination]}.',12,INK)
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

    # ------------------------------------------------------------------ Layer 1 live loop
    def loop_now(self):
        """Advance the LSTM -> RL loop to the city clock and return this hour's forecast and decision."""
        now = self.now_dt()
        key = live.hour_index(now)
        if self._loop_view is None or self._loop_view[0] != key:
            try:
                if self.loop.advance_to(now):
                    self.loop.save()
                elif self.loop.state['cursor'] is not None and not self.loop.path.exists():
                    self.loop.save()
                self._loop_view = (key, self.loop.now(now))
            except (OSError, LookupError, ValueError, OverflowError):
                self._loop_view = (key, None)
        return self._loop_view[1]

    def live_surge(self):
        """Surge feature for dispatch (0-1) from the live LSTM forecast; the 1.2 outlook if the loop is unavailable."""
        view = self.loop_now()
        return view['surge'] if view else ai.surge_level(self.today(), self.now_dt().hour)

    def loop_week(self):
        now = self.now_dt()
        start = live.hour_index(now) - 7 * 24
        self.loop.warm_up(start)
        while self.loop.state['cursor'] < live.hour_index(now) - 1:
            self.loop.step()
        self.loop.save()
        self._loop_view = None
        self.render()

    def check_loop(self):
        self.loop_checks = live.self_test()
        self.render()

    def loop_card(self, parent=None):
        view = self.loop_now()
        card = self.box(parent or self.body,LILAC)
        self.label(card,'LIVE LOOP · LSTM > RL > OUTCOMES > UPDATE',10,VIOLET,True)
        if not view:
            self.label(card,'The live loop is starting.',13,MUTED)
            return card
        fc = view['forecast']
        self.label(card,f"Next hour: about {round(fc['requests'][0])} requests ({ai.ratio_text(view['ratio']) if view['ratio'] >= 1.005 else 'as usual'})",17,INK,True)
        self.label(card,'LSTM forecast, next 6 hours: '+' · '.join(f"{t.strftime('%H')}h {round(r)}" for t, r in zip(fc['hours'], fc['requests'])),12,MUTED)
        self.label(card,f"Supply agent adds {round(view['boost']*100)}% drivers this hour (state: calendar + LSTM level {fc['level']})",13,VIOLET,True)
        err = f" · forecast error last 24 h {view['mape_24h']*100:.0f}%" if view['mape_24h'] is not None else ''
        self.label(card,f"Models {view['lstm']} · {view['agent']} · {view['hours']} hours learned on this phone{err}",11,MUTED)
        self.shown['loop'] = view
        return card

    def registered_candidates(self, pickup):
        surge = self.live_surge()
        online = self.store.online_drivers()
        point = geo.PLACE_COORDS[pickup]
        return [ai.registered_candidate(a, self.store.driver_position(a), point, surge, len(online) == 1 and surge >= .5)
                for a in online]

    def layer2_on(self):
        return self.store.twin['enabled']

    def decide(self, pickup, exclude=()):
        """Layer 1 ranks drivers (unchanged since 1.2.0); Layer 2, when on, rehearses Layer 1's top three
        and the price in the twin, and the Guardian checks both. Falls back to Layer 1 otherwise."""
        return layer2.decide_ride(self.store, pickup, self.now_dt(), extra=self.registered_candidates(pickup),
                                  exclude=exclude, enabled=self.layer2_on())

    @staticmethod
    def store_price(base, multiplier):
        from .store import _priced
        return _priced(base, multiplier)

    def start_of(self, chosen):
        if chosen.account:
            return self.store.driver_position(self.store.account(chosen.account))
        return geo.zone_drift(chosen.zone, time.time())

    def pick_driver(self, pickup, exclude=()):
        decision = self.decide(pickup, exclude)
        return decision['choice'], decision['why'], self.start_of(decision['choice'])

    def price_card(self, decision, base):
        card = self.box(self.body,ICE)
        m = decision['multiplier']
        self.label(card,'PRICE CHECK · LAYER 2' if decision['layer'] == 2 else 'PRICE · LAYER 1',10,CYAN,True)
        if decision['layer'] == 2:
            self.label(card,f'×{m:.1f} here · checked by the Guardian',16,INK,True)
            plan = (decision['twin'] or {}).get('plan','')
            self.label(card,(f'Agent 2 rehearsed three price plans in the twin and chose: {plan.lower()}. ' if plan else '')
                       + f'Surges are capped at ×{layer2.PRICE_CAP:.1f}. Base fare {money(base)}.',12,MUTED)
        else:
            self.label(card,'Base fare · Layer 2 is switched off',16,INK,True)
            self.label(card,'Turn the twin layer on in the Twin tab to rehearse prices and drivers.',12,MUTED)

    def twin_card(self, decision):
        info = decision.get('twin') or {}
        if not info.get('rollouts'):
            return
        card = self.box(self.body,ICE)
        self.label(card,'AGENT 1 · REHEARSED IN THE CITY TWIN',10,CYAN,True)
        for name, wait in info['rollouts']:
            mark = '>' if name == decision['choice'].name else ' '
            self.label(card,f'{mark} {name} · {wait:.1f} min total wait, next {layer2.HORIZON_MIN} min',13,INK,name == decision['choice'].name)
        self.label(card,f"Layer 1 picked {info['layer1']}; Agent 1 sends {decision['choice'].name}.",12,MUTED)

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
        decision = self.decide(self.pickup)
        chosen = decision['choice']
        label = f'{chosen.name} · ' + ('registered driver' if chosen.account else 'ATLAS demo driver')
        twin = dict(decision['twin'], layer=2) if decision['twin'] else None
        self.store.book(self.pickup,self.destination,self.comfort,driver=label,why=decision['why'],
                        driver_id=chosen.account or None,start=self.start_of(chosen),
                        multiplier=decision['multiplier'],twin=twin,log=decision['log'])
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
        co = ride.get('co') if geo.has_co_rider(ride) else None
        if ride.get('pending'):
            title = 'Waiting for driver'
        elif co:
            title = (f"Please wait · {co['name']} is in the car",'Driver at your pickup',
                     f"Dropping {co['name']} first",'On your way')[ride['stage']]
        else:
            title = ('Driver on the way','Driver at pickup','On your way')[ride['stage']]
        self.label(card,title,23,GREEN,True)
        self.label(card,ride['driver'],17,INK,True)
        self.label(card,f"{PLACES[ride['pickup']]} > {PLACES[ride['destination']]}",14,MUTED)
        self.label(card,f"{money(ride['fare'])} · {ride['party']} seat(s)",25,INK,True)
        if ride.get('surge'):
            self.label(card,f"Includes ×{ride['surge']:.1f} busy-time price · checked by the Guardian",12,CYAN)
        self.label(card,'Reference '+ride['id'],10,MUTED)
        if co:
            self.shared_stops(ride, co)
        if ride.get('why'):
            twin = ride.get('twin') or {}
            why = self.box(self.body,LILAC)
            head = self.row(why,22)
            self.label(head,'WHY THIS DRIVER',10,VIOLET,True)
            if twin.get('rollouts'):
                self.label(head,'TWIN-TESTED',10,CYAN,True).halign = 'right'
            self.label(why,ride['why'],13,INK)
            if twin.get('reason'):
                self.label(why,twin['reason'],12,CYAN)
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
            last = geo.last_stage(ride)
            self.button(self.body,'Complete ride' if ride['stage']==last else 'Skip to next stage','ride_next',self.next_ride)
        self.button(self.body,'Cancel ride','ride_cancel',lambda:self.message('Cancel this ride?','Your reserved shared seats will be released.',self.cancel_ride),False)

    def shared_stops(self, ride, co):
        """The order of stops in a shared car: you board, the earlier rider gets out, then you do."""
        box = self.box(self.body,LILAC)
        self.label(box,'SHARED CAR · ORDER OF STOPS',10,VIOLET,True)
        stage = ride['stage']
        stops = ((f"{co['name']} is on board (picked up at {co['boarded']})", True),
                 (f"You board at {PLACES[ride['pickup']]}", stage >= 2),
                 (f"{co['name']} gets out at {co['drop']}", co['dropped']),
                 (f"You get out at {PLACES[ride['destination']]}", False))
        current = (1, 1, 2, 3)[stage]
        for i, (text, done) in enumerate(stops):
            mark = '[x]' if done else ('>' if i == current else '[  ]')
            self.label(box,f'{mark} {i+1}. {text}',13,INK if done or i == current else MUTED,i == current)
        if not co['dropped']:
            self.label(box,f"Your drop-off comes after {co['name']}'s. Please wait while the driver finishes "
                           f"that stop.",12,VIOLET)
        else:
            self.label(box,f"{co['name']} has been dropped. Next stop: you.",12,VIOLET)

    def redispatch(self):
        ride = self.store.ride
        exclude = [ride['driver_id']] + ride.get('declined', [])
        decision = self.decide(ride['pickup'], exclude=exclude)
        chosen, start = decision['choice'], self.start_of(decision['choice'])
        before = self.store.snapshot()
        ride.setdefault('declined', []).append(ride['driver_id'])
        ride.update(driver=f'{chosen.name} · ' + ('registered driver' if chosen.account else 'ATLAS demo driver'),
                    why=decision['why'], driver_id=chosen.account or None, pending=bool(chosen.account),
                    live=dict(start=[start[0], start[1]], t=time.time()))
        if decision['twin'] and decision['twin'].get('rollouts'):
            ride['twin'] = dict(ride.get('twin') or {}, **{k: v for k, v in decision['twin'].items() if k != 'multiplier'})
        self.store._log([e for e in decision['log'] if e['agent'] != 'Agent 2'])
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
        if self.layer2_on() and self.store.twin['status']['pricing'] == 'active':
            hint = layer2.driver_hint(d['base'], self.now_dt())
            box = self.box(self.body,AMBER)
            self.label(box,'TWIN HINT · AGENT 2 · '+self.now_dt().strftime('%H:%M'),10,SURGE,True)
            self.label(box,hint['text'],15,INK,True)
            self.label(box,'A suggestion, never an order: you can ignore it.',11,MUTED)
            self.button(box,'Show me on the map','twin_hint_map',lambda:self.go('map'),False)
            self.shown['driver_hint'] = hint
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
        view = self.loop_now()
        if view:
            self.label(smart,f"Live LSTM: about {round(view['forecast']['requests'][0])} requests next hour · "
                             f"the supply agent adds {round(view['boost']*100)}% drivers",13,VIOLET,True)

    def job_accept(self):
        self.store.driver_respond(True)
        self.render()

    def job_decline(self):
        job = self.store.driver_job()
        exclude = [self.store.user['id']] + job.get('declined', [])
        chosen, why, start = self.pick_driver(job['pickup'], exclude=exclude)
        self.store.twin_record([layer2.entry('Guardian', f'{chosen.name} offered after a decline', 'info')])
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
        if self.layer2_on():
            hint = self.box(self.body,AMBER)
            self.label(hint,'TWIN HINT · KITCHEN',10,SURGE,True)
            text = layer2.kitchen_hint(order['courier'] if order and order.get('courier') else plan)
            self.label(hint,text,14,INK,True)
            self.shown['kitchen_hint'] = text
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
            if not is_food and geo.has_co_rider(record):
                co = record['co']
                self.label(card,f"Shared with {co['name']} · {co['name']} got out at {co['drop']} first" if co['dropped']
                           else f"Shared with {co['name']}",12,VIOLET)
            if not is_food and (record.get('twin') or {}).get('rollouts'):
                self.label(card,'Twin-tested by Agent 1 · checked by the Guardian',12,CYAN)
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
        self.loop.reset()
        self._loop_view, self.loop_checks = None, None
        self.pickup,self.destination,self.party,self.restaurant,self.address,self.comfort = 0,1,1,0,0,False
        self.outlook_day, self.lab, self.models, self.form, self.reg_role = 0, None, None, {}, 'passenger'
        self.layer2_checks = None
        self.go('welcome')

    def privacy(self):
        self.title_block('Transparent by design','Your data. Your device.','Privacy notice · effective 14 November 2026')
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
            ('The city twin (Layer 2)','Version 1.3 adds a digital twin of Cork that runs on this phone. It mirrors the '
             'drivers, rides and couriers already in the app, plays the next 30 minutes with the learned surge outlook, '
             'and lets three agents rehearse the driver, the price and driver hints before you see them. A Guardian '
             'checks each decision and keeps a log on this phone. Nothing is sent anywhere. You can switch the twin off '
             'in the Twin tab; the app then works exactly as 1.2.0.'),
            ('About this project','Maintainer: FUllSCIPTS / ATLAS on GitHub. Questions: github.com/FUllSCIPTS/ATLAS/issues. '
             'Do not post personal details publicly.')):
            card = self.box(self.body)
            self.label(card,heading,21,INK,True)
            self.label(card,description,15,MUTED)
        if not self.store.signed_in:
            self.button(self.body,'Back','privacy_back',lambda:self.go('welcome'),False)

    # ------------------------------------------------------------------ Layer 2: the city twin
    def twin_screen(self):
        now_dt = self.now_dt()
        on = self.layer2_on()
        state = self.store.twin
        self.title_block('City twin · Layer 2', f'Cork, {layer2.HORIZON_MIN} minutes ahead',
                         f"City time {now_dt.strftime('%H:%M')} · rehearsing to "
                         f"{(now_dt + dt.timedelta(minutes=layer2.HORIZON_MIN)).strftime('%H:%M')} · runs on this phone")
        mirror = layer2.mirror(self.store, time.time())
        card = self.box(self.body,ICE)
        self.label(card,'MIRROR',10,CYAN,True)
        self.label(card,f"Twin fidelity {mirror['fidelity']:.2f} · {mirror['drivers']} drivers · "
                        f"{mirror['count']} things tracked",15,INK,True)
        self.add_map(card, 190, fit=[geo.PLACE_COORDS[i] for i in range(3)])
        self.live_label = self.label(card,self.live_text(),11,MUTED)
        self.shown['fidelity'] = mirror['fidelity']
        fore = self.box(self.body,ICE)
        self.label(fore,'FORESEE · NEXT 30 MINUTES (FROM LAYER 1’S OUTLOOK)',10,CYAN,True)
        for row in layer2.foresee(now_dt):
            plan = layer2.agent2(row['place'], now_dt)
            move = f" · move {plan['move']['cars']} cars from {PLACES[plan['move']['src']]}" if plan['move'] else ''
            self.label(fore,f"{row['name']} · demand {ai.ratio_text(row['ratio']) if row['ratio'] >= 1.005 else 'as usual'}",14,INK,True)
            self.label(fore,f"{row['free']} cars free · Agent 2: ×{plan['multiplier']:.1f}{move}",12,MUTED)
        layers = self.box(self.body)
        self.label(layers,'LAYER 1 · LEARNED MODELS + LIVE LOOP',10,VIOLET,True)
        for name, method in ai.MODELS:
            self.label(layers,name+' · running',13,INK,True)
        view = self.loop_now()
        if view:
            self.label(layers,f"Live LSTM {view['lstm']} > supply agent {view['agent']} · running",13,INK,True)
            self.label(layers,'Forecasts every hour, acts, records the outcome, retrains and validates nightly',11,MUTED)
        self.label(layers,'LAYER 2 · TWIN AGENTS',10,CYAN,True)
        for key, name, what in layer2.AGENTS:
            st = 'off' if not on else state['status'].get(key, 'watching' if key == 'guardian' else 'active')
            if key == 'guardian' and on:
                st = f"watching · {state['blocks']} blocked of {state['checks']} checked"
            self.label(layers,name+' · '+st,13,INK if on else MUTED,True)
            self.label(layers,what,11,MUTED)
        self.button(layers,'Turn Layer 2 off (Layer 1 only)' if on else 'Turn Layer 2 on','layer2_toggle',
                    self.toggle_layer2,not on)
        self.label(layers,'With Layer 2 off, ATLAS Go chooses drivers and prices exactly as version 1.2.0.',11,MUTED)
        guard = self.box(self.body)
        self.label(guard,'GUARDIAN LOG · EVERY DECISION, CHECKED',10,GREEN,True)
        log = state['log'][-8:]
        if not log:
            self.label(guard,'No decisions yet. Book a ride, or run the fault drill below.',13,MUTED)
        for item in reversed(log):
            shade = RED if item['result'] == 'blocked' else CYAN if item['result'] in ('fallback','retested') else GREEN
            when = dt.datetime.fromtimestamp(item['t']).strftime('%H:%M:%S')
            self.label(guard,f"{when} · {item['agent']} · {item['decision']}",13,INK,True)
            self.label(guard,item['result']+(' · '+item['detail'] if item.get('detail') else ''),12,shade,True)
        self.button(guard,'Run Guardian fault drill','twin_drill',self.fault_drill,False)
        self.label(guard,'The drill makes Agent 2 send a ×4.0 price in the twin. The Guardian should block it, '
                         'serve riders with Layer 1’s base price, re-test Agent 2 and hand control back.',11,MUTED)
        checks = self.box(self.body,LILAC)
        self.label(checks,'CHECK LAYER 2',10,VIOLET,True)
        for name, ok, detail in getattr(self, 'layer2_checks', None) or []:
            self.label(checks,('PASS · ' if ok else 'FAIL · ')+name,14,INK if ok else SURGE,True)
            self.label(checks,detail,12,MUTED)
        self.button(checks,'Check Layer 2' if not getattr(self,'layer2_checks',None) else 'Check again','twin_check',
                    self.check_layer2,False)

    def toggle_layer2(self):
        self.store.set_layer2(not self.layer2_on())
        self.render()

    def fault_drill(self):
        if not self.layer2_on():
            raise ValueError('Turn Layer 2 on to run the fault drill.')
        place = self.pickup
        self.store.twin_record([], status=dict(pricing='retesting'))
        entries = layer2.fault_drill(self.store, place, self.now_dt())
        handed = any(e['result'] == 'handed back' for e in entries)
        self.store.twin_record(entries, status=dict(pricing='active' if handed else 'retesting'))
        self.render()

    def check_layer2(self):
        self.layer2_checks = layer2.self_test(self.now_dt())
        self.render()

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
        loop_box = self.loop_card()
        self.label(loop_box,'Every city hour the LSTM forecasts demand from the last 24 hours of trips, unserved requests '
                            'and boosts; the supply agent acts on that forecast; the outcome is recorded. Each night both '
                            'models are retrained on this experience and kept only if they beat the current model on '
                            'held-out recent hours.',11,MUTED)
        for u in reversed(self.loop.state['updates'][-3:]):
            parts = []
            if u.get('lstm'):
                x = u['lstm']
                parts.append(f"LSTM {'kept new' if x['accepted'] else 'kept old'} ({x['before']:.3f} to {x['after']:.3f})")
            if u.get('agent'):
                x = u['agent']
                parts.append(f"agent {'improved' if x.get('improved') else 'kept'} ({x['champion']:.0f} vs {x['challenger']:.0f})")
            self.label(loop_box,u['t'][:10]+' · '+(' · '.join(parts) or 'collecting experience'),11,INK)
        for name, ok, detail in self.loop_checks or []:
            self.label(loop_box,('PASS · ' if ok else 'FAIL · ')+name,13,INK if ok else SURGE,True)
            self.label(loop_box,detail,11,MUTED)
        row = self.row(loop_box,48)
        self.button(row,'Run 7 city days','loop_week',self.loop_week,False)
        self.button(row,'Check the loop','loop_check',self.check_loop,False)
        day = today + dt.timedelta(days=self.outlook_day)
        summary = ai.day_summary(day)
        card = self.box(self.body)
        self.label(card,'SURGE OUTLOOK',10,VIOLET,True)
        self.label(card,day.strftime('%a %d %b %Y') + (' · today' if day == today else ''),13,MUTED)
        self.label(card,summary['title'],21,INK,True)
        card.add_widget(OutlookChart(summary['hours'], now=self.now_dt().hour if day == today else None))
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
