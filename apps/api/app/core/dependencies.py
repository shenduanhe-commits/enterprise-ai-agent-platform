from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserResponse
from app.services.user_service import UserService


async def get_db() -> AsyncGenerator[AsyncSession, None]:

    async with AsyncSessionLocal() as session:
        yield session


DbSession = Annotated[AsyncSession, Depends(get_db)]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    db: DbSession,
    token: str = Depends(oauth2_scheme),
) -> UserResponse:
    user_service = UserService(UserRepository())
    return await user_service.get_user_by_token(db, token)


CurrentUser = Annotated[UserResponse, Depends(get_current_user)]
