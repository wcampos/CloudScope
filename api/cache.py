"""Redis cache for AWS resources. Cache is only refreshed on page load or explicit refresh."""

import json
import logging
import os
from typing import Any

import redis

logger = logging.getLogger(__name__)

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
_RESOURCE_CACHE_PREFIX = "cloudscope:resources:"
_RESOURCE_CACHE_TTL = 86400 * 7  # 7 days; refresh is explicit via button or page

_redis_client: redis.Redis | None = None


def get_redis() -> redis.Redis | None:
    """Return Redis client if available; None if Redis is disabled or unreachable."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    if not REDIS_URL or REDIS_URL == "false":
        return None
    try:
        _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        _redis_client.ping()
        return _redis_client
    except Exception as e:
        logger.warning("Redis not available: %s", e)
        return None


def _cache_key(profile_id: int) -> str:
    return f"{_RESOURCE_CACHE_PREFIX}{profile_id}"


def get_cached_resources(profile_id: int) -> dict[str, Any] | None:
    """Return cached resources for the profile, or None if miss or Redis unavailable."""
    r = get_redis()
    if not r:
        return None
    try:
        raw = r.get(_cache_key(profile_id))
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as e:
        logger.warning("Cache get failed: %s", e)
        return None


def set_cached_resources(profile_id: int, data: dict[str, Any]) -> None:
    """Store resources in cache for the profile."""
    r = get_redis()
    if not r:
        return
    try:
        key = _cache_key(profile_id)
        r.set(key, json.dumps(data), ex=_RESOURCE_CACHE_TTL)
    except Exception as e:
        logger.warning("Cache set failed: %s", e)


def invalidate_resources(profile_id: int) -> None:
    """Remove cached resources for the profile (e.g. before refresh)."""
    r = get_redis()
    if not r:
        return
    try:
        r.delete(_cache_key(profile_id))
    except Exception as e:
        logger.warning("Cache invalidate failed: %s", e)
