"""Python UI acceptance: dispatch actual Kivy controls and capture framebuffer.
Android enables this only in a debuggable APK with an explicit launch intent.
"""
import json
import time
import traceback
from pathlib import Path
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.utils import platform
from .store import LocalStore
from . import intelligence as ai


def ai_rank(app):
    return ai.rank(app.pickup, extra=app.registered_candidates(app.pickup))


class Acceptance:
    def __init__(self, app):
        self.app = app
        self.checks = 0
        self.output = app.store.path.parent / 'test-output'
        self.output.mkdir(parents=True, exist_ok=True)
        self.steps = []
        self.index = 0
        self.waiting_capture = None
        self.capture_deadline = 0
        self.wait_deadline = 0
        self.captures = 0

    def check(self, condition, message):
        if not condition:
            raise AssertionError(message)
        self.checks += 1

    def click(self, key):
        self.check(key in self.app.controls, 'Missing control: '+key)
        self.app.controls[key].trigger_action(duration=0)

    def capture(self, name):
        # Desktop uses the Kivy framebuffer. Android requests an OS screenshot
        # from the host driver, avoiding OpenGL readback state changes.
        self.check(all(w.width >= 40 and w.height >= 44 for w in self.app.controls.values()), 'Controls meet minimum usable dimensions')
        if platform == 'android':
            self.check(self.app.container.padding[1]>0,'Status-bar inset applied')
            self.check(self.app.container.padding[3]>0,'Gesture-bar inset applied')
            (self.output/'capture-request.txt').write_text(name)
            self.waiting_capture = name
            self.captures += 1
            self.capture_deadline = time.monotonic()+45
        else:
            saved = Window.screenshot(name=str(self.output / (name+'.png')))
            Path(saved).replace(self.output / (name+'.png'))

    def shared_reserved(self):
        store = self.app.store
        self.check(store.ride['shared'] and store.ride['party']==2, 'Shared ride confirmed')
        self.check(store.offers[0].seats==1, 'Two shared seats reserved')
        restored = LocalStore(store.path)
        self.check(restored.ride is not None and restored.offers[0].seats==1, 'Reservation persists')

    def insets_ready(self):
        # Android reports system-bar sizes asynchronously after start; slow emulators can
        # take a few seconds. Wait for them (bounded by wait_deadline) before the first capture.
        if platform != 'android':
            return
        if self.app.container.padding[1] <= 0 or self.app.container.padding[3] <= 0:
            return 'wait'
        self.check(True, 'System-bar insets known before first capture')

    def lab_finished(self):
        if self.app.lab is None or not self.app.lab.done:
            return 'wait'
        self.check(True, 'Learning lab finished')

    def fill(self, **values):
        for key, value in values.items():
            self.check(key in self.app.controls, 'Missing field: '+key)
            self.app.controls[key].text = value

    def until(self, condition, message):
        def step():
            if not condition():
                return 'wait'
            self.check(True, message)
        return step

    def live_on(self):
        self.app.live_paused = False

    def live_off(self):
        self.app.live_paused = True

    def account(self, email):
        return next(a for a in self.app.store.accounts if a['email'] == email)

    def start(self, _dt=0):
        a = self.app
        a.reset()
        a.live_paused = True
        S = a.store
        drv, sel, pas = 'driver@atlas.ie', 'seller@atlas.ie', 'rider@atlas.ie'
        self.steps = [
            self.insets_ready, lambda:self.check(a.screen=='welcome','Fresh install opens the welcome screen'),
            lambda:self.capture('01-welcome'), lambda:self.click('welcome_guest'),
            lambda:self.check(S.guest and a.screen=='home','Guest passenger mode'),
            lambda:self.capture('02-home'), lambda:self.click('home_ride'),
            lambda:self.capture('03-ride-booking'), lambda:self.click('book_ride'),
            lambda:self.check(S.ride is not None, 'Solo booking confirmed'),
            lambda:self.check(S.ride['driver'].startswith('Morgan') and 'Mardyke' in S.ride['why'],
                              'Learned dispatch policy chooses and explains the driver'),
            lambda:self.check(a.live_map is not None and S.ride['live']['start'], 'Ride screen shows the live map'),
            lambda:self.capture('04-ride-live'),
            lambda:self.click('ride_next'),lambda:self.click('ride_next'),lambda:self.click('ride_next'),
            lambda:self.check(S.ride is None and len(S.history)==1,'Solo ride completed'),
            lambda:self.click('nav_home'),lambda:self.click('home_pool'),lambda:self.capture('05-shared-rides'),
            lambda:setattr(a.controls['party'],'text','2 seats'),lambda:self.click('find_pool'),
            lambda:self.click('join_pool-1'),self.shared_reserved,
            lambda:self.click('ride_cancel'),lambda:self.click('dialog_confirm'),
            lambda:self.check(S.ride is None and S.offers[0].seats==3,'Cancellation restores capacity'),
            lambda:self.click('nav_food'),lambda:self.capture('06-food-home'),
            lambda:self.click('restaurant_0'),lambda:self.capture('07-food-menu'),
            lambda:self.click('add_bowl'),lambda:self.click('add_juice'),lambda:self.click('menu_cart'),
            lambda:self.check(S.cart.total()==1730,'Basket total includes delivery'),
            lambda:self.capture('08-basket'),lambda:self.click('checkout'),
            lambda:self.check(S.order is not None and S.cart.count()==0,'Checkout clears basket'),
            lambda:self.check(S.order['courier']['dispatch_after']==7,'Learned courier timing saved with order'),
            lambda:self.capture('09-order-tracking'),
            lambda:self.click('order_next'),lambda:self.click('order_next'),lambda:self.click('order_next'),
            lambda:self.check(S.order is None,'Order delivered'),
            lambda:self.click('nav_map'),
            lambda:self.check(a.live_map is not None and a.live_map.interactive,'Live map opens'),
            lambda:self.check(sum(m['kind']=='driver' for m in a.live_map.markers)>=10,'Map shows nearby drivers'),
            lambda:self.capture('10-live-map'),
            lambda:self.click('map_zoom_in'),lambda:self.check(a.live_map.zoom==15,'Map zooms in'),
            lambda:self.click('map_zoom_out'),lambda:self.check(a.live_map.zoom==14,'Map zooms out'),
            # live, time-lapse progress without pressing anything
            lambda:self.click('nav_home'),lambda:self.click('home_ride'),lambda:self.click('book_ride'),self.live_on,
            self.until(lambda:S.ride is not None and S.ride['stage']>=1,'Live journey reaches the pickup on its own'),
            self.live_off,lambda:self.click('ride_cancel'),lambda:self.click('dialog_confirm'),
            lambda:self.click('nav_activity'),lambda:self.capture('11-activity'),
            lambda:self.click('nav_profile'),lambda:self.capture('12-profile'),
            lambda:self.click('privacy'),lambda:self.capture('13-privacy'),
            lambda:self.click('nav_profile'),lambda:self.click('profile_learn'),
            lambda:self.check(a.screen=='intelligence' and 'outlook_next' in a.controls,'Intelligence screen opens'),
            lambda:self.click('models_check'),
            lambda:self.check(a.models and all(ok for _, ok, _ in a.models) and len(a.models)==6,'All six models pass the on-device check'),
            lambda:self.capture('14-intelligence'),
            lambda:self.click('outlook_next'),lambda:self.check(a.outlook_day==1,'Outlook moves to the next day'),
            lambda:self.click('outlook_today'),lambda:self.check(a.outlook_day==0,'Outlook returns to today'),
            lambda:self.click('lab_train'),self.lab_finished,
            lambda:self.check(a.lab.result()['candidate']<a.lab.nearest,'Sandbox policy beats the nearest-driver rule'),
            lambda:setattr(a.scroll,'scroll_y',0),lambda:self.capture('15-learning-lab'),
            # ---- driver registration
            lambda:self.click('nav_profile'),lambda:self.click('profile_register'),
            lambda:self.click('reg_role_driver'),
            lambda:self.fill(reg_name='Siobhan Driver',reg_email='not-an-email',reg_phone='087 123 4567',
                             reg_password='drive2026',reg_confirm='drive2026',reg_vehicle='Toyota Corolla · silver',
                             reg_plate='241-c-1234',reg_licence='a12345',reg_seats='4'),
            lambda:setattr(a.controls['reg_base'],'text','UCC Campus'),
            lambda:self.click('reg_agree'),lambda:self.click('register_submit'),
            lambda:self.check(not S.accounts and 'dialog_confirm' in a.controls,'Invalid email is rejected'),
            lambda:self.click('dialog_confirm'),
            lambda:self.check(a.controls['reg_name'].text=='Siobhan Driver','Form keeps typed details after an error'),
            lambda:self.fill(reg_email=drv),lambda:self.capture('16-register-driver'),
            lambda:self.click('register_submit'),
            lambda:self.check(S.role=='driver' and a.screen=='driver','Driver account created and signed in'),
            lambda:self.check(self.account(drv)['driver']['plate']=='241-C-1234' and 'drive2026' not in json.dumps(S.accounts),
                              'Plate normalised; password stored only as a hash'),
            lambda:self.click('driver_online'),lambda:self.check(self.account(drv)['driver']['online'],'Driver goes online'),
            lambda:self.capture('17-driver-home'),
            lambda:self.click('nav_profile'),lambda:self.click('logout'),
            lambda:self.check(a.screen=='welcome' and S.user is None and self.account(drv)['driver']['online'],
                              'Signed out; driver stays available for dispatch on this phone'),
            # ---- seller registration and menu
            lambda:self.click('welcome_register'),lambda:self.click('reg_role_seller'),
            lambda:self.fill(reg_name='Cathal Baker',reg_email=sel,reg_phone='+353 86 765 4321',reg_password='bread2026',
                             reg_confirm='bread2026',reg_kitchen='Lee Side Bakery',reg_cuisine='Bakery & coffee',
                             reg_business='FBO-12345',reg_prep='10'),
            lambda:self.click('reg_agree'),lambda:self.capture('18-register-seller'),lambda:self.click('register_submit'),
            lambda:self.check(S.role=='seller' and a.screen=='seller','Seller account and kitchen created'),
            lambda:self.click('kitchen_menu'),
            lambda:self.fill(dish_name='Sourdough toastie',dish_detail='Cheddar · red onion · rocket',dish_price='8.50'),
            lambda:self.click('dish_add'),
            lambda:self.fill(dish_name='Flat white',dish_detail='Double shot · oat or dairy',dish_price='3,60'),
            lambda:self.click('dish_add'),
            lambda:self.check([d['price'] for d in S.kitchen_of(S.user)['dishes']]==[850,360],'Dishes priced in cents'),
            lambda:self.capture('19-seller-menu'),
            lambda:self.click('nav_profile'),lambda:self.click('logout'),
            # ---- passenger registration, matched to the registered driver, order from the seller
            lambda:self.click('welcome_register'),lambda:self.click('reg_role_passenger'),
            lambda:self.fill(reg_name='Aoife Rider',reg_email=pas,reg_phone='0851112233',reg_password='ride2026x',reg_confirm='ride2026x'),
            lambda:self.click('reg_agree'),lambda:self.click('register_submit'),
            lambda:self.check(S.role=='passenger' and a.screen=='home','Passenger account created'),
            lambda:self.check(not S.my_history(),'New passenger sees only their own history'),
            lambda:self.click('home_ride'),
            lambda:self.check(any(c.account for c, _ in ai_rank(a)),'Registered online driver competes in dispatch'),
            lambda:self.click('book_ride'),
            lambda:self.check(S.ride['driver_id']==self.account(drv)['id'] and S.ride['pending'],'Policy matches the registered driver'),
            lambda:self.capture('20-ride-waiting'),
            lambda:self.click('nav_food'),lambda:self.click('restaurant_3'),
            lambda:self.click('add_'+S.kitchen_of(self.account(sel))['dishes'][0]['id']),lambda:self.click('menu_cart'),
            lambda:self.check(S.cart.total()==1100,'Seller dish in basket with delivery'),
            lambda:self.click('checkout'),
            lambda:self.check(S.order['pending'] and S.order['courier']['prep']==10,'Seller order waits for the kitchen; courier timed to its prep'),
            lambda:self.click('nav_profile'),lambda:self.click('logout'),
            # ---- wrong password, then the driver accepts and drives
            lambda:self.click('welcome_login'),lambda:self.fill(login_email=drv,login_password='wrong-pass1'),
            lambda:self.click('login_submit'),lambda:self.check(S.user is None,'Wrong password is refused'),
            lambda:self.click('dialog_confirm'),lambda:self.fill(login_password='drive2026'),lambda:self.click('login_submit'),
            lambda:self.check(a.screen=='driver' and 'job_accept' in a.controls,'Driver sees the ride request'),
            lambda:self.capture('21-driver-request'),
            lambda:self.click('job_accept'),lambda:self.check(not S.ride['pending'],'Driver accepted'),
            lambda:self.click('job_next'),lambda:self.click('job_next'),lambda:self.click('job_next'),
            lambda:self.check(S.ride is None and self.account(drv)['driver']['earnings']==860
                              and self.account(drv)['driver']['accepted']==1,'Trip completed; earnings and acceptance recorded'),
            lambda:self.click('nav_profile'),lambda:self.click('logout'),
            # ---- seller accepts and hands over to the courier
            lambda:self.click('welcome_login'),lambda:self.fill(login_email=sel,login_password='bread2026'),lambda:self.click('login_submit'),
            lambda:self.click('order_accept'),lambda:self.click('order_ready'),
            lambda:self.check(S.order['stage']==1,'Seller marked the food ready'),
            lambda:self.capture('22-seller-order'),
            lambda:self.click('nav_profile'),lambda:self.click('logout'),
            lambda:self.click('welcome_login'),lambda:self.fill(login_email=pas,login_password='ride2026x'),lambda:self.click('login_submit'),
            lambda:self.click('home_active_order'),lambda:self.click('order_next'),lambda:self.click('order_next'),
            lambda:self.check(S.order is None and S.kitchen_of(self.account(sel))['sales']==850,'Seller sale recorded'),
            lambda:self.check(len(S.my_history())==2,'Passenger history has their ride and order'),
            # ---- account deletion
            lambda:self.click('nav_profile'),lambda:self.click('delete_account'),
            lambda:setattr(a.controls['dialog_password'],'text','ride2026x'),lambda:self.click('dialog_confirm'),
            lambda:self.check(a.screen=='welcome' and len(S.accounts)==2,'Passenger deleted their account'),
            lambda:self.check(LocalStore(S.path).session is None and len(LocalStore(S.path).accounts)==2,'Deletion persists'),
        ]
        self.steps += [
            lambda:self.click('welcome_guest'),lambda:self.click('home_ride'),
            lambda:setattr(a.controls['destination'],'text','UCC Campus'),
            lambda:self.check('book_ride' not in a.controls,'Same-place booking blocked on screen'),
            lambda:setattr(a.controls['destination'],'text','Cork City Centre'),
            lambda:setattr(a.controls['vehicle'],'text','ATLAS Comfort · extra space'),
            lambda:(self.account(drv)['driver'].__setitem__('online', False), S.save()),
            lambda:self.click('book_ride'),
            lambda:self.check(S.ride['fare']==1118,'Comfort selection affects confirmation'),
            lambda:self.click('nav_home'),lambda:self.click('home_ride'),lambda:self.click('book_ride'),
            lambda:self.check(S.ride['fare']==1118,'Duplicate booking keeps active ride'),
            lambda:self.click('dialog_confirm'),lambda:self.click('nav_activity'),lambda:self.click('activity_ride'),
            lambda:self.click('ride_cancel'),lambda:self.click('dialog_confirm'),
            lambda:self.click('nav_home'),lambda:self.click('home_pool'),lambda:setattr(a.controls['pickup'],'text','Cork Airport'),
            lambda:self.check(not any(k.startswith('join_') for k in a.controls),'Unmatched route has no join button'),
            lambda:setattr(a.controls['pickup'],'text','UCC Campus'),lambda:self.click('join_pool-2'),
            lambda:self.check(S.offers[1].seats==0,'Last two seats can be reserved'),
            lambda:self.click('ride_cancel'),lambda:self.click('dialog_confirm'),
            lambda:self.check(S.offers[1].seats==2,'Second cancellation restores seats'),
            lambda:self.click('nav_food'),lambda:self.click('restaurant_1'),
            lambda:self.click('add_pizza'),lambda:self.click('add_pizza'),lambda:self.click('menu_cart'),
            lambda:self.click('remove_pizza'),lambda:self.check(S.cart.count()==1,'Remove decrements quantity'),
            lambda:self.click('clear_cart'),lambda:self.check('empty_food' in a.controls,'Clear basket empty state'),
            lambda:self.click('empty_food'),lambda:self.click('restaurant_2'),lambda:self.click('add_curry'),
            lambda:self.click('nav_food'),lambda:self.click('restaurant_0'),lambda:self.click('add_bowl'),
            lambda:self.check(S.cart.items=={'curry':1},'Cross-restaurant error preserves basket'),
            lambda:self.click('dialog_confirm'),lambda:self.click('nav_profile'),lambda:self.click('reset'),
            lambda:self.click('dialog_cancel'),lambda:self.check(S.cart.count()==1,'Cancelled reset preserves data'),
            lambda:self.click('reset'),lambda:self.click('dialog_confirm'),
            lambda:self.check(not S.history and not S.accounts and not S.cart.items and a.screen=='welcome','Confirmed reset clears state'),
        ]
        Clock.schedule_once(self.next_step, .6)

    def next_step(self, _dt):
        try:
            if self.waiting_capture:
                acknowledgement = self.output/'capture-ack.txt'
                if acknowledgement.exists() and acknowledgement.read_text().strip()==self.waiting_capture:
                    self.waiting_capture = None
                elif time.monotonic()>self.capture_deadline:
                    raise TimeoutError('Android system screenshot was not acknowledged')
                else:
                    Clock.schedule_once(self.next_step,.1)
                    return
            if self.index < len(self.steps):
                if self.steps[self.index]() == 'wait':
                    if not self.wait_deadline:
                        self.wait_deadline = time.monotonic()+60
                    elif time.monotonic()>self.wait_deadline:
                        raise TimeoutError('Step did not finish in time')
                    Clock.schedule_once(self.next_step,.25)
                    return
                self.wait_deadline = 0
                self.index += 1
                Clock.schedule_once(self.next_step,.6)
                return
            shots = len(list(self.output.glob('*.png'))) if platform != 'android' else self.captures
            self.finish(True, f'{self.checks} Python UI and persistence assertions; {shots} screenshots', shots)
        except Exception:
            self.finish(False, traceback.format_exc())

    def finish(self, success, detail, screenshots=0):
        result = dict(success=success,checks=self.checks,detail=detail,screenshots=screenshots)
        (self.output/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        print('ATLAS_ACCEPTANCE '+json.dumps(result),flush=True)
        if platform != 'android':
            self.app.stop()
