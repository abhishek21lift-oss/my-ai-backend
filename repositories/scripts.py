from datetime import datetime, timezone
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

    async def publish(
        self,
        id: UUID,
        publish_platform: Optional[str] = None,
    ) -> Optional[Script]:
        kwargs: dict = {"status": ScriptStatusEnum.published}
        if publish_platform:
            kwargs["publish_platform"] = publish_platform
        kwargs["published_at"] = datetime.now(timezone.utc)
        return await self.update(id, **kwargs)

    async def rate(
        self,
        id: UUID,
        rating: int,
        notes: Optional[str] = None,
    ) -> Optional[Script]:
        return await self.update(
            id,
            user_rating=max(1, min(5, rating)),
            user_notes=notes,
            rated_at=datetime.now(timezone.utc),
        )

    async def get_top_rated(
        self,
        user_id: UUID,
        platform: Optional[PlatformEnum] = None,
        topic_id: Optional[UUID] = None,
        limit: int = 3,
    ) -> List[Script]:
        q = select(Script).where(
            Script.user_id == user_id,
            Script.user_rating.isnot(None),
        )
        if platform:
            q = q.where(Script.platform == platform)
        if topic_id:
            q = q.where(Script.topic_id == topic_id)
        q = q.order_by(Script.user_rating.desc()).limit(limit)
        result = await self.session.execute(q)
        return list(result.scalars().all())
