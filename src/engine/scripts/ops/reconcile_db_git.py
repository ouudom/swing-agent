#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

try:
    import psycopg
except ImportError as exc:
    raise SystemExit("psycopg missing. Run inside container or install src/requirements.txt.") from exc


ZONE_ID_RE = re.compile(r"\b([a-z]{6}|xauusd)-\d{4}-W\d{2}-[A-Z0-9_-]+\b")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def connect():
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


def rows(sql: str, params=()):
    with connect() as con:
        cur = con.execute(sql, params)
        cols = [d.name for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def normalize_source(source: str | None) -> str | None:
    if not source:
        return None
    if source.startswith("swing-agent/"):
        return source.removeprefix("swing-agent/")
    return source


def scan_files(root: Path):
    found: dict[str, set[str]] = {}
    for path in root.rglob("*.md"):
        text = path.read_text(errors="ignore")
        for match in ZONE_ID_RE.finditer(text):
            found.setdefault(match.group(0), set()).add(rel(path, repo_root()))
    return found


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Reconcile swing-agent DB structured rows with git prose files.")
    parser.add_argument("--wiki-root", default=str(repo_root() / "wiki"))
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)

    wiki_root = Path(args.wiki_root)
    files_by_zone = scan_files(wiki_root)
    db_zones = rows("SELECT zone_id, source_file FROM zone_ledger ORDER BY zone_id")
    verdicts = rows("SELECT zone_id, source_file FROM validation_verdict ORDER BY zone_id, validation_date")

    issues = []
    for row in db_zones:
        source = normalize_source(row.get("source_file"))
        if source and source.startswith("wiki/") and not (repo_root() / source).exists():
            issues.append(f"DB zone source missing: {row['zone_id']} -> {row.get('source_file')}")
        if row["zone_id"] not in files_by_zone and source and source.startswith("wiki/weekly-forecasts/"):
            issues.append(f"DB zone not mentioned in wiki outputs: {row['zone_id']}")

    for row in verdicts:
        source = normalize_source(row.get("source_file"))
        if source and source.startswith("wiki/") and not (repo_root() / source).exists():
            issues.append(f"DB verdict source missing: {row['zone_id']} -> {row.get('source_file')}")

    db_zone_ids = {row["zone_id"] for row in db_zones}
    for zone_id, paths in sorted(files_by_zone.items()):
        if zone_id not in db_zone_ids:
            issues.append(f"Wiki mentions zone not in DB: {zone_id} -> {', '.join(sorted(paths))}")

    if issues:
        print("RECONCILE FAIL")
        for issue in issues:
            print(f"- {issue}")
        return 1 if args.strict else 0
    print("RECONCILE OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
