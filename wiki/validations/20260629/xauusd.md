---
type: daily_validation
instrument: xauusd
date: 2026-06-29
week: 2026-W27
generated_utc: "2026-06-29T03:04:00Z"
run_type: automated_hourly
zones:
  - id: xauusd-2026-W27-PRIMARY
    direction: SHORT
    zone: [4120, 4160]
    entry_confluence: 3.5
    verdict: NO_TRADE
    e0: false
    reason: zone_unreached_E1_dropped
  - id: xauusd-2026-W27-SECONDARY
    direction: SHORT
    zone: [4190, 4220]
    entry_confluence: 3.5
    verdict: NO_TRADE
    e0: false
    reason: zone_unreached_E1_dropped
---

# XAUUSD Daily Validation — 2026-06-29 (W27 Monday, hourly re-run)

**Run:** 2026-06-29 03:04 UTC (automated hourly) | **Spot:** 4066.14 | H4_ATR: 39.37 | D1_ATR: 124.66 (median 115.99, EXPANDING) | D1 ADX 48.6 TRENDING

**Gates:** ✅ CB calendar clear (no decision 06-29/06-30) | ✅ Econ calendar clear today (next: 07-01 Warsh speaks + ISM Mfg PMI, both beyond today's 21:00 expiry) | V1 ✅ intact | V1b ✅ intact (both zones)

**Macro:** DFII10 2.19% (slope20 +0.13, supports SHORT) | DGS2 context 4.09% (drift +0.10 < 0.15 threshold — no re-forecast)

---

## Zone 1 — PRIMARY SHORT 4120–4160 (carried ZC from weekly)

**Q1/Q2 blocks:** V1 ✅ | V1b ✅ (spot 4068.66 well inside, no 2-consecutive-H4-close breach) | V3 ✅ clear | VIX ✅ no SHORT veto (calm) | Macro flip ✅ none

**Q3 re-forecast:** No triggers (T1 DFII10 +0.13 < 0.15; weekend gap gate N/A — W27 zones re-forecast fresh 06-28).

**Q4 Entry Confluence:**

| # | Signal | Wt | Pass | Note |
|---|--------|----|------|------|
| E0 | 1H confirm toward SHORT | 3.0 | ❌ 0 | Latest closed 1H (02:00 UTC) shows no fresh engulf/pin/CHoCH toward SHORT; spot 4066.14 is ~54pts BELOW the zone bottom (4120) — not zone-proximate regardless. |
| E1 | H4 structure aligned (LH+LL) | 2.5 | ❌ 0 | H4 state UP (last CHoCH UP @ 4044.57, 3 bars ago) — not aligned with SHORT thesis at current bar. |
| E2 | DFII10 slope20 > 0 | 2.0 | ✅ 2.0 | DFII10 2.19%, slope +0.13, rising real yields = gold bearish. |
| E3 | Macro drift OK | 1.0 | ✅ 1.0 | Within band (DGS2 drift +0.10 < 0.15). |
| E4 | ATR compression | 1.0 | ❌ 0 | D1 ATR 124.66 > 20d median 115.99 — EXPANDING, not compressed (rubric requires ATR < median). Corrects prior run's mis-score. |
| E5 | DXY slope20 > 0 | 0.5 | ✅ 0.5 | DXY 101.34, +0.33% 1w. |
| **TOTAL** | | **10** | **3.5** | < 5.0 floor |

**❌ NO TRADE — EC 3.5 < 5.0 floor.** Zone unreached (price ~54–144pts below 4120–4160 box); no genuine entry confirmation exists yet. PENDING.

---

## Zone 2 — SECONDARY SHORT 4190–4220

Identical inputs (E2/E3/E5 same, E0/E1/E4 same). **EC 3.5/10 — ❌ NO TRADE.** Zone unreached (price ~124–154pts below box). PENDING.

---

## Summary

| Zone | Verdict | EC | Note |
|------|---------|----|------|
| PRIMARY SHORT 4120–4160 | ❌ NO TRADE | 3.5 | Zone unreached, no E0; E4 corrected to fail (ATR expanding not compressed) |
| SECONDARY SHORT 4190–4220 | ❌ NO TRADE | 3.5 | Zone unreached, no E0 |

First session of W27. No structural change. GLD inflow watch (per `_HOT.md` base-risk note) still standing — D1 close > 4448 (POC) would kill the bear thesis; not close today.

---

## Run 2 — 2026-06-29 04:17 UTC (automated hourly)

Spot 4068.26 (vs 4066.14 prior run, +2pt) | H4_ATR 37.29 | D1_ATR 124.66 (median 115.99, still EXPANDING) | D1 ADX 48.6 unchanged. CB calendar clear; econ calendar still clear today (07-01 Warsh/ISM beyond expiry). Fresh 1H bear pin found but ~52–150pts off both zones (zone unreached) — discounted, same as prior run. DFII10 2.19% unchanged. No re-forecast trigger (DGS2 drift unchanged). **Both zones unchanged: EC 3.5/10 — ❌ NO TRADE.** PENDING.

## Run 3 — 2026-06-29 05:07 UTC (automated hourly)

Spot 4056.71 (vs 4068.26 prior, −11.5pt, drifting further below both zones) | H4_ATR 37.29 | D1_ATR 124.66 (median 115.99, still EXPANDING) | D1 RSI 36.7 / Stoch 16.7 (D1 oversold but H4 Stoch 84.3 overbought, mixed) | H4 structure UP (still not aligned with SHORT thesis). CB calendar clear; econ calendar clear today (07-01 Warsh+ISM beyond expiry). VIX 18.89 calm, no SHORT veto. No fresh E0 toward SHORT at either zone. DXY 101.385 (+0.33% 1w, unchanged slope). No re-forecast trigger. **Both zones unchanged: EC 3.5/10 — ❌ NO TRADE.** PENDING.

## Run 4 — 2026-06-29 06:16 UTC (automated hourly)

Spot 4060.19 (vs 4056.71 prior, +3.5pt, still ~60–160pt below both zones) | H4_ATR 37.29 | D1_ATR 124.66 (median 115.99, still EXPANDING) | D1 Stoch 16.7 oversold / H4 Stoch 84.3 overbought (mixed, unchanged) | D1 structure DOWN (BOS DOWN @4023.50) / H4 structure UP (CHoCH UP @4044.57, unchanged) — still not aligned with SHORT thesis. CB calendar clear through 07-01; econ calendar still clear today (07-01 Warsh+ISM beyond expiry). VIX 18.89 calm, no SHORT veto. No fresh E0 toward SHORT at either zone. DFII10 2.19% unchanged. No re-forecast trigger. V1b ✅ intact both zones. **Both zones unchanged: EC 3.5/10 — ❌ NO TRADE.** PENDING.

## Run 5 — 2026-06-29 08:10 UTC (automated daily /validate)

Spot 4065.04 (vs 4060.19 prior, +4.9pt, still ~55–155pt below both zones) | H4_ATR 36.92 | D1_ATR 124.66 (median 115.99, still EXPANDING — E4 fails) | D1 ADX 48.6 TRENDING (unchanged, strong downtrend). D1 Stoch 16.7 oversold / H4 Stoch 81.3 overbought (mixed divergence, unchanged). CB calendar clear through 07-01; econ calendar clear today (07-01 Warsh 13:00 + ISM PMI 14:00 UTC beyond today's expiry, no window block today). VIX 18.89 calm, no SHORT veto. Latest closed 1H shows both a bull pin and a bear pin (RSI 52/Stoch 39, no directional reclaim) — neither zone-proximate (price still 55–155pt below both boxes), discounted same as Runs 1–4. DFII10 2.19% unchanged (drift <0.10%, no macro flip). No re-forecast trigger. V1b ✅ intact both zones. **Both zones unchanged: EC 3.5/10 — ❌ NO TRADE.** PENDING.

## Run 6 — 2026-06-29 09:08 UTC (automated hourly)

Spot 4053.16 (vs 4065.04 prior, −11.9pt, drifting further below both zones, now ~67–167pt away) | H4_ATR 36.92 | D1_ATR 124.66 (median 115.99, still EXPANDING — E4 fails) | D1 Stoch 16.7 oversold / H4 Stoch 81.3 overbought (mixed, unchanged). CB calendar clear through 07-01; econ calendar clear today (07-01 Warsh 13:00 + ISM PMI 14:00 UTC still beyond today's expiry, no window block today). VIX 18.89 calm (spike +0.26), no SHORT veto. Latest closed 1H: RSI 45/Stoch 32 — no fresh engulf/pin/CHoCH toward SHORT; zone not proximate regardless (spot now further below both boxes). DFII10 2.19% unchanged (drift +0.13 < 0.15, no macro flip). No re-forecast trigger. V1b ✅ intact both zones. **Both zones unchanged: EC 3.5/10 — ❌ NO TRADE.** PENDING.

## Run 7 — 2026-06-29 10:08 UTC (automated hourly)

Spot 4031.59 (vs 4053.16 prior, −21.6pt, drifting further below both zones, now ~88–189pt away) | H4_ATR 36.92 | D1_ATR 124.66 (median 115.99, still EXPANDING — E4 fails) | D1 ADX 48.6 TRENDING unchanged | D1 Stoch 16.7 oversold / H4 Stoch 81.3 overbought (mixed, unchanged) | D1 structure DOWN (BOS @4023.5) / H4 structure UP (CHoCH @4044.6) — still not aligned. CB calendar clear through 07-01; econ calendar clear today (07-01 Warsh 13:00 + ISM PMI 14:00 UTC still beyond today's expiry). No fresh E0 toward SHORT at either zone; zone not proximate regardless. DFII10 unchanged, no macro flip. No re-forecast trigger. V1b ✅ intact both zones. **Both zones unchanged: EC 3.5/10 — ❌ NO TRADE.** PENDING.

## Run 8 — 2026-06-29 11:13 UTC (automated hourly)

Spot 4037.08 (vs 4031.59 prior, +5.5pt, still ~83–183pt below both zones) | H4_ATR 36.92 | D1_ATR 124.66 (median 115.99, still EXPANDING — E4 fails) | DFII10 2.19% (slope +0.0092, supports SHORT, unchanged) | VIX 18.89 calm, no veto. CB calendar clear through 07-01; econ calendar clear today (07-01 Warsh 13:00 + ISM PMI 14:00 UTC still beyond today's expiry). No E0 toward SHORT at either zone this hour; zone not proximate regardless. No macro flip, no re-forecast trigger. V1b ✅ intact both zones. **Both zones unchanged: EC 3.5/10 — ❌ NO TRADE.** PENDING.

## Run 9 — 2026-06-29 12:08 UTC (automated hourly)

Spot 4047.05 (vs 4037.08 prior, +10pt, still ~73–173pt below both zones) | H4_ATR 36.18 | D1_ATR 124.66 (median 115.99, still EXPANDING — E4 fails) | D1 ADX 48.6 TRENDING unchanged. CB calendar clear through 07-01; econ calendar clear today (07-01 Warsh 13:00 + ISM PMI 14:00 UTC still beyond today's expiry). Latest closed 1H (11:00 UTC) fired a bull pin — LONG-direction, wrong-way for the SHORT thesis and zone remains unreached regardless, discounted. GLD +25.68t INFLOW (1w) — base-risk warning persists per `_HOT.md` watch note, no D1 close > 4448 POC today. No macro flip, no re-forecast trigger. V1b ✅ intact both zones. **Both zones unchanged: EC 3.5/10 — ❌ NO TRADE.** PENDING.

## Run 10 — 2026-06-29 13:10 UTC (automated hourly)

Spot 4050.24 (vs 4047.05 prior, +3.2pt, still ~70–170pt below both zones) | H4_ATR 36.18 | D1_ATR 124.66 (median 115.99, still EXPANDING) | D1 ADX 48.6 TRENDING unchanged (floor 6.0 today). CB calendar clear through 07-01; econ calendar HIGH-impact 07-01 13:00 (Fed Warsh) + 14:00 (ISM Mfg PMI) — still beyond today's 21:00 expiry. Latest closed 1H (12:00 UTC, RSI 46/Stoch 24) fired a Stoch-reclaim LONG-confirm (12→24) — wrong-way for the SHORT thesis, zone remains unreached regardless, discounted. No macro flip, no re-forecast trigger. V1b ✅ intact both zones. **Both zones unchanged: EC 3.5/10 — ❌ NO TRADE.** PENDING.

## Run 11 — 2026-06-29 15:06 UTC (automated hourly)

Spot 4023.75 (vs 4050.24 prior, −26.5pt, drifted further below both zones — now ~96–196pt away) | H4_ATR 36.18 | D1_ATR 124.66 (median 115.99, still EXPANDING — E4 fails) | DFII10 2.19% FALLING (against the SHORT thesis — E2/E3 fail) | DXY 101.148 (1d −0.26%, against SHORT — E5 fails) | D1 structure DOWN / H4 structure UP (CHoCH @4044.57) — H4 not aligned with SHORT, E1 fails. CB calendar clear through 07-01; econ calendar HIGH-impact 07-01 13:00 (Fed Warsh) + 14:00 (ISM Mfg PMI) — still beyond today's expiry. Latest closed 1H fired a LONG-confirm pin (bull) — wrong-way for the SHORT thesis, and both zones remain unreached regardless. No macro flip beyond drift, no re-forecast trigger. V1b ✅ intact both zones (4120-4160 threshold 4165.00; 4190-4220 threshold 4225.00). **Both zones: EC ~0/10 (all E's fail — H4 wrong-way, DFII10 falling, ATR expanding, DXY falling) — ❌ NO TRADE.** PENDING.
