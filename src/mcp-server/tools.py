#!/usr/bin/env python3
"""
tools.py — pure tool functions for the swing-agent read/compute/write surface.

No transport here. `server_mcp.py` imports `TOOLS` (name -> callable) and the
helpers from this module. Each function is typed so FastMCP can auto-derive its
inputSchema.
"""
from __future__ import annotations

import json
import os
import re
import sys
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[1]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
ENGINE_SCRIPTS = SRC_ROOT / "engine" / "scripts"
if str(ENGINE_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(ENGINE_SCRIPTS))  # zone_context + its db/structure/backtest_signals deps

from engine import commands  # noqa: E402


ROW_CAP = int(os.getenv("MCP_ROW_CAP", "500"))
SQL_TIMEOUT_MS = int(os.getenv("MCP_SQL_TIMEOUT_MS", "5000"))

READ_ONLY_SQL = re.compile(r"^\s*(select|with|show)\b", re.I | re.S)
FORBIDDEN_SQL = re.compile(
    r"\b(insert|update|delete|drop|alter|create|truncate|grant|revoke|copy|vacuum|call|do)\b",
    re.I,
)

BACKTEST_ALLOWLIST = {
    "offset_session": ["src/engine/scripts/backtest/backtest_offset_session.py"],
    "e0_variants": ["src/engine/scripts/backtest/backtest_e0_variants.py"],
    "entry_sim": ["src/engine/scripts/backtest/backtest_entry_sim.py"],
}

BACKTEST_ARG_ALLOWLIST = {
    "offset_session": {"--wfill"},
    "e0_variants": {"--instrument", "--tf"},
    "entry_sim": {"--instrument"},
}

GATE_ALLOWLIST = {
    "econ_calendar": ["src/engine/scripts/gates/check_econ_calendar.py"],
    "cb_calendar": ["src/engine/scripts/gates/check_cb_calendar.py"],
    "intervention_watch": ["src/engine/scripts/gates/check_intervention_watch.py"],
    "structured_news_event": ["src/engine/scripts/gates/check_structured_news_event.py"],
    "v1b": ["src/engine/scripts/gates/check_intraday_invalidation.py"],
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def pg_connect():
    import psycopg

    dsn = os.getenv("DATABASE_URL")
    if dsn:
        return psycopg.connect(dsn)
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "swing_agent"),
        user=os.getenv("POSTGRES_USER", "swing_agent"),
        password=os.getenv("POSTGRES_PASSWORD", "swing_agent_dev_password"),
    )


def norm(value):
    if value is None:
        return None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def query(sql: str, params=(), row_cap: int = ROW_CAP):
    with pg_connect() as con:
        with con.cursor() as cur:
            cur.execute(f"SET LOCAL statement_timeout = {SQL_TIMEOUT_MS}")
            cur.execute(sql, params)
            cols = [d.name for d in cur.description]
            rows = cur.fetchmany(row_cap + 1)
    truncated = len(rows) > row_cap
    rows = rows[:row_cap]
    return {
        "columns": cols,
        "rows": [{cols[i]: norm(v) for i, v in enumerate(row)} for row in rows],
        "row_count": len(rows),
        "truncated": truncated,
    }


def execute(sql: str, params=()):
    with pg_connect() as con:
        with con.transaction():
            with con.cursor() as cur:
                cur.execute(sql, params)
                if cur.description:
                    cols = [d.name for d in cur.description]
                    rows = cur.fetchall()
                    return [{cols[i]: norm(v) for i, v in enumerate(row)} for row in rows]
    return []


def drain_notifications_best_effort(limit: int = 20) -> None:
    try:
        from engine.scripts.ops.send_notifications import drain_pending

        drain_pending(limit=limit)
    except Exception:
        pass


def sql_query(sql: str, limit: int | None = None):
    text = sql.strip()
    if ";" in text.rstrip(";"):
        raise ValueError("multiple SQL statements rejected")
    if not READ_ONLY_SQL.match(text) or FORBIDDEN_SQL.search(text):
        raise ValueError("only read-only SELECT/WITH/SHOW SQL allowed")
    cap = min(int(limit or ROW_CAP), ROW_CAP)
    return query(text.rstrip(";"), row_cap=cap)


