import logging
from uuid import UUID

logger = logging.getLogger(__name__)


async def generate_research_report(
    ctx: dict, user_id: str, topic_id: str, title: str, focus_areas: list[str] | None = None
) -> dict:
    uid = UUID(user_id)
    tid = UUID(topic_id)
    from core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        redis = ctx["redis"]
        from models.schemas import ResearchGenerateRequest
        from services.research import ResearchService
        svc = ResearchService(session, redis)
        req = ResearchGenerateRequest(topic_id=tid, title=title, focus_areas=focus_areas or [])
        report = await svc.generate(uid, req)
        logger.info(
            "Background research report complete",
            extra={"ctx_report_id": str(report.id), "ctx_user_id": user_id},
        )
        return {"status": "ok", "report_id": str(report.id)}
