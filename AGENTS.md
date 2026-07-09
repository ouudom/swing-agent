# swing-agent - Codex Operating Manual

## Prime Directive

Operate this repo as the deployed system of record for the swing-trading app.

- Work only inside `swing-agent/`; do not read or write parent `swing-trading/`.
- Runtime state is Postgres, not markdown files.
- Codex judgment runs through MCP only.
- Deterministic code computes numbers; Codex decides ambiguous market judgment.
- Never invent derived numbers in prose. Recompute/read through MCP each run.

## System Shape

Thin deployed swing-trading system for 11 instruments:

`xauusd`, `eurusd`, `gbpusd`, `eurgbp`, `audusd`, `nzdusd`, `usdcad`, `usdchf`,
`usdjpy`, `eurjpy`, `gbpjpy`.

Services:

- `postgres` - canonical DB.
- `pipeline` - APScheduler + deterministic scripts.
- `mcp-native` - native MCP over Streamable HTTP on port `8766`, path `/mcp`.
- `dashboard` - read-only monitoring UI/API on port `8888`.

One app folder matters: `src/`.

There is no `wiki/` anymore. Phase 1, 2026-07-05, moved prose into Postgres. The container runs
from Postgres + config. It never reads markdown as runtime state.

## Postgres Is Canonical

Tables for prose:

- `rulebook` - constitution, setup library, currency exposure, templates, per-instrument profile
  and confluence criteria.
- `context_doc` - regenerated snapshots, especially `yield_environment` and `calibration`.
- `forecast_doc` - weekly forecast prose. Key: `{YYYY-WNN}/{instrument}`.
- `validation_doc` - validation prose. Key: `{YYYY-MM-DD}/{instrument}`.
- `doc_history` - prior prose versions.

Tables for structured trading state:

- `zone_ledger` - published zones and current zone quality state.
- `validation_verdict` - hourly validation verdict records.
- `trade_log` - real order lifecycle state.
- `zone_outcome`, `trade_outcome` - replay/outcome records.
- `feature_snapshot` - frozen feature vectors used for publish/validate decisions.
- `notification_event`, `routine_checkpoint`, `trigger_state` - ops state.

## MCP Only

Register:

```bash
codex mcp add --transport http swing-agent http://<host>:8766/mcp \
  --header "Authorization: Bearer $MCP_AUTH_TOKEN"
```

If a connector cannot send headers, server also accepts `?token=<MCP_AUTH_TOKEN>`.

Current MCP tool surface has 21 tools:

- Read/context: `get_context_pack`, `get_doc`, `list_docs`, `get_brief`, `get_zone_context`,
  `sql_query`, `get_news`, `get_econ`, `get_calibration`.
- Compute: `compute_indicators`, `run_gate`, `run_replay`, `run_calibration`, `run_backtest`.
- Writes: `publish_zone`, `write_verdict`, `write_trade_log`, `snapshot_features`,
  `write_doc`, `queue_notification`, `update_checkpoint`.

`sql_query` is read-only: `SELECT` / `WITH` / `SHOW`, capped by server settings.

`run_backtest` and `run_gate` are allowlisted. Do not bypass with shell unless explicitly doing
local code maintenance, not live ops.

## Judgment Routine Contract

Every live market run follows same order:

1. Read context through MCP:
   `get_context_pack(instrument)`, `get_brief`, `get_zone_context` where relevant,
   gates, calibration, news/econ.
2. Decide:
   zone selection, bias flip, re-forecast need, entry verdict, contradiction handling.
3. Write structured state first:
   `publish_zone`, `write_verdict`, `write_trade_log`, `snapshot_features`.
4. Write prose second:
   `write_doc`.
5. Do not use git as operational record unless user explicitly maintains a separate audit trail.

If a write partially fails, retry same natural key:

- same `zone_id`
- same `run_id`
- same `doc_key`

Writes are designed as upserts. Do not mutate inputs just to make retry pass.

## Weekly Forecast

Monday after weekly data refresh, per instrument:

1. Call `get_context_pack(instrument)`.
2. Call `get_zone_context(instrument)` for full DB-native zone-scoring context:
   structure, momentum, macro, ATR/SL preview, COT.
3. Call `get_brief`, `run_replay`, `get_calibration`, `get_news`, `get_econ`.
4. Select and score Trading Zones.
5. For every published zone:
   `publish_zone(...)`.
6. Freeze R1 features:
   `snapshot_features(event_type="publish", features=<get_zone_context output or scored subset>)`.
