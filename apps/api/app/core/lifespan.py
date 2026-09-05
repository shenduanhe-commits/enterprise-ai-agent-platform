import logging
from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import FastAPI
from langgraph.checkpoint.memory import InMemorySaver

from app.ai.knowledge.store import get_chunk_store
from app.ai.mcp.client import create_mcp_clients, register_mcp_tools
from app.ai.mcp.servers import MCP_ENABLED
from app.ai.runtime.checkpointer import open_postgres_checkpointer
from app.core.database import AsyncSessionLocal
from app.core.logging import setup_logging
from app.repositories.agent_repository import AgentRepository
from app.repositories.knowledge_document_repository import KnowledgeDocumentRepository
from app.repositories.tool_repository import ToolRepository
from app.services.knowledge_service import KnowledgeService
from app.services.tool_service import ToolService

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
                print(
                    f"Knowledge collection rebuilt; reindexed {rebuilt_count} documents"
                )
        except Exception:
            logger.exception("knowledge collection/reindex unavailable")

        app.state.mcp_clients = []
        app.state.mcp_tools = []
        if MCP_ENABLED:
            pairs = await create_mcp_clients(stack)
            app.state.mcp_clients = [client for _, client in pairs]
            app.state.mcp_tools = await register_mcp_tools(app.state.mcp_clients)
            names = [name for name, _ in pairs]
            print(f"MCP: {len(app.state.mcp_tools)} tool(s) from {names or 'none'}")
            if not app.state.mcp_tools:
                logger.warning("MCP: no tools discovered; builtin tools only")

        try:
            async with AsyncSessionLocal() as db:
                synced = await ToolService(
                    ToolRepository(), AgentRepository()
                ).sync_catalog(db, app.state.mcp_tools)
            print(f"Tool catalog: {synced} row(s)")
        except Exception:
            logger.exception("tool catalog sync unavailable")

        yield

    print("EAAP API shutting down...")
