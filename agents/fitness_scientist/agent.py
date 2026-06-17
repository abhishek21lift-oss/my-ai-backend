import logging
from uuid import UUID

import httpx

from agents.base import BaseAgent, ToolDef
from agents.context import AgentContext
from agents.fitness_scientist.prompts import SYSTEM_PROMPT
from models.db import ReportStatusEnum
from repositories.research_reports import ResearchReportsRepository
from repositories.trend_analysis import TrendAnalysisRepository
from repositories.viral_content import ViralContentRepository

logger = logging.getLogger(__name__)

_HTTP_TIMEOUT = 10


def _extract_text(html: str, max_chars: int = 2000) -> str:
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        return text[:max_chars]
    except Exception:
        return html[:max_chars]


class FitnessScientistAgent(BaseAgent):
    AGENT_NAME = "fitness_scientist"
    TASK_TYPE = "analyze_content_fitness"

    def get_system_prompt(self, ctx: AgentContext) -> str:
        return SYSTEM_PROMPT

    def get_initial_message(self, ctx: AgentContext) -> str:
        return (
            f"Analyze content fitness for topic_id={ctx.topic_id} on platform={ctx.platform}.\n"
            f"Trend analysis ID: {ctx.trend_id()}\n"
            "Call get_trend_analysis and get_viral_metrics to gather data. "
            "Optionally fetch a top content URL with fetch_page_context for real context. "
            "Then synthesize a fitness report with save_fitness_report."
        )

    def get_tools(self, ctx: AgentContext) -> list[ToolDef]:
        trend_repo = TrendAnalysisRepository(ctx.session)
        viral_repo = ViralContentRepository(ctx.session)
        report_repo = ResearchReportsRepository(ctx.session)

        async def get_trend_analysis(trend_id: str = None) -> dict:
            tid = trend_id or ctx.trend_id()
            if not tid:
                return {"error": "no trend_id available"}
            trend = await trend_repo.get_by_id(UUID(tid))
            if not trend:
                return {"error": f"Trend {tid} not found"}
            return {
                "id": str(trend.id),
                "trend_score": trend.trend_score,
                "velocity": trend.velocity.value,
                "keywords": trend.keywords,
                "insights": trend.insights,
                "platforms": trend.platforms,
                "period": trend.period.value,
            }

        async def get_viral_metrics() -> dict:
            items = await viral_repo.get_by_topic(ctx.topic_id, limit=20)
            if not items:
                return {"count": 0, "avg_viral_score": 0, "avg_engagement_rate": 0, "sample_urls": []}
            scores = [i.viral_score for i in items]
            rates = [i.engagement_rate for i in items if i.engagement_rate is not None]
            content_types: dict = {}
            for i in items:
                ct = i.content_type.value if i.content_type else "unknown"
                content_types[ct] = content_types.get(ct, 0) + 1
            sample_urls = [i.content_url for i in items if i.content_url][:3]
            return {
                "count": len(items),
                "avg_viral_score": round(sum(scores) / len(scores), 1),
                "avg_engagement_rate": round(sum(rates) / len(rates), 1) if rates else 0,
                "max_viral_score": max(scores),
                "content_type_distribution": content_types,
                "platform": ctx.platform,
                "sample_urls": sample_urls,
            }

        async def fetch_page_context(url: str) -> dict:
            """Fetch and extract clean text from a real content URL."""
            if not url or not url.startswith("http"):
                return {"error": "Invalid URL"}
            try:
                async with httpx.AsyncClient(
                    timeout=_HTTP_TIMEOUT,
                    follow_redirects=True,
                    headers={"User-Agent": "Mozilla/5.0 ViralAI/2.0"},
                ) as client:
                    r = await client.get(url)
                    r.raise_for_status()
                    content_type = r.headers.get("content-type", "")
                    if "html" not in content_type:
                        return {"error": "Not an HTML page", "content_type": content_type}
                    text = _extract_text(r.text)
                    return {"url": url, "text": text, "chars": len(text)}
            except httpx.HTTPError as exc:
                return {"error": f"HTTP error: {exc}"}
            except Exception as exc:
                return {"error": f"Fetch failed: {exc}"}

        async def save_fitness_report(
            title: str,
            summary: str,
            content: str,
            key_findings: list[str],
            fitness_score: float,
            optimal_format: str,
            optimal_tone: str,
            hook_styles: list[str],
            optimal_duration_seconds: int = None,
        ) -> dict:
            fitness_meta = {
                "fitness_score": fitness_score,
                "optimal_format": optimal_format,
                "optimal_tone": optimal_tone,
                "hook_styles": hook_styles,
                "optimal_duration_seconds": optimal_duration_seconds,
                "platform": ctx.platform,
            }
            full_key_findings = [
                f"Fitness Score: {fitness_score}/100",
                f"Optimal Format: {optimal_format}",
                f"Optimal Tone: {optimal_tone}",
                f"Best Hook Styles: {', '.join(hook_styles)}",
            ] + key_findings

            report = await report_repo.create(
                user_id=ctx.user_id,
                topic_id=ctx.topic_id,
                title=title or f"Content Fitness Report — {ctx.platform}",
                summary=summary,
                content=content,
                key_findings=full_key_findings[:10],
                sources=[{"title": "Trend Analysis", "url": "internal", "type": "data"}],
                tags=["fitness_analysis", "agent_generated", ctx.platform],
                word_count=len(content.split()),
                status=ReportStatusEnum.completed,
            )
            return {
                "id": str(report.id),
                "fitness_score": fitness_score,
                "optimal_format": optimal_format,
                "saved": True,
            }

        return [
            ToolDef(
                name="get_trend_analysis",
                description="Retrieve the trend analysis data for this topic.",
                parameters={
                    "type": "object",
                    "properties": {
                        "trend_id": {"type": "string"},
                    },
                    "required": [],
                },
                fn=get_trend_analysis,
            ),
            ToolDef(
                name="get_viral_metrics",
                description="Get aggregated engagement metrics and sample content URLs for this topic.",
                parameters={"type": "object", "properties": {}, "required": []},
                fn=get_viral_metrics,
            ),
            ToolDef(
                name="fetch_page_context",
                description=(
                    "Fetch and extract clean readable text from a real web URL. "
                    "Use this to read the actual content of a high-performing page."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "Full URL starting with http(s)://"},
                    },
                    "required": ["url"],
                },
                fn=fetch_page_context,
            ),
            ToolDef(
                name="save_fitness_report",
                description="Save the content fitness analysis report. Call exactly once.",
                parameters={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "summary": {"type": "string", "description": "2-3 sentence executive summary"},
                        "content": {"type": "string", "description": "Full fitness analysis (300-600 words)"},
                        "key_findings": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "4-6 specific actionable findings",
                        },
                        "fitness_score": {"type": "number"},
                        "optimal_format": {"type": "string"},
                        "optimal_tone": {"type": "string"},
                        "hook_styles": {"type": "array", "items": {"type": "string"}},
                        "optimal_duration_seconds": {"type": "integer"},
                    },
                    "required": [
                        "title", "summary", "content", "key_findings",
                        "fitness_score", "optimal_format", "optimal_tone", "hook_styles",
                    ],
                },
                fn=save_fitness_report,
            ),
        ]
