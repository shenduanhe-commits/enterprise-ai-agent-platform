import logging
import operator
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Annotated, Any

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.config import get_stream_writer
from langgraph.errors import GraphBubbleUp
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from typing_extensions import TypedDict

from app.ai.llm.gateway import LLMGateway
from app.ai.structured import parse_final_answer
from app.ai.tools.manager import ToolManager
from app.ai.tools.parser import parse_tool_call_arguments
from app.ai.type import AIMessage
from app.core.exceptions import AgentRuntimeException, BusinessException

logger = logging.getLogger(__name__)

SpanRecorder = Callable[..., Awaitable[None]]

_MAX_ITERATIONS = 5
_TOKEN_CHUNK_SIZE = 8


def iter_token_chunks(text: str, size: int = _TOKEN_CHUNK_SIZE) -> list[str]:
    if not text:
        return []
    return [text[i : i + size] for i in range(0, len(text), size)]


def _emit(payload: tuple) -> None:
    try:
        get_stream_writer()(payload)
    except RuntimeError:
        pass


class AgentGraphState(TypedDict):
    messages: Annotated[list[AIMessage], operator.add]
    iteration: int


@dataclass
class GraphRunResult:
    status: str
    message: AIMessage | None = None
    pending: dict | None = None


class AgentGraph:
    """手写 StateGraph。对话 Memory 在库里；图状态（含工具消息）在 checkpointer。"""

    def __init__(
        self,
        llm_gateway: LLMGateway,
        tool_manager: ToolManager,
        agent: Any,
        checkpointer: BaseCheckpointSaver | None = None,
        span_recorder: SpanRecorder | None = None,
        conversation_id: int | None = None,
    ):
        self.llm_gateway = llm_gateway
        self.tool_manager = tool_manager
        self.agent = agent
        self._checkpointer = checkpointer
        self._span_recorder = span_recorder
        self._conversation_id = conversation_id
        self._graph = self._build()

    # 构建 StateGraph
    def _build(self):
        builder = StateGraph(AgentGraphState)
        builder.add_node("call_model", self._call_model)
        builder.add_node("execute_tools", self._execute_tools)
        builder.add_edge(START, "call_model")
        builder.add_conditional_edges(
            "call_model",
            self._route,
            {
                "execute_tools": "execute_tools",
                END: END,
            },
        )
        builder.add_edge("execute_tools", "call_model")
        return builder.compile(checkpointer=self._checkpointer)

    def _config(self, thread_id: str | None) -> dict | None:
        if self._checkpointer is None or thread_id is None:
            return None
        return {"configurable": {"thread_id": str(thread_id)}}

    async def _input_for_turn(
        self, messages: list[AIMessage], config: dict | None
    ) -> dict:
        if config is None:
            return {"messages": messages, "iteration": 0}
        snapshot = await self._graph.aget_state(config)
        if snapshot.values and snapshot.values.get("messages"):
            # checkpoint 里已有历史，只追加本轮 user，避免和 Memory 拼重复。
            return {"messages": [messages[-1]], "iteration": 0}
        return {"messages": messages, "iteration": 0}

    async def _reject_if_paused(self, config: dict | None) -> None:
        if config is None:
            return
        snapshot = await self._graph.aget_state(config)
        if snapshot.next:
            raise BusinessException("有待审批的工具调用，请先批准或拒绝")

    # 非流式 /chat 走这里
    async def run(
        self, messages: list[AIMessage], thread_id: str | None = None
    ) -> GraphRunResult:
        config = self._config(thread_id)
        await self._reject_if_paused(config)
        payload = await self._input_for_turn(messages, config)
        final = await self._graph.ainvoke(payload, config)
        return self._result_from_output(final)

    async def resume(self, thread_id: str, decisions: list[dict]) -> GraphRunResult:
        config = self._config(thread_id)
        if config is None:
            raise AgentRuntimeException("resume 需要 checkpointer")
        snapshot = await self._graph.aget_state(config)
        if not snapshot.next:
            raise BusinessException("没有待审批的执行")
        pending = snapshot.interrupts[0].value if snapshot.interrupts else None
        mapping = self._decision_map(decisions, pending)
        final = await self._graph.ainvoke(
            Command(resume={"decisions": mapping}),
            config,
        )
        return self._result_from_output(final)

    async def get_status(self, thread_id: str) -> dict:
        config = self._config(thread_id)
        if config is None:
            return {"run_id": thread_id, "status": "idle", "pending": None}
        snapshot = await self._graph.aget_state(config)
        if snapshot.next:
            pending = None
            if snapshot.interrupts:
                pending = snapshot.interrupts[0].value
            return {
                "run_id": thread_id,
                "status": "interrupted",
                "pending": pending,
            }
        return {"run_id": thread_id, "status": "idle", "pending": None}

    def _result_from_output(self, final: dict) -> GraphRunResult:
        interrupts = final.get("__interrupt__") or []
        if interrupts:
            first = interrupts[0]
            pending = first.value if hasattr(first, "value") else first
            return GraphRunResult(status="interrupted", pending=pending)
        last = final["messages"][-1]
        return GraphRunResult(status="completed", message=last)

    # 流式 /chat/stream 走这里
    async def stream(
        self, messages: list[AIMessage], thread_id: str | None = None
    ) -> AsyncIterator[tuple[str, dict]]:
        config = self._config(thread_id)
        await self._reject_if_paused(config)
        payload = await self._input_for_turn(messages, config)
        saw_interrupt = False
        async for event in self._graph.astream(payload, config, stream_mode="custom"):
            if isinstance(event, tuple) and event and event[0] == "interrupt":
                saw_interrupt = True
            yield event
        if saw_interrupt or config is None:
            return
        snapshot = await self._graph.aget_state(config)
        if snapshot.next and snapshot.interrupts:
            pending = snapshot.interrupts[0].value
            yield ("interrupt", pending)

    @asynccontextmanager
    async def _node_span(self, node: str, tool_name: str | None = None):
        started_at = datetime.now(UTC)
        try:
            yield
        except GraphBubbleUp:
            raise
        except Exception as exc:
            await self._record_span(
                node,
                started_at,
                tool_name=tool_name,
                status="error",
                error=str(exc),
            )
            raise
        else:
            await self._record_span(
                node,
                started_at,
                tool_name=tool_name,
                status="ok",
            )

    async def _record_span(
        self,
        node: str,
        started_at: datetime,
        *,
        tool_name: str | None,
        status: str,
        error: str | None = None,
    ) -> None:
        duration_ms = max(
            0, int((datetime.now(UTC) - started_at).total_seconds() * 1000)
        )
        logger.info(
            "run_span conversation_id=%s node=%s status=%s duration_ms=%s "
            "tool_name=%s error=%s",
            self._conversation_id,
            node,
            status,
            duration_ms,
            tool_name,
            error,
        )
        if self._span_recorder is None:
            return
        try:
            await self._span_recorder(
                node=node,
                started_at=started_at,
                duration_ms=duration_ms,
                tool_name=tool_name,
                status=status,
                error=error,
            )
        except Exception:
            logger.exception("failed to persist run_span node=%s", node)

    def _tool_name_for_calls(self, calls: list[dict]) -> str | None:
        names = [
            call["function"]["name"]
            for call in calls
            if call.get("function", {}).get("name")
        ]
        if not names:
            return None
        return ",".join(names)

    # 调用模型
    async def _call_model(self, state: AgentGraphState) -> dict:
        async with self._node_span("call_model"):
            iteration = state.get("iteration", 0) + 1
            if iteration > _MAX_ITERATIONS:
                raise AgentRuntimeException("Agent execution exceeded max iterations")

            response = await self.llm_gateway.chat(
                provider=self.agent.provider,
                model=self.agent.model_name,
                messages=state["messages"],
                tools=self.tool_manager.get_schemas(),
            )
            if not response.tool_calls:
                parsed = parse_final_answer(response.content)
                response = AIMessage(role="assistant", content=parsed.answer)
                for chunk in iter_token_chunks(parsed.answer):
                    _emit(("token", {"text": chunk}))
            return {"messages": [response], "iteration": iteration}

    # 路由
    def _route(self, state: AgentGraphState):
        last = state["messages"][-1]
        if last.tool_calls:
            return "execute_tools"
        return END

    # 执行工具
    async def _execute_tools(self, state: AgentGraphState) -> dict:
        last = state["messages"][-1]
        calls = last.tool_calls or []
        async with self._node_span("execute_tools", self._tool_name_for_calls(calls)):
            return await self._run_tools(calls)

    async def _run_tools(self, calls: list[dict]) -> dict:
        pending = self._approval_payload(calls)
        approved_by_id: dict[str, bool] = {}
        if pending:
            if self._checkpointer is None:
                raise AgentRuntimeException("危险工具需要 checkpointer 才能审批")
            _emit(("interrupt", pending))
            approved_by_id = self._approved_by_id(interrupt(pending))

        tool_results: list[AIMessage] = []
        for call in calls:
            name = call["function"]["name"]
            call_id = call["id"]
            tool = self.tool_manager.get(name)
            needs_approval = bool(tool and tool.requires_approval)
            if needs_approval and not approved_by_id.get(call_id, False):
                result = AIMessage(
                    role="tool",
                    tool_call_id=call_id,
                    content="user denied",
                )
                tool_results.append(result)
                _emit(
                    (
                        "tool",
                        {
                            "id": call_id,
                            "name": name,
                            "status": "result",
                            "content": result.content,
                        },
                    )
                )
                continue

            _emit(("tool", {"id": call_id, "name": name, "status": "start"}))
            result = await self._execute_one_tool(call)
            tool_results.append(result)
            _emit(
                (
                    "tool",
                    {
                        "id": call_id,
                        "name": name,
                        "status": "result",
                        "content": result.content,
                    },
                )
            )
        return {"messages": tool_results}

    def _approval_payload(self, calls: list[dict]) -> dict | None:
        pending = []
        for call in calls:
            tool = self.tool_manager.get(call["function"]["name"])
            if not tool or not tool.requires_approval:
                continue
            arguments = call["function"].get("arguments", "{}")
            try:
                parsed = parse_tool_call_arguments(arguments)
            except Exception:
                parsed = arguments
            pending.append(
                {
                    "id": call["id"],
                    "name": tool.name,
                    "arguments": parsed,
                }
            )
        if not pending:
            return None
        return {"pending": pending}

    def _decision_map(
        self, decisions: list[dict], pending: dict | None
    ) -> dict[str, bool]:
        expected = [item["id"] for item in (pending or {}).get("pending", [])]
        mapping: dict[str, bool] = {}
        for item in decisions:
            call_id = item["id"]
            if call_id in mapping:
                raise BusinessException("同一工具调用不能重复选择")
            mapping[call_id] = bool(item["approved"])
        if set(mapping) != set(expected):
            raise BusinessException("每个待审批工具都需要选择批准或拒绝")
        return mapping

    def _approved_by_id(self, decision: Any) -> dict[str, bool]:
        if not isinstance(decision, dict):
            return {}
        raw = decision.get("decisions", decision)
        if isinstance(raw, dict):
            return {key: bool(value) for key, value in raw.items()}
        if isinstance(raw, list):
            return {item["id"]: bool(item["approved"]) for item in raw}
        return {}

    # 执行单个工具
    async def _execute_one_tool(self, call: dict) -> AIMessage:
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


async def run_graph(
    llm_gateway: LLMGateway,
    tool_manager: ToolManager,
    agent: Any,
    messages: list[AIMessage],
    thread_id: str | None = None,
    checkpointer: BaseCheckpointSaver | None = None,
) -> AIMessage:
    outcome = await AgentGraph(
        llm_gateway, tool_manager, agent, checkpointer=checkpointer
    ).run(messages, thread_id=thread_id)
    if outcome.status != "completed" or outcome.message is None:
        raise AgentRuntimeException("Agent paused for approval")
    return outcome.message


async def stream_graph(
    llm_gateway: LLMGateway,
    tool_manager: ToolManager,
    agent: Any,
    messages: list[AIMessage],
    thread_id: str | None = None,
    checkpointer: BaseCheckpointSaver | None = None,
) -> AsyncIterator[tuple[str, dict]]:
    async for event in AgentGraph(
        llm_gateway, tool_manager, agent, checkpointer=checkpointer
    ).stream(messages, thread_id=thread_id):
        yield event
