#!/usr/bin/env python3
"""
import_wiki_to_doc.py — one-shot: load every wiki/*.md into the Postgres doc tables
(Phase 1). Idempotent — re-running upserts (and versions) each doc by doc_key.

Routing by path:
  wiki/system/constitution.md          -> rulebook   constitution   (system)
  wiki/system/setup_library.md         -> rulebook   setup          (system)
  wiki/system/currency_exposure.md     -> rulebook   currency       (system)
  wiki/system/yield_environment.md     -> context    macro
  wiki/system/calibration.md           -> context    calibration
  wiki/system/{inst}/{inst}_profile.md -> rulebook   profile        (instrument)
  wiki/system/{inst}/confluence_criteria.md -> rulebook confluence  (instrument)
  wiki/templates/{name}.md             -> rulebook   template       (system)
  wiki/weekly-forecasts/{week}/{inst}.md -> forecast
  wiki/validations/{month}/{date}/{inst}.md -> validation

Run inside the pipeline container (has psycopg + env):
  docker compose run --rm pipeline python src/engine/scripts/ops/import_wiki_to_doc.py
Add --dry-run to print the routing table without writing.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

INSTRUMENTS = {
    "xauusd", "eurusd", "gbpusd", "eurgbp", "audusd", "nzdusd",
    "usdcad", "usdchf", "usdjpy", "eurjpy", "gbpjpy",
}


def repo_root() -> Path:
    override = os.getenv("SWING_AGENT_REPO_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    return Path(__file__).resolve().parents[4]


def connect():
    try:
        import psycopg
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("psycopg missing. Run inside the pipeline container.") from exc
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


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Split leading `---`-delimited YAML frontmatter from the body. Uses PyYAML if
    available, else a minimal `key: value` parser (frontmatter here is flat)."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    raw = text[3:end].strip("\n")
    body = text[end + 4:].lstrip("\n")
    try:
        import yaml  # type: ignore
        fm = yaml.safe_load(raw) or {}
        if not isinstance(fm, dict):
            fm = {}
        return fm, body
    except Exception:
        fm = {}
        for line in raw.splitlines():
            m = re.match(r"^([A-Za-z0-9_]+):\s*(.*)$", line)
            if m:
                fm[m.group(1)] = m.group(2).strip()
        return fm, body


def first_heading(body: str, fallback: str) -> str:
    for line in body.splitlines():
        s = line.strip()
        if s.startswith("# "):
            return s[2:].strip()
    return fallback


def title_of(fm: dict, body: str, fallback: str) -> str:
    return str(fm.get("title") or first_heading(body, fallback))


def route(path: Path, rel: str) -> dict | None:
    """Return an upsert descriptor for a wiki markdown file, or None to skip."""
    parts = Path(rel).parts
    name = path.stem
    if rel.startswith("wiki/system/"):
        if name == "constitution":
            return {"type": "rulebook", "key": "constitution", "scope": "system", "kind": "constitution"}
        if name == "setup_library":
            return {"type": "rulebook", "key": "setup_library", "scope": "system", "kind": "setup"}
        if name == "currency_exposure":
            return {"type": "rulebook", "key": "currency_exposure", "scope": "system", "kind": "currency"}
        if name == "yield_environment":
            return {"type": "context", "key": "yield_environment", "kind": "macro"}
        if name == "calibration":
            return {"type": "context", "key": "calibration", "kind": "calibration"}
        # per-instrument: wiki/system/{inst}/{file}.md
        if len(parts) >= 4 and parts[2] in INSTRUMENTS:
            inst = parts[2]
            if name.endswith("_profile"):
                return {"type": "rulebook", "key": f"{inst}/profile", "scope": "instrument",
                        "instrument": inst, "kind": "profile"}
            if name == "confluence_criteria":
                return {"type": "rulebook", "key": f"{inst}/confluence", "scope": "instrument",
                        "instrument": inst, "kind": "confluence"}
        return None
    if rel.startswith("wiki/templates/"):
        return {"type": "rulebook", "key": f"template/{name}", "scope": "system", "kind": "template"}
    if rel.startswith("wiki/weekly-forecasts/") and len(parts) >= 4:
        week_dir, inst = parts[2], name  # e.g. '2026W27', 'xauusd'
        return {"type": "forecast", "key_from_fm": True, "week_dir": week_dir, "instrument": inst}
    if rel.startswith("wiki/validations/") and len(parts) >= 5:
        date_dir, inst = parts[3], name  # e.g. '20260705', 'xauusd'
        return {"type": "validation", "key_from_fm": True, "date_dir": date_dir, "instrument": inst}
    return None


def norm_week(week_dir: str, fm: dict) -> str:
    wk = str(fm.get("week") or "")
    if re.match(r"^\d{4}-W\d{2}$", wk):
        return wk
    m = re.match(r"^(\d{4})W(\d{2})$", week_dir)
    return f"{m.group(1)}-W{m.group(2)}" if m else week_dir


def norm_date(date_dir: str, fm: dict) -> str:
    d = str(fm.get("date") or "")
    if re.match(r"^\d{4}-\d{2}-\d{2}$", d):
        return d
    m = re.match(r"^(\d{4})(\d{2})(\d{2})$", date_dir)
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else date_dir


UPSERTS = {
    "rulebook": (
        "rulebook",
        ["doc_key", "scope", "instrument", "kind", "title", "body", "frontmatter", "source_path"],
    ),
    "context": (
        "context_doc",
        ["doc_key", "kind", "title", "body", "frontmatter", "source_path"],
    ),
    "forecast": (
        "forecast_doc",
        ["doc_key", "instrument", "week", "title", "body", "frontmatter", "generated", "source_path"],
    ),
    "validation": (
        "validation_doc",
        ["doc_key", "instrument", "valid_date", "week", "title", "body", "frontmatter", "source_path"],
    ),
}


def build_row(desc: dict, fm: dict, body: str, rel: str) -> tuple[str, list, list]:
    dtype = desc["type"]
    table, cols = UPSERTS[dtype]
    fm_json = json.dumps(fm, default=str, sort_keys=True)
    if dtype == "rulebook":
        key = desc["key"]
        vals = {
            "doc_key": key, "scope": desc["scope"], "instrument": desc.get("instrument"),
            "kind": desc["kind"], "title": title_of(fm, body, key), "body": body,
            "frontmatter": fm_json, "source_path": rel,
        }
    elif dtype == "context":
        key = desc["key"]
        vals = {
            "doc_key": key, "kind": desc["kind"], "title": title_of(fm, body, key),
            "body": body, "frontmatter": fm_json, "source_path": rel,
        }
    elif dtype == "forecast":
        inst = desc["instrument"]
        week = norm_week(desc["week_dir"], fm)
        key = f"{week}/{inst}"
        vals = {
            "doc_key": key, "instrument": inst, "week": week,
            "title": title_of(fm, body, key), "body": body, "frontmatter": fm_json,
            "generated": fm.get("generated"), "source_path": rel,
        }
    else:  # validation
        inst = desc["instrument"]
        vdate = norm_date(desc["date_dir"], fm)
        key = f"{vdate}/{inst}"
        vals = {
            "doc_key": key, "instrument": inst, "valid_date": vdate,
            "week": fm.get("week"), "title": title_of(fm, body, key), "body": body,
            "frontmatter": fm_json, "source_path": rel,
        }
    return table, cols, [vals[c] for c in cols]


def upsert(con, table: str, cols: list, values: list) -> None:
    placeholders = ", ".join("%s::jsonb" if c == "frontmatter" else "%s" for c in cols)
    key = values[0]
    prev = con.execute(
        f"SELECT version, body, frontmatter FROM {table} WHERE doc_key = %s", (key,)
    ).fetchone()
    version = 1
    if prev:
        version = int(prev[0]) + 1
        con.execute(
            "INSERT INTO doc_history (source_table, doc_key, version, body, frontmatter) "
            "VALUES (%s,%s,%s,%s,%s::jsonb) ON CONFLICT DO NOTHING",
            (table, key, prev[0], prev[1], json.dumps(prev[2], default=str)),
        )
    update = ", ".join(f"{c} = EXCLUDED.{c}" for c in cols if c != "doc_key")
    con.execute(
        f"INSERT INTO {table} ({', '.join(cols)}, version, updated_utc) "
        f"VALUES ({placeholders}, %s, now()) "
        f"ON CONFLICT (doc_key) DO UPDATE SET {update}, version = EXCLUDED.version, updated_utc = now()",
        (*values, version),
    )


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    root = repo_root()
    wiki = root / "wiki"
    if not wiki.is_dir():
        print(f"no wiki/ at {wiki}", file=sys.stderr)
        return 1

    planned = []
    for path in sorted(wiki.rglob("*.md")):
        rel = str(path.relative_to(root))
        desc = route(path, rel)
        if not desc:
            print(f"skip  {rel}")
            continue
        fm, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        table, cols, values = build_row(desc, fm, body, rel)
        planned.append((table, cols, values, rel))
        print(f"{desc['type']:11s} {values[0]:28s} <- {rel}")

    if args.dry_run:
        print(f"\n[dry-run] {len(planned)} docs would be written")
        return 0

    with connect() as con:
        with con.transaction():
            for table, cols, values, _rel in planned:
                upsert(con, table, cols, values)
    print(f"\nimported {len(planned)} docs into Postgres doc tables")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
