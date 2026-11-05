"""Python/Kivy screens for the ATLAS Go offline passenger model."""
import os
from pathlib import Path
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, Line, Ellipse
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

GREEN = color('#075E4A')
INK = color('#182D26')
MUTED = color('#5B6D64')
LIME = color('#DFFF73')
BG = color('#F6F7F2')
WHITE = color('#FFFFFF')
PALE = color('#E8F1E1')


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


class AtlasGoApp(App):
    title = 'ATLAS Go'

    def build(self):
        Window.clearcolor = BG
        if platform != 'android':
            Window.size = (440, 940)
        Window.bind(on_keyboard=self.on_keyboard)
        path = Path(os.environ.get('ATLAS_DATA_DIR', self.user_data_dir)) / 'state.json'
        self.store = LocalStore(path)
        self.screen = self.store.ui.get('screen', 'home')
        self.pickup = self.store.ui.get('pickup', 0)
        self.destination = self.store.ui.get('destination', 1)
        self.party = self.store.ui.get('party', 1)
        self.comfort = self.store.ui.get('comfort', False)
        self.restaurant = self.store.ui.get('restaurant', 0)
        self.address = self.store.ui.get('address', 0)
        self.controls = {}
        self.container = BoxLayout(orientation='vertical')
        self.render()
        return self.container

    def on_start(self):
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

    def save_ui(self):
        self.store.ui = {key: getattr(self, key) for key in ('screen','pickup','destination','party','comfort','restaurant','address')}
        self.store.save()

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
                   'active_order':self.active_order,'activity':self.activity,'profile':self.profile,'privacy':self.privacy}
        screens.get(self.screen,self.home)()
        nav = BoxLayout(size_hint_y=None,height=dp(62),padding=dp(7),spacing=dp(4))
        for key, name in (('home','Home'),('share','Share'),('food','Food'),('activity','Activity'),('profile','You')):
            button = self.button(nav,name,'nav_'+key,lambda key=key:self.go(key),False)
            button.size_hint_y = 1
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
        self.label(self.body,'Made for your everyday',20,INK,True)
        share = self.box(self.body,color('#E9F1DA'))
        self.label(share,'SHARED RIDES · FROM €4.90 / SEAT',10,GREEN,True)
        self.label(share,'Same direction? Share the journey.',19,INK,True)
        self.label(share,'Choose a route, check seats and join a demo carpool.',13,MUTED)
        self.button(share,'Find a shared ride →','home_pool',lambda:self.go('share'),False)
        food = self.box(self.body)
        self.label(food,'Something delicious is nearby.',19,INK,True)
        self.label(food,'Bowls, pizza and comfort food · demo menus',13,MUTED)
        self.button(food,'Explore food →','home_eat',lambda:self.go('food'),False)
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
                self.label(card,'Try UCC Campus → Cork City Centre with one or two seats. These offers are seeded demo data.',14,MUTED)

    def book_solo(self):
        self.store.book(self.pickup,self.destination,self.comfort)
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
        self.label(card,f"{PLACES[ride['pickup']]} → {PLACES[ride['destination']]}",14,MUTED)
        self.label(card,f"{money(ride['fare'])} · {ride['party']} seat(s)",25,INK,True)
        self.label(card,'Reference '+ride['id'],10,MUTED)
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
            self.button(card,'View menu →','restaurant_'+str(index),lambda i=index:self.open_menu(i),False)
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
        self.store.cart.add(item)
        self.store.save()
        self.render()

    def remove_food(self, item):
        self.store.cart.remove(item)
        self.store.save()
        self.render()

    def clear_cart(self):
        self.store.cart.clear()
        self.store.save()
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
        self.select(self.body,'DELIVER TO',PLACES,self.address,'delivery_address',lambda v:self.update_selection('address',v))
        self.button(self.body,'Place demo order','checkout',self.checkout)
        self.button(self.body,'Clear basket','clear_cart',self.clear_cart,False)

    def checkout(self):
        self.store.checkout(self.address)
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
            route = 'To '+PLACES[record['address']] if is_food else PLACES[record['pickup']]+' → '+PLACES[record['destination']]
            self.label(card,route,13,MUTED)
            self.label(card,record['id'],10,MUTED)

    def profile(self):
        self.title_block('Your space','Hello, explorer.','ATLAS Go · Python model application · v1.0.0')
        card = self.box(self.body)
        self.label(card,'DEMO PROFILE',11,GREEN,True)
        self.label(card,'Guest passenger',25,INK,True)
        self.label(card,'Cork, Ireland · EUR',14,MUTED)
        self.label(card,'No account or login needed. Your activity stays on this device.',15,MUTED)
        self.button(self.body,'Privacy & how this demo works','privacy',lambda:self.go('privacy'),False)
        self.button(self.body,'Reset all demo data','reset',lambda:self.message('Reset demo data?','Delete rides, food orders and basket. Restore demo seat availability.',self.reset),False)
        self.label(self.body,'Project help: github.com/FUllSCIPTS/ATLAS/issues\nThis demo does not provide emergency transport or live customer support.',13,MUTED)

    def reset(self):
        self.store.reset()
        self.pickup,self.destination,self.party,self.restaurant,self.address,self.comfort = 0,1,1,0,0,False
        self.go('home')

    def privacy(self):
        self.title_block('Transparent by design','Your demo. Your device.','Privacy notice · effective 5 November 2026')
        for heading,description in (
            ('Local data only','Simulated rides, food orders, basket items and shared-seat availability stay in private app storage. No app data is transmitted. No ads, analytics, accounts, payments or location access are included.'),
            ('Delete whenever you like','Use You → Reset all demo data, clear app storage in Android Settings, or uninstall. Android backup is disabled. Drivers, restaurants and distances are illustrative.'),
            ('About this project','Maintainer: FUllSCIPTS / ATLAS on GitHub. Questions: github.com/FUllSCIPTS/ATLAS/issues. Do not post personal details publicly. ATLAS Go is an educational model, separate from real transport and food services.')):
            card = self.box(self.body)
            self.label(card,heading,21,INK,True)
            self.label(card,description,15,MUTED)