def get_news(instrument: str | None = None, days: int = 7, limit: int = 25):
    since = datetime.now(timezone.utc) - timedelta(days=int(days))
    terms = []
    if instrument:
        inst = instrument.lower()
        terms = [inst, inst[:3], inst[3:], "usd" if "usd" in inst else inst]
    where = ["datetime_utc >= %s"]
    params: list[object] = [since]
    if terms:
        like = " OR ".join(["LOWER(headline || ' ' || COALESCE(summary,'') || ' ' || COALESCE(related,'')) LIKE %s"] * len(terms))
        where.append(f"({like})")
        params += [f"%{t}%" for t in terms]
    params.append(min(int(limit), ROW_CAP))
    return query(
        "SELECT datetime_utc, category, headline, source, url, summary, related "
        f"FROM news WHERE {' AND '.join(where)} ORDER BY datetime_utc DESC LIMIT %s",
        params,
        row_cap=min(int(limit), ROW_CAP),
    )


def get_econ(start: str | None = None, days: int = 7, country: str | None = None):
    start_date = date.fromisoformat(start) if start else datetime.now(timezone.utc).date()
    end_date = start_date + timedelta(days=int(days))
    where = ["date >= %s", "date <= %s"]
    params: list[object] = [start_date, end_date]
    if country:
        where.append("country = %s")
        params.append(country.upper())
    return query(
        "SELECT date, time_utc, country, event, impact, estimate, actual, prev, unit "
        f"FROM econ_calendar WHERE {' AND '.join(where)} ORDER BY date, time_utc, country",
        params,
    )


def get_calibration(instrument: str | None = None):
    params: list[object] = []
    where = ""
    if instrument:
        where = "WHERE instrument = %s"
        params.append(instrument.lower())
    return {
        "zone_outcome": query(
            "SELECT instrument, direction, status, COUNT(*) AS n, AVG(r_result) AS avg_r "
            f"FROM zone_outcome {where} GROUP BY instrument, direction, status "
            "ORDER BY instrument, direction, status",
            params,
        ),
        "trade_outcome": query(
            "SELECT instrument, direction, status, COUNT(*) AS n, AVG(r_result) AS avg_r "
            f"FROM trade_outcome {where} GROUP BY instrument, direction, status "
            "ORDER BY instrument, direction, status",
            params,
        ),
    }


def get_brief(instrument: str, kind: str = "validate"):
    inst = instrument.lower()
    latest = query(
        "SELECT tf, MAX(datetime) AS latest_dt FROM ohlc "
        "WHERE symbol = %s GROUP BY tf ORDER BY tf",
        (inst,),
    )
    zones = query(
        "SELECT * FROM zone_ledger WHERE instrument = %s ORDER BY week DESC, label LIMIT 20",
        (inst,),
    )
    trades = query(
        "SELECT * FROM trade_outcome WHERE instrument = %s ORDER BY week DESC, label LIMIT 20",
        (inst,),
    )
    verdicts = query(
        "SELECT * FROM validation_verdict WHERE instrument = %s ORDER BY validation_date DESC, run_id DESC LIMIT 20",
        (inst,),
    )
    return {
        "instrument": inst,
        "kind": kind,
        "generated_utc": utc_now(),
        "latest_ohlc": latest,
        "zones": zones,
        "trade_outcome": trades,
        "validation_verdicts": verdicts,
        "news": get_news(inst, days=7, limit=10),
        "econ": get_econ(days=7),
    }


def compute_indicators(instrument: str, tf: str = "1h", limit: int = 200):
    inst = instrument.lower()
    rows = query(
        "SELECT datetime, open, high, low, close, volume FROM ohlc "
        "WHERE symbol = %s AND tf = %s ORDER BY datetime DESC LIMIT %s",
        (inst, tf, min(max(int(limit), 30), 500)),
        row_cap=min(max(int(limit), 30), 500),
    )["rows"]
    bars = list(reversed(rows))
    closes = [float(r["close"]) for r in bars if r["close"] is not None]
    highs = [float(r["high"]) for r in bars if r["high"] is not None]
    lows = [float(r["low"]) for r in bars if r["low"] is not None]
    if len(closes) < 15:
        raise ValueError("not enough bars")
    trs = []
    for i in range(1, len(closes)):
        trs.append(max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1])))
    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gains = [max(d, 0.0) for d in deltas[-14:]]
    losses = [abs(min(d, 0.0)) for d in deltas[-14:]]
    avg_loss = sum(losses) / 14
    rs = (sum(gains) / 14) / avg_loss if avg_loss else None
    rsi14 = 100.0 if rs is None else 100 - (100 / (1 + rs))
    return {
        "instrument": inst,
        "tf": tf,
        "bars": len(bars),
        "latest_datetime": bars[-1]["datetime"],
        "latest_close": closes[-1],
        "atr14": sum(trs[-14:]) / 14,
        "rsi14": rsi14,
        "sma20": sum(closes[-20:]) / 20 if len(closes) >= 20 else None,
        "sma50": sum(closes[-50:]) / 50 if len(closes) >= 50 else None,
    }


