import logging
from typing import List, Optional
from uuid import UUID

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from core.cache import CacheService
from exceptions.app_exceptions import NotFoundError
from models.db import ReportStatusEnum, ResearchReport
from models.schemas import ResearchGenerateRequest, ResearchReportUpdate
from repositories.research_reports import ResearchReportsRepository
from repositories.topics import TopicsRepository
from services.llm.anthropic import AnthropicService

logger = logging.getLogger(__name__)

_TTL = 1800  # 30 minutes

_SYSTEM = """You are a professional content research analyst. Write comprehensive,
data-driven research reports about social media topics and content trends.
Always respond with valid JSON only."""

_PROMPT = """Topic: {topic_name} ({category})
Report title: {title}
Focus areas: {focus_areas}

Write a detailed research report and return JSON:
{{
  "summary": "<2-3 sentence executive summary>",
  "content": "<full markdown report, 500-1000 words>",
  "key_findings": ["<finding 1>", "<finding 2>", "<finding 3>", "<finding 4>"],
  "sources": [
    {{"title": "<source name>", "url": "<url or 'internal analysis'>", "type": "research|news|data"}}
  ]
}}"""


class ResearchService:
    def __init__(self, session: AsyncSession, redis: aioredis.Redis) -> None:
        self.repo = ResearchReportsRepository(session)
        self.topics_repo = TopicsRepository(session)
        self.cache = CacheService(redis, default_ttl=_TTL)
        self.llm = AnthropicService()

    async def generate(
        self, user_id: UUID, req: ResearchGenerateRequest
    ) -> ResearchReport:
        topic = await self.topics_repo.get_by_id(req.topic_id)
        if not topic or topic.user_id != user_id:
            raise NotFoundError(f"Topic {req.topic_id} not found")

        # Create placeholder report immediately (status=processing)
        report = await self.repo.create(
            user_id=user_id,
            topic_id=req.topic_id,
            title=req.title,
            tags=req.tags,
            status=ReportStatusEnum.processing,
        )

        try:
            prompt = _PROMPT.format(
                topic_name=topic.name,
                category=topic.category or "general",
                title=req.title,
                focus_areas=", ".join(req.focus_areas) if req.focus_areas else "broad overview",
            )
            data = await self.llm.complete_json(_SYSTEM, prompt, max_tokens=4096)

            content = data.get("content", "")
            word_count = len(content.split())

            report = await self.repo.update(
                report.id,
                summary=data.get("summary"),
                content=content,
                key_findings=data.get("key_findings", []),
                sources=data.get("sources", []),
                word_count=word_count,
                status=ReportStatusEnum.completed,
            )
        except Exception as exc:
            await self.repo.set_status(report.id, ReportStatusEnum.draft)
            logger.error("Report generation failed", extra={"ctx_report_id": str(report.id)})
            raise

        await self.cache.invalidate_pattern(
            CacheService.key("research", str(user_id), "*")
        )
        return report  # type: ignore[return-value]

    async def get(self, user_id: UUID, report_id: UUID) -> ResearchReport:
        cache_key = CacheService.key("research", str(user_id), str(report_id))
        if cached := await self.cache.get(cache_key):
            return cached  # type: ignore[return-value]

        report = await self.repo.get_by_id(report_id)
        if not report or report.user_id != user_id:
            raise NotFoundError(f"Research report {report_id} not found")

        await self.cache.set(cache_key, report)
        return report

    async def list(
        self,
        user_id: UUID,
        offset: int = 0,
        limit: int = 20,
        status: Optional[ReportStatusEnum] = None,
    ) -> tuple[List[ResearchReport], int]:
        if status:
            items = await self.repo.get_by_status(user_id, status)
            return items[offset : offset + limit], len(items)
        items = await self.repo.get_by_user(user_id, offset, limit)
        total = await self.repo.count()
        return items, total

    async def update(
        self, user_id: UUID, report_id: UUID, data: ResearchReportUpdate
    ) -> ResearchReport:
        await self.get(user_id, report_id)
        payload = {k: v for k, v in data.model_dump().items() if v is not None}
        if "content" in payload:
            payload["word_count"] = len(payload["content"].split())
        report = await self.repo.update(report_id, **payload)
        await self.cache.delete(
            CacheService.key("research", str(user_id), str(report_id))
        )
        return report  # type: ignore[return-value]

    async def archive(self, user_id: UUID, report_id: UUID) -> ResearchReport:
        await self.get(user_id, report_id)
        report = await self.repo.archive(report_id)
        await self.cache.delete(
            CacheService.key("research", str(user_id), str(report_id))
        )
        return report  # type: ignore[return-value]

    async def delete(self, user_id: UUID, report_id: UUID) -> None:
        await self.get(user_id, report_id)
        await self.repo.delete(report_id)
        await self.cache.delete(
            CacheService.key("research", str(user_id), str(report_id))
        )
