import logging
from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import FastAPI
from langgraph.checkpoint.memory import InMemorySaver

from app.ai.knowledge.store import get_chunk_store
from app.ai.runtime.checkpointer import open_postgres_checkpointer
from app.core.database import AsyncSessionLocal
from app.core.logging import setup_logging
from app.repositories.agent_repository import AgentRepository
from app.repositories.knowledge_document_repository import KnowledgeDocumentRepository
from app.services.knowledge_service import KnowledgeService

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

        try:
            store = get_chunk_store()
            rebuilt = await store.ensure_collection()
            if rebuilt:
                async with AsyncSessionLocal() as db:
                    rebuilt_count = await KnowledgeService(
                        KnowledgeDocumentRepository(),
                        AgentRepository(),
                        chunk_store=store,
                    ).reindex_all(db)
                print(f"Knowledge collection rebuilt; reindexed {rebuilt_count} documents")
        except Exception:
            logger.exception("knowledge collection/reindex unavailable")

        yield

    print("EAAP API shutting down...")
