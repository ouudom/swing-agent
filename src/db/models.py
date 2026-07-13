"""SQLAlchemy 2.0 declarative models — typed mirror of `src/database/init.sql`.

Additive infrastructure only (see docs/framework-migration-plan.md Phase 3). Nothing
in the existing pipeline/MCP/dashboard imports this yet — `engine/scripts/db.py` (the
legacy sqlite/postgres dual-backend, all-string CSV frames) is still the load-bearing
path. Cutting existing callers over to this ORM is a separate, tested pass: every
replay script (`zone_ledger.py`, `zone_outcomes.py`, `trade_outcome.py`,
`ohlc_store.py`) and every MCP/dashboard query touches `db.py`'s contract, and none of
that can be verified without a live Postgres run.

Column shapes here must match init.sql exactly — this is a mirror, not a redesign.
"""
from __future__ import annotations

from datetime import date as date_, datetime

from sqlalchemy import (
    ARRAY,
    BigInteger,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Ohlc(Base):
    __tablename__ = "ohlc"
    source: Mapped[str] = mapped_column(Text, primary_key=True)
    symbol: Mapped[str] = mapped_column(Text, primary_key=True)
    tf: Mapped[str] = mapped_column(Text, primary_key=True)
    datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    open: Mapped[float | None] = mapped_column(Float)
    high: Mapped[float | None] = mapped_column(Float)
    low: Mapped[float | None] = mapped_column(Float)
    close: Mapped[float | None] = mapped_column(Float)
    volume: Mapped[float | None] = mapped_column(Float)

    __table_args__ = (Index("ix_ohlc_symbol_tf_datetime", "symbol", "tf", "datetime"),)


class MacroSeries(Base):
    __tablename__ = "macro_series"
    series_id: Mapped[str] = mapped_column(Text, primary_key=True)
    date: Mapped[date_] = mapped_column(Date, primary_key=True)
    value: Mapped[float | None] = mapped_column(Float)


class MarketSeries(Base):
    __tablename__ = "market_series"
    source: Mapped[str] = mapped_column(Text, primary_key=True)
    symbol: Mapped[str] = mapped_column(Text, primary_key=True)
    date: Mapped[date_] = mapped_column(Date, primary_key=True)
    value: Mapped[float | None] = mapped_column(Float)


class OhlcQuarantine(Base):
    __tablename__ = "ohlc_quarantine"
    symbol: Mapped[str] = mapped_column(Text, primary_key=True)
    tf: Mapped[str] = mapped_column(Text, primary_key=True)
    datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    action: Mapped[str] = mapped_column(Text, primary_key=True)
    open: Mapped[float | None] = mapped_column(Float)
    high: Mapped[float | None] = mapped_column(Float)
    low: Mapped[float | None] = mapped_column(Float)
    close: Mapped[float | None] = mapped_column(Float)
    ref_close: Mapped[float | None] = mapped_column(Float)
    flagged_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class EconCalendar(Base):
    __tablename__ = "econ_calendar"
    date: Mapped[date_] = mapped_column(Date, primary_key=True)
    time_utc: Mapped[str | None] = mapped_column(Text)
    country: Mapped[str] = mapped_column(Text, primary_key=True)
    event: Mapped[str] = mapped_column(Text, primary_key=True)
    impact: Mapped[str | None] = mapped_column(Text)
    estimate: Mapped[str | None] = mapped_column(Text)
    actual: Mapped[str | None] = mapped_column(Text)
    prev: Mapped[str | None] = mapped_column(Text)
    unit: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (Index("ix_econ_calendar_date_country", "date", "country"),)


class GldHoldings(Base):
    __tablename__ = "gld_holdings"
    date: Mapped[date_] = mapped_column(Date, primary_key=True)
    tonnes: Mapped[float | None] = mapped_column(Float)
    aum_usd: Mapped[float | None] = mapped_column(Float)
    spot: Mapped[float | None] = mapped_column(Float)


class Cot(Base):
    __tablename__ = "cot"
    contract: Mapped[str] = mapped_column(Text, primary_key=True)
    date: Mapped[date_] = mapped_column(Date, primary_key=True)
    long: Mapped[int | None] = mapped_column(BigInteger)
    short: Mapped[int | None] = mapped_column(BigInteger)
    net: Mapped[int | None] = mapped_column(BigInteger)
    net_prev: Mapped[int | None] = mapped_column(BigInteger)


class News(Base):
    __tablename__ = "news"
    datetime_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    category: Mapped[str | None] = mapped_column(Text)
    headline: Mapped[str] = mapped_column(Text, primary_key=True)
    source: Mapped[str] = mapped_column(Text, primary_key=True)
    url: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    related: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (Index("ix_news_datetime_category", "datetime_utc", "category"),)


class ZoneLedger(Base):
    __tablename__ = "zone_ledger"
    zone_id: Mapped[str] = mapped_column(Text, primary_key=True)
    instrument: Mapped[str] = mapped_column(Text, nullable=False)
    week: Mapped[str] = mapped_column(Text, nullable=False)
    label: Mapped[str] = mapped_column(Text, nullable=False)
    direction: Mapped[str] = mapped_column(Text, nullable=False)
    zone_bottom: Mapped[float | None] = mapped_column(Float)
    zone_top: Mapped[float | None] = mapped_column(Float)
    zone_confluence: Mapped[float | None] = mapped_column(Float)
    conviction: Mapped[str | None] = mapped_column(Text)
    invalidation_level: Mapped[float | None] = mapped_column(Float)
    tp_anchor: Mapped[float | None] = mapped_column(Float)
    published_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_file: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    replay_status: Mapped[str | None] = mapped_column(Text)
    entry_confluence: Mapped[float | None] = mapped_column(Float)
    daily_verdict: Mapped[str | None] = mapped_column(Text)
    limit_price: Mapped[float | None] = mapped_column(Float)
    validated_date: Mapped[date_ | None] = mapped_column(Date)
    anchor_set_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    anchor_locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (Index("ix_zone_ledger_instrument_week", "instrument", "week"),)


class ZoneOutcome(Base):
    __tablename__ = "zone_outcome"
    zone_id: Mapped[str] = mapped_column(Text, primary_key=True)
    instrument: Mapped[str] = mapped_column(Text, nullable=False)
    week: Mapped[str] = mapped_column(Text, nullable=False)
    label: Mapped[str | None] = mapped_column(Text)
    direction: Mapped[str | None] = mapped_column(Text)
    zone_confluence: Mapped[float | None] = mapped_column(Float)
    conviction: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(Text)
    touched: Mapped[int | None] = mapped_column(Integer)
    fill_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    entry: Mapped[float | None] = mapped_column(Float)
    sl_dist: Mapped[float | None] = mapped_column(Float)
    r_result: Mapped[float | None] = mapped_column(Float)
    mfe_r: Mapped[float | None] = mapped_column(Float)
    mae_r: Mapped[float | None] = mapped_column(Float)
    exit_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (Index("ix_zone_outcome_instrument_week", "instrument", "week"),)


class ZoneAtrSlOutcome(Base):
    __tablename__ = "zone_atr_sl_outcome"
    zone_id: Mapped[str] = mapped_column(Text, primary_key=True)
    instrument: Mapped[str] = mapped_column(Text, nullable=False)
    week: Mapped[str] = mapped_column(Text, nullable=False)
    label: Mapped[str | None] = mapped_column(Text)
    direction: Mapped[str | None] = mapped_column(Text)
    zone_confluence: Mapped[float | None] = mapped_column(Float)
    conviction: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(Text)
    touched: Mapped[int | None] = mapped_column(Integer)
    fill_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    entry: Mapped[float | None] = mapped_column(Float)
    sl_dist: Mapped[float | None] = mapped_column(Float)
    r_result: Mapped[float | None] = mapped_column(Float)
    mfe_r: Mapped[float | None] = mapped_column(Float)
    mae_r: Mapped[float | None] = mapped_column(Float)
    exit_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (Index("ix_zone_atr_sl_outcome_instrument_week", "instrument", "week"),)


class TradeOutcome(Base):
    __tablename__ = "trade_outcome"
    zone_id: Mapped[str] = mapped_column(Text, primary_key=True)
    instrument: Mapped[str] = mapped_column(Text, nullable=False)
    week: Mapped[str] = mapped_column(Text, nullable=False)
    label: Mapped[str | None] = mapped_column(Text)
    direction: Mapped[str | None] = mapped_column(Text)
    zone_confluence: Mapped[float | None] = mapped_column(Float)
    conviction: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(Text)
    e0_present: Mapped[str | None] = mapped_column(Text)
    ec_score: Mapped[float | None] = mapped_column(Float)
    ec_flags: Mapped[str | None] = mapped_column(Text)
    anchor: Mapped[float | None] = mapped_column(Float)
    sl_dist: Mapped[float | None] = mapped_column(Float)
    offset: Mapped[float | None] = mapped_column("offset", Float)
    limit_px: Mapped[float | None] = mapped_column(Float)
    entry: Mapped[float | None] = mapped_column(Float)
    fill_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    r_result: Mapped[float | None] = mapped_column(Float)
    mfe_r: Mapped[float | None] = mapped_column(Float)
    mae_r: Mapped[float | None] = mapped_column(Float)
    exit_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    block_flags: Mapped[str | None] = mapped_column(Text)
    block_verdict: Mapped[str | None] = mapped_column(Text)
    resolved_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (Index("ix_trade_outcome_instrument_week", "instrument", "week"),)


class PipelineRun(Base):
    __tablename__ = "pipeline_run"
    run_id: Mapped[str] = mapped_column(Text, primary_key=True)
    job_name: Mapped[str] = mapped_column(Text, nullable=False)
    instrument: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    started_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_s: Mapped[float | None] = mapped_column(Float)
    command: Mapped[str | None] = mapped_column(Text)
    returncode: Mapped[int | None] = mapped_column(Integer)
    stdout_tail: Mapped[str | None] = mapped_column(Text)
    stderr_tail: Mapped[str | None] = mapped_column(Text)
    error: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (Index("ix_pipeline_run_job_started", "job_name", "started_utc"),)


class ValidationVerdict(Base):
    __tablename__ = "validation_verdict"
    zone_id: Mapped[str] = mapped_column(
        Text, ForeignKey("zone_ledger.zone_id", ondelete="CASCADE"), primary_key=True
    )
    validation_date: Mapped[date_] = mapped_column(Date, primary_key=True)
    run_id: Mapped[str] = mapped_column(Text, primary_key=True)
    instrument: Mapped[str] = mapped_column(Text, nullable=False)
    verdict: Mapped[str] = mapped_column(Text, nullable=False)
    entry_confluence: Mapped[float | None] = mapped_column(Float)
    limit_price: Mapped[float | None] = mapped_column(Float)
    hard_block_flags: Mapped[str | None] = mapped_column(Text)
    reason: Mapped[str | None] = mapped_column(Text)
    source_file: Mapped[str | None] = mapped_column(Text)
    created_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    payload: Mapped[dict] = mapped_column(JSONB, server_default="{}")

    __table_args__ = (Index("ix_validation_verdict_instrument_date", "instrument", "validation_date"),)


class NotificationEvent(Base):
    __tablename__ = "notification_event"
    event_id: Mapped[str] = mapped_column(Text, primary_key=True)
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    instrument: Mapped[str | None] = mapped_column(Text)
    zone_id: Mapped[str | None] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="pending")
    created_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    sent_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error: Mapped[str | None] = mapped_column(Text)
    payload: Mapped[dict] = mapped_column(JSONB, server_default="{}")

    __table_args__ = (Index("ix_notification_event_status_created", "status", "created_utc"),)


