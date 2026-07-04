#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "engine" / "scripts"))

import db  # noqa: E402


def call(url: str, token: str, tool: str, args: dict):
    payload = json.dumps({"tool": tool, "args": args}).encode()
    req = urllib.request.Request(
        f"{url.rstrip('/')}/call",
        data=payload,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        raise RuntimeError(exc.read().decode()) from exc
    if not body.get("ok"):
        raise RuntimeError(body)
    return body["result"]


def run_local(args: list[str], timeout: int = 300):
    return subprocess.run(
        ["bash", "src/engine/scripts/pyrun.sh", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def latest_ohlc_local(instrument: str):
    out = {}
    for tf in ["15min", "1day", "1h", "4h"]:
        out[tf] = db.last_ohlc_dt(instrument, tf)
    return out


def norm_dt(value) -> str:
    text = str(value).replace("T", " ").removesuffix("+00:00")
    if len(text) == 10:
        return text + " 00:00:00"
    return text


def indicators_local(instrument: str, tf: str):
    frame = db.read_ohlc(instrument, tf).tail(200)
    for col in ["open", "high", "low", "close", "volume"]:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    closes = frame["close"].tolist()
    highs = frame["high"].tolist()
    lows = frame["low"].tolist()
    trs = [
        max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1]))
        for i in range(1, len(closes))
    ]
    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gains = [max(d, 0.0) for d in deltas[-14:]]
    losses = [abs(min(d, 0.0)) for d in deltas[-14:]]
    avg_loss = sum(losses) / 14
    rs = (sum(gains) / 14) / avg_loss if avg_loss else None
    return {
        "latest_datetime": str(frame["datetime"].iloc[-1]),
        "latest_close": closes[-1],
        "atr14": sum(trs[-14:]) / 14,
        "rsi14": 100.0 if rs is None else 100 - (100 / (1 + rs)),
        "sma20": sum(closes[-20:]) / 20,
        "sma50": sum(closes[-50:]) / 50,
    }


def close(a, b, tol: float = 1e-12) -> bool:
    if a is None or b is None:
        return a == b
    return math.isclose(float(a), float(b), rel_tol=tol, abs_tol=tol)


def assert_equal(label: str, left, right):
    if left != right:
        raise AssertionError(f"{label}: {left!r} != {right!r}")
    print(f"OK {label}: {left}")


def assert_close(label: str, left, right):
    if not close(left, right):
        raise AssertionError(f"{label}: {left!r} != {right!r}")
    print(f"OK {label}: {left}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Phase 2.4 MCP parity check.")
    parser.add_argument("--url", default=os.getenv("MCP_URL", "http://127.0.0.1:8765"))
    parser.add_argument("--token", default=os.getenv("MCP_AUTH_TOKEN", "dev-token"))
    parser.add_argument("--instrument", default="eurusd")
    parser.add_argument("--date", default="2026-07-04")
    args = parser.parse_args(argv)

    instrument = args.instrument.lower()

    brief = call(args.url, args.token, "get_brief", {"instrument": instrument, "kind": "validate"})
    assert_equal("brief instrument", brief["instrument"], instrument)
    local_latest = latest_ohlc_local(instrument)
    mcp_latest = {row["tf"]: norm_dt(row["latest_dt"]) for row in brief["latest_ohlc"]["rows"]}
    for tf, local_dt in local_latest.items():
        assert_equal(f"latest {tf}", mcp_latest[tf], norm_dt(local_dt))

    assert_equal("zone count", brief["zones"]["row_count"], len(db.read_slice("zone_ledger", {"instrument": instrument}, ["zone_id"])))
    assert_equal(
        "trade_outcome count",
        brief["trade_outcome"]["row_count"],
        len(db.read_slice("trade_outcome", {"instrument": instrument}, ["zone_id"])),
    )

    mcp_ind = call(args.url, args.token, "compute_indicators", {"instrument": instrument, "tf": "1h"})
    local_ind = indicators_local(instrument, "1h")
    assert_equal("indicator latest", norm_dt(mcp_ind["latest_datetime"]), norm_dt(local_ind["latest_datetime"]))
    for key in ["latest_close", "atr14", "rsi14", "sma20", "sma50"]:
        assert_close(f"indicator {key}", mcp_ind[key], local_ind[key])

    gate_args = ["--instrument", instrument, "--date", args.date, "--days", "2"]
    mcp_gate = call(args.url, args.token, "run_gate", {"name": "econ_calendar", "args": gate_args})
    local_gate = run_local(["src/engine/scripts/check_econ_calendar.py", *gate_args], timeout=120)
    assert_equal("econ gate returncode", mcp_gate["returncode"], local_gate.returncode)
    assert_equal("econ gate stdout", mcp_gate["stdout_tail"], local_gate.stdout)

    bt_args = ["--instrument", instrument, "--tf", "H1"]
    mcp_bt = call(args.url, args.token, "run_backtest", {"name": "e0_variants", "args": bt_args})
    local_bt = run_local(["src/engine/scripts/backtest_e0_variants.py", *bt_args], timeout=600)
    assert_equal("backtest returncode", mcp_bt["returncode"], local_bt.returncode)
    assert_equal("backtest stdout", mcp_bt["stdout_tail"], local_bt.stdout[-8000:])

    offset_args = ["--wfill", "12"]
    mcp_offset = call(args.url, args.token, "run_backtest", {"name": "offset_session", "args": offset_args})
    local_offset = run_local(["src/engine/scripts/backtest_offset_session.py", *offset_args], timeout=600)
    assert_equal("offset backtest returncode", mcp_offset["returncode"], local_offset.returncode)
    assert_equal("offset backtest stdout", mcp_offset["stdout_tail"], local_offset.stdout[-8000:])

    print("MCP parity PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
