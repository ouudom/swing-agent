---
type: daily_validation
instrument: gbpjpy
date: 2026-07-02
week: 2026-W27
active_zone: PRIMARY
v1_structure_intact: false
v1b_intact: false
v3_news_clear: true
vix_veto: false
vix_stale: true
reforecast_action: NONE
reforecast_triggers: []
e0_entry_confirmation: false
e1: false
e2: false
e3: false
e4: false
e5: false
entry_confluence_score: 0.0
zone_confluence_score: 7.0
e0_pattern: none
anchor_type: N/A
anchor_price: 0.000
h4_atr: 0.397
d1_atr: 1.113
d1_atr_compressed: false
sl_distance: 0.477
offset: 0.00
order_limit: INVALIDATED
limit_price: 0.000
limit_direction: N/A
limit_expires: N/A
tp1_price: 0.000
tp2_price: 0.000
be_trigger_r: 1.5
dfii10_now: 0.0
dfii10_baseline: 0.0
dfii10_slope: 0.0
dxy_slope: 0.0
adx_val: 15.3
---

# Validation — 2026-07-02 (PRIMARY SHORT + COUNTER LONG zones from [[2026-W27]])

*Rerun 06:15 UTC — spot pulled back to 214.485 (was 215.873), still at/above MoF level 214.0. HARD_BLOCK unchanged. PRIMARY stays INVALIDATED (V1b already triggered, not reversible intraday).*

## Market Snapshot
| | Value | Note |
|---|---|---|
| Spot | 214.485 | pulled back but still ≥ MoF level 214.0 |
| H4 ATR | 0.387 | — |
| D1 ATR | 1.093 | not compressed vs median 0.95 |
| VIX | 16.45 (stale) | veto suspended (DEAD for gbpjpy) |
| ADX D1 | 15.3 | ranging |
| MoF | HARD_BLOCK longs | spot 214.485 ≥ level 214.0; ambush-tactics shift confirmed |

## Q1+Q2 — Hard Blocks

### Zone A: PRIMARY SHORT 215.00–215.60 (ZC 7.0)
| Block | Result | Note |
|---|---|---|
| V1 | ⚠ borderline | D1 closes: 215.505 → 215.850 → 215.873. Yesterday + today above 215.60 zone top |
| **V1b** | ❌ **INVALIDATED** | 2 consecutive H4 closes (215.850 @ 00:00, 215.873 @ 04:00) both > threshold 215.650 (zone top 215.60 + buffer 0.05) |
| V3 | ✅ clear | No BoJ/BoE decisions; US NFP caution only |

### Zone B: COUNTER LONG 212.00–212.55 (ZC 6.0)
| Block | Result | Note |
|---|---|---|
| V1 | ✅ intact | spot far above zone |
| V1b | ✅ intact | H4 closes well above — threshold 211.950 not breached |
| **MoF HARD_BLOCK** | ❌ **NO TRADE** | spot 215.873 > intervention level 214.0; new longs blocked; ambush-tactics regime |
| V3 | ✅ clear | — |

## Q3 — Re-Forecast Check
No T1-T5 triggers for cross pair (macro dead). Squeeze was ON at weekly publication; D1+H4 squeeze may have fired upward (price broke above 215.6). Flag for W28 /weekly: if D1 close > 216.20 confirms upside break, void the SHORT zone and reassess. Current D1 close 215.873 < 216.20 — breakout not confirmed yet.

## Result
```
Zone A (SHORT 215.00–215.60): INVALIDATED — V1b breach: 2 consec H4 closes (215.850, 215.873) > threshold 215.650. Cancel any live limit.
Zone B (LONG 212.00–212.55): NO TRADE — MoF HARD_BLOCK (spot 215.873 > level 214.0; ambush regime active)
```
No active zones remain for GBPJPY. W28 /weekly to re-assess range vs upside break (invalidation level D1 close > 216.20).

## Rerun 09:07 UTC (automated hourly)
PRIMARY SHORT and old COUNTER LONG remain INVALIDATED / MoF HARD_BLOCK — no active zones this instrument. Ledger re-asserted NO_TRADE (hard-block) on COUNTER to keep lock cleared. No PENDING zones.
