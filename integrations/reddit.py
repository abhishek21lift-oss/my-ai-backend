import logging
from typing import List

import httpx

from core.config import get_settings
from integrations.base import DataSourceClient, RawContent

logger = logging.getLogger(__name__)


class RedditClient(DataSourceClient):
    """Reddit public JSON API — no OAuth required for public subreddits."""

    def __init__(self) -> None:
        s = get_settings()
        self._user_agent = s.REDDIT_USER_AGENT
        self._timeout = s.HTTP_TIMEOUT

    async def search(self, query: str, max_results: int = 25) -> List[RawContent]:
        headers = {"User-Agent": self._user_agent}
        try:
            async with httpx.AsyncClient(timeout=self._timeout, headers=headers) as client:
                r = await client.get(
                    "https://www.reddit.com/search.json",
                    params={"q": query, "sort": "hot", "limit": min(max_results, 100), "type": "link"},
                )
                r.raise_for_status()
                data = r.json()
        except httpx.HTTPError as exc:
            logger.warning("Reddit search error: %s", exc)
            return []
        except Exception as exc:
            logger.warning("Reddit unexpected error: %s", exc)
            return []

        return self._parse_listing(data)

    async def get_hot(self, subreddit: str, limit: int = 25) -> List[RawContent]:
        headers = {"User-Agent": self._user_agent}
        try:
            async with httpx.AsyncClient(timeout=self._timeout, headers=headers) as client:
                r = await client.get(
                    f"https://www.reddit.com/r/{subreddit}/hot.json",
                    params={"limit": min(limit, 100)},
                )
                r.raise_for_status()
                data = r.json()
        except httpx.HTTPError as exc:
            logger.warning("Reddit r/%s/hot error: %s", subreddit, exc)
            return []
        except Exception as exc:
            logger.warning("Reddit unexpected error: %s", exc)
            return []

        return self._parse_listing(data)

    def _parse_listing(self, data: dict) -> List[RawContent]:
        results: List[RawContent] = []
        for child in data.get("data", {}).get("children", []):
            post = child.get("data", {})
            if post.get("stickied"):
                continue
            score = int(post.get("score", 0))
            num_comments = int(post.get("num_comments", 0))
            views = score * 10
            eng = round((num_comments / max(views, 1)) * 100, 2)
            results.append(RawContent(
                source="reddit",
                title=(post.get("title") or "")[:500],
                url=f"https://reddit.com{post.get('permalink', '')}",
                platform="reddit",
                content_type="post",
                views=views,
                likes=score,
                shares=0,
                comments=num_comments,
                engagement_rate=eng,
                extra={
                    "upvote_ratio": post.get("upvote_ratio", 0.5),
                    "subreddit": post.get("subreddit", ""),
                },
            ))
        return results
