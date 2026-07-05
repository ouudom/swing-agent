#!/usr/bin/env python3
"""
check_live_trades.py — live order-lifecycle checker for `trade_log`.

`trade_log` rows are written by the MCP tool `write_trade_log`, called from the hourly
/validate routine: it logs ORDER_LIMIT (with limit/SL/TP already computed per the
constitution formula), NO_TRADE, or INVALIDATED. Once a row reaches RUNNING (filled) or
a terminal status, `write_trade_log` refuses further status changes — only THIS script
may move a trade forward from there. That split keeps /validate from flip-flopping a
resting limit or a live position hour to hour.

Two passes, mechanical only (no signal/EC logic — that's /validate's job, already baked
into limit_price/sl_price/tp_price at ORDER_LIMIT time):

  1. status=ORDER_LIMIT — check 1H bars since the row was last updated for a touch of
     limit_price. First touch → RUNNING (entry_price=limit_price, fill_time=bar time).
     No touch by the zone week's Friday 13:00 UTC cutoff (weekend-gap policy, matches
     trade_outcome.py) → EXPIRED.
  2. status=RUNNING — walk 1H bars from fill_time forward: TP at tp_price → WIN; SL at
     sl_price → LOSS; BE arms (stop → entry) once a bar's favorable excursion reaches
     +1.5R (R = |entry - sl_price|); same-bar SL+TP ambiguity → SL (conservative,
     matches trade_outcome.py/zone_outcomes.py convention).

Usage:
  bash src/engine/scripts/pyrun.sh src/engine/scripts/ops/check_live_trades.py
  bash src/engine/scripts/pyrun.sh src/engine/scripts/ops/check_live_trades.py --instrument xauusd
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone

try:
    import psycopg
except ImportError as exc:
    raise SystemExit("psycopg missing. Run inside container or `bash scripts/pyrun.sh --setup`.") from exc


def connect():
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


def queue_notification(
    con,
    event_type: str,
    title: str,
    message: str,
    instrument: str | None = None,
    zone_id: str | None = None,
    payload: dict | None = None,
) -> None:
    event_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{event_type}:{zone_id}:{title}:{message}"))
    with con.cursor() as cur:
        cur.execute(
            """
            INSERT INTO notification_event (
              event_id, event_type, instrument, zone_id, title, message, payload
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s::jsonb)
            ON CONFLICT (event_id) DO NOTHING
            """,
            (event_id, event_type, instrument, zone_id, title, message, json.dumps(payload or {})),
        )


def friday_cutoff(week: str) -> datetime:
    """Fri 13:00 UTC of the zone's ISO week — unfilled limits expire here."""
    year, wnum = week.split("-W")
    mon = datetime.fromisocalendar(int(year), int(wnum), 1).replace(tzinfo=timezone.utc)
    return mon + timedelta(days=4, hours=13)


