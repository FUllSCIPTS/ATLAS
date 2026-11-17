# ATLAS Go 1.6.0 release notes

**Pre-booked rides and SOS.** Ordinary and shared rides can be booked for later, and passengers and drivers have an SOS button during a ride.

| Component | 1.4.0 | 1.6.0 |
|---|---|---|
| Pre-book an ordinary ride | Not implemented | Implemented: pickup 15 minutes to 7 days ahead; the fare is fixed when you pre-book; a driver is chosen 10 minutes before pickup |
| Pre-book a shared ride | Not implemented | Implemented: one or two seats are held from the moment you pre-book and released on cancel |
| SOS during a ride | Not implemented | Implemented: records ride, time and place; **Call 112** and **Message my trusted contact** open the phone's dialler and messaging app; ending it needs the password |
| Trusted contact | Not implemented | **You → Safety & SOS**: a name and mobile number, kept on the phone |
| Bank payments (passengers, drivers, food sellers) | Not implemented | Implemented in 1.5.0 (sandbox bank): pay by bank, balances, payouts |
| Back end using PostgreSQL | Not implemented | Implemented in 1.5.0: [`server/`](../../server/README.md), optional, not packaged in the APK |
| User registration | On the phone | On the phone and, when connected, on the server (1.5.0) |
| Layer 1 live loop and Layer 2 digital twin | Implemented | Unchanged (the same code and results as 1.4.0) |
| Android permissions | 4 | The same 4: SOS opens other apps with `ACTION_DIAL` and `ACTION_SENDTO`, so it needs no call or SMS permission |

**Limits you should know about.** The phone is the scheduler: ATLAS Go must be open and signed in around the pickup time, otherwise a pre-booking is marked *missed* after 30 minutes. ATLAS Go has no control room: an SOS alerts nobody until you press call or send, and the Emergency screen says so. In an emergency call 112.

**Upgrading.** 1.6.0 reads 1.5.0, 1.4.0, 1.3.0, 1.2.0 and 1.1.0 data files. See the [CHANGELOG](../../CHANGELOG.md) and the [user guide](../../docs/USER_GUIDE.md#14-pre-book-a-ride-new-in-16).
