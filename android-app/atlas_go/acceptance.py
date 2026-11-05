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

    def start(self, _dt=0):
        a = self.app
        a.reset()
        self.steps = [
            self.insets_ready, lambda:self.capture('01-home'), lambda:self.click('home_ride'),
            lambda:self.capture('02-ride-booking'), lambda:self.click('book_ride'),
            lambda:self.check(a.store.ride is not None, 'Solo booking confirmed'),
            lambda:self.check(a.store.ride['driver'].startswith('Morgan') and 'Mardyke' in a.store.ride['why'],
                              'Learned dispatch policy chooses and explains the driver'),
            lambda:self.capture('03-ride-confirmed'),
            lambda:self.click('ride_next'),lambda:self.click('ride_next'),lambda:self.click('ride_next'),
            lambda:self.check(a.store.ride is None and len(a.store.history)==1,'Solo ride completed'),
            lambda:self.click('nav_share'),lambda:self.capture('04-shared-rides'),
            lambda:setattr(a.controls['party'],'text','2 seats'),lambda:self.click('find_pool'),
            lambda:self.click('join_pool-1'),self.shared_reserved,
            lambda:self.capture('05-shared-confirmed'),lambda:self.click('ride_cancel'),
            lambda:self.click('dialog_confirm'),
            lambda:self.check(a.store.ride is None and a.store.offers[0].seats==3,'Cancellation restores capacity'),
            lambda:self.click('nav_food'),lambda:self.capture('06-food-home'),
            lambda:self.click('restaurant_0'),lambda:self.capture('07-food-menu'),
            lambda:self.click('add_bowl'),lambda:self.click('add_juice'),lambda:self.click('menu_cart'),
            lambda:self.check(a.store.cart.total()==1730,'Basket total includes delivery'),
            lambda:self.capture('08-basket'),lambda:self.click('checkout'),
            lambda:self.check(a.store.order is not None and a.store.cart.count()==0,'Checkout clears basket'),
            lambda:self.check(a.store.order['courier']['dispatch_after']==7,'Learned courier timing saved with order'),
            lambda:self.capture('09-order-tracking'),
            lambda:self.click('order_next'),lambda:self.click('order_next'),lambda:self.click('order_next'),
            lambda:self.check(a.store.order is None,'Order delivered'),
            lambda:self.click('nav_activity'),lambda:self.capture('10-activity'),
            lambda:self.click('nav_profile'),lambda:self.capture('11-profile'),
            lambda:self.click('privacy'),lambda:self.capture('12-privacy'),
            lambda:self.click('nav_profile'),lambda:self.click('profile_learn'),
            lambda:self.check(a.screen=='intelligence' and 'outlook_next' in a.controls,'Intelligence screen opens'),
            lambda:self.capture('13-intelligence'),
            lambda:self.click('outlook_next'),lambda:self.check(a.outlook_day==1,'Outlook moves to the next day'),
            lambda:self.click('outlook_today'),lambda:self.check(a.outlook_day==0,'Outlook returns to today'),
            lambda:self.click('lab_train'),self.lab_finished,
            lambda:self.check(a.lab.result()['candidate']<a.lab.nearest,'Sandbox policy beats the nearest-driver rule'),
            lambda:setattr(a.scroll,'scroll_y',0),lambda:self.capture('14-learning-lab'),
        ]
        self.steps += [
            lambda:self.click('nav_home'),lambda:self.click('home_ride'),
            lambda:setattr(a.controls['destination'],'text','UCC Campus'),
            lambda:self.check('book_ride' not in a.controls,'Same-place booking blocked on screen'),
            lambda:setattr(a.controls['destination'],'text','Cork City Centre'),
            lambda:setattr(a.controls['vehicle'],'text','ATLAS Comfort · extra space'),
            lambda:self.click('book_ride'),
            lambda:self.check(a.store.ride['fare']==1118,'Comfort selection affects confirmation'),
            lambda:self.click('nav_home'),lambda:self.click('home_ride'),lambda:self.click('book_ride'),
            lambda:self.check(a.store.ride['fare']==1118,'Duplicate booking keeps active ride'),
            lambda:self.click('dialog_confirm'),lambda:self.click('nav_activity'),lambda:self.click('activity_ride'),
            lambda:self.click('ride_cancel'),lambda:self.click('dialog_confirm'),
            lambda:self.click('nav_share'),lambda:setattr(a.controls['pickup'],'text','Cork Airport'),
            lambda:self.check(not any(k.startswith('join_') for k in a.controls),'Unmatched route has no join button'),
            lambda:setattr(a.controls['pickup'],'text','UCC Campus'),lambda:self.click('join_pool-2'),
            lambda:self.check(a.store.offers[1].seats==0,'Last two seats can be reserved'),
            lambda:self.click('ride_cancel'),lambda:self.click('dialog_confirm'),
            lambda:self.check(a.store.offers[1].seats==2,'Second cancellation restores seats'),
            lambda:self.click('nav_food'),lambda:self.click('restaurant_1'),
            lambda:self.click('add_pizza'),lambda:self.click('add_pizza'),lambda:self.click('menu_cart'),
            lambda:self.click('remove_pizza'),lambda:self.check(a.store.cart.count()==1,'Remove decrements quantity'),
            lambda:self.click('clear_cart'),lambda:self.check('empty_food' in a.controls,'Clear basket empty state'),
            lambda:self.click('empty_food'),lambda:self.click('restaurant_2'),lambda:self.click('add_curry'),
            lambda:self.click('nav_food'),lambda:self.click('restaurant_0'),lambda:self.click('add_bowl'),
            lambda:self.check(a.store.cart.items=={'curry':1},'Cross-restaurant error preserves basket'),
            lambda:self.click('dialog_confirm'),lambda:self.click('nav_profile'),lambda:self.click('reset'),
            lambda:self.click('dialog_cancel'),lambda:self.check(a.store.cart.count()==1,'Cancelled reset preserves data'),
            lambda:self.click('reset'),lambda:self.click('dialog_confirm'),
            lambda:self.check(not a.store.history and not a.store.cart.items and a.screen=='home','Confirmed reset clears state'),
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
            self.finish(True, f'{self.checks} Python UI and persistence assertions; fourteen screenshots')
        except Exception:
            self.finish(False, traceback.format_exc())

    def finish(self, success, detail):
        result = dict(success=success,checks=self.checks,detail=detail)
        (self.output/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        print('ATLAS_ACCEPTANCE '+json.dumps(result),flush=True)
        if platform != 'android':
            self.app.stop()
