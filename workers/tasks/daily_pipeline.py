"""
Daily automation pipeline — runs every morning at 06:00 UTC.

Sequence for each active user × topic:
  1. Viral Scout     — discover 5-7 viral items
  2. Trend Detector  — analyse patterns
  3. Fitness Scientist — validate content science
  4. Hook Generator  — produce 5 hooks
  5. Script Writer   — write 2 scripts
  6. Daily Report    — pre-generate recommendations
"""
import logging
from uuid import UUID

logger = logging.getLogger(__name__)

# Default platform used for automated daily runs.
# Can be overridden per-user or per-topic in future.
_DEFAULT_PLATFORM = "youtube"


async def run_daily_pipeline(ctx: dict) -> dict:
    """
    Cron entry point: discover topics for every active user and run the
    full content pipeline, then pre-generate daily recommendations.
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
                logger.info(
                    "Daily pipeline: no active topics",
                    extra={"ctx_user_id": str(user.id)},
                )
                continue

            # Enqueue one pipeline job per active topic (non-blocking)
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
            logger.exception(
                "Daily pipeline: failed for user",
                extra={"ctx_user_id": str(user.id)},
            )

    # Pre-generate daily recommendations for all users in-process
    recs_ok = 0
    for user in users:
        try:
            await _generate_user_recommendations(ctx, user.id)
            recs_ok += 1
        except Exception:
            logger.exception(
                "Daily recs: failed for user",
                extra={"ctx_user_id": str(user.id)},
            )

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
