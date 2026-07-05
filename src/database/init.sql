-- auto-swing Postgres schema
-- Source: data/database/index.db schema inventory on 2026-07-04.
-- Excludes SQLite `lost_and_found` recovery artifact.

CREATE TABLE IF NOT EXISTS ohlc (
  source text NOT NULL,
  symbol text NOT NULL,
  tf text NOT NULL,
  datetime timestamptz NOT NULL,
  open double precision,
  high double precision,
  low double precision,
  close double precision,
  volume double precision,
  PRIMARY KEY (source, symbol, tf, datetime)
);

CREATE INDEX IF NOT EXISTS ix_ohlc_symbol_tf_datetime
  ON ohlc (symbol, tf, datetime);

CREATE TABLE IF NOT EXISTS macro_series (
  series_id text NOT NULL,
  date date NOT NULL,
  value double precision,
  PRIMARY KEY (series_id, date)
);

CREATE TABLE IF NOT EXISTS market_series (
  source text NOT NULL,
  symbol text NOT NULL,
  date date NOT NULL,
  value double precision,
  PRIMARY KEY (source, symbol, date)
);

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
);

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
);

CREATE INDEX IF NOT EXISTS ix_econ_calendar_date_country
  ON econ_calendar (date, country);

CREATE TABLE IF NOT EXISTS gld_holdings (
  date date PRIMARY KEY,
  tonnes double precision,
  aum_usd double precision,
  spot double precision
);

CREATE TABLE IF NOT EXISTS cot (
  contract text NOT NULL,
  date date NOT NULL,
  long bigint,
  short bigint,
  net bigint,
  net_prev bigint,
  PRIMARY KEY (contract, date)
);

CREATE TABLE IF NOT EXISTS news (
  datetime_utc timestamptz NOT NULL,
  category text,
  headline text NOT NULL,
  source text NOT NULL,
  url text,
  summary text,
  related text,
  PRIMARY KEY (datetime_utc, source, headline)
);

CREATE INDEX IF NOT EXISTS ix_news_datetime_category
  ON news (datetime_utc, category);

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
);

CREATE INDEX IF NOT EXISTS ix_zone_ledger_instrument_week
  ON zone_ledger (instrument, week);

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
);

CREATE INDEX IF NOT EXISTS ix_zone_outcome_instrument_week
  ON zone_outcome (instrument, week);

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
);

CREATE INDEX IF NOT EXISTS ix_trade_outcome_instrument_week
  ON trade_outcome (instrument, week);

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
);

CREATE INDEX IF NOT EXISTS ix_pipeline_run_job_started
  ON pipeline_run (job_name, started_utc);

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
);

CREATE INDEX IF NOT EXISTS ix_validation_verdict_instrument_date
  ON validation_verdict (instrument, validation_date);

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
);

CREATE INDEX IF NOT EXISTS ix_notification_event_status_created
  ON notification_event (status, created_utc);

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
);

CREATE INDEX IF NOT EXISTS ix_trade_log_instrument_status
  ON trade_log (instrument, status);

CREATE TABLE IF NOT EXISTS routine_checkpoint (
  routine_name text PRIMARY KEY,
  status text NOT NULL,
  last_run_utc timestamptz,
  branch text,
  commit_sha text,
  notes text,
  updated_utc timestamptz NOT NULL DEFAULT now()
);
