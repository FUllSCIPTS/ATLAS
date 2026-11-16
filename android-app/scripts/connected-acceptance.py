"""Connected-mode acceptance: the real Kivy app -> HTTP -> the ATLAS Go server -> PostgreSQL.

Start the server (see server/README.md), then from android-app/:
    ATLAS_API_URL=http://127.0.0.1:8080 ATLAS_DATA_DIR="$PWD/local-data-connected" KIVY_NO_ARGS=1 \
        xvfb-run -a python scripts/connected-acceptance.py
It registers a driver and a passenger through the screens, connects both to the server, links their
bank accounts there, pays for a ride by bank, waits for the background sync and pays the driver out.
The result is written to <ATLAS_DATA_DIR>/test-output/result.json (check it and the database with verify-connected.py).
"""
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kivy.config import Config
Config.set('graphics', 'width', '440'); Config.set('graphics', 'height', '940')
from kivy.clock import Clock
from atlas_go.app import AtlasGoApp
from atlas_go.acceptance import Acceptance, ORDINARY

URL = os.environ['ATLAS_API_URL']

class Connected(Acceptance):
    def idle(self, message):
        return self.until(lambda: not self.app.busy, message)
    def start(self, _dt=0):
        a = self.app; a.reset(); a.clock_override = ORDINARY; a.live_paused = True; S = a.store
        drv, pas = 'driver@atlas.ie', 'rider@atlas.ie'
        self.steps = [
            lambda: self.click('welcome_register'), lambda: self.click('reg_role_driver'),
            lambda: self.fill(reg_name='Siobhan Driver', reg_email=drv, reg_phone='087 123 4567', reg_password='drive2026',
                              reg_confirm='drive2026', reg_vehicle='Toyota Corolla', reg_plate='241-C-1234', reg_licence='A12345', reg_seats='4'),
            lambda: setattr(a.controls['reg_base'], 'text', 'UCC Campus'),
            lambda: self.click('reg_agree'), lambda: self.click('register_submit'),
            lambda: self.click('driver_online'), lambda: self.click('open_wallet'),
            lambda: self.fill(server_url=URL, server_password='drive2026'), lambda: self.click('server_connect'),
            self.until(lambda: S.user.get('server'), 'Driver connected to the server'),
            self.idle('idle'),
            lambda: self.fill(bank_iban='DE89 3704 0044 0532 0130 00', bank_password='drive2026'), lambda: self.click('bank_link'),
            self.until(lambda: S.user.get('bank'), 'Driver payout account linked on the server, then the phone'),
            lambda: self.click('nav_profile'), lambda: self.click('logout'),
            # passenger: registration auto-connects because a server address is saved
            lambda: self.click('welcome_register'), lambda: self.click('reg_role_passenger'),
            lambda: self.fill(reg_name='Aoife Rider', reg_email=pas, reg_phone='0851112233', reg_password='ride2026x', reg_confirm='ride2026x'),
            lambda: self.click('reg_agree'), lambda: self.click('register_submit'),
            self.until(lambda: S.user and S.user.get('server'), 'Passenger auto-connected at registration'),
            self.idle('idle'),
            lambda: self.click('nav_profile'), lambda: self.click('profile_wallet'),
            lambda: self.fill(bank_iban='IE29 AIBK 9311 5212 3456 78', bank_password='ride2026x'),
            lambda: self.click('bank_consent'), lambda: self.click('bank_link'),
            self.until(lambda: S.user.get('bank'), 'Passenger mandate created by the server'),
            lambda: self.check(S.user['bank']['mandate']['id'].startswith('M-') and len(S.user['bank']['mandate']['id']) == 14,
                               'Phone keeps the mandate id issued by the server'),
            lambda: self.click('nav_home'), lambda: self.click('home_ride'), lambda: self.click('book_ride'),
            lambda: self.check(S.ride['pending'] and S.payment(S.ride['payment'])['status'] == 'authorised', 'Ride authorised'),
            lambda: self.click('nav_profile'), lambda: self.click('logout'),
            lambda: self.click('welcome_login'), lambda: self.fill(login_email=drv, login_password='drive2026'), lambda: self.click('login_submit'),
            lambda: self.click('job_accept'), lambda: self.click('job_next'), lambda: self.click('job_next'), lambda: self.click('job_next'),
            self.until(lambda: S.payments[0]['synced'], 'Captured payment copied to the server in the background'),
            self.idle('idle'),
            lambda: self.click('open_wallet'), lambda: self.capture('connected-wallet'),
            lambda: self.click('payout'), lambda: setattr(a.controls['dialog_password'], 'text', 'drive2026'), lambda: self.click('dialog_confirm'),
            self.until(lambda: S.payouts and S.payouts[0]['synced'], 'Payout made on the server first, then recorded on the phone'),
            lambda: self.check(S.payouts[0]['amount'] == 731 and S.wallet()['balance'] == 0, 'Balance paid out'),
            lambda: self.click('dialog_confirm'),
            lambda: self.click('server_sync'), self.idle('idle'),
            lambda: self.check('up to date' in a.sync_note, 'Nothing left to sync: ' + a.sync_note),
        ]
        Clock.schedule_once(self.next_step, .6)

class App(AtlasGoApp):
    def on_start(self):
        self.acceptance = Connected(self)
        Clock.schedule_once(self.acceptance.start, 1.5)

App().run()
