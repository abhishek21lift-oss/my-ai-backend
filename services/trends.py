import logging
from typing import List, Optional
from uuid import UUID

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from core.cache import CacheService
from exceptions.app_exceptions import NotFoundError
from models.db import TrendAnalysis, TrendPeriodEnum, TrendVelocityEnum
from models.schemas import TrendAnalyzeRequest, TrendAnalysisCreate
from repositories.topics import TopicsRepository
from repositories.trend_analysis import TrendAnalysisRepository
from repositories.viral_content import ViralContentRepository
from services.llm.anthropic import AnthropicService

logger = logging.getLogger(__name__)

_TTL = 3600  # 1 hour

_SYSTEM = """You are a social media trend analyst. Given a topic and available data,
produce a concise trend analysis. Always respond with valid JSON only."""

_PROMPT = """Topic: {topic_name}
Category: {category}
Period: {period}
Recent viral content titles: {viral_titles}
Extra context: {context}

Return JSON:
{{
  "trend_score": <0-100 float>,
  "velocity": "<rising|falling|stable|viral>",
  "keywords": ["<kw1>", "<kw2>", ...],
  "insights": "<2-3 sentence analysis>",
  "platforms": ["<platform1>", ...]
}}"""


class TrendService:
    def __init__(self, session: AsyncSession, redis: aioredis.Redis) -> None:
        self.repo = TrendAnalysisRepository(session)
        self.topics_repo = TopicsRepository(session)
        self.viral_repo = ViralContentRepository(session)
        self.cache = CacheService(redis, default_ttl=_TTL)
        self.llm = AnthropicService()

    async def analyze(self, user_id: UUID, req: TrendAnalyzeRequest) -> TrendAnalysis:
        topic = await self.topics_repo.get_by_id(req.topic_id)
        if not topic or topic.user_id != user_id:
            raise NotFoundError(f"Topic {req.topic_id} not found")

        viral = await self.viral_repo.get_by_topic(req.topic_id, limit=10)
        viral_titles = [v.title for v in viral]

        prompt = _PROMPT.format(
            topic_name=topic.name,
            category=topic.category or "general",
            period=req.period.value,
            viral_titles=", ".join(viral_titles) if viral_titles else "none yet",
            context=req.context or "none",
        )

        data = await self.llm.complete_json(_SYSTEM, prompt)

        trend = await self.repo.create(
            user_id=user_id,
            topic_id=req.topic_id,
            period=req.period,
            trend_score=float(data.get("trend_score", 0)),
            velocity=TrendVelocityEnum(data.get("velocity", "stable")),
            keywords=data.get("keywords", []),
            insights=data.get("insights"),
            data_points=[],
            platforms=data.get("platforms", []),
        )
        await self.cache.invalidate_pattern(
            CacheService.key("trend", str(user_id), "*")
        )
        return trend

    async def create_manual(
        self, user_id: UUID, data: TrendAnalysisCreate
    ) -> TrendAnalysis:
        trend = await self.repo.create(user_id=user_id, **data.model_dump())
        await self.cache.invalidate_pattern(
            CacheService.key("trend", str(user_id), "*")
        )
        return trend

    async def get(self, user_id: UUID, trend_id: UUID) -> TrendAnalysis:
        trend = await self.repo.get_by_id(trend_id)
        if not trend or trend.user_id != user_id:
            raise NotFoundError(f"Trend analysis {trend_id} not found")
        return trend

    async def list(
        self,
        user_id: UUID,
        offset: int = 0,
        limit: int = 20,
        period: Optional[TrendPeriodEnum] = None,
    ) -> tuple[List[TrendAnalysis], int]:
        if period:
            items = await self.repo.get_by_period(user_id, period, offset, limit)
        else:
            items = await self.repo.get_by_user(user_id, offset, limit)
        total = await self.repo.count()
        return items, total

    async def get_rising(self, user_id: UUID) -> List[TrendAnalysis]:
        cache_key = CacheService.key("trend", str(user_id), "rising")
        if cached := await self.cache.get(cache_key):
            return cached  # type: ignore[return-value]
        items = await self.repo.get_rising(user_id)
        await self.cache.set(cache_key, items)
        return items

    async def get_viral(self, user_id: UUID) -> List[TrendAnalysis]:
        cache_key = CacheService.key("trend", str(user_id), "viral")
        if cached := await self.cache.get(cache_key):
            return cached  # type: ignore[return-value]
        items = await self.repo.get_viral(user_id)
        await self.cache.set(cache_key, items)
        return items
