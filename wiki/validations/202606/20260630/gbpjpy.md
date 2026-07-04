---
type: daily_validation
instrument: gbpjpy
date: 2026-06-30
week: 2026-W27
generated_utc: "2026-06-30T16:21:30Z"
run_type: automated_hourly
zones:
  - id: gbpjpy-2026-W27-PRIMARY
    direction: SHORT
    zone: [215.00, 215.60]
    entry_confluence: 5.5
    verdict: ORDER_LIMIT
    e0: false
    limit_price: 215.739
  - id: gbpjpy-2026-W27-COUNTER
    direction: LONG
    zone: [212.00, 212.55]
    entry_confluence: 0.0
    verdict: NO_TRADE
    e0: false
    reason: zone_unreached
---

# GBPJPY Daily Validation — 2026-06-30 (W27 Tuesday)

**Run:** 2026-06-30 16:21 UTC (automated hourly) | **Spot:** 215.557 (latest 1H)

**Gates:** ✅ CB calendar clear | ✅ Econ calendar: Bailey 2026-07-01 13:00 UTC beyond today's expiry | ✅ Intervention watch reviewed through 2026-06-30: active MoF regime hard-blocks new longs; primary SHORT not blocked.

> [!warning] GBPJPY trades above the 214.0 MoF hard-block level for new longs. Counter-long remains blocked while spot stays in the active intervention zone.

## Zone 1 — PRIMARY SHORT 215.00–215.60
**Spot 215.557 — IN ZONE.**

V1b ✅ intact (last 2 H4 closes 215.546, 215.557; SHORT threshold 215.650). V1/V3: no hard block on the short.

| # | Signal | Wt | Pass |
|---|--------|----|------|
| E0 reversal confirm | 3.0 | ❌ none on latest closed 1H |
| E1 H4 extreme still live | 2.5 | ✅ |
| E2 session | 1.5 | ❌ outside long-only NY edge; short gets no session credit |
| E3 H1 timing structure | 1.0 | ✅ |
| E4 structure intact | 1.0 | ✅ |
| E5 not extended / ADX<25 | 1.0 | ✅ |
| **TOTAL** | **10** | **5.5** |

```
SL = avg(0.5×D1_ATR 0.5505, H4_ATR 0.426) = 0.488
anchor = 50% zone midpoint = 215.300 (no E0)
offset = max(0.488/3, (10-5.5)×0.2×0.488) = 0.439
limit_price = 215.300 + 0.439 = 215.739
SL price = 215.739 + 0.488 = 216.227
TP1 (2.5R) = 214.519 (manual) | TP2 (3.0R) = 214.275 (limit) | BE @1.5R = 215.007
```

**✅ ORDER LIMIT: SELL 215.739 | SL 216.227 | TP1 2.5R 214.519 (manual) | TP2 3.0R 214.275 (limit) | BE @1.5R | expires 2026-06-30 21:00 UTC**
Entry Confluence: 5.5/10 (E0:❌ E1:✅ E2:❌ E3:✅ E4:✅ E5:✅)
"If price reaches 215.739, order triggers. Cancel if not hit by 21:00 UTC."

Ledger: ACCEPT (no-E0) — midpoint anchor, not locked; re-derives next hour per D032. FX netting: INDEPENDENT (no other live FX order).

## Zone 2 — COUNTER LONG 212.00–212.55
Spot 215.557 is 1.41% above zone top and spot is above the MoF hard-block level for new longs. **❌ NO TRADE — zone unreached + MoF long block.**

No re-forecast trigger yet; watch USDJPY/JPY-cross extension.
