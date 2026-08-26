from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm.gateway import LLMGateway
from app.ai.memory.manager import MemoryManager
from app.ai.prompts.manager import PromptManager
from app.ai.runtime.agent_graph import AgentGraph, iter_token_chunks
from app.ai.tools.manager import ToolManager
from app.ai.tools.parser import parse_tool_call_arguments
from app.ai.type import AIMessage
from app.core.exceptions import AgentRuntimeException
from langgraph.checkpoint.base import BaseCheckpointSaver
from app.schemas import AgentResponse
from app.schemas.chat import ChatResponse
from app.schemas.conversation import ConversationResponse
from app.schemas.conversation_message import ConversationMessageResponse


class AgentExecutor:
    def __init__(
        self,
        llm_gateway: LLMGateway,
        prompt_manager: PromptManager,
        memory_manager: MemoryManager,
        tool_manager: ToolManager,
        checkpointer: BaseCheckpointSaver | None = None,
    ):

        self.llm_gateway = llm_gateway
        self.prompt_manager = prompt_manager
        self.memory_manager = memory_manager
        self.tool_manager = tool_manager
        self.checkpointer = checkpointer

    def _graph(self, agent: AgentResponse) -> AgentGraph:
        return AgentGraph(
            self.llm_gateway,
            self.tool_manager,
            agent,
            checkpointer=self.checkpointer,
        )

    # 非流式 /chat 走这里
    async def execute(
        self,
        db: AsyncSession,
        agent: AgentResponse,
        conversation: ConversationResponse,
        user_message: str,
        variables: dict | None = None,
    ) -> ChatResponse:

        messages = await self._build_messages(
            db, agent, conversation, user_message, variables
        )

        outcome = await self._graph(agent).run(
            messages, thread_id=str(conversation.id)
        )
        if outcome.status == "interrupted":
            await self.memory_manager.create_user_message(
                db, conversation.id, user_message
            )
            return ChatResponse(
                conversation_id=conversation.id,
                role="assistant",
                content=None,
                status="interrupted",
                pending=outcome.pending,
            )

        message: ConversationMessageResponse = await self.memory_manager.create_message(
            db,
            conversation_id=conversation.id,
            user_message=user_message,
            assistant_message=outcome.message.content if outcome.message else "",
        )

        return ChatResponse(
            conversation_id=conversation.id,
            role="assistant",
            content=outcome.message.content if outcome.message else None,
            created_at=message.created_at,
            status="completed",
        )

    # SSE 走这里
    async def execute_stream(
        self,
        db: AsyncSession,
        agent: AgentResponse,
        conversation: ConversationResponse,
        user_message: str,
        variables: dict | None = None,
    ) -> AsyncIterator[tuple[str, dict]]:
        messages = await self._build_messages(
            db, agent, conversation, user_message, variables
        )

        token_parts: list[str] = []
        interrupted: dict | None = None
        async for event, data in self._graph(agent).stream(
            messages, thread_id=str(conversation.id)
        ):
            if event == "token":
                token_parts.append(data["text"])
            if event == "interrupt":
                interrupted = data
            yield event, data

        if interrupted:
            await self.memory_manager.create_user_message(
                db, conversation.id, user_message
            )
            yield "done", {
                "conversation_id": conversation.id,
                "status": "interrupted",
            }
            return

        await self.memory_manager.create_message(
            db,
            conversation_id=conversation.id,
            user_message=user_message,
            assistant_message="".join(token_parts),
        )
        yield "done", {"conversation_id": conversation.id, "status": "completed"}

    async def resume(
        self,
        db: AsyncSession,
        agent: AgentResponse,
        conversation: ConversationResponse,
        decisions: list[dict],
    ) -> ChatResponse:
        outcome = await self._graph(agent).resume(str(conversation.id), decisions)
        if outcome.status == "interrupted":
            return ChatResponse(
                conversation_id=conversation.id,
                role="assistant",
                content=None,
                status="interrupted",
                pending=outcome.pending,
            )
        content = outcome.message.content if outcome.message else ""
        message = await self.memory_manager.create_assistant_message(
            db, conversation.id, content or ""
        )
        return ChatResponse(
            conversation_id=conversation.id,
            role="assistant",
            content=content,
            created_at=message.created_at,
            status="completed",
        )

    async def get_run_status(
        self, agent: AgentResponse, conversation: ConversationResponse
    ) -> dict:
        return await self._graph(agent).get_status(str(conversation.id))

    # 构建 messages
    async def _build_messages(
        self,
        db: AsyncSession,
        agent: AgentResponse,
        conversation: ConversationResponse,
        user_message: str,
        variables: dict | None,
    ) -> list[AIMessage]:
        system_message = await self.prompt_manager.build(
            db, agent=agent, variables=variables
        )
        memory = await self.memory_manager.get_recent_messages(
            db,
            conversation_id=conversation.id,
            limit=10,
        )
        return [
            system_message,
            *memory,
            AIMessage(role="user", content=user_message),
        ]

    # 非graph 非流式 /chat 走这里
    async def run_loop(
        self,
        agent: AgentResponse,
        messages: list[AIMessage],
    ) -> AIMessage:
        parts: list[str] = []
        async for event, data in self.stream_loop(agent, messages):
            if event == "token":
                parts.append(data["text"])
        return AIMessage(role="assistant", content="".join(parts) or None)

    # 非graph SSE 走这里
    async def stream_loop(
        self,
        agent: AgentResponse,
        messages: list[AIMessage],
    ) -> AsyncIterator[tuple[str, dict]]:
        max_iterations = 5

        for _ in range(max_iterations):
            response: AIMessage = await self.llm_gateway.chat(
                provider=agent.provider,
                model=agent.model_name,
                messages=messages,
                tools=self.tool_manager.get_schemas(),
            )

            if not response.tool_calls:
                for chunk in iter_token_chunks(response.content or ""):
                    yield "token", {"text": chunk}
                return

            messages.append(
                AIMessage(
                    role="assistant",
                    content=response.content,
                    tool_calls=response.tool_calls,
                )
            )

            tool_results: list[AIMessage] = []
            for call in response.tool_calls:
                name = call["function"]["name"]
                call_id = call["id"]
                yield "tool", {"id": call_id, "name": name, "status": "start"}
                result = await self.execute_one_tool(call)
                tool_results.append(result)
                yield (
                    "tool",
                    {
                        "id": call_id,
                        "name": name,
                        "status": "result",
                        "content": result.content,
                    },
                )

            messages.extend(tool_results)

        raise AgentRuntimeException("Agent execution exceeded max iterations")

    # 工具执行函数
    async def execute_one_tool(self, call: dict) -> AIMessage:
        tool = self.tool_manager.get(call["function"]["name"])

        if not tool:
            return AIMessage(
                role="tool",
                tool_call_id=call["id"],
                content="tool not found",
            )

        arguments = parse_tool_call_arguments(call["function"]["arguments"])
        result = await tool.execute(**arguments)
        return AIMessage(
            role="tool",
            tool_call_id=call["id"],
            content=result,
        )

    # 遍历多个工具并执行
    async def execute_tools(
        self,
        tool_calls: list[dict],
    ) -> list[AIMessage]:
        return [await self.execute_one_tool(call) for call in tool_calls]
