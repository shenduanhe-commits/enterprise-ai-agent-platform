from types import SimpleNamespace

import pytest

from app.ai.llm.gateway import LLMGateway
from app.ai.llm.providers.base import BaseLLMProvider
from app.ai.llm.providers.mock import MockLLMProvider
from app.ai.runtime.agent_executor import AgentExecutor
from app.ai.runtime.agent_graph import run_graph, stream_graph
from app.ai.tools.builtin.calculator import CalculatorTool
from app.ai.tools.manager import ToolManager
from app.ai.type import AIMessage
from app.core.exceptions import AgentRuntimeException


def _tools() -> ToolManager:
    tools = ToolManager()
    tools.register(CalculatorTool())
    return tools


def _agent():
    return SimpleNamespace(provider="mock", model_name="mock-model")


async def _run(provider, user_message: str) -> AIMessage:
    return await run_graph(
        LLMGateway({"mock": provider}),
        _tools(),
        _agent(),
        [AIMessage(role="user", content=user_message)],
    )


class AlwaysToolLLMProvider(BaseLLMProvider):
    async def chat(
        self,
        model: str,
        messages: list[AIMessage],
        tools: list[dict] | None = None,
    ) -> AIMessage:
        return AIMessage(
            role="assistant",
            tool_calls=[
                {
                    "id": "call_loop",
                    "function": {
                        "name": "calculator",
                        "arguments": '{"expression": "1+1"}',
                    },
                }
            ],
        )


class ScriptedLLMProvider(BaseLLMProvider):
    def __init__(self, responses: list[AIMessage]):
        self.responses = list(responses)
        self.index = 0

    async def chat(
        self,
        model: str,
        messages: list[AIMessage],
        tools: list[dict] | None = None,
    ) -> AIMessage:
        response = self.responses[min(self.index, len(self.responses) - 1)]
        self.index += 1
        return response


@pytest.mark.asyncio
async def test_run_graph_returns_text_without_tools():
    result = await _run(MockLLMProvider(), "你好")

    assert "Mock AI Response" in (result.content or "")
    assert not result.tool_calls


@pytest.mark.asyncio
async def test_run_graph_executes_calculator():
    result = await _run(MockLLMProvider(), "12*7+5 等于多少")

    assert result.content == "计算结果是 89"


@pytest.mark.asyncio
async def test_run_graph_unknown_tool_does_not_crash():
    result = await _run(
        ScriptedLLMProvider(
            [
                AIMessage(
                    role="assistant",
                    tool_calls=[
                        {
                            "id": "call_1",
                            "function": {
                                "name": "not_a_real_tool",
                                "arguments": "{}",
                            },
                        }
                    ],
                ),
                AIMessage(role="assistant", content="tool was missing"),
            ]
        ),
        "do something",
    )

    assert result.content == "tool was missing"


@pytest.mark.asyncio
async def test_run_graph_exceeds_max_iterations():
    with pytest.raises(AgentRuntimeException, match="max iterations"):
        await _run(AlwaysToolLLMProvider(), "loop")


@pytest.mark.asyncio
async def test_execute_uses_graph_not_loop():
    executor = AgentExecutor(
        llm_gateway=LLMGateway({"mock": MockLLMProvider()}),
        prompt_manager=None,
        memory_manager=None,
        tool_manager=_tools(),
    )

    async def fake_build(db, agent, conversation, user_message, variables):
        return [AIMessage(role="user", content=user_message)]

    saved: dict = {}

    async def fake_save(db, conversation_id, user_message, assistant_message):
        saved["content"] = assistant_message
        return SimpleNamespace(created_at=None)

    async def loop_should_not_run(*args, **kwargs):
        raise AssertionError("非流式 /chat 不应再走 run_loop")

    executor._build_messages = fake_build
    executor.memory_manager = SimpleNamespace(create_message=fake_save)
    executor.run_loop = loop_should_not_run

    result = await executor.execute(
        db=None,
        agent=_agent(),
        conversation=SimpleNamespace(id=1),
        user_message="12*7+5 等于多少",
    )

    assert result.content == "计算结果是 89"
    assert saved["content"] == "计算结果是 89"


async def _collect_graph_stream(user_message: str):
    events: list[tuple[str, dict]] = []
    async for event in stream_graph(
        LLMGateway({"mock": MockLLMProvider()}),
        _tools(),
        _agent(),
        [AIMessage(role="user", content=user_message)],
    ):
        events.append(event)
    return events


@pytest.mark.asyncio
async def test_stream_graph_chunks_plain_text():
    events = await _collect_graph_stream("你好")
    tokens = [data["text"] for event, data in events if event == "token"]

    assert all(event == "token" for event, _ in events)
    assert len(tokens) > 1
    assert "Mock AI Response" in "".join(tokens)


@pytest.mark.asyncio
async def test_stream_graph_emits_tool_then_tokens():
    events = await _collect_graph_stream("12*7+5 等于多少")
    kinds = [event for event, _ in events]

    assert kinds[:2] == ["tool", "tool"]
    assert events[0][1] == {
        "id": "call_calculator_1",
        "name": "calculator",
        "status": "start",
    }
    assert events[1][1]["status"] == "result"
    assert events[1][1]["content"] == "89"
    assert "".join(data["text"] for event, data in events if event == "token") == (
        "计算结果是 89"
    )


@pytest.mark.asyncio
async def test_execute_stream_uses_graph_not_loop():
    executor = AgentExecutor(
        llm_gateway=LLMGateway({"mock": MockLLMProvider()}),
        prompt_manager=None,
        memory_manager=None,
        tool_manager=_tools(),
    )

    async def fake_build(db, agent, conversation, user_message, variables):
        return [AIMessage(role="user", content=user_message)]

    saved: dict = {}

    async def fake_save(db, conversation_id, user_message, assistant_message):
        saved["content"] = assistant_message
        return SimpleNamespace(created_at=None)

    async def loop_should_not_run(*args, **kwargs):
        raise AssertionError("SSE /chat/stream 不应再走 stream_loop")
        yield

    executor._build_messages = fake_build
    executor.memory_manager = SimpleNamespace(create_message=fake_save)
    executor.stream_loop = loop_should_not_run

    events: list[tuple[str, dict]] = []
    async for event in executor.execute_stream(
        db=None,
        agent=_agent(),
        conversation=SimpleNamespace(id=1),
        user_message="你好",
    ):
        events.append(event)

    assert events[-1] == ("done", {"conversation_id": 1})
    assert "Mock AI Response" in saved["content"]
