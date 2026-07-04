---
type: daily_validation
instrument: gbpusd
date: 2026-06-29
week: 2026-W27
generated_utc: "2026-06-29T03:04:00Z"
run_type: automated_hourly
zones:
  - id: gbpusd-2026-W27-PRIMARY
    direction: SHORT
    zone: [1.3340, 1.3390]
    entry_confluence: 1.0
    verdict: NO_TRADE
    e0: false
    reason: zone_unreached_no_extreme
  - id: gbpusd-2026-W27-COUNTER
    direction: LONG
    zone: [1.3140, 1.3180]
    entry_confluence: 3.5
    verdict: NO_TRADE
    e0: false
    reason: zone_unreached_below_floor
---

# GBPUSD Daily Validation — 2026-06-29 (W27 Monday)

**Run:** 2026-06-29 03:04 UTC (automated hourly) | **Spot:** 1.32053 | H4_ATR: 0.00269 | D1_ATR: 0.00809 (median 0.00754) | D1 ADX 27.5 TRENDING

**Gates:** ✅ CB calendar clear | ✅ Econ calendar clear today (07-01 Bailey/Warsh/ISM beyond expiry) | V1 ✅ | V1b ✅ (both zones)

**Macro:** DGS2 4.09% (drift +0.10 < 0.15) | DXY 101.35, no jump gate triggered against PRIMARY SHORT.

---

## Zone 1 — PRIMARY SHORT 1.3340–1.3390

Spot 1.32053 is ~130–150 pips below the zone. 03:04 re-run: pull flagged a LONG-confirm (Stoch-reclaim + bull engulf) on the latest 1H, but it's not zone-proximate to this SHORT zone (price far below resistance) and wrong-direction anyway — discounted.

| # | Signal | Wt | Pass |
|---|--------|----|------|
| E0 reversal confirm | 3.0 | ❌ (pattern present but not at zone) |
| E1 D1 oscillator still extreme | 2.5 | ❌ |
| E2 H1 oscillator extreme | 1.5 | ❌ |
| E3 non-trending ADX<25 | 1.0 | ❌ (27.5) |
| E4 structure intact | 1.0 | ✅ |
| E5 ATR compression | 1.0 | ❌ |
| **TOTAL** | **10** | **1.0** |

**❌ NO TRADE — EC 1.0 < 5.0.** PENDING.

## Zone 2 — COUNTER LONG 1.3140–1.3180

Spot is ~260 pips above this dip-buy zone. The fresh LONG-confirm E0 (Stoch-reclaim+engulf) fired at current spot, not at the zone — still discounted as not zone-proximate (E0 weight stays 0).

| # | Signal | Wt | Pass |
|---|--------|----|------|
| E0 reversal confirm | 3.0 | ❌ |
| E1 D1 oscillator still extreme | 2.5 | ✅ |
| E2 H1 oscillator extreme | 1.5 | ❌ |
| E3 non-trending ADX<25 | 1.0 | ❌ |
| E4 structure intact | 1.0 | ✅ |
| E5 ATR compression | 1.0 | ❌ |
| **TOTAL** | **10** | **3.5** |

**❌ NO TRADE — EC 3.5 < 5.0.** PENDING. (D1 oscillator already extreme but zone untouched and ADX still trending against the fade.)

---

## Summary

| Zone | Verdict | EC |
|------|---------|----|
| PRIMARY SHORT 1.3340–1.3390 | ❌ NO TRADE | 1.0 |
| COUNTER LONG 1.3140–1.3180 | ❌ NO TRADE | 3.5 |

First session of W27. No re-forecast trigger.

---

## Run 2 — 2026-06-29 04:17 UTC (automated hourly)

Spot 1.31979 (vs 1.32053 prior, −7 pips) | D1 ADX 27.5 unchanged. CB calendar clear; econ calendar still clear today (07-01 Bailey/Warsh/ISM beyond expiry). No fresh E0 this run (prior off-zone LONG-confirm has lapsed). DXY 101.372, no jump gate against PRIMARY SHORT. No re-forecast trigger. **Both zones unchanged: PRIMARY SHORT EC 1.0/10, COUNTER LONG EC 3.5/10 — both ❌ NO TRADE.** PENDING.

## Run 3 — 2026-06-29 05:07 UTC (automated hourly)

