---
type: daily_validation
instrument: eurgbp
date: 2026-07-03
week: 2026-W27
active_zone: NONE
v1_structure_intact: false
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
e4: false
e5: false
entry_confluence_score: 0.0
zone_confluence_score: 0.0
e0_pattern: none
anchor_type: N/A
order_limit: INVALIDATED
limit_price: 0000.00
limit_direction: N/A
h4_atr: 0.00121
d1_atr: 0.0028
d1_atr_compressed: false
adx_val: 22.9
---

# Validation — 2026-07-03 (SECONDARY zone from [[2026-W27]])

## Market Snapshot
| | Value | vs Baseline |
|---|---|---|
| Spot | 0.85629 (D1 close) | ~900 pips below zone |
| D1 close 07-01 | 0.85685 | first breach of W28 flag |
| D1 close 07-02 | 0.85639 | |
| D1 close 07-03 | 0.85629 | 3 consecutive closes < 0.8580 |
| H4 ATR | 0.00121 | — |
| D1 ATR | 0.0028 | median 0.0026 → expanding |
| D1 ADX(14) | 22.9 | transitional, no fade-veto |

## Q1+Q2 — Hard Blocks
| | Block | Result | Note |
|---|---|---|---|
| V1 | D1 close beyond zone | — | never touched zone |
| **W28 pre-set flag** | D1 close < 0.8580 → void SHORT zone | ❌ **TRIGGERED** | closes 0.85685/0.85639/0.85629 all < 0.8580, 3 consecutive |
| V1b (0.8675-0.8710, buf 0.0004) | 2 consec H4 closes > 0.8714 | ✅ intact (moot) | closes 0.856xx |
| V3 | Hard news within 2h | ✅ clear | no ECB/BoE/tier-1 in window |

## Result
### ❌ INVALIDATED
```
INVALIDATED — pre-set W28 forecast flag triggered: D1 close < 0.8580 confirmed 3 consecutive
bars (07-01/07-02/07-03), squeeze broke down against the SHORT thesis. Zone 0.8675-0.8710 void.
Removed from _HOT.md pending list.
```

Prior LONG 0.8595-0.8620 zone was already INVALIDATED 07-02 (V1). No active eurgbp zones remain
for W27.
