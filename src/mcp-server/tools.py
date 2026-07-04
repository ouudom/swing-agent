#!/usr/bin/env python3
"""
tools.py — pure tool functions for the swing-agent read/compute/write surface.

No transport here. Both the legacy REST server (`server.py`) and the native MCP
server (`server_mcp.py`) import `TOOLS` (name -> callable) and the helpers from
this module. Each function is typed so FastMCP can auto-derive its inputSchema.
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

from engine import commands  # noqa: E402


ROW_CAP = int(os.getenv("MCP_ROW_CAP", "500"))
SQL_TIMEOUT_MS = int(os.getenv("MCP_SQL_TIMEOUT_MS", "5000"))

READ_ONLY_SQL = re.compile(r"^\s*(select|with|show)\b", re.I | re.S)
FORBIDDEN_SQL = re.compile(
    r"\b(insert|update|delete|drop|alter|create|truncate|grant|revoke|copy|vacuum|call|do)\b",
    re.I,
)

BACKTEST_ALLOWLIST = {
    "offset_session": ["src/engine/scripts/backtest_offset_session.py"],
    "e0_variants": ["src/engine/scripts/backtest_e0_variants.py"],
    "entry_sim": ["src/engine/scripts/backtest_entry_sim.py"],
}

BACKTEST_ARG_ALLOWLIST = {
    "offset_session": {"--wfill"},
    "e0_variants": {"--instrument", "--tf"},
    "entry_sim": {"--instrument"},
}

GATE_ALLOWLIST = {
    "econ_calendar": ["src/engine/scripts/check_econ_calendar.py"],
    "cb_calendar": ["src/engine/scripts/check_cb_calendar.py"],
    "intervention_watch": ["src/engine/scripts/check_intervention_watch.py"],
    "structured_news_event": ["src/engine/scripts/check_structured_news_event.py"],
    "v1b": ["src/engine/scripts/check_v1b.py"],
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


def command_payload(result: commands.CommandResult):
    return {
        "command": result.command,
        "returncode": result.returncode,
        "stdout_tail": result.stdout[-8000:],
        "stderr_tail": result.stderr[-8000:],
    }


def run_gate(name: str, args: list[str] | None = None):
    if name not in GATE_ALLOWLIST:
        raise ValueError(f"gate not allowlisted: {name}")
    return command_payload(commands.pyrun([*GATE_ALLOWLIST[name], *(args or [])], timeout_s=120))


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


TOOLS = {
    "sql_query": sql_query,
    "get_brief": get_brief,
    "get_news": get_news,
    "get_econ": get_econ,
    "get_calibration": get_calibration,
    "compute_indicators": compute_indicators,
    "run_gate": run_gate,
    "run_replay": run_replay,
    "run_calibration": run_calibration,
    "run_backtest": run_backtest,
    "publish_zone": publish_zone,
    "write_verdict": write_verdict,
    "queue_notification": queue_notification,
    "update_checkpoint": update_checkpoint,
}
