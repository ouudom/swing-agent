#!/usr/bin/env python3
from __future__ import annotations

import os

try:
    import psycopg
except ImportError as exc:
    raise SystemExit("psycopg missing. Run inside container or `bash scripts/pyrun.sh --setup`.") from exc


DDL = [
    """
    CREATE TABLE IF NOT EXISTS validation_verdict (
      zone_id text NOT NULL REFERENCES zone_ledger(zone_id) ON DELETE CASCADE,
      validation_date date NOT NULL,
      run_id text NOT NULL,
      instrument text NOT NULL,
      verdict text NOT NULL,
      entry_confluence double precision,
      limit_price double precision,
      hard_block_flags text,
      reason text,
      source_file text,
      created_utc timestamptz NOT NULL DEFAULT now(),
      updated_utc timestamptz NOT NULL DEFAULT now(),
      payload jsonb NOT NULL DEFAULT '{}'::jsonb,
      PRIMARY KEY (zone_id, validation_date, run_id)
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_validation_verdict_instrument_date ON validation_verdict (instrument, validation_date)",
    """
    CREATE TABLE IF NOT EXISTS notification_event (
      event_id text PRIMARY KEY,
      event_type text NOT NULL,
      instrument text,
      zone_id text,
      title text NOT NULL,
      message text NOT NULL,
      status text NOT NULL DEFAULT 'pending',
      created_utc timestamptz NOT NULL DEFAULT now(),
      sent_utc timestamptz,
      error text,
      payload jsonb NOT NULL DEFAULT '{}'::jsonb
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_notification_event_status_created ON notification_event (status, created_utc)",
    """
    CREATE TABLE IF NOT EXISTS routine_checkpoint (
      routine_name text PRIMARY KEY,
      status text NOT NULL,
      last_run_utc timestamptz,
      branch text,
      commit_sha text,
      notes text,
      updated_utc timestamptz NOT NULL DEFAULT now()
    )
    """,
    "ALTER TABLE zone_ledger ADD COLUMN IF NOT EXISTS replay_status text",
    """
    CREATE TABLE IF NOT EXISTS trade_log (
      zone_id text PRIMARY KEY REFERENCES zone_ledger(zone_id) ON DELETE CASCADE,
      instrument text NOT NULL,
      week text NOT NULL,
      label text,
      direction text,
      status text NOT NULL DEFAULT 'PENDING',
      entry_confluence double precision,
      limit_price double precision,
      sl_price double precision,
      tp_price double precision,
      hard_block_flags text,
      reason text,
      entry_price double precision,
      fill_time timestamptz,
      exit_price double precision,
      exit_time timestamptz,
      r_result double precision,
      validation_date date,
      run_id text,
      created_utc timestamptz NOT NULL DEFAULT now(),
      updated_utc timestamptz NOT NULL DEFAULT now()
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_trade_log_instrument_status ON trade_log (instrument, status)",
    """
    CREATE TABLE IF NOT EXISTS trigger_state (
      instrument text PRIMARY KEY,
      last_fired_h1 timestamptz,
      last_fire_reason text,
      updated_utc timestamptz NOT NULL DEFAULT now()
    )
    """,
]


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


def main() -> int:
    with connect() as con:
        with con.transaction():
            for stmt in DDL:
                con.execute(stmt)
    print("postgres migrations applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
