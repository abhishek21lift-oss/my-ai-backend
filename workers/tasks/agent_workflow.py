import logging
from typing import Optional
from uuid import UUID

logger = logging.getLogger(__name__)


async def run_agent_workflow(
    ctx: dict,
    user_id: str,
    topic_id: str,
    platform: str,
    orchestrator_log_id: Optional[str] = None,
) -> dict:
    """ARQ task: run the full 5-agent content pipeline."""
    uid = UUID(user_id)
    tid = UUID(topic_id)
    oid = UUID(orchestrator_log_id) if orchestrator_log_id else None

    from core.database import AsyncSessionLocal
    from models.db import PlatformEnum
    from agents.orchestrator.schemas import PipelineRequest
    from agents.orchestrator.workflow import run_content_pipeline

    try:
        plat = PlatformEnum(platform)
    except ValueError:
        logger.error(f"Invalid platform: {platform}")
        return {"status": "error", "error": f"Invalid platform: {platform}"}

    async with AsyncSessionLocal() as session:
        redis = ctx["redis"]
        request = PipelineRequest(user_id=uid, topic_id=tid, platform=plat)
        result = await run_content_pipeline(request, session, redis, oid)

    if result.success:
        try:
            from datetime import date
            from core.cache import CacheService
            cache_key = CacheService.key("recs", str(uid), str(date.today()))
            await ctx["redis"].delete(cache_key)
        except Exception:
            logger.warning("Cache invalidation failed in agent_workflow", extra={"ctx_user_id": user_id})

    return {"status": "ok", **result.to_dict()}
