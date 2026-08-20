from fastapi import APIRouter

from app.core.dependencies import CurrentUser, DbSession
from app.core.exceptions import NotFoundException
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])

user_service = UserService(UserRepository())


@router.post("", response_model=UserResponse)
async def create_user(user_data: UserCreate, db: DbSession):

    return await user_service.create_user(db, user_data)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser):

    return current_user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, current_user: CurrentUser):
    if user_id != current_user.id:
        raise NotFoundException("用户不存在")
    return current_user
