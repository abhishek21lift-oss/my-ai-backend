from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, update

from models.db import ApiKey
from repositories.base import BaseRepository


class ApiKeysRepository(BaseRepository[ApiKey]):
    def __init__(self, session):
        super().__init__(session, ApiKey)

    async def get_by_user(self, user_id: UUID) -> List[ApiKey]:
        result = await self.session.execute(
            select(ApiKey)
            .where(ApiKey.user_id == user_id, ApiKey.is_active.is_(True))
            .order_by(ApiKey.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_prefix(self, key_prefix: str) -> Optional[ApiKey]:
        result = await self.session.execute(
            select(ApiKey).where(
                ApiKey.key_prefix == key_prefix,
                ApiKey.is_active.is_(True),
            )
        )
        return result.scalars().first()

    async def deactivate(self, key_id: UUID) -> None:
        await self.session.execute(
            update(ApiKey).where(ApiKey.id == key_id).values(is_active=False)
        )
        await self.session.commit()

    async def touch_last_used(self, key_id: UUID) -> None:
        await self.session.execute(
            update(ApiKey)
            .where(ApiKey.id == key_id)
            .values(last_used_at=datetime.now(timezone.utc))
        )
        await self.session.commit()
