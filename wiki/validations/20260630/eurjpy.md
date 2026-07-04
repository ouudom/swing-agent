---
type: daily_validation
instrument: eurjpy
date: 2026-06-30
week: 2026-W27
generated_utc: "2026-06-30T16:21:30Z"
run_type: automated_hourly
zones:
  - id: eurjpy-2026-W27-PRIMARY
    direction: LONG
    zone: [183.00, 183.60]
    entry_confluence: 0.0
    verdict: NO_TRADE
    e0: false
    reason: zone_unreached
  - id: eurjpy-2026-W27-SECONDARY
    direction: SHORT
    zone: [186.00, 186.50]
    entry_confluence: 0.0
    verdict: NO_TRADE
    e0: false
    reason: zone_unreached
---

# EURJPY Daily Validation — 2026-06-30 (W27 Tuesday)

**Run:** 2026-06-30 16:21 UTC (automated hourly) | **Spot:** 185.681 (latest 1H)

**Gates:** ✅ CB calendar clear | ✅ Econ calendar: 0 HIGH hits in window | ✅ Intervention watch reviewed through 2026-06-30: spot 185.681 above 185.0 hard line → **HARD_BLOCK new longs**.

## Zone 1 — PRIMARY LONG 183.00–183.60
Spot 185.681 is 1.13% above zone top and above the MoF hard-block line for new longs. **❌ NO TRADE — zone unreached + MoF long block.** PENDING.

## Zone 2 — SECONDARY SHORT 186.00–186.50
Spot 185.681 is 0.17% below zone bottom — near, still out of zone. **❌ NO TRADE — zone unreached.** PENDING.

No re-forecast trigger.
