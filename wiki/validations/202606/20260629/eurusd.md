---
type: daily_validation
instrument: eurusd
date: 2026-06-29
week: 2026-W27
generated_utc: "2026-06-29T03:04:00Z"
run_type: automated_hourly
zones:
  - id: eurusd-2026-W27-PRIMARY
    direction: SHORT
    zone: [1.1450, 1.1490]
    entry_confluence: 1.0
    verdict: NO_TRADE
    e0: false
    reason: zone_unreached_no_extreme
  - id: eurusd-2026-W27-SECONDARY
    direction: SHORT
    zone: [1.1500, 1.1545]
    entry_confluence: 1.0
    verdict: NO_TRADE
    e0: false
    reason: zone_unreached_no_extreme
---

# EURUSD Daily Validation — 2026-06-29 (W27 Monday)

**Run:** 2026-06-29 03:04 UTC (automated hourly) | **Spot:** 1.13892 | H4_ATR: 0.00253 | D1_ATR: 0.00642 (median 0.00575) | D1 ADX 34.7 TRENDING

**Gates:** ✅ CB calendar clear | ✅ Econ calendar clear today (07-01 Warsh/ISM beyond expiry) | V1 ✅ | V1b ✅ (both zones)

**Macro:** DGS2 4.09% (drift +0.10 < 0.15, no re-forecast) | DXY 101.36 (no jump gate triggered against either SHORT zone)

---

## Zone 1 — PRIMARY SHORT 1.1450–1.1490

Both zones sit ~5–6 big-figures above spot (1.13898). Mean-reversion E0 (reversal AGAINST the approach into the zone) cannot fire — price hasn't approached the zone at all.

| # | Signal | Wt | Pass |
|---|--------|----|------|
| E0 reversal confirm | 3.0 | ❌ |
| E1 H4 oscillator still extreme | 2.5 | ❌ |
| E2 band touch H4 | 1.5 | ❌ |
| E3 non-trending ADX<25 | 1.0 | ❌ (ADX 34.7, trending) |
| E4 ATR compression | 1.0 | ❌ |
| E5 structure intact | 1.0 | ✅ |
| **TOTAL** | **10** | **1.0** |

**❌ NO TRADE — EC 1.0 < 5.0.** Zone unreached; D1 ADX>30 also stands against the fade per the constitution veto row. PENDING.

## Zone 2 — SECONDARY SHORT 1.1500–1.1545

Same inputs. **EC 1.0/10 — ❌ NO TRADE.** PENDING.

---

## Summary

| Zone | Verdict | EC |
|------|---------|----|
| PRIMARY SHORT 1.1450–1.1490 | ❌ NO TRADE | 1.0 |
| SECONDARY SHORT 1.1500–1.1545 | ❌ NO TRADE | 1.0 |

First session of W27. No structural change, no re-forecast trigger.

---

## Run 2 — 2026-06-29 04:17 UTC (automated hourly)

Spot 1.13838 (vs 1.13892 prior, −5 pips) | D1 ADX 34.7 unchanged, still trending against the fade. CB calendar clear; econ calendar still clear today. SHORT-direction bear engulf found on latest 1H but zones remain ~5–6 figures above spot — discounted, zone unreached. DXY 101.366, no jump gate against either zone. No re-forecast trigger. **Both zones unchanged: EC 1.0/10 — ❌ NO TRADE.** PENDING.

## Run 3 — 2026-06-29 05:07 UTC (automated hourly)

Spot 1.13861 (vs 1.13838 prior, +2 pips, still ~5–6 figures below both zones) | D1 RSI 32.7 / Stoch 15.1 / CCI −101.6 (oversold but D1 structure DOWN — ADX still trending against the fade, no change). CB calendar clear; econ calendar still clear today. No fresh E0 at either zone. DXY 101.384, flat, no jump gate against either SHORT zone. No re-forecast trigger. **Both zones unchanged: EC 1.0/10 — ❌ NO TRADE.** PENDING.

## Run 4 — 2026-06-29 06:16 UTC (automated hourly)

Spot 1.13932 (vs 1.13861 prior, +7 pips, still ~5–6 figures below both zones) | D1 Stoch 15.1 oversold / CCI −101.6 oversold, D1 structure DOWN (BOS DOWN @1.15028) — ADX still trending against the fade, no change. CB calendar clear through 07-01; econ calendar still clear today (07-01 Warsh/ISM beyond expiry). Fresh LONG-confirm (Stoch-reclaim + bull engulf) on latest 1H, but wrong-direction and zones remain ~5–6 figures above spot — discounted, zone unreached. DXY jump −0.11% (1d), no jump gate against either SHORT zone. No re-forecast trigger. V1b ✅ intact both zones. **Both zones unchanged: EC 1.0/10 — ❌ NO TRADE.** PENDING.

## Run 5 — 2026-06-29 08:10 UTC (automated daily /validate)

