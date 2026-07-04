"""
db.py — shared DB access for the canonical store.

Default backend remains SQLite (`data/database/index.db`). Set `SWING_DB_BACKEND=postgres`
to use Postgres with the same public helpers. Reads still return CSV-shaped all-string
frames; writes accept the existing all-string frames and let Postgres cast typed columns.

Used by: zone_ledger.py, zone_outcomes.py, trade_outcome.py, fetch_data.py,
ohlc_store.py. Tables are written live by those scripts — there is no CSV import step.
"""
from __future__ import annotations

import os
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

DB = Path("data/database/index.db")
BACKEND = os.getenv("SWING_DB_BACKEND", "sqlite").lower()

# Index set for the state tables — re-applied after every replace.
INDEXES = {
    "zone_ledger": [("instrument", "week")],
    "zone_outcome": [("instrument", "week")],
    "trade_outcome": [("instrument", "week")],
}


def _sqlite_con() -> sqlite3.Connection:
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB, timeout=30)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=30000")  # wait, don't error, on a held write lock
    con.execute("PRAGMA synchronous=NORMAL")  # WAL-safe durability without fsync per commit
    return con


def _pg_con():
    try:
        import psycopg
    except ImportError as exc:
        raise RuntimeError(
            "SWING_DB_BACKEND=postgres requires psycopg. Run `bash scripts/pyrun.sh --setup`."
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


def _con():
    return _pg_con() if BACKEND == "postgres" else _sqlite_con()


def _empty(columns) -> pd.DataFrame:
    if columns:
        return pd.DataFrame({c: pd.Series(dtype=str) for c in columns})
    return pd.DataFrame()


def _q(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _ph() -> str:
    return "%s" if BACKEND == "postgres" else "?"


def _to_string_frame(rows, columns) -> pd.DataFrame:
    df = pd.DataFrame(rows, columns=columns)
    return df.map(_format_cell).where(df.notna(), "").astype(str)


def _format_cell(value):
    if pd.isna(value):
        return ""
    if isinstance(value, datetime):
        if value.tzinfo is not None:
            value = value.astimezone(timezone.utc).replace(tzinfo=None)
        return value.isoformat(sep=" ")
    if isinstance(value, date):
        return value.isoformat()
    return value


def _pg_read_sql(con, sql: str, params=()) -> pd.DataFrame:
    with con.cursor() as cur:
        cur.execute(sql, params)
        columns = [d.name for d in cur.description]
        return _to_string_frame(cur.fetchall(), columns)


def _read_sql(con, sql: str, params=()) -> pd.DataFrame:
    if BACKEND == "postgres":
        return _pg_read_sql(con, sql, params)
    return pd.read_sql_query(sql, con, params=params)


def _clean_cell(value):
    if pd.isna(value) or value == "":
        return None if BACKEND == "postgres" else ""
    if BACKEND == "postgres" and (isinstance(value, bool) or value.__class__.__name__ == "bool_"):
        return int(value)
    if BACKEND == "postgres" and value in ("True", "False"):
        return 1 if value == "True" else 0
    return str(value)


def _insert_df(con, table: str, df: pd.DataFrame):
    if df.empty:
        return
    cols = list(df.columns)
    col_sql = ", ".join(_q(c) for c in cols)
    ph = ", ".join([_ph()] * len(cols))
    rows = [tuple(_clean_cell(v) for v in row) for row in df.itertuples(index=False, name=None)]
    sql = f"INSERT INTO {_q(table)} ({col_sql}) VALUES ({ph})"
    if BACKEND == "postgres":
        with con.cursor() as cur:
            cur.executemany(sql, rows)
    else:
        con.executemany(sql, rows)


def table_exists(con, table: str) -> bool:
    if BACKEND == "postgres":
        row = con.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='public' AND table_name=%s",
            (table,),
        ).fetchone()
    else:
        row = con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ).fetchone()
    return row is not None


