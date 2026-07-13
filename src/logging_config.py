"""structlog setup (see docs/framework-migration-plan.md Phase 5). Call
`configure_logging()` once at process start in a service entrypoint (celery_app.py,
dashboard/api/app.py, mcp_server). Existing engine/scripts print()-based logging is
untouched — those run as subprocesses and their stdout/stderr is already captured
and persisted by `pipeline.tasks.run_job` (stdout_tail/stderr_tail on `pipeline_run`);
routing them through structlog too would double-log the same content.
"""
from __future__ import annotations

import logging
import sys

import structlog


def configure_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=level)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None):
    return structlog.get_logger(name)
