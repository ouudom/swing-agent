"""
Central-bank decision-date check — mechanical event gate for /weekly + /validate.

Reads the `cb_calendar` Postgres table (Phase 2 — was cb_calendar_{year}.json, imported once
via ops/import_calendar_json_to_db.py) and reports every scheduled central-bank decision inside
the lookahead window, with the instruments each one hard-blocks or flags as caution. Web search
supplements this; it never replaces it (the W24 ECB miss is why this file exists).

Usage:
    bash scripts/pyrun.sh scripts/gates/check_cb_calendar.py                       # today, 7-day window
    bash scripts/pyrun.sh scripts/gates/check_cb_calendar.py --date 2026-06-11
    bash scripts/pyrun.sh scripts/gates/check_cb_calendar.py --days 10
    bash scripts/pyrun.sh scripts/gates/check_cb_calendar.py --instrument eurusd   # filter

Exit codes: 0 = ran (events or not). 1 = cb_calendar table empty/unreadable or query
date beyond a bank's verified_through (calendar can't be trusted for that window).
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone

SRC_ROOT_ENGINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # .../src/engine/scripts
if SRC_ROOT_ENGINE not in sys.path:
    sys.path.insert(0, SRC_ROOT_ENGINE)

INSTRUMENTS = ["xauusd", "eurusd", "gbpusd", "eurgbp", "audusd", "nzdusd",
               "usdcad", "usdchf", "usdjpy", "eurjpy", "gbpjpy"]


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


def load_banks() -> list[dict]:
    with pg_connect() as con:
        with con.cursor() as cur:
            cur.execute(
                "SELECT bank_code, name, time_note, hard_block, caution, dates, verified_through "
                "FROM cb_calendar ORDER BY bank_code"
            )
            cols = [d.name for d in cur.description]
            rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    if not rows:
        print("❌ cb_calendar table is empty — run ops/import_calendar_json_to_db.py "
              "(or insert rows) before trading.")
        sys.exit(1)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description="Central-bank decision-date check")
    ap.add_argument("--date", help="YYYY-MM-DD (default: today UTC)")
    ap.add_argument("--days", type=int, default=7, help="lookahead window in days (default 7)")
    ap.add_argument("--instrument", choices=INSTRUMENTS, help="filter to one instrument")
    args = ap.parse_args()

    start = (datetime.strptime(args.date, "%Y-%m-%d").date() if args.date
             else datetime.now(timezone.utc).date())
    end = start + timedelta(days=args.days)

    banks = load_banks()

    unverified = []
    hits = []
    for bank in banks:
        vt = bank["verified_through"]
        if vt and end > vt:
            unverified.append((bank["bank_code"], vt))
        for d in bank["dates"]:
            dt = datetime.strptime(d["date"], "%Y-%m-%d").date()
            if start <= dt <= end:
                hits.append((dt, bank["bank_code"], bank, d["status"]))

    if args.instrument:
        hits = [h for h in hits if args.instrument in h[2]["hard_block"] + h[2]["caution"]]

    print(f"CB calendar check — window {start} → {end} (UTC)"
          + (f", instrument {args.instrument}" if args.instrument else ""))

    if not hits:
        print("✅ No scheduled central-bank decisions in window.")
    for dt, code, bank, status in sorted(hits):
        est = "  ⚠ ESTIMATED DATE — VERIFY on the bank's official calendar" if status == "estimated" else ""
        days_away = (dt - start).days
        when = "TODAY" if days_away == 0 else f"in {days_away}d"
        print(f"\n🔔 {dt} ({when}) — {bank['name']} [{code}]{est}")
        print(f"   {bank['time_note']}")
        if bank["hard_block"]:
            print(f"   HARD BLOCK: {', '.join(bank['hard_block'])}")
        if bank["caution"]:
            print(f"   caution:    {', '.join(bank['caution'])}")

    if unverified:
        print()
        for code, vt in unverified:
            print(f"❌ {code}: calendar only verified through {vt} — window extends past it. "
                  f"Update the cb_calendar table (bank_code={code}) from the bank's official schedule.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