def read_table(table: str, columns=None) -> pd.DataFrame:
    """Read a table as all-string (NULL→''). Missing DB/table → empty frame."""
    if BACKEND != "postgres" and not DB.exists():
        return _empty(columns)
    con = _con()
    try:
        if not table_exists(con, table):
            return _empty(columns)
        df = _read_sql(con, f"SELECT * FROM {_q(table)}")
    finally:
        con.close()
    df = df.where(df.notna(), "").astype(str)
    if columns:                       # tolerate older/narrower stored schema
        for c in columns:
            if c not in df.columns:
                df[c] = ""
    return df


def write_table(table: str, df: pd.DataFrame, mirror_csv=None, columns=None):
    """Replace `table` with df, re-apply indexes, then dump the CSV mirror."""
    if columns:
        df = df[columns]
    con = _con()
    try:
        if BACKEND == "postgres":
            with con.transaction():
                con.execute(f"DELETE FROM {_q(table)}")
                _insert_df(con, table, df)
        else:
            df.to_sql(table, con, if_exists="replace", index=False)
        for cols in INDEXES.get(table, []):
            idx = f"ix_{table}_{'_'.join(cols)}"
            con.execute(
                f'CREATE INDEX IF NOT EXISTS "{idx}" ON {_q(table)} ({", ".join(_q(c) for c in cols)})'
            )
        con.commit()
    finally:
        con.close()
    if mirror_csv:
        mirror_csv = Path(mirror_csv)
        mirror_csv.parent.mkdir(parents=True, exist_ok=True)
        tmp = str(mirror_csv) + ".tmp"
        df.to_csv(tmp, index=False)
        Path(tmp).replace(mirror_csv)


OHLC_COLUMNS = ["source", "symbol", "tf", "datetime", "open", "high", "low", "close", "volume"]


# ── reader helpers (return CSV-shaped frames; callers parse dtypes as before) ──

def clean_symbol(symbol: str) -> str:
    """Canonical ohlc-table symbol form: lowercase, no slash (e.g. EUR/USD → eurusd)."""
    return symbol.lower().replace("/", "")


def read_ohlc(symbol: str, tf: str, source: str = "twelvedata") -> pd.DataFrame:
    """Bars for one (source,symbol,tf) as columns datetime,open,high,low,close,volume
    (strings — caller parses). Empty frame if absent → caller can CSV-fallback."""
    symbol = clean_symbol(symbol)
    if BACKEND != "postgres" and not DB.exists():
        return _empty(["datetime", "open", "high", "low", "close", "volume"])
    con = _con()
    try:
        if not table_exists(con, "ohlc"):
            return _empty(["datetime", "open", "high", "low", "close", "volume"])
        df = _read_sql(
            con,
            "SELECT datetime,open,high,low,close,volume FROM ohlc "
            f"WHERE source={_ph()} AND symbol={_ph()} AND tf={_ph()} ORDER BY datetime",
            (source, symbol, tf),
        )
    finally:
        con.close()
    return df


def last_ohlc_dt(symbol: str, tf: str, source: str = "twelvedata"):
    """MAX(datetime) for one ohlc slice as a string, or None. Replaces the _manifest.json bookmark."""
    symbol = clean_symbol(symbol)
    if BACKEND != "postgres" and not DB.exists():
        return None
    con = _con()
    try:
        if not table_exists(con, "ohlc"):
            return None
        row = con.execute(
            f"SELECT MAX(datetime) FROM ohlc WHERE source={_ph()} AND symbol={_ph()} AND tf={_ph()}",
            (source, symbol, tf),
        ).fetchone()
    finally:
        con.close()
    return row[0] if row and row[0] else None


def last_series_date(table: str, where: dict):
    """MAX(date) for a macro_series/market_series slice as a string, or None."""
    if BACKEND != "postgres" and not DB.exists():
        return None
    con = _con()
    try:
        if not table_exists(con, table):
            return None
        clause = " AND ".join(f"{_q(k)}={_ph()}" for k in where)
        row = con.execute(
            f"SELECT MAX(date) FROM {_q(table)} WHERE {clause}", tuple(where.values())
        ).fetchone()
    finally:
        con.close()
    return row[0] if row and row[0] else None


