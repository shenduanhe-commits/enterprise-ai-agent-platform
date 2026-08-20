from fastapi import APIRouter

from app.core.dependencies import CurrentUser, DbSession
from app.repositories.user_repository import UserRepository
from app.schemas.user import (
    RefreshRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["Auth"])

user_service = UserService(UserRepository())


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: DbSession):
    return await user_service.create_user(db, user_data)


@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin, db: DbSession):
    return await user_service.login(db, login_data)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: DbSession):
    return await user_service.refresh_tokens(db, body.refresh_token)


@router.get("/me", response_model=UserResponse)
async def me(current_user: CurrentUser):
    return current_user
