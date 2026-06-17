from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.db import PlatformEnum, Script, ScriptStatusEnum
from repositories.base import BaseRepository


class ScriptsRepository(BaseRepository[Script]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Script, session)

    async def get_by_user(
        self, user_id: UUID, offset: int = 0, limit: int = 50
    ) -> List[Script]:
        result = await self.session.execute(
            select(Script)
            .where(Script.user_id == user_id)
            .order_by(Script.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_topic(self, topic_id: UUID) -> List[Script]:
        result = await self.session.execute(
            select(Script).where(Script.topic_id == topic_id)
        )
        return list(result.scalars().all())

    async def get_by_hook(self, hook_id: UUID) -> List[Script]:
        result = await self.session.execute(
            select(Script).where(Script.hook_id == hook_id)
        )
        return list(result.scalars().all())

    async def get_by_status(
        self, user_id: UUID, status: ScriptStatusEnum, offset: int = 0, limit: int = 50
    ) -> List[Script]:
        result = await self.session.execute(
            select(Script)
            .where(
                Script.user_id == user_id,
                Script.status == status,
            )
            .order_by(Script.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_platform(
        self, user_id: UUID, platform: PlatformEnum
    ) -> List[Script]:
        result = await self.session.execute(
            select(Script).where(
                Script.user_id == user_id,
                Script.platform == platform,
            )
        )
        return list(result.scalars().all())

    async def get_published(
        self, user_id: UUID, offset: int = 0, limit: int = 50
    ) -> List[Script]:
        return await self.get_by_status(user_id, ScriptStatusEnum.published, offset, limit)

    async def set_status(
        self, id: UUID, status: ScriptStatusEnum
    ) -> Optional[Script]:
        return await self.update(id, status=status)

    async def approve(self, id: UUID) -> Optional[Script]:
        return await self.set_status(id, ScriptStatusEnum.approved)

    async def publish(self, id: UUID) -> Optional[Script]:
        return await self.set_status(id, ScriptStatusEnum.published)
