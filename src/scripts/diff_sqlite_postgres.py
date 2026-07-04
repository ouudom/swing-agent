#!/usr/bin/env python3
"""
Compare SQLite canonical store against auto-swing Postgres.

Checks row counts, min/max key ranges, and deterministic sample hashes.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sqlite3
import sys
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None


TABLES = {
    "ohlc": ["source", "symbol", "tf", "datetime"],
    "macro_series": ["series_id", "date"],
    "market_series": ["source", "symbol", "date"],
    "ohlc_quarantine": ["symbol", "tf", "datetime", "action"],
    "econ_calendar": ["date", "country", "event"],
    "gld_holdings": ["date"],
    "news": ["datetime_utc", "source", "headline"],
    "zone_ledger": ["zone_id"],
    "zone_outcome": ["zone_id"],
    "trade_outcome": ["zone_id"],
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_env() -> None:
    if load_dotenv is None:
        return
    src_env = repo_root() / "auto-swing" / "src" / ".env"
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
        dbname=os.getenv("POSTGRES_DB", "auto_swing"),
        user=os.getenv("POSTGRES_USER", "auto_swing"),
        password=os.getenv("POSTGRES_PASSWORD", "auto_swing_dev_password"),
    )


def quote(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def key_sql(cols: list[str]) -> str:
    return " || '|' || ".join(f"COALESCE(CAST({quote(c)} AS TEXT), '')" for c in cols)


def table_where(table: str) -> str:
    if table != "ohlc":
        return ""
    keys = ["source", "symbol", "tf", "datetime"]
    return "WHERE " + " AND ".join(f"COALESCE(CAST({quote(c)} AS TEXT), '') <> ''" for c in keys)


def norm(value) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        if value.tzinfo is not None:
            value = value.astimezone(timezone.utc).replace(tzinfo=None)
        return value.isoformat(sep=" ")
    if isinstance(value, date):
        return value.isoformat()
    text = str(value)
    text = (
        text.replace("T", " ")
        .replace("Z|", "|")
        .replace("+00|", "|")
        .replace("+00:00|", "|")
        .removesuffix("Z")
        .removesuffix("+00")
        .removesuffix("+00:00")
        .removesuffix(" UTC")
    )
    try:
        if text and all(ch in "0123456789+-.eE" for ch in text):
            return format(Decimal(text).normalize(), "f")
    except InvalidOperation:
        pass
    return text


def sqlite_scalar(con, sql: str):
    return con.execute(sql).fetchone()[0]


def pg_scalar(con, sql: str):
    return con.execute(sql).fetchone()[0]


def sample_rows(con, backend: str, table: str, key_cols: list[str], limit: int):
    order = ", ".join(quote(c) for c in key_cols)
    where = table_where(table)
    sql = f"SELECT * FROM {quote(table)} {where} ORDER BY {order} LIMIT {limit}"
    if backend == "sqlite":
        cur = con.execute(sql)
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
    else:
        cur = con.execute(sql)
        cols = [d.name for d in cur.description]
        rows = cur.fetchall()
    return cols, rows


def sample_hash(con, backend: str, table: str, key_cols: list[str], limit: int) -> str:
    cols, rows = sample_rows(con, backend, table, key_cols, limit)
    h = hashlib.sha256()
    h.update("|".join(cols).encode())
    for row in rows:
        h.update(b"\n")
        h.update("|".join(norm(v) for v in row).encode())
    return h.hexdigest()


def table_check(sqlite, pg, table: str, key_cols: list[str], limit: int) -> tuple[bool, str]:
    where = table_where(table)
    sqlite_count = sqlite_scalar(sqlite, f"SELECT COUNT(*) FROM {quote(table)} {where}")
    pg_count = pg_scalar(pg, f"SELECT COUNT(*) FROM {quote(table)} {where}")
    key_expr = key_sql(key_cols)
    sqlite_min = sqlite_scalar(sqlite, f"SELECT MIN({key_expr}) FROM {quote(table)} {where}")
    sqlite_max = sqlite_scalar(sqlite, f"SELECT MAX({key_expr}) FROM {quote(table)} {where}")
    pg_min = pg_scalar(pg, f"SELECT MIN({key_expr}) FROM {quote(table)} {where}")
    pg_max = pg_scalar(pg, f"SELECT MAX({key_expr}) FROM {quote(table)} {where}")
    sqlite_hash = sample_hash(sqlite, "sqlite", table, key_cols, limit)
    pg_hash = sample_hash(pg, "postgres", table, key_cols, limit)
    ok = (
        sqlite_count == pg_count
        and norm(sqlite_min) == norm(pg_min)
        and norm(sqlite_max) == norm(pg_max)
        and sqlite_hash == pg_hash
    )
    msg = (
        f"{table}: count {sqlite_count}/{pg_count}; "
        f"min {sqlite_min}/{pg_min}; max {sqlite_max}/{pg_max}; "
        f"sample {sqlite_hash[:12]}/{pg_hash[:12]}"
    )
    return ok, msg


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Diff SQLite and Postgres stores.")
    parser.add_argument("--sqlite", default=str(repo_root() / "data" / "database" / "index.db"))
    parser.add_argument("--tables", nargs="*", default=list(TABLES))
    parser.add_argument("--sample", type=int, default=200)
    args = parser.parse_args(argv)

    sqlite_path = Path(args.sqlite)
    if not sqlite_path.exists():
        raise SystemExit(f"SQLite DB not found: {sqlite_path}")
    unknown = sorted(set(args.tables) - set(TABLES))
    if unknown:
        raise SystemExit(f"Unknown table(s): {', '.join(unknown)}")

    load_env()
    failures = 0
    with sqlite3.connect(sqlite_path) as sqlite, pg_connect() as pg:
        for table in args.tables:
            ok, msg = table_check(sqlite, pg, table, TABLES[table], args.sample)
            print(("OK " if ok else "BAD ") + msg)
            failures += 0 if ok else 1
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
