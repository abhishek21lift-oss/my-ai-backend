from typing import Optional
from uuid import UUID

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import CurrentUser
from core.redis import get_redis
from models.db import PlatformEnum, ScriptStatusEnum
from models.schemas import (
    PaginatedResponse,
    PublishRequest,
    RateRequest,
    ScriptGenerateRequest,
    ScriptResponse,
    ScriptUpdate,
)
from services.scripts import ScriptService

router = APIRouter(prefix="/scripts", tags=["scripts"])


@router.post("", response_model=ScriptResponse, status_code=status.HTTP_201_CREATED)
async def generate_script(
    payload: ScriptGenerateRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> ScriptResponse:
    svc = ScriptService(session, redis)
    script = await svc.generate(current_user.id, payload)
    return ScriptResponse.model_validate(script)


@router.get("", response_model=PaginatedResponse[ScriptResponse])
async def list_scripts(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[ScriptStatusEnum] = Query(None),
    platform: Optional[PlatformEnum] = Query(None),
) -> PaginatedResponse[ScriptResponse]:
    svc = ScriptService(session, redis)
    items, total = await svc.list(current_user.id, offset, limit, status, platform)
    return PaginatedResponse(
        items=[ScriptResponse.model_validate(s) for s in items],
        total=total,
        offset=offset,
        limit=limit,
        has_more=(offset + limit) < total,
    )


@router.get("/{script_id}", response_model=ScriptResponse)
async def get_script(
    script_id: UUID,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> ScriptResponse:
    svc = ScriptService(session, redis)
    script = await svc.get(current_user.id, script_id)
    return ScriptResponse.model_validate(script)


@router.put("/{script_id}", response_model=ScriptResponse)
async def update_script(
    script_id: UUID,
    payload: ScriptUpdate,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> ScriptResponse:
    svc = ScriptService(session, redis)
    script = await svc.update(current_user.id, script_id, payload)
    return ScriptResponse.model_validate(script)


@router.post("/{script_id}/approve", response_model=ScriptResponse)
async def approve_script(
    script_id: UUID,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> ScriptResponse:
    svc = ScriptService(session, redis)
    script = await svc.approve(current_user.id, script_id)
    return ScriptResponse.model_validate(script)


@router.post("/{script_id}/publish", response_model=ScriptResponse)
async def publish_script(
    script_id: UUID,
    payload: PublishRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> ScriptResponse:
    svc = ScriptService(session, redis)
    script = await svc.publish(current_user.id, script_id, payload.publish_platform)
    return ScriptResponse.model_validate(script)


@router.post("/{script_id}/rate", response_model=ScriptResponse)
async def rate_script(
    script_id: UUID,
    payload: RateRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> ScriptResponse:
    svc = ScriptService(session, redis)
    script = await svc.rate(current_user.id, script_id, payload.rating, payload.notes)
    return ScriptResponse.model_validate(script)


@router.delete("/{script_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_script(
    script_id: UUID,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> None:
    svc = ScriptService(session, redis)
    await svc.delete(current_user.id, script_id)
