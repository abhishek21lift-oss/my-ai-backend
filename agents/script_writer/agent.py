import logging
from uuid import UUID

from agents.base import BaseAgent, ToolDef
from agents.context import AgentContext
from agents.script_writer.prompts import SYSTEM_PROMPT
from models.db import PlatformEnum, ScriptFormatEnum, ScriptStatusEnum
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
            f"Write 5 scripts for topic_id={ctx.topic_id} on platform={ctx.platform}.\n"
            f"Available hook IDs: {ctx.hook_ids()}\n"
            f"Trend ID: {ctx.trend_id()}\n"
            f"Fitness report ID: {ctx.report_id()}\n"
            "Start by calling get_top_rated_scripts for style examples, "
            "then get_content_context to load hooks, trends, and fitness data. "
            "Then call save_script exactly 5 times: "
            "Scripts 1-2: short_form, Scripts 3-4: long_form, Script 5: experimental."
        )

    def get_tools(self, ctx: AgentContext) -> list[ToolDef]:
        hooks_repo = HooksRepository(ctx.session)
        scripts_repo = ScriptsRepository(ctx.session)
        trend_repo = TrendAnalysisRepository(ctx.session)
        report_repo = ResearchReportsRepository(ctx.session)

        async def get_top_rated_scripts(limit: int = 2) -> dict:
            """Retrieve highest user-rated scripts for the same topic/platform as style examples."""
            plat = PlatformEnum(ctx.platform)
            scripts = await scripts_repo.get_top_rated(
                ctx.user_id, platform=plat, topic_id=ctx.topic_id, limit=limit
            )
            if not scripts:
                scripts = await scripts_repo.get_top_rated(ctx.user_id, limit=limit)

            return {
                "count": len(scripts),
                "examples": [
                    {
                        "title": s.title,
                        "script_format": s.script_format.value if s.script_format else "short_form",
                        "content": s.content[:800] if s.content else "",
                        "outline": s.outline,
                        "word_count": s.word_count,
                        "duration_seconds": s.duration_seconds,
                        "user_rating": s.user_rating,
                        "platform": s.platform.value,
                    }
                    for s in scripts
                ],
                "note": "Use these as style references — apply their structure and pacing, never copy verbatim.",
            }

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
            script_format: str = "short_form",
            duration_seconds: int = None,
            word_count: int = None,
            platform: str = None,
        ) -> dict:
            plat = PlatformEnum(platform) if platform else PlatformEnum(ctx.platform)
            wc = word_count or len(content.split())

            try:
                fmt = ScriptFormatEnum(script_format)
            except ValueError:
                fmt = ScriptFormatEnum.short_form

            script = await scripts_repo.create(
                user_id=ctx.user_id,
                topic_id=ctx.topic_id,
                hook_id=UUID(hook_id),
                title=title,
                platform=plat,
                script_format=fmt,
                duration_seconds=duration_seconds,
                content=content,
                outline=outline,
                word_count=wc,
                status=ScriptStatusEnum.draft,
            )

            await hooks_repo.mark_used(UUID(hook_id))

            return {
                "id": str(script.id),
                "title": script.title,
                "script_format": fmt.value,
                "word_count": wc,
                "duration_seconds": duration_seconds,
                "saved": True,
            }

        return [
            ToolDef(
                name="get_top_rated_scripts",
                description=(
                    "Retrieve the highest user-rated scripts for this topic/platform as style examples. "
                    "Study their outline structure, pacing, and CTA approach. Never copy verbatim."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "default": 2, "minimum": 1, "maximum": 5},
                    },
                    "required": [],
                },
                fn=get_top_rated_scripts,
            ),
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
                    "Save one complete script to the database. Call exactly 5 times "
                    "(2 short_form, 2 long_form, 1 experimental). Returns the script UUID."
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
                        "script_format": {
                            "type": "string",
                            "enum": ["short_form", "long_form", "carousel", "thread", "experimental"],
                            "description": "Script 1-2: short_form, Script 3-4: long_form, Script 5: experimental",
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
