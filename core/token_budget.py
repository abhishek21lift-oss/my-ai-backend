import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


class TokenBudgetService:
    """Per-user monthly token tracking and quota enforcement."""

    def __init__(self, redis: aioredis.Redis) -> None:
        self._redis = redis

    def _key(self, user_id: UUID) -> str:
        month = datetime.now().strftime("%Y-%m")
        return f"tokens:{user_id}:{month}"

    async def consume(self, user_id: UUID, tokens: int) -> int:
        """Increment token counter. Returns new total."""
        key = self._key(user_id)
        total = await self._redis.incrby(key, tokens)
        if total == tokens:
            # First write this month — set 35-day TTL
            await self._redis.expire(key, 86400 * 35)
        logger.debug("Token consume", extra={"ctx_user_id": str(user_id), "ctx_tokens": tokens, "ctx_total": total})
        return total

    async def get_used(self, user_id: UUID) -> int:
        """Return tokens consumed this month."""
        val = await self._redis.get(self._key(user_id))
        return int(val) if val else 0

    async def get_remaining(self, user_id: UUID, quota: Optional[int]) -> Optional[int]:
        """Return remaining tokens, or None if no quota set."""
        if quota is None:
            return None
        used = await self.get_used(user_id)
        return max(0, quota - used)

    async def is_within_budget(self, user_id: UUID, quota: Optional[int]) -> bool:
        """True if quota is not set or not exceeded."""
        if quota is None:
            return True
        used = await self.get_used(user_id)
        return used < quota
