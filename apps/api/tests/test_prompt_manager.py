from types import SimpleNamespace

import pytest

from app.ai.prompts.manager import PromptManager
from app.ai.type import AIMessage
from app.core.exceptions import BusinessException


class FakeAgent:
    id = 1
    system_prompt = "You are assistant for {company}"


class FakePromptRepository:
    def __init__(self, template: str | None = None):
        self.template = template

    async def get_latest_by_agent(self, db, agent_id):
        if self.template is None:
            return None
        return SimpleNamespace(template=self.template)


@pytest.mark.asyncio
async def test_prompt_render_uses_agent_system_prompt():
    manager = PromptManager(FakePromptRepository())

    result = await manager.build(
        db=None, agent=FakeAgent(), variables={"company": "EAAP"}
    )

    assert isinstance(result, AIMessage)
    assert result.role == "system"
    assert result.content == "You are assistant for EAAP"


@pytest.mark.asyncio
async def test_prompt_prefers_latest_template():
    manager = PromptManager(FakePromptRepository(template="fixed template"))

    result = await manager.build(
        db=None, agent=FakeAgent(), variables={"company": "EAAP"}
    )

    assert result.content == "fixed template"


@pytest.mark.asyncio
async def test_prompt_missing_variable_raises():
    manager = PromptManager(FakePromptRepository())

    with pytest.raises(BusinessException, match="提示词参数"):
        await manager.build(db=None, agent=FakeAgent(), variables={"wrong": "x"})
