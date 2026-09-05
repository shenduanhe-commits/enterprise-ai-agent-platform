from typing import Annotated

from fastapi import Depends, Request
from langgraph.checkpoint.base import BaseCheckpointSaver
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.knowledge.reranker import get_reranker
from app.ai.knowledge.retriever import KnowledgeRetriever
from app.ai.knowledge.store import get_chunk_store
from app.ai.llm.gateway import (
    LLMGateway,
)
from app.ai.llm.providers.anthropic import (
    AnthropicProvider,
)
from app.ai.llm.providers.mock import (
    MockLLMProvider,
)
from app.ai.llm.providers.openai import (
    OpenAIProvider,
)
from app.ai.llm.providers.qwen import (
    QwenProvider,
)
from app.ai.memory.manager import (
    MemoryManager,
)
from app.ai.prompts.manager import (
    PromptManager,
)
from app.ai.runtime.agent_executor import (
    AgentExecutor,
)
from app.ai.tools import BUILTIN_TOOLS
from app.ai.tools.base import BaseTool
from app.ai.tools.manager import ToolManager
from app.core.config import settings
from app.core.database import get_db
from app.repositories.agent_repository import AgentRepository
from app.repositories.conversation_message_repository import (
    ConversationMessageRepository,
)
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.prompt_repository import PromptRepository
from app.repositories.tool_repository import ToolRepository
from app.services.tool_service import ToolService


def get_llm_gateway() -> LLMGateway:
    # mock 始终注册：没 API Key 也能测 Chat / 工具循环。
    # Agent.provider 填 "mock" 时 Gateway 才能找到，否则是 Unsupported provider。
    providers = {"mock": MockLLMProvider()}

    if settings.QWEN_API_KEY and settings.QWEN_BASE_URL:
        providers["qwen"] = QwenProvider(settings.QWEN_API_KEY, settings.QWEN_BASE_URL)

    if settings.OPENAI_API_KEY:
        providers["openai"] = OpenAIProvider(settings.OPENAI_API_KEY)

    if settings.ANTHROPIC_API_KEY:
        providers["anthropic"] = AnthropicProvider(settings.ANTHROPIC_API_KEY)

    return LLMGateway(providers=providers)


LLMGatewayDep = Annotated[LLMGateway, Depends(get_llm_gateway)]

DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_prompt_repository() -> PromptRepository:
    return PromptRepository()


PromptRepositoryDep = Annotated[PromptRepository, Depends(get_prompt_repository)]


async def get_prompt_manager(
    repository: PromptRepositoryDep,
) -> PromptManager:
    return PromptManager(repository=repository)


PromptManagerDep = Annotated[PromptManager, Depends(get_prompt_manager)]


async def get_conversation_message_repository() -> ConversationMessageRepository:

    return ConversationMessageRepository()


ConversationMessageRepositoryDep = Annotated[
    ConversationMessageRepository, Depends(get_conversation_message_repository)
]


async def get_memory_manager(
    repository: ConversationMessageRepositoryDep,
) -> MemoryManager:

    return MemoryManager(repository=repository)


MemoryManagerDep = Annotated[MemoryManager, Depends(get_memory_manager)]


def get_tool_manager(request: Request, names: list[str] | None) -> ToolManager:
    """None names = all available. Empty list = no tools."""
    mcp_tools = [
        tool
        for tool in getattr(request.app.state, "mcp_tools", []) or []
        if isinstance(tool, BaseTool)
    ]
    available: dict[str, BaseTool] = {
        tool.name: tool for tool in [*BUILTIN_TOOLS, *mcp_tools]
    }
    manager = ToolManager()
    if names is None:
        for tool in available.values():
            manager.register(tool)
    else:
        for name in names:
            tool = available.get(name)
            if tool is not None:
                manager.register(tool)
    return manager


# 根据路径参数agent_id或者run_id获取agent_id，找不到则返回none
async def agent_id_for_tools(
    request: Request,
    db: AsyncSession,
    conversations: ConversationRepository | None = None,
) -> int | None:
    """Chat has agent_id; HITL resume only has run_id (= conversation_id)."""
    raw_agent = request.path_params.get("agent_id")
    if raw_agent is not None:
        return int(raw_agent)
    raw_run = request.path_params.get("run_id")
    if raw_run is None:
        return None
    repo = conversations or ConversationRepository()
    conversation = await repo.get_by_id(db, int(raw_run))
    if conversation is None:
        return None
    return conversation.agent_id


def get_checkpointer(request: Request) -> BaseCheckpointSaver | None:
    return getattr(request.app.state, "checkpointer", None)


CheckpointerDep = Annotated[BaseCheckpointSaver | None, Depends(get_checkpointer)]


def _knowledge_retriever() -> KnowledgeRetriever:
    return KnowledgeRetriever(store=get_chunk_store(), reranker=get_reranker())


async def get_agent_executor(
    request: Request,
    db: DbSession,
    llm_gateway: LLMGatewayDep,
    prompt_manager: PromptManagerDep,
    memory_manager: MemoryManagerDep,
    checkpointer: CheckpointerDep,
) -> AgentExecutor:
    names: list[str] | None = None
    agent_id = await agent_id_for_tools(request, db)
    if agent_id is not None:
        names = await ToolService(
            ToolRepository(), AgentRepository()
        ).selected_names_for_agent(db, agent_id)

    return AgentExecutor(
        llm_gateway=llm_gateway,
        prompt_manager=prompt_manager,
        memory_manager=memory_manager,
        tool_manager=get_tool_manager(request, names),
        checkpointer=checkpointer,
        knowledge_retriever=_knowledge_retriever(),
    )


AgentExecutorDep = Annotated[AgentExecutor, Depends(get_agent_executor)]
