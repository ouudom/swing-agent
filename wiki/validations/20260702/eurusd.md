---
type: daily_validation
instrument: eurusd
date: 2026-07-02
week: 2026-W27
active_zone: PRIMARY
v1_structure_intact: true
v1b_intact: true
v3_news_clear: false
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
anchor_price: 0.00000
h4_atr: 0.00222
d1_atr: 0.00623
d1_atr_compressed: false
sl_distance: 0.00260
offset: 0.00
order_limit: NO_TRADE
limit_price: 0.00000
limit_direction: N/A
limit_expires: N/A
tp1_price: 0.00000
tp2_price: 0.00000
be_trigger_r: 1.5
dfii10_now: 0.0
dfii10_baseline: 0.0
dfii10_slope: 0.0
dxy_slope: 0.0
adx_val: 0.0
---

# Validation — 2026-07-02 (PRIMARY + SECONDARY zones from [[2026-W27]])

*Rerun 06:15 UTC — spot refreshed, verdict unchanged (V3 NFP block still active).*

## Market Snapshot
| | Value | Note |
|---|---|---|
| Spot | 1.14193 | below both zones (1.1450–1.1490, 1.1500–1.1545) |
| H4 ATR | 0.00260 | — |
| D1 ATR | 0.00642 | expanding vs median 0.00575 |
| VIX | 16.45 (2026-06-30) | **stale — veto suspended** |

## Q1+Q2 — Hard Blocks

### Zone A: SHORT 1.1450–1.1490 (PRIMARY, ZC 7.0)
| Block | Result | Note |
|---|---|---|
| V1 | ✅ intact | spot 1.13860 — price pulled away from zone |
| V1b | ✅ intact | H4 closes below zone |
| **V3 — NFP** | ❌ **NO TRADE** | US NFP + AHE + URate @ 12:30 UTC (within 2h of 13:00 NYC open) |

### Zone B: SHORT 1.1500–1.1545 (SECONDARY, ZC 6.5)
Same V3 block. NO TRADE.

## Result
```
Zone A (SHORT 1.1450–1.1490): NO TRADE — V3 hard block: US NFP 12:30 UTC
Zone B (SHORT 1.1500–1.1545): NO TRADE — V3 hard block: US NFP 12:30 UTC
```
Both zones PENDING. Spot 1.13860 has retreated significantly below zones. Review at /weekly W28 if zones not touched.

## Rerun 07:07 UTC (automated hourly)
Spot 1.14193 (unchanged) | H4_ATR 0.00260 | D1_ATR 0.00642 (median stale, expanding) | DGS2 4.09% (stale, last 06-30, no macro flip). CB calendar clear. Econ calendar EXIT-1 stale coverage but NFP 12:30 UTC confirmed — V3 hard block holds (event within 2h of 13:00 UTC NY open). V1b intact both zones. No E0 toward SHORT. **Both zones unchanged: NO TRADE — V3 NFP hard block.** PENDING.

## Rerun 08:07 UTC (automated hourly)
Spot 1.14171 (D1 close) | H4_ATR 0.00223 | D1_ATR 0.00623 (not compressed) | DGS2 4.14% (baseline 4.09, +0.09 drift — no flip trigger) | DXY jump -0.325 (falling, WITH SHORT bias, no gate). NFP 12:30 UTC still within 2h of NY open — V3 hard block holds. V1/V1b intact both zones. No E0 either direction. **Both zones NO TRADE — V3 NFP hard block.** Ledger CANCEL (hard-block), lock cleared. PENDING.

## Rerun 09:07 UTC (automated hourly)
Spot 1.14113 (D1 close). NFP 12:30 UTC within 2h of NY open → V3 event-window hard block holds both zones (SHORT 1.1450-1.1490, 1.1500-1.1545), spot well below, unreached. Ledger: NO_TRADE (hard-block), lock cleared. PENDING.

## Rerun 10:07 UTC (automated hourly)
Spot 1.14100 (D1 close) | H4_ATR 0.00217 | D1_ATR 0.00633 (median 0.00624, not compressed). NFP 12:30 UTC still ahead — V3 event-window hard block holds (within 2h of 13:00 UTC NY open). V1/V1b intact both zones (H4 closes 1.14100/1.14088). No E0 toward SHORT. **Both zones unchanged: NO TRADE — V3 NFP hard block.** Ledger: NO_TRADE (hard-block), lock cleared. PENDING.

