from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessException, NotFoundException
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserResponse


class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def create_user(
        self, db: AsyncSession, user_data: UserCreate
    ) -> UserResponse:

        # 查询用户是否存在

        existing_user = await self.repository.get_by_email(db, user_data.email)

        if existing_user:
            raise BusinessException("邮箱已经存在")

        # 创建用户

        user = await self.repository.create(db, user_data)

        # ORM Model 转 Response Schema

        return UserResponse.model_validate(user)

    async def get_user(self, db: AsyncSession, user_id: int) -> UserResponse:

        user = await self.repository.get_by_id(db, user_id)

        if not user:
            raise NotFoundException("用户不存在")

        return UserResponse.model_validate(user)

    async def get_users(self, db: AsyncSession) -> list[UserResponse]:

        users = await self.repository.get_all(db)

        return [UserResponse.model_validate(user) for user in users]
