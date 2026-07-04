#!/usr/bin/env python3
"""
Backfill swing-agent Postgres from the current SQLite canonical store.

Run from repo root or swing-agent/src:
  python swing-agent/src/scripts/backfill_sqlite_to_postgres.py

Requires Postgres schema already initialized from postgres/init.sql.
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from pathlib import Path

import pandas as pd

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional convenience
    load_dotenv = None


TABLES = [
    "ohlc",
    "macro_series",
    "market_series",
    "ohlc_quarantine",
    "econ_calendar",
    "gld_holdings",
    "news",
    "zone_ledger",
    "zone_outcome",
    "trade_outcome",
]


def repo_root() -> Path:
    here = Path(__file__).resolve()
    return here.parents[2]


def load_env() -> None:
    if load_dotenv is None:
        return
    src_env = repo_root() / "swing-agent" / "src" / ".env"
    if src_env.exists():
        load_dotenv(src_env)


def pg_connect():
    try:
        import psycopg
    except ImportError as exc:
        raise SystemExit(
            "psycopg missing. Run `bash scripts/pyrun.sh --setup` after requirements update."
        ) from exc

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


def quote(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def clean_frame(df: pd.DataFrame) -> pd.DataFrame:
    return df.astype(object).where(pd.notna(df), None).replace({"": None})


def table_where(table: str) -> str:
    if table != "ohlc":
        return ""
    keys = ["source", "symbol", "tf", "datetime"]
    return "WHERE " + " AND ".join(f"COALESCE(CAST({quote(c)} AS TEXT), '') <> ''" for c in keys)


def insert_chunk(pg, table: str, df: pd.DataFrame) -> int:
    if df.empty:
        return 0
    df = clean_frame(df)
    cols = list(df.columns)
    col_sql = ", ".join(quote(c) for c in cols)
    placeholders = ", ".join(["%s"] * len(cols))
    sql = f"INSERT INTO {quote(table)} ({col_sql}) VALUES ({placeholders})"
    rows = [tuple(row) for row in df.itertuples(index=False, name=None)]
    with pg.cursor() as cur:
        cur.executemany(sql, rows)
    return len(rows)


def sqlite_count(sqlite_path: Path, table: str) -> int:
    with sqlite3.connect(sqlite_path) as con:
        where = table_where(table)
        return int(con.execute(f"SELECT COUNT(*) FROM {quote(table)} {where}").fetchone()[0])


def sqlite_skipped(sqlite_path: Path, table: str) -> int:
    if table != "ohlc":
        return 0
    with sqlite3.connect(sqlite_path) as con:
        total = int(con.execute(f"SELECT COUNT(*) FROM {quote(table)}").fetchone()[0])
    return total - sqlite_count(sqlite_path, table)


def backfill_table(sqlite_path: Path, pg, table: str, chunk_size: int) -> int:
    total = 0
    with sqlite3.connect(sqlite_path) as sqlite:
        where = table_where(table)
        sql = f"SELECT * FROM {quote(table)} {where}"
        for chunk in pd.read_sql_query(sql, sqlite, chunksize=chunk_size):
            total += insert_chunk(pg, table, chunk)
    return total


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Backfill Postgres from SQLite canonical DB.")
    parser.add_argument("--sqlite", default=str(repo_root() / "data" / "database" / "index.db"))
    parser.add_argument("--tables", nargs="*", default=TABLES)
    parser.add_argument("--chunk-size", type=int, default=5000)
    parser.add_argument("--no-truncate", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    sqlite_path = Path(args.sqlite)
    if not sqlite_path.exists():
        raise SystemExit(f"SQLite DB not found: {sqlite_path}")

    unknown = sorted(set(args.tables) - set(TABLES))
    if unknown:
        raise SystemExit(f"Unknown table(s): {', '.join(unknown)}")

    load_env()
    counts = {table: sqlite_count(sqlite_path, table) for table in args.tables}
    for table in args.tables:
        skipped = sqlite_skipped(sqlite_path, table)
        suffix = f" skipped_invalid={skipped}" if skipped else ""
        print(f"{table}: sqlite rows={counts[table]}{suffix}")
    if args.dry_run:
        return 0

    pg = pg_connect()
    try:
        with pg.transaction():
            if not args.no_truncate:
                joined = ", ".join(quote(t) for t in args.tables)
                pg.execute(f"TRUNCATE {joined}")
            for table in args.tables:
                inserted = backfill_table(sqlite_path, pg, table, args.chunk_size)
                print(f"{table}: inserted={inserted}")
                if inserted != counts[table]:
                    raise RuntimeError(f"{table}: inserted {inserted}, expected {counts[table]}")
    finally:
        pg.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