def get_zone_context(instrument: str):
    """Full deterministic zone-scoring context for /weekly, assembled from the DB:
    structure (pivots/swings/fibs/BOS-CHoCH/time-at-price), momentum (D1+H4), ATR + SL
    preview, macro (DXY/VIX/FRED), and COT positioning. DB-native replacement for the
    retired weekly_pull_*.txt dump — the numbers the AI needs to publish Trading Zones."""
    import zone_context
    return zone_context.build(instrument)


def command_payload(result: commands.CommandResult):
    return {
        "command": result.command,
        "returncode": result.returncode,
        "stdout_tail": result.stdout[-8000:],
        "stderr_tail": result.stderr[-8000:],
    }


GATE_ALERT_TRIGGERS = {
    "cb_calendar": ["(TODAY)"],
    "econ_calendar": ["no-trade window"],
    "intervention_watch": ["🛑", "⚠ CAUTION"],
    "structured_news_event": ["T4_X=TRUE"],
    "v1b": ["V1b BREACH"],
}


def _gate_instrument(args: list[str] | None) -> str | None:
    args = args or []
    for flag in ("--instrument",):
        if flag in args:
            return args[args.index(flag) + 1].lower()
    return None


def _gate_alert_identity(name: str, inst: str | None, triggers: list[str]) -> tuple[str | None, dict]:
    if name != "intervention_watch":
        return None, {}

    severity = "hard_block" if "🛑" in triggers else "caution"
    now = datetime.now(timezone.utc)
    bucket = now.strftime("%Y%m%dT%H") if severity == "hard_block" else now.strftime("%Y%m%d")
    event_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"gate:{name}:{inst or name}:{severity}:{bucket}"))
    return event_id, {"severity": severity, "throttle_bucket": bucket}


def run_gate(name: str, args: list[str] | None = None):
    if name not in GATE_ALLOWLIST:
        raise ValueError(f"gate not allowlisted: {name}")
    result = commands.pyrun([*GATE_ALLOWLIST[name], *(args or [])], timeout_s=120)
    payload = command_payload(result)
    stdout = result.stdout or ""
    triggers = [t for t in GATE_ALERT_TRIGGERS.get(name, []) if t in stdout]
    if triggers:
        inst = _gate_instrument(args)
        event_id, alert_meta = _gate_alert_identity(name, inst, triggers)
        queue_notification(
            event_type=f"gate_{name}",
            title=f"{(inst or name).upper()} gate alert: {name}",
            message=stdout.strip()[-1500:],
            instrument=inst,
            payload={"gate": name, "triggers": triggers, "args": args or [], **alert_meta},
            event_id=event_id,
        )
    return payload


def run_replay(week: str | None = None, instrument: str | None = None):
    return {
        "zone_outcomes": command_payload(commands.zone_outcomes(week, instrument)),
        "trade_outcome": command_payload(commands.trade_outcome(week, instrument)),
    }


def run_calibration():
    return command_payload(commands.calibration())


def run_backtest(name: str, args: list[str] | None = None):
    if name not in BACKTEST_ALLOWLIST:
        raise ValueError(f"backtest not allowlisted: {name}")
    safe_args = [str(a) for a in (args or [])]
    for i, arg in enumerate(safe_args):
        if arg.startswith("-") and arg not in BACKTEST_ARG_ALLOWLIST[name]:
            raise ValueError("backtest arg not allowlisted")
        if arg == "--out":
            raise ValueError("backtest file output disabled over MCP")
        if i and safe_args[i - 1].startswith("-") and ("/" in arg or "\\" in arg or ".." in arg):
            raise ValueError("path-like backtest arg rejected")
    return command_payload(commands.pyrun([*BACKTEST_ALLOWLIST[name], *safe_args], timeout_s=600))


