import logging
from uuid import UUID

logger = logging.getLogger(__name__)


async def generate_script_for_topic(
    ctx: dict,
    user_id: str,
    topic_id: str,
    platform: str,
    title: str,
    hook_id: str | None = None,
    duration_seconds: int | None = None,
    tone: str | None = None,
) -> dict:
    uid = UUID(user_id)
    tid = UUID(topic_id)
    hid = UUID(hook_id) if hook_id else None
    from core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        redis = ctx["redis"]
        from models.db import PlatformEnum
        from models.schemas import ScriptGenerateRequest
        from services.scripts import ScriptService
        svc = ScriptService(session, redis)
        req = ScriptGenerateRequest(
            topic_id=tid,
            platform=PlatformEnum(platform),
            title=title,
            hook_id=hid,
            duration_seconds=duration_seconds,
            tone=tone,
        )
        script = await svc.generate(uid, req)
        logger.info(
            "Background script generation complete",
            extra={"ctx_script_id": str(script.id), "ctx_user_id": user_id},
        )
        return {"status": "ok", "script_id": str(script.id)}
