# ATLAS Go 1.4.0 release notes

**The learning agents now work as one loop on the phone.** Every city hour a compact LSTM forecasts demand for the next six hours from the last 24 hours of served trips, unserved requests, extra drivers and the calendar. The supply agent decides how many extra drivers to add, using the calendar *and* that forecast. The hour's real outcome is recorded. The agent learns from every hour; each night the LSTM is refitted on what actually happened, and both models are kept only if they beat the current ones on held-out recent hours.

| Component | 1.3.0 | 1.4.0 |
|---|---|---|
| Live LSTM inference feeding the on-device RL agent | Not implemented | Implemented (`atlas_go/loop.py`) |
| Continuous online LSTM–RL retraining | Not implemented | Implemented: agent hourly, LSTM output layer nightly, champion/challenger validation |
| LSTM forecast in dispatch | Fixed hourly tables | The live forecast is the dispatch policy's surge feature |

**Results (simulation, held out Jul–Dec 2026):** next-hour forecast error 9.3 % (surge recall 0.81); supply cost −18 % and unserved requests −18 % against the 1.2 calendar agent.

**Where to see it:** How ATLAS learns → *Live loop* (forecast, decision, versions, nightly accept/reject), *Run 7 city days*, *Check the loop*; drivers see the live forecast in *When to drive*; the Twin tab lists the loop under Layer 1.

**Unchanged:** the 1.2 learned tables (`intelligence.py`, `learned.py`), Layer 2, permissions (no new ones). Everything runs on the phone; nothing is sent anywhere.

Install: the 1.4.0 APK is signed with the same key as 1.3.0 and installs over it. Uninstall 1.2.0 first. Full list: [CHANGELOG](../../CHANGELOG.md).
