# swing-agent Routines

Operational contract for the AI leg. Run from the `swing-agent/` repo root. Postgres is canonical
for numbers and prose (Phase 1, 2026-07-05) — there is no `wiki/` to check out or commit to.

## Ownership

- Weekly writes only `forecast_doc` (key `{YYYY-WNN}/{instrument}`) via `write_doc`.
- Validate writes only `validation_doc` (key `{YYYY-MM-DD}/{instrument}`) via `write_doc`.
- Structured DB write (`publish_zone`/`write_verdict`/`write_trade_log`) happens first through
  MCP; the `write_doc` prose write happens second — both are the durable record, no git step.
- Reconcile (`reconcile_db_git.py`) is now optional — only relevant if this deploy still
  maintains a separate git-based audit trail alongside Postgres.

## Laptop Validate Routine

Run hourly during market hours from a local checkout on the `live` branch:

```bash
export MCP_URL=http://127.0.0.1:8766/mcp
export MCP_AUTH_TOKEN=<token>

# Per instrument:
# 1. Call MCP get_context_pack(instrument) — rules + confluence + macro + calibration.
# 2. Call MCP get_brief/run_gate/compute_indicators.
# 3. Decide verdict.
# 4. MCP write_verdict + write_trade_log.
# 5. MCP write_doc(doc_type="validation", key="{date}/{instrument}", body=<markdown>).
```

Retry rule: writes are idempotent (upsert on natural key / doc_key) — re-run with the same
`run_id`/`doc_key` rather than mutating state on a partial failure.

### Event-Gated Firing (replaces the blind hourly clock)

Rather than waking Claude every hour for all 11 instruments, the deterministic pipeline decides
*when* a `/validate` run is worth the tokens and fires the routine trigger itself. The gate
(`src/engine/scripts/ops/fire_validate_trigger.py`) runs in-container on the scheduler
(mon-fri, `:07/:22/:37/:52`, a few minutes after each `brief_refresh` OHLC pull) and, per
instrument, POSTs the Claude routine trigger **only** when a live zone is actionable:

- **ENTRY** — the latest H1 bar touches a live zone, an E0 fired toward it (1H pin/engulf or
  RSI-reclaim), and the programmatic Entry Confluence ≥ `EC_GATE` (4.0 — deliberately below the
  real 5.0 floor; the scorer is provisional, so gate loose and let Claude make the real call).
- **INVAL** — a V1 (D1 close beyond the zone) or V1b (two consecutive H4 closes beyond
  zone+ATR buffer) fired on a still-live zone → wake `/validate` to formally INVALIDATE it.

It skips (no fire, no tokens) when: no new H1 bar closed since the last fire for that instrument
(`trigger_state` dedup — this also silences weekends/holidays); no OPEN zone; or every zone is
already RUNNING/terminal in `trade_log` (a live trade → `check_live_trades.py` owns it) or
already INVALIDATED. The gate is pure Python — no Claude, no MCP writes.

Env for the trigger POST (set in `.env`, read by the container):

```bash
CLAUDE_TRIGGER_URL=https://api.anthropic.com/v1/claude_code/routines/<trigger_id>/fire
CLAUDE_TRIGGER_TOKEN=<token>          # falls back to ANTHROPIC_API_KEY
CLAUDE_TRIGGER_AUTH_HEADER=x-api-key  # set 'Authorization' if the routine wants 'Bearer <token>'
```

**Rollout — dry-run against real Postgres first** (the gate logic can only be verified against
live zones + OHLC, which exist only in the deployed DB):

```bash
docker compose run --rm pipeline \
  python src/engine/scripts/ops/fire_validate_trigger.py --dry-run          # all 11, no POST
docker compose run --rm pipeline \
  python src/engine/scripts/ops/fire_validate_trigger.py --instrument xauusd --dry-run
```

Confirm the FIRE/skip decisions look right, then let the scheduler job run live. Until
`CLAUDE_TRIGGER_URL` is set, the gate evaluates and logs but every fire attempt errors out
loudly (no silent no-op), so a misconfigured token surfaces immediately.

## Weekly Routine

Monday after weekly data refresh:

```bash
export MCP_URL=http://127.0.0.1:8766/mcp
export MCP_AUTH_TOKEN=<token>

# For all 11 instruments:
# 1. Call MCP get_context_pack(instrument) + get_zone_context (structure/momentum/macro/ATR+SL/COT) +
#    get_brief/run_replay/get_calibration/get_news/get_econ.
# 2. Score Trading Zones.
# 3. For every published zone: MCP publish_zone.
# 4. MCP write_doc(doc_type="forecast", key="{week}/{instrument}", body=<markdown>).
```

## Reconcile

```bash
docker compose exec -T pipeline \
  python src/engine/scripts/ops/reconcile_db_git.py
```

Strict mode for CI/routine hard-fail:

```bash
docker compose exec -T pipeline \
  python src/engine/scripts/ops/reconcile_db_git.py --strict
```

## Notifications

MCP write tools queue `notification_event` rows for important events. Sender:

```bash
docker compose exec -T pipeline \
  python src/engine/scripts/ops/send_notifications.py
```

The scheduler runs notification send every 5 minutes. If Telegram env is missing, it exits cleanly.

## Cloud Dry Run

Only after laptop routine is boring:

1. Expose MCP via Tailscale or Cloudflare Tunnel.
2. Require strong `MCP_AUTH_TOKEN`.
3. Shadow mode first: read MCP context only, no `publish_zone`/`write_verdict`/`write_doc`.
4. Enable writes for one instrument only.
5. Expand after that instrument's writes look right in the dashboard.

Rollback: disable cloud routine; laptop routine remains source of operations.