class TradeLog(Base):
    __tablename__ = "trade_log"
    zone_id: Mapped[str] = mapped_column(
        Text, ForeignKey("zone_ledger.zone_id", ondelete="CASCADE"), primary_key=True
    )
    instrument: Mapped[str] = mapped_column(Text, nullable=False)
    week: Mapped[str] = mapped_column(Text, nullable=False)
    label: Mapped[str | None] = mapped_column(Text)
    direction: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="PENDING")
    entry_confluence: Mapped[float | None] = mapped_column(Float)
    limit_price: Mapped[float | None] = mapped_column(Float)
    sl_price: Mapped[float | None] = mapped_column(Float)
    tp_price: Mapped[float | None] = mapped_column(Float)
    hard_block_flags: Mapped[str | None] = mapped_column(Text)
    reason: Mapped[str | None] = mapped_column(Text)
    entry_price: Mapped[float | None] = mapped_column(Float)
    fill_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    exit_price: Mapped[float | None] = mapped_column(Float)
    exit_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    r_result: Mapped[float | None] = mapped_column(Float)
    validation_date: Mapped[date_ | None] = mapped_column(Date)
    run_id: Mapped[str | None] = mapped_column(Text)
    created_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (Index("ix_trade_log_instrument_status", "instrument", "status"),)


