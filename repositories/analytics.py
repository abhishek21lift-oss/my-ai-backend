from datetime import datetime
from typing import List
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.db import Analytics, EntityTypeEnum, EventTypeEnum
from repositories.base import BaseRepository


class AnalyticsRepository(BaseRepository[Analytics]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Analytics, session)

    async def get_by_user(
        self, user_id: UUID, offset: int = 0, limit: int = 100
    ) -> List[Analytics]:
        result = await self.session.execute(
            select(Analytics)
            .where(Analytics.user_id == user_id)
            .order_by(Analytics.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_entity(
        self, entity_type: EntityTypeEnum, entity_id: UUID
    ) -> List[Analytics]:
        result = await self.session.execute(
            select(Analytics)
            .where(
                Analytics.entity_type == entity_type,
                Analytics.entity_id == entity_id,
            )
            .order_by(Analytics.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_event(
        self,
        user_id: UUID,
        event_type: EventTypeEnum,
        offset: int = 0,
        limit: int = 100,
    ) -> List[Analytics]:
        result = await self.session.execute(
            select(Analytics)
            .where(
                Analytics.user_id == user_id,
                Analytics.event_type == event_type,
            )
            .order_by(Analytics.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_events(
        self,
        user_id: UUID,
        entity_type: EntityTypeEnum,
        event_type: EventTypeEnum,
    ) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(Analytics).where(
                Analytics.user_id == user_id,
                Analytics.entity_type == entity_type,
                Analytics.event_type == event_type,
            )
        )
        return result.scalar_one()

    async def get_event_summary(
        self, user_id: UUID, since: datetime
    ) -> List[dict]:
        result = await self.session.execute(
            select(
                Analytics.entity_type,
                Analytics.event_type,
                func.count().label("count"),
            )
            .where(
                Analytics.user_id == user_id,
                Analytics.created_at >= since,
            )
            .group_by(Analytics.entity_type, Analytics.event_type)
            .order_by(func.count().desc())
        )
        return [
            {"entity_type": r.entity_type, "event_type": r.event_type, "count": r.count}
            for r in result.all()
        ]

    async def track(
        self,
        user_id: UUID,
        entity_type: EntityTypeEnum,
        entity_id: UUID,
        event_type: EventTypeEnum,
        metadata: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Analytics:
        return await self.create(
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            event_type=event_type,
            metadata_=metadata or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )
