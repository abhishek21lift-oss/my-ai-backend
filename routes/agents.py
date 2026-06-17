import logging
from typing import Optional
from uuid import UUID

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from agents.orchestrator.schemas import PipelineRequest
from agents.orchestrator.workflow import run_content_pipeline
from core.config import get_settings
from core.database import get_db
from core.dependencies import CurrentUser
from core.redis import get_redis
from models.db import AgentStatusEnum, PlatformEnum
from models.schemas import AgentLogResponse, AgentRunRequest, AgentRunResponse, PaginatedResponse
from repositories.agent_logs import AgentLogsRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agents", tags=["agents"])


@router.post(
    "/run",
    response_model=AgentRunResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger the full content pipeline (async via ARQ)",
)
async def trigger_pipeline(
    payload: AgentRunRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> AgentRunResponse:
    """
    Enqueues the 5-agent pipeline as an ARQ background job.
    Returns the orchestrator log_id immediately for status polling.
    """
    from arq import create_pool
    from arq.connections import RedisSettings
    from core.config import get_settings

    settings = get_settings()

    # Create orchestrator log so the client can poll immediately
    logs_repo = AgentLogsRepository(session)
    orch_log = await logs_repo.create(
        user_id=current_user.id,
        agent_name="orchestrator",
        task_type="content_pipeline",
        status=AgentStatusEnum.pending,
    )
    await session.commit()

    # Enqueue the ARQ job
    arq_pool = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
    job = await arq_pool.enqueue_job(
        "run_agent_workflow",
        user_id=str(current_user.id),
        topic_id=str(payload.topic_id),
        platform=payload.platform.value,
        orchestrator_log_id=str(orch_log.id),
    )
    await arq_pool.aclose()

    logger.info(
        "Pipeline enqueued",
        extra={
            "ctx_log_id": str(orch_log.id),
            "ctx_job_id": job.job_id if job else "none",
            "ctx_user_id": str(current_user.id),
        },
    )
    return AgentRunResponse(
        orchestrator_log_id=orch_log.id,
        status=AgentStatusEnum.pending,
        message="Pipeline queued. Poll /agents/run/{orchestrator_log_id} for status.",
        job_id=job.job_id if job else None,
    )


@router.post(
    "/run/sync",
    response_model=AgentRunResponse,
    status_code=status.HTTP_200_OK,
    summary="Run the full pipeline synchronously (for testing / low-latency use)",
)
async def run_pipeline_sync(
    payload: AgentRunRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> AgentRunResponse:
    """
    Runs the pipeline in-request. Use only for development or small topics.
    Production usage should prefer the async /run endpoint.
    """
    request = PipelineRequest(
        user_id=current_user.id,
        topic_id=payload.topic_id,
        platform=payload.platform,
    )
    result = await run_content_pipeline(request, session, redis)
    return AgentRunResponse(
        orchestrator_log_id=result.orchestrator_log_id,
        status=AgentStatusEnum.completed if result.success else AgentStatusEnum.failed,
        message="Pipeline complete." if result.success else f"Pipeline failed: {result.error}",
        result=result.to_dict(),
    )


@router.get(
    "/run/{log_id}",
    response_model=AgentRunResponse,
    summary="Get pipeline status by orchestrator log ID",
)
async def get_pipeline_status(
    log_id: UUID,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db),
) -> AgentRunResponse:
    logs_repo = AgentLogsRepository(session)
    log = await logs_repo.get_by_id(log_id)
    if not log or log.user_id != current_user.id:
        from exceptions.app_exceptions import NotFoundError
        raise NotFoundError(f"Pipeline log {log_id} not found")

    sub_tasks = await logs_repo.get_sub_tasks(log_id)
    stages = [
        {
            "agent_name": s.agent_name,
            "task_type": s.task_type,
            "status": s.status.value,
            "duration_ms": s.duration_ms,
            "input_tokens": s.input_tokens,
            "output_tokens": s.output_tokens,
            "error": s.error,
        }
        for s in sub_tasks
    ]

    return AgentRunResponse(
        orchestrator_log_id=log.id,
        status=log.status,
        message=f"Pipeline {log.status.value}",
        result=log.output,
        stages=stages,
    )


@router.get(
    "/logs",
    response_model=PaginatedResponse[AgentLogResponse],
    summary="List agent run logs for the current user",
)
async def list_agent_logs(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    agent_name: Optional[str] = Query(None),
) -> PaginatedResponse[AgentLogResponse]:
    logs_repo = AgentLogsRepository(session)
    if agent_name:
        items = await logs_repo.get_by_agent(agent_name, offset, limit)
        total = len(items)
    else:
        items = await logs_repo.get_by_user(current_user.id, offset, limit)
        total = await logs_repo.count()
    return PaginatedResponse(
        items=[AgentLogResponse.model_validate(l) for l in items],
        total=total,
        offset=offset,
        limit=limit,
        has_more=(offset + limit) < total,
    )
