import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BusinessException,
    NotFoundException,
    UnauthorizedException,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.repositories.user_repository import UserRepository
from app.schemas.user import TokenResponse, UserCreate, UserLogin, UserResponse


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

    # 根据 ID 获取用户
    async def get_user_by_id(self, db: AsyncSession, user_id: int) -> UserResponse:

        user = await self.repository.get_by_id(db, user_id)

        if not user:
            raise NotFoundException("用户不存在")

        return UserResponse.model_validate(user)

    # 根据邮箱获取用户
    async def get_user_by_email(self, db: AsyncSession, email: str) -> UserResponse:
        user = await self.repository.get_by_email(db, email)
        if not user:
            raise NotFoundException("用户不存在")
        return UserResponse.model_validate(user)

    def _tokens_for(self, user) -> TokenResponse:
        return TokenResponse(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
            token_type="bearer",
            user=UserResponse.model_validate(user),
        )

    # 根据 token 获取用户
    async def get_user_by_token(self, db: AsyncSession, token: str) -> UserResponse:
        try:
            payload = decode_token(token)
            if payload.get("typ") != "access":
                raise UnauthorizedException("Token 无效")

            try:
                user_id = int(payload.get("sub"))
            except (TypeError, ValueError) as e:
                raise UnauthorizedException("Token 无效") from e

            user = await self.repository.get_by_id(db, user_id)

            if not user:
                raise UnauthorizedException("用户不存在")
            return UserResponse.model_validate(user)
        except UnauthorizedException:
            raise
        except jwt.ExpiredSignatureError:
            raise UnauthorizedException("Token 过期")
        except jwt.InvalidTokenError:
            raise UnauthorizedException("Token 无效")

    async def refresh_tokens(
        self, db: AsyncSession, refresh_token: str
    ) -> TokenResponse:
        try:
            payload = decode_token(refresh_token)
            if payload.get("typ") != "refresh":
                raise UnauthorizedException("Token 无效")

            try:
                user_id = int(payload.get("sub"))
            except (TypeError, ValueError) as e:
                raise UnauthorizedException("Token 无效") from e

            user = await self.repository.get_by_id(db, user_id)
            if not user:
                raise UnauthorizedException("用户不存在")
            return self._tokens_for(user)
        except UnauthorizedException:
            raise
        except jwt.ExpiredSignatureError:
            raise UnauthorizedException("Token 过期")
        except jwt.InvalidTokenError:
            raise UnauthorizedException("Token 无效")

    # 获取所有用户
    async def get_users(self, db: AsyncSession) -> list[UserResponse]:

        users = await self.repository.get_all(db)

        return [UserResponse.model_validate(user) for user in users]

    # 登录
    async def login(self, db: AsyncSession, login_data: UserLogin) -> TokenResponse:
        user = await self.repository.get_by_email(db, login_data.email)

        if not user or not verify_password(user.password_hash, login_data.password):
            raise UnauthorizedException("邮箱或密码错误")

        return self._tokens_for(user)
