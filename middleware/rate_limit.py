import time
import logging
from typing import Tuple

import redis.asyncio as aioredis

from exceptions.app_exceptions import RateLimitError

logger = logging.getLogger(__name__)


async def check_rate_limit(
    redis: aioredis.Redis,
    key_id: str,
    limit_rpm: int,
) -> Tuple[bool, int]:
    """
    Sliding-window rate limiter using a Redis sorted set.
    Returns (is_allowed, current_count).
    Raises RateLimitError when the limit is exceeded.
    """
    now = time.time()
    window_start = now - 60.0
    redis_key = f"rl:rpm:{key_id}"

    async with redis.pipeline(transaction=True) as pipe:
        pipe.zremrangebyscore(redis_key, "-inf", window_start)
        pipe.zadd(redis_key, {f"{now}:{key_id}": now})
        pipe.zcard(redis_key)
        pipe.expire(redis_key, 60)
        results = await pipe.execute()

    current_count: int = results[2]

    if current_count > limit_rpm:
        logger.warning(
            "Rate limit exceeded",
            extra={"ctx_key_id": key_id, "ctx_count": current_count, "ctx_limit": limit_rpm},
        )
        raise RateLimitError(
            f"Rate limit exceeded: {current_count}/{limit_rpm} requests per minute",
            retry_after=60,
        )

    return True, current_count


async def check_daily_token_quota(
    redis: aioredis.Redis,
    user_id: str,
    tokens_to_add: int,
    daily_limit: int,
) -> None:
    """Sliding-window token quota check (24-hour window)."""
    from exceptions.app_exceptions import QuotaExceededError

    redis_key = f"quota:tokens:{user_id}"
    current = await redis.get(redis_key)
    used = int(current) if current else 0

    if used + tokens_to_add > daily_limit:
        raise QuotaExceededError(
            f"Daily token quota exceeded: {used}/{daily_limit} tokens used"
        )

    pipe = redis.pipeline()
    pipe.incrby(redis_key, tokens_to_add)
    pipe.expire(redis_key, 86400)
    await pipe.execute()
