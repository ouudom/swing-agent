---
type: daily_validation
instrument: gbpusd
date: 2026-06-30
week: 2026-W27
generated_utc: "2026-06-30T16:21:30Z"
run_type: automated_hourly
zones:
  - id: gbpusd-2026-W27-PRIMARY
    direction: SHORT
    zone: [1.3340, 1.3390]
    entry_confluence: 0.0
    verdict: NO_TRADE
    e0: false
    reason: zone_unreached
  - id: gbpusd-2026-W27-COUNTER
    direction: LONG
    zone: [1.3140, 1.3180]
    entry_confluence: 0.0
    verdict: NO_TRADE
    e0: false
    reason: zone_unreached
---

# GBPUSD Daily Validation — 2026-06-30 (W27 Tuesday)

**Run:** 2026-06-30 16:21 UTC (automated hourly) | **Spot:** 1.32543 (latest 1H)

**Gates:** ✅ CB calendar clear | ✅ Econ calendar: 6 HIGH hits in window (UK GDP/Bailey + US set) — none inside today's window. Note: FF feed glitched mid-pull this run, dedicated econ gate still served clean from DB cache (EXIT=0).

## Zone 1 — PRIMARY SHORT 1.3340–1.3390
Spot 1.32543 is 0.64% below zone bottom — out of zone. **❌ NO TRADE — zone unreached.** PENDING.

## Zone 2 — COUNTER LONG 1.3140–1.3180
Spot 1.32543 is 0.56% above zone top — out of zone. **❌ NO TRADE — zone unreached.** PENDING.

No re-forecast trigger. Both zones unchanged from W27 publish.
