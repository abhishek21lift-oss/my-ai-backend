from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.db import Hook, HookTypeEnum, PlatformEnum
from repositories.base import BaseRepository


class HooksRepository(BaseRepository[Hook]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Hook, session)

    async def get_by_user(
        self, user_id: UUID, offset: int = 0, limit: int = 50
    ) -> List[Hook]:
        result = await self.session.execute(
            select(Hook)
            .where(Hook.user_id == user_id)
            .order_by(Hook.quality_score.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_topic(self, topic_id: UUID) -> List[Hook]:
        result = await self.session.execute(
            select(Hook).where(Hook.topic_id == topic_id)
        )
        return list(result.scalars().all())

    async def get_unused(
        self, user_id: UUID, platform: Optional[PlatformEnum] = None, limit: int = 20
    ) -> List[Hook]:
        q = select(Hook).where(
            Hook.user_id == user_id,
            Hook.is_used == False,
        )
        if platform:
            q = q.where(Hook.platform == platform)
        q = q.order_by(Hook.quality_score.desc()).limit(limit)
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def get_by_type(
        self, user_id: UUID, hook_type: HookTypeEnum
    ) -> List[Hook]:
        result = await self.session.execute(
            select(Hook).where(
                Hook.user_id == user_id,
                Hook.hook_type == hook_type,
            )
        )
        return list(result.scalars().all())

    async def get_by_platform(
        self, user_id: UUID, platform: PlatformEnum
    ) -> List[Hook]:
        result = await self.session.execute(
            select(Hook).where(
                Hook.user_id == user_id,
                Hook.platform == platform,
            )
        )
        return list(result.scalars().all())

    async def get_top_scoring(self, user_id: UUID, limit: int = 10) -> List[Hook]:
        result = await self.session.execute(
            select(Hook)
            .where(Hook.user_id == user_id)
            .order_by(Hook.quality_score.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def mark_used(self, id: UUID) -> Optional[Hook]:
        return await self.update(id, is_used=True)
