from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.exceptions import UnauthorizedException
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserResponse
from app.services.user_service import UserService

_bearer = HTTPBearer(auto_error=False)

BearerCreds = Annotated[
    HTTPAuthorizationCredentials | None,
    Depends(_bearer),
]


async def get_db() -> AsyncGenerator[AsyncSession, None]:

    async with AsyncSessionLocal() as session:
        yield session


DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    db: DbSession,
    creds: BearerCreds,
) -> UserResponse:
    if creds is None or not creds.credentials:
        raise UnauthorizedException("未登录")
    user_service = UserService(UserRepository())
    return await user_service.get_user_by_token(db, creds.credentials)


CurrentUser = Annotated[UserResponse, Depends(get_current_user)]
