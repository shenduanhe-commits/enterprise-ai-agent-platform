from fastapi import APIRouter

from app.core.dependencies import DbSession
from app.repositories.user_repository import UserRepository
from app.schemas.user import TokenResponse, UserLogin
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["Auth"])

user_service = UserService(UserRepository())


@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin, db: DbSession):
    return await user_service.login(db, login_data)
