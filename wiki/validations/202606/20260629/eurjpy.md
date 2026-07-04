---
type: daily_validation
instrument: eurjpy
date: 2026-06-29
week: 2026-W27
generated_utc: "2026-06-29T03:04:00Z"
run_type: automated_hourly
zones:
  - id: eurjpy-2026-W27-PRIMARY
    direction: LONG
    zone: [183.0, 183.6]
    entry_confluence: 2.0
    verdict: NO_TRADE
    e0: false
    reason: zone_unreached_below_floor
  - id: eurjpy-2026-W27-SECONDARY
    direction: SHORT
    zone: [186.0, 186.5]
    entry_confluence: 2.0
    verdict: NO_TRADE
    e0: false
    reason: zone_unreached_below_floor
---

# EURJPY Daily Validation — 2026-06-29 (W27 Monday)

**Run:** 2026-06-29 03:04 UTC (automated hourly) | **Spot:** 184.255 | H4_ATR: 0.342 | D1_ATR: 0.889 (median 0.765) | D1 ADX 18.8 RANGING

**Gates:** ✅ CB calendar clear | ✅ Econ calendar clear today | V1 ✅ | V1b ✅ (both zones) | **Intervention watch (#4): ⚠ CAUTION — spot 184.235 is INSIDE the band (182.0–185.0), cap LONG conviction MEDIUM** (no hard block; JPY crosses slam in sympathy with MoF action). Watch refreshed today (`verified_through` → 06-29, no escalation).

---

## Zone 1 — PRIMARY LONG 183.0–183.6

Spot is ~64–124 pips above the zone, between PRIMARY and SECONDARY.

| # | Signal | Wt | Pass |
|---|--------|----|------|
| E0 reversal confirm | 3.0 | ❌ |
| E1 washout still live (LONG) | 2.5 | ❌ |
| E2 session window (NY/London overlap 12–16 UTC) | 1.5 | ❌ (off-session at run time) |
| E3 calm regime intact | 1.0 | ❌ |
| E4 structure intact | 1.0 | ✅ |
| E5 not extended (ADX<25) | 1.0 | ✅ (18.8) |
| **TOTAL** | **10** | **2.0** |

**❌ NO TRADE — EC 2.0 < 5.0.** Conviction would be capped MEDIUM anyway per the intervention CAUTION band. PENDING.

## Zone 2 — SECONDARY SHORT 186.0–186.5

Same component breakdown (E1 evaluated for overbought-still-live, also false at current bar). **EC 2.0/10 — ❌ NO TRADE.** PENDING.

---

## Summary

| Zone | Verdict | EC |
|------|---------|----|
| PRIMARY LONG 183.0–183.6 | ❌ NO TRADE | 2.0 |
| SECONDARY SHORT 186.0–186.5 | ❌ NO TRADE | 2.0 |

Macro NONE for eurjpy (context only). No re-forecast trigger (price-driven only — T3/T4).

---

## Run 2 — 2026-06-29 04:17 UTC (automated hourly)

Spot 184.165 (vs 184.255 prior, essentially flat) | D1 ADX 18.8 unchanged, ranging. CB calendar clear; econ calendar still clear today. **Intervention watch (#4) re-confirmed: ⚠ CAUTION — spot 184.165 still inside the band (182.0–185.0), LONG conviction capped MEDIUM** (no escalation, jawboning unchanged). No fresh E0 this run; off-session for both zones' session-window component. No re-forecast trigger. **Both zones unchanged: EC 2.0/10 — ❌ NO TRADE.** PENDING.

## Run 3 — 2026-06-29 05:07 UTC (automated hourly)

Spot 184.238 (vs 184.165 prior, +7 pips) | D1 RSI 42.8, D1 ADX 18.8 unchanged, ranging. CB calendar clear; econ calendar still clear today. **Intervention watch (#4) re-confirmed: ⚠ CAUTION — spot 184.238 still inside the band (182.0–185.0), LONG conviction capped MEDIUM** (no escalation, jawboning unchanged from 06-19). No fresh E0 zone-proximate; off-session for both zones' session-window component. No re-forecast trigger. **Both zones unchanged: EC 2.0/10 — ❌ NO TRADE.** PENDING.

## Run 4 — 2026-06-29 06:16 UTC (automated hourly)

Spot 184.357 (vs 184.238 prior, +12 pips) | D1 ADX 18.8 unchanged, ranging; TTM squeeze OFF (D1/H4) — no effect on score (E3 calm-row was already failing). CB calendar clear through 07-01; econ calendar clear in window. **Intervention watch (#4) re-confirmed: ⚠ CAUTION — spot 184.357 still inside the band (182.0–185.0), LONG conviction capped MEDIUM** (no escalation, jawboning unchanged from 06-19). Fresh LONG-confirm (bull engulf) at current spot, but spot already above PRIMARY LONG zone (183.0–183.6) — reversal away from, not into, the zone, discounted. No re-forecast trigger (price-driven only — T3/T4, no trigger). V1b ✅ intact both zones. **Both zones unchanged: EC 2.0/10 — ❌ NO TRADE.** PENDING.

## Run 5 — 2026-06-29 08:12 UTC (automated daily /validate)

Spot 184.543 (vs 184.357 prior, +19 pips) | D1 ADX 18.8 RANGING unchanged | D1 RSI 60 (mid, not washout), D1 Stoch 24.1 (mid) — neither LONG washout nor SHORT overbought extreme cleanly live at D1. CB calendar clear through 07-01; econ calendar CLEAR — no high-impact EUR/JPY releases in the 2-day window today (improvement vs prior runs' Bailey-adjacent reads, which were GBP-only anyway and not gating eurjpy). **Intervention watch (#4) re-confirmed: ⚠ CAUTION — spot 184.543 still inside the band (182.0–185.0), LONG conviction capped MEDIUM** (jawboning still dated 06-19, no fresh escalation for this pair specifically). Latest closed 1H: RSI-reclaim 69→60 + band-reclaim (Keltner-high re-entry), both SHORT-confirm — but spot sits well below SECONDARY SHORT zone (186.0–186.5, ~145 pips away) and above PRIMARY LONG zone top (183.6, ~94 pips away, wrong direction for a LONG reclaim anyway) — neither zone-proximate, discounted. ECBDFR 2.25% (context only, dead for eurjpy). No re-forecast trigger (price-driven only — T3/T4, no trigger). V1b ✅ intact both zones. **Both zones unchanged: EC 2.0/10 — ❌ NO TRADE.** PENDING.

## Run 6 — 2026-06-29 09:08 UTC (automated hourly)

Spot 184.484 (vs 184.543 prior, −5.9 pips, essentially flat) | no clean D1 extreme reported (mid-range, same as run 5). CB calendar clear through 07-01; econ calendar clear — no high-impact EUR/JPY releases in window. **Intervention watch (#4) re-confirmed: ⚠ CAUTION — spot 184.484 still inside the band (182.0–185.0), LONG conviction capped MEDIUM** (jawboning unchanged, no fresh escalation specific to eurjpy). Latest closed 1H: RSI 58/Stoch 78, Stoch-reclaim SHORT-confirm fired — but SECONDARY SHORT zone (186.0–186.5) is still ~150 pips above spot, not zone-proximate, discounted (E0 stays 0). PRIMARY LONG zone (183.0–183.6) ~88 pips below spot, also untouched. No re-forecast trigger (price-driven only). V1b ✅ intact both zones. **Both zones unchanged: EC 2.0/10 — ❌ NO TRADE.** PENDING.

## Run 7 — 2026-06-29 10:08 UTC (automated hourly)

Spot 184.629 (vs 184.484 prior, +14.5 pips) | D1 ADX 18.8 RANGING (favors reversal) | D1 Stoch 24.1/18.2 mid / W%R −66.4 / CCI −89.7 (not a clean extreme either side) | D1 structure DOWN (CHoCH @184.03) / H4 UP (CHoCH @184.11). CB calendar clear through 07-01; econ calendar clear — no high-impact EUR/JPY releases in window. **Intervention watch (#4) re-confirmed: ⚠ CAUTION — spot 184.629 still inside the band (182.0–185.0), LONG conviction capped MEDIUM.** Latest closed 1H bull engulf fired but SECONDARY SHORT (186.0–186.5) still ~137 pips above spot and PRIMARY LONG (183.0–183.6) ~103 pips below — neither zone-proximate, discounted. No re-forecast trigger. V1b ✅ intact both zones. **Both zones unchanged: EC 2.0/10 — ❌ NO TRADE.** PENDING.

## Run 8 — 2026-06-29 11:13 UTC (automated hourly)

Spot 184.613 (vs 184.629 prior, −1.6 pips, essentially flat) | H4_ATR 0.359 | D1_ATR 0.889 (median 0.765, EXPANDING). CB calendar clear through 07-01; econ calendar clear — no high-impact EUR/JPY releases in window. **Intervention watch (#4) re-confirmed: ⚠ CAUTION — spot 184.613 still inside the band (182.0–185.0), LONG conviction capped MEDIUM.** Latest closed 1H bull pin fired but SECONDARY SHORT (186.0–186.5) still ~137 pips above spot and PRIMARY LONG (183.0–183.6) ~101 pips below — neither zone-proximate, discounted. No re-forecast trigger (price-driven only). V1b ✅ intact both zones. **Both zones unchanged: EC 2.0/10 — ❌ NO TRADE.** PENDING.

## Run 9 — 2026-06-29 12:08 UTC (automated hourly)

Spot 184.623 (vs 184.613 prior, +1.0 pip, essentially flat) | H4_ATR 0.352 | D1_ATR 0.889 (median 0.765, EXPANDING) | D1 ADX 18.8 RANGING unchanged. CB calendar clear through 07-01; econ calendar clear — no high-impact EUR/JPY releases in window. **Intervention watch (#4) re-confirmed: ⚠ CAUTION — spot 184.623 still inside the band (182.0–185.0), LONG conviction capped MEDIUM** (jawboning still dated 06-19, no fresh escalation specific to eurjpy). Latest closed 1H (11:00 UTC, RSI 64/Stoch 87) fired a bull pin — but SECONDARY SHORT (186.0–186.5) still ~138 pips above spot and PRIMARY LONG (183.0–183.6) ~102 pips below — neither zone-proximate, discounted. No re-forecast trigger (price-driven only). V1b ✅ intact both zones. **Both zones unchanged: EC 2.0/10 — ❌ NO TRADE.** PENDING.

## Run 10 — 2026-06-29 13:10 UTC (automated hourly)

Spot 184.623 (vs 184.623 prior, flat) | D1 ADX 18.8 RANGING unchanged (floor 6.0 today). CB calendar clear through 07-01; econ calendar clear today — no high-impact EUR/JPY releases. **Intervention watch (#4) re-confirmed: ⚠ CAUTION — spot 184.623 still inside the band (182.0–185.0, MoF level 185.0), LONG conviction capped MEDIUM** (jawboning still dated 06-19/06-29, no fresh eurjpy-specific escalation). Latest closed 1H (12:00 UTC, RSI 60/Stoch 87) fired a bear engulf SHORT-confirm — but SECONDARY SHORT (186.0–186.5) still ~1.4 above spot and PRIMARY LONG (183.0–183.6) ~1.0 below — neither zone-proximate, discounted. No re-forecast trigger. V1b ✅ intact both zones. **Both zones unchanged: EC 2.0/10 — ❌ NO TRADE.** PENDING.

## Run 11 — 2026-06-29 15:06 UTC (automated hourly)

Spot 184.921 (vs 184.623 prior, +29.8 pips, sitting between both zones — PRIMARY LONG 183.0–183.6 ~1.32 below, SECONDARY SHORT 186.0–186.5 ~1.08 above) | D1 Stoch 24.1 / W%R −66.4 / CCI −89.7 (mild, not a clean extreme either side) | H4 W%R −13.1 OVERBOUGHT / Stoch 73.2. CB calendar clear through 07-01; econ calendar clear today — no high-impact EUR/JPY releases. **Intervention watch (#4) re-confirmed: ⚠ CAUTION — spot 184.921 still inside the band (182.0–185.0, MoF level 185.0), LONG conviction capped MEDIUM.** Latest closed 1H fired no E0 either direction; neither zone is touched. No re-forecast trigger (price-driven only). V1b ✅ intact both zones (thresholds 182.960 / 186.540). **Both zones unchanged: EC ~0/10 — ❌ NO TRADE.** PENDING.