7. Write forecast prose:
   `write_doc(doc_type="forecast", key="{YYYY-WNN}/{instrument}", ...)`.

## Validate Routine

Validate is event-gated, not blind hourly.

`src/engine/scripts/ops/fire_validate_trigger.py` runs inside the scheduler at
`:07/:22/:37/:52` UTC, after OHLC refresh. It wakes the model only when deterministic checks find
an actionable live zone.

Fire reasons:

- `ENTRY` - latest H1 touches a live zone, E0 fires toward it, programmatic EC >= `4.0`.
- `INVAL` - V1 or V1b invalidation fires on a still-live zone.

Skips:

- no new H1 since last fire (`trigger_state` dedup).
- no OPEN zone.
- zone already RUNNING or terminal in `trade_log`.
- zone already INVALIDATED.

When fired, per instrument:

1. Read `get_context_pack`, `get_brief`, `compute_indicators`, gates, calibration, news/econ.
2. Decide `ORDER_LIMIT`, `NO_TRADE`, `INVALIDATED`, `HARD_BLOCK`, or `CANCEL_LIMIT`.
3. Write `write_verdict`.
4. Write `write_trade_log`.
5. Freeze R2 features:
   `snapshot_features(event_type="validate", features=<EC breakdown + flags + live inputs>)`.
6. Write validation prose:
   `write_doc(doc_type="validation", key="{YYYY-MM-DD}/{instrument}", ...)`.

Server-enforced gates:

- `write_verdict` rejects `ORDER_LIMIT` when `hard_block_flags` non-empty.
- `write_verdict` rejects `ORDER_LIMIT` when `entry_confluence < 5.0`.
- `write_trade_log` also rejects those cases.
- `write_trade_log` requires `limit_price`, `sl_price`, `tp_price` for `ORDER_LIMIT`.
- Once `trade_log.status` is `RUNNING`, `WIN`, `LOSS`, `BREAKEVEN`, or `EXPIRED`, validate cannot
  change it. Only scheduled `check_live_trades.py` may move it further.

## Trade Math

Do not hand-recompute core trade constants. Read code.

Source: `src/engine/scripts/replay/trade_outcome.py`.

Current v3 formulas:

```text
SL:     H4_ATR14 if (0.5 * D1_ATR14) < H4_ATR14 else avg(0.5 * D1_ATR14, H4_ATR14)
offset: session_mult * SL, outward beyond anchor
        Asia 22-07 UTC = 0.40
        London 07-12 UTC = 0.20
        NY 12-21 UTC = 0.30, owns 12-16 overlap
anchor: confirmation candle close when E0 present and locked 4h; else 50% zone midpoint
TP:     3.0R nearer zone, 4.0R further zone, single limit
BE:     +1.5R
Friday: 13:00 UTC cancel unfilled limits; open positions keep running
```

## Contradiction Protocol

Macro bias vs technical structure conflict:

- Add `> [!warning]` in prose.
- Lower conviction to `MEDIUM` regardless of zone confluence.
- Record why in forecast/validation body via `write_doc`.
- Keep structured state consistent with final decision.

No `_HOT.md`. No parking-lot file. The forecast/validation doc itself is the record.

## Local Code Work

Use repo-local docs:

- `README.md` - orientation.
- `docs/README.md` - project context index.
- `docs/deployment.md` - server deploy, MCP registration, smoke tests.
- `docs/routines.md` - operational routine contract.
- `docs/service-reference.md` - service commands, MCP reference, dashboard notes.
- `docs/implementation-plan.md` - historical only; top notice supersedes old `wiki/` design.

Useful checks:

```bash
docker compose run --rm pipeline python src/engine/scripts/ops/fire_validate_trigger.py --dry-run
docker compose run --rm pipeline python src/engine/scripts/ops/fire_validate_trigger.py --instrument xauusd --dry-run
docker compose exec -T pipeline python src/engine/scripts/ops/apply_postgres_migrations.py
docker compose exec -T pipeline python src/engine/scripts/ops/send_notifications.py --dry-run
```

Dashboard:

```bash
curl http://127.0.0.1:8888/health
curl http://127.0.0.1:8888/api/health
```

MCP health:

```bash
curl http://127.0.0.1:8766/health
```

## Hard Boundaries

- Do not edit parent repo.
- Do not resurrect `wiki/`.
- Do not store computed numbers only in prose.
- Do not bypass MCP for live state writes.
- Do not override hard-block gates with judgment.
- Do not move locked `trade_log` rows from validate.
- Do not expose MCP publicly without strong token and tunnel/VPN.
