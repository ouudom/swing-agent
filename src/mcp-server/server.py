#!/usr/bin/env python3
"""
server.py — legacy REST/JSON transport over the auto-swing tool surface.

Kept for curl-based routines and back-compat. Tool logic lives in `tools.py`; the
native MCP transport is `server_mcp.py`. Both import the same `TOOLS` dict, so the
two transports never drift.
"""
from __future__ import annotations

import json
import os
import sys
import traceback
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

SRC_ROOT = Path(__file__).resolve().parents[1]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

sys.path.insert(0, str(Path(__file__).resolve().parent))  # sibling `tools` module
from tools import TOOLS, utc_now  # noqa: E402


HOST = os.getenv("MCP_HOST", "0.0.0.0")
PORT = int(os.getenv("MCP_PORT", "8765"))
TOKEN = os.getenv("MCP_AUTH_TOKEN", "dev-token")


class Handler(BaseHTTPRequestHandler):
    server_version = "auto-swing-mcp/0.1"

    def log_message(self, fmt, *args):
        print(f"{utc_now()} {self.client_address[0]} {fmt % args}", flush=True)

    def _json(self, status: int, payload):
        body = json.dumps(payload, default=str, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _authorized(self) -> bool:
        header = self.headers.get("Authorization", "")
        return header == f"Bearer {TOKEN}"

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/health":
            return self._json(HTTPStatus.OK, {"ok": True, "time": utc_now()})
        if not self._authorized():
            return self._json(HTTPStatus.UNAUTHORIZED, {"ok": False, "error": "unauthorized"})
        if path in {"/tools", "/mcp/tools"}:
            return self._json(HTTPStatus.OK, {"ok": True, "tools": sorted(TOOLS)})
        return self._json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "not found"})

    def do_POST(self):
        path = urlparse(self.path).path
        if not self._authorized():
            return self._json(HTTPStatus.UNAUTHORIZED, {"ok": False, "error": "unauthorized"})
        try:
            raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            payload = json.loads(raw or b"{}")
            if path in {"/call", "/mcp/call"}:
                tool = payload.get("tool")
                args = payload.get("args") or {}
            elif path.startswith("/tools/"):
                tool = path.rsplit("/", 1)[-1]
                args = payload
            else:
                return self._json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "not found"})
            if tool not in TOOLS:
                raise ValueError(f"unknown tool: {tool}")
            if not isinstance(args, dict):
                raise ValueError("args must be an object")
            result = TOOLS[tool](**args)
            return self._json(HTTPStatus.OK, {"ok": True, "tool": tool, "result": result})
        except Exception as exc:
            return self._json(
                HTTPStatus.BAD_REQUEST,
                {
                    "ok": False,
                    "error": str(exc),
                    "type": exc.__class__.__name__,
                    "trace": traceback.format_exc(limit=3),
                },
            )


def main() -> int:
    print(f"auto-swing REST server starting on {HOST}:{PORT}", flush=True)
    if TOKEN == "dev-token":
        print("WARNING: MCP_AUTH_TOKEN not set; using dev-token", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
