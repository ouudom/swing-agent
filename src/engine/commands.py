from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


INSTRUMENTS = [
    "xauusd",
    "eurusd",
    "gbpusd",
    "eurgbp",
    "audusd",
    "nzdusd",
    "usdcad",
    "usdchf",
    "usdjpy",
    "eurjpy",
    "gbpjpy",
]


@dataclass
class CommandResult:
    command: list[str]
    returncode: int
    stdout: str
    stderr: str


def repo_root() -> Path:
    override = os.getenv("SWING_AGENT_REPO_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    return Path(__file__).resolve().parents[2]


def engine_script(name: str) -> str:
    return f"src/engine/scripts/{name}"


def app_script(name: str) -> str:
    return f"src/engine/scripts/ops/{name}"


def run(command: list[str], timeout_s: int | None = None) -> CommandResult:
    proc = subprocess.run(
        command,
        cwd=repo_root(),
        text=True,
        capture_output=True,
        timeout=timeout_s,
        check=False,
    )
    return CommandResult(command, proc.returncode, proc.stdout, proc.stderr)


def pyrun(args: list[str], timeout_s: int | None = None) -> CommandResult:
    if Path("/.dockerenv").exists():
        return run([sys.executable, *args], timeout_s=timeout_s)
    launcher = repo_root() / "src" / "engine" / "scripts" / "pyrun.sh"
    if launcher.exists():
        return run(["bash", str(launcher.relative_to(repo_root())), *args], timeout_s=timeout_s)
    return run([sys.executable, *args], timeout_s=timeout_s)


def weekly_pull(instrument: str, force: bool = False) -> CommandResult:
    args = [engine_script("pipeline/weekly_pull.py"), "--instrument", instrument]
    if force:
        args.append("--force")
    return pyrun(args, timeout_s=900)


def zone_outcomes(week: str | None = None, instrument: str | None = None) -> CommandResult:
    args = [engine_script("replay/zone_outcomes.py")]
    if week:
        args += ["--week", week]
    if instrument:
        args += ["--instrument", instrument]
    return pyrun(args, timeout_s=600)


def trade_outcome(week: str | None = None, instrument: str | None = None) -> CommandResult:
    args = [engine_script("replay/trade_outcome.py")]
    if week:
        args += ["--week", week]
    if instrument:
        args += ["--instrument", instrument]
    return pyrun(args, timeout_s=600)


def calibration() -> CommandResult:
    return pyrun([engine_script("replay/calibration.py")], timeout_s=300)


def brief_refresh(instrument: str) -> CommandResult:
    return weekly_pull(instrument, force=False)


def reconcile(strict: bool = False) -> CommandResult:
    args = [app_script("reconcile_db_git.py")]
    if strict:
        args.append("--strict")
    return pyrun(args, timeout_s=120)


def send_notifications(limit: int = 20, dry_run: bool = False) -> CommandResult:
    args = [app_script("send_notifications.py"), "--limit", str(limit)]
    if dry_run:
        args.append("--dry-run")
    return pyrun(args, timeout_s=120)
