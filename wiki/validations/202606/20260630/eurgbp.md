---
type: daily_validation
instrument: eurgbp
date: 2026-06-30
week: 2026-W27
generated_utc: "2026-06-30T16:21:30Z"
run_type: automated_hourly
zones:
  - id: eurgbp-2026-W27-PRIMARY
    direction: LONG
    zone: [0.8595, 0.8620]
    entry_confluence: 4.5
    verdict: NO_TRADE
    e0: false
    reason: score_below_floor
  - id: eurgbp-2026-W27-SECONDARY
    direction: SHORT
    zone: [0.8675, 0.8710]
    entry_confluence: 0.0
    verdict: NO_TRADE
    e0: false
    reason: zone_unreached
---

# EURGBP Daily Validation — 2026-06-30 (W27 Tuesday)

**Run:** 2026-06-30 16:21 UTC (automated hourly) | **Spot:** 0.86131 (latest 1H)

**Gates:** ✅ CB calendar clear | ✅ Econ calendar: Bailey 2026-07-01 13:00 UTC beyond today's expiry | No USD leg/DXY gate.

## Zone 1 — PRIMARY LONG 0.8595–0.8620
**Spot 0.86131 — IN ZONE.**

V1b ✅ intact (last 2 H4 closes 0.86114, 0.86131; LONG threshold 0.85910). V1/V3/macro-flip: no hard block.

| # | Signal | Wt | Pass |
|---|--------|----|------|
| E0 reversal confirm | 3.0 | ❌ none on latest closed 1H |
| E1 D1 oscillator still extreme | 2.5 | ✅ |
| E2 H1 oscillator extreme | 1.5 | ❌ |
| E3 non-trending ADX<25 | 1.0 | ✅ |
| E4 structure intact | 1.0 | ✅ |
| E5 compression holds | 1.0 | ❌ |
| **TOTAL** | **10** | **4.5** |

**❌ NO TRADE — score < 5.0:** Entry Confluence 4.5/10. Prior no-E0 midpoint order no longer qualifies; ledger effective state = NO_TRADE.

## Zone 2 — SECONDARY SHORT 0.8675–0.8710
Spot 0.86131 is 0.71% below zone bottom — out of zone. **❌ NO TRADE — zone unreached.** PENDING.

No re-forecast trigger.
