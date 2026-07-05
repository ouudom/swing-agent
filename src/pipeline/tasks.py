from __future__ import annotations

import json
import os
import sys
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[1]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from engine import commands


@dataclass
class RunRecord:
    run_id: str
    job_name: str
    instrument: str | None
    status: str
    started_utc: str
    finished_utc: str
    duration_s: float
    command: str
    returncode: int | None
    stdout_tail: str
    stderr_tail: str
    error: str


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def tail(text: str, limit: int = 4000) -> str:
    return text[-limit:] if text else ""


def log_path() -> Path:
    path = Path(os.getenv("PIPELINE_RUN_LOG", SRC_ROOT / "logs" / "pipeline_run.jsonl"))
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def write_jsonl(record: RunRecord) -> None:
    with log_path().open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(asdict(record), sort_keys=True) + "\n")


def run_job(job_name: str, instrument: str | None = None, **kwargs) -> RunRecord:
    started = utc_now()
    run_id = str(uuid.uuid4())
    result = None
    error = ""
    try:
        if job_name == "brief_refresh":
            if not instrument:
                raise ValueError("brief_refresh requires instrument")
            result = commands.brief_refresh(instrument)
        elif job_name == "fetch_data":
            if not instrument:
                raise ValueError("fetch_data requires instrument")
            result = commands.fetch_data(instrument, force=bool(kwargs.get("force", False)))
        elif job_name == "zone_outcomes":
            result = commands.zone_outcomes(kwargs.get("week"), instrument)
        elif job_name == "trade_outcome":
            result = commands.trade_outcome(kwargs.get("week"), instrument)
        elif job_name == "calibration":
            result = commands.calibration()
        elif job_name == "check_live_trades":
            result = commands.check_live_trades(instrument)
        elif job_name == "fire_validate_trigger":
            result = commands.fire_validate_trigger(instrument)
        elif job_name == "reconcile":
            result = commands.reconcile(strict=bool(kwargs.get("strict", False)))
        elif job_name == "send_notifications":
            result = commands.send_notifications(limit=int(kwargs.get("limit", 20)))
        else:
            raise ValueError(f"unknown job: {job_name}")
        status = "ok" if result.returncode == 0 else "error"
    except Exception as exc:
        status = "error"
        error = str(exc)
    finished = utc_now()
    record = RunRecord(
        run_id=run_id,
        job_name=job_name,
        instrument=instrument,
        status=status,
        started_utc=started.isoformat(),
        finished_utc=finished.isoformat(),
        duration_s=(finished - started).total_seconds(),
        command=" ".join(result.command) if result else "",
        returncode=result.returncode if result else None,
        stdout_tail=tail(result.stdout) if result else "",
        stderr_tail=tail(result.stderr) if result else "",
        error=error,
    )
    write_jsonl(record)
    return record


def refresh_all_briefs() -> list[RunRecord]:
    return [run_job("brief_refresh", instrument=inst) for inst in commands.INSTRUMENTS]


def nightly_replay() -> list[RunRecord]:
    return [
        run_job("zone_outcomes"),
        run_job("trade_outcome"),
        run_job("calibration"),
        run_job("reconcile"),
        run_job("send_notifications"),
    ]
