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


def _pg_connect():
    import psycopg

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


def queue_notification(
    event_type: str,
    title: str,
    message: str,
    instrument: str | None = None,
    zone_id: str | None = None,
    payload: dict | None = None,
) -> None:
    """Best-effort notification queue write — never let a notify failure mask the
    original job error (this runs from the error path itself)."""
    try:
        event_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{event_type}:{zone_id}:{title}:{message}"))
        with _pg_connect() as con:
            with con.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO notification_event (
                      event_id, event_type, instrument, zone_id, title, message, payload
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s::jsonb)
                    ON CONFLICT (event_id) DO NOTHING
                    """,
                    (event_id, event_type, instrument, zone_id, title, message, json.dumps(payload or {})),
                )
    except Exception:
        pass


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


def log(message: str) -> None:
    print(f"{utc_now().isoformat()} task {message}", flush=True)


def job_label(job_name: str, instrument: str | None = None) -> str:
    return f"{job_name}{' '+instrument if instrument else ''}"


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
    label = job_label(job_name, instrument)
    log(f"start {label} run_id={run_id}")
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
    log(
        f"finish {label} run_id={run_id} status={status} "
        f"duration_s={record.duration_s:.1f} returncode={record.returncode}"
    )
    if record.command:
        log(f"command {label} run_id={run_id}: {record.command}")
    if status == "error":
        detail = error or tail(result.stderr if result else "", 500) or "non-zero returncode"
        log(f"error {label} run_id={run_id}: {detail}")
        queue_notification(
            event_type="pipeline_job_error",
            title=f"pipeline job failed: {job_name}",
            message=detail,
            instrument=instrument,
            payload={"run_id": run_id, "returncode": record.returncode},
        )
    return record


def refresh_all_briefs() -> list[RunRecord]:
    return [run_job("brief_refresh", instrument=inst) for inst in commands.INSTRUMENTS]


def _weekly_digest() -> None:
    """Nightly digest: today's resolved trades + any instrument/direction pair whose
    lifetime trade_outcome total_r has gone negative (edge looks DEAD)."""
    try:
        with _pg_connect() as con:
            with con.cursor() as cur:
                cur.execute(
                    "SELECT instrument, status, COUNT(*), SUM(r_result) FROM trade_outcome "
                    "WHERE exit_time::date = (now() AT TIME ZONE 'utc')::date "
                    "GROUP BY instrument, status ORDER BY instrument, status"
                )
                today_rows = cur.fetchall()
                cur.execute(
                    "SELECT instrument, direction, COUNT(*) AS n, SUM(r_result) AS total_r "
                    "FROM trade_outcome GROUP BY instrument, direction "
                    "HAVING COUNT(*) >= 5 AND SUM(r_result) <= 0 "
                    "ORDER BY instrument, direction"
                )
                dead_rows = cur.fetchall()
    except Exception:
        return

    if not today_rows and not dead_rows:
        log("weekly_digest skipped: no resolved trades or dead edges")
        return

    lines = []
    if today_rows:
        lines.append("Resolved today:")
        lines += [f"  {inst.upper()} {status}: n={n} total_r={float(tr or 0):+.2f}" for inst, status, n, tr in today_rows]
    if dead_rows:
        lines.append("Edge check (n>=5, total_r<=0 — DEAD):")
        lines += [f"  {inst.upper()} {direction}: n={n} total_r={float(tr):+.2f}" for inst, direction, n, tr in dead_rows]

    queue_notification(
        event_type="weekly_digest",
        title="Nightly replay digest",
        message="\n".join(lines),
        payload={"date": utc_now().date().isoformat()},
    )
    log(f"weekly_digest queued: resolved_rows={len(today_rows)} dead_edges={len(dead_rows)}")


def nightly_replay() -> list[RunRecord]:
    records = [
        run_job("zone_outcomes"),
        run_job("trade_outcome"),
        run_job("calibration"),
        run_job("reconcile"),
        run_job("send_notifications"),
    ]
    _weekly_digest()
    return records