Spot 1.32038 (vs 1.31979 prior, +6 pips) | D1 RSI 35.8 / Stoch 13.1 / W%R −81.9 / CCI −106.3 (oversold, D1 structure DOWN, H4 UP — ADX still trending against the fade, no change). CB calendar clear; econ calendar still clear today (07-01 Bailey/Warsh/ISM beyond expiry). Fresh 1H pins both directions reported but neither zone-proximate — discounted same as prior runs. DXY 101.382, no jump gate against PRIMARY SHORT. No re-forecast trigger. **Both zones unchanged: PRIMARY SHORT EC 1.0/10, COUNTER LONG EC 3.5/10 — both ❌ NO TRADE.** PENDING.

## Run 4 — 2026-06-29 06:16 UTC (automated hourly)

Spot 1.32115 (vs 1.32038 prior, +8 pips) | D1 Stoch 13.1 oversold / W%R −81.9 oversold / CCI −106.3 oversold (D1 structure DOWN @1.33266, H4 BOS UP @1.32192) — ADX still trending against the fade, no change. CB calendar clear through 07-01; econ calendar still clear today (07-01 Bailey/Warsh/ISM beyond expiry). Fresh LONG-confirm (bull engulf) at current spot, ~260 pips above COUNTER LONG zone — discounted, not zone-proximate. DXY jump −0.11% (1d), no jump gate against PRIMARY SHORT. No re-forecast trigger. V1b ✅ intact both zones. **Both zones unchanged: PRIMARY SHORT EC 1.0/10, COUNTER LONG EC 3.5/10 — both ❌ NO TRADE.** PENDING.

## Run 5 — 2026-06-29 08:10 UTC (automated daily /validate)

