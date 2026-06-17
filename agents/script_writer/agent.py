import logging
from uuid import UUID

from agents.base import BaseAgent, ToolDef
from agents.context import AgentContext
from agents.script_writer.prompts import SYSTEM_PROMPT
from models.db import PlatformEnum, ScriptStatusEnum
from repositories.hooks import HooksRepository
from repositories.research_reports import ResearchReportsRepository
from repositories.scripts import ScriptsRepository
from repositories.trend_analysis import TrendAnalysisRepository

logger = logging.getLogger(__name__)


class ScriptWriterAgent(BaseAgent):
    AGENT_NAME = "script_writer"
    TASK_TYPE = "write_scripts"

    def get_system_prompt(self, ctx: AgentContext) -> str:
        return SYSTEM_PROMPT

    def get_initial_message(self, ctx: AgentContext) -> str:
        return (
            f"Write scripts for topic_id={ctx.topic_id} on platform={ctx.platform}.\n"
            f"Available hook IDs: {ctx.hook_ids()}\n"
            f"Trend ID: {ctx.trend_id()}\n"
            "Call get_content_context to load all necessary context, "
            "select the 2 best hooks, then call save_script exactly 2 times."
        )

    def get_tools(self, ctx: AgentContext) -> list[ToolDef]:
        hooks_repo = HooksRepository(ctx.session)
        scripts_repo = ScriptsRepository(ctx.session)
        trend_repo = TrendAnalysisRepository(ctx.session)
        report_repo = ResearchReportsRepository(ctx.session)

        async def get_content_context() -> dict:
            hook_ids = ctx.hook_ids()
            hooks_data = []
            for hid in hook_ids:
                try:
                    hook = await hooks_repo.get_by_id(UUID(hid))
                    if hook:
                        hooks_data.append({
                            "id": str(hook.id),
                            "hook_type": hook.hook_type.value,
                            "content": hook.content,
                            "quality_score": hook.quality_score,
                            "platform": hook.platform.value,
                        })
                except (ValueError, Exception):
                    continue

            # Sort by quality score, take top 5 for context
            hooks_data.sort(key=lambda h: h.get("quality_score", 0), reverse=True)

            trend_data = {}
            if ctx.trend_id():
                trend = await trend_repo.get_by_id(UUID(ctx.trend_id()))
                if trend:
                    trend_data = {
                        "keywords": trend.keywords,
                        "insights": trend.insights,
                        "velocity": trend.velocity.value,
                        "trend_score": trend.trend_score,
                    }

            fitness_data = {}
            if ctx.report_id():
                report = await report_repo.get_by_id(UUID(ctx.report_id()))
                if report:
                    fitness_data = {
                        "summary": report.summary,
                        "key_findings": report.key_findings[:5],
                        "fitness_score": ctx.fitness_score(),
                    }

            return {
                "hooks": hooks_data[:5],
                "trend": trend_data,
                "fitness": fitness_data,
                "platform": ctx.platform,
                "topic_id": str(ctx.topic_id),
            }

        async def save_script(
            hook_id: str,
            title: str,
            content: str,
            outline: list[dict],
            duration_seconds: int = None,
            word_count: int = None,
            platform: str = None,
        ) -> dict:
            plat = PlatformEnum(platform) if platform else PlatformEnum(ctx.platform)
            wc = word_count or len(content.split())

            script = await scripts_repo.create(
                user_id=ctx.user_id,
                topic_id=ctx.topic_id,
                hook_id=UUID(hook_id),
                title=title,
                platform=plat,
                duration_seconds=duration_seconds,
                content=content,
                outline=outline,
                word_count=wc,
                status=ScriptStatusEnum.draft,
            )

            # Mark the hook as used
            await hooks_repo.mark_used(UUID(hook_id))

            return {
                "id": str(script.id),
                "title": script.title,
                "word_count": wc,
                "duration_seconds": duration_seconds,
                "saved": True,
            }

        return [
            ToolDef(
                name="get_content_context",
                description=(
                    "Load all context needed for script writing: available hooks (with quality scores), "
                    "trend insights, and fitness report recommendations."
                ),
                parameters={"type": "object", "properties": {}, "required": []},
                fn=get_content_context,
            ),
            ToolDef(
                name="save_script",
                description=(
                    "Save one complete script to the database. Call exactly 2 times "
                    "using the 2 highest-quality hooks. Returns the script UUID."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "hook_id": {"type": "string", "description": "UUID of the hook to open with"},
                        "title": {"type": "string", "description": "Script title"},
                        "content": {"type": "string", "description": "Full script text with speaker directions"},
                        "outline": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "section": {"type": "string"},
                                    "duration": {"type": "integer"},
                                    "notes": {"type": "string"},
                                },
                            },
                            "description": "Script sections with timing",
                        },
                        "duration_seconds": {"type": "integer", "description": "Total duration in seconds"},
                        "word_count": {"type": "integer", "description": "Total word count"},
                        "platform": {
                            "type": "string",
                            "enum": ["youtube", "tiktok", "instagram", "twitter", "linkedin", "reddit", "other"],
                        },
                    },
                    "required": ["hook_id", "title", "content", "outline"],
                },
                fn=save_script,
            ),
        ]
