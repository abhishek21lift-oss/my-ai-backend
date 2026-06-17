from typing import List, Optional
from uuid import UUID

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import CurrentUser
from core.redis import get_redis
from models.db import TrendPeriodEnum
from models.schemas import (
    PaginatedResponse,
    TrendAnalysisCreate,
    TrendAnalysisResponse,
    TrendAnalyzeRequest,
)
from services.trends import TrendService

router = APIRouter(prefix="/trends", tags=["trends"])


@router.post("/analyze", response_model=TrendAnalysisResponse, status_code=status.HTTP_201_CREATED)
async def analyze_trend(
    payload: TrendAnalyzeRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> TrendAnalysisResponse:
    svc = TrendService(session, redis)
    trend = await svc.analyze(current_user.id, payload)
    return TrendAnalysisResponse.model_validate(trend)


@router.post("", response_model=TrendAnalysisResponse, status_code=status.HTTP_201_CREATED)
async def create_trend(
    payload: TrendAnalysisCreate,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> TrendAnalysisResponse:
    svc = TrendService(session, redis)
    trend = await svc.create_manual(current_user.id, payload)
    return TrendAnalysisResponse.model_validate(trend)


@router.get("", response_model=PaginatedResponse[TrendAnalysisResponse])
async def list_trends(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    period: Optional[TrendPeriodEnum] = Query(None),
) -> PaginatedResponse[TrendAnalysisResponse]:
    svc = TrendService(session, redis)
    items, total = await svc.list(current_user.id, offset, limit, period)
    return PaginatedResponse(
        items=[TrendAnalysisResponse.model_validate(t) for t in items],
        total=total,
        offset=offset,
        limit=limit,
        has_more=(offset + limit) < total,
    )


@router.get("/rising", response_model=List[TrendAnalysisResponse])
async def get_rising_trends(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> List[TrendAnalysisResponse]:
    svc = TrendService(session, redis)
    items = await svc.get_rising(current_user.id)
    return [TrendAnalysisResponse.model_validate(t) for t in items]


@router.get("/viral", response_model=List[TrendAnalysisResponse])
async def get_viral_trends(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> List[TrendAnalysisResponse]:
    svc = TrendService(session, redis)
    items = await svc.get_viral(current_user.id)
    return [TrendAnalysisResponse.model_validate(t) for t in items]


@router.get("/{trend_id}", response_model=TrendAnalysisResponse)
async def get_trend(
    trend_id: UUID,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> TrendAnalysisResponse:
    svc = TrendService(session, redis)
    trend = await svc.get(current_user.id, trend_id)
    return TrendAnalysisResponse.model_validate(trend)
