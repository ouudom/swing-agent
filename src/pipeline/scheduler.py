from __future__ import annotations

import argparse
import sys
from datetime import datetime, time, timezone
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

SRC_ROOT = Path(__file__).resolve().parents[1]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from engine.commands import INSTRUMENTS
from pipeline import tasks

MARKET_TZ = ZoneInfo("UTC")
MARKET_TZ_CONFIG_KEY = "market_timezone"
MARKET_OPEN_UTC = time(21, 0)
MARKET_CLOSE_UTC = time(21, 0)
MARKET_CRON_DAYS = "sun,mon,tue,wed,thu,fri"


def load_market_timezone() -> ZoneInfo:
    try:
        with tasks._pg_connect() as con:
            with con.cursor() as cur:
                cur.execute("SELECT value FROM system_config WHERE key = %s", (MARKET_TZ_CONFIG_KEY,))
                row = cur.fetchone()
        tz_name = (row[0] if row else None) or str(MARKET_TZ)
        return ZoneInfo(tz_name)
    except Exception:
        return MARKET_TZ


def is_fx_market_open(now_utc: Optional[datetime] = None) -> bool:
    """Retail FX week: Sunday 21:00 UTC through Friday 21:00 UTC."""
    now_utc = now_utc or datetime.now(timezone.utc)
    if now_utc.tzinfo is None:
        now_utc = now_utc.replace(tzinfo=timezone.utc)
    now_market_tz = now_utc.astimezone(load_market_timezone())
    weekday = now_market_tz.weekday()  # Mon=0 ... Sun=6
    local_time = now_market_tz.time()

    if weekday <= 3:  # Mon-Thu
        return True
    if weekday == 4:  # Friday
        return local_time < MARKET_CLOSE_UTC
    if weekday == 6:  # Sunday
        return local_time >= MARKET_OPEN_UTC
    return False


def run_market_job(job_name: str, instrument: Optional[str] = None, **kwargs):
    if not is_fx_market_open():
        now = datetime.now(timezone.utc).isoformat()
        print(f"skip {job_name}{' '+instrument if instrument else ''}: FX market closed at {now}")
        return None
    return tasks.run_job(job_name, instrument, **kwargs)


def build_scheduler():
    try:
        from apscheduler.schedulers.blocking import BlockingScheduler
        from apscheduler.triggers.cron import CronTrigger
    except ImportError as exc:
        raise SystemExit(
            "APScheduler missing. Run `bash scripts/pyrun.sh --setup` after requirements update."
        ) from exc

    scheduler = BlockingScheduler(timezone="UTC")

    for instrument in INSTRUMENTS:
        scheduler.add_job(
            run_market_job,
            CronTrigger(day_of_week=MARKET_CRON_DAYS, minute="*/15"),
            args=["brief_refresh", instrument],
            id=f"brief_refresh_{instrument}",
            max_instances=1,
            coalesce=True,
        )

    scheduler.add_job(
        run_market_job,
        CronTrigger(day_of_week=MARKET_CRON_DAYS, minute="*/15"),
        args=["check_live_trades"],
        id="check_live_trades",
        max_instances=1,
        coalesce=True,
    )
    # Gate in front of the Claude /validate routine. Offset a few minutes past brief_refresh
    # (:00/:15/:30/:45) so fresh OHLC has landed; the gate's trigger_state dedup makes the
    # runs where no new H1 bar closed cheap no-ops (self-skip, no Claude tokens).
    scheduler.add_job(
        run_market_job,
        CronTrigger(day_of_week=MARKET_CRON_DAYS, minute="7,22,37,52"),
        args=["fire_validate_trigger"],
        id="fire_validate_trigger",
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        tasks.nightly_replay,
        CronTrigger(day_of_week="mon-fri", hour=22, minute=0),
        id="nightly_replay",
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        tasks.run_job,
        CronTrigger(day_of_week="mon-fri", minute="*/5"),
        args=["send_notifications"],
        id="send_notifications",
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        tasks.run_job,
        CronTrigger(day_of_week="mon-fri", hour=23, minute=10),
        args=["reconcile"],
        id="reconcile",
        max_instances=1,
        coalesce=True,
    )
    return scheduler


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="swing-agent deterministic pipeline scheduler")
    parser.add_argument(
        "--once",
        choices=[
            "brief_refresh",
            "fetch_data",
            "zone_outcomes",
            "trade_outcome",
            "check_live_trades",
            "fire_validate_trigger",
            "calibration",
            "reconcile",
            "send_notifications",
        ],
    )
    parser.add_argument("--instrument", choices=INSTRUMENTS)
    parser.add_argument("--week")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    if args.once:
        if args.once in {"brief_refresh", "fetch_data"} and not args.instrument:
            parser.error(f"--instrument required for --once {args.once}")
        record = tasks.run_job(args.once, instrument=args.instrument, week=args.week, force=args.force)
        print(record)
        return 0 if record.status == "ok" else 1

    scheduler = build_scheduler()
    print(
        "swing-agent scheduler starting (UTC); "
        f"market_tz={load_market_timezone().key}; "
        f"FX market open=Sunday {MARKET_OPEN_UTC} UTC, close=Friday {MARKET_CLOSE_UTC} UTC"
    )
    scheduler.start()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
