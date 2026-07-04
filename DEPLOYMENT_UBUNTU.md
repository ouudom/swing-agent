# swing-agent Ubuntu Deployment Guide

Target: Ubuntu server running Docker Compose from the `swing-agent/` repo/folder only. Do **not**
deploy the parent `swing-trading` repo. The deterministic engine is vendored under
`src/engine/scripts/`.

## 1. Server Prep

```bash
sudo apt update
sudo apt install -y ca-certificates curl git ufw
```

Install Docker Engine + Compose plugin:

```bash
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo tee /etc/apt/keyrings/docker.asc >/dev/null
sudo chmod a+r /etc/apt/keyrings/docker.asc
. /etc/os-release
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $VERSION_CODENAME stable" | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker "$USER"
```

Log out/in once so Docker group applies.

Firewall baseline:

```bash
sudo ufw allow OpenSSH
sudo ufw enable
```

Do not expose Postgres publicly. Compose binds it to `127.0.0.1`.

## 2. Clone Repo

```bash
mkdir -p ~/apps
cd ~/apps
git clone <SWING_AGENT_REPO_URL> swing-agent
cd swing-agent
```

Use the branch carrying the standalone `swing-agent` folder as repo root.

## 3. Configure Env

```bash
cp src/.env.example src/.env
nano src/.env
```

Set:

```bash
POSTGRES_PASSWORD=<strong-password>
TWELVE_DATA_KEY=<key>
FRED_KEY=<key>
MCP_AUTH_TOKEN=<future-token>
TELEGRAM_BOT_TOKEN=<optional>
TELEGRAM_CHAT_ID=<optional>
```

Keep:

```bash
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
MCP_PORT=8765
```

The pipeline and MCP containers override `POSTGRES_HOST=postgres` internally. Compose binds Postgres
and MCP to `127.0.0.1` on the host.

## 4. Start Postgres

```bash
docker compose -f src/docker-compose.yml up -d postgres
docker compose -f src/docker-compose.yml ps
```

Wait until Postgres is healthy.

## 5. Backfill From SQLite

Run from host after placing the migration SQLite file at `data/database/index.db`, or restore from a
Postgres dump instead.

```bash
docker compose -f src/docker-compose.yml run --rm pipeline \
  python src/engine/scripts/ops/backfill_sqlite_to_postgres.py
docker compose -f src/docker-compose.yml run --rm pipeline \
  python src/engine/scripts/ops/diff_sqlite_postgres.py
```

Expected: every table prints `OK`. `lost_and_found` is intentionally excluded.

For existing volumes after upgrades:

```bash
docker compose -f src/docker-compose.yml exec -T pipeline \
  python src/engine/scripts/ops/apply_postgres_migrations.py
```

## 6. Start Pipeline + MCP

Two MCP transports front the **same** tool surface (`src/mcp-server/tools.py`):

- `mcp-server` (port 8765) — legacy REST/JSON, for `curl` routines.
- `mcp-native` (port 8766) — native Model Context Protocol (Streamable HTTP), for
  registering directly in Claude Code / any MCP client.

Start all three long-running services:

```bash
docker compose -f src/docker-compose.yml up -d pipeline mcp-server mcp-native
docker compose -f src/docker-compose.yml ps
```

Run ledger:

```bash
tail -f src/logs/pipeline_run.jsonl
```

REST smoke (port 8765):

```bash
curl http://127.0.0.1:8765/health
curl -H "Authorization: Bearer $MCP_AUTH_TOKEN" http://127.0.0.1:8765/tools
curl -H "Authorization: Bearer $MCP_AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tool":"sql_query","args":{"sql":"select count(*) as n from zone_ledger"}}' \
  http://127.0.0.1:8765/call
```

Native MCP smoke (port 8766) — `/health` is open, `/mcp` requires the Bearer token:

```bash
curl http://127.0.0.1:8766/health
# unauthenticated MCP call must 401:
curl -s -o /dev/null -w "%{http_code}\n" -X POST http://127.0.0.1:8766/mcp
# MCP initialize handshake (expect a text/event-stream `initialize` result):
curl -s -X POST http://127.0.0.1:8766/mcp \
  -H "Authorization: Bearer $MCP_AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"probe","version":"0"}}}'
```

Register the native server with Claude Code (laptop or cloud routine host):

```bash
claude mcp add --transport http swing-agent \
  http://<host-or-tunnel>:8766/mcp \
  --header "Authorization: Bearer $MCP_AUTH_TOKEN"
```

All 15 tools (`get_brief`, `get_zone_context`, `sql_query`, `run_gate`, `run_replay`, `run_backtest`,
`run_calibration`, `get_news`, `get_econ`, `get_calibration`, `compute_indicators`,
`publish_zone`, `write_verdict`, `queue_notification`, `update_checkpoint`) then appear
in Claude Code with schemas auto-derived from the Python signatures.

Do not expose either MCP port publicly without a tunnel/VPN and a strong `MCP_AUTH_TOKEN`.
Compose binds both to `127.0.0.1` on the host by default.

Structured write smoke should use a test zone only, then remove it. Production writes happen through
`publish_zone` and `write_verdict`, followed by markdown commit/push from Claude Code.

## 7. One-Shot Jobs

Use one-shot mode before trusting the long-running scheduler:

```bash
docker compose -f src/docker-compose.yml run --rm pipeline \
  python src/pipeline/scheduler.py --once brief_refresh --instrument eurusd

docker compose -f src/docker-compose.yml run --rm pipeline \
  python src/pipeline/scheduler.py --once trade_outcome

docker compose -f src/docker-compose.yml run --rm pipeline \
  python src/pipeline/scheduler.py --once reconcile

docker compose -f src/docker-compose.yml run --rm pipeline \
  python src/pipeline/scheduler.py --once send_notifications
```

Routine contract lives in `ROUTINES.md`.

## 8. Backups

Manual backup:

```bash
cd src
./engine/scripts/ops/backup_postgres.sh
```

Cron example:

```bash
crontab -e
```

```cron
0 23 * * 1-5 cd ~/apps/swing-agent/src && ./engine/scripts/ops/backup_postgres.sh >> backups/backup.log 2>&1
```

## 9. Update Deploy

```bash
cd ~/apps/swing-agent
git pull --ff-only
docker compose -f src/docker-compose.yml build pipeline mcp-server mcp-native
docker compose -f src/docker-compose.yml up -d
```

## 10. Rollback

```bash
docker compose -f src/docker-compose.yml stop pipeline mcp-server mcp-native
```

SQLite path remains default when `SWING_DB_BACKEND` is unset, so manual legacy scripts still work.