def read_slice(table: str, where: dict, cols: list[str]) -> pd.DataFrame:
    """Generic slice read: SELECT cols FROM table WHERE <where> ORDER BY cols[0]."""
    blank = _empty(cols)
    if BACKEND != "postgres" and not DB.exists():
        return blank
    con = _con()
    try:
        if not table_exists(con, table):
            return blank
        clause = " AND ".join(f"{_q(k)}={_ph()}" for k in where)
        df = _read_sql(
            con,
            f"SELECT {','.join(_q(c) for c in cols)} FROM {_q(table)} "
            f'{"WHERE " + clause if where else ""} ORDER BY {_q(cols[0])}',
            tuple(where.values()),
        )
    finally:
        con.close()
    return df


# ── DB-live sync helpers (canonical = DB; CSV mirror written by caller) ────────

def sync_slice(table: str, where: dict, df: pd.DataFrame, index_cols=None):
    """Replace the `where` slice of `table` with df (df already carries the key cols).
    Fail-soft is the CALLER's job. Used for macro_series/market_series per-series sync."""
    out = df.astype(str)
    con = _con()
    try:
        if BACKEND == "postgres":
            with con.transaction():
                clause = " AND ".join(f"{_q(k)}={_ph()}" for k in where)
                con.execute(f"DELETE FROM {_q(table)} WHERE {clause}", tuple(where.values()))
                _insert_df(con, table, out)
        else:
            if table_exists(con, table):
                clause = " AND ".join(f"{k}=?" for k in where)
                con.execute(f'DELETE FROM "{table}" WHERE {clause}', tuple(where.values()))
                out.to_sql(table, con, if_exists="append", index=False)
            else:
                out.to_sql(table, con, if_exists="replace", index=False)
            con.commit()
        if index_cols and BACKEND != "postgres":
            idx = f"ix_{table}_{'_'.join(index_cols)}"
            con.execute(f'CREATE INDEX IF NOT EXISTS "{idx}" ON "{table}" ({", ".join(index_cols)})')
            con.commit()
    finally:
        con.close()


def sync_table(table: str, df: pd.DataFrame):
    """Replace a whole single-file table (gld_holdings/news/econ_calendar) from df.
    Fail-soft is the CALLER's job."""
    con = _con()
    try:
        out = df.astype(str)
        if BACKEND == "postgres":
            with con.transaction():
                con.execute(f"DELETE FROM {_q(table)}")
                _insert_df(con, table, out)
        else:
            out.to_sql(table, con, if_exists="replace", index=False)
            con.commit()
    finally:
        con.close()


def replace_ohlc_slice(source: str, symbol: str, tf: str, bars: pd.DataFrame):
    """Replace the (source,symbol,tf) slice of the `ohlc` table with `bars`.

    `bars` carries datetime+open/high/low/close/volume for one series; source/symbol/tf
    are prepended. Values stored as text (the all-string convention used across the DB,
    so reads round-trip exactly). Called by ohlc_store.upsert.
    """
    symbol = clean_symbol(symbol)
    df = bars.copy()
    df.insert(0, "tf", tf)
    df.insert(0, "symbol", symbol)
    df.insert(0, "source", source)
    df = df[OHLC_COLUMNS].astype(str)
    con = _con()
    try:
        if BACKEND == "postgres":
            with con.transaction():
                con.execute(
                    f"DELETE FROM ohlc WHERE source={_ph()} AND symbol={_ph()} AND tf={_ph()}",
                    (source, symbol, tf),
                )
                _insert_df(con, "ohlc", df)
        else:
            if table_exists(con, "ohlc"):
                con.execute(
                    "DELETE FROM ohlc WHERE source=? AND symbol=? AND tf=?",
                    (source, symbol, tf),
                )
                df.to_sql("ohlc", con, if_exists="append", index=False)
            else:
                df.to_sql("ohlc", con, if_exists="replace", index=False)
            con.execute(
                "CREATE INDEX IF NOT EXISTS ix_ohlc_symbol_tf_datetime "
                "ON ohlc (symbol, tf, datetime)"
            )
            con.commit()
    finally:
        con.close()
