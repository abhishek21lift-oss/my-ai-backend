import logging
from typing import List

import httpx

from core.config import get_settings
from integrations.base import DataSourceClient, RawContent

logger = logging.getLogger(__name__)
_BASE = "https://www.googleapis.com/youtube/v3"


class YouTubeClient(DataSourceClient):
    def __init__(self) -> None:
        s = get_settings()
        self._api_key = s.YOUTUBE_API_KEY
        self._timeout = s.HTTP_TIMEOUT

    @property
    def available(self) -> bool:
        return bool(self._api_key)

    async def search(self, query: str, max_results: int = 10) -> List[RawContent]:
        if not self.available:
            logger.debug("YouTube API key not configured, skipping")
            return []
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                r = await client.get(
                    f"{_BASE}/search",
                    params={
                        "part": "snippet",
                        "q": query,
                        "type": "video",
                        "order": "viewCount",
                        "maxResults": min(max_results, 50),
                        "key": self._api_key,
                    },
                )
                r.raise_for_status()
                items = r.json().get("items", [])
                if not items:
                    return []

                video_ids = [
                    i["id"]["videoId"]
                    for i in items
                    if i.get("id", {}).get("videoId")
                ]
                if not video_ids:
                    return []

                r2 = await client.get(
                    f"{_BASE}/videos",
                    params={
                        "part": "statistics,snippet",
                        "id": ",".join(video_ids),
                        "key": self._api_key,
                    },
                )
                r2.raise_for_status()
                stats_items = r2.json().get("items", [])
        except httpx.HTTPError as exc:
            logger.warning("YouTube API error: %s", exc)
            return []
        except Exception as exc:
            logger.warning("YouTube unexpected error: %s", exc)
            return []

        results: List[RawContent] = []
        for video in stats_items:
            stats = video.get("statistics", {})
            snippet = video.get("snippet", {})
            views = int(stats.get("viewCount", 0))
            likes = int(stats.get("likeCount", 0))
            comments = int(stats.get("commentCount", 0))
            eng = round((likes + comments) / views * 100, 2) if views > 0 else None
            results.append(RawContent(
                source="youtube",
                title=(snippet.get("title") or "")[:500],
                url=f"https://www.youtube.com/watch?v={video['id']}",
                platform="youtube",
                content_type="video",
                views=views,
                likes=likes,
                shares=0,
                comments=comments,
                engagement_rate=eng,
                published_at=snippet.get("publishedAt"),
                extra={"channel": snippet.get("channelTitle", "")},
            ))
        return results
