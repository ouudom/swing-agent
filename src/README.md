# swing-agent src

Deployed app folder. Run commands from the `swing-agent/` repo root. Postgres, deterministic
pipeline, and read/compute/write MCP bridge.

## Local Postgres

```bash
docker compose up -d postgres
```

Optional production/local overrides live in `.env` (gitignored, repo root). Without `.env`, compose uses dev
defaults:

- DB: `swing_agent`
- User: `swing_agent`
- Password: `swing_agent_dev_password`
- Port: `127.0.0.1:5432`

## Backfill From SQLite

```bash
docker compose run --rm pipeline \
  python src/engine/scripts/ops/backfill_sqlite_to_postgres.py
docker compose run --rm pipeline \
  python src/engine/scripts/ops/diff_sqlite_postgres.py
```

Place the migration SQLite file at `data/database/index.db` first, or restore a Postgres dump instead.
Backfill excludes SQLite `lost_and_found`. That table is a recovery artifact, not app state.

Apply schema migrations to an existing Postgres volume:

```bash
docker compose exec -T pipeline \
  python src/engine/scripts/ops/apply_postgres_migrations.py
```

## Backup

```bash
cd src
./engine/scripts/ops/backup_postgres.sh
```

## Pipeline Scheduler

One-shot dry control:

```bash
docker compose run --rm pipeline \
  python src/pipeline/scheduler.py --once brief_refresh --instrument eurusd
docker compose run --rm pipeline \
  python src/pipeline/scheduler.py --once zone_outcomes
docker compose run --rm pipeline \
  python src/pipeline/scheduler.py --once trade_outcome
docker compose run --rm pipeline \
  python src/pipeline/scheduler.py --once check_live_trades
docker compose run --rm pipeline \
  python src/pipeline/scheduler.py --once calibration
docker compose run --rm pipeline \
  python src/pipeline/scheduler.py --once reconcile
docker compose run --rm pipeline \
  python src/pipeline/scheduler.py --once send_notifications
```

Long-running scheduler:

```bash
docker compose up -d pipeline
```

Run records append to `src/logs/pipeline_run.jsonl` by default. This log path is local runtime state
and ignored by git.

## MCP Read/Compute Server

`mcp-native` — port 8766, native MCP over Streamable HTTP (`/mcp`), register in Claude Code —
fronts the tool surface (`src/mcp-server/tools.py`).

Start full local stack:

```bash
docker compose up -d --build
```

Native MCP endpoint (8766) — register with Claude Code:

```bash
claude mcp add --transport http swing-agent http://127.0.0.1:8766/mcp \
  --header "Authorization: Bearer dev-token"
```

Set `MCP_AUTH_TOKEN` in `.env` before any LAN/tunnel exposure. Read/compute tools:
`sql_query`, `get_brief`, `get_zone_context`, `get_news`, `get_econ`, `get_calibration`,
`compute_indicators`, `run_gate`, `run_replay`, `run_calibration`, `run_backtest`.

Structured write tools:
`publish_zone`, `write_verdict`, `write_trade_log`, `queue_notification`, `update_checkpoint`.

`write_trade_log` logs the hourly /validate routine's LIVE order state (ORDER_LIMIT with
limit/SL/TP, NO_TRADE, INVALIDATED) into `trade_log` — distinct from `write_verdict`'s
`validation_verdict` record and from `zone_ledger.status`/`replay_status` (zone-quality/
replay bookkeeping, not real order lifecycle). Once a row reaches RUNNING (filled) or a
terminal status, only the scheduled `check_live_trades` job may move it further — the
hourly routine can no longer flip its status.

## Monitoring Dashboard

Read-only React/Vite frontend for an at-a-glance system overview — open zones + latest verdict,
system P&L replay (total R / win-rate / R-by-instrument), recent validations & trades, pipeline-run
health, and routine/data freshness. Standalone service (`dashboard`), own two-stage image
(node build → python API); it does **not** import the MCP tool surface — it carries its own
`pg_connect` and a fixed map of read-only SQL behind `/api/*`, and serves the built bundle
same-origin. Source: `src/dashboard/` (`api/server.py`, `web/`).

- Port 8888, bound `127.0.0.1` — view over an SSH tunnel (`ssh -L 8888:127.0.0.1:8888 <host>`).
- No auth (localhost-only, read-only). No bind mount — **rebuild the image to ship UI changes**:
  `docker compose up -d --build dashboard`.
- Local web dev: `cd src/dashboard/web && npm install && npm run dev` (Vite proxies `/api` → :8888).

```bash
curl http://127.0.0.1:8888/health
curl http://127.0.0.1:8888/api/health   # routines + jobs + data freshness
```

Reconcile DB versus git prose:

```bash
docker compose exec -T pipeline \
  python src/engine/scripts/ops/reconcile_db_git.py
```

Notification dry run:

```bash
docker compose exec -T pipeline \
  python src/engine/scripts/ops/send_notifications.py --dry-run
```