Spot 1.32139 (vs 1.32115 prior, +2 pips, flat) | D1 ADX 21.6 TRANSITIONAL (chop, against the fade) | D1 Stoch 13.1 oversold / W%R −81.9 oversold / CCI −106.3 oversold (D1 reversal extreme intact, compression signal per pull) | D1_ATR 0.00498 (median 0.00495, EXPANDING — compression fails). CB calendar clear through 07-01; econ calendar clear today (07-01 Bailey 13:00 + Warsh 13:00 + ISM PMI 14:00 UTC beyond today's expiry). Latest closed 1H: RSI 56/Stoch 75, SHORT-confirm band-reclaim fired at current spot (Keltner-high re-entry) — wrong zone (PRIMARY SHORT is ~120 pips above spot, not reached) and COUNTER LONG remains ~260 pips below spot, neither zone-proximate. DXY 101.236 flat, no jump gate against PRIMARY SHORT. No re-forecast trigger. V1b ✅ intact both zones. **Both zones unchanged: PRIMARY SHORT EC 1.0/10, COUNTER LONG EC 3.5/10 — both ❌ NO TRADE.** PENDING.

## Run 6 — 2026-06-29 09:08 UTC (automated hourly)

Spot 1.32129 (vs 1.32139 prior, −1 pip, flat) | D1 Stoch 13.1 oversold / W%R −81.9 oversold / CCI −106.3 oversold (D1 reversal extreme intact, unchanged). CB calendar clear through 07-01; econ calendar clear today (07-01 Bailey 13:00 + Warsh 13:00 + ISM PMI 14:00 UTC still beyond today's expiry). VIX 18.89 (spike +0.26), no veto. Latest closed 1H: RSI 51/Stoch 68 — no fresh reclaim; PRIMARY SHORT still ~120 pips above spot, COUNTER LONG still ~260 pips below, neither zone-proximate. DXY jump −0.049, no gate against PRIMARY SHORT. No re-forecast trigger. V1b ✅ intact both zones. **Both zones unchanged: PRIMARY SHORT EC 1.0/10, COUNTER LONG EC 3.5/10 — both ❌ NO TRADE.** PENDING.

## Run 7 — 2026-06-29 10:08 UTC (automated hourly)

Spot 1.32166 (vs 1.32129 prior, +3.7 pips) | D1 ADX 27.5 TRENDING | D1 Stoch 13.1/12.9 / W%R −81.9 / CCI −106.3 oversold (D1 reversal extreme intact, unchanged) | H4 TTM squeeze ON 1b | D1 structure DOWN (BOS @1.33266) / H4 structure UP (BOS @1.32192). CB calendar clear through 07-01; econ calendar clear today (Bailey/Warsh 13:00 + ISM PMI 14:00 UTC still beyond today's expiry). 1H bull engulf fired — relevant to the COUNTER LONG thesis but that zone (1.3140–1.3180) is still ~260 pips below spot, not proximate; PRIMARY SHORT (1.3340–1.3390) still ~175 pips above, untouched. No re-forecast trigger. V1b ✅ intact both zones. **Both zones unchanged: PRIMARY SHORT EC 1.0/10, COUNTER LONG EC 3.5/10 — both ❌ NO TRADE.** PENDING.

## Run 8 — 2026-06-29 11:13 UTC (automated hourly)

Spot 1.32258 (vs 1.32166 prior, +0.9 pips) | H4_ATR 0.00278 | D1_ATR 0.00809 (median 0.00754, EXPANDING) | DGS2 4.09% FALLING unchanged | DXY 101.211, no jump gate against PRIMARY SHORT. CB calendar clear through 07-01; econ calendar clear today (Bailey/Warsh 13:00 + ISM PMI 14:00 UTC still beyond today's expiry). No fresh E0 this hour; PRIMARY SHORT (1.3340–1.3390) still ~132 pips above spot, COUNTER LONG (1.3140–1.3180) still ~78 pips below — neither zone-proximate. No re-forecast trigger. V1b ✅ intact both zones. **Both zones unchanged: PRIMARY SHORT EC 1.0/10, COUNTER LONG EC 3.5/10 — both ❌ NO TRADE.** PENDING.

## Run 9 — 2026-06-29 12:08 UTC (automated hourly)

Spot 1.32305 (vs 1.32258 prior, +4.7 pips) | H4_ATR 0.00281 | D1_ATR 0.00809 (median 0.00754, EXPANDING) | D1 ADX 27.5 TRENDING unchanged, still against the fade. CB calendar clear through 07-01; econ calendar clear today (Bailey/Warsh 13:00 + ISM PMI 14:00 UTC still beyond today's expiry). Latest closed 1H (11:00 UTC, RSI 63/Stoch 83) fired no E0 either direction; PRIMARY SHORT (1.3340–1.3390) still ~95–115 pips above spot, COUNTER LONG (1.3140–1.3180) still ~125–165 pips below — neither zone-proximate. No re-forecast trigger. V1b ✅ intact both zones. **Both zones unchanged: PRIMARY SHORT EC 1.0/10, COUNTER LONG EC 3.5/10 — both ❌ NO TRADE.** PENDING.

## Run 10 — 2026-06-29 13:10 UTC (automated hourly)

Spot 1.32381 (vs 1.32305 prior, +7.6 pips) | D1 ADX 27.5 TRENDING unchanged, still against the fade (floor 6.0 today). CB calendar clear through 07-01; econ calendar HIGH-impact 07-01 13:00 (BoE Bailey + Fed Warsh) + 14:00 (ISM Mfg PMI) — still beyond today's expiry. Latest closed 1H (12:00 UTC, RSI 61/Stoch 88) fired a bear pin SHORT-confirm — PRIMARY SHORT (1.3340–1.3390) still ~95–100 pips above spot, COUNTER LONG (1.3140–1.3180) still ~140–165 pips below — neither zone-proximate. No re-forecast trigger. V1b ✅ intact both zones. **Both zones unchanged: PRIMARY SHORT EC 1.0/10, COUNTER LONG EC 3.5/10 — both ❌ NO TRADE.** PENDING.

## Run 11 — 2026-06-29 15:06 UTC (automated hourly)

Spot 1.32475 (vs 1.32381 prior, +9.4 pips, sitting between both zones — PRIMARY SHORT 1.3340–1.3390 ~85–135 pips above, COUNTER LONG 1.3140–1.3180 ~295–335 pips below) | D1 Stoch 13.1 oversold / W%R −81.9 oversold / CCI −106.3 oversold (D1 extreme is COUNTER LONG-side, E1 passes for that zone's thesis but zone not touched) | H4 Stoch 80.1 OVERBOUGHT / D1 structure DOWN (BOS @1.33266) / H4 BOS UP @1.32315 (fresh). CB calendar clear through 07-01; econ calendar HIGH-impact 07-01 13:00 (BoE Bailey + Fed Warsh) + 14:00 (ISM Mfg PMI) — still beyond today's expiry. No E0 fired toward either zone this hour; both remain unreached. No re-forecast trigger. V1b ✅ intact both zones (thresholds 1.33960 / 1.31340). **Both zones unchanged: PRIMARY SHORT EC 1.0/10, COUNTER LONG EC 3.5/10 — both ❌ NO TRADE.** PENDING.
