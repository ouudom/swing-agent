---
type: system
updated: 2026-07-04
confidence: low
tags: [calibration, edge-validation, shadow-ledger]
related: [zone_outcomes, zone_ledger, constitution]
---

# Calibration — Edge Performance

> **AUTO-GENERATED** by `scripts/calibration.py` at 2026-07-04 05:13Z. Do not hand-edit — re-run the script. Source: `data/database/index.db` (`zone_outcome`/`trade_outcome` tables).

Zones tracked: **54** · completed shadow trades: **31** · invalidated-before-fill (capital saved): **0** · min-n for verdicts: **10**.

## Overall (completed shadow trades)

n=31 · win 39% · +17.0R (avg +0.55) · **WORKING**

## Status mix (all tracked zones)

| status | count |
|---|---|
| NO_TOUCH | 13 |
| LOSS_SL | 13 |
| WIN_TP1 | 12 |
| PENDING | 7 |
| BREAKEVEN | 6 |
| RUNNING | 3 |

> INVALIDATED before fill = the system refused a zone that later broke its kill level — a capital-saving outcome, not a loss.

### By R1 confluence bucket

| R1 confluence bucket | n | win% | total R | avg R | verdict |
|---|---|---|---|---|---|
| 7.0–7.9 | 12 | 25% | +1.5 | +0.12 | WORKING |
| <7.0 | 16 | 50% | +13.0 | +0.81 | WORKING |
| >=8.0 | 3 | 33% | +2.5 | +0.83 | INSUFFICIENT (n<10) |

### By instrument

| instrument | n | win% | total R | avg R | verdict |
|---|---|---|---|---|---|
| audusd | 3 | 67% | +5.0 | +1.67 | INSUFFICIENT (n<10) |
| eurgbp | 3 | 33% | +0.5 | +0.17 | INSUFFICIENT (n<10) |
| eurusd | 5 | 20% | +0.5 | +0.10 | INSUFFICIENT (n<10) |
| gbpjpy | 2 | 50% | +1.5 | +0.75 | INSUFFICIENT (n<10) |
| gbpusd | 6 | 17% | -0.5 | -0.08 | INSUFFICIENT (n<10) |
| nzdusd | 4 | 50% | +3.0 | +0.75 | INSUFFICIENT (n<10) |
| usdchf | 5 | 40% | +3.0 | +0.60 | INSUFFICIENT (n<10) |
| usdjpy | 1 | 0% | -1.0 | -1.00 | INSUFFICIENT (n<10) |
| xauusd | 2 | 100% | +5.0 | +2.50 | INSUFFICIENT (n<10) |

### By direction

| direction | n | win% | total R | avg R | verdict |
|---|---|---|---|---|---|
| LONG | 14 | 29% | +2.0 | +0.14 | WORKING |
| SHORT | 17 | 47% | +15.0 | +0.88 | WORKING |

### By conviction

| conviction | n | win% | total R | avg R | verdict |
|---|---|---|---|---|---|
| MEDIUM | 22 | 41% | +15.5 | +0.70 | WORKING |
| MEDIUM-HIGH | 3 | 67% | +4.0 | +1.33 | INSUFFICIENT (n<10) |
| MEDIUM-LOW | 6 | 17% | -2.5 | -0.42 | INSUFFICIENT (n<10) |

### By fill session

| fill session | n | win% | total R | avg R | verdict |
|---|---|---|---|---|---|
| Asia | 9 | 56% | +9.5 | +1.06 | INSUFFICIENT (n<10) |
| London | 15 | 40% | +9.0 | +0.60 | WORKING |
| NY | 7 | 14% | -1.5 | -0.21 | INSUFFICIENT (n<10) |

### By instrument × direction

| instrument | dir | n | win% | total R | verdict |
|---|---|---|---|---|---|
| audusd | LONG | 2 | 50% | +2.5 | INSUFFICIENT (n<10) |
| audusd | SHORT | 1 | 100% | +2.5 | INSUFFICIENT (n<10) |
| eurgbp | LONG | 2 | 0% | -2.0 | INSUFFICIENT (n<10) |
| eurgbp | SHORT | 1 | 100% | +2.5 | INSUFFICIENT (n<10) |
| eurusd | LONG | 2 | 0% | -2.0 | INSUFFICIENT (n<10) |
| eurusd | SHORT | 3 | 33% | +2.5 | INSUFFICIENT (n<10) |
| gbpjpy | LONG | 1 | 100% | +2.5 | INSUFFICIENT (n<10) |
| gbpjpy | SHORT | 1 | 0% | -1.0 | INSUFFICIENT (n<10) |
| gbpusd | LONG | 2 | 0% | -1.0 | INSUFFICIENT (n<10) |
| gbpusd | SHORT | 4 | 25% | +0.5 | INSUFFICIENT (n<10) |
| nzdusd | LONG | 3 | 33% | +0.5 | INSUFFICIENT (n<10) |
| nzdusd | SHORT | 1 | 100% | +2.5 | INSUFFICIENT (n<10) |
| usdchf | LONG | 2 | 50% | +1.5 | INSUFFICIENT (n<10) |
| usdchf | SHORT | 3 | 33% | +1.5 | INSUFFICIENT (n<10) |
| usdjpy | SHORT | 1 | 0% | -1.0 | INSUFFICIENT (n<10) |
| xauusd | SHORT | 2 | 100% | +5.0 | INSUFFICIENT (n<10) |

## R2 — Entry Confluence (trade_outcome replay)

Replayed fills: completed **23** · LIMIT_MISSED (offset never reached = D030 near-miss) **7** · min-n **10**.

n=23 · win 30% · +8.0R (avg +0.35) · **WORKING**

### By Entry Confluence (EC) bucket

| EC bucket | n | win% | total R | avg R | verdict |
|---|---|---|---|---|---|
| >=8.0 | 9 | 22% | -1.0 | -0.11 | INSUFFICIENT (n<10) |
| 6.5–7.9 | 9 | 33% | +4.0 | +0.44 | INSUFFICIENT (n<10) |
| 5.0–6.4 | 3 | 67% | +7.0 | +2.33 | INSUFFICIENT (n<10) |
| <5.0 (sub-floor) | 2 | 0% | -2.0 | -1.00 | INSUFFICIENT (n<10) |

### Gate accuracy (was the block correct?)

> Counterfactual: each zone is filled in replay **despite** the gate. A gate KEEPS EDGE when its blocked trades net ≤0R (loss avoided); COSTING EDGE when they net >0R (winner refused). Replaces the old unverified "INVALIDATED = capital saved" assumption.

| gate | n blocked | would-be win% | would-be total R | verdict |
|---|---|---|---|---|
| V1 | 4 | 0% | -4.0 | INSUFFICIENT (n<10) |
| V1b | 8 | 0% | -7.0 | INSUFFICIENT (n<10) |
| V3 | 10 | 50% | +6.0 | INSUFFICIENT (n<10) |
| VETO_VIX | 0 | — | — | INSUFFICIENT |
| VETO_ADX | 1 | — | — | INSUFFICIENT |
| INTERVENTION | 0 | — | — | INSUFFICIENT |
| EC_FLOOR | 3 | 0% | -2.0 | INSUFFICIENT (n<10) |

> D030 offset watch: **7** zones filled at the zone midpoint in `zone_outcome` but the entry-mechanics offset limit was never reached — the offset is leaving fills (often the winners) on the table.

---
_Verdict logic: UNPROVEN/INSUFFICIENT until n≥min-n; then WORKING (total R>0) or DEAD (total R≤0). Low n = noise; treat WORKING/DEAD as directional, not final, below ~20 trades._