Spot 1.14046 (vs 1.13932 prior, +11 pips, still ~4–5 figures below both SHORT zones) | D1 ADX 24.1 TRANSITIONAL (chop risk, still against the fade) | D1 Stoch 15.1 oversold / CCI −101.6 oversold (D1 reversal extreme intact) | D1_ATR 0.00517 (median 0.00502, EXPANDING — compression fails). CB calendar clear through 07-01; econ calendar clear today (07-01 Warsh 13:00 + ISM PMI 14:00 UTC beyond today's expiry). Latest closed 1H: RSI 56/Stoch 71, SHORT-confirm band-reclaim fired at current spot (Keltner-high re-entry) — but spot still sits ~4–5 figures below both PRIMARY/SECONDARY boxes, not zone-proximate, discounted same as prior runs. DGS2 4.09% unchanged (drift <0.10%, no macro flip); DXY 101.238 flat, no jump gate against either SHORT zone. No re-forecast trigger. V1b ✅ intact both zones. **Both zones unchanged: EC 1.0/10 — ❌ NO TRADE.** PENDING.

## Run 6 — 2026-06-29 09:08 UTC (automated hourly)

Spot 1.13983 (vs 1.14046 prior, −6 pips, still ~4–5 figures below both SHORT zones) | D1 Stoch 15.1 oversold / CCI −101.6 oversold (D1 reversal extreme intact, unchanged). CB calendar clear through 07-01; econ calendar clear today (07-01 Warsh 13:00 + ISM PMI 14:00 UTC still beyond today's expiry). VIX 18.89 (spike +0.26), no veto. Latest closed 1H: RSI 53/Stoch 66 — no fresh reclaim toward SHORT; zones remain unreached. DGS2 4.09% unchanged (drift +0.10 < 0.15, no macro flip); DXY jump −0.049, no gate against either SHORT zone. No re-forecast trigger. V1b ✅ intact both zones. **Both zones unchanged: EC 1.0/10 — ❌ NO TRADE.** PENDING.

## Run 7 — 2026-06-29 10:08 UTC (automated hourly)

Spot 1.14039 (vs 1.13983 prior, +5.6 pips, still ~46–151 pips below both SHORT zones) | D1 Stoch 15.1/9.2 oversold / W%R −76.7 / CCI −101.6 oversold (D1 reversal extreme intact, unchanged) | D1 ADX 34.7 TRENDING | D1 structure DOWN (BOS @1.15028) / H4 structure UP (CHoCH @1.13899). CB calendar clear through 07-01; econ calendar clear today (07-01 Warsh 13:00 + ISM PMI 14:00 UTC still beyond today's expiry). 1H bull engulf fired but that's a LONG-direction signal, not the bearish reversal needed for either SHORT zone — discounted, and zones remain unreached regardless. DGS2 4.09% unchanged, no macro flip. No re-forecast trigger. V1b ✅ intact both zones. **Both zones unchanged: EC 1.0/10 — ❌ NO TRADE.** PENDING.

## Run 8 — 2026-06-29 11:13 UTC (automated hourly)

Spot 1.14060 (vs 1.14039 prior, +2 pips, still ~39–144 pips below both SHORT zones) | H4_ATR 0.00263 | D1_ATR 0.00642 (median 0.00575, still EXPANDING) | DGS2 4.09% (FALLING, unchanged, no macro flip) | DXY 101.210, no jump gate against either SHORT zone. CB calendar clear through 07-01; econ calendar clear today (07-01 Warsh 13:00 + ISM PMI 14:00 UTC still beyond today's expiry). No fresh reversal E0 toward SHORT this hour; zones remain unreached regardless. No re-forecast trigger. V1b ✅ intact both zones. **Both zones unchanged: EC 1.0/10 — ❌ NO TRADE.** PENDING.

## Run 9 — 2026-06-29 12:08 UTC (automated hourly)

Spot 1.14069 (vs 1.14060 prior, +0.9 pips, still ~38–143 pips below both SHORT zones) | H4_ATR 0.0026 | D1_ATR 0.00642 (median 0.00575, still EXPANDING) | D1 ADX 34.7 TRENDING unchanged, still against the fade. CB calendar clear through 07-01; econ calendar clear today (07-01 Warsh 13:00 + ISM PMI 14:00 UTC still beyond today's expiry). Latest closed 1H (11:00 UTC, RSI 59/Stoch 68) fired no E0 either direction. No re-forecast trigger. V1b ✅ intact both zones. **Both zones unchanged: EC 1.0/10 — ❌ NO TRADE.** PENDING.

## Run 10 — 2026-06-29 13:10 UTC (automated hourly)

Spot 1.14050 (vs 1.14069 prior, −1.9 pips, still ~40–145 pips below both SHORT zones 1.1450–1.1490 / 1.1500–1.1545) | D1 ADX 34.7 TRENDING unchanged, still against the fade (floor 6.0 today). CB calendar clear through 07-01; econ calendar HIGH-impact 07-01 13:00 (Fed Warsh) + 14:00 (ISM Mfg PMI) — still beyond today's expiry. Latest closed 1H (12:00 UTC) fired a bear engulf SHORT-confirm but neither zone is reached (gap unreached, discounted per anchor rule). No re-forecast trigger. V1b ✅ intact both zones. **Both zones unchanged: EC 1.0/10 — ❌ NO TRADE.** PENDING.

## Run 11 — 2026-06-29 15:06 UTC (automated hourly)

Spot 1.14193 (vs 1.14050 prior, +14.3 pips, still ~26–135 pips below both SHORT zones) | H4_ATR 0.0026 | D1_ATR 0.00642 (median 0.00575, still EXPANDING — E4 fails) | D1 Stoch 15.1 oversold / CCI −101.6 oversold (oversold extreme is the LONG-side read, opposite of what either SHORT zone needs — E1 fails) | DGS2 4.09% FALLING (USD soft, against SHORT) | H4 structure UP (CHoCH @1.13899, against SHORT, E5/E1 fail). CB calendar clear through 07-01; econ calendar HIGH-impact 07-01 13:00 (Fed Warsh) + 14:00 (ISM Mfg PMI) — still beyond today's expiry, no window block today. No E0 toward SHORT this hour; zones remain unreached regardless. No macro flip, no re-forecast trigger. V1b ✅ intact both zones (thresholds 1.14950 / 1.15500). **Both zones unchanged: EC 1.0/10 — ❌ NO TRADE.** PENDING.
