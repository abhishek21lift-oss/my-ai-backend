from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.db import TrendAnalysis, TrendPeriodEnum, TrendVelocityEnum
from repositories.base import BaseRepository


class TrendAnalysisRepository(BaseRepository[TrendAnalysis]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(TrendAnalysis, session)

    async def get_by_user(
        self, user_id: UUID, offset: int = 0, limit: int = 50
    ) -> List[TrendAnalysis]:
        result = await self.session.execute(
            select(TrendAnalysis)
            .where(TrendAnalysis.user_id == user_id)
            .order_by(TrendAnalysis.analyzed_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_latest_for_topic(
        self, topic_id: UUID, period: Optional[TrendPeriodEnum] = None
    ) -> Optional[TrendAnalysis]:
        q = select(TrendAnalysis).where(TrendAnalysis.topic_id == topic_id)
        if period:
            q = q.where(TrendAnalysis.period == period)
        q = q.order_by(TrendAnalysis.analyzed_at.desc()).limit(1)
        result = await self.session.execute(q)
        return result.scalar_one_or_none()

    async def get_rising(
        self, user_id: UUID, limit: int = 20
    ) -> List[TrendAnalysis]:
        result = await self.session.execute(
            select(TrendAnalysis)
            .where(
                TrendAnalysis.user_id == user_id,
                TrendAnalysis.velocity == TrendVelocityEnum.rising,
            )
            .order_by(TrendAnalysis.trend_score.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_viral(
        self, user_id: UUID, limit: int = 20
    ) -> List[TrendAnalysis]:
        result = await self.session.execute(
            select(TrendAnalysis)
            .where(
                TrendAnalysis.user_id == user_id,
                TrendAnalysis.velocity == TrendVelocityEnum.viral,
            )
            .order_by(TrendAnalysis.trend_score.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_period(
        self, user_id: UUID, period: TrendPeriodEnum, offset: int = 0, limit: int = 50
    ) -> List[TrendAnalysis]:
        result = await self.session.execute(
            select(TrendAnalysis)
            .where(
                TrendAnalysis.user_id == user_id,
                TrendAnalysis.period == period,
            )
            .order_by(TrendAnalysis.analyzed_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_since(
        self, user_id: UUID, since: datetime
    ) -> List[TrendAnalysis]:
        result = await self.session.execute(
            select(TrendAnalysis)
            .where(
                TrendAnalysis.user_id == user_id,
                TrendAnalysis.analyzed_at >= since,
            )
            .order_by(TrendAnalysis.trend_score.desc())
        )
        return list(result.scalars().all())