## Rerun 11:12 UTC (automated hourly)
Spot 1.14076 (H4) | H4_ATR 0.00223 | D1_ATR 0.00623 (median 0.00623) | DGS2 4.09% | DXY 101.054. Both zones (1.1450-1.1490, 1.1500-1.1545) unreached, spot ~40-90pips below. NFP 12:30 UTC within 2h of 13:00 UTC NY open — V3 event-window hard block holds. V1/V1b intact. **Both zones unchanged: NO TRADE — V3 NFP hard block.** Ledger: CANCEL (hard-block), lock cleared. PENDING.

## Rerun 13:15 UTC (automated hourly)
NFP printed 12:30 UTC — spike wicked into PRIMARY zone intrabar (H1 12:00 bar high 1.14730 > 1.1450 floor) but H1 13:00 candle closed back below at 1.14487 — no 1H close inside zone, no EC scoring triggered. V3 window cleared (past 13:00). V1/V1b intact both zones. **Both zones unchanged: NO TRADE — no qualifying 1H close in zone.** Ledger untouched (no verdict change). PENDING — watch next hour, spot sitting right at zone floor.

## Rerun 14:07 UTC (automated hourly)
Spot 1.14539 (H4 close) — now closing INSIDE PRIMARY zone 1.1450-1.1490 (14:00 1H close 1.14539). V3 window fully clear. V1/V1b intact (H4 closes 1.14006/1.14539, threshold 1.14950). DXY jump **-0.663** (101.39→100.727) — exceeds 0.5 threshold **AGAINST** the short (USD weakening = EUR strength = against SHORT thesis). **DXY-jump hard block triggers: PRIMARY NO TRADE.** DGS2 4.14% (baseline 4.09, +0.05 drift, below 0.15 re-forecast threshold). SECONDARY 1.1500-1.1545 unreached (spot below). **PRIMARY: NO TRADE — DXY-jump hard block (>0.5 against zone).** Ledger: CANCEL (hard-block), lock cleared. Both zones PENDING.

## Rerun 15:13 UTC (automated hourly — full recompute, not trusting prior read)
DB guard ok (backup index_20260702_151323.db.gz). CB calendar clear (window 07-02→07-04). Econ calendar: NFP/AHE/URate 12:30 UTC printed — current time 15:13 UTC, ±30min window (12:00-13:00) long past, V3 event-window clear. Fresh data pull: spot 1.14454 (H4 close), H4_ATR 0.00222, D1_ATR 0.00623 (median 0.00623, not compressed). DGS2 4.14% (baseline 4.09, drift +0.05, below 0.15 re-forecast threshold — no flip). **DXY jump -0.645** (101.39→100.745) — still exceeds 0.5 threshold **AGAINST** both SHORT zones (USD weakening persists, not a stale read — confirmed fresh). VIX 16.59 (2026-07-01, 1-day lag; spike +0.14, no veto — LONGs-only gate n/a for SHORT zones anyway).

### Zone A: SHORT 1.1450–1.1490 (PRIMARY)
V1 ✅ intact (spot 1.14454 inside zone, no D1 close beyond) | V1b ✅ intact (H4 closes 1.14006/1.14454, threshold 1.14950) | V3 ✅ clear (NFP window passed) | **DXY-jump hard block ❌** (-0.645 against SHORT thesis) → **NO TRADE**, hard-block, EC not scored.

### Zone B: SHORT 1.1500–1.1545 (SECONDARY)
V1 ✅ intact (spot below zone, unreached) | V1b ✅ intact | V3 ✅ clear | **DXY-jump hard block ❌** (same -0.645, applies to all eurusd SHORT zones today) → **NO TRADE**, hard-block, EC not scored.

**Both zones: NO TRADE — DXY-jump hard block (>0.5 against zone), confirmed fresh at 15:13 UTC.** Ledger: CANCEL (hard-block), lock cleared. Both zones remain PENDING.
