---
type: daily_validation
instrument: usdchf
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
e2: true
e3: true
e4: false
e5: true
entry_confluence_score: 3.5
order_limit: NO_TRADE
limit_price: 0000.00
limit_direction: N/A
h4_atr: 0.00185
d1_atr: 0.00501
d1_atr_compressed: true
dxy_slope: 0.677
adx_val: 35.0
---

# Validation — 2026-07-03 (PRIMARY zone from [[2026-W27]])

## Market Snapshot
| | Value |
|---|---|
| Spot | 0.80287 — ~8 pips above zone top 0.8020 |
| H4 ATR | 0.00185 |
| D1 ATR | 0.00501 (median 0.00524 → compressed) |
| DGS2 4.14% (baseline 4.09, +0.05 drift, no flip) | DXY 20d slope +0.677 (LONG-aligned) |
| D1 ADX 35.0 (LONG fades exempt from ADX>30 veto per constitution) |

## Q1+Q2 — Hard Blocks
| | Result |
|---|---|
| V1/V1b (buf 0.0004) | ✅ intact, closes 0.80448/0.80287 |
| V3 | ✅ clear (Swiss CPI + NFP already cleared) |

## Q4 — Entry Confluence
| | Pts | Result |
|---|---|---|
| E0 RSI-reclaim | 3.0 | ❌ zone unreached, no fresh H1 reversal |
| E1 H1 osc extreme | 2.5 | ❌ stale (last extreme Jun 29, no retest) |
| E2 DXY slope aligned | 1.5 | ✅ +0.677 |
| E3 squeeze/calm | 1.0 | ✅ D1 ATR compressed |
| E4 ADX<25 | 1.0 | ❌ 35.0 (exempt from hard veto, still no EC pt) |
| E5 structure intact | 1.0 | ✅ |
| **Total** | **3.5/10** | below floor |

## Result
### ❌ NO TRADE
```
PRIMARY LONG 0.7990-0.8020: NO TRADE — zone unreached (spot 8 pips above top) + EC 3.5/10 < 5.0.
DXY slope/compression/structure favorable but E0 not fired. PENDING.
```

## Hourly recheck — 03:07 UTC
PRIMARY zone RESOLVED this week (zone_outcome WIN_TP1 +2.5R, midpoint touch 07-02) — zero OPEN
zones remain for usdchf this week. No further validation needed; _HOT.md updated to drop it.
