"""
HTTP endpoints that can be triggered by external schedulers
(Vercel Cron, GitHub Actions, uptime monitors, etc.).

All endpoints require the CRON_SECRET header to prevent unauthorized calls.
Set CRON_SECRET in your environment to any strong random string.
"""
import logging
from fastapi import APIRouter, Header, HTTPException, status

from core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/cron", tags=["cron"])


def _verify_secret(authorization: str | None) -> None:
    settings = get_settings()
    if not settings.CRON_SECRET:
        raise HTTPException(status_code=503, detail="Cron secret not configured")
    expected = f"Bearer {settings.CRON_SECRET}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.post(
    "/daily-pipeline",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger the daily full-pipeline run for all users",
)
async def trigger_daily_pipeline(
    authorization: str | None = Header(None),
) -> dict:
    """
    Enqueues run_daily_pipeline as an ARQ background job.
    Safe to call repeatedly — ARQ deduplicates by job ID.
    """
    _verify_secret(authorization)

    from arq import create_pool
    from arq.connections import RedisSettings
    from core.config import get_settings

    settings = get_settings()
    arq_pool = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
    job = await arq_pool.enqueue_job("run_daily_pipeline")
    await arq_pool.aclose()

    logger.info("Cron: daily-pipeline enqueued", extra={"ctx_job_id": job.job_id if job else "none"})
    return {"status": "queued", "job_id": job.job_id if job else None}


@router.post(
    "/daily-reports",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Pre-generate daily recommendations for all active users",
)
async def trigger_daily_reports(
    authorization: str | None = Header(None),
) -> dict:
    _verify_secret(authorization)

    from arq import create_pool
    from arq.connections import RedisSettings
    from core.config import get_settings

    settings = get_settings()
    arq_pool = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
    job = await arq_pool.enqueue_job("bulk_daily_reports")
    await arq_pool.aclose()

    logger.info("Cron: daily-reports enqueued", extra={"ctx_job_id": job.job_id if job else "none"})
    return {"status": "queued", "job_id": job.job_id if job else None}


@router.post(
    "/trend-refresh",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger trend data refresh for all topics",
)
async def trigger_trend_refresh(
    authorization: str | None = Header(None),
) -> dict:
    _verify_secret(authorization)

    from arq import create_pool
    from arq.connections import RedisSettings
    from core.config import get_settings

    settings = get_settings()
    arq_pool = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
    job = await arq_pool.enqueue_job("bulk_trend_refresh")
    await arq_pool.aclose()

    return {"status": "queued", "job_id": job.job_id if job else None}
