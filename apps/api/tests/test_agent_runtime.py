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
async def test_run_loop_exceeds_max_iterations():
    with pytest.raises(AgentRuntimeException, match="max iterations"):
        await _executor(AlwaysToolLLMProvider()).run_loop(
            _agent(),
            [AIMessage(role="user", content="loop")],
        )
