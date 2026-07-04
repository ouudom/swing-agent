---
type: daily_validation
instrument: xauusd
date: 2026-07-02
week: 2026-W27
active_zone: PRIMARY
v1_structure_intact: true
v1b_intact: true
v3_news_clear: true
vix_veto: false
vix_stale: true
reforecast_action: NONE
reforecast_triggers: []
e0_entry_confirmation: false
e1: false
e2: true
e3: true
e4: true
e5: true
entry_confluence_score: 4.5
zone_confluence_score: 7.5
e0_pattern: none
anchor_type: N/A
anchor_price: 0.00
h4_atr: 40.92
d1_atr: 109.55
d1_atr_compressed: true
sl_distance: 54.78
offset: 0.00
order_limit: NO_TRADE
limit_price: 0.00
limit_direction: N/A
limit_expires: N/A
tp1_price: 0.00
tp2_price: 0.00
be_trigger_r: 1.5
dfii10_now: 2.20
dfii10_baseline: 2.23
dfii10_slope: 0.13
dxy_slope: 0.725
adx_val: 48.0
---

# Validation — 2026-07-02 (PRIMARY + SECONDARY zones from [[2026-W27]])

*Rerun 06:15 UTC — spot refreshed, verdict unchanged (V3 NFP block still active).*

## Market Snapshot
| | Value | Note |
|---|---|---|
| Spot | 4023.75 | below both zones (4120–4160, 4190–4220) |
| H4 ATR (trading) | 36.18 | — |
| D1 ATR | 124.66 | expanding vs median 115.99 |
| VIX | 16.45 (2026-06-30) | **stale (>1d lag) — veto suspended** |
| ADX(14) D1 | 48.0 | trending — from weekly |

## Q1+Q2 — Hard Blocks

### Zone A: SHORT 4120–4160 (PRIMARY, ZC 7.5)
| Block | Result | Note |
|---|---|---|
| V1 | ✅ intact | D1 close 4069.19 < 4120 — zone not breached from below |
| V1b | ✅ intact | H4 closes below zone |
| **V3 — NFP** | ❌ **NO TRADE** | US NFP + AHE + URate @ 12:30 UTC today — within 2h of 13:00 UTC NY open |
| VETO | ✅ N/A | VIX 16.45 << 35 (stale but well below) |

### Zone B: SHORT 4190–4220 (SECONDARY, ZC 6.5)
| Block | Result | Note |
|---|---|---|
| V3 — NFP | ❌ **NO TRADE** | same as Zone A |

## Q3 — Re-Forecast Check
No re-forecast triggers. Spot 4069 — price extended away from zones. T6 watch (DGS2 drift from 4.09) not reviewed (V3 block preempts).

## Result
```
Zone A (SHORT 4120–4160): NO TRADE — V3 hard block: US NFP at 12:30 UTC (within 2h of 13:00 UTC NY open)
Zone B (SHORT 4190–4220): NO TRADE — V3 hard block: US NFP at 12:30 UTC
```
Both zones PENDING. No order limits placed. Resume validation next session (07-03 or post-NFP).

## Rerun 07:12 UTC (automated hourly)
Spot 4070.42 (H4 close) | H4_ATR 43.23 | D1_ATR 109.55 (median 117.26, compressed) | D1 ADX 48.6 TRENDING | DFII10 2.20% (+0.04, rising — bearish gold). CB calendar clear. Econ calendar EXIT-1 stale coverage but NFP 12:30 UTC confirmed independently — V3 hard block holds (event within 2h of 13:00 UTC NY open, per established precedent this session). V1/V1b intact both zones (thresholds 4165.00 / 4225.00, last 2 H4 closes 4070.67/4070.42). E0: LONG-confirm pin fired (wrong direction, discounted) — no SHORT-confirm. **Both zones unchanged: NO TRADE — V3 NFP hard block.** PENDING.

## Rerun 08:07 UTC (automated hourly)
Spot 4067.99 (D1 close) | H4_ATR 44.1 | D1_ATR 109.55 (median 117.26, compressed). NFP+AHE+URate 12:30 UTC still ahead (within 2h of 13:00 UTC NY open) — V3 hard block holds. V1/V1b intact both zones. E0: no SHORT-confirm either zone. **Both zones NO TRADE — V3 NFP hard block.** Ledger CANCEL (hard-block), lock cleared. PENDING.

## Rerun 09:07 UTC (automated hourly)
Spot 4070.30 (D1 close, unchanged range). NFP still ahead (12:30 UTC) — within 2h of 13:00 UTC NY open → V3 event-window hard block holds for both zones (PRIMARY 4120-4160, SECONDARY 4190-4220), spot well below both, unreached anyway. Ledger: NO_TRADE (hard-block), lock cleared. PENDING.

## Rerun 10:07 UTC (automated hourly)
Spot 4063.82 (D1 close) | H4_ATR 40.7 | D1_ATR 108.28 (median 117.26, compressed). NFP+AHE+URate 12:30 UTC still ahead — V3 event-window hard block holds (within 2h of 13:00 UTC NY open). V1/V1b intact both zones (H4 closes 4063.82/4065.81, well below 4165.00 threshold). E0: LONG pin fired (wrong direction, discounted) — no SHORT-confirm. **Both zones unchanged: NO TRADE — V3 NFP hard block.** Ledger: NO_TRADE (hard-block), lock cleared. PENDING.

## Rerun 11:12 UTC (automated hourly)
Spot 4058.39 (D1) | H4_ATR 44.1 | D1_ATR 109.55 (median 117.26, compressed) | DFII10 2.19% | VIX 18.41. Both zones (4120-4160, 4190-4220) unreached, spot ~60-160pts below. NFP 12:30 UTC (78min away) within 2h of 13:00 UTC NY open — V3 event-window hard block holds. V1/V1b intact. **Both zones unchanged: NO TRADE — V3 NFP hard block.** Ledger: CANCEL (hard-block), lock cleared. PENDING.

