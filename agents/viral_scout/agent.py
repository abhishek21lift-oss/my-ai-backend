import hashlib
import logging
from uuid import UUID

from agents.base import BaseAgent, ToolDef
from agents.context import AgentContext
from agents.viral_scout.prompts import SYSTEM_PROMPT
from integrations.reddit import RedditClient
from integrations.rss import RSSClient
from integrations.youtube import YouTubeClient
from models.db import ContentTypeEnum, PlatformEnum
from repositories.topics import TopicsRepository
from repositories.viral_content import ViralContentRepository

logger = logging.getLogger(__name__)

_youtube = YouTubeClient()
_reddit = RedditClient()
_rss = RSSClient()


def _content_hash(platform: str, url: str, title: str) -> str:
    if url:
        raw = f"{platform}:{url.lower()}"
    else:
        raw = f"{platform}:{title.lower()}"
    return hashlib.sha256(raw.encode()).hexdigest()


class ViralScoutAgent(BaseAgent):
    AGENT_NAME = "viral_scout"
    TASK_TYPE = "discover_viral_content"

    def get_system_prompt(self, ctx: AgentContext) -> str:
        return SYSTEM_PROMPT

    def get_initial_message(self, ctx: AgentContext) -> str:
        return (
            f"Scout viral content for topic_id={ctx.topic_id} on platform={ctx.platform}.\n"
            "Start by calling get_topic_info, then get_existing_content. "
            "Then use search_youtube or search_reddit to find real trending content. "
            "Save 5-7 items with save_viral_content."
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
                        "content_url": i.content_url,
                    }
                    for i in items
                ],
            }

        async def search_youtube(query: str, max_results: int = 8) -> dict:
            results = await _youtube.search(query, max_results=max_results)
            return {
                "source": "youtube",
                "available": _youtube.available,
                "count": len(results),
                "items": [
                    {
                        "title": r.title,
                        "url": r.url,
                        "platform": r.platform,
                        "content_type": r.content_type,
                        "views": r.views,
                        "likes": r.likes,
                        "comments": r.comments,
                        "engagement_rate": r.engagement_rate,
                        "published_at": r.published_at,
                    }
                    for r in results
                ],
            }

        async def search_reddit(query: str, max_results: int = 15) -> dict:
            results = await _reddit.search(query, max_results=max_results)
            return {
                "source": "reddit",
                "count": len(results),
                "items": [
                    {
                        "title": r.title,
                        "url": r.url,
                        "platform": r.platform,
                        "content_type": r.content_type,
                        "views": r.views,
                        "likes": r.likes,
                        "comments": r.comments,
                        "engagement_rate": r.engagement_rate,
                    }
                    for r in results
                ],
            }

        async def search_rss(query: str, max_results: int = 10) -> dict:
            results = await _rss.search(query, max_results=max_results)
            return {
                "source": "rss",
                "count": len(results),
                "items": [
                    {
                        "title": r.title,
                        "url": r.url,
                        "platform": r.platform,
                        "content_type": r.content_type,
                        "published_at": r.published_at,
                        "summary": r.extra.get("summary", ""),
                    }
                    for r in results
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

            c_hash = _content_hash(plat.value, content_url or "", title)

            # Dedup: return existing item if same hash for this user
            from sqlalchemy import select
            existing = await ctx.session.execute(
                select(type(None).__mro__[0])  # placeholder, use repo below
            )
            # Use repo's filter
            from models.db import ViralContent as _VC
            from sqlalchemy import select as _select
            dup = await ctx.session.execute(
                _select(_VC).where(
                    _VC.user_id == ctx.user_id,
                    _VC.content_hash == c_hash,
                )
            )
            dup_item = dup.scalar_one_or_none()
            if dup_item:
                return {
                    "id": str(dup_item.id),
                    "title": dup_item.title,
                    "saved": False,
                    "duplicate": True,
                }

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
                content_hash=c_hash,
            )
            return {"id": str(item.id), "title": item.title, "saved": True}

        return [
            ToolDef(
                name="get_topic_info",
                description="Retrieve topic name, category, and description.",
                parameters={"type": "object", "properties": {}, "required": []},
                fn=get_topic_info,
            ),
            ToolDef(
                name="get_existing_content",
                description="Check what viral content is already cataloged for this topic (avoid duplicates).",
                parameters={
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "default": 10},
                    },
                    "required": [],
                },
                fn=get_existing_content,
            ),
            ToolDef(
                name="search_youtube",
                description=(
                    "Search YouTube for trending videos related to a query. "
                    "Returns real view/like/comment counts. "
                    "Returns empty list if YOUTUBE_API_KEY not configured."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "max_results": {"type": "integer", "default": 8, "minimum": 1, "maximum": 20},
                    },
                    "required": ["query"],
                },
                fn=search_youtube,
            ),
            ToolDef(
                name="search_reddit",
                description=(
                    "Search Reddit for hot posts related to a query. "
                    "Returns real upvote/comment counts. No API key required."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "max_results": {"type": "integer", "default": 15, "minimum": 1, "maximum": 50},
                    },
                    "required": ["query"],
                },
                fn=search_reddit,
            ),
            ToolDef(
                name="search_rss",
                description=(
                    "Search Google News RSS for recent articles related to a query. "
                    "Useful for news topics, trends, and current events."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "max_results": {"type": "integer", "default": 10, "minimum": 1, "maximum": 20},
                    },
                    "required": ["query"],
                },
                fn=search_rss,
            ),
            ToolDef(
                name="save_viral_content",
                description=(
                    "Save one discovered viral content item. "
                    "Call once per item. Returns the saved item's UUID. "
                    "Automatically deduplicates by content URL."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "viral_score": {"type": "number", "description": "Estimated viral score 0-100"},
                        "platform": {
                            "type": "string",
                            "enum": ["youtube", "tiktok", "instagram", "twitter", "linkedin", "reddit", "other"],
                        },
                        "content_type": {
                            "type": "string",
                            "enum": ["video", "post", "article", "thread", "reel", "short"],
                        },
                        "content_url": {"type": "string"},
                        "views": {"type": "integer", "minimum": 0},
                        "likes": {"type": "integer", "minimum": 0},
                        "shares": {"type": "integer", "minimum": 0},
                        "comments": {"type": "integer", "minimum": 0},
                        "engagement_rate": {"type": "number"},
                    },
                    "required": ["title", "viral_score"],
                },
                fn=save_viral_content,
            ),
        ]
