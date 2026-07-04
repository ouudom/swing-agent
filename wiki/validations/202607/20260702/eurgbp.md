---
type: daily_validation
instrument: eurgbp
date: 2026-07-02
week: 2026-W27
active_zone: PRIMARY
v1_structure_intact: false
v1b_intact: true
v3_news_clear: true
vix_veto: false
vix_stale: true
reforecast_action: WARN_LOG
reforecast_triggers: [T3]
e0_entry_confirmation: false
e1: false
e2: false
e3: false
e4: false
e5: false
entry_confluence_score: 3.5
zone_confluence_score: 7.5
e0_pattern: none
anchor_type: N/A
anchor_price: 0.00000
h4_atr: 0.00117
d1_atr: 0.00303
d1_atr_compressed: false
sl_distance: 0.00134
offset: 0.00
order_limit: INVALIDATED
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
adx_val: 23.4
---

# Validation — 2026-07-02 (PRIMARY + SECONDARY zones from [[2026-W27]])

*Rerun 06:15 UTC — spot recovered to 0.86201 (was 0.85673). SECONDARY SHORT re-scored: EC 3.5/10 (D1/H4 oscillators mid, not extreme — Stoch 28.7/38.3, W%R -61.6/-70.6, CCI -19.3/16.7; SHORT-confirm E0 none). NO TRADE, floor unreachable.*

## Market Snapshot
| | Value | vs Baseline |
|---|---|---|
| Spot | 0.86201 | recovering; below SHORT zone floor |
| H4 ATR | 0.00121 | — |
| D1 ATR | 0.00280 | vs median ~0.00262 → not compressed |
| VIX | 16.45 (2026-06-30) | **stale (>1d lag) — veto suspended** |
| ADX D1 | 23.4 | transitional / ranging |
| Rate diff EUR−GBP | −1.479% | flat (context only — macro dead) |

## Q1+Q2 — Hard Blocks

### Zone A: LONG 0.8595–0.8620 (PRIMARY, ZC 7.5)
| Block | Result | Note |
|---|---|---|
| **V1** | ❌ **INVALIDATED** | D1 close 0.85673 < zone bottom 0.85950 (yesterday 0.85685, today 0.85673 — both closes below floor) |
| V1b | ✅ N/A | V1 already triggers INVALIDATED |
| V3 | ✅ clear | No EU/GB hard events today; US NFP caution only (no USD leg) |

> Wick-close-back-inside rule NOT applicable here — two consecutive D1 closes below 0.8595 confirm breakout, not a wick sweep.

### Zone B: SHORT 0.8675–0.8710 (SECONDARY, ZC 6.5)
| Block | Result | Note |
|---|---|---|
| V1 | ✅ intact | D1 close 0.85673 well below zone top 0.8710 |
| V1b | ✅ intact | H4 closes 0.8567/0.8567 — no breach of 0.8710+0.0004 |
| V3 | ✅ clear | No EU/GB hard events |
| Zone position | ❌ PENDING | Spot 0.85673 is 100+ pips below zone bottom (0.8675). No entry signal possible. |

## Q3 — Re-Forecast Check
T3 warn-log: EURGBP extended the W26 loss (LONG broke at 0.8625) and now D1 closed below 0.8595 floor. Potential bear bias shift from range to bearish structure. Weekly forecast noted "D1 CHoCH DOWN @0.86182" and warned "D1 close < 0.8580 = squeeze breaks down." At 0.85673, price is approaching but has not closed < 0.8580. → WARN_LOG (flag for /weekly W28 re-assessment if D1 close < 0.8580).

> [!warning] W28 re-forecast flag
> If D1 closes < 0.8580, the bear squeeze breaks down — void the SECONDARY short zone (0.8675–0.8710) at W28 /weekly and reassess bias. Current structure still ambiguous (ADX 23, transitional).

## Result
```
Zone A (LONG 0.8595–0.8620): INVALIDATED — V1: D1 closes 0.85685 + 0.85673 both below zone bottom 0.8595
Zone B (SHORT 0.8675–0.8710): NO TRADE — EC 3.5/10 (floor 5.0), oscillators mid not extreme, no E0
```

