# auto-swing src

Deployed app folder. Run commands from the `auto-swing/` repo root. Postgres, deterministic
pipeline, and read/compute/write MCP bridge.

## Local Postgres

```bash
docker compose -f src/docker-compose.yml up -d postgres
```

Optional production/local overrides live in `src/.env` (gitignored). Without `.env`, compose uses dev
defaults:

- DB: `auto_swing`
- User: `auto_swing`
- Password: `auto_swing_dev_password`
- Port: `127.0.0.1:5432`

## Backfill From SQLite

```bash
docker compose -f src/docker-compose.yml run --rm pipeline \
  python src/scripts/backfill_sqlite_to_postgres.py
docker compose -f src/docker-compose.yml run --rm pipeline \
  python src/scripts/diff_sqlite_postgres.py
```

Place the migration SQLite file at `data/database/index.db` first, or restore a Postgres dump instead.
Backfill excludes SQLite `lost_and_found`. That table is a recovery artifact, not app state.

Apply schema migrations to an existing Postgres volume:

```bash
docker compose -f src/docker-compose.yml exec -T pipeline \
  python src/scripts/apply_postgres_migrations.py
```

## Backup

```bash
cd src
./scripts/backup_postgres.sh
```

## Pipeline Scheduler

One-shot dry control:

```bash
docker compose -f src/docker-compose.yml run --rm pipeline \
  python src/pipeline/scheduler.py --once brief_refresh --instrument eurusd
docker compose -f src/docker-compose.yml run --rm pipeline \
  python src/pipeline/scheduler.py --once zone_outcomes
docker compose -f src/docker-compose.yml run --rm pipeline \
  python src/pipeline/scheduler.py --once trade_outcome
docker compose -f src/docker-compose.yml run --rm pipeline \
  python src/pipeline/scheduler.py --once calibration
docker compose -f src/docker-compose.yml run --rm pipeline \
  python src/pipeline/scheduler.py --once reconcile
docker compose -f src/docker-compose.yml run --rm pipeline \
  python src/pipeline/scheduler.py --once send_notifications
```

Long-running scheduler:

```bash
docker compose -f src/docker-compose.yml up -d pipeline
```

Run records append to `src/logs/pipeline_run.jsonl` by default. This log path is local runtime state
and ignored by git.

## MCP Read/Compute Server

Two transports over the **same** tool surface (`src/mcp-server/tools.py`):

- `mcp-server` — port 8765, REST/JSON (`/call`, `/tools/<name>`), for `curl`.
- `mcp-native` — port 8766, native MCP over Streamable HTTP (`/mcp`), register in Claude Code.

Start full local stack:

```bash
docker compose -f src/docker-compose.yml up -d --build
```

REST endpoint (8765):

```bash
curl http://127.0.0.1:8765/health
curl -H "Authorization: Bearer dev-token" http://127.0.0.1:8765/tools
curl -H "Authorization: Bearer dev-token" \
  -H "Content-Type: application/json" \
  -d '{"tool":"get_brief","args":{"instrument":"eurusd","kind":"validate"}}' \
  http://127.0.0.1:8765/call
```

Native MCP endpoint (8766) — register with Claude Code:

```bash
claude mcp add --transport http auto-swing http://127.0.0.1:8766/mcp \
  --header "Authorization: Bearer dev-token"
```

Both share one auth token and one Postgres backend. Set `MCP_AUTH_TOKEN` in `.env` before any
LAN/tunnel exposure. Read/compute tools:
`sql_query`, `get_brief`, `get_news`, `get_econ`, `get_calibration`, `compute_indicators`,
`run_gate`, `run_replay`, `run_calibration`, `run_backtest`.

Structured write tools:
`publish_zone`, `write_verdict`, `queue_notification`, `update_checkpoint`.

Parity check:

```bash
docker compose -f src/docker-compose.yml exec -T pipeline \
  python src/scripts/mcp_parity_check.py --url http://mcp-server:8765 --token dev-token \
  --instrument eurusd --date 2026-07-04
```

Reconcile DB versus git prose:

```bash
docker compose -f src/docker-compose.yml exec -T pipeline \
  python src/scripts/reconcile_db_git.py
```

Notification dry run:

```bash
docker compose -f src/docker-compose.yml exec -T pipeline \
  python src/scripts/send_notifications.py --dry-run
```