def _clean_payload(payload: dict | None) -> str:
    return json.dumps(payload or {}, sort_keys=True)


def _zone_exists(zone_id: str) -> bool:
    return bool(query("SELECT zone_id FROM zone_ledger WHERE zone_id = %s", (zone_id,), row_cap=1)["rows"])


def publish_zone(
    zone_id: str,
    instrument: str,
    week: str,
    label: str,
    direction: str,
    zone_bottom: float | None = None,
    zone_top: float | None = None,
    zone_confluence: float | None = None,
    conviction: str | None = None,
    invalidation_level: float | None = None,
    tp_anchor: float | None = None,
    published_utc: str | None = None,
    source_file: str | None = None,
    status: str = "OPEN",
    notes: str | None = None,
    payload: dict | None = None,
):
    inst = instrument.lower()
    direction = direction.upper()
    if direction not in {"LONG", "SHORT"}:
        raise ValueError("direction must be LONG or SHORT")
    if status not in {"OPEN", "PENDING", "RESOLVED", "INVALIDATED", "NO_TRADE"}:
        raise ValueError("invalid zone status")
    published = published_utc or utc_now()
    row = execute(
        """
        INSERT INTO zone_ledger (
          zone_id, instrument, week, label, direction, zone_bottom, zone_top, zone_confluence,
          conviction, invalidation_level, tp_anchor, published_utc, source_file, status, notes
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (zone_id) DO UPDATE SET
          instrument = EXCLUDED.instrument,
          week = EXCLUDED.week,
          label = EXCLUDED.label,
          direction = EXCLUDED.direction,
          zone_bottom = EXCLUDED.zone_bottom,
          zone_top = EXCLUDED.zone_top,
          zone_confluence = EXCLUDED.zone_confluence,
          conviction = EXCLUDED.conviction,
          invalidation_level = EXCLUDED.invalidation_level,
          tp_anchor = EXCLUDED.tp_anchor,
          published_utc = EXCLUDED.published_utc,
          source_file = EXCLUDED.source_file,
          status = EXCLUDED.status,
          notes = EXCLUDED.notes
        RETURNING *
        """,
        (
            zone_id, inst, week, label, direction, zone_bottom, zone_top, zone_confluence,
            conviction, invalidation_level, tp_anchor, published, source_file, status, notes,
        ),
    )
    if payload:
        queue_notification(
            event_type="weekly_publish",
            title=f"{inst.upper()} {week} {label} {direction}",
            message=f"Published zone {zone_id}: {zone_bottom}-{zone_top} {direction}",
            instrument=inst,
            zone_id=zone_id,
            payload=payload,
        )
    return {"zone": row[0] if row else None, "idempotent": True}


