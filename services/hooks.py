import logging
from typing import List, Optional
from uuid import UUID

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from core.cache import CacheService
from exceptions.app_exceptions import NotFoundError
from models.db import Hook, HookTypeEnum, PlatformEnum
from models.schemas import HookGenerateRequest
from repositories.hooks import HooksRepository
from repositories.topics import TopicsRepository
from repositories.viral_content import ViralContentRepository
from services.llm.anthropic import AnthropicService

logger = logging.getLogger(__name__)

_TTL = 600  # 10 minutes

_SYSTEM = """You are an expert social media copywriter specializing in viral hooks.
Create attention-grabbing opening lines optimized for the target platform.
Always respond with valid JSON only."""

_PROMPT = """Topic: {topic_name}
Platform: {platform}
Hook types requested: {hook_types}
Number of hooks: {count}
Viral content inspiration: {viral_titles}
Style notes: {style_notes}

Generate {count} hooks and return JSON:
{{
  "hooks": [
    {{
      "hook_type": "<question|statement|statistic|story|controversy|list|challenge>",
      "content": "<hook text>",
      "quality_score": <0-100 float>
    }}
  ]
}}"""


class HookService:
    def __init__(self, session: AsyncSession, redis: aioredis.Redis) -> None:
        self.repo = HooksRepository(session)
        self.topics_repo = TopicsRepository(session)
        self.viral_repo = ViralContentRepository(session)
        self.cache = CacheService(redis, default_ttl=_TTL)
        self.llm = AnthropicService()

    async def generate(self, user_id: UUID, req: HookGenerateRequest) -> List[Hook]:
        topic = await self.topics_repo.get_by_id(req.topic_id)
        if not topic or topic.user_id != user_id:
            raise NotFoundError(f"Topic {req.topic_id} not found")

        viral = await self.viral_repo.get_by_topic(req.topic_id, limit=5)
        viral_titles = [v.title for v in viral]

        hook_types = (
            ", ".join(h.value for h in req.hook_types)
            if req.hook_types
            else "any type"
        )

        prompt = _PROMPT.format(
            topic_name=topic.name,
            platform=req.platform.value,
            hook_types=hook_types,
            count=req.count,
            viral_titles=", ".join(viral_titles) if viral_titles else "none",
            style_notes=req.style_notes or "none",
        )

        data = await self.llm.complete_json(_SYSTEM, prompt)
        raw_hooks = data.get("hooks", [])

        created: List[Hook] = []
        for item in raw_hooks[: req.count]:
            hook_type_val = item.get("hook_type", "statement")
            try:
                hook_type = HookTypeEnum(hook_type_val)
            except ValueError:
                hook_type = HookTypeEnum.statement

            content = str(item.get("content", "")).strip()
            if not content:
                continue

            hook = await self.repo.create(
                user_id=user_id,
                topic_id=req.topic_id,
                viral_content_id=req.viral_content_id,
                hook_type=hook_type,
                platform=req.platform,
                content=content,
                character_count=len(content),
                quality_score=float(item.get("quality_score", 0)),
                is_used=False,
            )
            created.append(hook)

        await self.cache.invalidate_pattern(
            CacheService.key("hooks", str(user_id), "*")
        )
        return created

    async def get(self, user_id: UUID, hook_id: UUID) -> Hook:
        hook = await self.repo.get_by_id(hook_id)
        if not hook or hook.user_id != user_id:
            raise NotFoundError(f"Hook {hook_id} not found")
        return hook

    async def list(
        self,
        user_id: UUID,
        offset: int = 0,
        limit: int = 20,
        platform: Optional[PlatformEnum] = None,
        unused_only: bool = False,
    ) -> tuple[List[Hook], int]:
        if unused_only:
            items = await self.repo.get_unused(user_id, platform, limit)
            return items, len(items)
        if platform:
            items = await self.repo.get_by_platform(user_id, platform)
            return items[offset : offset + limit], len(items)
        items = await self.repo.get_by_user(user_id, offset, limit)
        total = await self.repo.count()
        return items, total

    async def mark_used(self, user_id: UUID, hook_id: UUID) -> Hook:
        await self.get(user_id, hook_id)
        hook = await self.repo.mark_used(hook_id)
        await self.cache.delete(CacheService.key("hooks", str(user_id), str(hook_id)))
        return hook  # type: ignore[return-value]

    async def delete(self, user_id: UUID, hook_id: UUID) -> None:
        await self.get(user_id, hook_id)
        await self.repo.delete(hook_id)

    async def rate(
        self, user_id: UUID, hook_id: UUID, rating: int, notes: Optional[str] = None
    ) -> Hook:
        await self.get(user_id, hook_id)
        hook = await self.repo.rate(hook_id, rating, notes)
        await self.cache.delete(CacheService.key("hooks", str(user_id), str(hook_id)))
        return hook  # type: ignore[return-value]

    async def get_top(self, user_id: UUID, limit: int = 10) -> List[Hook]:
        return await self.repo.get_top_scoring(user_id, limit)
