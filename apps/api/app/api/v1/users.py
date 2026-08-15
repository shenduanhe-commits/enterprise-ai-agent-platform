from fastapi import APIRouter, HTTPException

from app.core.dependencies import DbSession
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


user_service = UserService(UserRepository())


@router.post("", response_model=UserResponse)
async def create_user(user_data: UserCreate, db: DbSession):

    try:
        return await user_service.create_user(db, user_data)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: DbSession):

    user = await user_service.get_user(db, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.get("", response_model=list[UserResponse])
async def get_users(db: DbSession):

    return await user_service.get_users(db)