def write_verdict(
    zone_id: str,
    verdict: str,
    validation_date: str,
    instrument: str | None = None,
    run_id: str | None = None,
    entry_confluence: float | None = None,
    limit_price: float | None = None,
    hard_block_flags: list[str] | str | None = None,
    reason: str | None = None,
    source_file: str | None = None,
    payload: dict | None = None,
):
    if not _zone_exists(zone_id):
        raise ValueError(f"unknown zone_id: {zone_id}")
    verdict = verdict.upper()
    if verdict not in {"ORDER_LIMIT", "NO_TRADE", "INVALIDATED", "HARD_BLOCK", "CANCEL_LIMIT"}:
        raise ValueError("invalid verdict")
    if isinstance(hard_block_flags, list):
        flags = ",".join(str(x).upper() for x in hard_block_flags if str(x).strip())
    else:
        flags = (hard_block_flags or "").upper()
    if verdict == "ORDER_LIMIT" and flags:
        raise ValueError("ORDER_LIMIT rejected while hard_block_flags is non-empty")
    if verdict == "ORDER_LIMIT" and (entry_confluence is None or float(entry_confluence) < 5.0):
        raise ValueError("ORDER_LIMIT rejected: entry_confluence must be >= 5.0")
    run = run_id or f"{validation_date}-{zone_id}"
    inst = (instrument or zone_id.split("-", 1)[0]).lower()
    rows = execute(
        """
        INSERT INTO validation_verdict (
          zone_id, validation_date, run_id, instrument, verdict, entry_confluence, limit_price,
          hard_block_flags, reason, source_file, payload
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb)
        ON CONFLICT (zone_id, validation_date, run_id) DO UPDATE SET
          instrument = EXCLUDED.instrument,
          verdict = EXCLUDED.verdict,
          entry_confluence = EXCLUDED.entry_confluence,
          limit_price = EXCLUDED.limit_price,
          hard_block_flags = EXCLUDED.hard_block_flags,
          reason = EXCLUDED.reason,
          source_file = EXCLUDED.source_file,
          payload = EXCLUDED.payload,
          updated_utc = now()
        RETURNING *
        """,
        (
            zone_id, validation_date, run, inst, verdict, entry_confluence, limit_price,
            flags, reason, source_file, _clean_payload(payload),
        ),
    )
    zone_status = "OPEN"
    if verdict in {"INVALIDATED", "HARD_BLOCK"}:
        zone_status = "INVALIDATED"
    elif verdict == "ORDER_LIMIT":
        zone_status = "OPEN"
    execute(
        """
        UPDATE zone_ledger
        SET entry_confluence = %s,
            daily_verdict = %s,
            limit_price = %s,
            validated_date = %s,
            status = CASE WHEN %s IN ('INVALIDATED','HARD_BLOCK') THEN 'INVALIDATED' ELSE status END
        WHERE zone_id = %s
        """,
        (entry_confluence, verdict, limit_price, validation_date, verdict, zone_id),
    )
    if verdict in {"ORDER_LIMIT", "INVALIDATED", "HARD_BLOCK", "CANCEL_LIMIT"}:
        queue_notification(
            event_type="validation_verdict",
            title=f"{inst.upper()} {verdict} {zone_id}",
            message=reason or f"{zone_id}: {verdict}",
            instrument=inst,
            zone_id=zone_id,
            payload={"validation_date": validation_date, "verdict": verdict, **(payload or {})},
        )
    return {"verdict": rows[0] if rows else None, "zone_status": zone_status, "idempotent": True}


LOCKED_TRADE_STATUSES = {"RUNNING", "WIN", "LOSS", "BREAKEVEN", "EXPIRED"}


