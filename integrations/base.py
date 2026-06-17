from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class RawContent:
    """Normalised content item from any real-data source."""
    source: str           # "youtube" | "reddit" | "rss"
    title: str
    url: str
    platform: str         # maps to PlatformEnum value
    content_type: str     # maps to ContentTypeEnum value
    views: int = 0
    likes: int = 0
    shares: int = 0
    comments: int = 0
    engagement_rate: Optional[float] = None
    published_at: Optional[str] = None   # ISO 8601 string
    extra: dict = field(default_factory=dict)


class DataSourceClient(ABC):
    @abstractmethod
    async def search(self, query: str, max_results: int = 10) -> List[RawContent]: ...
