from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import CurrentUser
from core.security import generate_api_key, hash_api_key
from exceptions.app_exceptions import NotFoundError
from models.db import PlanEnum
from models.schemas import APIKeyCreate, APIKeyCreatedResponse, APIKeyResponse, RegisterRequest, RegisterResponse, UserResponse
from repositories.api_keys import ApiKeysRepository
from repositories.users import UsersRepository

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    session: AsyncSession = Depends(get_db),
) -> RegisterResponse:
    users_repo = UsersRepository(session)
    if await users_repo.email_exists(payload.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = await users_repo.create(
        email=payload.email,
        display_name=payload.display_name,
        plan=PlanEnum.free,
        is_active=True,
    )
    raw_key, key_hash, key_prefix = generate_api_key()
    keys_repo = ApiKeysRepository(session)
    await keys_repo.create(
        user_id=user.id,
        key_hash=key_hash,
        key_prefix=key_prefix,
        name="Default",
        rate_limit_rpm=60,
    )
    return RegisterResponse(
        user=UserResponse.model_validate(user),
        api_key=raw_key,
    )


@router.post("/keys", response_model=APIKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    payload: APIKeyCreate,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db),
) -> APIKeyCreatedResponse:
    raw_key, key_hash, key_prefix = generate_api_key()
    repo = ApiKeysRepository(session)
    api_key = await repo.create(
        user_id=current_user.id,
        key_hash=key_hash,
        key_prefix=key_prefix,
        name=payload.name,
        rate_limit_rpm=payload.rate_limit_rpm or 60,
        rate_limit_tpd=payload.rate_limit_tpd,
        expires_at=payload.expires_at,
    )
    return APIKeyCreatedResponse(
        id=api_key.id,
        key=raw_key,
        key_prefix=api_key.key_prefix,
        name=api_key.name,
        rate_limit_rpm=api_key.rate_limit_rpm,
        created_at=api_key.created_at,
    )


@router.get("/keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db),
) -> List[APIKeyResponse]:
    repo = ApiKeysRepository(session)
    keys = await repo.get_by_user(current_user.id)
    return [APIKeyResponse.model_validate(k) for k in keys]


@router.delete("/keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: UUID,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_db),
) -> None:
    repo = ApiKeysRepository(session)
    key = await repo.get_by_id(key_id)
    if not key or key.user_id != current_user.id:
        raise NotFoundError(f"API key {key_id} not found")
    await repo.deactivate(key_id)
