from __future__ import annotations

import argparse
import sys
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[1]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from engine.commands import INSTRUMENTS
from pipeline import tasks


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
            tasks.run_job,
            CronTrigger(day_of_week="mon-fri", hour="7-20", minute="*/15"),
            args=["brief_refresh", instrument],
            id=f"brief_refresh_active_{instrument}",
            max_instances=1,
            coalesce=True,
        )
        scheduler.add_job(
            tasks.run_job,
            CronTrigger(day_of_week="mon-fri", hour="21-23,0-6", minute="0,30"),
            args=["brief_refresh", instrument],
            id=f"brief_refresh_overnight_{instrument}",
            max_instances=1,
            coalesce=True,
        )

    scheduler.add_job(
        tasks.run_job,
        CronTrigger(day_of_week="mon-fri", minute="*/15"),
        args=["check_live_trades"],
        id="check_live_trades",
        max_instances=1,
        coalesce=True,
    )
    # Gate in front of the Claude /validate routine. Offset a few minutes past brief_refresh
    # (:00/:15/:30/:45) so fresh OHLC has landed; the gate's trigger_state dedup makes the
    # runs where no new H1 bar closed cheap no-ops (self-skip, no Claude tokens).
    scheduler.add_job(
        tasks.run_job,
        CronTrigger(day_of_week="mon-fri", minute="7,22,37,52"),
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
    print("swing-agent scheduler starting (UTC)")
    scheduler.start()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
