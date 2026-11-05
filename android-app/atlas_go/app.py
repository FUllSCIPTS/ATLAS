"""Python/Kivy screens for the ATLAS Go offline passenger model."""
import datetime as dt
import math
import os
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
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex as color, platform
from .domain import PLACES, RESTAURANTS, MENU, DISHES, distance, fare, money
from .store import LocalStore
from . import intelligence as ai
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
    """Original route illustration. No maps SDK or location collection."""
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
                Line(points=[nx, base_y, nx, y + h - dp(4)], width=dp(1), dash_length=dp(4), dash_offset=dp(3))
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
                Line(points=[x, py(self.nearest), x + w, py(self.nearest)], width=dp(1), dash_length=dp(5), dash_offset=dp(4))
                Color(*VIOLET)
                Line(points=[x, py(self.approved), x + w, py(self.approved)], width=dp(1), dash_length=dp(2), dash_offset=dp(3))
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
        Window.bind(on_keyboard=self.on_keyboard)
        data_dir = os.environ.get('ATLAS_DATA_DIR') or (self.user_data_dir if platform == 'android' else str(Path.home()/'.atlas-go'))
        path = Path(data_dir) / 'state.json'
        self.store = LocalStore(path)
        self.screen = self.store.ui.get('screen', 'home')
        self.pickup = self.store.ui.get('pickup', 0)
        self.destination = self.store.ui.get('destination', 1)
        self.party = self.store.ui.get('party', 1)
        self.comfort = self.store.ui.get('comfort', False)
        self.restaurant = self.store.ui.get('restaurant', 0)
        self.address = self.store.ui.get('address', 0)
        self.outlook_day = self.store.ui.get('outlook_day', 0)
        self.lab = None
        self.controls = {}
        self.container = BoxLayout(orientation='vertical')
        self.render()
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
        self.store.ui = {key: getattr(self, key) for key in ('screen','pickup','destination','party','comfort','restaurant','address','outlook_day')}
        self.store.save()

    def today(self):
        override = os.environ.get('ATLAS_TODAY')
        return dt.date.fromisoformat(override) if override else dt.date.today()

    def on_pause(self):
        self.save_ui()
        return True

    def on_stop(self):
        self.save_ui()

    def on_keyboard(self, _window, key, *_args):
        if key == 27 and self.screen != 'home':
            self.go('home')
            return True
        return False

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

    def safe(self, callback):
        try:
            callback()
        except (ValueError, OSError) as error:
            self.message('Check your selection', str(error))

    def message(self, title, description, confirm=None):
        content = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(12))
        label = Label(text=description, color=INK, halign='left')
        label.bind(size=lambda widget,value: setattr(widget,'text_size',value))
        content.add_widget(label)
        popup = Popup(title=title, content=content, size_hint=(.9,None), height=dp(260),
                      background='', background_color=WHITE, title_color=GREEN, separator_color=GREEN)
        def done():
            popup.dismiss()
            if confirm:
                confirm()
        self.button(content,'Confirm' if confirm else 'OK','dialog_confirm',done)
        if confirm:
            self.button(content,'Keep current data','dialog_cancel',popup.dismiss,False)
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

    def render(self):
        self.controls = {}
        self.container.clear_widgets()
        header = BoxLayout(size_hint_y=None,height=dp(58),padding=(dp(21),dp(5)),spacing=dp(8))
        self.label(header,'ATLAS Go',23,GREEN,True)
        badge = Label(text='LOCAL DEMO',size_hint_x=None,width=dp(90),font_size=sp(10),bold=True,color=GREEN)
        header.add_widget(badge)
        self.container.add_widget(header)
        self.scroll = ScrollView(do_scroll_x=False,bar_width=dp(3))
        self.body = BoxLayout(orientation='vertical',size_hint_y=None,padding=(dp(21),dp(12),dp(21),dp(24)),spacing=dp(12))
        self.body.bind(minimum_height=self.body.setter('height'))
        self.scroll.add_widget(self.body)
        self.container.add_widget(self.scroll)
        screens = {'home':self.home,'ride':lambda:self.ride(False),'share':lambda:self.ride(True),
                   'food':self.food,'menu':self.menu,'cart':self.cart,'active_ride':self.active_ride,
                   'active_order':self.active_order,'activity':self.activity,'profile':self.profile,'privacy':self.privacy,
                   'intelligence':self.intelligence}
        screens.get(self.screen,self.home)()
        nav = BoxLayout(size_hint_y=None,height=dp(62),padding=dp(7),spacing=dp(4))
        for key, name in (('home','Home'),('share','Share'),('food','Food'),('activity','Activity'),('profile','You')):
            button = self.button(nav,name,'nav_'+key,lambda key=key:self.go(key),False)
            button.size_hint_y = 1
            button.font_size = sp(11)
            button.padding = (0,0)
            button.bind(width=lambda widget,value:setattr(widget,'text_size',(value-dp(4),None)))
            button.background_color = LIME if self.screen == key else WHITE
        self.container.add_widget(nav)

    def home(self):
        self.title_block('Cork, Ireland','Your city. One app.','Go somewhere good. Bring someone along.')
        hero = self.box(self.body,GREEN)
        self.label(hero,'MOVE TOGETHER',10,LIME,True)
        self.label(hero,'A little less driving.\nA lot more living.',25,WHITE,True)
        self.label(hero,'Rides, shared journeys and local food.',13,WHITE)
        hero.add_widget(RouteMap())
        quick = BoxLayout(size_hint_y=None,height=dp(54),spacing=dp(8))
        self.body.add_widget(quick)
        for name, key in (('Ride','ride'),('Share ride','share'),('Food','food')):
            self.button(quick,name,'home_'+key,lambda key=key:self.go(key),key=='ride',54)
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
        self.label(share,'Choose a route, check seats and join a demo carpool.',13,MUTED)
        self.button(share,'Find a shared ride >','home_pool',lambda:self.go('share'),False)
        food = self.box(self.body)
        self.label(food,'Something delicious is nearby.',19,INK,True)
        self.label(food,'Bowls, pizza and comfort food · demo menus',13,MUTED)
        self.button(food,'Explore food >','home_eat',lambda:self.go('food'),False)
        if self.store.ride:
            self.button(self.body,'View active ride','home_active_ride',lambda:self.go('active_ride'))
        if self.store.order:
            self.button(self.body,'Track food order','home_active_order',lambda:self.go('active_order'))
        self.label(self.body,'Interactive model · No real rides, deliveries or charges.',12,MUTED)

    def select(self, parent, title, values, value, key, callback):
        self.label(parent,title,11,MUTED,True)
        spinner = Spinner(text=values[value],values=values,size_hint_y=None,height=dp(48),
                          background_normal='',background_color=PALE,color=INK,font_size=sp(14))
        spinner.bind(text=lambda _widget, text:callback(values.index(text)))
        self.controls[key] = spinner
        parent.add_widget(spinner)

    def update_selection(self, field, value):
        setattr(self,field,value)
        self.save_ui()
        Clock.schedule_once(lambda _dt:self.render(),0)

    def ride(self, shared=False):
        self.title_block('More company. Less cost.' if shared else "Let's get moving",
                         'Share the journey' if shared else 'Where are we going?',
                         'Demo carpools · same route · available seats' if shared else 'Book a simulated ride between saved places.')
        route = self.box(self.body)
        self.select(route,'PICKUP',PLACES,self.pickup,'pickup',lambda v:self.update_selection('pickup',v))
        self.select(route,'DESTINATION',PLACES,self.destination,'destination',lambda v:self.update_selection('destination',v))
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
            self.label(preview,f'Demo pickup in 4 min · {distance(self.pickup,self.destination)} km illustrative route',12,MUTED)
            self.label(preview,money(fare(self.pickup,self.destination,self.comfort)),31,GREEN,True)
            self.label(preview,'Estimated total · demo payment only',12,MUTED)
            self.button(preview,'Book demo ride','book_ride',self.book_solo)
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
                self.label(card,'Try UCC Campus > Cork City Centre with one or two seats. These offers are seeded demo data.',14,MUTED)

    def dispatch_card(self):
        chosen, why = ai.choose(self.pickup)
        card = self.box(self.body,LILAC)
        self.label(card,f'ATLAS PICKS YOUR DRIVER · POLICY {learned.POLICY_VERSION}',10,VIOLET,True)
        for candidate, probability in ai.rank(self.pickup):
            mark = '>' if candidate == chosen else ' '
            self.label(card,f'{mark} {candidate.name} · {candidate.zone}',15,INK,candidate == chosen)
            self.label(card,f'{candidate.eta} min away · {round(candidate.accept*100)}% likely to accept · '
                            f'area surge {round(candidate.surge*100)}%' + (' · last free car' if candidate.last else ''),11,MUTED)
        self.label(card,why,13,INK)
        self.label(card,'Learned by reinforcement learning in a simulated city. Illustrative drivers.',11,MUTED)

    def book_solo(self):
        chosen, why = ai.choose(self.pickup)
        self.store.book(self.pickup,self.destination,self.comfort,driver=f'{chosen.name} · ATLAS demo driver',why=why)
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
        self.title_block('Booking confirmed',"You're sharing this ride" if ride['shared'] else 'Your ride is booked','Simulation · no real driver has been contacted')
        self.body.add_widget(RouteMap())
        card = self.box(self.body)
        self.label(card,('Driver confirmed','Driver at pickup','On your way')[ride['stage']],23,GREEN,True)
        self.label(card,ride['driver'],17,INK,True)
        self.label(card,f"{PLACES[ride['pickup']]} > {PLACES[ride['destination']]}",14,MUTED)
        self.label(card,f"{money(ride['fare'])} · {ride['party']} seat(s)",25,INK,True)
        self.label(card,'Reference '+ride['id'],10,MUTED)
        if ride.get('why'):
            why = self.box(self.body,LILAC)
            self.label(why,'WHY THIS DRIVER',10,VIOLET,True)
            self.label(why,ride['why'],13,INK)
        self.label(self.body,'Use the button below to advance the simulated journey.',13,MUTED)
        self.button(self.body,'Complete demo ride' if ride['stage']==2 else 'Simulate next stage','ride_next',self.next_ride)
        self.button(self.body,'Cancel demo ride','ride_cancel',lambda:self.message('Cancel this ride?','Your reserved shared seats will be released.',self.cancel_ride),False)

    def next_ride(self):
        self.store.advance_ride()
        self.go('active_ride' if self.store.ride else 'activity')

    def cancel_ride(self):
        self.store.advance_ride(cancel=True)
        self.go('activity')

    def food(self):
        self.title_block('Good food. Close by.','What are you craving?','Illustrative Cork kitchens · all orders are simulated')
        descriptions = ('Fresh bowls & wraps · 20–30 min','Stone-baked favourites · 25–35 min','Indian comfort food · 25–40 min')
        marks = ('FRESH & COLOURFUL','SLICE OF HAPPINESS','WARM & SPICED')
        fills = ('#E4EFCC','#F6E4C8','#F0DECF')
        for index,name in enumerate(RESTAURANTS):
            card = self.box(self.body)
            banner = self.box(card,color(fills[index]),20)
            self.label(banner,marks[index],17,GREEN,True)
            self.label(card,name,21,INK,True)
            self.label(card,descriptions[index],13,MUTED)
            self.label(card,'€2.50 demo delivery · no real restaurant orders',11,MUTED)
            self.button(card,'View menu >','restaurant_'+str(index),lambda i=index:self.open_menu(i),False)
        self.button(self.body,f'Basket ({self.store.cart.count()})','food_cart',lambda:self.go('cart'))

    def open_menu(self, restaurant):
        self.restaurant = restaurant
        self.go('menu')

    def menu(self):
        self.title_block('The menu',RESTAURANTS[self.restaurant],'Choose your favourites. Add up to ten of each item.')
        for dish in MENU:
            if dish.restaurant != self.restaurant:
                continue
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
        self.title_block('Your basket','A good choice.','Demo checkout · no payment information required')
        if not self.store.cart.items:
            self.label(self.body,'Your basket is empty. Find something you love.',16,MUTED)
            self.button(self.body,'Browse food','empty_food',lambda:self.go('food'))
            return
        card = self.box(self.body)
        self.label(card,RESTAURANTS[self.store.cart.restaurant],20,INK,True)
        for item, quantity in self.store.cart.items.items():
            dish = DISHES[item]
            self.label(card,f'{quantity} × {dish.name}   {money(dish.price*quantity)}',16,INK,True)
            self.button(card,'Remove one '+dish.name,'remove_'+item,lambda item=item:self.remove_food(item),False)
        self.label(card,'Food subtotal: '+money(self.store.cart.subtotal()),14,MUTED)
        self.label(card,'Demo delivery: €2.50',14,MUTED)
        self.label(card,'Total  '+money(self.store.cart.total()),28,GREEN,True)
        plan = ai.courier_plan(self.store.cart.restaurant)
        timing = self.box(self.body,LILAC)
        self.label(timing,'COURIER TIMING · LEARNED',10,VIOLET,True)
        self.label(timing,ai.courier_text(plan),13,INK)
        self.select(self.body,'DELIVER TO',PLACES,self.address,'delivery_address',lambda v:self.update_selection('address',v))
        self.button(self.body,'Place demo order','checkout',self.checkout)
        self.button(self.body,'Clear basket','clear_cart',self.clear_cart,False)

    def checkout(self):
        restaurant = self.store.cart.restaurant
        self.store.checkout(self.address, ai.courier_plan(restaurant) if restaurant is not None else None)
        self.go('active_order')

    def active_order(self):
        order = self.store.order
        if not order:
            self.screen = 'activity'
            self.activity()
            return
        self.title_block('Order confirmed','Good food is coming.','Simulation · no kitchen or courier has been contacted')
        card = self.box(self.body,color('#E4EFCC'))
        self.label(card,('Kitchen is preparing','Courier is on the way','Arriving at your door')[order['stage']],25,GREEN,True)
        self.label(card,RESTAURANTS[order['restaurant']],20,INK,True)
        self.label(card,'Deliver to '+PLACES[order['address']],14,MUTED)
        self.label(card,money(order['fare']),30,INK,True)
        for item,quantity in order['items'].items():
            self.label(card,f'{quantity} × {DISHES[item].name}',15,INK)
        self.label(card,'Reference '+order['id'],10,MUTED)
        if order.get('courier'):
            timing = self.box(self.body,LILAC)
            self.label(timing,'COURIER TIMING · LEARNED',10,VIOLET,True)
            self.label(timing,ai.courier_text(order['courier']),13,INK)
        self.button(self.body,'Mark demo order delivered' if order['stage']==2 else 'Simulate next stage','order_next',self.next_order)

    def next_order(self):
        self.store.advance_order()
        self.go('active_order' if self.store.order else 'activity')

    def activity(self):
        self.title_block('All in one place','Your activity','Demo journeys and orders are saved on this device.')
        if self.store.ride:
            self.button(self.body,'Active ride · view journey','activity_ride',lambda:self.go('active_ride'))
        if self.store.order:
            self.button(self.body,'Active food order · track','activity_order',lambda:self.go('active_order'))
        if not self.store.history:
            self.label(self.body,'Your story starts here. Try a demo ride or food order.',16,MUTED)
        for record in reversed(self.store.history):
            is_food = 'restaurant' in record
            card = self.box(self.body)
            self.label(card,'Food · '+RESTAURANTS[record['restaurant']] if is_food else 'Shared ride' if record['shared'] else 'ATLAS ride',19,INK,True)
            self.label(card,record['status']+' · '+money(record['fare']),17,GREEN,True)
            route = 'To '+PLACES[record['address']] if is_food else PLACES[record['pickup']]+' > '+PLACES[record['destination']]
            self.label(card,route,13,MUTED)
            self.label(card,record['id'],10,MUTED)

    def profile(self):
        self.title_block('Your space','Hello, explorer.',f'ATLAS Go · Python model application · v{__version__}')
        card = self.box(self.body)
        self.label(card,'DEMO PROFILE',11,GREEN,True)
        self.label(card,'Guest passenger',25,INK,True)
        self.label(card,'Cork, Ireland · EUR',14,MUTED)
        self.label(card,'No account or login needed. Your activity stays on this device.',15,MUTED)
        self.button(self.body,'How ATLAS learns','profile_learn',lambda:self.go('intelligence'),False)
        self.button(self.body,'Privacy & how this demo works','privacy',lambda:self.go('privacy'),False)
        self.button(self.body,'Reset all demo data','reset',lambda:self.message('Reset demo data?','Delete rides, food orders and basket. Restore demo seat availability.',self.reset),False)
        self.label(self.body,'Project help: github.com/FUllSCIPTS/ATLAS/issues\nThis demo does not provide emergency transport or live customer support.',13,MUTED)

    def reset(self):
        self.store.reset()
        self.pickup,self.destination,self.party,self.restaurant,self.address,self.comfort = 0,1,1,0,0,False
        self.outlook_day, self.lab = 0, None
        self.go('home')

    def privacy(self):
        self.title_block('Transparent by design','Your demo. Your device.','Privacy notice · effective 5 November 2026')
        for heading,description in (
            ('Local data only','Simulated rides, food orders, basket items and shared-seat availability stay in private app storage. No app data is transmitted. No ads, analytics, accounts, payments or location access are included.'),
            ('Delete whenever you like','Use You > Reset all demo data, clear app storage in Android Settings, or uninstall. Android backup is disabled. Drivers, restaurants and distances are illustrative.'),
            ('Learning, on this device only','Surge outlooks, driver choice and courier timing come from small policies learned offline in a simulated city and bundled with the app. The learning lab retrains a sandbox copy on this phone; it never changes how demo rides are dispatched and sends nothing anywhere.'),
            ('About this project','Maintainer: FUllSCIPTS / ATLAS on GitHub. Questions: github.com/FUllSCIPTS/ATLAS/issues. Do not post personal details publicly. ATLAS Go is an educational model, separate from real transport and food services.')):
            card = self.box(self.body)
            self.label(card,heading,21,INK,True)
            self.label(card,description,15,MUTED)

    # ------------------------------------------------------------------ ATLAS intelligence
    def shift_outlook(self, days):
        self.outlook_day = max(-400, min(400, self.outlook_day + days))
        self.go('intelligence')

    def intelligence(self):
        today = self.today()
        self.title_block('ATLAS intelligence','How ATLAS learns',
                         'Learned in a simulated Cork · runs on this device · nothing is sent anywhere')
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
        for index, name in enumerate(RESTAURANTS):
            plan = ai.courier_plan(index)
            self.label(timing,name,15,INK,True)
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
