import logging
from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import FastAPI
from langgraph.checkpoint.memory import InMemorySaver

from app.ai.runtime.checkpointer import open_postgres_checkpointer
from app.core.logging import setup_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    生命周期管理
    """
    setup_logging()

    print("EAAP API starting...")
    async with AsyncExitStack() as stack:
        try:
            app.state.checkpointer = await stack.enter_async_context(
                open_postgres_checkpointer()
            )
            print("Graph checkpointer: Postgres")
        except Exception:
            logger.exception(
                "Postgres checkpointer unavailable; graph state will not survive restart"
            )
            app.state.checkpointer = InMemorySaver()
            print("Graph checkpointer: InMemory (dev fallback)")
        yield

    print("EAAP API shutting down...")
