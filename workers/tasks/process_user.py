"""
Fan-out worker task: process all active topics for a single user.

Spawned by run_daily_dispatch — one job per active user.
"""
import logging

logger = logging.getLogger(__name__)

_DEFAULT_PLATFORM = "youtube"


async def process_user_topics(ctx: dict, user_id: str) -> dict:
    """
    Retrieve active topics for this user and enqueue one run_agent_workflow
    job per topic. Returns immediately — pipeline jobs run independently.
    """
    from uuid import UUID as _UUID

    from core.database import AsyncSessionLocal
    from repositories.topics import TopicsRepository

    async with AsyncSessionLocal() as session:
        topics = await TopicsRepository(session).get_active_by_user(_UUID(user_id))

    if not topics:
        logger.info(
            "process_user_topics: no active topics",
            extra={"ctx_user_id": user_id},
        )
        return {"status": "ok", "queued": 0}

    arq_pool = await _get_arq_pool()
    queued = 0
    for topic in topics:
        job = await arq_pool.enqueue_job(
            "run_agent_workflow",
            user_id=user_id,
            topic_id=str(topic.id),
            platform=_DEFAULT_PLATFORM,
        )
        queued += 1
        logger.info(
            "process_user_topics: enqueued workflow",
            extra={
                "ctx_user_id": user_id,
                "ctx_topic_id": str(topic.id),
                "ctx_job_id": job.job_id if job else "none",
            },
        )
    await arq_pool.aclose()
    return {"status": "ok", "queued": queued}


async def _get_arq_pool():
    from arq import create_pool
    from arq.connections import RedisSettings
    from core.config import settings

    return await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
