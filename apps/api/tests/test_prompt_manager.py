import pytest
from app.ai.prompts.manager import PromptManager


class FakeAgent:
    system_prompt = "You are assistant for {company}"


@pytest.mark.asyncio
async def test_prompt_render():

    manager = PromptManager()

    result = await manager.build(agent=FakeAgent(), variables={"company": "EAAP"})

    assert result == ("You are assistant for EAAP")
