from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.db import AgentLog, AgentStatusEnum
from repositories.base import BaseRepository


class AgentLogsRepository(BaseRepository[AgentLog]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(AgentLog, session)

    async def get_by_user(
        self, user_id: UUID, offset: int = 0, limit: int = 50
    ) -> List[AgentLog]:
        result = await self.session.execute(
            select(AgentLog)
            .where(AgentLog.user_id == user_id)
            .order_by(AgentLog.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_status(
        self, status: AgentStatusEnum, offset: int = 0, limit: int = 50
    ) -> List[AgentLog]:
        result = await self.session.execute(
            select(AgentLog)
            .where(AgentLog.status == status)
            .order_by(AgentLog.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_agent(
        self, agent_name: str, offset: int = 0, limit: int = 50
    ) -> List[AgentLog]:
        result = await self.session.execute(
            select(AgentLog)
            .where(AgentLog.agent_name == agent_name)
            .order_by(AgentLog.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_sub_tasks(self, parent_log_id: UUID) -> List[AgentLog]:
        result = await self.session.execute(
            select(AgentLog).where(AgentLog.parent_log_id == parent_log_id)
        )
        return list(result.scalars().all())

    async def get_recent_failures(
        self, user_id: Optional[UUID] = None, limit: int = 20
    ) -> List[AgentLog]:
        q = select(AgentLog).where(AgentLog.status == AgentStatusEnum.failed)
        if user_id:
            q = q.where(AgentLog.user_id == user_id)
        q = q.order_by(AgentLog.created_at.desc()).limit(limit)
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def mark_running(self, id: UUID) -> Optional[AgentLog]:
        return await self.update(
            id, status=AgentStatusEnum.running, started_at=datetime.utcnow()
        )

    async def mark_completed(
        self, id: UUID, output: dict, input_tokens: int, output_tokens: int, duration_ms: int
    ) -> Optional[AgentLog]:
        return await self.update(
            id,
            status=AgentStatusEnum.completed,
            output=output,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            duration_ms=duration_ms,
            completed_at=datetime.utcnow(),
        )

    async def mark_failed(
        self, id: UUID, error: str, error_traceback: Optional[str] = None
    ) -> Optional[AgentLog]:
        return await self.update(
            id,
            status=AgentStatusEnum.failed,
            error=error,
            error_traceback=error_traceback,
            completed_at=datetime.utcnow(),
        )

    async def increment_retry(self, id: UUID) -> Optional[AgentLog]:
        log = await self.get_by_id(id)
        if not log:
            return None
        return await self.update(id, retry_count=log.retry_count + 1)
