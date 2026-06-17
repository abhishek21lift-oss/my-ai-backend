import logging
from datetime import date
from uuid import UUID

logger = logging.getLogger(__name__)


async def generate_daily_report(ctx: dict, user_id: str) -> dict:
    uid = UUID(user_id)
    from core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        redis = ctx["redis"]
        from services.recommendations import RecommendationsService
        svc = RecommendationsService(session, redis)
        response = await svc.get_daily(uid)
        logger.info(
            "Daily report generated",
            extra={"ctx_user_id": user_id, "ctx_items": len(response.items)},
        )
        return {"status": "ok", "items": len(response.items)}


async def bulk_daily_reports(ctx: dict) -> dict:
    """Cron job: pre-generate daily recommendations for all active users."""
    from core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        from repositories.users import UsersRepository
        users_repo = UsersRepository(session)
        users = await users_repo.get_active()

    count = 0
    for user in users:
        try:
            await generate_daily_report(ctx, str(user.id))
            count += 1
        except Exception:
            logger.exception("Daily report failed", extra={"ctx_user_id": str(user.id)})

    return {"status": "ok", "generated": count}
