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

-- Same replay as zone_outcome, but SL = constitution ATR formula instead of zone
-- width. Comparison-only: does NOT drive zone_ledger.status.
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
);

CREATE INDEX IF NOT EXISTS ix_zone_atr_sl_outcome_instrument_week
  ON zone_atr_sl_outcome (instrument, week);

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

CREATE TABLE IF NOT EXISTS trigger_state (
  instrument text PRIMARY KEY,
  last_fired_h1 timestamptz,
  last_fire_reason text,
  updated_utc timestamptz NOT NULL DEFAULT now()
);

-- ─────────────────────────────────────────────────────────────────────────────
-- Phase 1: wiki prose → DB (MCP-served context; retires wiki/*.md as canonical).
-- "Postgres = canonical for every number" now extends to words. Split by TYPE so
-- each doc kind has its own lifecycle/keys; doc_history keeps the version trail
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
);
CREATE INDEX IF NOT EXISTS ix_rulebook_kind_instrument ON rulebook (kind, instrument);

-- Regenerated snapshots (rewritten periodically by the pipeline / /weekly):
-- yield_environment (macro baseline), calibration (edge performance).
CREATE TABLE IF NOT EXISTS context_doc (
  doc_key text PRIMARY KEY,          -- 'yield_environment' | 'calibration'
  kind text NOT NULL,                -- macro | calibration
  title text,
  body text NOT NULL,
  frontmatter jsonb NOT NULL DEFAULT '{}'::jsonb,
  source_path text,
  version int NOT NULL DEFAULT 1,
  updated_utc timestamptz NOT NULL DEFAULT now()
);

-- Weekly forecast prose (numbers already in zone_ledger; this is the words).
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
);
CREATE INDEX IF NOT EXISTS ix_forecast_doc_instrument_week ON forecast_doc (instrument, week);

-- Daily/hourly validation prose (numbers already in validation_verdict).
CREATE TABLE IF NOT EXISTS validation_doc (
  doc_key text PRIMARY KEY,          -- '{date}/{instrument}' e.g. '2026-07-05/xauusd'
  instrument text NOT NULL,
  valid_date date NOT NULL,
  week text,
  title text,
  body text NOT NULL,
  frontmatter jsonb NOT NULL DEFAULT '{}'::jsonb,
  source_path text,
  version int NOT NULL DEFAULT 1,
  updated_utc timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_validation_doc_instrument_date ON validation_doc (instrument, valid_date);

-- Version trail across all four doc tables — replaces the git blame/diff you lose
-- by no longer keeping the .md files. write_doc archives the prior row here.
CREATE TABLE IF NOT EXISTS doc_history (
  source_table text NOT NULL,        -- 'rulebook' | 'context_doc' | 'forecast_doc' | 'validation_doc'
  doc_key text NOT NULL,
  version int NOT NULL,
  body text NOT NULL,
  frontmatter jsonb NOT NULL DEFAULT '{}'::jsonb,
  saved_utc timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (source_table, doc_key, version)
);

-- ─────────────────────────────────────────────────────────────────────────────
-- Phase 2: static config JSON → DB. Rebuilt/edited by Claude (web search during
-- /weekly JPY runs, yearly calendar rebuild) instead of hand-editing JSON files.
-- ─────────────────────────────────────────────────────────────────────────────

-- Central-bank decision calendar (check_cb_calendar.py). One row per bank; hard_block/
-- caution are the instrument lists that bank's decision affects; dates is the JSON array
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
);

-- JPY MoF intervention watch (check_intervention_watch.py). One row per JPY pair.
CREATE TABLE IF NOT EXISTS intervention_watch (
  pair text PRIMARY KEY,              -- 'usdjpy' | 'eurjpy' | 'gbpjpy'
  intervention_level double precision NOT NULL,
  caution_band double precision NOT NULL,
  regime text,
  verified_through date,
  updated_utc timestamptz NOT NULL DEFAULT now()
);

-- Jawboning quote log — append-only, Claude adds rows from web search each /weekly JPY run.
CREATE TABLE IF NOT EXISTS intervention_jawboning (
  pair text NOT NULL REFERENCES intervention_watch(pair) ON DELETE CASCADE,
  event_date date NOT NULL,
  official text,
  quote text,
  source text,
  created_utc timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (pair, event_date, official)
);

-- ─────────────────────────────────────────────────────────────────────────────
-- Phase 3: research/backtest readiness. Freezes the feature vector Claude actually
-- scored a decision on — R1 (get_zone_context) at publish, R2 (entry_confluence
-- breakdown) at validate — so a study 2-3 months out joins straight to r_result
-- without re-deriving every indicator from raw OHLC (slow, and drifts vs what was
-- actually judged at the time). jsonb `features` so new angles need no migration.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS feature_snapshot (
  snap_id text PRIMARY KEY,           -- '{zone_id}:{event_type}:{event_utc}'
  zone_id text NOT NULL REFERENCES zone_ledger(zone_id) ON DELETE CASCADE,
  instrument text NOT NULL,
  event_type text NOT NULL,           -- 'publish' (R1/get_zone_context) | 'validate' (R2/EC breakdown)
  event_utc timestamptz NOT NULL DEFAULT now(),
  features jsonb NOT NULL,
  created_utc timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_feature_snapshot_zone ON feature_snapshot (zone_id, event_type);
CREATE INDEX IF NOT EXISTS ix_feature_snapshot_instrument_event ON feature_snapshot (instrument, event_type, event_utc);

CREATE TABLE IF NOT EXISTS routine_checkpoint (
  routine_name text PRIMARY KEY,
  status text NOT NULL,
  last_run_utc timestamptz,
  branch text,
  commit_sha text,
  notes text,
  updated_utc timestamptz NOT NULL DEFAULT now()
);
