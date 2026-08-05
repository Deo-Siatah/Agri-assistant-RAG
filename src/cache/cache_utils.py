"""
Cache helpers — both functions are safe to call even if Redis is down or
not configured. Caching is an optimization, never a hard dependency.
"""

import json

from src.cache.redis_client import get_redis_client


def cache_get(key: str) -> dict | None:
    client = get_redis_client()
    if client is None:
        return None
    try:
        raw = client.get(key)
        return json.loads(raw) if raw else None
    except Exception as exc:  # noqa: BLE001
        print(f"[WARN] cache_get failed for key={key}: {exc}")
        return None


def cache_set(key: str, value: dict, ttl_seconds: int) -> None:
    client = get_redis_client()
    if client is None:
        return
    try:
        client.set(key, json.dumps(value), ex=ttl_seconds)
    except Exception as exc:  # noqa: BLE001
        print(f"[WARN] cache_set failed for key={key}: {exc}")