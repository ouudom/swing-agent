# auto-swing Routines

Operational contract for the AI leg. Run from the `auto-swing/` repo root. The app owns numbers in
Postgres. Claude Code owns prose in `wiki/`.

## Ownership

- Weekly writes only `wiki/weekly-forecasts/{instrument}/`.
- Validate writes only `wiki/validations/{instrument}/`.
- Structured DB write happens first through MCP; markdown commit happens second.
- Reconcile flags any split-brain after retries.

## Laptop Validate Routine

Run hourly during market hours from a local checkout on the `live` branch:

```bash
export MCP_URL=http://127.0.0.1:8765
export MCP_AUTH_TOKEN=<token>

# Per instrument:
# 1. Read wiki context.
# 2. Call MCP get_brief/run_gate/compute_indicators.
# 3. Decide verdict.
# 4. MCP write_verdict.
# 5. Write wiki/validations/{instrument}/YYYY-MM-DD.md.
# 6. git add + commit + push.
```

Retry rule: if DB write succeeds and git commit fails, do not write DB again with a new `run_id`.
Reuse the same `run_id`, fix git, then run reconcile.

## Weekly Routine

Monday after weekly data refresh:

```bash
export MCP_URL=http://127.0.0.1:8765
export MCP_AUTH_TOKEN=<token>

# For all 11 instruments:
# 1. Call MCP get_brief/run_replay/get_calibration/get_news/get_econ.
# 2. Write weekly forecast markdown.
# 3. For every published zone: MCP publish_zone.
# 4. git add + commit + push.
```

## Reconcile

```bash
docker compose -f src/docker-compose.yml exec -T pipeline \
  python src/scripts/reconcile_db_git.py
```

Strict mode for CI/routine hard-fail:

```bash
docker compose -f src/docker-compose.yml exec -T pipeline \
  python src/scripts/reconcile_db_git.py --strict
```

## Notifications

MCP write tools queue `notification_event` rows for important events. Sender:

```bash
docker compose -f src/docker-compose.yml exec -T pipeline \
  python src/scripts/send_notifications.py
```

The scheduler runs notification send every 5 minutes. If Telegram env is missing, it exits cleanly.

## Cloud Dry Run

Only after laptop routine is boring:

1. Expose MCP via Tailscale or Cloudflare Tunnel.
2. Require strong `MCP_AUTH_TOKEN`.
3. Give cloud routine git credentials limited to this repo.
4. Shadow mode first: read MCP, write markdown to test branch, no `publish_zone`/`write_verdict`.
5. Enable writes for one instrument only.
6. Expand after reconcile stays clean.

Rollback: disable cloud routine; laptop routine remains source of operations.
