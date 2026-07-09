---
description: Hourly daily-validation pass for one or all instruments (swing-agent, MCP-only)
argument-hint: [instrument] [date]
---

Run the swing-agent Validate Routine for **$ARGUMENTS** (instrument optional — default: all 11
active instruments in one pass; date optional — default: today UTC).

This repo is self-contained — do not read/write the parent `swing-trading` repo. MCP is the only
gateway to Postgres. Full contract: `docs/routines.md`. Formulas: `CLAUDE.md` Core Formulas (v3).

## Per-instrument steps

1. **Read rules context via MCP** (words, not numbers — Phase 1: docs live in Postgres, not
   wiki/*.md — this is what makes the routine judgment, not a mechanical rerun):
   - `get_context_pack(instrument)` — constitution (SL/TP/offset + V1/V1b/V3 hard blocks),
     this instrument's confluence_criteria (R2 rubric), macro baseline, calibration — bodies
     included. (Single doc: `get_doc("rulebook","{instrument}/confluence")`.)
   - Any existing zone rows for this instrument this week (from `get_brief` below)

2. **CB calendar check first (mandatory)** — `run_gate("cb_calendar", [instrument])`.

3. **Pull context via MCP**:
   - `get_brief(instrument, kind="validate")` — open zones, latest verdicts/trade_log, news/econ
   - `compute_indicators(instrument, tf="1h")` and `tf="4h"` — live ATR/RSI/SMA
   - `run_gate` for `econ_calendar`, and `intervention_watch` (JPY pairs only)

4. **Decide, per open zone** — four questions:
   - Forecast still valid? (V1/V1b/V3 hard blocks)
   - Bias flipped? (macro drift vs the `yield_environment` context doc baseline, from
     `get_context_pack` in step 1) — if yes, call `queue_notification(event_type="bias_flip",
     title="{INSTRUMENT} bias flip", message=<what drifted + new bias>, instrument=instrument)`.
   - Re-forecast needed? (mid-week trigger tree) — if yes, call
     `queue_notification(event_type="reforecast_triggered", title="{INSTRUMENT} re-forecast
     triggered", message=<trigger + zone_id>, instrument=instrument, zone_id=zone_id)`.
   - Order limit? — score Entry Confluence (R2, max 10, floor 5.0)

5. **Structured write first, both tools**:
   - `write_verdict(zone_id, verdict, validation_date, entry_confluence, limit_price,
     hard_block_flags, reason)` — the audit-trail verdict record (`validation_verdict` table).
   - `write_trade_log(zone_id, verdict, validation_date, entry_confluence, limit_price,
     sl_price, tp_price, hard_block_flags, reason)` — the LIVE order-state record (`trade_log`
     table). Compute `sl_price`/`tp_price` as absolute price levels from the constitution SL
     formula before calling this — `write_trade_log` requires them on `ORDER_LIMIT`.
   - **Both calls are idempotent per (zone_id, run_id) but `write_trade_log` will reject the
     write outright once that zone's trade_log row is `RUNNING` or terminal** (filled or closed) —
     that's expected once a real order is live; the checker script owns it from there, not you.
     Skip the call (or just log the rejection) rather than retrying with different values.
   - Also call `snapshot_features(zone_id, instrument, event_type="validate", features={...})`
     with the EC breakdown (`entry_confluence` score + `components`/`flags` if you computed it
     programmatically, or your own R2 rubric scoring) plus the `compute_indicators` values from
     step 3 — freezes the R2 feature vector this verdict was scored on (Phase 3). One snapshot
     per zone per validation pass, not per instrument-with-no-open-zone.

6. **Write the validation prose to the DB** (Phase 1 — no wiki/*.md):
   `write_doc(doc_type="validation", key="{YYYY-MM-DD}/{instrument}", body=<full markdown>,
   instrument=instrument, valid_date="{YYYY-MM-DD}", week="{YYYY-WNN}", title=..., frontmatter={...})`
   — e.g. key `2026-07-05/xauusd`. Per zone in the body: ✅ ORDER LIMIT | ❌ NO TRADE / INVALIDATED.

7. Before any FX order limit, note the advisory exposure check: `run_gate` has no `fx_exposure`
   entry today — if one exists by the time you run this, call it; otherwise note the gap in the
   markdown instead of skipping the check silently.

## After all instruments

8. **git (optional backup only)** — Postgres is canonical for numbers (step 5) and words (step 6),
   so the pass is durable without git. If a git mirror is still maintained, one commit on `live`;
   otherwise skip.

If step 5/6's MCP write succeeds but a later step fails: do **not** re-call `write_verdict`/
`write_trade_log` with a new `run_id`. Reuse the same `run_id`; `write_doc` already versioned the
prior body into `doc_history`.
