---
type: daily_validation
instrument: eurusd
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
e3: false
e4: false
e5: true
entry_confluence_score: 2.5
order_limit: NO_TRADE
limit_price: 0000.00
limit_direction: N/A
h4_atr: 0.00236
d1_atr: 0.00652
d1_atr_compressed: false
dxy_slope: -0.02
adx_val: 53.9
---

# Validation — 2026-07-03 (PRIMARY + SECONDARY zones from [[2026-W27]])

## Market Snapshot
| | Value |
|---|---|
| Spot | 1.14390 |
| H4 ATR | 0.00236 |
| D1 ATR | 0.00652 (median 0.00630, expanding) |
| DGS2 | 4.17%, slope +0.09 |
| DXY 1d jump | -0.02 (not >0.5 against) |
| D1 ADX | 53.9 (strong downtrend, WITH short thesis) |

## Q1+Q2 — Hard Blocks
| | Result |
|---|---|
| V1/V1b | ✅ intact both zones |
| V3 | ✅ clear (US markets thin, Jul 4 observed) |
| DXY-jump >0.5 against | ✅ clear (-0.02) |

## Q4 — Entry Confluence
| | Pts | Result |
|---|---|---|
| E0 reversal confirm | 3.0 | ❌ no H1 pin/engulf/reclaim |
| E1 D1 osc extreme | 2.5 | ❌ RSI 53.5, Stoch 69.7 — not extreme |
| E2 H1 osc extreme | 1.5 | ✅ H1 RSI 67 |
| E3 non-trend ADX<25 | 1.0 | ❌ ADX 53.9 |
| E4 D1 ATR compressed | 1.0 | ❌ expanding |
| E5 structure intact | 1.0 | ✅ |
| **Total** | **2.5/10** | below floor |

## Result
### ❌ NO TRADE (both zones)
```
PRIMARY 1.1450-1.1490 + SECONDARY 1.1500-1.1545: NO TRADE — EC 2.5/10 < 5.0 floor.
V1/V1b intact, PENDING.
```

## Hourly recheck — 03:07 UTC
Spot 1.14385 (unchanged), DGS2 4.17, DXY jump +0.017 (clear). EC 2.5/10 unchanged. V1b intact.
PRIMARY zone already RESOLVED this week (zone_outcome BREAKEVEN, midpoint touch 07-02) — only
SECONDARY remains OPEN. NO TRADE unchanged.

## Hourly recheck — 04:07 UTC (automated)
Spot 1.14409 (H4 close) | H4_ATR 0.00243 | D1_ATR 0.00669 (median 0.00624, expanding). CB calendar
clear. Econ calendar: Forex Factory feed down (fetch failure) — Fri 07-03 into weekend/Jul-4
holiday, low release-risk regardless; DXY 100.801 (fresh refetch), 1d jump well below 0.5 threshold,
no DXY-jump gate. V1b intact (SECONDARY, unreached — spot ~0.011 below zone 1.1500-1.1545).
trade_outcome replay: SECONDARY still unreached, PENDING (no EC computed, oscillators not extreme).
**SECONDARY: NO TRADE — zone unreached.** Ledger: NO_TRADE, lock cleared. PENDING.

## Hourly recheck — 05:07 UTC (automated)
Spot 1.14498 (H4 close) | H4_ATR 0.00243 | D1_ATR 0.00669 (median 0.00624, expanding). CB calendar
clear. Econ calendar: no HIGH releases in window (US markets thin Jul-4 observed). DGS2 4.17
(slope +0.09), DXY jump -0.15 (well below 0.5 against-threshold). SECONDARY 1.1500-1.1545 still
unreached (spot ~0.005 below zone bottom). V1b intact. EC unchanged 2.5/10 (RSI/Stoch not extreme,
ADX 53.9 strong trend against fade). Ledger: NO_TRADE, lock cleared. **NO TRADE — zone unreached.**

