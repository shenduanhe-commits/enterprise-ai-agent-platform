from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """
    User Repository
    """

    async def create(self, db: AsyncSession, email: str, password_hash: str) -> User:
        """
        Create a new user. password_hash 必须已由 Service 算好。
        """
        db_user = User(email=email, password_hash=password_hash)
        # 把对象放进当前 Session 的待写入队列（pending），还没有真正执行 SQL。
        db.add(db_user)
        # 提交事务：执行 INSERT，把数据写入 PostgreSQL，并结束事务。
        await db.commit()
        # 从数据库读回这一行，填充生成的字段（如自增 id、created_at）。
        await db.refresh(db_user)
        # 返回已落库、字段齐全的 User 对象给上层。
        return db_user

    async def get_by_id(self, db: AsyncSession, user_id: int) -> User | None:

        result = await db.execute(select(User).where(User.id == user_id))

        return result.scalar_one_or_none()

    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:

        result = await db.execute(select(User).where(User.email == email))

        return result.scalar_one_or_none()

    async def get_all(self, db: AsyncSession) -> list[User]:

        result = await db.execute(select(User))

        return result.scalars().all()
