from typing import List, Optional
from uuid import UUID

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import CurrentUser
from core.redis import get_redis
from models.db import PlatformEnum
from models.schemas import (
    PaginatedResponse,
    ViralContentCreate,
    ViralContentResponse,
    ViralContentUpdate,
)
from services.viral_content import ViralContentService

router = APIRouter(prefix="/viral-content", tags=["viral-content"])


@router.post("", response_model=ViralContentResponse, status_code=status.HTTP_201_CREATED)
async def create_viral_content(
    payload: ViralContentCreate,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> ViralContentResponse:
    svc = ViralContentService(session, redis)
    item = await svc.create(current_user.id, payload)
    return ViralContentResponse.model_validate(item)


@router.get("", response_model=PaginatedResponse[ViralContentResponse])
async def list_viral_content(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    platform: Optional[PlatformEnum] = Query(None),
    min_score: Optional[float] = Query(None, ge=0, le=100),
) -> PaginatedResponse[ViralContentResponse]:
    svc = ViralContentService(session, redis)
    items, total = await svc.list(current_user.id, offset, limit, platform, min_score)
    return PaginatedResponse(
        items=[ViralContentResponse.model_validate(i) for i in items],
        total=total,
        offset=offset,
        limit=limit,
        has_more=(offset + limit) < total,
    )


@router.get("/top", response_model=List[ViralContentResponse])
async def get_top_viral(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    limit: int = Query(10, ge=1, le=50),
) -> List[ViralContentResponse]:
    svc = ViralContentService(session, redis)
    items = await svc.get_top(current_user.id, limit)
    return [ViralContentResponse.model_validate(i) for i in items]


@router.get("/{content_id}", response_model=ViralContentResponse)
async def get_viral_content(
    content_id: UUID,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> ViralContentResponse:
    svc = ViralContentService(session, redis)
    item = await svc.get(current_user.id, content_id)
    return ViralContentResponse.model_validate(item)


@router.put("/{content_id}", response_model=ViralContentResponse)
async def update_viral_content(
    content_id: UUID,
    payload: ViralContentUpdate,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> ViralContentResponse:
    svc = ViralContentService(session, redis)
    item = await svc.update(current_user.id, content_id, payload)
    return ViralContentResponse.model_validate(item)


@router.delete("/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_viral_content(
    content_id: UUID,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> None:
    svc = ViralContentService(session, redis)
    await svc.delete(current_user.id, content_id)
