from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.db import ReportStatusEnum, ResearchReport
from repositories.base import BaseRepository


class ResearchReportsRepository(BaseRepository[ResearchReport]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ResearchReport, session)

    async def get_by_user(
        self, user_id: UUID, offset: int = 0, limit: int = 50
    ) -> List[ResearchReport]:
        result = await self.session.execute(
            select(ResearchReport)
            .where(ResearchReport.user_id == user_id)
            .order_by(ResearchReport.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_topic(
        self, topic_id: UUID, offset: int = 0, limit: int = 50
    ) -> List[ResearchReport]:
        result = await self.session.execute(
            select(ResearchReport)
            .where(ResearchReport.topic_id == topic_id)
            .order_by(ResearchReport.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_status(
        self, user_id: UUID, status: ReportStatusEnum
    ) -> List[ResearchReport]:
        result = await self.session.execute(
            select(ResearchReport).where(
                ResearchReport.user_id == user_id,
                ResearchReport.status == status,
            )
        )
        return list(result.scalars().all())

    async def get_completed(
        self, user_id: UUID, offset: int = 0, limit: int = 50
    ) -> List[ResearchReport]:
        return await self.get_by_status(user_id, ReportStatusEnum.completed)

    async def archive(self, id: UUID) -> Optional[ResearchReport]:
        return await self.update(id, status=ReportStatusEnum.archived)

    async def set_status(
        self, id: UUID, status: ReportStatusEnum
    ) -> Optional[ResearchReport]:
        return await self.update(id, status=status)

    async def search_by_tag(self, user_id: UUID, tag: str) -> List[ResearchReport]:
        result = await self.session.execute(
            select(ResearchReport).where(
                ResearchReport.user_id == user_id,
                ResearchReport.tags.contains([tag]),
            )
        )
        return list(result.scalars().all())
