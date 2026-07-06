#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
import argparse


def connect():
    try:
        import psycopg
    except ImportError as exc:
        raise SystemExit("psycopg missing. Run inside container or `bash scripts/pyrun.sh --setup`.") from exc

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


def telegram_send(bot_token: str, chat_id: str, text: str) -> None:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text, "disable_web_page_preview": "true"}).encode()
    with urllib.request.urlopen(url, data=data, timeout=20) as resp:
        payload = json.loads(resp.read())
    if not payload.get("ok"):
        raise RuntimeError(payload)


def drain_pending(limit: int = 20, dry_run: bool = False) -> int:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    if not dry_run and (not token or not chat_id):
        print("telegram disabled: TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID missing")
        return 0

    sent = 0
    with connect() as con:
        events = con.execute(
            """
            SELECT event_id, title, message
            FROM notification_event
            WHERE status = 'pending'
            ORDER BY created_utc
            LIMIT %s
            FOR UPDATE SKIP LOCKED
            """,
            (limit,),
        ).fetchall()
        for event_id, title, message in events:
            text = f"{title}\n\n{message}"
            if dry_run:
                print(f"dry-run {event_id}: {text[:120]}")
                continue
            try:
                telegram_send(token, chat_id, text)
                con.execute(
                    "UPDATE notification_event SET status='sent', sent_utc=now(), error=NULL WHERE event_id=%s",
                    (event_id,),
                )
                sent += 1
                print(f"sent {event_id}")
            except Exception as exc:
                con.execute(
                    "UPDATE notification_event SET error=%s WHERE event_id=%s",
                    (str(exc), event_id),
                )
                print(f"error {event_id}: {exc}")
    return sent


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Send pending notification_event rows to Telegram.")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    drain_pending(limit=args.limit, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
