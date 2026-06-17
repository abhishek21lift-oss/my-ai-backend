import logging
from uuid import UUID

from agents.base import BaseAgent, ToolDef
from agents.context import AgentContext
from agents.trend_detector.prompts import SYSTEM_PROMPT
from models.db import TrendPeriodEnum, TrendVelocityEnum
from repositories.keywords import KeywordsRepository
from repositories.trend_analysis import TrendAnalysisRepository
from repositories.viral_content import ViralContentRepository

logger = logging.getLogger(__name__)


class TrendDetectorAgent(BaseAgent):
    AGENT_NAME = "trend_detector"
    TASK_TYPE = "detect_trends"

    def get_system_prompt(self, ctx: AgentContext) -> str:
        return SYSTEM_PROMPT

    def get_initial_message(self, ctx: AgentContext) -> str:
        ids = ctx.viral_content_ids()
        return (
            f"Analyze trends for topic_id={ctx.topic_id} on platform={ctx.platform}.\n"
            f"Viral content IDs to analyze: {ids}\n"
            "Call get_viral_content_batch with these IDs, then get_previous_trend for "
            "velocity baseline, analyze patterns, then call save_trend_analysis."
        )

    def get_tools(self, ctx: AgentContext) -> list[ToolDef]:
        viral_repo = ViralContentRepository(ctx.session)
        trend_repo = TrendAnalysisRepository(ctx.session)
        keywords_repo = KeywordsRepository(ctx.session)

        async def get_viral_content_batch(viral_content_ids: list[str]) -> dict:
            items = []
            for id_str in viral_content_ids[:20]:
                try:
                    item = await viral_repo.get_by_id(UUID(id_str))
                    if item:
                        items.append({
                            "id": str(item.id),
                            "title": item.title,
                            "platform": item.platform.value,
                            "content_type": item.content_type.value if item.content_type else None,
                            "views": item.views,
                            "likes": item.likes,
                            "shares": item.shares,
                            "comments": item.comments,
                            "engagement_rate": item.engagement_rate,
                            "viral_score": item.viral_score,
                            "content_url": item.content_url,
                        })
                except (ValueError, Exception):
                    continue
            return {"count": len(items), "items": items}

        async def get_previous_trend() -> dict:
            """Fetch the most recent prior trend analysis for this topic (for velocity baseline)."""
            trend = await trend_repo.get_latest_for_topic(ctx.topic_id, TrendPeriodEnum.weekly)
            if not trend:
                return {"found": False, "message": "No previous trend data — use absolute scoring"}
            return {
                "found": True,
                "previous_trend_score": trend.trend_score,
                "previous_velocity": trend.velocity.value,
                "previous_keywords": trend.keywords,
                "analyzed_at": trend.analyzed_at.isoformat(),
                "previous_trend_id": str(trend.id),
            }

        async def save_trend_analysis(
            trend_score: float,
            velocity: str,
            keywords: list[str],
            insights: str,
            platforms: list[str] = None,
            period: str = "weekly",
            previous_trend_id: str = None,
        ) -> dict:
            try:
                vel = TrendVelocityEnum(velocity)
            except ValueError:
                vel = TrendVelocityEnum.stable

            try:
                per = TrendPeriodEnum(period)
            except ValueError:
                per = TrendPeriodEnum.weekly

            prev_id = UUID(previous_trend_id) if previous_trend_id else None

            trend = await trend_repo.create(
                user_id=ctx.user_id,
                topic_id=ctx.topic_id,
                period=per,
                trend_score=max(0.0, min(100.0, float(trend_score))),
                velocity=vel,
                keywords=keywords[:15],
                insights=insights,
                data_points=[],
                platforms=platforms or [ctx.platform],
                previous_trend_id=prev_id,
            )
            await ctx.session.flush()

            # Persist normalised keywords to the keywords table
            try:
                await keywords_repo.save_trend_keywords(trend.id, keywords[:15])
            except Exception as exc:
                logger.warning("Failed to save normalised keywords: %s", exc)

            return {
                "id": str(trend.id),
                "trend_score": trend.trend_score,
                "velocity": trend.velocity.value,
            }

        return [
            ToolDef(
                name="get_viral_content_batch",
                description="Retrieve engagement details for a batch of viral content items.",
                parameters={
                    "type": "object",
                    "properties": {
                        "viral_content_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["viral_content_ids"],
                },
                fn=get_viral_content_batch,
            ),
            ToolDef(
                name="get_previous_trend",
                description=(
                    "Get the most recent prior trend analysis for this topic. "
                    "Use the previous_trend_score as baseline for velocity calculation."
                ),
                parameters={"type": "object", "properties": {}, "required": []},
                fn=get_previous_trend,
            ),
            ToolDef(
                name="save_trend_analysis",
                description="Save trend analysis findings. Call exactly once.",
                parameters={
                    "type": "object",
                    "properties": {
                        "trend_score": {"type": "number"},
                        "velocity": {"type": "string", "enum": ["rising", "falling", "stable", "viral"]},
                        "keywords": {"type": "array", "items": {"type": "string"}, "description": "5-10 keywords"},
                        "insights": {"type": "string", "description": "2-3 sentence analysis"},
                        "platforms": {"type": "array", "items": {"type": "string"}},
                        "period": {"type": "string", "enum": ["daily", "weekly", "monthly"]},
                        "previous_trend_id": {"type": "string", "description": "UUID of the prior trend (from get_previous_trend)"},
                    },
                    "required": ["trend_score", "velocity", "keywords", "insights"],
                },
                fn=save_trend_analysis,
            ),
        ]
