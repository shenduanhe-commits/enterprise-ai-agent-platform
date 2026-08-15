from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessException, NotFoundException
from app.core.security import hash_password
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

        # 哈希放在 Service：API 只收明文，库里只存 password_hash。
        user = await self.repository.create(
            db,
            email=user_data.email,
            password_hash=hash_password(user_data.password),
        )

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
