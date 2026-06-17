from datetime import date
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.db import DailyReport
from repositories.base import BaseRepository


class DailyReportsRepository(BaseRepository[DailyReport]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(DailyReport, session)

    async def get_by_user(
        self, user_id: UUID, offset: int = 0, limit: int = 30
    ) -> List[DailyReport]:
        result = await self.session.execute(
            select(DailyReport)
            .where(DailyReport.user_id == user_id)
            .order_by(DailyReport.report_date.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_date(
        self, user_id: UUID, report_date: date
    ) -> Optional[DailyReport]:
        result = await self.session.execute(
            select(DailyReport).where(
                DailyReport.user_id == user_id,
                DailyReport.report_date == report_date,
            )
        )
        return result.scalar_one_or_none()

    async def get_date_range(
        self, user_id: UUID, start: date, end: date
    ) -> List[DailyReport]:
        result = await self.session.execute(
            select(DailyReport)
            .where(
                DailyReport.user_id == user_id,
                DailyReport.report_date >= start,
                DailyReport.report_date <= end,
            )
            .order_by(DailyReport.report_date.asc())
        )
        return list(result.scalars().all())

    async def get_latest(self, user_id: UUID) -> Optional[DailyReport]:
        result = await self.session.execute(
            select(DailyReport)
            .where(DailyReport.user_id == user_id)
            .order_by(DailyReport.report_date.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def upsert(self, user_id: UUID, report_date: date, **kwargs) -> DailyReport:
        existing = await self.get_by_date(user_id, report_date)
        if existing:
            return await self.update(existing.id, **kwargs)
        return await self.create(user_id=user_id, report_date=report_date, **kwargs)
