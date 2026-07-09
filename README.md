# swing-agent

Self-hosted, Dockerized swing-trading application: deterministic pipeline + Postgres store +
MCP server, driven by Claude Code (weekly forecast / hourly validation) on a schedule. No
Agent SDK worker — Claude Code talks to the app entirely through MCP.

One folder — `src/`: the deployed app (deterministic pipeline scripts, Postgres schema,
scheduler, native MCP server on :8766 `/mcp`, dashboard). There is no `wiki/` anymore — as of
Phase 1 (2026-07-05), Postgres is canonical for both numbers *and* prose. Rules, forecasts, and
validations live in `rulebook` / `context_doc` / `forecast_doc` / `validation_doc`, served over
MCP (`get_context_pack`, `get_doc`, `list_docs`, `write_doc`) and browsable in the dashboard's
Docs tab.

## Quick links

- [`docs/`](docs/README.md) — project context index: architecture, routines, deployment,
  service reference, historical plan.

## Deploy scope

Only `swing-agent/` is deployed — the parent `swing-trading` repo (research history, full
`wiki/`, `scripts/`) is not part of the container image or the runtime. `src/` runs headless
on Postgres + config; it never reads a `.md` file — Claude Code reads/writes prose through MCP.
