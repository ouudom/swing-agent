# Framework Migration Plan — swing-agent

Status: IMPLEMENTED (code), UNTESTED (no live Postgres/Redis available in the
implementing session — see "Verification status" at the bottom) · Author: Claude ·
Date: 2026-07-12 · Branch: `framework-migration`

Convert the ad-hoc script pipeline into a proper framework-project: installable package,
pydantic config, Celery + Redis task queue, Celery Beat scheduling, SQLAlchemy 2.0 +
Alembic (Postgres-only), FastAPI services.

## Decisions (locked)

| Decision | Choice |
|---|---|
| Queue / scheduler | **Celery + Redis** (Beat replaces APScheduler cron; worker pool runs jobs; Redis = broker + result backend) |
| Data layer | **Postgres-only + SQLAlchemy 2.0 + Alembic** — drop sqlite backend and all-string CSV frames |
| Rollout | **Phased**, this doc approved first |

## Current state (baseline)

- `src/pipeline/scheduler.py` — single **blocking** `APScheduler` process. Jobs run
  synchronously in-process.
- `src/pipeline/tasks.py::run_job` — string `if/elif` dispatch → `commands.*`.
- `src/engine/commands.py` — every job **shells out** via `subprocess` (`pyrun` →
  `pyrun.sh` → python script). Fork-per-job + stdout parsing.
- `src/engine/scripts/db.py` — dual sqlite/postgres, all-string CSV-shaped frames (legacy).
- `src/mcp_server/` (876 LOC), `src/dashboard/api/server.py` (589 LOC).
- Compose services: `postgres`, `pipeline`, `mcp-native`, `dashboard`.

Pain: one slow job blocks the cron loop; no retry/isolation/backpressure; no
concurrency across 11 instruments; fragile subprocess boundary; typed data faked as strings.

## Target architecture

```
APScheduler blocking loop        →  Celery Beat (cron) + Redis broker
subprocess in-process jobs       →  Celery worker pool (isolated, retry, soft timeout)
if/elif run_job dispatch         →  @app.task registry
all-string frames + dual backend →  SQLAlchemy 2.0 models + Alembic, Postgres-only
loose scripts + argparse + sys.path hacks → installable package (pyproject, src-layout)
scattered os.getenv              →  pydantic-settings Settings
trigger_state dedup in Postgres  →  Redis SETNX distributed lock
```

Compose after: `postgres`, `redis`, `worker`, `beat`, `mcp`, `dashboard` (+ optional `flower`).

## Phases

### Phase 0 — package hygiene (no behavior change)
- Add `pyproject.toml`; single installable package `swing_agent` (src-layout).
- Remove `sys.path.insert` hacks and the `pyrun.sh` macOS/`.pydeps` sandbox split.
- Deps declared in pyproject (retire `requirements.txt` as source of truth).
- `pydantic-settings` `Settings` object: `POSTGRES_*`, `TWELVE_DATA_KEY`, `FRED_KEY`,
  `REDIS_URL`, `MCP_AUTH_TOKEN`, `MCP_HOST/PORT`, `DASHBOARD_*`. Replace scattered
  `os.getenv` (in `tasks.py`, `db.py`, `scheduler.py`, MCP, dashboard).
- **Exit check:** `pip install -e .`, all existing scripts still run via console entrypoints.

### Phase 1 — Redis + Celery, replace scheduler
- Add `redis:7-alpine` service to compose (healthcheck, `redis_data` volume optional).
- New Celery app `swing_agent.queue.app` (broker + result = Redis).
- Convert each `commands.*` job → `@app.task`:
  - `autoretry_for=(TransientError,)`, `max_retries`, `retry_backoff=True`.
  - `soft_time_limit` from existing per-job budgets (fetch 900/1800, replay 600,
    validate 600, notify 120, live 120).
  - `acks_late=True`, `reject_on_worker_lost=True` for at-least-once.
- Compose services replace `pipeline`:
  - `worker` = `celery -A swing_agent.queue worker` (concurrency tuned to instrument count).
  - `beat`   = `celery -A swing_agent.queue beat` — Beat schedule replaces `build_scheduler()`:
    - `market_cycle` cron `:2,:22,:42` (mon-fri sun-window)
    - `context_refresh` `:10`
    - `send_notifications` `*/5`
    - `macro_refresh` `23:10`
    - `nightly_replay` `22:00`
  - Keep `is_fx_market_open()` as an in-task guard (Beat has no market awareness).
