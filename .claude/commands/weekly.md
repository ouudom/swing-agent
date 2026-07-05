---
description: Weekly Trading Zone forecast for one instrument (swing-agent, MCP-only)
argument-hint: [instrument]
---

Run the swing-agent Weekly Routine for **$ARGUMENTS** (one instrument; if omitted, ask which of
the 11: xauusd, eurusd, gbpusd, eurgbp, audusd, nzdusd, usdcad, usdchf, usdjpy, eurjpy, gbpjpy).

This repo is self-contained — do not read/write the parent `swing-trading` repo. MCP is the only
gateway to Postgres. Full contract: `ROUTINES.md`. Formulas: `CLAUDE.md` Core Formulas (v3).

## Steps

1. **Read rules context via MCP** (words, not numbers — Phase 1: docs live in Postgres, not
   wiki/*.md). One call:
   - `get_context_pack(instrument)` — returns constitution, setup_library, currency_exposure,
     this instrument's profile + confluence_criteria (R1 rubric), plus current macro
     (yield_environment) and calibration snapshots, bodies included. This is your full judgment
     context. (For an individual doc use `get_doc(doc_type, key)`, e.g.
     `get_doc("rulebook","xauusd/confluence")`.)

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

5. **Write the forecast prose to the DB** (Phase 1 — no wiki/*.md):
   - `write_doc(doc_type="forecast", key="{YYYY-WNN}/{instrument}", body=<full markdown>,
     instrument=instrument, week="{YYYY-WNN}", generated="{today}", title=..., frontmatter={...})`
     — e.g. key `2026-W27/xauusd`. This is the canonical forecast record.
   - If the macro baseline moved, rewrite it: `write_doc(doc_type="context", key="yield_environment",
     kind="macro", body=<updated macro markdown>)`.
   - Never write a derived number anywhere it could go stale — recompute from MCP each time.

6. **git (optional backup only)** — Postgres is now canonical for both numbers and words, so the
   forecast is durable after step 4+5. If a git mirror is still maintained, commit on `live`;
   otherwise skip.

If the MCP write in step 4/5 succeeds but a later step fails: do **not** re-call `publish_zone`/
`write_doc` with mutated state — `write_doc` already versioned the prior body into `doc_history`.
