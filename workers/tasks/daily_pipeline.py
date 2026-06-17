"""
Daily automation pipeline tasks.

run_daily_dispatch  — cron entry point; enqueues one process_user_topics job per active user
run_daily_pipeline  — legacy single-job version (kept for backward compat with old cron calls)
"""
import logging
from uuid import UUID

logger = logging.getLogger(__name__)

_DEFAULT_PLATFORM = "youtube"


async def run_daily_dispatch(ctx: dict) -> dict:
    """
    Cron entry point: fan out one process_user_topics job per active user.
    Each user's topics are processed independently with their own timeout budget.
    """
    from core.database import AsyncSessionLocal
    from repositories.users import UsersRepository

    async with AsyncSessionLocal() as session:
        users = await UsersRepository(session).get_active()

    if not users:
        logger.info("Daily dispatch: no active users found")
        return {"status": "ok", "users_queued": 0}

    arq_pool = await _get_arq_pool()
    queued = 0
    skipped = 0

    for user in users:
        try:
            job = await arq_pool.enqueue_job("process_user_topics", user_id=str(user.id))
            queued += 1
            logger.info(
                "Daily dispatch: enqueued user",
                extra={
                    "ctx_user_id": str(user.id),
                    "ctx_job_id": job.job_id if job else "none",
                },
            )
        except Exception:
            skipped += 1
            logger.exception("Daily dispatch: failed to enqueue user", extra={"ctx_user_id": str(user.id)})

    await arq_pool.aclose()

    result = {"status": "ok", "users_queued": queued, "users_skipped": skipped}
    logger.info("Daily dispatch cron complete", extra={**result})
    return result


async def run_daily_pipeline(ctx: dict) -> dict:
    """
    Legacy single-process pipeline: iterates all active users × topics in one job.
    Use run_daily_dispatch for production fan-out instead.
    """
    from core.database import AsyncSessionLocal
    from repositories.users import UsersRepository
    from repositories.topics import TopicsRepository

    async with AsyncSessionLocal() as session:
        users = await UsersRepository(session).get_active()

    if not users:
        logger.info("Daily pipeline: no active users found")
        return {"status": "ok", "pipelines_queued": 0}

    queued = 0
    skipped = 0

    for user in users:
        try:
            async with AsyncSessionLocal() as session:
                topics = await TopicsRepository(session).get_active_by_user(user.id)

            if not topics:
                continue

            arq_pool = await _get_arq_pool()
            for topic in topics:
                job = await arq_pool.enqueue_job(
                    "run_agent_workflow",
                    user_id=str(user.id),
                    topic_id=str(topic.id),
                    platform=_DEFAULT_PLATFORM,
                )
                queued += 1
                logger.info(
                    "Daily pipeline: enqueued",
                    extra={
                        "ctx_user_id": str(user.id),
                        "ctx_topic_id": str(topic.id),
                        "ctx_job_id": job.job_id if job else "none",
                    },
                )
            await arq_pool.aclose()

        except Exception:
            skipped += 1
            logger.exception("Daily pipeline: failed for user", extra={"ctx_user_id": str(user.id)})

    recs_ok = 0
    for user in users:
        try:
            await _generate_user_recommendations(ctx, user.id)
            recs_ok += 1
        except Exception:
            logger.exception("Daily recs: failed for user", extra={"ctx_user_id": str(user.id)})

    result = {
        "status": "ok",
        "pipelines_queued": queued,
        "users_skipped": skipped,
        "recommendations_generated": recs_ok,
    }
    logger.info("Daily pipeline cron complete", extra={**result})
    return result


async def _generate_user_recommendations(ctx: dict, user_id: UUID) -> None:
    from core.database import AsyncSessionLocal
    from services.recommendations import RecommendationsService

    async with AsyncSessionLocal() as session:
        redis = ctx["redis"]
        svc = RecommendationsService(session, redis)
        await svc.get_daily(user_id)


async def _get_arq_pool():
    from arq import create_pool
    from arq.connections import RedisSettings
    from core.config import settings

    return await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
