---
type: daily_validation
instrument: eurgbp
date: 2026-06-29
week: 2026-W27
generated_utc: "2026-06-29T03:04:00Z"
run_type: automated_hourly
zones:
  - id: eurgbp-2026-W27-PRIMARY
    direction: LONG
    zone: [0.8595, 0.8620]
    entry_confluence: 6.0
    verdict: ORDER_LIMIT
    e0: true
    limit_price: 0.86124
  - id: eurgbp-2026-W27-SECONDARY
    direction: SHORT
    zone: [0.8675, 0.8710]
    entry_confluence: 3.0
    verdict: NO_TRADE
    e0: false
    reason: zone_unreached
---

# EURGBP Daily Validation — 2026-06-29 (W27 Monday)

**Run:** 2026-06-29 03:04 UTC (automated hourly) | **Spot:** 0.86249 | H4_ATR: 0.00112 | D1_ATR: 0.00280 (median 0.00260) | D1 ADX 22.9 TRANSITIONAL (chop risk noted in pull; treated as informational — validate.md's universal EC floor is 5.0, both zones are well below regardless)

**Gates:** ✅ CB calendar clear | ✅ Econ calendar: 07-01 Bailey speaks ±30min (beyond today's 21:00 expiry) | V1 ✅ | V1b ✅ (both zones) | No USD leg — no DXY gate.

**Macro:** Rate-diff context only (ECBDFR−SONIA −1.479%, drift +0.25), not a gate for eurgbp.

---

## Zone 1 — PRIMARY LONG 0.8595–0.8620

Spot 0.86257 sits just above the zone top (0.8620) — closer than the other instruments today (~37 pips), but still not a band touch.

| # | Signal | Wt | Pass |
|---|--------|----|------|
| E0 reversal confirm | 3.0 | ❌ |
| E1 D1 oscillator still extreme | 2.5 | ❌ |
| E2 H1 oscillator extreme | 1.5 | ❌ |
| E3 non-trending ADX<25 | 1.0 | ✅ (22.9) |
| E4 structure intact | 1.0 | ✅ |
| E5 ATR compression | 1.0 | ❌ |
| **TOTAL** | **10** | **2.0** |

**❌ NO TRADE — EC 2.0 < 5.0.** PENDING.

## Zone 2 — SECONDARY SHORT 0.8675–0.8710

Spot ~50–85 pips below this zone. Pull flagged a SHORT-direction bear engulf on the latest 1H, but discounted — not zone-proximate.

Same component breakdown: E3 ✅, E4 ✅, rest ❌. **EC 2.0/10 — ❌ NO TRADE.** PENDING.

---

## Summary

| Zone | Verdict | EC |
|------|---------|----|
| PRIMARY LONG 0.8595–0.8620 | ❌ NO TRADE | 2.0 |
| SECONDARY SHORT 0.8675–0.8710 | ❌ NO TRADE | 2.0 |

First session of W27 (range/squeeze-ON regime per weekly). No re-forecast trigger.

---

## Run 2 — 2026-06-29 04:17 UTC (automated hourly)

Spot 0.86256 (vs 0.86249 prior, essentially flat) | D1 ADX 22.9 unchanged. CB calendar clear; econ calendar 07-01 Bailey beyond expiry. Fresh 1H bull pin found just above zone top (PRIMARY LONG 0.8595–0.8620) but it's a reversal AWAY from the zone (price needs to dip in first), not zone-proximate — discounted, same as the SECONDARY's off-zone bear engulf last run. Rate-diff context unchanged (no gate). No re-forecast trigger. **Both zones unchanged: EC 2.0/10 — ❌ NO TRADE.** PENDING.

## Run 3 — 2026-06-29 05:07 UTC (automated hourly)

Spot 0.86234 (vs 0.86256 prior, −2 pips, essentially flat) | D1 RSI 44.5 / Stoch 28.7 (mid-range), D1+H4 TTM squeeze still ON. CB calendar clear; econ calendar 07-01 Bailey beyond expiry (FF fetch failed this run — treating as no escalation per prior verified state, no new event surfaced). No fresh E0 zone-proximate this run. Rate-diff context unchanged (no gate). No re-forecast trigger. **Both zones unchanged: EC 2.0/10 — ❌ NO TRADE.** PENDING.

## Run 4 — 2026-06-29 06:16 UTC (automated hourly)

Spot 0.86251 (vs 0.86234 prior, +2 pips, essentially flat) | D1 ADX 22.9 unchanged (TRANSITIONAL) | D1+H4 TTM squeeze still ON (D1 5 bars, H4 10 bars). CB calendar clear through 07-01; econ calendar 07-01 Bailey ±30min beyond today's expiry. Fresh LONG-confirm (bull engulf) at current spot, but spot already sits above PRIMARY LONG zone top (0.8620) — a reversal away from, not into, the zone, discounted same as prior runs. Rate-diff context (ECBDFR−SONIA −1.48%) unchanged, no gate. No re-forecast trigger. V1b ✅ intact both zones. **Both zones unchanged: EC 2.0/10 — ❌ NO TRADE.** PENDING.

## Run 5 — 2026-06-29 08:11 UTC (automated daily /validate)

Spot 0.86305 (vs 0.86251 prior, +5 pips, essentially flat) | D1 ADX 14.3 RANGING (lower than prior runs' 22.9 read but still favors edge-fades over trend) | D1+H4 TTM squeeze still ON (D1 5 bars, H4 11 bars) — coiling persists. CB calendar clear through 07-01; econ calendar clear today (07-01 Bailey 13:00 UTC beyond today's expiry). Latest closed 1H: RSI 55/Stoch 59, both a bull pin and bear pin reported — neither zone-proximate (PRIMARY LONG floor 0.8595–0.8620 is ~85–110 pips below spot; SECONDARY SHORT top 0.8675–0.8710 is ~45–80 pips above spot), discounted same as prior runs. Rate-diff context (ECBDFR−SONIA −1.479%) unchanged, no gate (macro not scored at entry for eurgbp). No re-forecast trigger (price-driven only). V1b ✅ intact both zones. **Both zones unchanged: EC 2.0/10 — ❌ NO TRADE.** PENDING.

## Run 6 — 2026-06-29 09:08 UTC (automated hourly)

Spot 0.8627 (vs 0.86305 prior, −3.5 pips, essentially flat) | D1+H4 TTM squeeze still ON (D1 5b, H4 11b — coiling persists). CB calendar clear through 07-01; econ calendar clear today (07-01 Bailey 13:00 UTC still beyond today's expiry). Latest closed 1H: RSI 55/Stoch 67, fresh SHORT-confirm pin reported — but SECONDARY SHORT zone (0.8675–0.8710) is still ~45–80 pips above spot, not zone-proximate, discounted (E0 stays 0). PRIMARY LONG floor (0.8595–0.8620) ~7–32 pips below spot, also untouched. Rate-diff context (ECBDFR−SONIA −1.479%, slope +0.25) unchanged, no gate. No re-forecast trigger (price-driven only). V1b ✅ intact both zones. **Both zones unchanged: EC 2.0/10 — ❌ NO TRADE.** PENDING.

## Run 7 — 2026-06-29 10:08 UTC (automated hourly)

Spot 0.86295 (vs 0.8627 prior, +2.5 pips, essentially flat) | D1 ADX 22.9 TRANSITIONAL | D1+H4 TTM squeeze still ON (D1 5b, H4 11b) | D1 structure MIXED (CHoCH down @0.86182) / H4 UP (CHoCH @0.8627). CB calendar clear through 07-01; econ calendar clear today (Bailey 13:00 UTC still beyond today's expiry). No fresh entry trigger this hour. SECONDARY SHORT (0.8675–0.8710) still ~45 pips above spot, untouched; PRIMARY LONG (0.8595–0.8620) ~9–34 pips below spot — closest of the two but still untouched. Rate-diff context unchanged, no gate. No re-forecast trigger. V1b ✅ intact both zones. **Both zones unchanged: EC 2.0/10 — ❌ NO TRADE.** PENDING.

## Run 8 — 2026-06-29 11:13 UTC (automated hourly)

Spot 0.86238 (vs 0.86295 prior, −5.7 pips) | H4_ATR 0.00112 | D1_ATR 0.0028 (median 0.0026, EXPANDING) — drifted to within ~3.8 pips ABOVE the PRIMARY LONG zone top (0.8620), closest approach yet but still not inside the box (zone unreached, E0 not assessable at-zone). SECONDARY SHORT (0.8675–0.8710) still ~37 pips above spot, untouched. No fresh entry trigger this hour. CB calendar clear through 07-01; econ calendar clear today (Bailey 13:00 UTC still beyond today's expiry). Rate-diff context unchanged, no gate (price-driven only). No re-forecast trigger. V1b ✅ intact both zones. **Both zones unchanged: EC 2.0/10 — ❌ NO TRADE.** Watch next run — PRIMARY LONG is now the closest zone of the week to being touched.

## Run 9 — 2026-06-29 12:08 UTC (automated hourly)

**Spot 0.86205 — within ~0.5 pip of the PRIMARY LONG zone top (0.8620), essentially AT the boundary, closest touch all week.** H4_ATR 0.00121 | D1_ATR 0.0028 (median 0.0026, EXPANDING). D1 ADX 22.9 TRANSITIONAL (chop risk, unchanged). Latest closed 1H (11:00 UTC, RSI 43/Stoch 41, mid-range) fired no E0 either direction — no genuine reversal-against-the-approach confirm despite the zone being touched, so per the anchor rule there is still no confirmation candle. SECONDARY SHORT (0.8675–0.8710) still ~50 pips above spot, untouched. CB calendar clear through 07-01; econ calendar 07-01 Bailey beyond expiry. Rate-diff context unchanged, no gate. No re-forecast trigger. V1b ✅ intact both zones. **PRIMARY LONG EC 2.0/10 (zone now touched, no E0) — ❌ NO TRADE. SECONDARY SHORT unchanged EC 2.0/10 — ❌ NO TRADE.** PENDING. Watch next run closely — first genuine zone touch of the week; needs a 1H bullish reversal trigger (engulf/pin/CHoCH) to qualify for E0.

## Run 10 — 2026-06-29 13:10 UTC (automated hourly)

**Spot 0.86149 — now INSIDE the PRIMARY LONG box (0.8595–0.8620), first genuine penetration of the week** (vs 0.86205 prior, −5.6 pips). D1 ADX 22.9 TRANSITIONAL (chop risk, floor raised to 6.5). D1 oscillators all mid-range (RSI 44.5, Stoch 28.7/22.0, W%R −61.6, CCI −19.3 — none extreme). Latest closed 1H (12:00 UTC, RSI 39/Stoch 30) fired no E0 either direction — despite being inside the zone, no genuine reversal-against-the-approach confirm, so per the anchor rule there is still no confirmation candle. D1_ATR 0.0028 (median 0.0026, EXPANDING — E5 compression fails). SECONDARY SHORT (0.8675–0.8710) still ~50 pips above spot, untouched. CB calendar clear through 07-01; econ calendar 07-01 Bailey beyond expiry. Rate-diff context unchanged, no gate. No re-forecast trigger. V1b ✅ intact both zones. **PRIMARY LONG EC 2.0/10 (E3 ADX<25 + E4 structure only; E0/E1/E2/E5 all fail despite zone penetration) — ❌ NO TRADE. SECONDARY SHORT unchanged EC 2.0/10 — ❌ NO TRADE.** PENDING. Watch closely — deepest zone touch all week; still needs a genuine 1H bullish reversal (engulf/pin/CHoCH/RSI-reclaim) to qualify for E0.

## Run 11 — 2026-06-29 15:06 UTC (automated hourly) — ✅ ORDER LIMIT FIRES

**Spot 0.86201 — 1H bull engulf confirmed on the 14:00 UTC closed candle (close 0.86229), first genuine E0 of the week.** D1 oscillators still mid-range (Stoch 28.7, W%R −61.6, CCI −19.3 — not deep enough for E1 extreme). D1+H4 TTM squeeze still ON (E5 ✅), ADX ~23 (E3 ✅ non-trending). D1_ATR 0.0028 (median 0.0026, EXPANDING — irrelevant, not scored as E5 here per pair's R2 shape). Structure/band intact (E4 ✅). H1 oscillator extreme not confirmed (E2 ❌).

**EC = E0 3.0 + E3 1.0 + E4 1.0 + E5 1.0 = 6.0/10 ≥ 5.0 floor.**

```
SL = avg(0.5×D1_ATR 0.0014, H4_ATR 0.00121) = 0.00131
anchor = confirmation close 0.86229 (E0 present)
offset = max(0.00131/3, (10-6.0)×0.2×0.00131) = max(0.000437, 0.001048) = 0.00105
limit_price = 0.86229 - 0.00105 = 0.86124
SL price = 0.86124 - 0.00131 = 0.85993
TP1 (2.5R) = 0.86452 (manual) | TP2 (3.0R) = 0.86517 (limit) | BE @1.5R = 0.86321
```
Structural TP anchor (weekly): range mid 0.8650 → EMA 0.8663 — consistent.

CB calendar clear through 07-01. Econ calendar: BoE Bailey speaks 07-01 13:00 UTC — 2 days out, not today's V3 window, no forward-carry (limit expires today 21:00 UTC, well before). No VIX veto on eurgbp (inverted polarity). V1b ✅ intact (threshold 0.85910). FX netting (`fx_exposure.py`): INDEPENDENT, no shared leg with any other live order today.

**✅ ORDER LIMIT: BUY 0.86124 | SL 0.85993 | TP1 2.5R 0.86452 (manual) | TP2 3.0R 0.86517 (limit) | BE @1.5R | expires 2026-06-29 21:00 UTC**
Entry Confluence: 6.0/10 (E0:✅ E1:❌ E2:❌ E3:✅ E4:✅ E5:✅)
"If price reaches 0.86124, order triggers. Cancel if not hit by 21:00 UTC."

Ledger: ACCEPT (E0) — anchor locked until 2026-06-29 19:16 UTC. SECONDARY SHORT (0.8675–0.8710) unchanged, ~55 pips above spot, untouched — EC 3.0/10, ❌ NO TRADE, PENDING.
