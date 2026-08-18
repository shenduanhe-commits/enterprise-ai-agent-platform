from types import SimpleNamespace

import pytest

from app.ai.llm.gateway import LLMGateway
from app.ai.llm.providers.base import BaseLLMProvider
from app.ai.llm.providers.mock import MockLLMProvider
from app.ai.runtime.agent_executor import AgentExecutor
from app.ai.tools.builtin.calculator import CalculatorTool
from app.ai.tools.manager import ToolManager
from app.ai.type import AIMessage
from app.core.exceptions import AgentRuntimeException


def _executor(provider) -> AgentExecutor:
    tools = ToolManager()
    tools.register(CalculatorTool())
    return AgentExecutor(
        llm_gateway=LLMGateway({"mock": provider}),
        prompt_manager=None,
        memory_manager=None,
        tool_manager=tools,
    )


def _agent():
    return SimpleNamespace(provider="mock", model_name="mock-model")


class AlwaysToolLLMProvider(BaseLLMProvider):
    """每次都返回 tool_calls，用来测超轮次。"""

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
async def test_run_loop_returns_text_without_tools():
    result = await _executor(MockLLMProvider()).run_loop(
        _agent(),
        [AIMessage(role="user", content="你好")],
    )

    assert "Mock AI Response" in (result.content or "")
    assert not result.tool_calls


@pytest.mark.asyncio
async def test_run_loop_executes_calculator():
    result = await _executor(MockLLMProvider()).run_loop(
        _agent(),
        [AIMessage(role="user", content="12*7+5 等于多少")],
    )

    assert result.content == "计算结果是 89"


@pytest.mark.asyncio
async def test_run_loop_unknown_tool_does_not_crash():
    executor = _executor(
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
        )
    )

    result = await executor.run_loop(
        _agent(),
        [AIMessage(role="user", content="do something")],
    )

    assert result.content == "tool was missing"


@pytest.mark.asyncio
async def test_run_loop_exceeds_max_iterations():
    with pytest.raises(AgentRuntimeException, match="max iterations"):
        await _executor(AlwaysToolLLMProvider()).run_loop(
            _agent(),
            [AIMessage(role="user", content="loop")],
        )


async def _collect_stream(executor: AgentExecutor, user_message: str):
    events: list[tuple[str, dict]] = []
    async for event in executor.stream_loop(
        _agent(),
        [AIMessage(role="user", content=user_message)],
    ):
        events.append(event)
    return events


@pytest.mark.asyncio
async def test_stream_loop_chunks_plain_text():
    events = await _collect_stream(_executor(MockLLMProvider()), "你好")
    tokens = [data["text"] for event, data in events if event == "token"]

    assert all(event == "token" for event, _ in events)
    assert len(tokens) > 1
    assert "Mock AI Response" in "".join(tokens)


@pytest.mark.asyncio
async def test_stream_loop_emits_tool_then_tokens():
    events = await _collect_stream(_executor(MockLLMProvider()), "12*7+5 等于多少")
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
