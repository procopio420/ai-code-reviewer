from typing import Optional
import hashlib
from redis.asyncio import Redis, from_url
from .config import settings

_redis: Optional[Redis] = None


def _k(s: str) -> str:
    return f"{settings.CACHE_PREFIX}{s}"


async def init_cache(url: Optional[str] = None) -> Redis:
    global _redis
    if _redis is None:
        _redis = from_url(url or settings.CACHE_REDIS_URL, decode_responses=True)
    return _redis


async def get_cache() -> Redis:
    global _redis
    if _redis is None:
        await init_cache()
    assert _redis is not None
    return _redis


async def close_cache():
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None


def _normalize(language: str, code: str) -> str:
    lang = (language or "").strip().lower()
    lines = [ln.rstrip() for ln in (code or "").strip().splitlines()]
    return lang + "\n" + "\n".join(lines)


def code_hash(language: str, code: str) -> str:
    h = hashlib.sha256()
    h.update(_normalize(language, code).encode("utf-8"))
    return h.hexdigest()


async def cache_get_review_id(code_hash: str) -> Optional[str]:
    r = await get_cache()
    return await r.get(_k(f"codehash:{code_hash}"))


async def cache_set_review_id(
    code_hash: str, review_id: str, ttl: Optional[int] = None
):
    r = await get_cache()
    key = _k(f"codehash:{code_hash}")
    await r.set(key, review_id, ex=ttl or int(settings.CACHE_TTL_SECONDS))
