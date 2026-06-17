import logging
from uuid import UUID

from arq import ArqRedis

from core.database import AsyncSessionLocal
from core.redis import get_redis
from models.db import TrendPeriodEnum
from models.schemas import TrendAnalyzeRequest
from repositories.topics import TopicsRepository
from services.trends import TrendService

logger = logging.getLogger(__name__)


async def analyze_topic_trends(ctx: dict, user_id: str, topic_id: str) -> dict:
    uid = UUID(user_id)
    tid = UUID(topic_id)
    async with AsyncSessionLocal() as session:
        redis = ctx["redis"]
        topics_repo = TopicsRepository(session)
        topic = await topics_repo.get_by_id(tid)
        if not topic or topic.user_id != uid:
            return {"status": "skipped", "reason": "topic not found"}

        svc = TrendService(session, redis)
        req = TrendAnalyzeRequest(topic_id=tid, period=TrendPeriodEnum.week)
        trend = await svc.analyze(uid, req)
        logger.info("Trend analysis complete", extra={"ctx_trend_id": str(trend.id), "ctx_topic_id": topic_id})
        return {"status": "ok", "trend_id": str(trend.id)}


async def bulk_trend_refresh(ctx: dict) -> dict:
    """Cron job: refresh rising trends for all active topics."""
    async with AsyncSessionLocal() as session:
        from repositories.users import UsersRepository
        users_repo = UsersRepository(session)
        users = await users_repo.get_active()

        count = 0
        for user in users:
            topics_repo = TopicsRepository(session)
            topics = await topics_repo.get_active_by_user(user.id)
            for topic in topics[:5]:  # cap per user to avoid runaway
                try:
                    await analyze_topic_trends(ctx, str(user.id), str(topic.id))
                    count += 1
                except Exception:
                    logger.exception("Trend refresh failed", extra={"ctx_topic_id": str(topic.id)})

    return {"status": "ok", "analyzed": count}
