# ATLAS Go 1.3.0 release notes

**Two layers.** Layer 1 is the 1.2.0 intelligence (surge outlook, dispatch policy v1.4, acceptance model, supply agent, Q-learning courier timing, learning lab), unchanged: `intelligence.py` and `learned.py` are byte-identical and a test checks it. Layer 2 sits on top and only reads Layer 1's forecast, ranking and cost model. Turn Layer 2 off in the new **Twin** tab and the app behaves exactly as 1.2.0.

**The city twin.** A digital twin of Cork mirrors every driver, your car and the courier (with a fidelity score) and foresees the next 30 minutes per pickup place.

**Agent 1 · Dispatch** rehearses Layer 1's top three drivers 200 times each in the twin and sends the lowest total wait. **Agent 2 · Pricing and moves** rehearses three plans per area every five minutes, with prices capped at ×2.0 (×1.0 at ordinary times), and gives drivers a *Twin hint* and kitchens the courier's twin ETA. **Agent 3 · Guardian** checks every decision, blocks unsafe ones such as a ×4 price, falls back to Layer 1, re-tests the agent 500 times and hands control back. The Twin tab shows the Guardian log, a fault drill and four Layer 2 self-checks.

**Shared rides in the right order.** Every shared car already carries a rider. You wait while the driver comes with that rider, you board, the earlier rider is dropped, and only then are you dropped. The ride screen shows the stops as a checklist and the map shows the earlier rider's stop; the app refuses to finish your ride before the earlier drop-off. Seats are freed on arrival as well as on cancel.

**Permissions** are unchanged: Internet (map tiles), network state, fine and coarse location (foreground only). No background location, ads, analytics or payments. Everything in Layer 2 runs on the phone.

Install: uninstall 1.2.0 first (different signing key). Full list: [CHANGELOG](../../CHANGELOG.md).
