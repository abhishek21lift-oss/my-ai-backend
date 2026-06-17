import logging
from uuid import UUID

from agents.base import BaseAgent, ToolDef
from agents.context import AgentContext
from agents.hook_generator.prompts import SYSTEM_PROMPT
from models.db import HookTypeEnum, PlatformEnum
from repositories.hooks import HooksRepository
from repositories.research_reports import ResearchReportsRepository
from repositories.trend_analysis import TrendAnalysisRepository

logger = logging.getLogger(__name__)


class HookGeneratorAgent(BaseAgent):
    AGENT_NAME = "hook_generator"
    TASK_TYPE = "generate_hooks"

    def get_system_prompt(self, ctx: AgentContext) -> str:
        return SYSTEM_PROMPT

    def get_initial_message(self, ctx: AgentContext) -> str:
        return (
            f"Generate hooks for topic_id={ctx.topic_id} on platform={ctx.platform}.\n"
            f"Fitness report ID: {ctx.report_id()}\n"
            f"Trend ID: {ctx.trend_id()}\n"
            "Call get_fitness_insights and get_trending_keywords to gather context, "
            "then call save_hook exactly 5 times to create diverse, high-quality hooks."
        )

    def get_tools(self, ctx: AgentContext) -> list[ToolDef]:
        report_repo = ResearchReportsRepository(ctx.session)
        trend_repo = TrendAnalysisRepository(ctx.session)
        hooks_repo = HooksRepository(ctx.session)

        async def get_fitness_insights(report_id: str = None) -> dict:
            rid = report_id or ctx.report_id()
            if not rid:
                return {"error": "no report_id available"}
            report = await report_repo.get_by_id(UUID(rid))
            if not report:
                return {"error": f"Report {rid} not found"}
            return {
                "id": str(report.id),
                "summary": report.summary,
                "key_findings": report.key_findings,
                "fitness_score": ctx.fitness_score(),
                "platform": ctx.platform,
            }

        async def get_trending_keywords(trend_id: str = None) -> dict:
            tid = trend_id or ctx.trend_id()
            if not tid:
                return {"error": "no trend_id available"}
            trend = await trend_repo.get_by_id(UUID(tid))
            if not trend:
                return {"error": f"Trend {tid} not found"}
            return {
                "keywords": trend.keywords,
                "trend_score": trend.trend_score,
                "velocity": trend.velocity.value,
                "insights": trend.insights,
            }

        async def save_hook(
            hook_type: str,
            content: str,
            quality_score: float,
            platform: str = None,
        ) -> dict:
            try:
                ht = HookTypeEnum(hook_type)
            except ValueError:
                ht = HookTypeEnum.statement

            plat = PlatformEnum(platform) if platform else PlatformEnum(ctx.platform)

            hook = await hooks_repo.create(
                user_id=ctx.user_id,
                topic_id=ctx.topic_id,
                viral_content_id=None,
                hook_type=ht,
                platform=plat,
                content=content,
                character_count=len(content),
                quality_score=max(0.0, min(100.0, float(quality_score))),
                is_used=False,
            )
            return {"id": str(hook.id), "hook_type": ht.value, "quality_score": hook.quality_score}

        return [
            ToolDef(
                name="get_fitness_insights",
                description="Retrieve the content fitness report to understand optimal hook styles and tone.",
                parameters={
                    "type": "object",
                    "properties": {
                        "report_id": {"type": "string", "description": "Fitness report UUID (optional)"},
                    },
                    "required": [],
                },
                fn=get_fitness_insights,
            ),
            ToolDef(
                name="get_trending_keywords",
                description="Get trending keywords and insights to incorporate into hooks.",
                parameters={
                    "type": "object",
                    "properties": {
                        "trend_id": {"type": "string", "description": "Trend analysis UUID (optional)"},
                    },
                    "required": [],
                },
                fn=get_trending_keywords,
            ),
            ToolDef(
                name="save_hook",
                description=(
                    "Save one hook to the database. Call exactly 5 times with different hook_types. "
                    "Returns the saved hook's UUID."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "hook_type": {
                            "type": "string",
                            "enum": ["question", "statement", "statistic", "story",
                                     "controversy", "list", "challenge"],
                        },
                        "content": {"type": "string", "description": "The hook text"},
                        "quality_score": {"type": "number", "description": "Estimated quality 0-100"},
                        "platform": {
                            "type": "string",
                            "enum": ["youtube", "tiktok", "instagram", "twitter", "linkedin", "reddit", "other"],
                            "description": "Platform (defaults to task platform)",
                        },
                    },
                    "required": ["hook_type", "content", "quality_score"],
                },
                fn=save_hook,
            ),
        ]
