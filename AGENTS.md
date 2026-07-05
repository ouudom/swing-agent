# swing-agent — Codex Operating Manual

## What This Is
Deployed, thin version of the multi-instrument swing-trading system (11 instruments: xauusd +
10 FX pairs). Deterministic pipeline + Postgres run headless in Docker on a homeserver; the
judgment leg (weekly forecast + hourly validation) is **you, Codex, on a schedule/routine**,
talking to the app through **MCP only** — no Agent SDK worker.

This repo is self-contained: **do not read or write the parent `swing-trading` repo** (research
history, full `wiki/`, `scripts/`) when working here. `swing-agent/` is what deploys.

## One Folder — `src/`
There is no `wiki/` anymore (retired Phase 1, 2026-07-05) — **Postgres is canonical for every
number AND every word**. `src/` is the deployed app: deterministic pipeline scripts, Postgres
schema, scheduler, the native MCP server, the dashboard. The container never reads a `.md`; it
runs on Postgres + config only.

## Storage Split — Postgres canonical for words too (Phase 1)
Rules, forecasts, validations live in four DB tables served over MCP:
- `rulebook` — constitution, setup_library, currency_exposure, per-instrument profile +
  confluence_criteria, templates (human-authored reference).
- `context_doc` — regenerated snapshots: `yield_environment` (macro), `calibration`.
- `forecast_doc` — weekly forecast prose (key `{YYYY-WNN}/{instrument}`).
- `validation_doc` — validation prose (key `{YYYY-MM-DD}/{instrument}`).
- `doc_history` — prior versions (replaces the git blame lost by leaving files).

Read via `get_context_pack(instrument)` (boot bundle) / `get_doc(doc_type,key)` / `list_docs(...)`;
write via `write_doc(...)`. A fresh cloud routine gets full judgment context from MCP alone — no
git checkout needed. Still never store a derived number in a doc body — recompute via MCP each
time. `src/database/init.sql` + `apply_postgres_migrations.py` create the tables;
`import_wiki_to_doc.py` was the one-shot migration off the old `wiki/*.md` (already run, file
history only — no wiki/ left to re-import from).

## MCP — your only gateway to the app
One transport, 21 tools, one Postgres backend:
- `mcp-native` (native MCP, Streamable HTTP, port 8766, `/mcp` endpoint) — register via
  `Codex mcp add --transport http swing-agent http://<host>:8766/mcp --header
  "Authorization: Bearer $MCP_AUTH_TOKEN"`.

Tools: `get_brief`, `get_zone_context` (full DB-native zone-scoring context for /weekly —
structure/momentum/macro/ATR+SL/COT; replaces the old weekly_pull txt), `sql_query`
(read-only SELECT/WITH/SHOW only), `get_news`, `get_econ`, `get_calibration`,
`compute_indicators`, `run_gate`, `run_replay`, `run_calibration`,
`run_backtest` (allowlisted scripts + args only) — data/compute, read-only or sandboxed.
`get_context_pack`, `get_doc`, `list_docs` — prose docs (rules/forecasts/validations) read from DB.
`write_doc` — upsert a prose doc (versions prior into `doc_history`).
`publish_zone`, `write_verdict`, `write_trade_log`, `queue_notification`, `update_checkpoint` — structured writes,
idempotent (upsert on natural key). **`write_verdict` hard-rejects `ORDER_LIMIT` if
`hard_block_flags` is non-empty or `entry_confluence < 5.0`** — the gate is enforced server-side,
not by your judgment alone.
`snapshot_features` — freezes the feature vector a decision was scored on (`feature_snapshot`
table, Phase 3) for research/backtesting once enough weeks accumulate; call once per zone at
publish (R1) and once per zone at validate (R2), not on every read.

## Per-Run Discipline — DB is the whole record now
1. Call MCP to read context (`get_context_pack`, `get_brief`, gates, calibration, news/econ).
2. Decide (zone selection / bias-flip / re-forecast / verdict) — this is the part that needs you.
3. **Structured write through MCP** (`publish_zone` / `write_verdict` / `write_trade_log`) — the
   numeric durable record.
4. **Prose write through MCP** (`write_doc`) — the forecast/validation markdown body, replacing
   the old `wiki/weekly-forecasts/...` / `wiki/validations/...` files. `write_doc` versions the
   prior body into `doc_history` automatically.
5. git is now optional (no `wiki/` mirror to keep in sync) — only touch it if this deploy still
   maintains a separate git-based audit trail; otherwise Postgres alone is the record.

If a write in step 3/4 fails partway, do **not** re-call with mutated state to "fix" it — re-run
with the same `zone_id`/`doc_key`; every write is idempotent (upsert on natural key).

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
These constants live in `src/engine/scripts/replay/trade_outcome.py` (`TP_R_NEAR`, `TP_R_FAR`,
`_SESSION_MULT`, `friday_cutoff`) — read the code, don't hand-recompute.

## Docs Map
- `README.md` — orientation, quick links.
- `DEPLOYMENT_UBUNTU.md` — clone → env → Postgres → backfill → start → smoke test → update/rollback.
- `IMPLEMENTATION_PLAN.md` — architecture decisions, storage split, git workflow, migration status.
- `ROUTINES.md` — the weekly/hourly routine contract against MCP, cloud dry-run path.
- `src/README.md` — service list, one-shot jobs, MCP tool reference, DB↔git reconcile/parity checks.

## Contradiction Protocol
Macro bias vs technical structure conflict → flag with `> [!warning]`, lower conviction to MEDIUM
regardless of Zone Confluence score, note it in the validation/forecast doc body written via
`write_doc` (there is no `_HOT.md` to park pending questions in — the forecast/validation doc
itself is the record).
