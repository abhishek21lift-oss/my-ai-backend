from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.db import Topic
from repositories.base import BaseRepository


class TopicsRepository(BaseRepository[Topic]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Topic, session)

    async def get_by_user(
        self, user_id: UUID, offset: int = 0, limit: int = 50
    ) -> List[Topic]:
        result = await self.session.execute(
            select(Topic)
            .where(Topic.user_id == user_id)
            .order_by(Topic.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_active_by_user(self, user_id: UUID) -> List[Topic]:
        result = await self.session.execute(
            select(Topic).where(
                Topic.user_id == user_id,
                Topic.is_active == True,
            )
        )
        return list(result.scalars().all())

    async def get_by_category(self, user_id: UUID, category: str) -> List[Topic]:
        result = await self.session.execute(
            select(Topic).where(
                Topic.user_id == user_id,
                Topic.category == category,
            )
        )
        return list(result.scalars().all())

    async def name_exists(self, user_id: UUID, name: str) -> bool:
        result = await self.session.execute(
            select(Topic.id).where(
                Topic.user_id == user_id,
                Topic.name == name,
            )
        )
        return result.scalar_one_or_none() is not None

    async def deactivate(self, id: UUID) -> Optional[Topic]:
        return await self.update(id, is_active=False)

    async def count_by_user(self, user_id: UUID) -> int:
        from sqlalchemy import func
        result = await self.session.execute(
            select(func.count()).select_from(Topic).where(Topic.user_id == user_id)
        )
        return result.scalar_one()
