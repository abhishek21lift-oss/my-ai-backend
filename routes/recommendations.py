import redis.asyncio as aioredis
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import CurrentUser
from core.redis import get_redis
from models.schemas import DailyRecommendationsResponse
from services.recommendations import RecommendationsService

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/daily", response_model=DailyRecommendationsResponse)
async def get_daily_recommendations(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> DailyRecommendationsResponse:
    svc = RecommendationsService(session, redis)
    return await svc.get_daily(current_user.id)
