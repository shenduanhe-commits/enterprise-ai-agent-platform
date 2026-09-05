import logging
from collections.abc import AsyncIterator
from datetime import datetime

from langgraph.checkpoint.base import BaseCheckpointSaver
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.knowledge.retriever import (
    KnowledgeRetriever,
    format_knowledge_message,
)
from app.ai.llm.gateway import LLMGateway
from app.ai.memory.manager import MemoryManager
from app.ai.prompts.manager import PromptManager
from app.ai.runtime.agent_graph import AgentGraph, iter_token_chunks
from app.ai.runtime.supervisor import SupervisorGraph, wants_supervisor
from app.ai.structured import parse_final_answer
from app.ai.tools.manager import ToolManager
from app.ai.tools.parser import parse_tool_call_arguments
from app.ai.type import AIMessage
from app.core.exceptions import AgentRuntimeException
from app.repositories.run_span_repository import RunSpanRepository
from app.schemas import AgentResponse
from app.schemas.chat import ChatResponse, Citation
from app.schemas.conversation import ConversationResponse
from app.schemas.conversation_message import ConversationMessageResponse
from app.schemas.run import RunSpanCreate
from app.services.run_span_service import RunSpanService

logger = logging.getLogger(__name__)


class AgentExecutor:
    def __init__(
        self,
        llm_gateway: LLMGateway,
        prompt_manager: PromptManager,
        memory_manager: MemoryManager,
        tool_manager: ToolManager,
        checkpointer: BaseCheckpointSaver | None = None,
        span_service: RunSpanService | None = None,
        knowledge_retriever: KnowledgeRetriever | None = None,
    ):

        self.llm_gateway = llm_gateway
        self.prompt_manager = prompt_manager
        self.memory_manager = memory_manager
        self.tool_manager = tool_manager
        self.checkpointer = checkpointer
        self.span_service = span_service or RunSpanService(RunSpanRepository())
        self.knowledge_retriever = knowledge_retriever
        self._citations: list[Citation] = []

    def _graph(
        self,
        agent: AgentResponse,
        *,
        db: AsyncSession | None = None,
        conversation_id: int | None = None,
    ) -> AgentGraph:
        recorder = None
        if db is not None and conversation_id is not None:
            recorder = self._span_recorder(db, conversation_id)
        return AgentGraph(
            self.llm_gateway,
            self.tool_manager,
            agent,
            checkpointer=self.checkpointer,
            span_recorder=recorder,
            conversation_id=conversation_id,
        )

    def _supervisor(
        self,
        agent: AgentResponse,
        conversation: ConversationResponse,
        *,
        db: AsyncSession | None = None,
    ) -> SupervisorGraph:
        recorder = None
        if db is not None:
            recorder = self._span_recorder(db, conversation.id)
        return SupervisorGraph(
            self.llm_gateway,
            agent,
            knowledge_retriever=self.knowledge_retriever,
            user_id=conversation.user_id,
            agent_id=agent.id,
            span_recorder=recorder,
        )

    def _span_recorder(self, db: AsyncSession, conversation_id: int):
        async def record(
            *,
            node: str,
            started_at: datetime,
            duration_ms: int,
            tool_name: str | None,
            status: str,
            error: str | None,
        ) -> None:
            await self.span_service.create_span(
                db,
                RunSpanCreate(
                    conversation_id=conversation_id,
                    node=node,
                    started_at=started_at,
                    duration_ms=duration_ms,
                    tool_name=tool_name,
                    status=status,
                    error=error,
                ),
            )

        return record

    # 非流式 /chat 走这里
    async def execute(
        self,
        db: AsyncSession,
        agent: AgentResponse,
        conversation: ConversationResponse,
        user_message: str,
        variables: dict | None = None,
    ) -> ChatResponse:

        if wants_supervisor(user_message):
            team = self._supervisor(agent, conversation, db=db)
            outcome = await team.run(user_message)
            self._citations = team.citations
            if outcome.status == "failed":
                content = outcome.message.content if outcome.message else None
                return self._chat_response(
                    conversation.id,
                    content=content,
                    status="failed",
                    agents=outcome.agents,
                )
            content = outcome.message.content if outcome.message else None
            message = await self.memory_manager.create_message(
                db,
                conversation_id=conversation.id,
                user_message=user_message,
                assistant_message=content or "",
            )
            return self._chat_response(
                conversation.id,
                content=content,
                created_at=message.created_at,
                agents=outcome.agents,
            )

        messages = await self._build_messages(
            db, agent, conversation, user_message, variables
        )

        outcome = await self._graph(
            agent, db=db, conversation_id=conversation.id
        ).run(
            messages, thread_id=str(conversation.id)
        )
        if outcome.status == "interrupted":
            await self.memory_manager.create_user_message(
                db, conversation.id, user_message
            )
            return self._chat_response(
                conversation.id,
                status="interrupted",
                pending=outcome.pending,
            )

        content = outcome.message.content if outcome.message else None
        message: ConversationMessageResponse = await self.memory_manager.create_message(
            db,
            conversation_id=conversation.id,
            user_message=user_message,
            assistant_message=content or "",
        )
        return self._chat_response(
            conversation.id,
            content=content,
            created_at=message.created_at,
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
        if wants_supervisor(user_message):
            team = self._supervisor(agent, conversation, db=db)
            token_parts: list[str] = []
            failed: str | None = None
            async for event, data in team.stream(user_message):
                if event == "token":
                    token_parts.append(data["text"])
                if event == "error":
                    failed = data.get("message")
                yield event, data
            self._citations = team.citations
            if failed is not None:
                yield "done", self._chat_payload(
                    self._chat_response(
                        conversation.id,
                        content=failed,
                        status="failed",
                        agents=team.agents,
                    )
                )
                return
            content = "".join(token_parts) or None
            message = await self.memory_manager.create_message(
                db,
                conversation_id=conversation.id,
                user_message=user_message,
                assistant_message=content or "",
            )
            yield "done", self._chat_payload(
                self._chat_response(
                    conversation.id,
                    content=content,
                    created_at=message.created_at,
                    agents=team.agents,
                )
            )
            return

        messages = await self._build_messages(
            db, agent, conversation, user_message, variables
        )

        token_parts: list[str] = []
        interrupted: dict | None = None
        async for event, data in self._graph(
            agent, db=db, conversation_id=conversation.id
        ).stream(
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
            yield "done", self._chat_payload(
                self._chat_response(
                    conversation.id,
                    status="interrupted",
                    pending=interrupted,
                )
            )
            return

        content = "".join(token_parts) or None
        message = await self.memory_manager.create_message(
            db,
            conversation_id=conversation.id,
            user_message=user_message,
            assistant_message=content or "",
        )
        yield "done", self._chat_payload(
            self._chat_response(
                conversation.id,
                content=content,
                created_at=message.created_at,
            )
        )

    async def resume(
        self,
        db: AsyncSession,
        agent: AgentResponse,
        conversation: ConversationResponse,
        decisions: list[dict],
    ) -> ChatResponse:
        self._citations = []
        outcome = await self._graph(
            agent, db=db, conversation_id=conversation.id
        ).resume(str(conversation.id), decisions)
        if outcome.status == "interrupted":
            return self._chat_response(
                conversation.id,
                status="interrupted",
                pending=outcome.pending,
            )
        content = outcome.message.content if outcome.message else None
        message = await self.memory_manager.create_assistant_message(
            db, conversation.id, content or ""
        )
        return self._chat_response(
            conversation.id,
            content=content,
            created_at=message.created_at,
        )

    def _chat_response(
        self,
        conversation_id: int,
        *,
        content: str | None = None,
        status: str = "completed",
        pending: dict | None = None,
        created_at=None,
        citations: list[Citation] | None = None,
        agents: list[str] | None = None,
    ) -> ChatResponse:
        names = list(agents or [])
        return ChatResponse(
            conversation_id=conversation_id,
            role="assistant",
            content=content,
            created_at=created_at,
            status=status,
            pending=pending,
            citations=citations if citations is not None else list(self._citations),
            agent_name=names[-1] if names else None,
            agents=names,
        )

    def _chat_payload(self, response: ChatResponse) -> dict:
        return response.model_dump(mode="json")

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
        self._citations = []
        system_message = await self.prompt_manager.build(
            db, agent=agent, variables=variables
        )
        memory = await self.memory_manager.get_recent_messages(
            db,
            conversation_id=conversation.id,
            limit=10,
        )
        hits = await self._retrieve_hits(user_message, conversation, agent)
        self._citations = [
            Citation(
                document_id=hit.document_id,
                title=hit.source,
                chunk_id=hit.chunk_id,
            )
            for hit in hits
        ]
        messages = [system_message, *memory]
        if hits:
            messages.append(
                AIMessage(role="system", content=format_knowledge_message(hits))
            )
        messages.append(AIMessage(role="user", content=user_message))
        return messages

    async def _retrieve_hits(
        self,
        user_message: str,
        conversation: ConversationResponse,
        agent: AgentResponse,
    ):
        if self.knowledge_retriever is None:
            return []
        try:
            return await self.knowledge_retriever.retrieve(
                user_message,
                user_id=conversation.user_id,
                agent_id=agent.id,
            )
        except Exception:
            logger.exception("knowledge retrieve failed")
            return []

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
                parsed = parse_final_answer(response.content)
                for chunk in iter_token_chunks(parsed.answer):
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