def write_trade_log(
    zone_id: str,
    verdict: str,
    validation_date: str,
    instrument: str | None = None,
    week: str | None = None,
    label: str | None = None,
    direction: str | None = None,
    run_id: str | None = None,
    entry_confluence: float | None = None,
    limit_price: float | None = None,
    sl_price: float | None = None,
    tp_price: float | None = None,
    hard_block_flags: list[str] | str | None = None,
    reason: str | None = None,
):
    """Hourly /validate write-back for LIVE order state (distinct from write_verdict's
    validation_verdict record and from zone_ledger.status/replay_status, which are
    zone-quality/replay bookkeeping, not real order lifecycle).

    Once a trade_log row reaches RUNNING (filled) or a terminal status (WIN/LOSS/
    BREAKEVEN/EXPIRED), /validate can no longer change its status — only
    check_live_trades.py (the scheduled fill/close checker) may. This stops the hourly
    routine from flip-flopping a live order once it's in the market.
    """
    if not _zone_exists(zone_id):
        raise ValueError(f"unknown zone_id: {zone_id}")
    verdict = verdict.upper()
    if verdict not in {"ORDER_LIMIT", "NO_TRADE", "INVALIDATED", "HARD_BLOCK", "CANCEL_LIMIT"}:
        raise ValueError("invalid verdict")
    if isinstance(hard_block_flags, list):
        flags = ",".join(str(x).upper() for x in hard_block_flags if str(x).strip())
    else:
        flags = (hard_block_flags or "").upper()
    if verdict == "ORDER_LIMIT" and flags:
        raise ValueError("ORDER_LIMIT rejected while hard_block_flags is non-empty")
    if verdict == "ORDER_LIMIT" and (entry_confluence is None or float(entry_confluence) < 5.0):
        raise ValueError("ORDER_LIMIT rejected: entry_confluence must be >= 5.0")
    if verdict == "ORDER_LIMIT" and (sl_price is None or tp_price is None or limit_price is None):
        raise ValueError("ORDER_LIMIT requires limit_price, sl_price, tp_price")

    existing = query("SELECT status FROM trade_log WHERE zone_id = %s", (zone_id,), row_cap=1)["rows"]
    current_status = existing[0]["status"] if existing else None
    if current_status in LOCKED_TRADE_STATUSES:
        raise ValueError(
            f"trade_log for {zone_id} is locked at status={current_status} — "
            "the trade is live/closed; only check_live_trades.py may change it further"
        )

    status = {"ORDER_LIMIT": "ORDER_LIMIT", "NO_TRADE": "NO_TRADE",
              "INVALIDATED": "INVALIDATED", "HARD_BLOCK": "INVALIDATED",
              "CANCEL_LIMIT": "NO_TRADE"}[verdict]
    run = run_id or f"{validation_date}-{zone_id}"
    inst = (instrument or zone_id.split("-", 1)[0]).lower()
    zone_parts = zone_id.split("-")
    wk = week or (zone_parts[1] + "-" + zone_parts[2] if len(zone_parts) >= 4 else None)
    lbl = label or (zone_parts[-1] if len(zone_parts) >= 3 else None)

    rows = execute(
        """
        INSERT INTO trade_log (
          zone_id, instrument, week, label, direction, status, entry_confluence,
          limit_price, sl_price, tp_price, hard_block_flags, reason, validation_date, run_id
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (zone_id) DO UPDATE SET
          status = EXCLUDED.status,
          entry_confluence = EXCLUDED.entry_confluence,
          limit_price = EXCLUDED.limit_price,
          sl_price = EXCLUDED.sl_price,
          tp_price = EXCLUDED.tp_price,
          hard_block_flags = EXCLUDED.hard_block_flags,
          reason = EXCLUDED.reason,
          validation_date = EXCLUDED.validation_date,
          run_id = EXCLUDED.run_id,
          updated_utc = now()
        WHERE trade_log.status NOT IN ('RUNNING','WIN','LOSS','BREAKEVEN','EXPIRED')
        RETURNING *
        """,
        (
            zone_id, inst, wk, lbl, direction, status, entry_confluence,
            limit_price, sl_price, tp_price, flags, reason, validation_date, run,
        ),
    )
    if not rows:
        raise ValueError(
            f"trade_log for {zone_id} was locked by a concurrent fill/close — refresh and retry"
        )
    if verdict in {"ORDER_LIMIT", "INVALIDATED", "HARD_BLOCK"}:
        queue_notification(
            event_type="trade_log",
            title=f"{inst.upper()} {status} {zone_id}",
            message=reason or f"{zone_id}: {status}",
            instrument=inst,
            zone_id=zone_id,
            payload={"validation_date": validation_date, "verdict": verdict},
        )
    return {"trade_log": rows[0], "idempotent": True}


def snapshot_features(
    zone_id: str,
    instrument: str,
    event_type: str,
    features: dict,
    event_utc: str | None = None,
):
    """Freeze the feature vector a decision was actually scored on (Phase 3 —
    research/backtest readiness). Call this once per decision, not per read:
      - /weekly, right after get_zone_context — event_type="publish", features=that dict.
      - /validate, right after entry_confluence scoring — event_type="validate",
        features={"ec_score":..., "components": breakdown["components"], "flags": ...,
        plus any live compute_indicators/get_zone_context values used for the call}.
    Idempotent per (zone_id, event_type, event_utc) — safe to re-call on retry."""
    if not _zone_exists(zone_id):
        raise ValueError(f"unknown zone_id: {zone_id}")
    if event_type not in {"publish", "validate"}:
        raise ValueError("event_type must be 'publish' or 'validate'")
    ts = event_utc or utc_now()
    snap_id = f"{zone_id}:{event_type}:{ts}"
    rows = execute(
        """
        INSERT INTO feature_snapshot (snap_id, zone_id, instrument, event_type, event_utc, features)
        VALUES (%s,%s,%s,%s,%s,%s::jsonb)
        ON CONFLICT (snap_id) DO UPDATE SET features = EXCLUDED.features
        RETURNING *
        """,
        (snap_id, zone_id, instrument.lower(), event_type, ts, _clean_payload(features)),
    )
    return rows[0] if rows else None


