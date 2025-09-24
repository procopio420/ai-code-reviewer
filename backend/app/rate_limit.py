from typing import Optional
from redis.asyncio import Redis, from_url
from .config import settings
import time

_rate: Optional[Redis] = None


async def init_rate_limiter(url: Optional[str] = None):
    global _rate
    if _rate is None:
        _rate = from_url(url or settings.RATE_LIMIT_REDIS_URL, decode_responses=True)
    return _rate


async def get_rate_redis() -> Redis:
    global _rate
    if _rate is None:
        await init_rate_limiter()
    assert _rate is not None
    return _rate


async def close_rate_limiter():
    global _rate
    if _rate is not None:
        await _rate.aclose()
        _rate = None


async def limit_check(ip: str, per_hour: Optional[int] = None):
    r = await get_rate_redis()
    limit = per_hour or int(settings.RATE_LIMIT_PER_HOUR)
    bucket = int(time.time() // 3600)
    key = f"ratelimit:{ip}:{bucket}"
    cnt = await r.incr(key)
    if cnt == 1:
        await r.expire(key, 3600)
    if cnt > limit:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=429, detail=f"Rate limit exceeded ({limit} reviews/hour)"
        )
