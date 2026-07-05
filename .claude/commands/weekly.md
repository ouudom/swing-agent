---
description: Weekly Trading Zone forecast for one instrument (swing-agent, MCP-only)
argument-hint: [instrument]
---

Run the swing-agent Weekly Routine for **$ARGUMENTS** (one instrument; if omitted, ask which of
the 11: xauusd, eurusd, gbpusd, eurgbp, audusd, nzdusd, usdcad, usdchf, usdjpy, eurjpy, gbpjpy).

This repo is self-contained — do not read/write the parent `swing-trading` repo. MCP is the only
gateway to Postgres. Full contract: `ROUTINES.md`. Formulas: `CLAUDE.md` Core Formulas (v3).

## Steps

1. **Read wiki context** (words, not numbers):
   - `wiki/system/constitution.md` — risk/SL/TP/offset rules, multi-instrument table
   - `wiki/{instrument}/{instrument}_profile.md` — profile, sessions, ATR ranges, V1b
   - `wiki/{instrument}/confluence_criteria.md` — Zone Confluence (R1) scoring rubric
   - `wiki/system/calibration.md` — which pairs/directions are WORKING/DEAD/UNPROVEN
   - `wiki/system/yield_environment.md` — current macro baseline (about to be rewritten)

2. **Pull DB-native context via MCP** — call, in this order:
   - `get_zone_context(instrument)` — structure/momentum/macro/ATR+SL/COT, DB-native
   - `get_brief(instrument, kind="weekly")` — latest OHLC freshness, open zones, recent trades/verdicts
   - `run_replay(instrument=instrument)` if prior week needs resolving (retrospective HELD/BROKE/UNTESTED)
   - `get_calibration(instrument)` — edge performance gate
   - `get_news(instrument)` + `get_econ()` — headline/data-release context
   - CB calendar / econ-calendar / JPY intervention gates — call the relevant `run_gate` names
     (`cb_calendar`, `econ_calendar`, `intervention_watch` for JPY pairs) before scoring zones

3. **Decide** — score candidate Trading Zones with Zone Confluence (R1, max 10, floor 5.0) per
   `confluence_criteria.md`. Publish ≤3 zones (≤1 counter-trend).

4. **Structured write first** — for every published zone, call `publish_zone(...)` via MCP. This
   is the durable record even if the markdown/git step fails below.

5. **Write markdown** — `wiki/weekly-forecasts/{YYYYWNN}/{instrument}.md` (e.g. `2026W27/xauusd.md`).
   Update `wiki/system/yield_environment.md` if the macro baseline moved. Never write a derived
   number anywhere it could go stale — recompute from MCP each time.

6. **git add + commit + push** on the `live` branch.

If the MCP write in step 4 succeeds but git fails in step 6: do **not** re-call `publish_zone`
with new state. Fix git, then re-run `python src/engine/scripts/ops/reconcile_db_git.py`.
