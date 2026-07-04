#!/usr/bin/env python3
"""
server_mcp.py — native Model Context Protocol transport (Streamable HTTP).

Wraps the exact same `TOOLS` callables as the REST server (`server.py`). FastMCP
auto-derives each tool's JSON input schema from the function signature + type hints,
so Claude Code (and any MCP client) sees a fully-typed toolset with no hand-written
schemas.

Register with Claude Code:

    claude mcp add --transport http auto-swing \
      http://<host>:${MCP_NATIVE_PORT:-8766}/mcp \
      --header "Authorization: Bearer $MCP_AUTH_TOKEN"

Auth: a Bearer-token ASGI middleware guards every path except /health. Set a strong
MCP_AUTH_TOKEN in .env; never expose this port publicly without a tunnel/VPN.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[1]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))  # sibling `tools` module

from tools import TOOLS  # noqa: E402

from mcp.server.fastmcp import FastMCP  # noqa: E402
from starlette.middleware.base import BaseHTTPMiddleware  # noqa: E402
from starlette.requests import Request  # noqa: E402
from starlette.responses import JSONResponse  # noqa: E402

HOST = os.getenv("MCP_HOST", "0.0.0.0")
PORT = int(os.getenv("MCP_NATIVE_PORT", "8766"))
TOKEN = os.getenv("MCP_AUTH_TOKEN", "dev-token")

mcp = FastMCP("auto-swing", host=HOST, port=PORT)

# Register every REST tool under the same name; schema is inferred from type hints.
for _name, _fn in TOOLS.items():
    mcp.tool(name=_name)(_fn)


class BearerAuth(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/health":
            return JSONResponse({"ok": True})
        if request.headers.get("Authorization") != f"Bearer {TOKEN}":
            return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
        return await call_next(request)


def main() -> int:
    print(f"auto-swing NATIVE MCP server starting on {HOST}:{PORT} (path /mcp)", flush=True)
    if TOKEN == "dev-token":
        print("WARNING: MCP_AUTH_TOKEN not set; using dev-token", flush=True)

    import uvicorn

    app = mcp.streamable_http_app()  # ASGI app incl. the MCP session-manager lifespan
    app.add_middleware(BearerAuth)
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
