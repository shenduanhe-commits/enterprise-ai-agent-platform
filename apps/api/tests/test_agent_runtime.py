import pytest
from app.ai.llm.gateway import LLMGateway
from app.ai.llm.providers.mock import MockLLMProvider
from app.ai.runtime.agent_executor import AgentExecutor


class FakeAgent:
    id = 1

    system_prompt = "You are a helpful assistant"


class FakePromptManager:
    async def build(self, agent, user_input):
        return agent.system_prompt


class FakeMemoryManager:
    async def load(self, user_id, agent_id):
        return [{"role": "user", "content": "hello"}]

    async def save(self, **kwargs):
        pass


class FakeToolRegistry:
    def get_tools(self, agent):
        return []


@pytest.mark.asyncio
async def test_agent_executor():

    executor = AgentExecutor(
        llm_gateway=LLMGateway(MockLLMProvider()),
        prompt_manager=FakePromptManager(),
        memory_manager=FakeMemoryManager(),
        tool_registry=FakeToolRegistry(),
    )

    result = await executor.execute(agent=FakeAgent(), user_input="你好")

    assert "Mock AI Response" in result["response"].content
