from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from models.db import Keyword, TrendKeyword
from repositories.base import BaseRepository


class KeywordsRepository(BaseRepository[Keyword]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Keyword, session)

    async def get_or_create(self, keyword: str) -> Keyword:
        """Normalise and upsert a keyword. Returns the persisted Keyword."""
        normalised = keyword.strip().lower()[:100]
        stmt = (
            pg_insert(Keyword)
            .values(keyword=normalised)
            .on_conflict_do_nothing(index_elements=["keyword"])
            .returning(Keyword)
        )
        result = await self.session.execute(stmt)
        row = result.fetchone()
        if row:
            return row[0]
        # If on_conflict_do_nothing fired, fetch the existing row
        existing = await self.session.execute(
            select(Keyword).where(Keyword.keyword == normalised)
        )
        return existing.scalar_one()

    async def save_trend_keywords(
        self,
        trend_analysis_id: UUID,
        keywords: List[str],
        weight: float = 1.0,
    ) -> None:
        """Upsert keywords and link them to a trend analysis record."""
        for kw in keywords:
            keyword_obj = await self.get_or_create(kw)
            await self.session.flush()
            # Upsert the junction row (ignore if already exists)
            stmt = (
                pg_insert(TrendKeyword)
                .values(
                    trend_analysis_id=trend_analysis_id,
                    keyword_id=keyword_obj.id,
                    weight=weight,
                )
                .on_conflict_do_nothing()
            )
            await self.session.execute(stmt)

    async def get_top_keywords(self, days: int = 7, limit: int = 30) -> List[dict]:
        """Top keywords by weighted frequency across all trend analyses in the past N days."""
        sql = text("""
            SELECT k.keyword, SUM(tk.weight) as total_weight, COUNT(*) as frequency
            FROM trend_keywords tk
            JOIN keywords k ON k.id = tk.keyword_id
            JOIN trend_analysis ta ON ta.id = tk.trend_analysis_id
            WHERE ta.analyzed_at >= now() - make_interval(days => :days)
            GROUP BY k.keyword
            ORDER BY total_weight DESC
            LIMIT :limit
        """)
        result = await self.session.execute(sql, {"days": days, "limit": limit})
        return [
            {"keyword": row.keyword, "weight": row.total_weight, "frequency": row.frequency}
            for row in result.fetchall()
        ]
