# swing-agent

Self-hosted, Dockerized swing-trading application: deterministic pipeline + Postgres store +
MCP server, driven by Claude Code (weekly forecast / hourly validation) on a schedule. No
Agent SDK worker — Claude Code talks to the app entirely through MCP.

Two folders:

- **`wiki/`** — AI execution context. Curated rules, per-instrument confluence + profile,
  macro/calibration state, output templates, and the two AI-output folders
  (`weekly-forecasts/`, `validations/`). Nothing else lives here — no history dumps, no
  decisions log, no `_HOT`/`_INDEX`.
- **`src/`** — the deployed app: deterministic pipeline scripts, Postgres schema, scheduler,
  and two MCP transports (`mcp-server` REST on :8765, `mcp-native` on :8766 for Claude Code).

## Quick links

- [`DEPLOYMENT_UBUNTU.md`](DEPLOYMENT_UBUNTU.md) — clone → env → Postgres → backfill → start
  pipeline + MCP → smoke test → update/rollback, for a homeserver deploy.
- [`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md) — architecture decisions, storage split,
  git workflow, deterministic-vs-AI split, migration status.
- [`ROUTINES.md`](ROUTINES.md) — the Claude Code weekly/hourly routine contract against MCP.
- [`src/README.md`](src/README.md) — app-level dev notes: services, one-shot jobs, MCP tool
  reference, DB↔git reconcile/parity checks.

## Deploy scope

Only `swing-agent/` is deployed — the parent `swing-trading` repo (research history, full
`wiki/`, `scripts/`) is not part of the container image or the runtime. `src/` runs headless
on Postgres + config; it never reads a `.md` file.
