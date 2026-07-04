---
type: daily_validation
instrument: gbpusd
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
e2: true
e3: false
e4: true
e5: false
entry_confluence_score: 2.5
zone_confluence_score: 7.0
e0_pattern: none
anchor_type: N/A
anchor_price: 0.00000
h4_atr: 0.00314
d1_atr: 0.00776
d1_atr_compressed: false
sl_distance: 0.00390
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
adx_val: 25.0
---

# Validation — 2026-07-02 (PRIMARY + COUNTER zones from [[2026-W27]])

*Rerun 06:15 UTC — spot refreshed, verdict unchanged (V3 NFP block still active).*

## Market Snapshot
| | Value | Note |
|---|---|---|
| Spot | 1.32475 | between zones (SHORT 1.3340–1.3390 above; LONG 1.3140–1.3180 below) |
| H4 ATR | 0.00281 | — |
| D1 ATR | 0.00809 | expanding vs median 0.00754 |
| VIX | 16.45 (stale) | veto suspended |

## Q1+Q2 — Hard Blocks

### Zone A: SHORT 1.3340–1.3390 (PRIMARY, ZC 7.0)
| Block | Result | Note |
|---|---|---|
| V1 | ✅ intact | D1 close 1.32893 below zone |
| **V3 — NFP** | ❌ **NO TRADE** | US NFP @ 12:30 UTC (within 2h of 13:00 NYC open) |

### Zone B: COUNTER LONG 1.3140–1.3180 (ZC 6.0)
| Block | Result | Note |
|---|---|---|
| V1 | ✅ intact | spot 1.32893 above zone — zone below current price |
| **V3 — NFP** | ❌ **NO TRADE** | US NFP @ 12:30 UTC |

## Result
```
Zone A (SHORT 1.3340–1.3390): NO TRADE — V3 hard block: US NFP 12:30 UTC
Zone B (LONG 1.3140–1.3180): NO TRADE — V3 hard block: US NFP 12:30 UTC
```
Both zones PENDING. Spot 1.32893 mid-range between zones.

## Rerun 07:15 UTC (automated hourly)
Spot 1.32475 (H4 close) | H4_ATR 0.00281 | D1_ATR 0.00809 (median 0.00754, expanding) | DGS2/VIX stale (last 06-30) | DXY 101.206 (+0.06 vs baseline, no jump gate — direction check not against either zone). CB calendar clear. Econ calendar EXIT-1 stale coverage but NFP 12:30 UTC confirmed — V3 hard block holds (within 2h of 13:00 UTC NY open). V1b intact both zones. No E0 either direction. **Both zones unchanged: NO TRADE — V3 NFP hard block.** PENDING.

## Rerun 08:07 UTC (automated hourly)
Spot 1.33514 (D1 close) | H4_ATR 0.00292 | D1_ATR 0.00776 (median 0.00773, slightly expanded) | DXY jump -0.325 (falling). NFP 12:30 UTC still ahead — V3 hard block holds. V1/V1b intact both zones (SHORT close inside zone floor-mid, not breached; LONG above zone as expected). No E0 either direction/zone. **Both zones NO TRADE — V3 NFP hard block.** Ledger CANCEL (hard-block), lock cleared. PENDING.

## Rerun 09:07 UTC (automated hourly)
Spot 1.33478 (D1 close) — now INSIDE PRIMARY SHORT zone 1.3340-1.3390. NFP 12:30 UTC within 2h of NY open → V3 event-window hard block overrides regardless of zone touch/EC. COUNTER LONG 1.3140-1.3180 unreached. Ledger: NO_TRADE (hard-block) both zones, lock cleared. PENDING — watch for E0 post-NFP once window clears (~15:00 UTC).

## Rerun 10:07 UTC (automated hourly)
Spot 1.33423 (D1 close) — still touching PRIMARY SHORT zone 1.3340-1.3390 (near bottom). H4_ATR 0.00296 | D1_ATR 0.00810 (median 0.00787). NFP 12:30 UTC still ahead — V3 event-window hard block holds regardless of zone touch. V1/V1b intact both zones (H4 closes 1.33423/1.33373). No E0 either direction. COUNTER LONG 1.3140-1.3180 unreached. **Both zones NO TRADE — V3 NFP hard block.** Ledger: NO_TRADE (hard-block), lock cleared. PENDING — watch for E0 post-NFP once window clears (~15:00 UTC).

## Rerun 11:12 UTC (automated hourly)
Spot 1.33272 (H4) | H4_ATR 0.00292 | D1_ATR 0.00776 (median 0.00773) | DGS2 4.09% | DXY 101.045. PRIMARY SHORT 1.3340-1.3390: spot 68pips below zone bottom, approaching, not yet touching. COUNTER LONG 1.3140-1.3180: spot ~950pips above, unreached. NFP 12:30 UTC within 2h of 13:00 UTC NY open — V3 event-window hard block holds both zones. V1/V1b intact (H4 closes 1.33373/1.33272, threshold 1.33960). **Both zones unchanged: NO TRADE — V3 NFP hard block.** Ledger: CANCEL (hard-block), lock cleared. PENDING.

