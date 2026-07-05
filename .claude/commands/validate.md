---
description: Hourly daily-validation pass for one or all instruments (swing-agent, MCP-only)
argument-hint: [instrument] [date]
---

Run the swing-agent Validate Routine for **$ARGUMENTS** (instrument optional — default: all 11
active instruments in one pass; date optional — default: today UTC).

This repo is self-contained — do not read/write the parent `swing-trading` repo. MCP is the only
gateway to Postgres. Full contract: `ROUTINES.md`. Formulas: `CLAUDE.md` Core Formulas (v3).

## Per-instrument steps

1. **Read wiki context** (words, not numbers — this is what makes the routine judgment, not a
   mechanical rerun):
   - `wiki/system/constitution.md` — SL/TP/offset formula, hard-block rules (V1/V1b/V3)
   - `wiki/{instrument}/confluence_criteria.md` — Entry Confluence (R2) scoring rubric
   - Any existing zone rows for this instrument this week (from `get_brief` below)

2. **CB calendar check first (mandatory)** — `run_gate("cb_calendar", [instrument])`.

3. **Pull context via MCP**:
   - `get_brief(instrument, kind="validate")` — open zones, latest verdicts/trade_log, news/econ
   - `compute_indicators(instrument, tf="1h")` and `tf="4h"` — live ATR/RSI/SMA
   - `run_gate` for `econ_calendar`, and `intervention_watch` (JPY pairs only)

4. **Decide, per open zone** — four questions:
   - Forecast still valid? (V1/V1b/V3 hard blocks)
   - Bias flipped? (macro drift vs `wiki/system/yield_environment.md` baseline)
   - Re-forecast needed? (mid-week trigger tree)
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

6. **Write markdown** — `wiki/validations/{YYYYMM}/{YYYYMMDD}/{instrument}.md`
   (e.g. `20260704/xauusd.md`). Per zone: ✅ ORDER LIMIT | ❌ NO TRADE / INVALIDATED.

7. Before any FX order limit, note the advisory exposure check: `run_gate` has no `fx_exposure`
   entry today — if one exists by the time you run this, call it; otherwise note the gap in the
   markdown instead of skipping the check silently.

## After all instruments

8. **git add + commit + push** on the `live` branch — one commit for the whole hourly pass.

If step 5's MCP write succeeds but git fails in step 8: do **not** re-call with a new `run_id`.
Reuse the same `run_id`, fix git, then run `python src/engine/scripts/ops/reconcile_db_git.py`.