## Rerun 07:1x UTC (automated hourly)
Spot 0.85656 (D1 close, vs 0.86201 prior read — DB live value, note prior rerun's 0.86201 was a stale-pull artifact) | D1_ATR 0.00302 | H4_ATR 0.00123 | D1 ADX 22.9 TRANSITIONAL. CB calendar clear (no ECB/BoE). Econ calendar EXIT-1 stale coverage window — not a blocker (no USD leg, US events caution only). LONG zone remains INVALIDATED (V1 breach, unchanged). SHORT zone 0.8675–0.8710 V1b intact (threshold 0.8714, H4 closes 0.85670/0.85656); spot ~110 pips below zone, no SHORT E0 (only LONG engulf fired, wrong direction). **SHORT zone unchanged: NO TRADE — EC floor, zone unreached.** PENDING.

## Rerun 08:07 UTC (automated hourly)
Spot 0.85527 (D1 close) | rate-diff EUR−GBP -1.479 (baseline 2.88, drift -4.357 — weak/context, no hard gate). Econ calendar clear (no ECB/BoE tier-1 today). LONG zone remains INVALIDATED (unchanged). SHORT zone V1/V1b intact, no SHORT E0 (engulf fired LONG only, wrong direction), EC 3.0/10 < floor. **SHORT zone NO TRADE — EC floor.** Ledger updated (no lock, soft NO_TRADE). PENDING. W28 flag holds: D1 < 0.8580 = re-assess.

## Rerun 09:07 UTC (automated hourly)
Spot 0.85491 (D1 close 0.85491 vs prior 0.85527) | H4 ATR 0.00117, D1 ATR unchanged range. LONG zone remains INVALIDATED (V1 breach, unchanged). SHORT zone 0.8675-0.8710 V1/V1b intact; spot ~120 pips below zone, unreached; no SHORT E0. EC 3.0/10 < floor. **NO TRADE — EC floor, zone unreached.** No USD leg → NFP caution only, not a block. Ledger updated (soft NO_TRADE, no lock). PENDING. W28 flag holds: D1 < 0.8580 = re-assess.

## Rerun 10:07 UTC (automated hourly)
Spot 0.85528 (D1 close) | H4_ATR 0.00127 | D1_ATR 0.00309 (median 0.00263, expanding). LONG zone remains INVALIDATED (V1 breach, unchanged). SHORT zone 0.8675-0.8710 V1/V1b intact (H4 closes 0.85528/0.85538, threshold 0.87140); spot ~120 pips below zone, unreached. E0: LONG engulf fired (wrong direction for SHORT zone, discounted). EC ~3.0/10 < floor. **NO TRADE — EC floor, zone unreached.** No USD leg → NFP caution only, not a block. Ledger: NO_TRADE (soft, no lock). PENDING. W28 flag holds: D1 < 0.8580 = re-assess.

## Rerun 11:12 UTC (automated hourly)
Spot 0.85603 (H4) | H4_ATR 0.00126 | D1_ATR 0.00303. SHORT zone 0.8675-0.8710 unreached, spot ~150pips below zone bottom. V1b intact (H4 closes 0.85538/0.85603, threshold 0.87140). No high-impact EU/GB releases. LONG zone PRIMARY remains INVALIDATED (07-02 V1 breach, unchanged). **SECONDARY SHORT: NO TRADE — EC 3.0/10 (below floor, zone unreached, no E0).** Ledger: NO_TRADE (soft). PENDING.

## Rerun 13:15 UTC (automated hourly)
Spot 0.85652 (H4 12:00 close). SHORT zone 0.8675-0.8710 still unreached, ~100pips below zone bottom. USD NFP no direct leg (cross, caution-only). No change vs 11:12 run. **SECONDARY SHORT: NO TRADE — zone unreached.** PENDING. W28 flag holds: D1 < 0.8580 = re-assess.

## Rerun 14:07 UTC (automated hourly)
Spot 0.85576 (H4 close). SHORT zone 0.8675-0.8710 still unreached, ~110pips below zone bottom. No high-impact EU/GB releases. No USD leg — DXY move not applicable. LONG zone remains INVALIDATED. **SECONDARY SHORT: NO TRADE — zone unreached.** PENDING. W28 flag holds: D1 < 0.8580 = re-assess (spot now 0.85576, watch).

## Rerun 15:2x UTC (manual /validate)
Spot 0.85617 (H4 close 15:00 UTC) | H4_ATR 0.00136 | D1_ATR 0.00303 (median 0.00262, expanding, not compressed) | D1 ADX 16.92 (ranging, well below 30 fade-veto) | rate-diff EUR−GBP −1.482 (prev −1.479, slope20 +0.249 — weak/context only, no gate). VIX 16.59 (spike +0.14, no veto — EURGBP has none). CB calendar clear (no ECB/BoE in window). Econ calendar: no high-impact EU/GB releases 07-02→07-04 (coverage-edge warning on the 07-04 tail is immaterial — Saturday, no market). LONG zone PRIMARY remains ~~INVALIDATED~~ (V1 breach confirmed, unchanged, correctly removed from `_HOT.md`). SHORT zone 0.8675–0.8710 V1 intact (D1 close 0.85673/0.85685 well below zone top) and V1b intact (`check_v1b.py`: last 2 H4 closes 0.85655/0.85617, threshold 0.87140, buffer 0.0004 — clean). **Watch-note check: D1 close < 0.8580 trigger NOT fired** — last completed D1 close (07-01) = 0.85685, today's D1 bar still open at 0.85617, both above 0.8580; SHORT zone stays live, not voided. Spot is ~1090 pips below zone bottom (0.8675) — zone structurally unreached, no D1/H1 oscillator extreme at resistance possible, no E0 obtainable. **SECONDARY SHORT: NO TRADE — zone unreached (EC not scorable, floor unreachable).** PENDING, unchanged. W28 flag holds: D1 close < 0.8580 = void SHORT zone + re-assess bias — currently not triggered, spot approaching from above.
