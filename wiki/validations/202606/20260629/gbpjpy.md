---
type: daily_validation
instrument: gbpjpy
date: 2026-06-29
week: 2026-W27
generated_utc: "2026-06-29T03:04:00Z"
run_type: automated_hourly
zones:
  - id: gbpjpy-2026-W27-PRIMARY
    direction: SHORT
    zone: [215.0, 215.6]
    entry_confluence: 2.0
    verdict: NO_TRADE
    e0: false
    reason: zone_unreached_below_floor
  - id: gbpjpy-2026-W27-COUNTER
    direction: LONG
    zone: [212.0, 212.55]
    entry_confluence: 2.0
    verdict: NO_TRADE
    e0: false
    reason: zone_unreached_below_floor
---

# GBPJPY Daily Validation — 2026-06-29 (W27 Monday)

**Run:** 2026-06-29 03:04 UTC (automated hourly) | **Spot:** 213.637 | H4_ATR: 0.364 | D1_ATR: 1.093 (median 0.950) | D1 ADX 15.3 RANGING

**Gates:** ✅ CB calendar clear | ✅ Econ calendar: 07-01 Bailey speaks ±30min (beyond today's 21:00 expiry) | V1 ✅ | V1b ✅ (both zones) | **Intervention watch (#4): ⚠ CAUTION — spot 213.608 is INSIDE the band (210.0–214.0), cap LONG conviction MEDIUM**. Watch refreshed today (`verified_through` → 06-29, no escalation).

---

## Zone 1 — PRIMARY SHORT 215.0–215.6

Spot is ~140–200 pips below this resistance zone.

| # | Signal | Wt | Pass |
|---|--------|----|------|
| E0 reversal confirm | 3.0 | ❌ |
| E1 H4 still overbought | 2.5 | ❌ |
| E2 session (outside 12–16 UTC = 0.75 only / inside 13–15 = anti) | 1.5 | ❌ (off-session at run time) |
| E3 H1 timing structure | 1.0 | ❌ |
| E4 structure intact | 1.0 | ✅ |
| E5 not extended (ADX<25) | 1.0 | ✅ (15.3) |
| **TOTAL** | **10** | **2.0** |

**❌ NO TRADE — EC 2.0 < 5.0.** PENDING.

## Zone 2 — COUNTER LONG 212.0–212.55

Spot is only ~106 pips above this zone — closest approach of any gbpjpy box today, but still no band touch. Pull flagged both a LONG and SHORT 1H pin at current spot; both discounted as not zone-proximate.

Same component breakdown (E1 washout-still-live false at current bar). **EC 2.0/10 — ❌ NO TRADE.** Would be capped MEDIUM conviction anyway per intervention CAUTION band even if EC cleared. PENDING.

---

## Summary

| Zone | Verdict | EC |
|------|---------|----|
| PRIMARY SHORT 215.0–215.6 | ❌ NO TRADE | 2.0 |
| COUNTER LONG 212.0–212.55 | ❌ NO TRADE | 2.0 |

No macro/VIX rows for gbpjpy (dead). No re-forecast trigger.

---

## Run 2 — 2026-06-29 04:17 UTC (automated hourly)

Spot 213.528 (vs 213.637 prior, essentially flat) | D1 ADX 15.3 unchanged, ranging. CB calendar clear; econ calendar 07-01 Bailey beyond expiry. **Intervention watch (#4) re-confirmed: ⚠ CAUTION — spot 213.528 still inside the band (210.0–214.0), LONG conviction capped MEDIUM** (no escalation). No fresh E0 this run; off-session for both zones' session-window component. No re-forecast trigger. **Both zones unchanged: EC 2.0/10 — ❌ NO TRADE.** PENDING.

## Run 3 — 2026-06-29 05:07 UTC (automated hourly)

Spot 213.661 (vs 213.528 prior, +13 pips) | D1 RSI 46.4, D1 ADX 15.3 unchanged, ranging; D1+H4 TTM squeeze still ON. CB calendar clear; econ calendar 07-01 Bailey beyond expiry. **Intervention watch (#4) re-confirmed: ⚠ CAUTION — spot 213.661 still inside the band (210.0–214.0), LONG conviction capped MEDIUM** (no escalation). No fresh E0 zone-proximate; off-session for both zones' session-window component. No re-forecast trigger. **Both zones unchanged: EC 2.0/10 — ❌ NO TRADE.** PENDING.

## Run 4 — 2026-06-29 06:16 UTC (automated hourly)

Spot 213.768 (vs 213.661 prior, +11 pips) | D1 ADX 15.3 unchanged, ranging; D1+H4 TTM squeeze still ON (D1 11 bars, H4 6 bars). CB calendar clear through 07-01; econ calendar 07-01 Bailey ±30min beyond today's expiry. **Intervention watch (#4) re-confirmed: ⚠ CAUTION — spot 213.768 still inside the band (210.0–214.0), LONG conviction capped MEDIUM** (no escalation). No fresh E0 fired either direction this run; off-session for both zones' session-window component. No re-forecast trigger. V1b ✅ intact both zones. **Both zones unchanged: EC 2.0/10 — ❌ NO TRADE.** PENDING.

## Run 5 — 2026-06-29 08:13 UTC (automated daily /validate)

Spot 213.814 (vs 213.768 prior, +5 pips, essentially flat) | D1 ADX 15.3 RANGING unchanged | D1 TTM squeeze still ON (11 bars) + H4 W%R −15.0 / CCI 106.7 OVERBOUGHT (>+100) — pullback-extreme reading on H4, but D1 RSI/Stoch (25.2/26.5, mid) not at a clean SHORT-extreme for E1. CB calendar clear through 07-01; econ calendar clear today (07-01 Bailey 13:00 UTC beyond today's expiry). **Intervention watch (#4) re-confirmed: ⚠ CAUTION — spot 213.814 still inside the band (210.0–214.0), LONG conviction capped MEDIUM** (jawboning still dated 06-19, no fresh escalation specific to gbpjpy). Latest closed 1H: RSI-reclaim 69→60 + band-reclaim (Keltner-high re-entry), both SHORT-confirm — but PRIMARY SHORT zone (215.0–215.6) is ~120 pips above spot and COUNTER LONG (212.0–212.55) is ~126 pips below, neither zone-proximate, discounted same as prior runs. IUDSOIA 3.73% (context only, dead for gbpjpy). No re-forecast trigger (price-driven only). V1b ✅ intact both zones. **Both zones unchanged: EC 2.0/10 — ❌ NO TRADE.** PENDING.

## Run 6 — 2026-06-29 09:08 UTC (automated hourly)

Spot 213.832 (vs 213.814 prior, +1.8 pips, essentially flat) | D1 TTM squeeze still ON (11b) + H4 W%R −15.0 / CCI 106.7 OVERBOUGHT (>+100, pullback-extreme on H4, unchanged) | D1 RSI/Stoch not at clean SHORT-extreme. CB calendar clear through 07-01; econ calendar clear today (07-01 Bailey 13:00 UTC still beyond today's expiry). **Intervention watch (#4) re-confirmed: ⚠ CAUTION — spot 213.832 still inside the band (210.0–214.0), LONG conviction capped MEDIUM** (jawboning unchanged, no fresh escalation specific to gbpjpy). Latest closed 1H: RSI 56/Stoch 76, Stoch-reclaim SHORT-confirm fired — but PRIMARY SHORT zone (215.0–215.6) is still ~120 pips above spot and COUNTER LONG (212.0–212.55) ~128 pips below, neither zone-proximate, discounted. IUDSOIA 3.73% (context only). No re-forecast trigger (price-driven only). V1b ✅ intact both zones. **Both zones unchanged: EC 2.0/10 — ❌ NO TRADE.** PENDING.

## Run 7 — 2026-06-29 10:08 UTC (automated hourly)

Spot 213.925 (vs 213.832 prior, +9.3 pips) | D1 ADX 15.3 RANGING | D1 TTM squeeze still ON (11b) | H4 W%R −15.0 OVERBOUGHT / CCI 106.7 OVERBOUGHT (>+100, pullback-extreme on H4, unchanged) | D1 structure MIXED (BOS @215.24) / H4 UP (BOS @213.83, fresh this bar). CB calendar clear through 07-01; econ calendar clear today (Bailey 13:00 UTC still beyond today's expiry). **Intervention watch (#4) re-confirmed: ⚠ CAUTION — spot 213.925 still inside the band (210.0–214.0), LONG conviction capped MEDIUM.** 1H bull engulf fired but PRIMARY SHORT (215.0–215.6) still ~108 pips above spot and COUNTER LONG (212.0–212.55) ~138 pips below — neither zone-proximate, discounted. No re-forecast trigger. V1b ✅ intact both zones. **Both zones unchanged: EC 2.0/10 — ❌ NO TRADE.** PENDING.

## Run 8 — 2026-06-29 11:13 UTC (automated hourly)

Spot 214.116 (vs 213.925 prior, +19 pips) | H4_ATR 0.382 | D1_ATR 1.093 (median 0.95, EXPANDING). CB calendar clear through 07-01; econ calendar clear today (Bailey 13:00 UTC still beyond today's expiry). **Intervention watch (#4) ESCALATED: 🛑 HARD_BLOCK new LONGS — spot 214.116 has crossed ABOVE the 214.0 active MoF level (prior runs had it in the 210–214 CAUTION band only).** This directly affects the COUNTER LONG zone (212.0–212.55, still ~156 pips below spot, untouched) — any future LONG fill there is now standing-rule blocked, not just capped, until spot drops back below the level. No fresh E0 this hour; PRIMARY SHORT (215.0–215.6) still ~88 pips above spot, untouched. No re-forecast trigger (price-driven only). V1b ✅ intact both zones. **Both zones unchanged: EC 2.0/10 — ❌ NO TRADE.** PENDING. Flag for _HOT: intervention HARD_BLOCK now active for gbpjpy longs (was CAUTION).

## Run 9 — 2026-06-29 12:08 UTC (automated hourly)

Spot 214.148 (vs 214.116 prior, +3.2 pips) | H4_ATR 0.387 | D1_ATR 1.093 (median 0.95, EXPANDING) | D1 ADX 15.3 RANGING unchanged. CB calendar clear through 07-01; econ calendar clear today (Bailey 13:00 UTC still beyond today's expiry). **Intervention watch (#4) re-confirmed: 🛑 HARD_BLOCK new LONGS — spot 214.148 still above the 214.0 active MoF level.** COUNTER LONG zone (212.0–212.55, still ~159–214 pips below spot, untouched) remains standing-rule blocked if/when reached. Latest closed 1H (11:00 UTC, RSI 68/Stoch 95, overbought) fired no E0 either direction; PRIMARY SHORT (215.0–215.6) still ~85–145 pips above spot, untouched. No re-forecast trigger (price-driven only). V1b ✅ intact both zones. **Both zones unchanged: EC 2.0/10 — ❌ NO TRADE.** PENDING.

## Run 10 — 2026-06-29 13:10 UTC (automated hourly)

Spot 214.302 (vs 214.148 prior, +15.4 pips) | D1 ADX 15.3 RANGING unchanged (floor 6.0 today). CB calendar clear through 07-01; econ calendar HIGH-impact 07-01 13:00 (BoE Bailey) — still beyond today's expiry. **Intervention watch (#4) re-confirmed: 🛑 HARD_BLOCK new LONGS — spot 214.302 still above the 214.0 active MoF level.** COUNTER LONG zone (212.0–212.55, still ~175–230 pips below spot, untouched) remains standing-rule blocked if/when reached. Latest closed 1H (12:00 UTC, RSI 69/Stoch 94, overbought) fired a bear pin SHORT-confirm; PRIMARY SHORT (215.0–215.6) still ~70–130 pips above spot, untouched, not zone-proximate, discounted. No re-forecast trigger. V1b ✅ intact both zones. **Both zones unchanged: EC 2.0/10 — ❌ NO TRADE.** PENDING.

## Run 11 — 2026-06-29 15:06 UTC (automated hourly)

Spot 214.485 (vs 214.302 prior, +18.3 pips) | D1 Stoch 25.2 / W%R −68.9 / CCI −55.0 (mild, no clean extreme either side) | D1 TTM squeeze ON (11b) | H4 Stoch 85.7 OVERBOUGHT / W%R −1.2 OVERBOUGHT / CCI 137.1 OVERBOUGHT (>+100) | D1 structure MIXED (BOS UP @215.24) / H4 BOS UP @213.835 (fresh). **Intervention watch (#4) re-confirmed: 🛑 HARD_BLOCK new LONGS — spot 214.485 still above the 214.0 active MoF level.** COUNTER LONG zone (212.0–212.55, ~1.93–2.49 below spot, untouched) remains standing-rule blocked — written to ledger as NO_TRADE --hard-block this run (clears any stale lock). PRIMARY SHORT (215.0–215.6, ~0.52–1.12 above spot) untouched, no SHORT-confirm fired this hour. CB calendar clear through 07-01; econ calendar HIGH-impact 07-01 13:00 (BoE Bailey) — still beyond today's expiry. No re-forecast trigger. V1b ✅ intact both zones (thresholds 215.650 / 211.950). **Both zones: ❌ NO TRADE** (COUNTER LONG — hard-block; PRIMARY SHORT — EC ~0/10, zone unreached). PENDING.
