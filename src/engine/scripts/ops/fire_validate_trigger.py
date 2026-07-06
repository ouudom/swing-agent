"""
fire_validate_trigger — cheap Python gate in front of the Claude /validate routine.

Firing /validate on every H1 close for all 11 instruments spends Claude tokens on zones
price is nowhere near. This gate runs the SAME deterministic checks the replay uses
(E0 detection, programmatic Entry Confluence, V1/V1b invalidation) on stored OHLC — no
Claude — and only POSTs the routine trigger when a live zone is actually actionable RIGHT
NOW. Everything here is pure Python; the model is woken only past the gate.

Fire reasons (any live zone of the instrument matching → fire once for the instrument):
  ENTRY — price touched the zone on the latest H1 bar, an E0 fired toward the zone
          direction (1H pin/engulf or RSI-reclaim), AND the programmatic EC ≥ EC_GATE.
          EC_GATE (4.0) sits BELOW the real 5.0 ORDER_LIMIT floor on purpose: the
          scorer is a provisional approximation (see entry_confluence.py fidelity
          caveat), so we gate loose and let Claude make the real call.
  INVAL — a hard block fired on a still-live zone: V1 (a D1 close beyond the zone's far
          edge) or V1b (two consecutive H4 closes beyond zone+ATR buffer). /validate is
          woken to formally INVALIDATE it and write the trade_log row.

Skips (no fire, no tokens):
  - no new H1 bar since the last fire for this instrument (dedup via `trigger_state`) —
    this also naturally silences weekends/holidays, when no new bar lands;
  - the instrument has no OPEN zone in `zone_ledger`, or every one of its zones is already
    RUNNING/terminal in `trade_log` (a live trade → the fill/close checker owns it, not
    /validate) or already INVALIDATED.

Default dispatch runs local 9router validate first. 9router has no MCP; the runner builds
local context and owns DB writes through the same pure tool functions as MCP. If that
fails, this script falls back to the Anthropic routine `.../fire` endpoint. The instrument
and reason ride in the JSON body so the cloud routine validates just that instrument.

Env:
  CLAUDE_TRIGGER_URL   full fire URL, e.g.
                       https://api.anthropic.com/v1/claude_code/routines/<id>/fire
  CLAUDE_TRIGGER_TOKEN bearer/API token for the trigger (falls back to ANTHROPIC_API_KEY)
  CLAUDE_TRIGGER_AUTH_HEADER  header name (default 'x-api-key'; set 'Authorization' if the
                       routine expects 'Bearer <token>')
  VALIDATE_PRIMARY     9router (default) or cloud
  NINEROUTER_API_KEY / NINEROUTER_MODEL / NINEROUTER_BASE_URL / NINEROUTER_TIMEOUT_SEC

Usage:
  bash scripts/pyrun.sh scripts/ops/fire_validate_trigger.py --instrument xauusd
  bash scripts/pyrun.sh scripts/ops/fire_validate_trigger.py            # all 11
  bash scripts/pyrun.sh scripts/ops/fire_validate_trigger.py --instrument xauusd --dry-run
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]          # .../src/engine
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "replay"))

import db  # noqa: E402
import entry_confluence as ec  # noqa: E402
from zone_ledger import load_ledger  # noqa: E402
from zone_outcomes import week_window, atr14_before, load_tf, min_bar_range  # noqa: E402
from trade_outcome import e0_triggers, _v1b_fired, v1b_buffer  # noqa: E402

EC_GATE = 4.0
INSTRUMENTS = [
    "xauusd", "eurusd", "gbpusd", "eurgbp", "audusd", "nzdusd",
    "usdcad", "usdchf", "usdjpy", "eurjpy", "gbpjpy",
]
# a trade_log status here means the zone is live/closed — /validate must NOT be woken for it.
LOCKED_TRADE_STATUSES = {"RUNNING", "WIN", "LOSS", "BREAKEVEN", "EXPIRED"}
TRIGGER_TABLE = "trigger_state"
RUNNER = Path(__file__).with_name("run_validate_9router.py")
LOG_PATH = Path(os.getenv("VALIDATE_ROUTINE_LOG", ROOT.parent / "logs" / "validate_routine.jsonl"))


def log_event(event: str, **fields) -> None:
    row = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "component": "fire_validate_trigger",
        "event": event,
        **fields,
    }
    print(f"{row['ts']} validate-trigger {event} " + " ".join(f"{k}={v}" for k, v in fields.items()), flush=True)
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, sort_keys=True, default=str) + "\n")
    except Exception:
        pass


def _parse_dt(s):
    if s in (None, "", "nan"):
        return None
    t = pd.Timestamp(str(s))
    return t.tz_convert("UTC").tz_localize(None) if t.tz is not None else t


def _last_fired(inst: str):
    df = db.read_slice(TRIGGER_TABLE, {"instrument": inst},
                       ["instrument", "last_fired_h1", "last_fire_reason", "updated_utc"])
    if df.empty:
        return None
    return _parse_dt(df.iloc[0]["last_fired_h1"])


def _mark_fired(inst: str, h1_dt: pd.Timestamp, reason: str):
    row = pd.DataFrame([{
        "instrument": inst,
        "last_fired_h1": str(h1_dt),
        "last_fire_reason": reason,
        "updated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }])
    db.sync_slice(TRIGGER_TABLE, {"instrument": inst}, row)


def _live_zones(inst: str, ledger: pd.DataFrame) -> pd.DataFrame:
    """Zones still worth validating: OPEN in the ledger and not already live/closed/killed."""
    z = ledger[(ledger["instrument"] == inst) & (ledger["status"] == "OPEN")].copy()
    if z.empty:
        return z
    tl = db.read_slice("trade_log", {"instrument": inst}, ["zone_id", "status"])
    locked = set(tl[tl["status"].isin(LOCKED_TRADE_STATUSES | {"INVALIDATED"})]["zone_id"]) if not tl.empty else set()
    return z[~z["zone_id"].isin(locked)]


def _zone_signal(z: pd.Series, h1, h4, d1, mbr: float, last_bar) -> str | None:
    """Return 'ENTRY' | 'INVAL' | None for one zone, judged at the latest H1 bar."""
    top, bot = float(z["zone_top"]), float(z["zone_bottom"])
    is_long = z["direction"] == "LONG"
    start, end = week_window(z["week"])

    # INVAL — hard block on a still-live zone (checked across the zone's live week).
    sign = 1 if is_long else -1
    dwin = d1[(d1["datetime"] >= start) & (d1["datetime"] < end)]
    v1 = (dwin["close"] > top).any() if sign < 0 else (dwin["close"] < bot).any()
    v1b = _v1b_fired(h4, start, end, top, bot, sign, v1b_buffer(z["instrument"], h4, last_bar["datetime"]))
    if bool(v1) or bool(v1b):
        return "INVAL"

    # ENTRY — latest H1 bar touches the zone, E0 fired toward it, programmatic EC clears the gate.
    last = h1.iloc[-1]
    touched = (last["low"] <= top) and (last["high"] >= bot)
    if not touched:
        return None
    bull, bear = e0_triggers(h1)
    if not (bull[-1] if is_long else bear[-1]):
        return None
    sig_time = last["datetime"]
    dpre = d1[(d1["datetime"] >= start) & (d1["datetime"] <= sig_time)]
    structure_intact = not (bool((dpre["close"] > top).any()) if sign < 0 else bool((dpre["close"] < bot).any()))
    ec_score, _ = ec.score(z["instrument"], is_long, sig_time, top, bot, h1, h4, d1,
                           e0_present=True, structure_intact=structure_intact)
    return "ENTRY" if ec_score >= EC_GATE else None


def evaluate(inst: str) -> dict:
    """Decide whether to fire for one instrument. Returns a decision dict (no I/O side effects
    beyond OHLC reads)."""
    ledger = load_ledger()
    zones = _live_zones(inst, ledger)
    out = {"instrument": inst, "fire": False, "reason": None, "zone_id": None, "h1_dt": None, "skip": None}
    if zones.empty:
        out["skip"] = "no live zone"
        return out

    try:
        h1, h4, d1, mbr = load_tf(inst, "1h"), load_tf(inst, "4h"), load_tf(inst, "1day"), min_bar_range(inst)
    except FileNotFoundError:
        out["skip"] = "no OHLC"
        return out
    if h1.empty:
        out["skip"] = "no H1 bars"
        return out

    last_bar = h1.iloc[-1]
    h1_dt = last_bar["datetime"]
    out["h1_dt"] = str(h1_dt)
    if _last_fired(inst) is not None and h1_dt <= _last_fired(inst):
        out["skip"] = "no new H1 bar since last fire"
        return out

    # INVAL beats ENTRY if both present (kill first).
    signals = {}
    for _, z in zones.iterrows():
        sig = _zone_signal(z, h1, h4, d1, mbr, last_bar)
        if sig:
            signals[z["zone_id"]] = sig
    if not signals:
        out["skip"] = "no zone actionable this bar"
        return out
    inval = next((zid for zid, s in signals.items() if s == "INVAL"), None)
    zone_id = inval or next(iter(signals))
    out.update({"fire": True, "reason": signals[zone_id], "zone_id": zone_id})
    return out


def _fire_cloud(inst: str, reason: str, zone_id: str) -> str:
    url = os.getenv("CLAUDE_TRIGGER_URL")
    if not url:
        raise SystemExit("CLAUDE_TRIGGER_URL not set — cannot fire the routine trigger")
    token = os.getenv("CLAUDE_TRIGGER_TOKEN") or os.getenv("ANTHROPIC_API_KEY")
    if not token:
        raise SystemExit("CLAUDE_TRIGGER_TOKEN / ANTHROPIC_API_KEY not set — cannot authenticate the trigger")
    header = os.getenv("CLAUDE_TRIGGER_AUTH_HEADER", "x-api-key")
    auth_value = f"Bearer {token}" if header.lower() == "authorization" else token
    body = json.dumps({"instrument": inst, "reason": reason, "zone_id": zone_id,
                       "fired_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}).encode()
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header(header, auth_value)
    req.add_header("anthropic-version", os.getenv("ANTHROPIC_VERSION", "2023-06-01"))
    log_event("cloud_fire_start", instrument=inst, reason=reason, zone_id=zone_id)
    with urllib.request.urlopen(req, timeout=30) as resp:
        if resp.status >= 300:
            raise RuntimeError(f"trigger POST {resp.status}: {resp.read()[:400]!r}")
    log_event("cloud_fire_success", instrument=inst, reason=reason, zone_id=zone_id)
    return "cloud"


def _fire_9router(inst: str, reason: str, zone_id: str, h1_dt: str | None) -> str:
    cmd = [
        sys.executable,
        str(RUNNER),
        "--instrument", inst,
        "--reason", reason,
        "--zone-id", zone_id,
    ]
    if h1_dt:
        cmd += ["--h1-dt", h1_dt]
    log_event("9router_start", instrument=inst, reason=reason, zone_id=zone_id, h1_dt=h1_dt)
    proc = subprocess.run(cmd, cwd=ROOT.parent.parent, text=True, capture_output=True, timeout=None)
    if proc.returncode != 0:
        msg = (proc.stderr or proc.stdout or "").strip()
        log_event("9router_failed", instrument=inst, reason=reason, zone_id=zone_id, returncode=proc.returncode)
        raise RuntimeError(f"9router validate failed: {msg[-1200:]}")
    log_event("9router_success", instrument=inst, reason=reason, zone_id=zone_id)
    return "9router"


def fire(inst: str, reason: str, zone_id: str, h1_dt: str | None = None) -> str:
    primary = os.getenv("VALIDATE_PRIMARY", "9router").lower()
    if primary == "cloud":
        return _fire_cloud(inst, reason, zone_id)
    try:
        return _fire_9router(inst, reason, zone_id, h1_dt)
    except Exception as exc:  # noqa: BLE001 — cloud fallback owns live recovery.
        log_event("fallback_to_cloud", instrument=inst, reason=reason, zone_id=zone_id, error=str(exc))
        print(f"{inst:<8} 9router failed; falling back to cloud — {exc}")
        return _fire_cloud(inst, reason, zone_id)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--instrument", choices=INSTRUMENTS, help="one instrument (default: all 11)")
    ap.add_argument("--dry-run", action="store_true", help="evaluate + print, never POST or mark fired")
    args = ap.parse_args(argv)

    targets = [args.instrument] if args.instrument else INSTRUMENTS
    fired = 0
    for inst in targets:
        d = evaluate(inst)
        if not d["fire"]:
            log_event("skip", instrument=inst, skip=d["skip"])
            print(f"{inst:<8} skip — {d['skip']}")
            continue
        tag = f"{inst:<8} FIRE {d['reason']} ({d['zone_id']}) @ H1 {d['h1_dt']}"
        log_event("fire_candidate", instrument=inst, reason=d["reason"], zone_id=d["zone_id"], h1_dt=d["h1_dt"])
        if args.dry_run:
            log_event("dry_run_candidate", instrument=inst, reason=d["reason"], zone_id=d["zone_id"], h1_dt=d["h1_dt"])
            print(tag + "  [dry-run]")
            continue
        try:
            route = fire(inst, d["reason"], d["zone_id"], d["h1_dt"])
            _mark_fired(inst, _parse_dt(d["h1_dt"]), d["reason"])
            fired += 1
            log_event("fire_complete", instrument=inst, reason=d["reason"], zone_id=d["zone_id"], route=route)
            print(tag + f"  → {route}")
        except Exception as exc:  # noqa: BLE001  — fail-soft per instrument; one bad fire ≠ abort the sweep
            log_event("fire_failed", instrument=inst, reason=d["reason"], zone_id=d["zone_id"], error=str(exc))
            print(f"{inst:<8} FIRE FAILED — {exc}")
    print(f"\n{fired}/{len(targets)} instrument(s) fired")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
