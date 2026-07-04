---
type: daily_validation
instrument: eurusd
date: 2026-06-30
week: 2026-W27
generated_utc: "2026-06-30T16:21:30Z"
run_type: automated_hourly
zones:
  - id: eurusd-2026-W27-PRIMARY
    direction: SHORT
    zone: [1.1450, 1.1490]
    entry_confluence: 0.0
    verdict: NO_TRADE
    e0: false
    reason: zone_unreached
  - id: eurusd-2026-W27-SECONDARY
    direction: SHORT
    zone: [1.1500, 1.1545]
    entry_confluence: 0.0
    verdict: NO_TRADE
    e0: false
    reason: zone_unreached
---

# EURUSD Daily Validation — 2026-06-30 (W27 Tuesday)

**Run:** 2026-06-30 16:21 UTC (automated hourly) | **Spot:** 1.14145 (latest 1H)

**Gates:** ✅ CB calendar clear | ✅ Econ calendar: 5 HIGH hits in window (same US set as xauusd) — none inside today's window.

## Zone 1 — PRIMARY SHORT 1.1450–1.1490
Spot 1.14145 is 0.31% below zone bottom — out of zone. **❌ NO TRADE — zone unreached.** PENDING.

## Zone 2 — SECONDARY SHORT 1.1500–1.1545
Spot 1.14145 is 0.74% below zone bottom — out of zone. **❌ NO TRADE — zone unreached.** PENDING.

No re-forecast trigger. Both zones unchanged from W27 publish.
