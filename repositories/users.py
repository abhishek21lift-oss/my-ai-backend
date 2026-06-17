from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.db import PlanEnum, User
from repositories.base import BaseRepository


class UsersRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_active(self, offset: int = 0, limit: int = 50) -> List[User]:
        result = await self.session.execute(
            select(User)
            .where(User.is_active == True)
            .order_by(User.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_plan(self, plan: PlanEnum) -> List[User]:
        result = await self.session.execute(
            select(User).where(User.plan == plan)
        )
        return list(result.scalars().all())

    async def email_exists(self, email: str) -> bool:
        result = await self.session.execute(
            select(User.id).where(User.email == email)
        )
        return result.scalar_one_or_none() is not None

    async def deactivate(self, id: UUID) -> Optional[User]:
        return await self.update(id, is_active=False)

    async def update_plan(self, id: UUID, plan: PlanEnum) -> Optional[User]:
        return await self.update(id, plan=plan)

    async def set_token_quota(
        self, id: UUID, quota: Optional[int]
    ) -> Optional[User]:
        return await self.update(id, monthly_token_quota=quota)