- `market_cycle` / `nightly_replay` become Celery `chain`/`group` real dependency graphs:
  - `chain(price_refresh, group(check_live_trades, fire_validate_trigger), send_notifications)`
  - `chain(group(zone_outcomes, trade_outcome), calibration, weekly_digest, send_notifications)`
- `RunRecord` persistence → keep the run-log table write via task signals
  (`task_prerun`/`task_postrun`/`task_failure`); failures still `queue_notification`.
- **Exit check:** Beat fires jobs on Redis, worker executes, run-log + notifications intact;
  `--once` replaced by `celery call` / a thin CLI.

### Phase 2 — kill the subprocess boundary
- Import engine scripts as functions; tasks call them directly (no `subprocess`, no
  stdout parsing). Keep each script's `argparse __main__` for manual/local runs.
- **Correction (found during implementation):** `fetch_data.py --instrument all` is
  deliberately **sequential with a 9s sleep** between instruments
  (`src/engine/scripts/pipeline/fetch_data.py` main loop) — TwelveData free tier caps at
  8 API credits/minute; parallelizing it would blow through the rate limit and reintroduce
  the exact OHLC-freshness stagger the sleep was added to fix. Do **not** fan this out via
  a Celery `group`. `price_refresh("all")` stays one task, one subprocess call, sequential
  internally — only the *job-level* graph (independent jobs like `check_live_trades` ∥
  `fire_validate_trigger`, or `zone_outcomes` ∥ `trade_outcome`, none of which hit
  TwelveData) gets Celery-level parallelism. That part landed in Phase 1's `market_cycle`/
  `nightly_replay` tasks.
- Delete `commands.run/pyrun` shelling; `commands.py` becomes thin typed wrappers or folds
  into tasks. **Deferred** — importing 15+ engine scripts in-process instead of via
  subprocess touches every script's global state/argparse assumptions and cannot be
  verified without a live Postgres + API-key run; do this as its own tested pass, not
  bundled into the queue migration.
- **Exit check:** no `subprocess` in the hot path *for jobs where that's safe*; rate-limited
  external-API jobs keep their existing pacing unchanged.

### Phase 3 — data layer (SQLAlchemy + Alembic, Postgres-only)
- SQLAlchemy 2.0 declarative models for all tables (`zone_ledger`, `zone_outcome`,
  `trade_outcome`, `validation_verdict`, `trade_log`, `feature_snapshot`,
  `notification_event`, `routine_checkpoint`, `trigger_state`, `ohlc`, `macro_series`,
  `market_series`, `news`, `econ_calendar`, `rulebook`, `context_doc`, `forecast_doc`,
  `validation_doc`, `doc_history`, `system_config`).
- Alembic replaces `init.sql` + `apply_postgres_migrations.py`; baseline migration from
  current schema, then incremental.
- Delete sqlite backend + all-string frames from `db.py`; typed reads/writes.
- Migrate callers: replay scripts, `ohlc_store.upsert`, MCP tools, dashboard queries.
- **Exit check:** `alembic upgrade head` builds schema; sqlite code path gone; MCP
  `sql_query` still read-only over Postgres.

### Phase 4 — service framework + Redis leverage
- Confirm/port MCP server + dashboard API to FastAPI (async, lifespan, DI Settings).
- Redis distributed lock for `fire_validate_trigger` dedup (SETNX) replacing/augmenting
  `trigger_state`.
- Redis cache for hot context (`get_context_pack`, calibration) with TTL.
- Optional `flower` service for Celery observability; or task state surfaced in dashboard.

### Phase 5 — ops hardening
- `structlog` structured JSON logging across worker/beat/services.
- Healthchecks: `redis` (`redis-cli ping`), `worker` (`celery inspect ping`), `beat`.
- Dead-letter: exhausted-retry tasks → `notification_event` (hook already exists).
- Idempotency: confirm upserts on natural keys (`zone_id`, `run_id`, `doc_key`) survive
  at-least-once redelivery.

## Risks / notes

- **MCP-only live-state contract** (CLAUDE.md) unchanged — Celery is internal execution;
  Claude still writes state through MCP tools.
