---
type: daily_validation
instrument: gbpusd
date: 2026-07-03
week: 2026-W27
active_zone: NONE
v1_structure_intact: true
v1b_intact: true
v3_news_clear: true
vix_veto: false
vix_stale: false
reforecast_action: NONE
reforecast_triggers: []
e0_entry_confirmation: false
e1: false
e2: false
e3: false
e4: true
e5: false
entry_confluence_score: 1.0
order_limit: NO_TRADE
limit_price: 0000.00
limit_direction: N/A
h4_atr: 0.00281
d1_atr: 0.00809
d1_atr_compressed: false
adx_val: 40.7
---

# Validation — 2026-07-03 (PRIMARY + COUNTER zones from [[2026-W27]])

## Market Snapshot
| | Value |
|---|---|
| Spot | 1.33605 (D1 close) — **inside PRIMARY zone 1.3340-1.3390** |
| H4 ATR | 0.00281 |
| D1 ATR | 0.00809 (median 0.00754, expanding) |
| D1 RSI | 45.1 (neutral) | D1 Stoch 72.8 (not extreme) | D1 ADX 40.7 (strong trend) |
| H1 RSI | 46.6, H1 Stoch 53 (neutral, no reclaim) |
| DXY 1d jump | -0.02 (not >0.5 either direction) |

## Q1+Q2 — Hard Blocks
| | Result |
|---|---|
| V1b PRIMARY (buf 0.0006) | ✅ intact — H4 closes 1.33384/1.33605 < 1.3396 threshold |
| V1b COUNTER | ✅ intact (unreached) |
| V3 | ✅ clear |
| DXY-jump >0.5 against | ✅ clear |
| VIX veto (LONGs) | ✅ clear, VIX 18.4 |

## Q4 — Entry Confluence
**PRIMARY SHORT (spot inside zone, price rising into it — no bearish reversal):**
| | Pts | Result |
|---|---|---|
| E0 reversal confirm | 3.0 | ❌ last 4 H1 bars bullish continuation, no bearish turn |
| E1 D1 osc extreme (overbought) | 2.5 | ❌ RSI 45.1/Stoch 72.8, not extreme |
| E2 H1 osc extreme | 1.5 | ❌ neutral |
| E3 non-trend ADX<25 | 1.0 | ❌ ADX 40.7 |
| E4 structure intact | 1.0 | ✅ |
| E5 compression holds | 1.0 | ❌ expanding |
| **Total** | **1.0/10** | below floor |

**COUNTER LONG 1.3140-1.3180:** zone unreached (spot 1.33605, ~425 pips above) → EC 0.0.

## Result
### ❌ NO TRADE (both zones)
```
PRIMARY SHORT 1.3340-1.3390: NO TRADE — EC 1.0/10 < 5.0 (price inside zone but bullish
continuation, no reversal confirm, D1 ADX 40.7 strong trend against fade).
COUNTER LONG 1.3140-1.3180: NO TRADE — zone unreached.
Both PENDING, V1b intact.
```

## Hourly recheck — 03:07 UTC
Spot 1.33597 (unchanged), ADX still elevated. EC unchanged (COUNTER 0.0, zone unreached).
PRIMARY already RESOLVED this week (zone_outcome LOSS_SL -1.0R, 07-02) — only COUNTER remains OPEN.
NO TRADE unchanged.

## Hourly recheck — 04:07 UTC (automated)
Spot 1.33603 (H4 close) | H4_ATR 0.0033 | D1_ATR 0.00824 (median 0.00787, expanding). CB calendar
clear. Econ calendar: Forex Factory feed down (fetch failure) — Fri into weekend/Jul-4 holiday, low
release-risk regardless. COUNTER LONG 1.3140-1.3180 still unreached (spot ~0.018 above zone top).
V1b intact. trade_outcome replay: COUNTER PENDING, no EC (zone untouched). **COUNTER: NO TRADE —
zone unreached.** Ledger: NO_TRADE, lock cleared. PENDING.

## Hourly recheck — 05:07 UTC (automated)
Spot 1.33660 (H4 close) | H4_ATR 0.0033 | D1_ATR 0.00824 (median 0.00787, expanding). CB calendar
clear. Econ calendar: no HIGH releases in window. COUNTER LONG 1.3140-1.3180 still unreached (spot
~0.019 above zone top). V1b intact. EC unchanged (0.0, zone untouched). PRIMARY remains already
RESOLVED this week (LOSS_SL -1.0R, unaffected). Ledger: NO_TRADE, lock cleared. **NO TRADE — zone
unreached.**

## Hourly recheck — 07:07 UTC (automated)
Spot 1.33651 (H4 close) | H4_ATR 0.0033 | D1_ATR 0.00824 (median 0.00787, expanding). CB calendar
clear. Econ calendar: no HIGH releases in window. V1b intact (threshold 1.31340, last 2 H4 closes
1.33618/1.33651, both far above). COUNTER LONG 1.3140-1.3180 still unreached (spot ~0.0185 above
zone top). **Programmatic EC (entry_confluence.py) = 2.0/10**: E0 ❌ | E1 D1 osc extreme ❌ | E2 H1
osc extreme ❌ | E3 ADX<25 ✅ (below internal threshold per script) | E4 structure intact ✅ | E5 ATR
compression ❌. Below floor regardless of zone distance. **COUNTER: NO TRADE — EC 2.0/10, zone
unreached.** Ledger: NO_TRADE (soft), lock cleared. PENDING.

## Hourly recheck — 08:07 UTC (automated)
Spot 1.32475 (D1 close). H4_ATR 0.00281 | D1_ATR 0.00809 (median 0.00754, EXPANDING). CB calendar
clear 07-03→07-05. Econ calendar EXIT-1 stale (coverage ends 07-03, window to 07-05). V1b intact
(threshold 1.31340, closes 1.33724/1.33709 well above). DGS2 4.17% (was 4.14%, 20d slope +0.0074
rising). DXY 1w chg −0.26% (USD weak, clears LONG gate). VIX 16.59, no spike — LONG veto clear.
COUNTER LONG 1.3140-1.3180 still unreached (spot well above zone top). E0 absent. EC recomputed:
E0 0 + E1 1.0 (D1 RSI 35.8 recovering, borderline) + E2 0 (H4 Stoch 80.1 overbought, wrong side) +
E3 0 (ADX 27.5>25, trending) + E4 1.0 (zone/20d band intact) + E5 0 (ATR expanding) = **2.0/10**,
unchanged, below floor. **COUNTER: NO TRADE — EC 2.0/10, zone unreached.** Ledger: NO_TRADE (soft),
lock cleared. PENDING.

## Hourly recheck — 09:07 UTC (automated) — V1 INVALIDATION
Spot 1.33583 (D1 close), decisively above COUNTER LONG zone top 1.3180. **V1 hard block fires —
D1 close beyond zone → COUNTER 1.3140-1.3180 INVALIDATED.** Fade thesis dead; pair converted to
trend/breakout continuation, not a mean-reversion setup. CB calendar clear, econ EXIT-1 stale
(advisory), VIX veto clear (16.45), DXY-jump clear (+0.137 < 0.5). No active gbpusd zones remain
this week (PRIMARY already RESOLVED 07-02, COUNTER now INVALIDATED). Ledger: COUNTER INVALIDATED,
lock cleared. **Await re-forecast.**
