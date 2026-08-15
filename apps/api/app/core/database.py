from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

"""
 创建数据库连接URL
"""
DATABASE_URL = settings.DATABASE_URL.replace(
    "postgresql://",
    "postgresql+asyncpg://",
)

"""
 创建数据库连接池
"""
engine = create_async_engine(DATABASE_URL, echo=True)

"""
 创建数据库会话工厂
"""
AsyncSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话
    """
    async with AsyncSessionLocal() as session:
        yield session


async def close_db(app):
    """
    关闭数据库连接池
    """
    await engine.dispose()
