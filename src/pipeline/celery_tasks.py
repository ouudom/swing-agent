"""Celery task registry — thin wrappers around `pipeline.tasks.run_job`, which still
owns dispatch + run-log write + failure notification (see tasks.py). This layer adds
queueing, retry, isolation, and real parallel dependency graphs; it does not
re-implement job logic.

`market_cycle` / `nightly_replay` dispatch a `group()` for their independent legs and
`.get()` the result — safe here because task volume is low (well under a hundred/day)
and the worker is run with concurrency >= 4 (see docker-compose.yml `worker` service),
so a parent task blocked on a child never starves the pool. Do not lower worker
concurrency below the deepest fan-out (currently 2) without revisiting this.
"""
from __future__ import annotations

import sys
from dataclasses import asdict
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[1]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from celery import group
from celery.utils.log import get_task_logger

from pipeline import tasks
from pipeline.celery_app import app
from pipeline.scheduler import is_fx_market_open

logger = get_task_logger(__name__)

# soft_time_limit mirrors the timeouts previously passed to `commands.pyrun`.
JOB_TIME_LIMITS = {
    "brief_refresh": 900,
    "fetch_data": 1800,
    "price_refresh": 900,
    "context_refresh": 300,
    "macro_refresh": 1800,
    "zone_outcomes": 600,
    "trade_outcome": 600,
    "calibration": 300,
    "check_live_trades": 120,
    "fire_validate_trigger": 600,
    "reconcile": 120,
    "send_notifications": 120,
}


def _record_dict(record) -> dict:
    return asdict(record)


@app.task(
    name="pipeline.celery_tasks.run_job_task",
    autoretry_for=(Exception,),
    max_retries=2,
    retry_backoff=True,
    retry_backoff_max=120,
)
def run_job_task(job_name: str, instrument: str | None = None, **kwargs) -> dict:
    record = tasks.run_job(job_name, instrument, **kwargs)
    if record.status != "ok":
        # run_job already wrote the run-log row + queued a failure notification;
        # raising here only drives Celery's own retry/backoff.
        raise RuntimeError(f"{job_name}{' ' + instrument if instrument else ''} failed: {record.error or record.returncode}")
    return _record_dict(record)


def _job_signature(job_name: str, instrument: str | None = None, **kwargs):
    soft_limit = JOB_TIME_LIMITS.get(job_name)
    sig = run_job_task.s(job_name, instrument, **kwargs)
    if soft_limit:
        sig = sig.set(soft_time_limit=soft_limit, time_limit=soft_limit + 30)
    return sig


def _dispatch(job_name: str, instrument: str | None = None, **kwargs):
    """apply_async through the real broker (never `.apply()` — that runs eagerly
    in-process and skips the worker/queue entirely), with the job's time budget."""
    return _job_signature(job_name, instrument, **kwargs).apply_async()


@app.task(name="pipeline.celery_tasks.run_job_task_market_gated")
def run_job_task_market_gated(job_name: str, instrument: str | None = None, **kwargs) -> dict | None:
    if not is_fx_market_open():
        logger.info("skip %s: FX market closed", job_name)
        return None
    return _dispatch(job_name, instrument, **kwargs).get(disable_sync_subtasks=False)


@app.task(name="pipeline.celery_tasks.market_cycle")
def market_cycle() -> list[dict] | None:
    if not is_fx_market_open():
        logger.info("skip market_cycle: FX market closed")
        return None

    records = []
    refresh = _dispatch("price_refresh", "all").get(disable_sync_subtasks=False)
    records.append(refresh)

    if refresh["status"] == "ok":
        fanout = group(
            _job_signature("check_live_trades"),
            _job_signature("fire_validate_trigger"),
        ).apply_async()
        records.extend(fanout.get(disable_sync_subtasks=False))
    else:
        logger.warning("skip check_live_trades/fire_validate_trigger: price_refresh failed")

    records.append(_dispatch("send_notifications").get(disable_sync_subtasks=False))
    logger.info(
        "market_cycle finished: %s",
        ",".join(f"{r['job_name']}:{r['status']}" for r in records if r),
    )
    return records


@app.task(name="pipeline.celery_tasks.nightly_replay")
def nightly_replay() -> list[dict]:
    replay = group(
        _job_signature("zone_outcomes"),
        _job_signature("trade_outcome"),
    ).apply_async()
    records = list(replay.get(disable_sync_subtasks=False))

    records.append(_dispatch("calibration").get(disable_sync_subtasks=False))
    tasks._weekly_digest()
    records.append(_dispatch("send_notifications").get(disable_sync_subtasks=False))
    return records
