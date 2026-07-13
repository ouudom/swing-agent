"""baseline schema — mirrors src/database/init.sql verbatim

Revision ID: 0001_baseline
Revises:
Create Date: 2026-07-12

On an EXISTING deployment (schema already created by init.sql via the postgres
container's docker-entrypoint-initdb.d), do NOT run `alembic upgrade head` — it
would re-run CREATE TABLE IF NOT EXISTS harmlessly, but the point of this baseline
is to give Alembic a starting point without touching live data. Mark it applied
instead:

    alembic stamp 0001_baseline

On a FRESH database with no init.sql bootstrap, `alembic upgrade head` builds the
schema from scratch (every statement is idempotent — IF NOT EXISTS / ON CONFLICT).
Every statement here is copied verbatim from init.sql; do not hand-edit — regenerate
from init.sql if the two drift.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_baseline"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_ohlc_symbol_tf_datetime
  ON ohlc (symbol, tf, datetime)
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS macro_series (
  series_id text NOT NULL,
  date date NOT NULL,
  value double precision,
  PRIMARY KEY (series_id, date)
)
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS market_series (
  source text NOT NULL,
  symbol text NOT NULL,
  date date NOT NULL,
  value double precision,
  PRIMARY KEY (source, symbol, date)
)
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS ohlc_quarantine (
  symbol text NOT NULL,
  tf text NOT NULL,
  datetime timestamptz NOT NULL,
  action text NOT NULL,
  open double precision,
  high double precision,
  low double precision,
  close double precision,
  ref_close double precision,
  flagged_utc timestamptz,
  PRIMARY KEY (symbol, tf, datetime, action)
)
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS econ_calendar (
  date date NOT NULL,
  time_utc text,
  country text NOT NULL,
  event text NOT NULL,
  impact text,
  estimate text,
  actual text,
  prev text,
  unit text,
  PRIMARY KEY (date, country, event)
)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_econ_calendar_date_country
  ON econ_calendar (date, country)
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS gld_holdings (
  date date PRIMARY KEY,
  tonnes double precision,
  aum_usd double precision,
  spot double precision
)
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS cot (
  contract text NOT NULL,
  date date NOT NULL,
  long bigint,
  short bigint,
  net bigint,
  net_prev bigint,
  PRIMARY KEY (contract, date)
)
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS news (
  datetime_utc timestamptz NOT NULL,
  category text,
  headline text NOT NULL,
  source text NOT NULL,
  url text,
  summary text,
  related text,
  PRIMARY KEY (datetime_utc, source, headline)
)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_news_datetime_category
  ON news (datetime_utc, category)
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS zone_ledger (
  zone_id text PRIMARY KEY,
  instrument text NOT NULL,
  week text NOT NULL,
  label text NOT NULL,
  direction text NOT NULL,
  zone_bottom double precision,
  zone_top double precision,
  zone_confluence double precision,
  conviction text,
  invalidation_level double precision,
  tp_anchor double precision,
  published_utc timestamptz,
  source_file text,
  status text,
  notes text,
  replay_status text,
  entry_confluence double precision,
  daily_verdict text,
  limit_price double precision,
  validated_date date,
  anchor_set_utc timestamptz,
  anchor_locked_until timestamptz
)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_zone_ledger_instrument_week
  ON zone_ledger (instrument, week)
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS zone_outcome (
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
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_zone_outcome_instrument_week
  ON zone_outcome (instrument, week)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_zone_atr_sl_outcome_instrument_week
  ON zone_atr_sl_outcome (instrument, week)
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS trade_outcome (
  zone_id text PRIMARY KEY,
  instrument text NOT NULL,
  week text NOT NULL,
  label text,
  direction text,
  zone_confluence double precision,
  conviction text,
  status text,
  e0_present text,
  ec_score double precision,
  ec_flags text,
  anchor double precision,
  sl_dist double precision,
  "offset" double precision,
  limit_px double precision,
  entry double precision,
  fill_time timestamptz,
  r_result double precision,
  mfe_r double precision,
  mae_r double precision,
  exit_time timestamptz,
  block_flags text,
  block_verdict text,
  resolved_utc timestamptz
)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_trade_outcome_instrument_week
  ON trade_outcome (instrument, week)
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS pipeline_run (
  run_id text PRIMARY KEY,
  job_name text NOT NULL,
  instrument text,
  status text NOT NULL,
  started_utc timestamptz NOT NULL,
  finished_utc timestamptz,
  duration_s double precision,
  command text,
  returncode integer,
  stdout_tail text,
  stderr_tail text,
  error text
)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_pipeline_run_job_started
  ON pipeline_run (job_name, started_utc)
        """
    )
    op.execute(
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
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_validation_verdict_instrument_date
  ON validation_verdict (instrument, validation_date)
        """
    )
    op.execute(
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
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_notification_event_status_created
  ON notification_event (status, created_utc)
        """
    )
    op.execute(
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
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_trade_log_instrument_status
  ON trade_log (instrument, status)
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS trigger_state (
  instrument text PRIMARY KEY,
  last_fired_h1 timestamptz,
  last_fire_reason text,
  updated_utc timestamptz NOT NULL DEFAULT now()
)
        """
    )
    op.execute(
        """
        retires wiki/*.md as canonical).
-- "Postgres = canonical for every number" now extends to words. Split by TYPE so
-- each doc kind has its own lifecycle/keys
        """
    )
    op.execute(
        """
        doc_history keeps the version trail
-- that leaving git files would otherwise lose.
-- ─────────────────────────────────────────────────────────────────────────────

-- Human-authored reference rules (rarely change): constitution, setup_library,
-- currency_exposure, per-instrument profile + confluence_criteria, templates.
CREATE TABLE IF NOT EXISTS rulebook (
  doc_key text PRIMARY KEY,          -- 'constitution' | 'xauusd/profile' | 'xauusd/confluence' | 'template/weekly'
  scope text NOT NULL,               -- 'system' | 'instrument'
  instrument text,                   -- null for system scope
  kind text NOT NULL,                -- constitution|setup|currency|profile|confluence|template
  title text,
  body text NOT NULL,
  frontmatter jsonb NOT NULL DEFAULT '{}'::jsonb,
  source_path text,
  version int NOT NULL DEFAULT 1,
  updated_utc timestamptz NOT NULL DEFAULT now()
)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_rulebook_kind_instrument ON rulebook (kind, instrument)
        """
    )
    op.execute(
        """
        this is the words).
CREATE TABLE IF NOT EXISTS forecast_doc (
  doc_key text PRIMARY KEY,          -- '{week}/{instrument}' e.g. '2026-W27/xauusd'
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
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_forecast_doc_instrument_week ON forecast_doc (instrument, week)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_validation_doc_instrument_date ON validation_doc (instrument, valid_date)
        """
    )
    op.execute(
        """
        hard_block/
-- caution are the instrument lists that bank's decision affects
        """
    )
    op.execute(
        """
        dates is the JSON array
-- of {date, status} the checker scans within its lookahead window.
CREATE TABLE IF NOT EXISTS cb_calendar (
  bank_code text PRIMARY KEY,        -- 'FOMC' | 'ECB' | 'BoE' | 'BoJ' | 'SNB' | 'RBA' | 'RBNZ' | 'BoC'
  name text NOT NULL,
  time_note text,
  hard_block text[] NOT NULL DEFAULT '{}',
  caution text[] NOT NULL DEFAULT '{}',
  dates jsonb NOT NULL DEFAULT '[]'::jsonb,   -- [{"date":"2026-07-29","status":"confirmed"}, ...]
  verified_through date,
  updated_utc timestamptz NOT NULL DEFAULT now()
)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_feature_snapshot_zone ON feature_snapshot (zone_id, event_type)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_feature_snapshot_instrument_event ON feature_snapshot (instrument, event_type, event_utc)
        """
    )
    op.execute(
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
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS system_config (
  key text PRIMARY KEY,
  value text NOT NULL,
  updated_utc timestamptz NOT NULL DEFAULT now()
)
        """
    )
    op.execute(
        """
        INSERT INTO system_config (key, value) VALUES ('market_timezone', 'UTC') ON CONFLICT DO NOTHING
        """
    )


def downgrade() -> None:
    # Destructive and not expected to run against a live deployment — this baseline
    # exists to let Alembic track schema state, not to be rolled back on prod data.
    raise RuntimeError(
        "downgrade of the baseline migration is not supported — "
        "restore from a pg_dump snapshot instead"
    )
