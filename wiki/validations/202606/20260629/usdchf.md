---
type: daily_validation
instrument: usdchf
date: 2026-06-29
week: 2026-W27
generated_utc: "2026-06-29T03:04:00Z"
run_type: automated_hourly
zones:
  - id: usdchf-2026-W27-PRIMARY
    direction: LONG
    zone: [0.7990, 0.8020]
    entry_confluence: 2.5
    verdict: NO_TRADE
    e0: false
    reason: zone_unreached_below_floor
---

# USDCHF Daily Validation — 2026-06-29 (W27 Monday)

**Run:** 2026-06-29 03:04 UTC (automated hourly) | **Spot:** 0.80962 | H4_ATR: 0.00192 | D1_ATR: 0.00501 (median 0.00524 — compressed) | D1 ADX 35.0 TRENDING

**Gates:** ✅ CB calendar clear | ✅ Econ calendar clear today | V1 ✅ | V1b ✅ | DXY 101.346 (+0.32% 1w) — slope aligned WITH the LONG (DXY-slope-up macro-aligned per weekly thesis).

---

## Zone 1 — PRIMARY LONG 0.7990–0.8020

Spot 0.80977 is ~77–107 pips ABOVE the zone (price hasn't pulled back to the dip-buy level yet). Pull flagged a LONG-direction bull engulf on the latest 1H, but it's not zone-proximate — discounted (same rationale applied across all instruments today).

| # | Signal | Wt | Pass | Note |
|---|--------|----|------|------|
| E0 reversal confirm | 3.0 | ❌ | Pattern present but not at zone |
| E1 H1 oscillator still extreme | 2.5 | ❌ | Price above zone, not washed out |
| E2 DXY 20d slope aligned | 1.5 | ✅ | +0.32% 1w supports USD strength / LONG usdchf |
| E3 squeeze/calm context | 1.0 | ❌ | |
| E4 non-trending ADX<25 | 1.0 | ❌ | ADX 35.0, trending |
| E5 structure intact | 1.0 | ✅ | V1/V1b clear |
| **TOTAL** | **10** | **2.5** | |

**❌ NO TRADE — EC 2.5 < 5.0.** Zone unreached. PENDING.

---

## Summary

| Zone | Verdict | EC |
|------|---------|----|
| PRIMARY LONG 0.7990–0.8020 | ❌ NO TRADE | 2.5 |

First session of W27. No re-forecast trigger (US2Y FLIPPED-polarity context only).

---

## Run 2 — 2026-06-29 04:17 UTC (automated hourly)

Spot 0.81000 (vs 0.80977 prior, essentially flat) | D1 ADX 35.0 unchanged, still trending against the fade. CB calendar clear; econ calendar still clear today. No fresh E0 this run (prior off-zone bull engulf has lapsed). DXY 101.370 slope still aligned WITH the LONG thesis; DGS2 falling (context, US2Y polarity flipped — not a gate). No re-forecast trigger. **Zone unchanged: EC 2.5/10 — ❌ NO TRADE.** PENDING.

## Run 3 — 2026-06-29 05:07 UTC (automated hourly)

Spot 0.80979 (vs 0.81000 prior, −2 pips, still ~77–107 pips above zone) | D1 RSI 66.6 / Stoch 87.5 / W%R −19.1 (OVERBOUGHT — opposite of the washout needed for E1; D1 ADX still elevated, trending against the fade) | D1_ATR 0.00501 (median, compressed regime holds). CB calendar clear; econ calendar still clear today. No fresh E0 zone-proximate. DXY 101.381, slope still aligned WITH the LONG thesis. No re-forecast trigger. **Zone unchanged: EC 2.5/10 — ❌ NO TRADE.** PENDING.

## Run 4 — 2026-06-29 06:16 UTC (automated hourly)

Spot 0.80931 (vs 0.80979 prior, −5 pips, still ~91–141 pips above zone) | D1 Stoch 87.5 / W%R −19.1 (still OVERBOUGHT, opposite of washout needed for E1) | D1_ATR 0.00501 (median 0.00524, compressed regime holds) | D1 structure UP (BOS UP @0.80152) / H4 DOWN (CHoCH DOWN @0.80899). CB calendar clear through 07-01; econ calendar still clear today. Fresh SHORT-confirm (Stoch-reclaim + bear engulf) — wrong direction for the LONG zone and zone remains far below spot, discounted. DXY jump −0.12% (1d), slope still aligned WITH the LONG thesis. No re-forecast trigger. V1b ✅ intact. **Zone unchanged: EC 2.5/10 — ❌ NO TRADE.** PENDING.

## Run 5 — 2026-06-29 08:11 UTC (automated daily /validate)

Spot 0.80883 (vs 0.80931 prior, −5 pips, still ~86–136 pips above the PRIMARY LONG zone) | D1 ADX 37.5 TRENDING (mild trend, still against the fade) | D1 Stoch 87.5/%D 92.0 OVERBOUGHT, W%R −19.1 OVERBOUGHT (opposite of the washout needed for E1, unchanged) | D1_ATR 0.00189 (median 0.00176, EXPANDING — compression now fails, regime shift from prior runs' "compressed holds" read). CB calendar clear through 07-01; econ calendar clear today (07-01 Warsh 13:00 + ISM PMI 14:00 UTC beyond today's expiry). Latest closed 1H: RSI 46/Stoch 25, no E0 confirm fired either direction. DXY 101.235 (1w +0.06%), slope still aligned WITH the LONG thesis (no jump-anti gate triggered). DGS2 4.09% context only (US2Y polarity flipped for usdchf, not a gate). No re-forecast trigger. V1b ✅ intact. **Zone unchanged: EC 2.5/10 — ❌ NO TRADE.** PENDING.

## Run 6 — 2026-06-29 09:08 UTC (automated hourly)

Spot 0.80878 (vs 0.80883 prior, flat, still ~86–136 pips above the PRIMARY LONG zone) | D1 Stoch 87.5 / W%R −19.1 OVERBOUGHT (opposite of washout needed for E1, unchanged) | D1_ATR median 0.00524, still EXPANDING. CB calendar clear through 07-01; econ calendar clear today (07-01 Warsh 13:00 + ISM PMI 14:00 UTC still beyond today's expiry). VIX 18.89 (spike +0.26), washout — no gate. Latest closed 1H: RSI 46/Stoch 18, fresh LONG-confirm pin reported — but zone (0.7990–0.8020) remains far below spot, not zone-proximate, discounted (E0 stays 0). DXY jump −0.049, slope still aligned WITH the LONG thesis. No re-forecast trigger. V1b ✅ intact. **Zone unchanged: EC 2.5/10 — ❌ NO TRADE.** PENDING.

## Run 7 — 2026-06-29 10:08 UTC (automated hourly)

Spot 0.80855 (vs 0.80878 prior, −2.3 pips, still ~83–133 pips above the PRIMARY LONG zone) | D1_ATR 0.00501 now COMPRESSED (below 20d median 0.00524, first compression flip this week) | D1 ADX 35.0 TRENDING | D1 Stoch 87.5/92.0 / W%R −19.1 OVERBOUGHT (opposite of washout needed for E1, unchanged) | D1 structure UP (BOS @0.80152) / H4 DOWN (CHoCH @0.80899). CB calendar clear through 07-01; econ calendar clear today (Warsh 13:00 + ISM PMI 14:00 UTC still beyond today's expiry). 1H Stoch-reclaim + bear engulf fired — bearish signals, opposite of the LONG thesis here, discounted; zone (0.7990–0.8020) remains far below spot regardless. DXY slope still aligned WITH the LONG thesis. No re-forecast trigger. V1b ✅ intact. **Zone unchanged: EC 2.5/10 — ❌ NO TRADE.** PENDING.

## Run 8 — 2026-06-29 11:13 UTC (automated hourly)

Spot 0.80836 (vs 0.80855 prior, −1.9 pips, still ~82–131 pips above the PRIMARY LONG zone) | H4_ATR 0.00193 | D1_ATR 0.00501 (median 0.00524, still COMPRESSED) | DGS2 4.09% FALLING (flipped-polarity context, bearish for the LONG thesis) | DXY 101.220 (jump anti, no gate). CB calendar clear through 07-01; econ calendar clear today (Warsh 13:00 + ISM PMI 14:00 UTC still beyond today's expiry). No fresh E0 toward LONG this hour; zone remains untouched regardless. No re-forecast trigger. V1b ✅ intact. **Zone unchanged: EC 2.5/10 — ❌ NO TRADE.** PENDING.

## Run 9 — 2026-06-29 12:08 UTC (automated hourly)

Spot 0.80850 (vs 0.80836 prior, +1.4 pips, still ~65–115 pips above the PRIMARY LONG zone) | H4_ATR 0.00185 | D1_ATR 0.00501 (median 0.00524, still COMPRESSED) | D1 ADX 35.0 TRENDING unchanged. CB calendar clear through 07-01; econ calendar clear today (Warsh 13:00 + ISM PMI 14:00 UTC still beyond today's expiry). Latest closed 1H (11:00 UTC, RSI 40/Stoch 8) fired a bear pin — wrong direction for the LONG thesis (zone needs a bullish washout-reversal, not a bearish pin at an elevated level), discounted; zone remains untouched regardless. No re-forecast trigger. V1b ✅ intact. **Zone unchanged: EC 2.5/10 — ❌ NO TRADE.** PENDING.

## Run 10 — 2026-06-29 13:10 UTC (automated hourly)

Spot 0.80870 (vs 0.80850 prior, +2.0 pips, still ~85–88 pips above the PRIMARY LONG zone 0.7990–0.8020) | D1 ADX 35.0 TRENDING unchanged (floor 6.0 today). CB calendar clear through 07-01; econ calendar HIGH-impact 07-01 13:00 (Fed Warsh) + 14:00 (ISM Mfg PMI) — still beyond today's expiry. Latest closed 1H (12:00 UTC, RSI 47/Stoch 15) fired a bull engulf LONG-confirm — but zone (0.7990–0.8020) is still ~85 pips below spot, not zone-proximate, discounted. No re-forecast trigger. V1b ✅ intact. **Zone unchanged: EC 2.5/10 — ❌ NO TRADE.** PENDING.

## Run 11 — 2026-06-29 15:06 UTC (automated hourly)

Spot 0.80873 (vs 0.80870 prior, flat, still ~73–103 pips above the PRIMARY LONG zone) | H4_ATR 0.00185 | D1_ATR 0.00501 (median 0.00524, still COMPRESSED) | D1 Stoch 87.5 OVERBOUGHT / W%R −19.1 OVERBOUGHT (opposite of the washout LONG needs, E1 fails) | TTM squeeze OFF both D1/H4 (E3 fails) | D1 structure UP (BOS @0.80152) — trending, not a pullback (E4-style ADX gate fails). Latest closed 1H fired a Stoch-reclaim LONG-confirm (19→26) — but zone is still ~73 pips below spot, not zone-proximate, discounted. CB calendar clear through 07-01; econ calendar HIGH-impact 07-01 13:00 (Fed Warsh) + 14:00 (ISM Mfg PMI) — still beyond today's expiry. No re-forecast trigger. V1b ✅ intact (threshold 0.79860). **Zone unchanged: EC ~1.0/10 — ❌ NO TRADE.** PENDING.
