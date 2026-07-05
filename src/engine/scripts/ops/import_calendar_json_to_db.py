#!/usr/bin/env python3
"""
import_calendar_json_to_db.py — one-shot: load cb_calendar_{year}.json and
intervention_watch.json into Postgres (Phase 2). Idempotent — re-running upserts.

After this runs clean, check_cb_calendar.py / check_intervention_watch.py read Postgres
instead of the JSON files; the JSON files become inputs to this importer only (or can be
retired once Claude edits the tables directly via sql_query / a future write tool).

Run inside the pipeline container:
  docker compose run --rm pipeline python src/engine/scripts/ops/import_calendar_json_to_db.py
Add --dry-run to preview without writing. --year selects which cb_calendar_{year}.json (default:
every cb_calendar_*.json found in config/).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path


def repo_root() -> Path:
    override = os.getenv("SWING_AGENT_REPO_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    return Path(__file__).resolve().parents[4]


def config_dir() -> Path:
    return repo_root() / "src" / "engine" / "scripts" / "config"


def connect():
    try:
        import psycopg
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("psycopg missing. Run inside the pipeline container.") from exc
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


def load_cb_calendars() -> list[dict]:
    rows = []
    for path in sorted(config_dir().glob("cb_calendar_*.json")):
        cal = json.loads(path.read_text())
        for code, bank in cal.get("banks", {}).items():
            rows.append({
                "bank_code": code,
                "name": bank["name"],
                "time_note": bank.get("time_note"),
                "hard_block": bank.get("hard_block", []),
                "caution": bank.get("caution", []),
                "dates": bank.get("dates", []),
                "verified_through": bank.get("verified_through"),
                "_source": path.name,
            })
    return rows


def load_intervention_watch() -> tuple[list[dict], list[dict]]:
    path = config_dir() / "intervention_watch.json"
    if not path.exists():
        return [], []
    cfg = json.loads(path.read_text())
    pairs, jawboning = [], []
    for pair, data in cfg.get("pairs", {}).items():
        pairs.append({
            "pair": pair,
            "intervention_level": data["intervention_level"],
            "caution_band": data["caution_band"],
            "regime": data.get("regime"),
            "verified_through": data.get("verified_through"),
        })
        for j in data.get("jawboning", []):
            jawboning.append({
                "pair": pair,
                "event_date": j["date"],
                "official": j.get("official"),
                "quote": j.get("quote"),
                "source": j.get("source"),
            })
    return pairs, jawboning


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    banks = load_cb_calendars()
    pairs, jawboning = load_intervention_watch()

    print(f"cb_calendar: {len(banks)} bank rows")
    for b in banks:
        print(f"  {b['bank_code']:6s} hard_block={b['hard_block']} caution={b['caution']} "
              f"dates={len(b['dates'])} <- {b['_source']}")
    print(f"\nintervention_watch: {len(pairs)} pairs, {len(jawboning)} jawboning rows")
    for p in pairs:
        print(f"  {p['pair']:8s} level={p['intervention_level']} band={p['caution_band']} "
              f"regime={p['regime']}")

    if args.dry_run:
        print("\n[dry-run] no writes")
        return 0

    with connect() as con:
        with con.transaction():
            for b in banks:
                con.execute(
                    """
                    INSERT INTO cb_calendar (bank_code, name, time_note, hard_block, caution, dates, verified_through)
                    VALUES (%s,%s,%s,%s,%s,%s::jsonb,%s)
                    ON CONFLICT (bank_code) DO UPDATE SET
                      name = EXCLUDED.name, time_note = EXCLUDED.time_note,
                      hard_block = EXCLUDED.hard_block, caution = EXCLUDED.caution,
                      dates = EXCLUDED.dates, verified_through = EXCLUDED.verified_through,
                      updated_utc = now()
                    """,
                    (b["bank_code"], b["name"], b["time_note"], b["hard_block"], b["caution"],
                     json.dumps(b["dates"]), b["verified_through"]),
                )
            for p in pairs:
                con.execute(
                    """
                    INSERT INTO intervention_watch (pair, intervention_level, caution_band, regime, verified_through)
                    VALUES (%s,%s,%s,%s,%s)
                    ON CONFLICT (pair) DO UPDATE SET
                      intervention_level = EXCLUDED.intervention_level,
                      caution_band = EXCLUDED.caution_band,
                      regime = EXCLUDED.regime,
                      verified_through = EXCLUDED.verified_through,
                      updated_utc = now()
                    """,
                    (p["pair"], p["intervention_level"], p["caution_band"], p["regime"], p["verified_through"]),
                )
            for j in jawboning:
                con.execute(
                    """
                    INSERT INTO intervention_jawboning (pair, event_date, official, quote, source)
                    VALUES (%s,%s,%s,%s,%s)
                    ON CONFLICT (pair, event_date, official) DO UPDATE SET
                      quote = EXCLUDED.quote, source = EXCLUDED.source
                    """,
                    (j["pair"], j["event_date"], j["official"], j["quote"], j["source"]),
                )
    print(f"\nimported {len(banks)} banks, {len(pairs)} pairs, {len(jawboning)} jawboning rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
