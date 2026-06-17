import logging
from uuid import UUID

from agents.base import BaseAgent, ToolDef
from agents.context import AgentContext
from agents.viral_scout.prompts import SYSTEM_PROMPT
from models.db import ContentTypeEnum, PlatformEnum
from repositories.topics import TopicsRepository
from repositories.viral_content import ViralContentRepository

logger = logging.getLogger(__name__)


class ViralScoutAgent(BaseAgent):
    AGENT_NAME = "viral_scout"
    TASK_TYPE = "discover_viral_content"

    def get_system_prompt(self, ctx: AgentContext) -> str:
        return SYSTEM_PROMPT

    def get_initial_message(self, ctx: AgentContext) -> str:
        return (
            f"Scout viral content for topic_id={ctx.topic_id} on platform={ctx.platform}.\n"
            "Start by calling get_topic_info, then get_existing_content, "
            "then discover and save 5-7 new viral content items."
        )

    def get_tools(self, ctx: AgentContext) -> list[ToolDef]:
        repo = ViralContentRepository(ctx.session)
        topics_repo = TopicsRepository(ctx.session)

        async def get_topic_info() -> dict:
            topic = await topics_repo.get_by_id(ctx.topic_id)
            if not topic:
                return {"error": "topic not found"}
            return {
                "id": str(topic.id),
                "name": topic.name,
                "category": topic.category or "general",
                "description": topic.description or "",
            }

        async def get_existing_content(limit: int = 10) -> dict:
            items = await repo.get_by_topic(ctx.topic_id, limit=limit)
            return {
                "count": len(items),
                "items": [
                    {
                        "title": i.title,
                        "platform": i.platform.value,
                        "viral_score": i.viral_score,
                        "content_type": i.content_type.value if i.content_type else None,
                    }
                    for i in items
                ],
            }

        async def save_viral_content(
            title: str,
            viral_score: float,
            platform: str = None,
            content_type: str = "video",
            content_url: str = None,
            views: int = 0,
            likes: int = 0,
            shares: int = 0,
            comments: int = 0,
            engagement_rate: float = None,
        ) -> dict:
            plat = PlatformEnum(platform) if platform else PlatformEnum(ctx.platform)
            try:
                ct = ContentTypeEnum(content_type)
            except ValueError:
                ct = ContentTypeEnum.video

            item = await repo.create(
                user_id=ctx.user_id,
                topic_id=ctx.topic_id,
                platform=plat,
                content_type=ct,
                title=title,
                content_url=content_url,
                views=views,
                likes=likes,
                shares=shares,
                comments=comments,
                engagement_rate=engagement_rate,
                viral_score=max(0.0, min(100.0, float(viral_score))),
            )
            return {"id": str(item.id), "title": item.title, "saved": True}

        return [
            ToolDef(
                name="get_topic_info",
                description="Retrieve topic name, category, and description to inform discovery.",
                parameters={"type": "object", "properties": {}, "required": []},
                fn=get_topic_info,
            ),
            ToolDef(
                name="get_existing_content",
                description="Check what viral content items are already cataloged for this topic.",
                parameters={
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "description": "Max items to return", "default": 10},
                    },
                    "required": [],
                },
                fn=get_existing_content,
            ),
            ToolDef(
                name="save_viral_content",
                description=(
                    "Save one discovered viral content item to the database. "
                    "Call once per item. Returns the saved item's UUID."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Content title or headline"},
                        "viral_score": {"type": "number", "description": "Viral score 0-100"},
                        "platform": {
                            "type": "string",
                            "enum": ["youtube", "tiktok", "instagram", "twitter", "linkedin", "reddit", "other"],
                            "description": "Platform (defaults to task platform if omitted)",
                        },
                        "content_type": {
                            "type": "string",
                            "enum": ["video", "post", "article", "thread", "reel", "short"],
                        },
                        "content_url": {"type": "string", "description": "URL to the content"},
                        "views": {"type": "integer", "minimum": 0},
                        "likes": {"type": "integer", "minimum": 0},
                        "shares": {"type": "integer", "minimum": 0},
                        "comments": {"type": "integer", "minimum": 0},
                        "engagement_rate": {"type": "number", "description": "Engagement rate 0-100"},
                    },
                    "required": ["title", "viral_score"],
                },
                fn=save_viral_content,
            ),
        ]
