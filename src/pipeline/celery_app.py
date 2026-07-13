"""Celery app — broker/result backend on Redis. Replaces the blocking
APScheduler loop in `scheduler.py` (see docs/framework-migration-plan.md Phase 1).

Beat schedule lives here so `celery -A pipeline.celery_app beat` and
`celery -A pipeline.celery_app worker` both import it from one place.
"""
from __future__ import annotations

import sys
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[1]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from celery import Celery
from celery.schedules import crontab
from celery.signals import task_failure

from logging_config import configure_logging, get_logger
from settings import settings

configure_logging()
logger = get_logger(__name__)

app = Celery(
    "swing_agent",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

app.conf.update(
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_lost_connection=True,
    worker_prefetch_multiplier=1,
    task_default_retry_delay=30,
    result_expires=86400,
)

# Beat schedule — mirrors scheduler.py::build_scheduler() cron entries 1:1
# (same days/minutes as the APScheduler triggers it replaces).
# `market_cycle` and `nightly_replay` are graph-shaped tasks (chain/group), not
# single jobs; the FX-market-open guard lives inside them, not here (Beat cron
# is timezone/DST-only, no market-calendar awareness).
MARKET_CRON_DAYS = "sun,mon,tue,wed,thu,fri"  # retail FX week: Sun 21:00 UTC - Fri 21:00 UTC

app.conf.beat_schedule = {
    "market_cycle": {
        "task": "pipeline.celery_tasks.market_cycle",
        "schedule": crontab(minute="2,22,42", day_of_week=MARKET_CRON_DAYS),
    },
    "context_refresh": {
        "task": "pipeline.celery_tasks.run_job_task",
        "schedule": crontab(minute=10, day_of_week=MARKET_CRON_DAYS),
        "kwargs": {"job_name": "context_refresh"},
    },
    "send_notifications": {
        "task": "pipeline.celery_tasks.run_job_task_market_gated",
        "schedule": crontab(minute="*/5", day_of_week=MARKET_CRON_DAYS),
        "kwargs": {"job_name": "send_notifications"},
    },
    "macro_refresh": {
        "task": "pipeline.celery_tasks.run_job_task",
        "schedule": crontab(hour=23, minute=10, day_of_week="mon-fri"),
        "kwargs": {"job_name": "macro_refresh", "instrument": "all"},
    },
    "nightly_replay": {
        "task": "pipeline.celery_tasks.nightly_replay",
        "schedule": crontab(hour=22, minute=0, day_of_week="mon-fri"),
    },
}

app.autodiscover_tasks(["pipeline"], related_name="celery_tasks")


@task_failure.connect
def _on_task_failure(sender=None, task_id=None, exception=None, **kwargs):
    """Dead-letter hook: a task that exhausted its retries (run_job's own jobs already
    self-notify on failure via tasks.queue_notification — this catches the layer above,
    e.g. a bug in celery_tasks.py itself, not just a failed subprocess)."""
    name = getattr(sender, "name", "unknown")
    logger.error("task_failed", task=name, task_id=task_id, error=str(exception))
    try:
        from pipeline import tasks

        tasks.queue_notification(
            event_type="celery_task_error",
            title=f"celery task failed: {name}",
            message=str(exception),
            payload={"task_id": task_id},
        )
    except Exception:
        pass
