---
type: daily_validation
instrument: usdjpy
date: 2026-06-30
week: 2026-W27
generated_utc: "2026-06-30T16:21:30Z"
run_type: automated_hourly
zones:
  - id: usdjpy-2026-W27-COUNTER
    direction: SHORT
    zone: [161.90, 162.20]
    entry_confluence: 3.5
    verdict: INVALIDATED
    e0: false
    reason: v1b_breach
---

# USDJPY Daily Validation — 2026-06-30 (W27 Tuesday)

**Run:** 2026-06-30 16:21 UTC (automated hourly) | **Spot:** 162.668 (latest 1H)

**Gates:** ✅ CB calendar clear | ✅ Econ calendar: US high-impact releases 2026-07-01/02 beyond today's expiry | ✅ Intervention watch reviewed through 2026-06-30; active MoF regime hard-blocks new longs only.

## Zone 1 — COUNTER SHORT 161.90–162.20
V1b ❌ **BREACH / INVALIDATED**: last 2 H4 closes 162.606 and 162.668, both beyond SHORT threshold 162.240 (zone top 162.200 + buffer 0.040).

**❌ INVALIDATED — cancel live limit.** Ledger effective state = INVALIDATED, lock cleared.

No replacement order. Re-forecast follow-up flagged if USDJPY holds above 162.24 into next session.