def bars_since(con, instrument: str, since: datetime, tf: str = "1h"):
    with con.cursor() as cur:
        cur.execute(
            "SELECT datetime, open, high, low, close FROM ohlc "
            "WHERE symbol = %s AND tf = %s AND datetime > %s ORDER BY datetime",
            (instrument, tf, since),
        )
        cols = [d.name for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


def check_fills(con, instrument: str | None, now: datetime) -> list[str]:
    with con.cursor() as cur:
        cur.execute(
            "SELECT zone_id, instrument, week, direction, limit_price, updated_utc "
            "FROM trade_log WHERE status = 'ORDER_LIMIT'"
            + (" AND instrument = %s" if instrument else ""),
            (instrument,) if instrument else (),
        )
        cols = [d.name for d in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]

    notes = []
    for r in rows:
        cutoff = friday_cutoff(r["week"])
        bars = bars_since(con, r["instrument"], r["updated_utc"])
        is_long = r["direction"] == "LONG"
        limit = float(r["limit_price"])
        fill_bar = next(
            (b for b in bars if b["datetime"] <= cutoff
             and ((b["low"] <= limit) if is_long else (b["high"] >= limit))),
            None,
        )
        if fill_bar is not None:
            with con.cursor() as cur:
                cur.execute(
                    "UPDATE trade_log SET status='RUNNING', entry_price=%s, fill_time=%s, "
                    "updated_utc=now() WHERE zone_id=%s AND status='ORDER_LIMIT'",
                    (limit, fill_bar["datetime"], r["zone_id"]),
                )
            queue_notification(
                con, "trade_filled",
                title=f"{r['instrument'].upper()} FILLED {r['zone_id']}",
                message=f"{r['direction']} @ {limit} ({fill_bar['datetime']})",
                instrument=r["instrument"], zone_id=r["zone_id"],
                payload={"entry_price": limit, "fill_time": str(fill_bar["datetime"])},
            )
            notes.append(f"{r['zone_id']} FILLED @ {limit} ({fill_bar['datetime']})")
        elif now > cutoff:
            with con.cursor() as cur:
                cur.execute(
                    "UPDATE trade_log SET status='EXPIRED', updated_utc=now() "
                    "WHERE zone_id=%s AND status='ORDER_LIMIT'",
                    (r["zone_id"],),
                )
            queue_notification(
                con, "trade_expired",
                title=f"{r['instrument'].upper()} EXPIRED {r['zone_id']}",
                message="unfilled past Fri 13:00 UTC cutoff",
                instrument=r["instrument"], zone_id=r["zone_id"],
            )
            notes.append(f"{r['zone_id']} EXPIRED (unfilled past Fri 13:00 UTC cutoff)")
    return notes


def check_exits(con, instrument: str | None) -> list[str]:
    with con.cursor() as cur:
        cur.execute(
            "SELECT zone_id, instrument, direction, entry_price, sl_price, tp_price, fill_time "
            "FROM trade_log WHERE status = 'RUNNING'"
            + (" AND instrument = %s" if instrument else ""),
            (instrument,) if instrument else (),
        )
        cols = [d.name for d in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]

    notes = []
    for r in rows:
        is_long = r["direction"] == "LONG"
        sign = 1 if is_long else -1
        entry = float(r["entry_price"])
        sl_dist = abs(entry - float(r["sl_price"]))
        tp = float(r["tp_price"])
        stop = float(r["sl_price"])
        be_armed = False

        bars = bars_since(con, r["instrument"], r["fill_time"])
        exit_status = exit_price = exit_time = r_result = None
        for b in bars:
            hi, lo = float(b["high"]), float(b["low"])
            stopped = (lo <= stop) if is_long else (hi >= stop)
            hit_tp = (hi >= tp) if is_long else (lo <= tp)
            if stopped:
                exit_status = "BREAKEVEN" if be_armed and stop == entry else "LOSS"
                exit_price, exit_time = stop, b["datetime"]
                r_result = 0.0 if exit_status == "BREAKEVEN" else -1.0
                break
            if hit_tp:
                exit_status, exit_price, exit_time = "WIN", tp, b["datetime"]
                r_result = sign * (tp - entry) / sl_dist
                break
            fav = (hi - entry) if is_long else (entry - lo)
            if not be_armed and fav >= 1.5 * sl_dist:
                be_armed, stop = True, entry
                queue_notification(
                    con, "trade_be_armed",
                    title=f"{r['instrument'].upper()} BE ARMED {r['zone_id']}",
                    message=f"+1.5R reached — stop moved to entry {entry}",
                    instrument=r["instrument"], zone_id=r["zone_id"],
                )

        if exit_status:
            with con.cursor() as cur:
                cur.execute(
                    "UPDATE trade_log SET status=%s, exit_price=%s, exit_time=%s, r_result=%s, "
                    "updated_utc=now() WHERE zone_id=%s AND status='RUNNING'",
                    (exit_status, exit_price, exit_time, r_result, r["zone_id"]),
                )
            queue_notification(
                con, "trade_exit",
                title=f"{r['instrument'].upper()} {exit_status} {r['zone_id']}",
                message=f"{r_result:+.2f}R @ {exit_price} ({exit_time})",
                instrument=r["instrument"], zone_id=r["zone_id"],
                payload={"exit_status": exit_status, "exit_price": exit_price, "r_result": r_result},
            )
            notes.append(f"{r['zone_id']} {exit_status} ({r_result:+.2f}R)")
    return notes


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Check trade_log for fills and closes.")
    parser.add_argument("--instrument", default=None)
    args = parser.parse_args(argv)

    now = datetime.now(timezone.utc)
    with connect() as con:
        with con.transaction():
            notes = check_fills(con, args.instrument, now)
        with con.transaction():
            notes += check_exits(con, args.instrument)

    if notes:
        print("\n".join(notes))
    else:
        print("no fills/exits")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
