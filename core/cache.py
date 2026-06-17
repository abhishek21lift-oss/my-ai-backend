import json
from datetime import date, datetime
from typing import Any, Optional
from uuid import UUID

import redis.asyncio as aioredis


def _default_serializer(obj: Any) -> str:
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, UUID):
        return str(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


class CacheService:
    def __init__(self, redis: aioredis.Redis, default_ttl: int = 300) -> None:
        self.redis = redis
        self.default_ttl = default_ttl

    async def get(self, key: str) -> Optional[Any]:
        value = await self.redis.get(key)
        return json.loads(value) if value else None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        serialized = json.dumps(value, default=_default_serializer)
        await self.redis.setex(key, ttl or self.default_ttl, serialized)

    async def delete(self, key: str) -> None:
        await self.redis.delete(key)

    async def invalidate_pattern(self, pattern: str) -> None:
        async for key in self.redis.scan_iter(match=pattern, count=100):
            await self.redis.delete(key)

    @staticmethod
    def key(*parts: Any) -> str:
        return ":".join(str(p) for p in parts)
