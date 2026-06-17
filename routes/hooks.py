from typing import List, Optional
from uuid import UUID

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import CurrentUser
from core.redis import get_redis
from models.db import PlatformEnum
from models.schemas import HookGenerateRequest, HookResponse, PaginatedResponse, RateRequest
from services.hooks import HookService

router = APIRouter(prefix="/hooks", tags=["hooks"])


@router.post("", response_model=List[HookResponse], status_code=status.HTTP_201_CREATED)
async def generate_hooks(
    payload: HookGenerateRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> List[HookResponse]:
    svc = HookService(session, redis)
    hooks = await svc.generate(current_user.id, payload)
    return [HookResponse.model_validate(h) for h in hooks]


@router.get("", response_model=PaginatedResponse[HookResponse])
async def list_hooks(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    platform: Optional[PlatformEnum] = Query(None),
    unused_only: bool = Query(False),
) -> PaginatedResponse[HookResponse]:
    svc = HookService(session, redis)
    items, total = await svc.list(current_user.id, offset, limit, platform, unused_only)
    return PaginatedResponse(
        items=[HookResponse.model_validate(h) for h in items],
        total=total,
        offset=offset,
        limit=limit,
        has_more=(offset + limit) < total,
    )


@router.get("/top", response_model=List[HookResponse])
async def get_top_hooks(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    limit: int = Query(10, ge=1, le=50),
) -> List[HookResponse]:
    svc = HookService(session, redis)
    items = await svc.get_top(current_user.id, limit)
    return [HookResponse.model_validate(h) for h in items]


@router.get("/{hook_id}", response_model=HookResponse)
async def get_hook(
    hook_id: UUID,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> HookResponse:
    svc = HookService(session, redis)
    hook = await svc.get(current_user.id, hook_id)
    return HookResponse.model_validate(hook)


@router.post("/{hook_id}/use", response_model=HookResponse)
async def mark_hook_used(
    hook_id: UUID,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> HookResponse:
    svc = HookService(session, redis)
    hook = await svc.mark_used(current_user.id, hook_id)
    return HookResponse.model_validate(hook)


@router.post("/{hook_id}/rate", response_model=HookResponse)
async def rate_hook(
    hook_id: UUID,
    payload: RateRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> HookResponse:
    svc = HookService(session, redis)
    hook = await svc.rate(current_user.id, hook_id, payload.rating, payload.notes)
    return HookResponse.model_validate(hook)


@router.delete("/{hook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_hook(
    hook_id: UUID,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> None:
    svc = HookService(session, redis)
    await svc.delete(current_user.id, hook_id)
