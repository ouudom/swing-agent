---
type: daily_validation
instrument: eurjpy
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
e2: false
e3: false
e4: false
e5: false
entry_confluence_score: 4.5
zone_confluence_score: 7.0
e0_pattern: none
anchor_type: N/A
anchor_price: 0.000
h4_atr: 0.378
d1_atr: 0.938
d1_atr_compressed: false
sl_distance: 0.424
offset: 0.00
order_limit: NO_TRADE
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
adx_val: 18.8
---

# Validation — 2026-07-02 (PRIMARY + SECONDARY zones from [[2026-W27]])

*Rerun 06:15 UTC — spot 184.921. LONG re-scored: EC 2.5/10 (D1 oscillators mid, not washout — Stoch 24.1/W%R -66.4 not <-80; no E0). SHORT re-scored: EC 4.5/10 (H4 W%R -13.1 OVERBOUGHT ✅ E1, ADX 18.8 ✅ E5, structure intact ✅ E4, but TTM squeeze OFF both TF → E3 fails; no E0 fired → floor unreachable). Both NO TRADE.*

## Market Snapshot
| | Value | Note |
|---|---|---|
| Spot | 184.921 | mid-range; between zones (LONG 183.0–183.6 below, SHORT 186.0–186.5 above) |
| H4 ATR | 0.352 | — |
| D1 ATR | 0.889 | not compressed |
| VIX | 16.45 (stale) | veto suspended (DEAD for eurjpy) |
| ADX D1 | 18.8 | ranging |
| MoF | CAUTION — spot 184.935 inside 182.0–185.0 band | ambush-tactics shift confirmed 2026-07-02 |
| ECB rate | 2.25% | context only (macro dead) |

## Q1+Q2 — Hard Blocks

### Zone A: LONG 183.00–183.60 (PRIMARY, ZC 7.0)
| Block | Result | Note |
|---|---|---|
| V1 | ✅ intact | D1 closes 185.629 → 184.948 → 184.935 — all above 183.0 |
| V1b | ✅ intact | H4 closes 184.912 / 184.935 — threshold 182.960 not breached |
| V3 | ✅ clear | No BoJ/ECB decisions; US NFP caution only (no USD leg) |
| **MoF** | ⚠ CAUTION | Spot 184.935 inside 182–185 band (not HARD_BLOCK — below level 185.0). Cap conviction MEDIUM. |
| Zone position | ❌ PENDING | Spot 184.935 is 1.335 above zone top (183.60). Price not at zone. |

### Zone B: SHORT 186.00–186.50 (SECONDARY, ZC 6.5)
| Block | Result | Note |
|---|---|---|
| V1 | ✅ intact | D1 closes all below 186.0 |
| V1b | ✅ intact | H4 closes 184.912 / 184.935 — threshold 186.540 not breached |
| V3 | ✅ clear | No hard events |
| Zone position | ❌ PENDING | Spot 184.935 is 1.065 below zone bottom (186.0). Price not at zone. |

## Q3 — Re-Forecast Check
No re-forecast triggers. D1 last 3 closes declining (185.629 → 184.948 → 184.935) — moving toward LONG zone. MoF ambush-tactics update noted: regime ACTIVE, silence now the policy tool (updated verified_through 2026-07-02).

## Result
```
Zone A (LONG 183.00–183.60): NO TRADE — EC 2.5/10 (no washout, no E0) + MoF CAUTION (cap MEDIUM)
Zone B (SHORT 186.00–186.50): NO TRADE — EC 4.5/10 (E1 overbought live, but no squeeze/no E0)
```
Both zones structurally intact. Price mid-range. Monitor for approach to either zone.

## Rerun 07:1x UTC (automated hourly)
Spot 184.921 (unchanged) | D1_ATR 0.889 | H4_ATR 0.352 | D1 ADX 18.8 ranging (unchanged) | D1 Stoch 24.1 / H4 W%R −13.1 overbought (unchanged reads). CB calendar clear (no BoJ/ECB). Econ calendar EXIT-1 stale coverage — not a blocker (no USD leg, US events caution only). Intervention watch: CAUTION, spot inside 182.0–185.0 band, MoF ambush-tactics regime ACTIVE (verified_through 2026-07-02) — caps LONG conviction MEDIUM, no HARD_BLOCK. V1b intact both zones. No E0 either direction. **Both zones unchanged: NO TRADE — EC floor (LONG 2.5/10, SHORT 4.5/10), no E0.** PENDING.

## Rerun 08:07 UTC (automated hourly)
Spot 184.121 (D1 close) | D1_ATR 0.938 (median 0.869, expanding) | H4_ATR 0.385 | Intervention: CAUTION unchanged, spot inside 182.0–185.0 band. Econ calendar clear (no BoJ/ECB tier-1). V1/V1b intact both zones. No E0 either direction. **Both zones NO TRADE — EC 3.5/10 (below floor), no E0.** Ledger updated (no lock, soft NO_TRADE). PENDING.

