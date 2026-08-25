import operator
from collections.abc import AsyncIterator
from typing import Annotated, Any

from langgraph.config import get_stream_writer
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from app.ai.llm.gateway import LLMGateway
from app.ai.tools.manager import ToolManager
from app.ai.tools.parser import parse_tool_call_arguments
from app.ai.type import AIMessage
from app.core.exceptions import AgentRuntimeException

_MAX_ITERATIONS = 5
_TOKEN_CHUNK_SIZE = 8


def iter_token_chunks(text: str, size: int = _TOKEN_CHUNK_SIZE) -> list[str]:
    if not text:
        return []
    return [text[i : i + size] for i in range(0, len(text), size)]


class AgentGraphState(TypedDict):
    messages: Annotated[list[AIMessage], operator.add]
    iteration: int


class AgentGraph:
    """手写 StateGraph，行为对齐 run_loop。/chat 与 /chat/stream 都走这里。"""

    def __init__(
        self,
        llm_gateway: LLMGateway,
        tool_manager: ToolManager,
        agent: Any,
    ):
        self.llm_gateway = llm_gateway
        self.tool_manager = tool_manager
        self.agent = agent
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
        return builder.compile()

    # 非流式 /chat 走这里
    async def run(self, messages: list[AIMessage]) -> AIMessage:
        final = await self._graph.ainvoke(
            {"messages": messages, "iteration": 0},
        )
        last = final["messages"][-1]
        return AIMessage(role="assistant", content=last.content)

    # 流式 /chat/stream 走这里
    async def stream(
        self, messages: list[AIMessage]
    ) -> AsyncIterator[tuple[str, dict]]:
        async for event in self._graph.astream(
            {"messages": messages, "iteration": 0},
            stream_mode="custom",
        ):
            yield event

    # 调用模型
    async def _call_model(self, state: AgentGraphState) -> dict:
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
            writer = get_stream_writer()
            for chunk in iter_token_chunks(response.content or ""):
                writer(("token", {"text": chunk}))
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
        writer = get_stream_writer()
        tool_results: list[AIMessage] = []
        for call in last.tool_calls or []:
            name = call["function"]["name"]
            call_id = call["id"]
            writer(("tool", {"id": call_id, "name": name, "status": "start"}))
            result = await self._execute_one_tool(call)
            tool_results.append(result)
            writer(
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


# 非流式 /chat 走这里
async def run_graph(
    llm_gateway: LLMGateway,
    tool_manager: ToolManager,
    agent: Any,
    messages: list[AIMessage],
) -> AIMessage:
    return await AgentGraph(llm_gateway, tool_manager, agent).run(messages)


# 流式 /chat/stream 走这里
async def stream_graph(
    llm_gateway: LLMGateway,
    tool_manager: ToolManager,
    agent: Any,
    messages: list[AIMessage],
) -> AsyncIterator[tuple[str, dict]]:
    async for event in AgentGraph(llm_gateway, tool_manager, agent).stream(messages):
        yield event