## Rerun 13:15 UTC (automated hourly)
NFP printed 12:30 UTC — cable spiked, H1 13:00 close 1.33664, now INSIDE PRIMARY zone 1.3340-1.3390. V3 window CLEARED (past 13:00 cutoff) — scored EC live. **PRIMARY: E0 FAIL** (13:00 1H candle: open 1.33675/close 1.33664, tiny body, no bearish pin ≥2.5x tail or engulf of the prior big bullish 12:00 candle). **E1 FAIL** (D1 RSI 54.6, Stoch 49.0 — neither extreme, no overbought fade condition). E2 H1 RSI 71.7>65 PASS (1.5). E3 D1 ADX 24.99<25 PASS (1.0, borderline). E4 D1 close 1.33664 still below 20d high 1.34838 — band intact PASS (1.0). E5 D1 ATR 0.00822 > 20d median 0.00787 — NOT compressed, FAIL. **PRIMARY: NO TRADE — EC 3.5/10, floor miss (no E0, D1 oscillator not extreme).** COUNTER LONG 1.3140-1.3180 unreached (spot 1.33664 well above). Ledger: NO_TRADE (soft, no hard-block), lock=none. Both zones remain PENDING.

## Rerun 14:07 UTC (automated hourly)
Spot 1.33795 (H4 close), deeper inside PRIMARY zone 1.3340-1.3390. V3 window clear. V1/V1b intact (H4 closes 1.33117/1.33795, threshold 1.33960). DXY jump **-0.663** — exceeds 0.5 threshold **AGAINST** the short (USD weakening = cable strength = against SHORT thesis). **DXY-jump hard block triggers: PRIMARY NO TRADE.** COUNTER LONG 1.3140-1.3180 unreached (spot well above). **PRIMARY: NO TRADE — DXY-jump hard block (>0.5 against zone).** Ledger: CANCEL (hard-block), lock cleared. Both zones PENDING.

## Rerun 15:18 UTC (automated hourly)
Fresh recompute (bypassed frozen weekly_pull.txt, read live DB): spot 1.33711 (H4 close) | H4_ATR 0.00314 | D1_ATR 0.00776 (median 0.00773, not compressed) | DGS2 4.14 (slope +0.09) | DXY 100.761, jump **-0.629** (still exceeds 0.5 threshold) | VIX 16.59 (spike +0.14, no veto). D1 last 6 closes (06-24→07-01) all below 1.3340 — V1 intact. V1b: SHORT threshold 1.33960 vs last 2 H4 closes 1.33117/1.33711 → ✅ intact. LONG threshold 1.31340, spot far above → ✅ intact. CB calendar clear. Econ calendar: NFP/AHE/Unemployment printed 12:30 UTC — now 15:18 UTC, event window (±30min = 12:00-13:00) has passed, V3 event-window clear.

**DXY-jump direction check (per coordinator note):** jump -0.629 = USD weakening. AGAINST PRIMARY SHORT (short GBPUSD = long USD thesis) → **hard block confirmed on PRIMARY**. WITH COUNTER LONG (long GBPUSD = short USD thesis) → **no block on COUNTER**; COUNTER fails on EC floor instead (zone unreached, spot 1.33711 is ~1900 pips above the 1.3140-1.3180 box).

Live oscillator recompute (fresh, not the stale frozen-pull D1-oversold reading): **D1 now neutral** (RSI 46.9, Stoch 71.8/49.5, W%R -28.2, CCI 36.3 — the oversold bounce already resolved into mid-range) | **H4 overbought** (RSI 75.5, Stoch 92.9/85.9, W%R -7.1, CCI 225.6) | **H1 overbought** (RSI 73.8, Stoch 88.1/91.8, W%R -11.9, CCI 123.9). D1 ADX 25.0 (borderline, fails <25 strictly).

**PRIMARY SHORT 1.3340-1.3390 (spot 1.33711, inside zone):** E0 ❌ (last closed H1 14:00 candle: body 0.00006, small bullish lean, no bearish pin/engulf — no reversal-down signal) · E1 ❌ (D1 RSI 46.9 not overbought-extreme) · E2 ✅ 1.5 (H1 RSI 73.8>65, Stoch>80) · E3 ❌ (ADX 25.0, not <25) · E4 ✅ 1.0 (zone/structure intact) · E5 ❌ (D1 ATR 0.00776 > median 0.00773, not compressed). **EC = 2.5/10, floor miss.** Plus DXY-jump hard block (-0.629 against). **PRIMARY: NO TRADE — DXY-jump hard block + EC 2.5<5.0 floor.**

**COUNTER LONG 1.3140-1.3180 (spot 1.33711, zone unreached):** All E1/E2 fail (oscillators overbought not oversold), E3 fails (ADX 25.0), E4 pass (structure intact), E5 fail (not compressed), E0 fail (no signal — price not at zone). **EC ≈1.0/10, floor miss.** No DXY block (jump is WITH this direction) but irrelevant — EC floor miss stands. **COUNTER: NO TRADE — EC 1.0<5.0 floor, zone unreached.**

**Both zones: NO TRADE.** PRIMARY hard-blocked (DXY) + floor miss; COUNTER floor miss (unreached). PENDING, unchanged.
