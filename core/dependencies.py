from typing import Annotated
from uuid import UUID

import redis.asyncio as aioredis
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.cache import CacheService
from core.database import get_db
from core.redis import get_redis
from core.security import verify_api_key
from exceptions.app_exceptions import AuthenticationError, AuthorizationError
from models.db import ApiKey, PlanEnum, User

PLAN_LEVEL = {PlanEnum.free: 0, PlanEnum.pro: 1, PlanEnum.enterprise: 2}


async def get_current_user(
    x_api_key: Annotated[str | None, Header()] = None,
    session: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> User:
    if not x_api_key:
        raise AuthenticationError("Missing X-API-Key header")

    prefix = x_api_key[:10]
    cache = CacheService(redis, default_ttl=300)
    cache_key = CacheService.key("apikey", prefix)

    cached = await cache.get(cache_key)

    if cached:
        key_hash = cached["key_hash"]
        if not verify_api_key(x_api_key, key_hash):
            raise AuthenticationError("Invalid API key")
        user = User(
            id=cached["user_id"],
            email=cached["email"],
            plan=PlanEnum(cached["plan"]),
            is_active=cached["is_active"],
            monthly_token_quota=cached.get("monthly_token_quota"),
        )
        return user

    from sqlalchemy import select
    from models.db import ApiKey

    result = await session.execute(
        select(ApiKey, User)
        .join(User, ApiKey.user_id == User.id)
        .where(ApiKey.key_prefix == prefix, ApiKey.is_active == True)
    )
    row = result.first()

    if not row:
        raise AuthenticationError("Invalid API key")

    api_key_obj, user = row

    if not verify_api_key(x_api_key, api_key_obj.key_hash):
        raise AuthenticationError("Invalid API key")

    if not user.is_active:
        raise AuthenticationError("Account is inactive")

    # Cache resolved auth for 5 minutes
    await cache.set(cache_key, {
        "key_hash": api_key_obj.key_hash,
        "user_id": str(user.id),
        "email": user.email,
        "plan": user.plan.value,
        "is_active": user.is_active,
        "monthly_token_quota": user.monthly_token_quota,
    })

    # Update last_used_at (fire-and-forget, don't block request)
    from sqlalchemy import update
    from datetime import datetime, timezone
    await session.execute(
        update(ApiKey)
        .where(ApiKey.id == api_key_obj.id)
        .values(last_used_at=datetime.now(timezone.utc))
    )
    await session.commit()

    return user


def require_plan(min_plan: PlanEnum):
    async def _check(user: User = Depends(get_current_user)) -> User:
        if PLAN_LEVEL[user.plan] < PLAN_LEVEL[min_plan]:
            raise AuthorizationError(
                f"This feature requires the {min_plan.value} plan or higher"
            )
        return user
    return _check


CurrentUser = Annotated[User, Depends(get_current_user)]
