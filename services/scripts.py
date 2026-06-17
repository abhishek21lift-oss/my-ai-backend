import logging
from typing import List, Optional
from uuid import UUID

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from core.cache import CacheService
from exceptions.app_exceptions import NotFoundError
from models.db import PlatformEnum, Script, ScriptStatusEnum
from models.schemas import ScriptGenerateRequest, ScriptUpdate
from repositories.hooks import HooksRepository
from repositories.scripts import ScriptsRepository
from repositories.topics import TopicsRepository
from services.llm.anthropic import AnthropicService

logger = logging.getLogger(__name__)

_TTL = 600  # 10 minutes

_SYSTEM = """You are an expert scriptwriter for social media content creators.
Write engaging, platform-optimised video/post scripts.
Always respond with valid JSON only."""

_PROMPT = """Topic: {topic_name}
Platform: {platform}
Title: {title}
Opening hook: {hook_content}
Target duration: {duration}
Tone: {tone}
Outline notes: {outline_notes}

Write a complete script and return JSON:
{{
  "content": "<full script text with speaker directions>",
  "outline": [
    {{"section": "<section name>", "duration": <seconds int>, "notes": "<brief note>"}}
  ],
  "word_count": <int>
}}"""


class ScriptService:
    def __init__(self, session: AsyncSession, redis: aioredis.Redis) -> None:
        self.repo = ScriptsRepository(session)
        self.topics_repo = TopicsRepository(session)
        self.hooks_repo = HooksRepository(session)
        self.cache = CacheService(redis, default_ttl=_TTL)
        self.llm = AnthropicService()

    async def generate(self, user_id: UUID, req: ScriptGenerateRequest) -> Script:
        topic = await self.topics_repo.get_by_id(req.topic_id)
        if not topic or topic.user_id != user_id:
            raise NotFoundError(f"Topic {req.topic_id} not found")

        hook_content = "none"
        if req.hook_id:
            hook = await self.hooks_repo.get_by_id(req.hook_id)
            if hook and hook.user_id == user_id:
                hook_content = hook.content

        prompt = _PROMPT.format(
            topic_name=topic.name,
            platform=req.platform.value,
            title=req.title,
            hook_content=hook_content,
            duration=f"{req.duration_seconds}s" if req.duration_seconds else "flexible",
            tone=req.tone or "educational and engaging",
            outline_notes=req.outline_notes or "none",
        )

        data = await self.llm.complete_json(_SYSTEM, prompt, max_tokens=4096)

        content = str(data.get("content", "")).strip()
        word_count = data.get("word_count") or len(content.split())

        script = await self.repo.create(
            user_id=user_id,
            topic_id=req.topic_id,
            hook_id=req.hook_id,
            title=req.title,
            platform=req.platform,
            duration_seconds=req.duration_seconds,
            content=content,
            outline=data.get("outline", []),
            word_count=word_count,
            status=ScriptStatusEnum.draft,
        )

        # Mark the hook as used
        if req.hook_id:
            await self.hooks_repo.mark_used(req.hook_id)

        await self.cache.invalidate_pattern(
            CacheService.key("scripts", str(user_id), "*")
        )
        return script

    async def get(self, user_id: UUID, script_id: UUID) -> Script:
        script = await self.repo.get_by_id(script_id)
        if not script or script.user_id != user_id:
            raise NotFoundError(f"Script {script_id} not found")
        return script

    async def list(
        self,
        user_id: UUID,
        offset: int = 0,
        limit: int = 20,
        status: Optional[ScriptStatusEnum] = None,
        platform: Optional[PlatformEnum] = None,
    ) -> tuple[List[Script], int]:
        if status:
            items = await self.repo.get_by_status(user_id, status, offset, limit)
            return items, len(items)
        if platform:
            items = await self.repo.get_by_platform(user_id, platform)
            return items[offset : offset + limit], len(items)
        items = await self.repo.get_by_user(user_id, offset, limit)
        total = await self.repo.count()
        return items, total

    async def update(
        self, user_id: UUID, script_id: UUID, data: ScriptUpdate
    ) -> Script:
        await self.get(user_id, script_id)
        payload = {k: v for k, v in data.model_dump().items() if v is not None}
        if "content" in payload:
            payload["word_count"] = len(payload["content"].split())
        script = await self.repo.update(script_id, **payload)
        await self.cache.delete(
            CacheService.key("scripts", str(user_id), str(script_id))
        )
        return script  # type: ignore[return-value]

    async def approve(self, user_id: UUID, script_id: UUID) -> Script:
        await self.get(user_id, script_id)
        return await self.repo.approve(script_id)  # type: ignore[return-value]

    async def publish(
        self, user_id: UUID, script_id: UUID, publish_platform: Optional[str] = None
    ) -> Script:
        await self.get(user_id, script_id)
        return await self.repo.publish(script_id, publish_platform)  # type: ignore[return-value]

    async def rate(
        self, user_id: UUID, script_id: UUID, rating: int, notes: Optional[str] = None
    ) -> Script:
        await self.get(user_id, script_id)
        script = await self.repo.rate(script_id, rating, notes)
        await self.cache.delete(CacheService.key("scripts", str(user_id), str(script_id)))
        return script  # type: ignore[return-value]

    async def delete(self, user_id: UUID, script_id: UUID) -> None:
        await self.get(user_id, script_id)
        await self.repo.delete(script_id)
