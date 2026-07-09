# swing-agent docs

Fast-context index for this repo. Deep dives live in the files below; this page is the map.

## What this is

Self-hosted, Dockerized swing-trading app: deterministic pipeline + Postgres store + native MCP
server, driven by Claude Code (weekly forecast / hourly validation) on a schedule. No Agent SDK
worker — Claude Code talks to the app entirely through MCP. See root [`CLAUDE.md`](../CLAUDE.md)
for the full operating manual (routine contract, trade math, hard boundaries) — that file is
authoritative; this index just orients.

One folder matters at runtime: `src/`. There is no `wiki/` — as of Phase 1 (2026-07-05), Postgres
is canonical for both numbers *and* prose. `src/` never reads a `.md` file at runtime; Claude Code
reads/writes prose through MCP (`get_context_pack`, `get_doc`, `list_docs`, `write_doc`).

## Instruments

11 active: `xauusd` (momentum), `eurusd` `gbpusd` `eurgbp` `audusd` `nzdusd` `usdcad` `usdchf`
(mean-reversion variants), `usdjpy` (asymmetric carry-drift), `eurjpy` `gbpjpy` (cross-JPY fades).

## Services

| Service | Role | Port |
|---|---|---|
| `postgres` | canonical DB | 5432 |
| `pipeline` | APScheduler + deterministic scripts | — |
| `mcp-native` | MCP over Streamable HTTP, `/mcp` | 8766 |
| `dashboard` | read-only monitoring UI/API | 8888 |

## Postgres tables

Prose: `rulebook`, `context_doc`, `forecast_doc`, `validation_doc`, `doc_history`.

Structured state: `zone_ledger`, `validation_verdict`, `trade_log`, `zone_outcome`,
`trade_outcome`, `feature_snapshot`, `notification_event`, `routine_checkpoint`, `trigger_state`.

## MCP tool surface (21 tools)

- Read/context: `get_context_pack`, `get_doc`, `list_docs`, `get_brief`, `get_zone_context`,
  `sql_query` (read-only: `SELECT`/`WITH`/`SHOW`), `get_news`, `get_econ`, `get_calibration`.
- Compute: `compute_indicators`, `run_gate`, `run_replay`, `run_calibration`, `run_backtest`.
- Writes: `publish_zone`, `write_verdict`, `write_trade_log`, `snapshot_features`, `write_doc`,
  `queue_notification`, `update_checkpoint`.

## Trade math (v3)

```text
SL:     H4_ATR14 if (0.5 * D1_ATR14) < H4_ATR14 else avg(0.5 * D1_ATR14, H4_ATR14)
offset: session_mult * SL, outward beyond anchor
        Asia 22-07 UTC = 0.40 | London 07-12 UTC = 0.20 | NY 12-21 UTC = 0.30 (owns 12-16 overlap)
anchor: confirmation candle close (E0, locked 4h) | else 50% zone midpoint
TP:     3.0R nearer zone, 4.0R further zone, single limit; BE at +1.5R
Friday: 13:00 UTC cancel unfilled limits; open positions keep running
```

Source of truth: `src/engine/scripts/replay/trade_outcome.py` — never hand-recompute.

## Docs in this folder

- [`routines.md`](routines.md) — Claude Code weekly/hourly routine contract against MCP.
- [`deployment.md`](deployment.md) — clone → env → Postgres → backfill → start pipeline + MCP →
  smoke test → update/rollback, for a homeserver deploy.
- [`service-reference.md`](service-reference.md) — service commands, one-shot jobs, MCP tool
  reference, DB↔git reconcile.
- [`implementation-plan.md`](implementation-plan.md) — historical architecture decisions, storage
  split, migration status. Not current state — `CLAUDE.md` / root `README.md` / `routines.md`
  supersede it where they conflict.

## Hard boundaries (full list in `CLAUDE.md`)

- Do not resurrect `wiki/`.
- Do not store computed numbers only in prose — recompute through MCP.
- Do not bypass MCP for live state writes.
- Do not override hard-block gates with judgment.
