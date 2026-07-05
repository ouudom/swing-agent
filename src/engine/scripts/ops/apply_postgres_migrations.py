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
    # Phase 1: wiki prose → DB. Split by type; doc_history keeps the version trail.
    """
    CREATE TABLE IF NOT EXISTS rulebook (
      doc_key text PRIMARY KEY,
      scope text NOT NULL,
      instrument text,
      kind text NOT NULL,
      title text,
      body text NOT NULL,
      frontmatter jsonb NOT NULL DEFAULT '{}'::jsonb,
      source_path text,
      version int NOT NULL DEFAULT 1,
      updated_utc timestamptz NOT NULL DEFAULT now()
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_rulebook_kind_instrument ON rulebook (kind, instrument)",
    """
    CREATE TABLE IF NOT EXISTS context_doc (
      doc_key text PRIMARY KEY,
      kind text NOT NULL,
      title text,
      body text NOT NULL,
      frontmatter jsonb NOT NULL DEFAULT '{}'::jsonb,
      source_path text,
      version int NOT NULL DEFAULT 1,
      updated_utc timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS forecast_doc (
      doc_key text PRIMARY KEY,
      instrument text NOT NULL,
      week text NOT NULL,
      title text,
      body text NOT NULL,
      frontmatter jsonb NOT NULL DEFAULT '{}'::jsonb,
      generated date,
      source_path text,
      version int NOT NULL DEFAULT 1,
      updated_utc timestamptz NOT NULL DEFAULT now()
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_forecast_doc_instrument_week ON forecast_doc (instrument, week)",
    """
    CREATE TABLE IF NOT EXISTS validation_doc (
      doc_key text PRIMARY KEY,
      instrument text NOT NULL,
      valid_date date NOT NULL,
      week text,
      title text,
      body text NOT NULL,
      frontmatter jsonb NOT NULL DEFAULT '{}'::jsonb,
      source_path text,
      version int NOT NULL DEFAULT 1,
      updated_utc timestamptz NOT NULL DEFAULT now()
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_validation_doc_instrument_date ON validation_doc (instrument, valid_date)",
    """
    CREATE TABLE IF NOT EXISTS doc_history (
      source_table text NOT NULL,
      doc_key text NOT NULL,
      version int NOT NULL,
      body text NOT NULL,
      frontmatter jsonb NOT NULL DEFAULT '{}'::jsonb,
      saved_utc timestamptz NOT NULL DEFAULT now(),
      PRIMARY KEY (source_table, doc_key, version)
    )
    """,
    # Phase 2: static config JSON (cb_calendar / intervention_watch) → DB.
    """
    CREATE TABLE IF NOT EXISTS cb_calendar (
      bank_code text PRIMARY KEY,
      name text NOT NULL,
      time_note text,
      hard_block text[] NOT NULL DEFAULT '{}',
      caution text[] NOT NULL DEFAULT '{}',
      dates jsonb NOT NULL DEFAULT '[]'::jsonb,
      verified_through date,
      updated_utc timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS intervention_watch (
      pair text PRIMARY KEY,
      intervention_level double precision NOT NULL,
      caution_band double precision NOT NULL,
      regime text,
      verified_through date,
      updated_utc timestamptz NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS intervention_jawboning (
      pair text NOT NULL REFERENCES intervention_watch(pair) ON DELETE CASCADE,
      event_date date NOT NULL,
      official text,
      quote text,
      source text,
      created_utc timestamptz NOT NULL DEFAULT now(),
      PRIMARY KEY (pair, event_date, official)
    )
    """,
    # Phase 3: frozen feature vector per decision (R1 at publish, R2 at validate).
    """
    CREATE TABLE IF NOT EXISTS feature_snapshot (
      snap_id text PRIMARY KEY,
      zone_id text NOT NULL REFERENCES zone_ledger(zone_id) ON DELETE CASCADE,
      instrument text NOT NULL,
      event_type text NOT NULL,
      event_utc timestamptz NOT NULL DEFAULT now(),
      features jsonb NOT NULL,
      created_utc timestamptz NOT NULL DEFAULT now()
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_feature_snapshot_zone ON feature_snapshot (zone_id, event_type)",
    "CREATE INDEX IF NOT EXISTS ix_feature_snapshot_instrument_event ON feature_snapshot (instrument, event_type, event_utc)",
    # Comparison table: same zone_outcome replay, SL = constitution ATR formula
    # instead of zone width. Does NOT drive zone_ledger.status.
    """
    CREATE TABLE IF NOT EXISTS zone_atr_sl_outcome (
      zone_id text PRIMARY KEY,
      instrument text NOT NULL,
      week text NOT NULL,
      label text,
      direction text,
      zone_confluence double precision,
      conviction text,
      status text,
      touched integer,
      fill_time timestamptz,
      entry double precision,
      sl_dist double precision,
      r_result double precision,
      mfe_r double precision,
      mae_r double precision,
      exit_time timestamptz,
      resolved_utc timestamptz
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_zone_atr_sl_outcome_instrument_week ON zone_atr_sl_outcome (instrument, week)",
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
