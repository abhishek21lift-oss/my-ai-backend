from typing import Optional
from uuid import UUID

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import CurrentUser
from core.redis import get_redis
from models.db import ReportStatusEnum
from models.schemas import (
    PaginatedResponse,
    ResearchGenerateRequest,
    ResearchReportResponse,
    ResearchReportUpdate,
)
from services.research import ResearchService

router = APIRouter(prefix="/research", tags=["research"])


@router.post("", response_model=ResearchReportResponse, status_code=status.HTTP_201_CREATED)
async def generate_research(
    payload: ResearchGenerateRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> ResearchReportResponse:
    svc = ResearchService(session, redis)
    report = await svc.generate(current_user.id, payload)
    return ResearchReportResponse.model_validate(report)


@router.get("", response_model=PaginatedResponse[ResearchReportResponse])
async def list_research(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[ReportStatusEnum] = Query(None),
) -> PaginatedResponse[ResearchReportResponse]:
    svc = ResearchService(session, redis)
    items, total = await svc.list(current_user.id, offset, limit, status)
    return PaginatedResponse(
        items=[ResearchReportResponse.model_validate(r) for r in items],
        total=total,
        offset=offset,
        limit=limit,
        has_more=(offset + limit) < total,
    )


@router.get("/{report_id}", response_model=ResearchReportResponse)
async def get_research(
    report_id: UUID,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> ResearchReportResponse:
    svc = ResearchService(session, redis)
    report = await svc.get(current_user.id, report_id)
    return ResearchReportResponse.model_validate(report)


@router.put("/{report_id}", response_model=ResearchReportResponse)
async def update_research(
    report_id: UUID,
    payload: ResearchReportUpdate,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> ResearchReportResponse:
    svc = ResearchService(session, redis)
    report = await svc.update(current_user.id, report_id, payload)
    return ResearchReportResponse.model_validate(report)


@router.post("/{report_id}/archive", response_model=ResearchReportResponse)
async def archive_research(
    report_id: UUID,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> ResearchReportResponse:
    svc = ResearchService(session, redis)
    report = await svc.archive(current_user.id, report_id)
    return ResearchReportResponse.model_validate(report)


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_research(
    report_id: UUID,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> None:
    svc = ResearchService(session, redis)
    await svc.delete(current_user.id, report_id)
