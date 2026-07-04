---
type: daily_validation
instrument: usdchf
date: 2026-07-02
week: 2026-W27
active_zone: PRIMARY
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
e4: false
e5: false
entry_confluence_score: 0.0
zone_confluence_score: 6.5
e0_pattern: none
anchor_type: N/A
anchor_price: 0.00000
h4_atr: 0.00165
d1_atr: 0.00465
d1_atr_compressed: false
sl_distance: 0.00198
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

# Validation — 2026-07-02 (PRIMARY zone from [[2026-W27]])

*Rerun 06:15 UTC — spot refreshed, verdict unchanged (V3 NFP block still active). E0 read: Stoch-reclaim LONG (19→26) fired but zone unreached — no order regardless.*

## Market Snapshot
| | Value | Note |
|---|---|---|
| Spot | 0.80873 | above zone (LONG 0.7990–0.8020) |
| H4 ATR | 0.00185 | — |
| D1 ATR | 0.00501 | compressed vs median 0.00524 |
| VIX | 16.45 (stale) | veto suspended |

## Q1+Q2 — Hard Blocks

### Zone A: LONG 0.7990–0.8020 (PRIMARY, ZC 6.5)
| Block | Result | Note |
|---|---|---|
| V1 | ✅ intact | spot 0.80875 — zone below current price |
| **V3 — NFP** | ❌ **NO TRADE** | US NFP @ 12:30 UTC (within 2h of 13:00 NYC open) |

## Result
```
Zone A (LONG 0.7990–0.8020): NO TRADE — V3 hard block: US NFP 12:30 UTC
```
Zone PENDING. Spot 0.80875 above zone (USDCHF DXY-driven; may pull to zone post-NFP if USD weakens). Check W28 /weekly.

## Rerun 07:09 UTC (automated hourly)
Spot 0.80873 (unchanged) | H4_ATR 0.00185 | D1_ATR 0.00501 (median 0.00524, compressed) | D1 ADX 35.0 TRENDING | DGS2 4.09% (drift 0.000%, no T6) | DGS2 20d slope +0.0074 (rising, bullish USDCHF context). CB calendar clear, no SNB. Econ calendar EXIT-1 stale coverage but NFP 12:30 UTC confirmed — V3 hard block holds (within 2h of 13:00 UTC NY open). V1b intact (thresholds 0.79860, H4 closes 0.80888/0.80832). E0: Stoch-reclaim LONG fired earlier but zone still unreached (spot 80+ pips above zone). **Zone unchanged: NO TRADE — V3 NFP hard block.** PENDING.

## Rerun 08:07 UTC (automated hourly)
Spot 0.80554 (D1 close) | H4_ATR 0.00174 | D1_ATR 0.00465 (median 0.00524, compressed) | DGS2 4.14% (+0.09 drift, no flip) | DXY jump -0.325 (falling, no anti-jump gate). NFP 12:30 UTC still ahead — V3 hard block holds. V1/V1b intact (D1 low 0.80546 wicked back inside — sweep not breach). E0 Stoch-reclaim LONG still fired. **Zone NO TRADE — V3 NFP hard block overrides fired E0** (entry-in-window risk; no forward-carry applicable, event is in-window). Ledger CANCEL (hard-block), lock cleared. PENDING.

## Rerun 09:07 UTC (automated hourly)
Spot 0.80483 (D1 close), zone LONG 0.7990-0.8020 unreached (spot above). NFP 12:30 UTC within 2h of NY open → V3 event-window hard block holds. Ledger: NO_TRADE (hard-block), lock cleared. PENDING.

## Rerun 10:07 UTC (automated hourly)
Spot 0.80537 (D1 close) | H4_ATR 0.00181 | D1_ATR 0.00484 (median 0.00524, compressed). Zone LONG 0.7990-0.8020 still unreached (spot ~50 pips above zone top). V1/V1b intact (H4 closes 0.80537/0.80667, threshold 0.79860). E0 Stoch-reclaim LONG still fired but irrelevant while zone unreached. NFP 12:30 UTC still ahead — V3 event-window hard block holds. **Zone unchanged: NO TRADE — V3 NFP hard block, zone unreached.** Ledger: NO_TRADE (hard-block), lock cleared. PENDING.

## Rerun 11:12 UTC (automated hourly)
Spot 0.80619 (H4) | H4_ATR 0.00174 | D1_ATR 0.00465 (median 0.00524, compressed) | DGS2 4.09%. Zone LONG 0.7990-0.8020 still unreached (spot ~40pips above zone top). V1/V1b intact. NFP 12:30 UTC within 2h of 13:00 UTC NY open — V3 event-window hard block holds. **Zone unchanged: NO TRADE — V3 NFP hard block, zone unreached.** Ledger: CANCEL (hard-block), lock cleared. PENDING.

## Rerun 13:15 UTC (automated hourly)
Spot 0.80343 (H1 13:00 close). Zone LONG 0.7990-0.8020 still unreached, ~320pips above zone top. V3 window cleared (past 13:00) but moot — zone not touched. **Zone unchanged: NO TRADE — zone unreached.** PENDING.

## Rerun 14:07 UTC (automated hourly)
Spot 0.80237 (H4 close), ~37pips above zone top 0.8020 — still unreached from above, approaching. V1/V1b intact (H4 closes 0.80674/0.80237, threshold 0.79860). DXY jump -0.663 (not a gate for usdchf — jump-anti rule, fade context only per Step0 table). **Zone unchanged: NO TRADE — zone unreached.** PENDING.

## Rerun 15:15 UTC
Spot 0.80221 (H1 close) — zone LONG 0.7990–0.8020 still unreached, ~2pips above zone top. H4_ATR 0.00181 | D1_ATR 0.00465 (median 0.00524, compressed ✅) | D1 ADX 52.93 (strong trend — LONG fades exempt from ADX>30 veto per confluence_criteria). DGS2 4.14% (baseline 4.09, drift +0.05%, no T1). DXY 1d jump -0.643 (anti, no block) | DXY 20d slope +0.677 (rising, aligned w/ LONG). V1/V1b intact (H4 closes 0.80674/0.80221, threshold 0.79860). V3: Swiss CPI (06:30) + US NFP/AHE/UR (12:30) both fully cleared — current time well outside ±30min windows, no forward-carry events remain today; SNB quarterly gate N/A (July non-decision month). CB calendar clear. E0 Stoch-reclaim LONG (from earlier pull) still on file but zone unreached — no fresh reversal signal at the box. EC scored 3.5/10 (E2 DXY-slope ✅, E3 compression ✅, E5 structure ✅; E0/E1/E4 ❌) — below 5.0 floor independent of zone-reach. **Zone unchanged: NO TRADE — zone unreached + EC 3.5 < 5.0 floor.** PENDING.
