"""
run_validate_9router — local /validate routine with 9router judgment.

9router has no MCP. This script builds local context from repo functions/DB, asks 9router
for strict JSON judgment, validates it, then performs DB writes through the same pure
tool functions used by the MCP server. If anything fails, caller should fall back to the
cloud routine.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]          # .../src/engine
SRC_ROOT = ROOT.parent                              # .../src
REPO_ROOT = SRC_ROOT.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "replay"))

from zone_ledger import load_ledger  # noqa: E402
from zone_outcomes import atr14_before, load_tf, min_bar_range  # noqa: E402
from trade_outcome import TP_R_FAR, TP_R_NEAR, session_mult  # noqa: E402


def _load_tools():
    path = SRC_ROOT / "mcp_server" / "tools.py"
    spec = importlib.util.spec_from_file_location("swing_mcp_tools", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load tools from {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


tools = _load_tools()
LOG_PATH = Path(os.getenv("VALIDATE_ROUTINE_LOG", SRC_ROOT / "logs" / "validate_routine.jsonl"))


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log_event(event: str, **fields) -> None:
    row = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "component": "run_validate_9router",
        "event": event,
        **fields,
    }
    print(f"{row['ts']} validate-9router {event} " + " ".join(f"{k}={v}" for k, v in fields.items()), flush=True)
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, sort_keys=True, default=str) + "\n")
    except Exception:
        pass


def _json_trim(obj, limit: int = 9000):
    text = json.dumps(obj, default=str, ensure_ascii=True)
    if len(text) <= limit:
        return obj
    return {"truncated": True, "chars": len(text), "preview": text[:limit]}


def _preview(text: str, limit: int = 1200) -> str:
    value = (text or "").replace("\n", "\\n")
    return value[:limit]


def _load_chat_response(raw: str) -> dict:
    text = (raw or "").strip()
    if not text:
        raise ValueError("9router returned empty response body")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Some OpenAI-compatible proxies accidentally stream SSE even when stream=false.
    data_objects = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("data:"):
            continue
        payload = line.removeprefix("data:").strip()
        if not payload or payload == "[DONE]":
            continue
        try:
            data_objects.append(json.loads(payload))
        except json.JSONDecodeError:
            continue
    if data_objects:
        content_parts = []
        last_obj = data_objects[-1]
        for obj in data_objects:
            choices = obj.get("choices") or []
            if not choices:
                continue
            choice = choices[0]
            message = choice.get("message") or {}
            if message.get("content"):
                return obj
            delta = choice.get("delta") or {}
            if delta.get("content"):
                content_parts.append(delta["content"])
        if content_parts:
            return {"choices": [{"message": {"content": "".join(content_parts)}}]}
        return last_obj
    raise ValueError(f"9router returned non-JSON response: {_preview(raw)}")


def _chat_content(data: dict) -> str:
    try:
        choice = data["choices"][0]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError(f"9router response missing choices: {_json_trim(data, 1200)}") from exc
    message = choice.get("message") or {}
    content = message.get("content")
    if content is None:
        delta = choice.get("delta") or {}
        content = delta.get("content")
    if content is None:
        raise ValueError(f"9router response missing message content: {_json_trim(choice, 1200)}")
    return str(content)


def _load_decision(content: str) -> dict:
    text = (content or "").strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start:end + 1])
        raise ValueError(f"9router content was not JSON: {_preview(content)}")


def _zone(zone_id: str) -> dict:
    rows = tools.query("SELECT * FROM zone_ledger WHERE zone_id = %s", (zone_id,), row_cap=1)["rows"]
    if not rows:
        raise ValueError(f"unknown zone_id: {zone_id}")
    return rows[0]


def _tp_r_for_zone(zone: dict) -> float:
    ledger = load_ledger()
    grp = ledger[(ledger["instrument"] == zone["instrument"]) & (ledger["week"] == zone["week"])]
    if grp.empty:
        return TP_R_NEAR
    h1 = load_tf(zone["instrument"], "1h")
    spot = float(h1["close"].iloc[-1]) if not h1.empty else None
    if spot is None:
        return TP_R_NEAR
    dists = {
        z["zone_id"]: abs((float(z["zone_top"]) + float(z["zone_bottom"])) / 2 - spot)
        for _, z in grp.iterrows()
    }
    nearest = min(dists, key=dists.get)
    return TP_R_NEAR if zone["zone_id"] == nearest else TP_R_FAR


def _trade_plan(zone: dict, h1_dt: str | None) -> dict:
    inst = zone["instrument"]
    h1, h4, d1, mbr = load_tf(inst, "1h"), load_tf(inst, "4h"), load_tf(inst, "1day"), min_bar_range(inst)
    if h1.empty:
        raise ValueError("no H1 bars for trade plan")
    bar = h1.iloc[-1]
    if h1_dt:
        target = pd.Timestamp(h1_dt)
        matched = h1[h1["datetime"] == target]
        if not matched.empty:
            bar = matched.iloc[-1]
    sig_time = bar["datetime"]
    d1_atr = atr14_before(d1, pd.Timestamp(sig_time.date()))
    h4_trade = h4[(h4["high"] - h4["low"]) >= mbr]
    h4_atr = atr14_before(h4_trade, sig_time)
    if d1_atr is None or h4_atr is None:
        raise ValueError("not enough ATR history for trade plan")

    is_long = zone["direction"] == "LONG"
    sign = 1 if is_long else -1
    sl = h4_atr if 0.5 * d1_atr < h4_atr else (0.5 * d1_atr + h4_atr) / 2
    anchor = float(bar["close"])
    offset = session_mult(sig_time) * sl
    limit_px = anchor - sign * offset
    tp_r = _tp_r_for_zone(zone)
    sl_price = limit_px - sign * sl
    tp_price = limit_px + sign * tp_r * sl
    return {
        "anchor": round(anchor, 6),
        "sl_dist": round(sl, 6),
        "offset": round(offset, 6),
        "limit_price": round(limit_px, 6),
        "sl_price": round(sl_price, 6),
        "tp_price": round(tp_price, 6),
        "tp_r": tp_r,
        "session_mult": session_mult(sig_time),
        "signal_time": str(sig_time),
    }


def build_context(instrument: str, reason: str, zone_id: str, h1_dt: str | None) -> dict:
    log_event("context_start", instrument=instrument, reason=reason, zone_id=zone_id, h1_dt=h1_dt)
    zone = _zone(zone_id)
    ctx = {
        "trigger": {"instrument": instrument, "reason": reason, "zone_id": zone_id, "h1_dt": h1_dt},
        "zone": zone,
        "trade_plan": _trade_plan(zone, h1_dt),
        "context_pack": _json_trim(tools.get_context_pack(instrument), 12000),
        "brief": _json_trim(tools.get_brief(instrument, kind="validate"), 12000),
        "indicators": {
            "h1": tools.compute_indicators(instrument, "1h", 200),
            "h4": tools.compute_indicators(instrument, "4h", 200),
            "d1": tools.compute_indicators(instrument, "1day", 200),
        },
        "calibration": _json_trim(tools.get_calibration(instrument), 9000),
        "news": tools.get_news(instrument, days=7, limit=10),
        "econ": tools.get_econ(days=7),
    }
    log_event(
        "context_built",
        instrument=instrument,
        reason=reason,
        zone_id=zone_id,
        trade_plan=ctx["trade_plan"],
    )
    return ctx


def _prompt(context: dict) -> list[dict]:
    schema = {
        "action": "ORDER_LIMIT | NO_TRADE | INVALIDATED | HARD_BLOCK | CANCEL_LIMIT",
        "entry_confluence": "number or null",
        "hard_block_flags": [
            "DAILY_ZONE_BREAK",
            "H4_BUFFER_BREAK",
            "CENTRAL_BANK_CARRY_RISK",
            "VETO_VIX",
            "VETO_ADX",
            "INTERVENTION",
            "EC_FLOOR",
        ],
        "reason": "short DB reason",
        "validation_body": "markdown validation note",
        "ec_breakdown": {"components": {}, "flags": []},
    }
    return [
        {
            "role": "system",
            "content": (
                "You are swing-agent /validate judgment. Return only valid JSON. "
                "Do not invent prices. Use supplied trade_plan prices if ORDER_LIMIT. "
                "ORDER_LIMIT needs entry_confluence >= 5.0 and no hard_block_flags. "
                "If trigger reason is INVAL, prefer INVALIDATED unless context clearly says cancel/no-trade."
            ),
        },
        {
            "role": "user",
            "content": json.dumps({"required_schema": schema, "context": context}, default=str, ensure_ascii=True),
        },
    ]


def call_9router(context: dict) -> dict:
    key = os.getenv("NINEROUTER_API_KEY")
    if not key:
        raise RuntimeError("NINEROUTER_API_KEY not set")
    model = os.getenv("NINEROUTER_MODEL", "openai/gpt-4.1-mini")
    base = os.getenv("NINEROUTER_BASE_URL", "https://api.9router.com/v1/chat/completions")
    timeout = int(os.getenv("NINEROUTER_TIMEOUT_SEC", "90"))
    trigger = context["trigger"]
    log_event(
        "llm_request_start",
        instrument=trigger["instrument"],
        reason=trigger["reason"],
        zone_id=trigger["zone_id"],
        model=model,
        timeout_s=timeout,
    )
    body = json.dumps({
        "model": model,
        "messages": _prompt(context),
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
    }).encode()
    req = urllib.request.Request(base, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {key}")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = getattr(resp, "status", None)
            content_type = resp.headers.get("Content-Type", "")
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        log_event(
            "llm_http_error",
            instrument=trigger["instrument"],
            reason=trigger["reason"],
            zone_id=trigger["zone_id"],
            model=model,
            status=exc.code,
            response_preview=_preview(raw),
        )
        raise

    log_event(
        "llm_response_received",
        instrument=trigger["instrument"],
        reason=trigger["reason"],
        zone_id=trigger["zone_id"],
        model=model,
        status=status,
        content_type=content_type,
        response_chars=len(raw),
    )
    try:
        data = _load_chat_response(raw)
    except Exception as exc:
        log_event(
            "llm_response_parse_failed",
            instrument=trigger["instrument"],
            reason=trigger["reason"],
            zone_id=trigger["zone_id"],
            model=model,
            status=status,
            content_type=content_type,
            response_chars=len(raw),
            response_preview=_preview(raw),
            error=str(exc),
        )
        raise
    content = _chat_content(data)
    decision = _load_decision(content)
    log_event(
        "llm_request_success",
        instrument=trigger["instrument"],
        reason=trigger["reason"],
        zone_id=trigger["zone_id"],
        model=model,
    )
    return decision


def validate_decision(decision: dict) -> dict:
    action = str(decision.get("action", "")).upper()
    if action not in {"ORDER_LIMIT", "NO_TRADE", "INVALIDATED", "HARD_BLOCK", "CANCEL_LIMIT"}:
        raise ValueError(f"invalid action: {action}")
    flags = decision.get("hard_block_flags") or []
    if isinstance(flags, str):
        flags = [x.strip().upper() for x in flags.split(",") if x.strip()]
    flags = [str(x).upper() for x in flags if str(x).strip()]
    ec = decision.get("entry_confluence")
    ec = None if ec in ("", None) else float(ec)
    if action == "ORDER_LIMIT" and flags:
        raise ValueError("ORDER_LIMIT rejected while hard_block_flags non-empty")
    if action == "ORDER_LIMIT" and (ec is None or ec < 5.0):
        raise ValueError("ORDER_LIMIT rejected: entry_confluence must be >= 5.0")
    body = str(decision.get("validation_body") or "").strip()
    if not body:
        raise ValueError("validation_body required")
    reason = str(decision.get("reason") or action).strip()
    normalized = {**decision, "action": action, "hard_block_flags": flags, "entry_confluence": ec, "reason": reason}
    log_event("decision_validated", action=action, entry_confluence=ec, hard_block_flags=flags)
    return normalized


def write_outputs(instrument: str, zone: dict, context: dict, decision: dict) -> dict:
    today = datetime.now(timezone.utc).date().isoformat()
    run_id = f"{today}-{zone['zone_id']}"
    action = decision["action"]
    prices = context["trade_plan"] if action == "ORDER_LIMIT" else {}
    log_event("write_start", instrument=instrument, zone_id=zone["zone_id"], action=action, run_id=run_id)
    payload = {
        "source": "9router",
        "model": os.getenv("NINEROUTER_MODEL", "openai/gpt-4.1-mini"),
        "trigger": context["trigger"],
        "decision": decision,
        "trade_plan": context["trade_plan"],
    }
    verdict = tools.write_verdict(
        zone_id=zone["zone_id"],
        verdict=action,
        validation_date=today,
        instrument=instrument,
        run_id=run_id,
        entry_confluence=decision["entry_confluence"],
        limit_price=prices.get("limit_price"),
        hard_block_flags=decision["hard_block_flags"],
        reason=decision["reason"],
        source_file="run_validate_9router.py",
        payload=payload,
    )
    trade = tools.write_trade_log(
        zone_id=zone["zone_id"],
        verdict=action,
        validation_date=today,
        instrument=instrument,
        week=zone.get("week"),
        label=zone.get("label"),
        direction=zone.get("direction"),
        run_id=run_id,
        entry_confluence=decision["entry_confluence"],
        limit_price=prices.get("limit_price"),
        sl_price=prices.get("sl_price"),
        tp_price=prices.get("tp_price"),
        hard_block_flags=decision["hard_block_flags"],
        reason=decision["reason"],
    )
    snap = tools.snapshot_features(
        zone_id=zone["zone_id"],
        instrument=instrument,
        event_type="validate",
        features={
            "trigger": context["trigger"],
            "trade_plan": context["trade_plan"],
            "ec_breakdown": decision.get("ec_breakdown"),
            "hard_block_flags": decision["hard_block_flags"],
            "indicators": context["indicators"],
        },
        event_utc=_utc_now(),
    )
    doc = tools.write_doc(
        doc_type="validation",
        key=f"{today}/{instrument}",
        instrument=instrument,
        valid_date=today,
        week=zone.get("week"),
        title=f"{instrument.upper()} validation {today}",
        body=decision["validation_body"],
        frontmatter={"source": "9router", "zone_id": zone["zone_id"], "verdict": action, "run_id": run_id},
        source_path="run_validate_9router.py",
    )
    log_event("write_success", instrument=instrument, zone_id=zone["zone_id"], action=action, run_id=run_id)
    return {"verdict": verdict, "trade_log": trade, "snapshot": snap, "doc": doc}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--instrument", required=True)
    ap.add_argument("--reason", required=True, choices=["ENTRY", "INVAL"])
    ap.add_argument("--zone-id", required=True)
    ap.add_argument("--h1-dt")
    ap.add_argument("--dry-run", action="store_true", help="build context only; no 9router call, no writes")
    args = ap.parse_args(argv)

    try:
        model = os.getenv("NINEROUTER_MODEL", "openai/gpt-4.1-mini")
        validator = Path(__file__).name
        log_event(
            "validator_selected",
            instrument=args.instrument.lower(),
            reason=args.reason,
            zone_id=args.zone_id,
            validator=validator,
            provider="9router",
            model=model,
        )
        context = build_context(args.instrument.lower(), args.reason, args.zone_id, args.h1_dt)
        if args.dry_run:
            log_event("dry_run_complete", instrument=args.instrument.lower(), reason=args.reason, zone_id=args.zone_id)
            print(json.dumps({
                "ok": True,
                "dry_run": True,
                "validator": validator,
                "provider": "9router",
                "model": model,
                "context_keys": sorted(context),
                "trade_plan": context["trade_plan"],
            }))
            return 0
        decision = validate_decision(call_9router(context))
        zone = context["zone"]
        result = write_outputs(args.instrument.lower(), zone, context, decision)
        print(json.dumps({
            "ok": True,
            "validator": validator,
            "provider": "9router",
            "model": model,
            "action": decision["action"],
            "zone_id": args.zone_id,
            "result": result,
        }, default=str))
        return 0
    except Exception as exc:
        log_event("failed", instrument=args.instrument.lower(), reason=args.reason, zone_id=args.zone_id, error=str(exc))
        raise


if __name__ == "__main__":
    os.chdir(REPO_ROOT)
    raise SystemExit(main())
