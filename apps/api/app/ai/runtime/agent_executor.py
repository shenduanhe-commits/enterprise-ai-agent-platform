from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm.gateway import LLMGateway
from app.ai.memory.manager import MemoryManager
from app.ai.prompts.manager import PromptManager
from app.ai.tools.manager import ToolManager
from app.ai.tools.parser import parse_tool_call_arguments
from app.ai.type import AIMessage
from app.core.exceptions import AgentRuntimeException
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
    ):

        self.llm_gateway = llm_gateway
        self.prompt_manager = prompt_manager
        self.memory_manager = memory_manager
        self.tool_manager = tool_manager

    async def execute(
        self,
        db: AsyncSession,
        agent: AgentResponse,
        conversation: ConversationResponse,
        user_message: str,
        variables: dict | None = None,
    ) -> ChatResponse:

        system_message = await self.prompt_manager.build(
            db, agent=agent, variables=variables
        )

        memory = await self.memory_manager.get_recent_messages(
            db,
            conversation_id=conversation.id,
            limit=10,
        )

        messages = [
            system_message,
            *memory,
            AIMessage(role="user", content=user_message),
        ]

        result: AIMessage = await self.run_loop(
            agent,
            messages,
        )

        message: ConversationMessageResponse = await self.memory_manager.create_message(
            db,
            conversation_id=conversation.id,
            user_message=user_message,
            assistant_message=result.content,
        )

        return ChatResponse(
            conversation_id=conversation.id,
            role="assistant",
            content=result.content,
            created_at=message.created_at,
        )

    # 工具调用循环
    async def run_loop(
        self,
        agent: AgentResponse,
        messages: list[AIMessage],
    ) -> AIMessage:

        max_iterations = 5

        for _ in range(max_iterations):
            response: AIMessage = await self.llm_gateway.chat(
                provider=agent.provider,
                model=agent.model_name,
                messages=messages,
                tools=self.tool_manager.get_schemas(),
            )

            # 没有工具调用
            if not response.tool_calls:
                return response

            # 有工具调用

            messages.append(
                AIMessage(
                    role="assistant",
                    content=response.content,
                    tool_calls=response.tool_calls,
                )
            )

            tool_results = await self.execute_tools(response.tool_calls)

            messages.extend(tool_results)

        raise AgentRuntimeException("Agent execution exceeded max iterations")

    # 工具调用执行
    async def execute_tools(
        self,
        tool_calls: list[dict],
    ) -> list[AIMessage]:

        results: list[AIMessage] = []

        for call in tool_calls:
            tool = self.tool_manager.get(call["function"]["name"])

            if not tool:
                results.append(
                    AIMessage(
                        role="tool",
                        tool_call_id=call["id"],
                        content="tool not found",
                    )
                )

                continue
            arguments = parse_tool_call_arguments(call["function"]["arguments"])
            result = await tool.execute(**arguments)

            results.append(
                AIMessage(
                    role="tool",
                    tool_call_id=call["id"],
                    content=result,
                )
            )

        return results
