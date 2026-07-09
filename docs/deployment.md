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
cp .env.example .env
nano .env
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
```

The pipeline and MCP containers override `POSTGRES_HOST=postgres` internally. Compose binds Postgres
and MCP to `127.0.0.1` on the host.

## 4. Start Postgres

```bash
docker compose up -d postgres
docker compose ps
```

Wait until Postgres is healthy.

## 5. Backfill From SQLite

Run from host after placing the migration SQLite file at `data/database/index.db`, or restore from a
Postgres dump instead.

```bash
docker compose run --rm pipeline \
  python src/engine/scripts/ops/backfill_sqlite_to_postgres.py
docker compose run --rm pipeline \
  python src/engine/scripts/ops/diff_sqlite_postgres.py
```

Expected: every table prints `OK`. `lost_and_found` is intentionally excluded.

For existing volumes after upgrades:

```bash
docker compose exec -T pipeline \
  python src/engine/scripts/ops/apply_postgres_migrations.py
```

## 6. Start Pipeline + MCP

`mcp-native` (port 8766) fronts the tool surface (`src/mcp-server/tools.py`) as native
Model Context Protocol over Streamable HTTP, for registering directly in Claude Code /
any MCP client.

A third service, `dashboard` (port 8888), is an optional read-only monitoring frontend
(open zones, system P&L replay, validations, pipeline/routine health) — bound `127.0.0.1`,
view over an SSH tunnel.

Start all long-running services:

```bash
docker compose up -d pipeline mcp-native dashboard
docker compose ps
```

Run ledger:

```bash
tail -f src/logs/pipeline_run.jsonl
```

Dashboard smoke (port 8888) — then tunnel `ssh -L 8888:127.0.0.1:8888 <host>` and open
`http://localhost:8888`:

```bash
curl http://127.0.0.1:8888/health
curl http://127.0.0.1:8888/api/health
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

Some connector UIs (e.g. claude.ai's generic "Add custom connector" dialog) only take a URL —
no custom-header field. For those, pass the token as a query param instead (checked as a
fallback in `BearerAuth`, `src/mcp-server/server_mcp.py`):

```
https://<host-or-tunnel>/mcp?token=<MCP_AUTH_TOKEN>
```

All 21 tools (`get_brief`, `get_zone_context`, `sql_query`, `run_gate`, `run_replay`, `run_backtest`,
`run_calibration`, `get_news`, `get_econ`, `get_calibration`, `compute_indicators`,
`get_doc`, `list_docs`, `write_doc`, `get_context_pack`,
`publish_zone`, `write_verdict`, `write_trade_log`, `snapshot_features`, `queue_notification`,
`update_checkpoint`) then appear in Claude Code with schemas auto-derived from the Python signatures.

Do not expose the MCP port publicly without a tunnel/VPN and a strong `MCP_AUTH_TOKEN`.
Compose binds it to `127.0.0.1` on the host by default.

Structured write smoke should use a test zone only, then remove it. Production writes happen through
`publish_zone` and `write_verdict`, followed by markdown commit/push from Claude Code.

## 6b. Expose MCP for a Cloud Scheduled Agent (Cloudflare Tunnel + nginx)

Only needed if the hourly `/validate` routine runs as a cloud-hosted scheduled agent instead of a
local cron — the cloud host can't reach `127.0.0.1:8766` on your homeserver directly. Requires: a
domain on Cloudflare, `cloudflared` installed on the homeserver, nginx already reverse-proxying
other services there.

**1. Generate a strong `MCP_AUTH_TOKEN`** (if still `dev-token`) and restart:

```bash
openssl rand -hex 32   # put the output in .env as MCP_AUTH_TOKEN=...
docker compose up -d mcp-native
```

**2. nginx vhost** (`/etc/nginx/sites-available/mcp.yourdomain.com`) — proxies to the
container's loopback-only port, no public TLS cert needed since Cloudflare Tunnel terminates TLS
at the edge:

```nginx
server {
    listen 127.0.0.1:8080;   # cloudflared's local origin — not directly internet-reachable
    server_name mcp.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8766;
        proxy_http_version 1.1;
        proxy_set_header Connection "";       # required for the MCP streaming response
        proxy_buffering off;
        proxy_read_timeout 300s;
    }
}
```

```bash
ln -s /etc/nginx/sites-available/mcp.yourdomain.com /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

**3. Cloudflare Tunnel** — point the public hostname at nginx's origin (not straight at 8766, so
nginx stays the single choke point for every exposed service):

```bash
cloudflared tunnel login
cloudflared tunnel create swing-agent-mcp
cloudflared tunnel route dns swing-agent-mcp mcp.yourdomain.com
```

`~/.cloudflared/config.yml`:

```yaml
tunnel: swing-agent-mcp
credentials-file: /root/.cloudflared/<tunnel-id>.json
ingress:
  - hostname: mcp.yourdomain.com
    service: http://127.0.0.1:8080
  - service: http_status:404
```

```bash
cloudflared tunnel run swing-agent-mcp
# or as a service: cloudflared service install && systemctl enable --now cloudflared
```

**4. Smoke test from outside the LAN**:

```bash
curl https://mcp.yourdomain.com/health
curl -s -o /dev/null -w "%{http_code}\n" -X POST https://mcp.yourdomain.com/mcp   # 401 unauthed
```

**5. Register from the cloud agent side**:

```bash
claude mcp add --transport http swing-agent https://mcp.yourdomain.com/mcp \
  --header "Authorization: Bearer $MCP_AUTH_TOKEN"
```

The Bearer check happens in `server_mcp.py` regardless of transport — the tunnel adds network-path
protection (no direct port exposure, Cloudflare's edge DDoS/WAF) on top, not instead of it. Rotate
`MCP_AUTH_TOKEN` if it ever leaks into a log or shared screen.

## 7. One-Shot Jobs

Use one-shot mode before trusting the long-running scheduler:

```bash
docker compose run --rm pipeline \
  python src/pipeline/scheduler.py --once brief_refresh --instrument eurusd

docker compose run --rm pipeline \
  python src/pipeline/scheduler.py --once trade_outcome

docker compose run --rm pipeline \
  python src/pipeline/scheduler.py --once reconcile

docker compose run --rm pipeline \
  python src/pipeline/scheduler.py --once send_notifications
```

Routine contract lives in `docs/routines.md`.

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
docker compose build pipeline mcp-native
docker compose up -d
```

## 10. Rollback

```bash
docker compose stop pipeline mcp-native
```

SQLite path remains default when `SWING_DB_BACKEND` is unset, so manual legacy scripts still work.