def queue_notification(
    event_type: str,
    title: str,
    message: str,
    instrument: str | None = None,
    zone_id: str | None = None,
    payload: dict | None = None,
    event_id: str | None = None,
):
    event_id = event_id or str(uuid.uuid5(uuid.NAMESPACE_URL, f"{event_type}:{zone_id}:{title}:{message}"))
    rows = execute(
        """
        INSERT INTO notification_event (
          event_id, event_type, instrument, zone_id, title, message, payload
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s::jsonb)
        ON CONFLICT (event_id) DO UPDATE SET
          title = EXCLUDED.title,
          message = EXCLUDED.message,
          payload = EXCLUDED.payload
        RETURNING *
        """,
        (event_id, event_type, instrument, zone_id, title, message, _clean_payload(payload)),
    )
    drain_notifications_best_effort()
    return rows[0] if rows else {"event_id": event_id}


def update_checkpoint(
    routine_name: str,
    status: str,
    branch: str | None = None,
    commit_sha: str | None = None,
    notes: str | None = None,
):
    rows = execute(
        """
        INSERT INTO routine_checkpoint (routine_name, status, last_run_utc, branch, commit_sha, notes)
        VALUES (%s,%s,now(),%s,%s,%s)
        ON CONFLICT (routine_name) DO UPDATE SET
          status = EXCLUDED.status,
          last_run_utc = EXCLUDED.last_run_utc,
          branch = EXCLUDED.branch,
          commit_sha = EXCLUDED.commit_sha,
          notes = EXCLUDED.notes,
          updated_utc = now()
        RETURNING *
        """,
        (routine_name, status, branch, commit_sha, notes),
    )
    return rows[0] if rows else None


# ─────────────────────────────────────────────────────────────────────────────
# Docs — wiki prose served from Postgres (Phase 1). Four tables, split by type;
# `doc_type` selects which. write_doc versions the prior row into doc_history.
# ─────────────────────────────────────────────────────────────────────────────

DOC_TABLES = {
    "rulebook": {
        "table": "rulebook",
        "cols": ["doc_key", "scope", "instrument", "kind", "title", "body", "frontmatter", "source_path"],
        "list_extra": ["scope", "instrument", "kind"],
    },
    "context": {
        "table": "context_doc",
        "cols": ["doc_key", "kind", "title", "body", "frontmatter", "source_path"],
        "list_extra": ["kind"],
    },
    "forecast": {
        "table": "forecast_doc",
        "cols": ["doc_key", "instrument", "week", "title", "body", "frontmatter", "generated", "source_path"],
        "list_extra": ["instrument", "week", "generated"],
    },
    "validation": {
        "table": "validation_doc",
        "cols": ["doc_key", "instrument", "valid_date", "week", "title", "body", "frontmatter", "source_path"],
        "list_extra": ["instrument", "valid_date", "week"],
    },
}


def _doc_spec(doc_type: str):
    spec = DOC_TABLES.get(doc_type)
    if not spec:
        raise ValueError(f"unknown doc_type: {doc_type} (one of {sorted(DOC_TABLES)})")
    return spec


def get_doc(doc_type: str, key: str):
    """Read one prose doc from Postgres. doc_type ∈ rulebook|context|forecast|validation.
    key is the doc_key (e.g. 'constitution', 'xauusd/confluence', '2026-W27/xauusd',
    '2026-07-05/xauusd')."""
    spec = _doc_spec(doc_type)
    rows = query(f"SELECT * FROM {spec['table']} WHERE doc_key = %s", (key,), row_cap=1)["rows"]
    return rows[0] if rows else None


def list_docs(
    doc_type: str,
    instrument: str | None = None,
    week: str | None = None,
    kind: str | None = None,
):
    """List prose docs (metadata only, no body) for a doc_type, newest first."""
    spec = _doc_spec(doc_type)
    meta = [c for c in spec["cols"] if c not in {"body", "frontmatter"}] + ["version", "updated_utc"]
    where, params = [], []
    if instrument and "instrument" in spec["cols"]:
        where.append("instrument = %s")
        params.append(instrument.lower())
    if week and "week" in spec["cols"]:
        where.append("week = %s")
        params.append(week)
    if kind and "kind" in spec["cols"]:
        where.append("kind = %s")
        params.append(kind)
    clause = f"WHERE {' AND '.join(where)}" if where else ""
    return query(
        f"SELECT {', '.join(meta)} FROM {spec['table']} {clause} ORDER BY updated_utc DESC",
        tuple(params),
    )


