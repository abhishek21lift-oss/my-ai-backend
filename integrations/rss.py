import logging
from typing import List

import feedparser
import httpx

from integrations.base import DataSourceClient, RawContent

logger = logging.getLogger(__name__)


class RSSClient(DataSourceClient):
    def __init__(self, timeout: int = 15) -> None:
        self._timeout = timeout

    async def search(self, query: str, max_results: int = 10) -> List[RawContent]:
        """Google News RSS as a general-purpose news search."""
        url = (
            f"https://news.google.com/rss/search"
            f"?q={query}&hl=en-US&gl=US&ceid=US:en"
        )
        return await self.fetch_feed(url, max_results)

    async def fetch_feed(self, url: str, max_results: int = 15) -> List[RawContent]:
        try:
            async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
                r = await client.get(url)
                r.raise_for_status()
                raw = r.text
        except httpx.HTTPError as exc:
            logger.warning("RSS fetch error %s: %s", url, exc)
            return []
        except Exception as exc:
            logger.warning("RSS unexpected error: %s", exc)
            return []

        feed = feedparser.parse(raw)
        results: List[RawContent] = []
        for entry in feed.entries[:max_results]:
            results.append(RawContent(
                source="rss",
                title=(entry.get("title") or "")[:500],
                url=entry.get("link", ""),
                platform="other",
                content_type="article",
                views=0,
                likes=0,
                shares=0,
                comments=0,
                engagement_rate=None,
                published_at=entry.get("published"),
                extra={"summary": (entry.get("summary") or "")[:300], "feed_url": url},
            ))
        return results
