"""Redis distributed lock/cache helpers (see docs/framework-migration-plan.md Phase 4).

Additive utility — not wired into any caller yet. `fire_validate_trigger.py`'s
`trigger_state` Postgres-table dedup is live-order-firing logic; swapping it to this
SETNX lock needs a dedicated pass verified against a running stack, not a blind edit
here. Use this for *new* dedup/cache needs, or as the target when that cutover happens.
"""
from __future__ import annotations

import json
from contextlib import contextmanager
from typing import Any, Iterator

from settings import settings

_client = None


def get_client():
    global _client
    if _client is None:
        import redis

        _client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    return _client


@contextmanager
def lock(key: str, ttl_s: int = 60) -> Iterator[bool]:
    """SETNX-based lock. Yields True if the lock was acquired (caller should proceed),
    False if another holder has it (caller should skip). Always releases on exit if
    this call acquired it — never releases a lock it didn't acquire (that would let a
    slow holder's lock be stolen out from under it)."""
    client = get_client()
    acquired = bool(client.set(f"lock:{key}", "1", nx=True, ex=ttl_s))
    try:
        yield acquired
    finally:
        if acquired:
            client.delete(f"lock:{key}")


def cache_get(key: str) -> Any | None:
    raw = get_client().get(f"cache:{key}")
    return json.loads(raw) if raw is not None else None


def cache_set(key: str, value: Any, ttl_s: int = 300) -> None:
    get_client().set(f"cache:{key}", json.dumps(value, default=str), ex=ttl_s)