## Hourly recheck — 07:07 UTC (automated) — ✅ ORDER LIMIT
Spot 1.14530 (H4 close) | H4_ATR 0.00243 | D1_ATR 0.00669 (median 0.00624, expanding, NOT
compressed). CB calendar clear. Econ calendar EXIT-1 stale (FF feed down); no known high-impact
EU/US releases this weekend regardless — US markets thin (Jul-4 observed, advisory only, not a V3
tag on this pair's calendar). V1b intact (threshold 1.15500, last 2 H4 closes 1.14416/1.14530).
DGS2 4.17 (slope +0.09, <0.15 no forced re-forecast). DXY jump -0.173 (<0.5, no block).

**Entry Confluence (programmatic, `entry_confluence.py`) — SECONDARY SHORT 1.1500-1.1545:**
E0 reversal confirm ❌ (no H1 pin/engulf/reclaim) | E1 H4 oscillator still extreme ✅ (Stoch/W%R/CCI
mid-to-overbought) | E2 H4 band touch ✅ | E3 non-trend ADX<25 ❌ (D1 ADX 34.7) | E4 ATR compression
❌ (expanding) | E5 structure intact ✅. **EC = 2.5+1.5+1.0 = 5.0/10 — floor met exactly.**

No E0 → anchor = 50% zone midpoint = 1.15225. SL = avg(0.5×D1ATR 0.00335, H4ATR 0.00243) = 0.00289.
offset = max(SL/3, (10-5.0)×0.2×SL) = 0.00289. limit = anchor + offset (SHORT) = **1.15514**.
SL price = 1.15803. TP1 (2.5R) = 1.14792 (manual). TP2 (3.0R) = 1.14647 (limit). BE @1.5R = 1.15080.

FX exposure check: `fx_exposure.py` — no other live FX orders today → **INDEPENDENT**, no netting concern.

```
EURUSD ORDER LIMIT: SELL 1.15514 | SL 1.15803 | TP1 2.5R 1.14792 (manual) | TP2 3.0R 1.14647 (limit) | BE @1.5R 1.15080 | expires 2026-07-03 21:00 UTC
Entry Confluence: 5.0/10 (E0:❌ E1:✅ E2:✅ E3:❌ E4:❌ E5:✅)
Anchor: 50% zone midpoint 1.15225 | SL 0.00289 | offset 0.00289 | R:R 2.5
"If price reaches 1.15514, order triggers. Cancel if not hit by 21:00 UTC."
```
Ledger: SECONDARY ORDER_LIMIT (no `--e0`, unlocked — re-derives next hour), EC 5.0.

## Hourly recheck — 08:07 UTC (automated)
Spot 1.14193 (well below zone, untouched). H4_ATR 0.0026 | D1_ATR 0.00642 (median 0.00575,
EXPANDING not compressed ❌). CB calendar clear 07-03→07-05. Econ calendar EXIT-1 stale (coverage
ends 07-03, window to 07-05). V1b intact (structure well clear of 1.1545 top). DGS2 4.09% (slope
+0.0074 rising) — DXY 1d jump −0.471 (USD weak, clears gate — jump is WITH short thesis not
against). E0 absent (H4 mid-range recovery, RSI 63, not a bearish reversal confirm). EC recomputed:
E0 0 + E1 1.0 (H4 mid, not extreme) + E2 0 (no band touch) + E3 0 (ADX 34.7>25, trending) + E4 0
(ATR expanding) + E5 1.0 (structure intact) = **3.0/10**, below floor — **verdict flips to NO
TRADE** (zone unlocked since no E0 ever fired, so fresh score governs). **SECONDARY: NO TRADE — EC
3.0/10 < 5.0 floor, no E0.** Ledger updated to NO_TRADE (soft), lock cleared — resting order limit
should be cancelled.

## Hourly recheck — 09:07 UTC (automated)
Spot 1.14193-1.14530 (recomputed). CB calendar clear. Econ calendar EXIT-1 stale (advisory,
US thin Jul-4). V1/V1b intact SECONDARY. DXY jump clear (WITH short thesis). E0 still absent
(H4 mid-range recovery, RSI 63, no bearish reversal confirm). D1 ATR expanding, ADX 53.9 trending
against fade. EC recomputed 3.0/10, unchanged, below floor. **SECONDARY: NO TRADE — EC 3.0/10.**
Ledger: NO_TRADE (soft), lock cleared. PENDING.

## Hourly recheck — 10:07 UTC (automated)
Spot 1.14432 (H4 close). H4_ATR 0.00251 | D1_ATR 0.00665 (median 0.00630, expanding, not
compressed). CB calendar clear 07-03→07-05. Econ calendar EXIT-1 stale (advisory, US thin Jul-4).
DGS2 4.17% (drift +0.08 vs baseline 4.09, below 0.15 flip threshold). DXY 1d jump −0.042, clear
(WITH short thesis). V1/V1b intact SECONDARY (threshold 1.1550, closes 1.14550/1.14432 well below);
D1 close 1.14432 < zone bottom 1.1500, unreached. E0: no pin/engulf on latest closed 1H (O 1.14419
→ C 1.14432). EC unchanged 3.0/10, below floor. **SECONDARY: NO TRADE — EC 3.0/10, zone unreached.**
Ledger: NO_TRADE (soft), lock cleared. PENDING.

## Hourly recheck — 11:07 UTC (automated)
Spot 1.14484 (H4 close). H4_ATR 0.00251. CB calendar clear 07-03→07-05. Econ calendar EXIT-1 stale
(coverage ends 07-03, window to 07-05) — unknown risk, advisory only. V1b SECONDARY (SHORT,
threshold 1.1550) intact — H4 closes 1.14550/1.14484 well below. D1 close 1.14484 < zone bottom
1.1500, unreached, V1 clear. E0: no pin/engulf on latest closed 1H (O 1.14478 → C 1.14484, tiny
body). EC unchanged 3.0/10, below floor. **SECONDARY: NO TRADE — EC 3.0/10, zone unreached.**
Ledger: NO_TRADE (soft), lock cleared. PENDING.

## Hourly recheck — 12:07 UTC (automated)
Spot 1.14484 (H4 close, unchanged from 11:07). H4_ATR 0.00251. CB calendar clear 07-03→07-05. Econ
calendar EXIT-1 still stale (FF feed capped at 07-03, refetch confirmed no change) — unknown risk,
advisory only. V1b SECONDARY (SHORT, threshold 1.1550) intact — H4 closes 1.14550/1.14484 well
below. D1 close 1.14484 < zone bottom 1.1500, unreached, V1 clear. E0: bull pin fired on latest
closed 1H — wrong direction for SHORT zone (mean-reversion needs bearish turn at resistance), no
count. EC unchanged 3.0/10, below floor. **SECONDARY: NO TRADE — EC 3.0/10, zone unreached.**
Ledger: NO_TRADE (soft), lock cleared. PENDING.

## Hourly recheck — 14:02 UTC (automated)
Spot 1.14407 (H4 close 12:00, drift down from 1.14484). H4_ATR ~0.0026. CB calendar clear
07-03→07-05 (re-verified). Econ calendar EXIT-1 still stale (FF feed capped at 07-03) — unknown
risk, advisory only. V1b SECONDARY (SHORT, threshold 1.1550) intact — H4 closes 1.14491/1.14407
well below. D1 zone 1.1500-1.1545 unreached. E0: prev closed 1H (13:00) O1.14479→C1.14388, bearish
body-dominant, no pin/engulf. EC unchanged 3.0/10, below floor. **SECONDARY: NO TRADE — EC 3.0/10,
zone unreached.** Ledger: NO_TRADE (soft), lock cleared. PENDING.

## Hourly recheck — 16:18 UTC (automated)
Spot 1.14392 (~flat vs 14:02). H4_ATR 0.00236 | D1_ATR 0.00652 (median 0.00630, expanding). CB
calendar clear 07-03→07-05. Econ calendar EXIT-1 still stale (FF feed capped at 07-03) — unknown
risk, advisory only. DXY 1d jump -0.01 (clear, WITH short thesis). D1 ADX 53.9 (strong trend, gates
E3). V1b SECONDARY (SHORT, threshold 1.1550) intact, well below. D1 zone 1.1500-1.1545 unreached,
gap ~110 pips. No pin/engulf/reclaim on latest closed 1H. EC unchanged 3.0/10, below floor.
**SECONDARY: NO TRADE — EC 3.0/10, zone unreached.** Ledger: NO_TRADE (soft), lock cleared. PENDING.
