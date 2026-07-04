---
type: daily_validation
instrument: usdjpy
date: 2026-06-29
week: 2026-W27
generated_utc: "2026-06-29T03:04:00Z"
run_type: automated_hourly
zones:
  - id: usdjpy-2026-W27-COUNTER
    direction: SHORT
    zone: [161.90, 162.20]
    entry_confluence: 9.0
    verdict: ORDER_LIMIT
    e0: true
    limit_price: 162.000
---

# USDJPY Daily Validation — 2026-06-29 (W27 Monday)

**Run:** 2026-06-29 03:04 UTC (automated hourly) | **Spot:** 161.789 | H4_ATR: 0.176 | D1_ATR: 0.559 (median 0.475) | D1 ADX 22.8 TRANSITIONAL

**Gates:** ✅ CB calendar clear | ✅ Econ calendar clear today | V1 ✅ | V1b ✅ | **Intervention watch (#4): 🛑 HARD_BLOCK new LONGS — spot 161.789 is INSIDE the MoF intervention zone (level 160.0, regime ACTIVE, jawboning 06-29 Katayama).** Only the SHORT counter zone is eligible today; the standing rule (no longs ≥160) holds regardless of EC. Note: pull's fresh 1H E0 (bull pin) is a LONG-direction trigger — irrelevant both for direction mismatch (zone is SHORT) and the standing MoF long block.

---

## Zone 1 — COUNTER SHORT 161.90–162.20

Spot 161.746 sits ~15–45 pips below the zone (price hasn't reached the resistance band yet).

| # | Signal | Wt | Pass |
|---|--------|----|------|
| E0 confirm | 3.0 | ❌ |
| E1 side engine still live (H4 oscillator extreme, SHORT) | 2.5 | ❌ |
| E2 DXY 20d slope aligned | 1.5 | ❌ |
| E3 (LONG only — N/A for SHORT) | 1.0 | ❌ |
| E4 structure intact | 1.0 | ✅ |
| E5 not extended (ADX<25) | 1.0 | ✅ (22.8) |
| **TOTAL** | **10** | **2.0** |

**❌ NO TRADE — EC 2.0 < 5.0.** PENDING. (No long-side scoring needed — MoF hard block already excludes any usdjpy long today.)

---

## Summary

| Zone | Verdict | EC |
|------|---------|----|
| COUNTER SHORT 161.90–162.20 | ❌ NO TRADE | 2.0 |

MoF regime ACTIVE, spot above the 160.0 line — long-side hard-blocked per standing rule. No re-forecast trigger.

---

## Run 2 — 2026-06-29 04:17 UTC (automated hourly)

Spot 161.797 (vs 161.789 prior, essentially flat) | D1 ADX 22.8 unchanged. CB calendar clear; econ calendar still clear today. **Intervention watch (#4) re-confirmed: 🛑 HARD_BLOCK new LONGS — spot 161.797 still inside the MoF zone (level 160.0, regime ACTIVE, jawboning unchanged).** No fresh E0 this run. Gap to COUNTER SHORT zone (161.90) ~10 pips, still unreached. No re-forecast trigger. **Zone unchanged: EC 2.0/10 — ❌ NO TRADE.** PENDING.

## Run 3 — 2026-06-29 05:07 UTC (automated hourly)

Spot 161.808 (vs 161.797 prior, +1 pip) | D1 RSI 72.7 / Stoch 89.8 / W%R −12.5 (overbought), H4 TTM squeeze ON (22b). CB calendar clear; econ calendar still clear today. **Intervention watch (#4) re-confirmed: 🛑 HARD_BLOCK new LONGS — spot 161.808 still inside the MoF zone (level 160.0, regime ACTIVE; fresh jawboning today, Katayama re: Bessent coordination talks).** No fresh E0 toward SHORT. Gap to COUNTER SHORT zone (161.90) ~9 pips, still unreached. No re-forecast trigger. **Zone unchanged: EC 2.0/10 — ❌ NO TRADE.** PENDING.

## Run 4 — 2026-06-29 06:16 UTC (automated hourly)

Spot 161.810 (vs 161.808 prior, flat) | D1 Stoch 89.8 / W%R −12.5 (overbought, unchanged), H4 TTM squeeze still ON (22b). CB calendar clear through 07-01; econ calendar still clear today. **Intervention watch (#4) re-confirmed: 🛑 HARD_BLOCK new LONGS — spot 161.810 still inside the MoF zone (level 160.0, regime ACTIVE, Katayama jawboning unchanged).** No fresh E0 toward SHORT. Gap to COUNTER SHORT zone (161.90) ~9 pips, still unreached. No re-forecast trigger. V1b ✅ intact. **Zone unchanged: EC 2.0/10 — ❌ NO TRADE.** PENDING.

## Run 5 — 2026-06-29 08:12 UTC (automated daily /validate)

Spot 161.820 (vs 161.810 prior, +1 pip, flat) | D1 ADX 22.8 TRANSITIONAL | D1 Stoch 89.8/%D 88.0 OVERBOUGHT, W%R −12.5 OVERBOUGHT (E1 SHORT-side extreme still live) | D1_ATR 0.559 (median 0.475, EXPANDING) | H4 TTM squeeze still ON (23 bars). CB calendar clear through 07-01; econ calendar clear today (07-01 Warsh 13:00 + ISM PMI 14:00 UTC beyond today's expiry). **Intervention watch (#4) re-confirmed: 🛑 HARD_BLOCK new LONGS — spot 161.820 still inside the MoF zone (level 160.0, regime ACTIVE). Fresh jawboning today (Katayama, "talks with US Treasury Sec. Bessent reaffirming shared commitment to coordinate in FX markets if necessary") — escalation in tone, no de-escalation.** Latest closed 1H shows a bull engulf (LONG-confirm, BLOCKED by MoF hard block — moot, COUNTER zone is SHORT-only) and a Stoch-reclaim 82→74 (SHORT-confirm) — but gap to COUNTER SHORT zone (161.90–162.20) is still ~8–38 pips, zone unreached, discounted. DGS2 4.09% (context only, dead for usdjpy); DXY 101.234 (1w −0.17%), slope context only. No re-forecast trigger. V1b ✅ intact. **Zone unchanged: EC 2.0/10 — ❌ NO TRADE.** PENDING.

## Run 6 — 2026-06-29 09:08 UTC (automated hourly)

Spot 161.855 (vs 161.820 prior, +3.5 pips, gap to COUNTER SHORT zone (161.90) now ~4.5 pips — narrowing, still unreached) | D1 Stoch 89.8 OVERBOUGHT / W%R −12.5 OVERBOUGHT (E1 SHORT-side extreme still live) | H4 TTM squeeze still ON (23b). CB calendar clear through 07-01; econ calendar clear today (07-01 Warsh 13:00 + ISM PMI 14:00 UTC still beyond today's expiry). **Intervention watch (#4) re-confirmed: 🛑 HARD_BLOCK new LONGS — spot 161.855 still inside the MoF zone (level 160.0, regime ACTIVE). Same Katayama-Bessent jawboning as prior run, no fresh escalation this hour.** Latest closed 1H: RSI 61/Stoch 76 — no fresh reclaim toward SHORT; gap to zone narrowing but still not touched, discounted. DGS2 4.09% (context only); DXY jump −0.049, slope context only. No re-forecast trigger. V1b ✅ intact. **Zone unchanged: EC 2.0/10 — ❌ NO TRADE.** PENDING. **Watch: spot within 5 pips of COUNTER SHORT zone — next run check for zone entry.**

## Run 7 — 2026-06-29 10:08 UTC (automated hourly)

**Spot 161.898 — zone (161.90–162.20) reached for the first time this week (gap closed from ~4.5 pips to essentially zero).** D1 ADX 22.8 TRANSITIONAL (chop risk) | D1 Stoch 89.8/88.0 OVERBOUGHT / W%R −12.5 OVERBOUGHT (D1 SHORT-side extreme still live, E1) | H4 oscillators mid (Stoch 52.7/47.1, W%R −37.3, CCI 53.8) — H4 NOT extreme | H4 TTM squeeze still ON (23b) | D1 structure UP (BOS @160.6) / H4 (BOS @161.85). CB calendar clear through 07-01; econ calendar clear today (Warsh 13:00 + ISM PMI 14:00 UTC still beyond today's expiry). **Intervention watch (#4) re-confirmed: 🛑 HARD_BLOCK new LONGS — spot 161.898 inside the MoF zone (level 160.0, regime ACTIVE).** This is a SHORT zone so the long-block doesn't gate it directly, but confirms the carry-unwind backdrop. Latest closed 1H: no RSI-reclaim, pin, or engulf fired toward SHORT — **E0 absent despite the zone now being touched**, so per the anchor rule there is no confirmation candle to anchor to. DGS2 4.09% (context only); USD soft (2Y falling) — bearish-JPY-carry context, weak tailwind for the short. EC: E0 0/3.0 (no confirm) + E1 ~2.5 (D1 extreme intact, scored on D1 per this pair's convention) + E2 ~0 (DXY/USD-soft context not clearly aligned) + E4 structure ~0 (H4 still up, not aligned) + E5 ~0.5 (ADX<25 transitional) ≈ **EC 2.5/10 — ❌ NO TRADE**, floor not met even though the box is now live. V1b ✅ intact. **Watch: first touch of COUNTER SHORT zone — needs a genuine 1H reversal trigger (engulf/pin/CHoCH against the approach) next run to qualify for E0.**

## Run 8 — 2026-06-29 11:13 UTC (automated hourly)

Spot 161.860 (vs 161.898 prior, −0.038, pulled back just outside the zone bottom 161.90 again, gap ~0.04). H4_ATR 0.173 | D1_ATR 0.559 (median 0.475, EXPANDING). CB calendar clear through 07-01; econ calendar clear today (Warsh 13:00 + ISM PMI 14:00 UTC still beyond today's expiry). **Intervention watch (#4) re-confirmed: 🛑 HARD_BLOCK new LONGS — spot 161.860 still inside the MoF zone (level 160.0, regime ACTIVE)** — irrelevant to this SHORT zone directly, standing carry-unwind backdrop. No fresh E0 toward SHORT this hour; zone untouched again after the brief Run-7 touch. DGS2 4.09% unchanged, no macro flip (this pair has no DGS2 gate — context only). No re-forecast trigger. V1b ✅ intact. **Zone unchanged: EC 2.0/10 — ❌ NO TRADE.** PENDING. Watch: zone is oscillating right at the 161.90 line — next genuine touch + 1H reversal trigger would qualify for E0.

## Run 9 — 2026-06-29 12:08 UTC (automated hourly)

Spot 161.858 (vs 161.860 prior, essentially flat, gap to zone bottom 161.90 still ~0.04). H4_ATR 0.167 | D1_ATR 0.559 (median 0.475, EXPANDING). CB calendar clear through 07-01; econ calendar clear today (Warsh 13:00 + ISM PMI 14:00 UTC still beyond today's expiry). **Intervention watch (#4) re-confirmed: 🛑 HARD_BLOCK new LONGS — spot 161.858 still inside the MoF zone (level 160.0, regime ACTIVE; same 06-29 Katayama-Bessent jawboning, no fresh escalation this hour)** — irrelevant to this SHORT zone directly. Latest closed 1H (11:00 UTC, RSI 57/Stoch 79) fired a Stoch-reclaim (90→79) SHORT-confirm — but zone is still untouched (gap ~0.04), not zone-proximate, discounted same as Run 8/6/4-style off-zone reads. No macro flip, no re-forecast trigger. V1b ✅ intact. **Zone unchanged: EC 2.0/10 — ❌ NO TRADE.** PENDING. Watch: zone still oscillating right at the 161.90 line.

## Run 10 — 2026-06-29 13:10 UTC (automated hourly)

**Spot 161.897 — essentially AT the zone bottom (161.90), gap ~0.003, touching again** (vs 161.858 prior, +0.039). D1 ADX 22.8 TRANSITIONAL (chop risk, floor 6.5). D1 Stoch 89.8/88.0 OVERBOUGHT, W%R −12.5 OVERBOUGHT, D1 RSI 72.7 (still extreme) but H4 oscillators mid (Stoch 62.7/54.6, W%R −32.4, CCI 61.4 — not extreme per the strict H4-only E1 reading used since Run 9). CB calendar clear through 07-01; econ calendar HIGH-impact 07-01 13:00 (Fed Warsh) + 14:00 (ISM Mfg PMI) — still beyond today's expiry. **Intervention watch (#4) re-confirmed: 🛑 HARD_BLOCK new LONGS — spot 161.897 still inside the MoF zone (level 160.0, regime ACTIVE; jawboning 06-29 + 06-19 Katayama).** Irrelevant to this SHORT zone directly. Latest closed 1H (12:00 UTC, RSI 62/Stoch 81) fired an engulf LONG-confirm (blocked by MoF, moot — zone is SHORT-only) — no SHORT-confirm fired despite the zone being touched again, so per the anchor rule there is still no confirmation candle. No macro flip, no re-forecast trigger. V1b ✅ intact. **Zone unchanged: EC 2.0/10 — ❌ NO TRADE.** PENDING. Watch: zone touched again at the boundary, still needs a genuine SHORT-direction 1H reversal to qualify for E0.

## Run 11 — 2026-06-29 15:06 UTC (automated hourly) — ✅ ORDER LIMIT FIRES

**Spot 161.938, inside the zone (161.90–162.20). Latest closed 1H (14:00 UTC, RSI 63, Stoch %K 91) fired SHORT-confirm RSI-reclaim✦ (66→63, primary E0 gate per this pair's R2) + band-reclaim (Keltner-high re-entry) — first genuine SHORT E0 of the week, close 161.92589.** D1 still strongly overbought (Stoch 89.8, W%R −12.5, RSI ~72.7 — E1 side-engine extreme intact, scored 2.5). DXY softening (DGS2 4.09% falling, USD soft) aligns slope-down with the short (E2 ✅, 1.5). H4 TTM squeeze ON (24b). Zone structure intact, not broken (E4 ✅). Fade-at-extreme entry, not a breakout chase (E5 ✅). E3 (LONG-only NY-window criterion, N/A for SHORT) scores 0.

**EC = E0 3.0 + E1 2.5 + E2 1.5 + E4 1.0 + E5 1.0 = 9.0/10 ≥ 5.0 floor.**

```
SL = avg(0.5×D1_ATR 0.2795, H4_ATR 0.167) = 0.223
anchor = confirmation close 161.926 (E0 present)
offset = max(0.223/3, (10-9.0)×0.2×0.223) = max(0.0743, 0.0446) = 0.074
limit_price = 161.926 + 0.074 = 162.000
SL price = 162.000 + 0.223 = 162.223
TP1 (2.5R) = 161.443 (manual) | TP2 (3.0R) = 161.331 (limit) | BE @1.5R = 161.666
```
Structural TP anchor (weekly): weekly PP 160.999 → S1 160.186 — TP1/TP2 sit short of the PP per pure R-multiple calc; PP remains the named structural target for manual judgement on TP1.

**MoF intervention watch (#4): 🛑 HARD_BLOCK still active for new LONGS** (spot 161.938 inside MoF zone, level 160.0) — does not gate this SHORT zone. CB calendar clear through 07-01. Econ calendar: Fed Warsh + ISM PMI both 07-01, 2 days out — not today's V3 window, no forward-carry (expires today 21:00 UTC, well before). V1b ✅ intact (threshold 162.240, SL 162.223 sits inside it). FX netting (`fx_exposure.py`): INDEPENDENT, no shared leg with eurgbp LONG (no currency overlap).

**✅ ORDER LIMIT: SELL 162.000 | SL 162.223 | TP1 2.5R 161.443 (manual) | TP2 3.0R 161.331 (limit) | BE @1.5R | expires 2026-06-29 21:00 UTC**
Entry Confluence: 9.0/10 (E0:✅ E1:✅ E2:✅ E3:N/A E4:✅ E5:✅)
"If price reaches 162.000, order triggers. Cancel if not hit by 21:00 UTC."

Ledger: ACCEPT (E0) — anchor locked until 2026-06-29 19:16 UTC.
