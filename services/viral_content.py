import logging
from typing import List, Optional
from uuid import UUID

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from core.cache import CacheService
from exceptions.app_exceptions import NotFoundError
from models.db import PlatformEnum, ViralContent
from models.schemas import ViralContentCreate, ViralContentUpdate
from repositories.viral_content import ViralContentRepository

logger = logging.getLogger(__name__)

_TTL = 900  # 15 minutes


class ViralContentService:
    def __init__(self, session: AsyncSession, redis: aioredis.Redis) -> None:
        self.repo = ViralContentRepository(session)
        self.cache = CacheService(redis, default_ttl=_TTL)

    async def create(self, user_id: UUID, data: ViralContentCreate) -> ViralContent:
        item = await self.repo.create(user_id=user_id, **data.model_dump())
        await self.cache.invalidate_pattern(CacheService.key("vc", str(user_id), "*"))
        return item

    async def get(self, user_id: UUID, item_id: UUID) -> ViralContent:
        cache_key = CacheService.key("vc", str(user_id), str(item_id))
        if cached := await self.cache.get(cache_key):
            return cached  # type: ignore[return-value]

        item = await self.repo.get_by_id(item_id)
        if not item or item.user_id != user_id:
            raise NotFoundError(f"Viral content {item_id} not found")

        await self.cache.set(cache_key, item)
        return item

    async def list(
        self,
        user_id: UUID,
        offset: int = 0,
        limit: int = 20,
        platform: Optional[PlatformEnum] = None,
        min_viral_score: Optional[float] = None,
    ) -> tuple[List[ViralContent], int]:
        if platform:
            items = await self.repo.get_by_platform(user_id, platform, offset, limit)
        elif min_viral_score is not None:
            items = await self.repo.get_top_viral(user_id, min_viral_score, limit)
        else:
            items = await self.repo.get_by_user(user_id, offset, limit)
        total = await self.repo.count()
        return items, total

    async def update(
        self, user_id: UUID, item_id: UUID, data: ViralContentUpdate
    ) -> ViralContent:
        await self.get(user_id, item_id)  # ownership check
        payload = {k: v for k, v in data.model_dump().items() if v is not None}
        item = await self.repo.update(item_id, **payload)
        await self.cache.delete(CacheService.key("vc", str(user_id), str(item_id)))
        return item  # type: ignore[return-value]

    async def delete(self, user_id: UUID, item_id: UUID) -> None:
        await self.get(user_id, item_id)  # ownership check
        await self.repo.delete(item_id)
        await self.cache.delete(CacheService.key("vc", str(user_id), str(item_id)))

    async def get_top(self, user_id: UUID, limit: int = 20) -> List[ViralContent]:
        return await self.repo.get_top_viral(user_id, min_score=70.0, limit=limit)
