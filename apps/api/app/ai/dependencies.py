from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

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
from langgraph.checkpoint.base import BaseCheckpointSaver
from app.ai.tools.builtin.calculator import CalculatorTool
from app.ai.tools.manager import ToolManager
from app.core.config import settings
from app.core.database import get_db
from app.repositories.conversation_message_repository import (
    ConversationMessageRepository,
)
from app.repositories.prompt_repository import PromptRepository


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


def get_tool_manager() -> ToolManager:
    manager = ToolManager()
    manager.register(CalculatorTool())
    return manager


ToolManagerDep = Annotated[ToolManager, Depends(get_tool_manager)]


def get_checkpointer(request: Request) -> BaseCheckpointSaver | None:
    return getattr(request.app.state, "checkpointer", None)


CheckpointerDep = Annotated[BaseCheckpointSaver | None, Depends(get_checkpointer)]


async def get_agent_executor(
    llm_gateway: LLMGatewayDep,
    prompt_manager: PromptManagerDep,
    memory_manager: MemoryManagerDep,
    tool_manager: ToolManagerDep,
    checkpointer: CheckpointerDep,
) -> AgentExecutor:

    return AgentExecutor(
        llm_gateway=llm_gateway,
        prompt_manager=prompt_manager,
        memory_manager=memory_manager,
        tool_manager=tool_manager,
        checkpointer=checkpointer,
    )


AgentExecutorDep = Annotated[AgentExecutor, Depends(get_agent_executor)]
