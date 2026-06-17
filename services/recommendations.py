import logging
from datetime import date, datetime, timezone
from typing import List
from uuid import UUID

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from core.cache import CacheService
from models.db import ReportStatusEnum, ScriptStatusEnum
from models.schemas import DailyRecommendationsResponse, RecommendationItem
from repositories.daily_reports import DailyReportsRepository
from repositories.hooks import HooksRepository
from repositories.research_reports import ResearchReportsRepository
from repositories.scripts import ScriptsRepository
from repositories.trend_analysis import TrendAnalysisRepository
from repositories.viral_content import ViralContentRepository

logger = logging.getLogger(__name__)

_TTL = 3600 * 6  # 6 hours — recommendations are stable within a day


class RecommendationsService:
    def __init__(self, session: AsyncSession, redis: aioredis.Redis) -> None:
        self.hooks_repo = HooksRepository(session)
        self.scripts_repo = ScriptsRepository(session)
        self.trends_repo = TrendAnalysisRepository(session)
        self.research_repo = ResearchReportsRepository(session)
        self.viral_repo = ViralContentRepository(session)
        self.daily_repo = DailyReportsRepository(session)
        self.cache = CacheService(redis, default_ttl=_TTL)

    async def get_daily(
        self, user_id: UUID, monthly_token_quota: int | None = None
    ) -> DailyRecommendationsResponse:
        today = date.today()
        cache_key = CacheService.key("recs", str(user_id), str(today))

        if cached := await self.cache.get(cache_key):
            return DailyRecommendationsResponse(**cached)

        items: List[RecommendationItem] = []

        # 1. Unused high-quality hooks (priority 9)
        hooks = await self.hooks_repo.get_unused(user_id, limit=3)
        for h in hooks:
            items.append(RecommendationItem(
                type="hook",
                id=h.id,
                title=f"{h.hook_type.value.title()} hook for {h.platform.value}",
                description=h.content[:120] + ("..." if len(h.content) > 120 else ""),
                priority=9,
                action="use_hook",
                metadata={"platform": h.platform.value, "quality_score": h.quality_score},
            ))

        # 2. Scripts ready for approval (priority 8)
        drafts = await self.scripts_repo.get_by_status(
            user_id, ScriptStatusEnum.draft, limit=3
        )
        for s in drafts:
            items.append(RecommendationItem(
                type="script",
                id=s.id,
                title=s.title,
                description=f"{s.platform.value} script ready for review",
                priority=8,
                action="review_script",
                metadata={"platform": s.platform.value, "word_count": s.word_count},
            ))

        # 3. Approved scripts ready to publish (priority 10)
        approved = await self.scripts_repo.get_by_status(
            user_id, ScriptStatusEnum.approved, limit=3
        )
        for s in approved:
            items.append(RecommendationItem(
                type="script",
                id=s.id,
                title=s.title,
                description=f"Ready to publish on {s.platform.value}",
                priority=10,
                action="publish_script",
                metadata={"platform": s.platform.value},
            ))

        # 4. Rising trends to explore (priority 7)
        rising = await self.trends_repo.get_rising(user_id, limit=3)
        for t in rising:
            items.append(RecommendationItem(
                type="trend",
                id=t.id,
                title=f"Rising trend (score {t.trend_score:.0f})",
                description=t.insights[:120] + "..." if t.insights and len(t.insights) > 120 else (t.insights or ""),
                priority=7,
                action="explore_trend",
                metadata={"trend_score": t.trend_score, "velocity": t.velocity.value},
            ))

        # 5. Completed research reports to read (priority 6)
        reports = await self.research_repo.get_by_status(
            user_id, ReportStatusEnum.completed
        )
        for r in reports[:2]:
            items.append(RecommendationItem(
                type="report",
                id=r.id,
                title=r.title,
                description=r.summary[:120] + "..." if r.summary and len(r.summary) > 120 else (r.summary or ""),
                priority=6,
                action="read_report",
                metadata={"word_count": r.word_count},
            ))

        # 6. Top viral content to analyse (priority 5)
        viral = await self.viral_repo.get_top_viral(user_id, min_score=80.0, limit=3)
        for v in viral:
            items.append(RecommendationItem(
                type="viral_content",
                id=v.id,
                title=v.title[:80],
                description=f"Viral score {v.viral_score:.1f} on {v.platform.value}",
                priority=5,
                action="analyse_content",
                metadata={"viral_score": v.viral_score, "platform": v.platform.value},
            ))

        # Sort by priority descending, cap at 15
        items.sort(key=lambda x: x.priority, reverse=True)
        items = items[:15]

        # Derive summary stats
        top_platforms: List[str] = list(
            {i.metadata.get("platform", "") for i in items if "platform" in i.metadata}
        )[:3]
        top_topics: List[str] = [t.keywords[0] for t in rising if t.keywords][:3]

        response = DailyRecommendationsResponse(
            report_date=today,
            user_id=user_id,
            items=items,
            summary=(
                f"{len(approved)} script(s) ready to publish, "
                f"{len(hooks)} unused hook(s) waiting, "
                f"{len(rising)} rising trend(s) to explore."
            ),
            top_platforms=top_platforms,
            top_trending_topics=top_topics,
            tokens_quota_remaining=monthly_token_quota,
            generated_at=datetime.now(timezone.utc),
        )

        await self.cache.set(cache_key, response.model_dump())
        return response
