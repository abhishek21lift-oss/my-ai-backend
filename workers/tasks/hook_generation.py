import logging
from uuid import UUID

logger = logging.getLogger(__name__)


async def generate_hooks_for_topic(
    ctx: dict, user_id: str, topic_id: str, platform: str, count: int = 5
) -> dict:
    uid = UUID(user_id)
    tid = UUID(topic_id)
    from core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        redis = ctx["redis"]
        from models.db import PlatformEnum
        from models.schemas import HookGenerateRequest
        from services.hooks import HookService
        svc = HookService(session, redis)
        req = HookGenerateRequest(topic_id=tid, platform=PlatformEnum(platform), count=count)
        hooks = await svc.generate(uid, req)
        logger.info(
            "Background hook generation complete",
            extra={"ctx_count": len(hooks), "ctx_topic_id": topic_id},
        )
        return {"status": "ok", "hooks_created": len(hooks)}