class TriggerState(Base):
    __tablename__ = "trigger_state"
    instrument: Mapped[str] = mapped_column(Text, primary_key=True)
    last_fired_h1: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_fire_reason: Mapped[str | None] = mapped_column(Text)
    updated_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Rulebook(Base):
    __tablename__ = "rulebook"
    doc_key: Mapped[str] = mapped_column(Text, primary_key=True)
    scope: Mapped[str] = mapped_column(Text, nullable=False)
    instrument: Mapped[str | None] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str | None] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    frontmatter: Mapped[dict] = mapped_column(JSONB, server_default="{}")
    source_path: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, server_default="1")
    updated_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (Index("ix_rulebook_kind_instrument", "kind", "instrument"),)


class ContextDoc(Base):
    __tablename__ = "context_doc"
    doc_key: Mapped[str] = mapped_column(Text, primary_key=True)
    kind: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str | None] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    frontmatter: Mapped[dict] = mapped_column(JSONB, server_default="{}")
    source_path: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, server_default="1")
    updated_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ForecastDoc(Base):
    __tablename__ = "forecast_doc"
    doc_key: Mapped[str] = mapped_column(Text, primary_key=True)
    instrument: Mapped[str] = mapped_column(Text, nullable=False)
    week: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str | None] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    frontmatter: Mapped[dict] = mapped_column(JSONB, server_default="{}")
    generated: Mapped[date_ | None] = mapped_column(Date)
    source_path: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, server_default="1")
    updated_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (Index("ix_forecast_doc_instrument_week", "instrument", "week"),)


