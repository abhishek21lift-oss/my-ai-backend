from dataclasses import dataclass, field
from typing import Any, Optional
from uuid import UUID

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class AgentContext:
    user_id: UUID
    topic_id: UUID
    platform: str           # PlatformEnum.value
    session: AsyncSession
    redis: aioredis.Redis
    parent_log_id: Optional[UUID] = None
    extra: dict[str, Any] = field(default_factory=dict)

    # Helpers for typed access to inter-agent payload keys
    def viral_content_ids(self) -> list[str]:
        return self.extra.get("viral_content_ids", [])

    def trend_id(self) -> Optional[str]:
        return self.extra.get("trend_id")

    def report_id(self) -> Optional[str]:
        return self.extra.get("report_id")

    def fitness_score(self) -> Optional[float]:
        return self.extra.get("fitness_score")

    def hook_ids(self) -> list[str]:
        return self.extra.get("hook_ids", [])


@dataclass
class AgentResult:
    output: dict[str, Any]
    input_tokens: int
    output_tokens: int
    duration_ms: int
    log_id: UUID
