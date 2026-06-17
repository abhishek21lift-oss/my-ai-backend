from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import CurrentUser
from exceptions.app_exceptions import ConflictError, NotFoundError
from models.schemas import PaginatedResponse, TopicCreate, TopicResponse, TopicUpdate
from repositories.topics import TopicsRepository

router = APIRouter(prefix="/topics", tags=["topics"])


@router.post("", response_model=TopicResponse, status_code=status.HTTP_201_CREATED)
async def create_topic(
    payload: TopicCreate,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db),
) -> TopicResponse:
    repo = TopicsRepository(session)
    if await repo.name_exists(current_user.id, payload.name):
        raise ConflictError(f"Topic '{payload.name}' already exists")
    topic = await repo.create(user_id=current_user.id, **payload.model_dump())
    return TopicResponse.model_validate(topic)


@router.get("", response_model=PaginatedResponse[TopicResponse])
async def list_topics(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None),
    active_only: bool = Query(False),
) -> PaginatedResponse[TopicResponse]:
    repo = TopicsRepository(session)
    if category:
        items = await repo.get_by_category(current_user.id, category)
        items = items[offset : offset + limit]
        total = len(items)
    elif active_only:
        items = await repo.get_active_by_user(current_user.id)
        total = len(items)
        items = items[offset : offset + limit]
    else:
        items = await repo.get_by_user(current_user.id, offset, limit)
        total = await repo.count_by_user(current_user.id)
    return PaginatedResponse(
        items=[TopicResponse.model_validate(t) for t in items],
        total=total,
        offset=offset,
        limit=limit,
        has_more=(offset + limit) < total,
    )


@router.get("/{topic_id}", response_model=TopicResponse)
async def get_topic(
    topic_id: UUID,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db),
) -> TopicResponse:
    repo = TopicsRepository(session)
    topic = await repo.get_by_id(topic_id)
    if not topic or topic.user_id != current_user.id:
        raise NotFoundError(f"Topic {topic_id} not found")
    return TopicResponse.model_validate(topic)


@router.put("/{topic_id}", response_model=TopicResponse)
async def update_topic(
    topic_id: UUID,
    payload: TopicUpdate,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db),
) -> TopicResponse:
    repo = TopicsRepository(session)
    topic = await repo.get_by_id(topic_id)
    if not topic or topic.user_id != current_user.id:
        raise NotFoundError(f"Topic {topic_id} not found")
    updated = await repo.update(topic_id, **{k: v for k, v in payload.model_dump().items() if v is not None})
    return TopicResponse.model_validate(updated)


@router.delete("/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_topic(
    topic_id: UUID,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db),
) -> None:
    repo = TopicsRepository(session)
    topic = await repo.get_by_id(topic_id)
    if not topic or topic.user_id != current_user.id:
        raise NotFoundError(f"Topic {topic_id} not found")
    await repo.deactivate(topic_id)
