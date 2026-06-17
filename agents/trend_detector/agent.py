import logging
from uuid import UUID

from agents.base import BaseAgent, ToolDef
from agents.context import AgentContext
from agents.trend_detector.prompts import SYSTEM_PROMPT
from models.db import TrendPeriodEnum, TrendVelocityEnum
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
            "Start by calling get_viral_content_batch with these IDs, analyze the patterns, "
            "then call save_trend_analysis with your findings."
        )

    def get_tools(self, ctx: AgentContext) -> list[ToolDef]:
        viral_repo = ViralContentRepository(ctx.session)
        trend_repo = TrendAnalysisRepository(ctx.session)

        async def get_viral_content_batch(viral_content_ids: list[str]) -> dict:
            items = []
            for id_str in viral_content_ids[:20]:  # cap to avoid token overflow
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
                        })
                except (ValueError, Exception):
                    continue
            return {"count": len(items), "items": items}

        async def save_trend_analysis(
            trend_score: float,
            velocity: str,
            keywords: list[str],
            insights: str,
            platforms: list[str] = None,
            period: str = "weekly",
        ) -> dict:
            try:
                vel = TrendVelocityEnum(velocity)
            except ValueError:
                vel = TrendVelocityEnum.stable

            try:
                per = TrendPeriodEnum(period)
            except ValueError:
                per = TrendPeriodEnum.weekly

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
            )
            return {"id": str(trend.id), "trend_score": trend.trend_score, "velocity": trend.velocity.value}

        return [
            ToolDef(
                name="get_viral_content_batch",
                description="Retrieve details for a batch of viral content items by their IDs.",
                parameters={
                    "type": "object",
                    "properties": {
                        "viral_content_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of viral content UUIDs to retrieve",
                        },
                    },
                    "required": ["viral_content_ids"],
                },
                fn=get_viral_content_batch,
            ),
            ToolDef(
                name="save_trend_analysis",
                description="Save the trend analysis findings to the database. Call exactly once.",
                parameters={
                    "type": "object",
                    "properties": {
                        "trend_score": {"type": "number", "description": "Trend strength 0-100"},
                        "velocity": {
                            "type": "string",
                            "enum": ["rising", "falling", "stable", "viral"],
                        },
                        "keywords": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "5-10 keywords driving this trend",
                        },
                        "insights": {"type": "string", "description": "2-3 sentence trend analysis"},
                        "platforms": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Relevant platforms for this trend",
                        },
                        "period": {
                            "type": "string",
                            "enum": ["daily", "weekly", "monthly"],
                            "description": "Analysis period",
                        },
                    },
                    "required": ["trend_score", "velocity", "keywords", "insights"],
                },
                fn=save_trend_analysis,
            ),
        ]