## Rerun 09:07 UTC (automated hourly)
Spot 183.9997 (H4 close, D1 close 183.9997). LONG zone 183.0-183.6: spot just above zone top (~40 pips), approaching from above but not yet inside — no entry. SHORT zone 186.0-186.5: spot ~200 pips below, unreached. EC 3.5/10 both < floor (no E0 either side). No hard events (EU/GB clear); no USD leg so NFP caution only. MoF regime active (ambush-tactics, no advance jawboning) — CAUTION on any future LONG near highs. Ledger updated (soft NO_TRADE, no lock). Both PENDING.

## Rerun 10:07 UTC (automated hourly)
Spot 184.007 (D1 close) | H4_ATR 0.378 | D1_ATR 0.998 (median 0.879, expanding). LONG zone 183.0-183.6: spot ~40 pips above top, still unreached from above. SHORT zone 186.0-186.5: spot ~200 pips below, unreached. V1/V1b intact both zones. No E0 either direction. EC < floor both zones. Intervention watch: CAUTION unchanged, spot inside 182.0-185.0 band, MoF ambush regime active — caps LONG conviction MEDIUM if reached. No BoJ/ECB events. **Both zones unchanged: NO TRADE — EC floor, zones unreached.** Ledger: NO_TRADE (soft, no lock). PENDING.

## Rerun 11:12 UTC (automated hourly)
Spot 184.135 (H4) | H4_ATR 0.385 | D1_ATR 0.938 (median 0.869, expanding). LONG zone 183.0-183.6: spot ~54pips above top, unreached from above; MoF CAUTION (spot inside 182.0-185.0 band, ambush-tactics regime ACTIVE) caps LONG conviction MEDIUM if reached. SHORT zone 186.0-186.5: spot ~186pips below, unreached. V1/V1b intact both zones (H4 closes 184.210/184.135, thresholds 182.960 / 186.540). No BoJ/ECB events. **Both zones unchanged: NO TRADE — EC floor (LONG 2.5/10, SHORT 3.5/10), zones unreached.** Ledger: NO_TRADE (soft). PENDING.

## Rerun 13:15 UTC (automated hourly)
Spot 184.350 (H1 13:00 close). LONG zone 183.0-183.6 still ~75pips above top, unreached; MoF CAUTION unchanged (spot inside 182.0-185.0 band). SHORT zone 186.0-186.5 ~165pips below, unreached. No BoJ/ECB events. **Both zones unchanged: NO TRADE — zones unreached.** PENDING.

## Rerun 14:07 UTC (automated hourly)
Spot 184.298 (H4 close). LONG zone 183.0-183.6 still ~70pips above top, unreached. SHORT zone 186.0-186.5 ~170pips below, unreached. V1/V1b intact both zones. Intervention watch: CAUTION unchanged — spot 184.298 inside 182.0-185.0 band, MoF ambush-tactics regime ACTIVE (2026-07-02 jawboning: silent intervention, no advance warning); caps LONG conviction MEDIUM if LONG zone reached. No BoJ/ECB events. **Both zones unchanged: NO TRADE — zones unreached.** PENDING.

## Rerun 15:2x UTC (fresh /validate run)
Spot 184.087 (H4 close 12:00 bar) | H4_ATR 0.378 | D1_ATR 0.938 (median 0.869, expanding, not compressed). CB calendar: no BoJ/ECB decisions in 2-day window. Econ calendar: no high-impact EU/JP releases in window (coverage to 07-03, adequate). Intervention watch: **CAUTION unchanged** — spot 184.087 inside 182.0–185.0 band, regime ACTIVE, MoF (Reuters) 2026-07-02 jawboning confirms ambush-tactics shift (silent intervention, no advance warning, crosses slam in sympathy with USDJPY) — watch config current, no refresh needed (verified_through already 2026-07-02); caps any LONG fill to conviction MEDIUM. D1 ADX 16.06 — well under 30, no fade-veto concern. V1 intact both zones (D1 closes 184.22/184.91/185.63/184.95, neither zone breached). V1b intact both zones (H4 closes 184.090/184.087; LONG threshold 182.960 not breached, SHORT threshold 186.540 not breached). No V3 event-window block. LONG zone 183.0–183.6: spot ~49 pips above zone top, unreached — no washout readings possible off-zone, EC floor-miss, no E0. SHORT zone 186.0–186.5: spot ~191 pips below zone bottom, unreached — EC floor-miss, no E0. **Both zones unchanged: NO TRADE (soft — structure intact, zones simply unreached).** PENDING.
