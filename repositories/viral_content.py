from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.db import PlatformEnum, ViralContent
from repositories.base import BaseRepository


class ViralContentRepository(BaseRepository[ViralContent]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ViralContent, session)

    async def get_by_user(
        self, user_id: UUID, offset: int = 0, limit: int = 50
    ) -> List[ViralContent]:
        result = await self.session.execute(
            select(ViralContent)
            .where(ViralContent.user_id == user_id)
            .order_by(ViralContent.viral_score.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_topic(
        self, topic_id: UUID, offset: int = 0, limit: int = 50
    ) -> List[ViralContent]:
        result = await self.session.execute(
            select(ViralContent)
            .where(ViralContent.topic_id == topic_id)
            .order_by(ViralContent.viral_score.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_platform(
        self, user_id: UUID, platform: PlatformEnum, offset: int = 0, limit: int = 50
    ) -> List[ViralContent]:
        result = await self.session.execute(
            select(ViralContent)
            .where(
                ViralContent.user_id == user_id,
                ViralContent.platform == platform,
            )
            .order_by(ViralContent.viral_score.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_top_viral(
        self, user_id: UUID, min_score: float = 70.0, limit: int = 20
    ) -> List[ViralContent]:
        result = await self.session.execute(
            select(ViralContent)
            .where(
                ViralContent.user_id == user_id,
                ViralContent.viral_score >= min_score,
            )
            .order_by(ViralContent.viral_score.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_avg_viral_score(self, user_id: UUID) -> float:
        result = await self.session.execute(
            select(func.avg(ViralContent.viral_score)).where(
                ViralContent.user_id == user_id
            )
        )
        return result.scalar_one() or 0.0

    async def count_by_platform(
        self, user_id: UUID, platform: PlatformEnum
    ) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(ViralContent).where(
                ViralContent.user_id == user_id,
                ViralContent.platform == platform,
            )
        )
        return result.scalar_one()
