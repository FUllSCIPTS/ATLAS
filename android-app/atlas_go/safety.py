"""Pre-booked rides and SOS (1.6.0): the rules for scheduling a ride ahead of time, and the
emergency helpers (112 dialler link, trusted-contact message, map link).

Pure Python. SOS is deliberately modest: ATLAS Go has no control room, so raising an SOS records
where and when it happened and helps the user call 112 and message a trusted contact through the
phone's own dialler and messaging app. It does not alert ATLAS staff or the emergency services by
itself. No call or message is placed without the user tapping it in that other app.
"""
from __future__ import annotations

import datetime as dt
import re
from urllib.parse import quote

# ---------------------------------------------------------------------------- pre-booking
MIN_AHEAD = 15 * 60           # a pre-booked pickup is at least 15 minutes away (sooner: book now)
MAX_AHEAD = 7 * 24 * 3600     # and at most 7 days away
DISPATCH_LEAD = 10 * 60       # a driver is looked for 10 minutes before the pickup time
GRACE = 30 * 60               # not dispatched 30 minutes after the pickup time: the booking is missed
MAX_PREBOOKS = 3              # upcoming pre-booked rides per account
PREBOOK_STATUSES = ('scheduled', 'dispatched', 'cancelled', 'missed', 'failed')
KEEP_FINISHED = 12            # finished pre-bookings kept per phone for the Activity list


def check_when(when, now: float) -> int:
    if type(when) not in (int, float):
        raise ValueError('Choose a pickup time.')
    if when < now + MIN_AHEAD:
        raise ValueError('Pre-book at least 15 minutes ahead, or book the ride now.')
    if when > now + MAX_AHEAD:
        raise ValueError('Rides can be pre-booked up to 7 days ahead.')
    return int(when)


def when_options(now: dt.datetime) -> list[tuple[str, dt.datetime]]:
    """The pickup times offered on the booking screens, all valid for check_when."""
    options = [('In 30 minutes', now + dt.timedelta(minutes=30)), ('In 1 hour', now + dt.timedelta(hours=1)),
               ('In 2 hours', now + dt.timedelta(hours=2))]
    for label, days, hour, minute in (('Today', 0, 18, 0), ('Tomorrow', 1, 8, 0), ('Tomorrow', 1, 17, 30)):
        at = (now + dt.timedelta(days=days)).replace(hour=hour, minute=minute, second=0, microsecond=0)
        if at >= now + dt.timedelta(seconds=MIN_AHEAD + 60):
            options.append((f'{label} {at:%H:%M}', at))
    return options


def when_text(when: float) -> str:
    return dt.datetime.fromtimestamp(when).strftime('%a %d %b · %H:%M')


def valid_prebook(p, offer_ids) -> bool:
    if not isinstance(p, dict) or p.get('status') not in PREBOOK_STATUSES:
        return False
    if not all(isinstance(p.get(k), str) and p[k] for k in ('id', 'account')):
        return False
    if any(type(p.get(k)) is not int for k in ('pickup', 'destination', 'when', 'created', 'fare')) or p['fare'] <= 0:
        return False
    if p['pickup'] == p['destination'] or not all(0 <= p[k] <= 3 for k in ('pickup', 'destination')):
        return False
    if type(p.get('comfort')) is not bool or type(p.get('pay_by_bank')) is not bool or p.get('party') not in (1, 2):
        return False
    if p.get('offer') is not None and p['offer'] not in offer_ids:
        return False
    return isinstance(p.get('reason', ''), str) and isinstance(p.get('ride', ''), str)


# ---------------------------------------------------------------------------- SOS
EMERGENCY_NUMBER = '112'      # Ireland and the EU; 999 also works in Ireland
PHONE = re.compile(r'^\+[1-9]\d{7,14}$')


def valid_trusted(contact) -> bool:
    return isinstance(contact, dict) and isinstance(contact.get('name'), str) and 2 <= len(contact['name']) <= 40 \
        and isinstance(contact.get('phone'), str) and bool(PHONE.match(contact['phone']))


def valid_sos(e) -> bool:
    if not isinstance(e, dict) or e.get('status') not in ('active', 'resolved') or e.get('role') not in ('passenger', 'driver'):
        return False
    if not isinstance(e.get('id'), str) or not isinstance(e.get('ride'), str) or type(e.get('at')) is not int:
        return False
    if e.get('account') is not None and not isinstance(e['account'], str):
        return False
    point = e.get('point')
    if not isinstance(point, list) or len(point) != 2 or not all(type(v) in (int, float) for v in point) or \
            not -90 <= point[0] <= 90 or not -180 <= point[1] <= 180:
        return False
    if e.get('source') not in ('device', 'route') or type(e.get('shared')) is not bool:
        return False
    return (e['status'] == 'resolved') == (type(e.get('resolved')) is int)


def dial_uri(number: str = EMERGENCY_NUMBER) -> str:
    """tel: link. Opening it shows the dialler with the number filled in; the user presses call."""
    if not re.fullmatch(r'\+?\d{3,15}', number or ''):
        raise ValueError('Invalid phone number.')
    return 'tel:' + number


def sms_uri(number: str, body: str) -> str:
    """sms: link with the message filled in; the user presses send in their messaging app."""
    if not PHONE.match(number or ''):
        raise ValueError('Invalid phone number.')
    return f'sms:{number}?body={quote(body, safe="")}'


def map_link(point) -> str:
    return f'https://www.openstreetmap.org/?mlat={point[0]:.5f}&mlon={point[1]:.5f}#map=17/{point[0]:.5f}/{point[1]:.5f}'


def sos_message(event: dict, name: str, ride: dict | None, places) -> str:
    """The text offered to the trusted contact. It carries what a helper needs and nothing else."""
    at = dt.datetime.fromtimestamp(event['at']).strftime('%H:%M on %d %b')
    who = name or 'An ATLAS Go user'
    text = f'SOS from {who} via ATLAS Go at {at}. '
    if ride:
        text += (f"{'Driving' if event['role'] == 'driver' else 'In a ride'} from {places[ride['pickup']]} to "
                 f"{places[ride['destination']]}" + ('' if event['role'] == 'driver' else f" with {ride['driver']}") + '. ')
    text += f"Last position: {map_link(event['point'])} . If you cannot reach them, call {EMERGENCY_NUMBER}."
    return text


def open_uri(uri: str) -> bool:
    """Hand a tel: or sms: link to Android (ACTION_DIAL / ACTION_SENDTO: no permission needed, nothing
    is sent until the user confirms in that app). Returns False where there is no Android."""
    try:
        from jnius import autoclass
    except ImportError:
        return False
    Intent, Uri = autoclass('android.content.Intent'), autoclass('android.net.Uri')
    activity = autoclass('org.kivy.android.PythonActivity').mActivity
    intent = Intent(Intent.ACTION_DIAL if uri.startswith('tel:') else Intent.ACTION_SENDTO, Uri.parse(uri))
    try:
        activity.startActivity(intent)
    except Exception:             # no dialler or messaging app on this device (ActivityNotFoundException)
        return False
    return True
