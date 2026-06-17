import logging
from typing import Any

import redis.asyncio as aioredis
from arq import cron
from arq.connections import RedisSettings

from core.config import settings
from workers.tasks.agent_workflow import run_agent_workflow
from workers.tasks.daily_pipeline import run_daily_dispatch, run_daily_pipeline
from workers.tasks.daily_report import bulk_daily_reports, generate_daily_report
from workers.tasks.process_user import process_user_topics
from workers.tasks.hook_generation import generate_hooks_for_topic
from workers.tasks.research import generate_research_report
from workers.tasks.script_generation import generate_script_for_topic
from workers.tasks.trend_analysis import analyze_topic_trends, bulk_trend_refresh

logger = logging.getLogger(__name__)


async def startup(ctx: dict) -> None:
    ctx["redis"] = aioredis.from_url(settings.REDIS_URL, decode_responses=False)
    logger.info("ARQ worker started")


async def shutdown(ctx: dict) -> None:
    await ctx["redis"].aclose()
    logger.info("ARQ worker shutdown")


class WorkerSettings:
    functions = [
        run_agent_workflow,
        run_daily_dispatch,
        run_daily_pipeline,
        process_user_topics,
        analyze_topic_trends,
        bulk_trend_refresh,
        generate_daily_report,
        bulk_daily_reports,
        generate_research_report,
        generate_hooks_for_topic,
        generate_script_for_topic,
    ]
    cron_jobs = [
        # 06:00 UTC — fan-out pipeline dispatch for all users × topics
        cron(run_daily_dispatch, hour=6, minute=0),
        # 05:00 UTC — pre-generate recommendation reports
        cron(bulk_daily_reports, hour=5, minute=0),
        # 06:00 & 18:00 UTC — refresh trend data
        cron(bulk_trend_refresh, hour={6, 18}),
    ]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    max_jobs = 10
    job_timeout = 600
    keep_result = 3600