## Rerun 13:15 UTC (automated hourly)
NFP printed 12:30 UTC — spot spiked hard: H4 12:00 bar high 4139.76, H1 13:00 close 4124.99987, now INSIDE PRIMARY zone 4120-4160. V3 event window CLEARED (13:00 cutoff passed) — scored EC live. **PRIMARY: E0 FAIL** (13:00 1H candle bullish continuation, no bearish engulf/pin/CHoCH toward short) — momentum still up off the NFP spike, wrong direction for short confirm. **E1 FAIL** (H4 structure now HH+HL — 07-02 12:00 bar made higher high 4139.76 > 07-01 12:00 high 4115.77 with higher low; short thesis needs LH+LL). E2 DFII10 20d slope +0.13 (rising, still supports short) PASS. E4 D1 ATR 112.57 < 20d median 117.26 (compressed) PASS. E0+E1 failures alone cap max available at 4.5/10 — below 5.0 floor regardless of remaining components. **PRIMARY: NO TRADE — EC ≈4.0/10, floor miss (no E0, structure flipped bullish).** SECONDARY 4190-4220 unreached (spot 4125 still 65pts below). Ledger: NO_TRADE (soft, no hard-block — EC gate not a gate failure), lock=none. Both zones remain PENDING.

## Rerun 14:07 UTC (automated hourly)
Spot 4130.54 (H4 close) | H4_ATR 40.92 | D1_ATR 109.55 (median 117.26, compressed) | DFII10 2.20% (slope20 +0.13) | DXY jump -0.66 | VIX 16.59. V3 window fully clear (NFP now 1h37m past). V1/V1b intact both zones (thresholds 4165.00 / 4225.00; last 2 H4 closes 4067.00/4130.54). PRIMARY still inside zone: 14:00 1H candle small-range continuation (O4135.5 H4138.9 L4129.8 C4130.5) — no bearish engulf/pin/CHoCH, **E0 FAIL**. H4 structure still HH+HL off the NFP spike (12:00 bar 4139.76 high > prior 4115.77) — **E1 FAIL** (needs LH+LL for short). E2 DFII10 slope+ PASS, E4 compressed PASS. E0+E1 fail caps EC ≈4.0/10, below floor. **PRIMARY: NO TRADE — no E0, structure still bullish against short.** SECONDARY 4190-4220 unreached. Ledger: NO_TRADE (soft), lock=none. Both zones PENDING.

## Rerun 15:11 UTC (fresh /validate)
DB guard OK (backup taken). Data pull current (W27 pull immutable as expected; live bars fresh via DB — last H4 12:00 UTC, last H1 15:00 UTC). CB calendar clear (no decisions in window). Econ calendar: NFP+AHE+URate fired 12:30 UTC TODAY as flagged — now 2h41m past, V3 event window (±30min = through 13:00 UTC) **fully cleared**.

Spot 4118.81 (H1 15:00 close) | H4_ATR 40.92 | D1_ATR 109.55 (median 117.26, **compressed**) | DFII10 2.20% (baseline 2.23, drift −0.03, slope20 +0.13) | DXY 100.795 (slope20 +0.725) | VIX 16.59 (stale by 1d, well below 35 — veto suspended, moot for SHORT anyway). D1 ADX 48 trending.

**Hard blocks — both zones:**
| Block | PRIMARY (4120–4160) | SECONDARY (4190–4220) |
|---|---|---|
| V1 (D1 close beyond zone) | ✅ intact (last D1 close 4035.59 < 4120) | ✅ intact |
| V1b (2×H4 close past threshold) | ✅ intact (thresh 4165.00; last 2 H4 closes 4067.00 / 4118.81) | ✅ intact (thresh 4225.00) |
| V3 (NFP window) | ✅ **CLEARED** (12:30 release now 2h41m past) | ✅ cleared |
| VETO (VIX>35, blocks SHORTs) | ✅ n/a (16.59 << 35) | ✅ n/a |

No re-forecast triggers. Macro drift −0.03 well inside ±0.10.

**Entry Confluence — PRIMARY:** price sits just under the zone floor (4118.81, zone starts 4120) after the NFP spike retraced from H1 high 4142.40. Checked last 3 closed H1 candles for a bearish reversal: 15:00 candle is red (O4127.55→C4118.81) but body 8.74 does NOT engulf the 14:00 body, and upper-wick pin ratio only 0.31 (need ≥2.5) — **E0 FAIL**. H4 structure remains HH+HL (12:00 bar high 4139.76 > prior 06-30/07-01 highs) — needs LH+LL for a short thesis — **E1 FAIL**. E2 DFII10 slope +0.13 (rising, bearish-gold) ✅ PASS. E3 macro drift −0.03 < 0.10 ✅ PASS. E4 D1 ATR compressed ✅ PASS. E5 DXY 20d slope +0.725 (rising, bearish-gold) ✅ PASS.
**EC = 0(E0) + 0(E1) + 2.0(E2) + 1.0(E3) + 1.0(E4) + 0.5(E5) = 4.5/10 — below 5.0 floor.**
**PRIMARY: NO TRADE — EC 4.5/10 (no E0, H4 structure still bullish HH+HL against short thesis).**

**SECONDARY (4190–4220):** unreached (spot 4118.81, ~72pts below zone bottom); same structure/E0 failure mode applies if extrapolated. **NO TRADE — zone unreached + EC would floor-miss on E0/E1 regardless.**

Ledger: both zones NO_TRADE (soft — EC-floor miss, not a hard-gate failure), lock cleared. Both zones remain PENDING.
