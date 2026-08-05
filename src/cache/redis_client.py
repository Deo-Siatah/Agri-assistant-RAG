"""
Shared Redis client — singleton, safe to import from anywhere.
Never crashes the app if Redis is unreachable; callers get None and
should treat that as "no cache available."
"""

from functools import lru_cache

import redis

from src.config.settings import get_settings


@lru_cache
def get_redis_client() -> redis.Redis | None:
    settings = get_settings()
    try:
        client = redis.from_url(settings.redis_url, decode_responses=True, socket_timeout=3)
        client.ping()
        return client
    except Exception as exc:  # noqa: BLE001
        print(f"[WARN] Redis unavailable, caching disabled: {exc}")
        return None