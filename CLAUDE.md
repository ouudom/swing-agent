# swing-agent — Claude Code Operating Manual

## What This Is
Deployed, thin version of the multi-instrument swing-trading system (11 instruments: xauusd +
10 FX pairs). Deterministic pipeline + Postgres run headless in Docker on a homeserver; the
judgment leg (weekly forecast + hourly validation) is **you, Claude Code, on a schedule/routine**,
talking to the app through **MCP only** — no Agent SDK worker.

This repo is self-contained: **do not read or write the parent `swing-trading` repo** (research
history, full `wiki/`, `scripts/`) when working here. `swing-agent/` is what deploys.

## Two Folders
- **`wiki/`** — your execution context. Curated rules only: `wiki/system/core/constitution.md`
  (risk/SL/TP/offset/multi-instrument table), `wiki/system/{instrument}/` (profile +
  confluence_criteria), `wiki/system/core/calibration.md` (edge performance),
  `wiki/system/core/yield_environment.md` (macro baseline), `wiki/templates/`. Plus your own
  output trail: `wiki/weekly-forecasts/{YYYYWNN}/{instrument}.md` (e.g. `2026W27/xauusd.md`) and
  `wiki/validations/{YYYYMMDD}/{instrument}.md` (e.g. `20260704/xauusd.md`).
  **Nothing else lives here** — no `_HOT.md`, `_INDEX.md`, `decisions.md`, no research/history
  dump. Never add a parallel context file; update in place.
- **`src/`** — the deployed app: deterministic pipeline scripts, Postgres schema, scheduler,
  two MCP transports. The container never reads a `.md`; it runs on Postgres + config only.

## Storage Split (non-negotiable)
**Postgres = canonical for every number** (OHLC, zones, outcomes, calibration, news, econ
calendar). **`wiki/` = canonical for every word** (rules, forecasts, validations). Never store
a derived number in `wiki/` — recompute it via MCP each time.

## MCP — your only gateway to the app
Two transports, same 14 tools, one Postgres backend:
- `mcp-server` (REST, port 8765) — `curl`-style, `/call` + `/tools/<name>`.
- `mcp-native` (native MCP, port 8766) — register via `claude mcp add --transport http
  swing-agent http://<host>:8766/mcp --header "Authorization: Bearer $MCP_AUTH_TOKEN"`.

Tools: `get_brief`, `sql_query` (read-only SELECT/WITH/SHOW only), `get_news`, `get_econ`,
`get_calibration`, `compute_indicators`, `run_gate`, `run_replay`, `run_calibration`,
`run_backtest` (allowlisted scripts + args only) — data/compute, read-only or sandboxed.
`publish_zone`, `write_verdict`, `queue_notification`, `update_checkpoint` — structured writes,
idempotent (upsert on natural key). **`write_verdict` hard-rejects `ORDER_LIMIT` if
`hard_block_flags` is non-empty or `entry_confluence < 5.0`** — the gate is enforced server-side,
not by your judgment alone.

## Per-Run Discipline — DB first, then git
1. Call MCP to read context (`get_brief`, gates, calibration, news/econ).
2. Decide (zone selection / bias-flip / re-forecast / verdict) — this is the part that needs you.
3. **Structured write through MCP first** (`publish_zone` / `write_verdict`) — this is the durable
   record even if the next step fails.
4. Write markdown to `wiki/weekly-forecasts/{week}/{instrument}.md` or `wiki/validations/{date}/{instrument}.md`.
5. `git add` + commit + push on the **`live` branch**.

If the DB write succeeds but git fails: **do not re-call the MCP write with a new `run_id`.**
Reuse the same `run_id`, fix git, then run reconcile (`src/scripts/reconcile_db_git.py`).

## Path Ownership (why `live` never conflicts)
- `/weekly` (you, manual) owns `wiki/weekly-forecasts/{week}/{instrument}.md` +
  `wiki/system/core/macro/yield_environment.md`.
- `/validate` (you, hourly routine) owns `wiki/validations/{date}/{instrument}.md` — nothing else.
These never overlap, so both can read/write `live` without merge conflicts. Full contract:
`ROUTINES.md`.

## Core Formulas (v3 — matches parent constitution, ported verbatim into `src/engine/scripts/`)
```
SL:     H4_ATR14 if (0.5×D1_ATR14) < H4_ATR14 else avg(0.5×D1_ATR14, H4_ATR14)
offset: session_mult × SL  (outward beyond anchor, EC-independent)
        session_mult @ order-placement UTC: Asia 22–07 = 0.40 | London 07–12 = 0.20 |
        NY 12–21 = 0.30 (owns 12–16 overlap)
anchor: confirmation candle CLOSE (E0 present, locked 4h) | 50% zone midpoint (no E0)
TP:     3.0R nearer zone | 4.0R further zone (distance-tiered, single limit); BE at +1.5R
Friday: 13:00 UTC (NY open) cancel all unfilled limits; open positions keep running.
```
These constants live in `src/engine/scripts/trade_outcome.py` (`TP_R_NEAR`, `TP_R_FAR`,
`_SESSION_MULT`, `friday_cutoff`) — read the code, don't hand-recompute.

## Docs Map
- `README.md` — orientation, quick links.
- `DEPLOYMENT_UBUNTU.md` — clone → env → Postgres → backfill → start → smoke test → update/rollback.
- `IMPLEMENTATION_PLAN.md` — architecture decisions, storage split, git workflow, migration status.
- `ROUTINES.md` — the weekly/hourly routine contract against MCP, cloud dry-run path.
- `src/README.md` — service list, one-shot jobs, MCP tool reference, DB↔git reconcile/parity checks.

## Contradiction Protocol
Macro bias vs technical structure conflict → flag with `> [!warning]`, lower conviction to MEDIUM
regardless of Zone Confluence score, note it in the validation/forecast markdown (this repo has
no `_HOT.md` to park pending questions in — the forecast/validation file itself is the record).