- Celery task idempotency is mandatory (at-least-once). All writes already upsert on
  natural keys — verify per task before enabling `acks_late`.
- Market-open guard must live in-task; Beat cron is timezone/DST only.
- Phase 3 is the largest blast radius (touches every DB caller). Land Phases 0–2 first;
  they're independently shippable.
- Secrets stay in `.env`; add `REDIS_URL`. No new external services beyond Redis.

## Rollback

Each phase is a separate branch/PR. Phases 0–2 keep the same job semantics, so revert =
restore the `pipeline` compose service + `scheduler.py`. Phase 3 rollback needs a schema
snapshot before `alembic upgrade` (pg_dump in the deploy step).

## What actually landed (this pass, branch `framework-migration`)

| Phase | Status | Files |
|---|---|---|
| 0 | Done | `pyproject.toml`, `src/settings.py`, `__init__.py`s, `mcp-server/`→`mcp_server/` rename |
| 1 | Done | `src/pipeline/celery_app.py`, `celery_tasks.py`; `redis`/`worker`/`beat` in `docker-compose.yml`; `pipeline` service removed |
| 2 | Scoped down | Job-graph parallelism (see correction above) landed via Phase 1's `market_cycle`/`nightly_replay`. Subprocess-boundary removal + fetch-fanout explicitly **not done** — see rationale inline in Phase 2 above |
| 3 | Scaffolded, not cut over | `src/db/models.py` (SQLAlchemy 2.0, all 21 tables, exact mirror of `init.sql`), `alembic.ini`, `src/db/migrations/` incl. baseline migration generated verbatim from `init.sql`. **Not yet wired** — `engine/scripts/db.py` (sqlite/postgres dual-backend) is still the live path; every caller (`zone_ledger.py`, `zone_outcomes.py`, `trade_outcome.py`, `ohlc_store.py`, MCP tools, dashboard) is untouched |
| 4 | Partial | `src/dashboard/api/app.py` — FastAPI port of `server.py`, same SQL/endpoints, wired into `src/dashboard/Dockerfile` (`CMD` now runs `app.py`; revert line included in the Dockerfile comment). `src/redis_lock.py` added as a standalone SETNX lock/cache utility — **not wired** into `fire_validate_trigger.py` (live order-dedup logic, needs a tested cutover, not a blind edit). MCP server left as-is (already ASGI/ FastMCP, no framework gap) |
| 5 | Partial | `src/logging_config.py` (structlog) wired into `celery_app.py`/`celery_tasks.py` only — dashboard's isolated Docker build context (`./src/dashboard`) can't reach it, kept on plain `print()` by design. Celery `task_failure` signal → `queue_notification` dead-letter hook added. Worker/beat healthchecks in compose. Idempotency audit of natural-key upserts **not done** — needs a live-DB pass |

## Verification status — read before deploying

**Nothing here has run against a live Postgres, Redis, or Celery worker.** This
session had no docker/database access. Every file above passed `python -m py_compile`
(syntax-valid) and the new `docker-compose.yml` parses as valid YAML with the expected
6 services — that is the full extent of verification performed.

Before this goes anywhere near the live deployment:
1. `docker compose build worker beat dashboard mcp-native` — confirm the shared
   Dockerfile installs celery/redis/fastapi/sqlalchemy/alembic/structlog cleanly.
2. `docker compose up postgres redis worker beat` — confirm the worker connects to
   Redis, Beat schedules fire, `celery -A pipeline.celery_app inspect ping` succeeds.
3. Trigger one job manually (`celery -A pipeline.celery_app call
   pipeline.celery_tasks.run_job_task --args='["context_refresh"]'`) and confirm a
   `pipeline_run` row lands, matching the old `--once context_refresh` behavior.
4. Confirm `market_cycle`'s `group().get()` fan-out doesn't deadlock — worker
   concurrency is set to 4 specifically for this; don't lower it without re-checking.
5. Dashboard: `curl :8888/health` and a couple of `/api/*` routes; diff a response
   against the old `server.py` for the same endpoint before fully cutting over.
6. Do **not** run `alembic upgrade head` against the live database — it already has
   this schema from `init.sql`. Run `alembic stamp 0001_baseline` instead so future
   migrations have a starting point without touching data.