class ValidationDoc(Base):
    __tablename__ = "validation_doc"
    doc_key: Mapped[str] = mapped_column(Text, primary_key=True)
    instrument: Mapped[str] = mapped_column(Text, nullable=False)
    valid_date: Mapped[date_] = mapped_column(Date, nullable=False)
    week: Mapped[str | None] = mapped_column(Text)
    title: Mapped[str | None] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    frontmatter: Mapped[dict] = mapped_column(JSONB, server_default="{}")
    source_path: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, server_default="1")
    updated_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (Index("ix_validation_doc_instrument_date", "instrument", "valid_date"),)


class DocHistory(Base):
    __tablename__ = "doc_history"
    source_table: Mapped[str] = mapped_column(Text, primary_key=True)
    doc_key: Mapped[str] = mapped_column(Text, primary_key=True)
    version: Mapped[int] = mapped_column(Integer, primary_key=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    frontmatter: Mapped[dict] = mapped_column(JSONB, server_default="{}")
    saved_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CbCalendar(Base):
    __tablename__ = "cb_calendar"
    bank_code: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    time_note: Mapped[str | None] = mapped_column(Text)
    hard_block: Mapped[list[str]] = mapped_column(ARRAY(Text), server_default="{}")
    caution: Mapped[list[str]] = mapped_column(ARRAY(Text), server_default="{}")
    dates: Mapped[list] = mapped_column(JSONB, server_default="[]")
    verified_through: Mapped[date_ | None] = mapped_column(Date)
    updated_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class InterventionWatch(Base):
    __tablename__ = "intervention_watch"
    pair: Mapped[str] = mapped_column(Text, primary_key=True)
    intervention_level: Mapped[float] = mapped_column(Float, nullable=False)
    caution_band: Mapped[float] = mapped_column(Float, nullable=False)
    regime: Mapped[str | None] = mapped_column(Text)
    verified_through: Mapped[date_ | None] = mapped_column(Date)
    updated_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class InterventionJawboning(Base):
    __tablename__ = "intervention_jawboning"
    pair: Mapped[str] = mapped_column(
        Text, ForeignKey("intervention_watch.pair", ondelete="CASCADE"), primary_key=True
    )
    event_date: Mapped[date_] = mapped_column(Date, primary_key=True)
    official: Mapped[str] = mapped_column(Text, primary_key=True)
    quote: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(Text)
    created_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FeatureSnapshot(Base):
    __tablename__ = "feature_snapshot"
    snap_id: Mapped[str] = mapped_column(Text, primary_key=True)
    zone_id: Mapped[str] = mapped_column(
        Text, ForeignKey("zone_ledger.zone_id", ondelete="CASCADE"), nullable=False
    )
    instrument: Mapped[str] = mapped_column(Text, nullable=False)
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    event_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    features: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_feature_snapshot_zone", "zone_id", "event_type"),
        Index("ix_feature_snapshot_instrument_event", "instrument", "event_type", "event_utc"),
    )


class RoutineCheckpoint(Base):
    __tablename__ = "routine_checkpoint"
    routine_name: Mapped[str] = mapped_column(Text, primary_key=True)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    last_run_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    branch: Mapped[str | None] = mapped_column(Text)
    commit_sha: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    updated_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SystemConfig(Base):
    __tablename__ = "system_config"
    key: Mapped[str] = mapped_column(Text, primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    updated_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
