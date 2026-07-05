"""
JPY intervention / jawboning watch — mechanical gate for /weekly + /validate (#4).

Reads the `intervention_watch` + `intervention_jawboning` Postgres tables (Phase 2 — was
intervention_watch.json, imported once via ops/import_calendar_json_to_db.py) and, given the
current spot, returns the intervention regime for a JPY pair (usdjpy/eurjpy/gbpjpy): how close
spot is to the MoF intervention level, and any recent jawboning. This is the structured
replacement for the manual web-search MoF read — modeled on check_cb_calendar.py.

Spot rises toward the level = JPY weakening = MoF intervention risk against further pair
upside, so the gate blocks/caps NEW LONGS of the pair (= shorts of JPY):
  spot >= intervention_level             → HARD_BLOCK new longs (active intervention zone)
  spot >= intervention_level − band      → CAUTION  (cap conviction MEDIUM)
  recent jawboning within --days         → CAUTION at minimum, regardless of level

Claude appends new jawboning rows to `intervention_jawboning` from web search during /weekly
JPY runs and pushes `intervention_watch.verified_through` forward (same discipline as before).

Usage:
    bash scripts/pyrun.sh scripts/gates/check_intervention_watch.py --instrument usdjpy --spot 160.5
    bash scripts/pyrun.sh scripts/gates/check_intervention_watch.py --instrument eurjpy --spot 185.2 --days 14

Exit codes: 0 = ran. 1 = pair absent from intervention_watch, or verified_through is
before the query date (watch is stale → refresh from web search before trusting it).
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone

JPY_PAIRS = ["usdjpy", "eurjpy", "gbpjpy"]


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


def load_pair(pair: str) -> dict | None:
    with pg_connect() as con:
        with con.cursor() as cur:
            cur.execute(
                "SELECT pair, intervention_level, caution_band, regime, verified_through "
                "FROM intervention_watch WHERE pair = %s",
                (pair,),
            )
            row = cur.fetchone()
            if not row:
                return None
            cols = [d.name for d in cur.description]
            data = dict(zip(cols, row))
            cur.execute(
                "SELECT event_date, official, quote FROM intervention_jawboning "
                "WHERE pair = %s ORDER BY event_date DESC",
                (pair,),
            )
            data["jawboning"] = [
                {"date": r[0], "official": r[1], "quote": r[2]} for r in cur.fetchall()
            ]
    return data


def main() -> int:
    ap = argparse.ArgumentParser(description="JPY intervention / jawboning watch")
    ap.add_argument("--instrument", required=True, choices=JPY_PAIRS)
    ap.add_argument("--spot", type=float, required=True, help="current spot price of the pair")
    ap.add_argument("--date", help="YYYY-MM-DD (default: today UTC)")
    ap.add_argument("--days", type=int, default=10, help="jawboning lookback window (default 10)")
    args = ap.parse_args()

    pair = load_pair(args.instrument)
    if not pair:
        print(f"❌ {args.instrument} not in intervention_watch table — "
              f"run ops/import_calendar_json_to_db.py or insert a row before trading JPY.")
        return 1

    today = (datetime.strptime(args.date, "%Y-%m-%d").date() if args.date
             else datetime.now(timezone.utc).date())
    level = float(pair["intervention_level"])
    band = float(pair["caution_band"])
    spot = args.spot

    if spot >= level:
        verdict = "🛑 HARD_BLOCK new longs — spot in active MoF intervention zone"
    elif spot >= level - band:
        verdict = "⚠ CAUTION — spot in intervention band; cap LONG conviction MEDIUM"
    else:
        verdict = "✅ clear of intervention band"

    cutoff = today - timedelta(days=args.days)
    recent = [j for j in pair["jawboning"] if j["date"] and j["date"] >= cutoff]

    print(f"Intervention watch — {args.instrument} @ {spot} (as of {today})")
    print(f"   level {level} | caution band {level - band}–{level} | regime {pair.get('regime','?')}")
    print(f"   {verdict}")
    if recent:
        print(f"   jawboning (last {args.days}d) → CAUTION at minimum:")
        for j in recent:
            print(f"     {j['date']} {j.get('official','?')}: \"{j.get('quote','')}\"")
    else:
        print(f"   no jawboning in last {args.days}d")

    vt = pair["verified_through"]
    if vt and today > vt:
        print(f"\n❌ watch verified only through {vt} — insert refreshed {args.instrument} "
              f"jawboning rows and push verified_through forward before trusting this.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
