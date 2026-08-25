from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from app.core.config import settings


@asynccontextmanager
async def open_postgres_checkpointer() -> AsyncIterator[AsyncPostgresSaver]:
    """进程内共享的 Postgres checkpointer。thread_id 用 conversation_id。

    用 .env 里的 postgresql://。SQLAlchemy 才需要改成 postgresql+asyncpg://。
    """
    async with AsyncConnectionPool(
        conninfo=settings.DATABASE_URL,
        min_size=1,
        max_size=5,
        kwargs={
            "autocommit": True,
            "prepare_threshold": 0,
            "row_factory": dict_row,
        },
        timeout=15,
    ) as pool:
        saver = AsyncPostgresSaver(conn=pool)
        await saver.setup()
        yield saver