def write_doc(
    doc_type: str,
    key: str,
    body: str,
    title: str | None = None,
    scope: str | None = None,
    instrument: str | None = None,
    kind: str | None = None,
    week: str | None = None,
    valid_date: str | None = None,
    generated: str | None = None,
    frontmatter: dict | None = None,
    source_path: str | None = None,
):
    """Upsert a prose doc into Postgres (Phase 1 — replaces writing wiki/*.md).
    Archives the prior row into doc_history and bumps version. Only the columns
    that exist on the target table are written; the rest are ignored."""
    spec = _doc_spec(doc_type)
    table = spec["table"]
    if not body or not body.strip():
        raise ValueError("body is required")

    prev = query(
        f"SELECT version, body, frontmatter FROM {table} WHERE doc_key = %s", (key,), row_cap=1
    )["rows"]
    version = 1
    if prev:
        version = int(prev[0]["version"]) + 1
        execute(
            "INSERT INTO doc_history (source_table, doc_key, version, body, frontmatter) "
            "VALUES (%s,%s,%s,%s,%s::jsonb) ON CONFLICT DO NOTHING",
            (table, key, prev[0]["version"], prev[0]["body"], _clean_payload(prev[0]["frontmatter"])),
        )

    supplied = {
        "doc_key": key,
        "scope": scope,
        "instrument": instrument.lower() if instrument else None,
        "kind": kind,
        "title": title,
        "body": body,
        "week": week,
        "valid_date": valid_date,
        "generated": generated,
        "source_path": source_path,
    }
    cols = [c for c in spec["cols"] if c != "frontmatter"]
    has_fm = "frontmatter" in spec["cols"]
    values = [supplied.get(c) for c in cols]
    for c in cols:
        if c in ("scope", "kind") and supplied.get(c) is None and prev is None:
            # required-ish on first insert; default sensibly rather than NULL-fail
            values[cols.index(c)] = "system" if c == "scope" else doc_type

    insert_cols = cols + (["frontmatter"] if has_fm else []) + ["version", "updated_utc"]
    placeholders = ["%s"] * len(cols) + (["%s::jsonb"] if has_fm else []) + ["%s", "now()"]
    row_vals = list(values) + ([_clean_payload(frontmatter)] if has_fm else []) + [version]
    update_cols = [c for c in cols if c != "doc_key"] + (["frontmatter"] if has_fm else []) + ["version"]
    set_clause = ", ".join(f"{c} = EXCLUDED.{c}" for c in update_cols) + ", updated_utc = now()"

    rows = execute(
        f"INSERT INTO {table} ({', '.join(insert_cols)}) VALUES ({', '.join(placeholders)}) "
        f"ON CONFLICT (doc_key) DO UPDATE SET {set_clause} RETURNING *",
        tuple(row_vals),
    )
    return {"doc": rows[0] if rows else None, "version": version, "table": table}


def get_context_pack(instrument: str):
    """One-call boot context for /weekly and /validate: the rulebook rules the
    routine needs (constitution, setup, currency, this instrument's profile +
    confluence) plus the current macro + calibration snapshots — bodies included.
    Lets a fresh cloud routine load full judgment context via MCP, no git checkout."""
    inst = instrument.lower()
    rule = query(
        "SELECT doc_key, kind, title, body FROM rulebook "
        "WHERE scope = 'system' OR instrument = %s ORDER BY scope, kind",
        (inst,),
    )
    ctx = query("SELECT doc_key, kind, title, body FROM context_doc ORDER BY kind")
    return {
        "instrument": inst,
        "generated_utc": utc_now(),
        "rulebook": rule["rows"],
        "context": ctx["rows"],
    }


TOOLS = {
    "sql_query": sql_query,
    "get_brief": get_brief,
    "get_doc": get_doc,
    "list_docs": list_docs,
    "write_doc": write_doc,
    "get_context_pack": get_context_pack,
    "get_news": get_news,
    "get_econ": get_econ,
    "get_calibration": get_calibration,
    "compute_indicators": compute_indicators,
    "get_zone_context": get_zone_context,
    "run_gate": run_gate,
    "run_replay": run_replay,
    "run_calibration": run_calibration,
    "run_backtest": run_backtest,
    "publish_zone": publish_zone,
    "write_verdict": write_verdict,
    "write_trade_log": write_trade_log,
    "snapshot_features": snapshot_features,
    "queue_notification": queue_notification,
    "update_checkpoint": update_checkpoint,
}
