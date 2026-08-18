from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.core.exceptions import NotFoundException
from app.schemas.agent import AgentCreate, AgentResponse
from app.services.agent_service import AgentService


def _agent(**overrides):
    data = {
        "id": 1,
        "name": "客服助手",
        "description": "企业客服 Agent",
        "provider": "mock",
        "model_name": "mock-model",
        "system_prompt": "你是客服专家",
        "created_by": 1,
        "created_at": datetime.now(timezone.utc),
        "status": "active",
    }
    data.update(overrides)
    return SimpleNamespace(**data)


class FakeAgentRepository:
    def __init__(self, agent=None, agents=None):
        self.agent = agent
        self.agents = agents or []
        self.create_calls = []

    async def create(self, db, agent_data, created_by):
        self.create_calls.append((db, agent_data, created_by))
        return self.agent

    async def get_by_id(self, db, agent_id, user_id):
        return self.agent

    async def get_all(self, db, user_id):
        return self.agents


@pytest.mark.asyncio
async def test_create_agent_passes_current_user_as_created_by():
    payload = AgentCreate(
        name="客服助手",
        description="企业客服 Agent",
        provider="mock",
        model_name="mock-model",
        system_prompt="你是客服专家",
    )
    repo = FakeAgentRepository(agent=_agent(created_by=7))

    result = await AgentService(repo).create_agent(None, payload, user_id=7)

    assert repo.create_calls == [(None, payload, 7)]
    assert isinstance(result, AgentResponse)
    assert result.created_by == 7
    assert result.name == "客服助手"


@pytest.mark.asyncio
async def test_get_agent_returns_owned_agent():
    repo = FakeAgentRepository(agent=_agent(id=3, created_by=2))

    result = await AgentService(repo).get_agent(None, agent_id=3, user_id=2)

    assert result.id == 3
    assert result.created_by == 2


@pytest.mark.asyncio
async def test_get_agent_raises_when_missing():
    repo = FakeAgentRepository(agent=None)

    with pytest.raises(NotFoundException, match="智能体不存在"):
        await AgentService(repo).get_agent(None, agent_id=99, user_id=1)


@pytest.mark.asyncio
async def test_get_agents_returns_current_user_list():
    repo = FakeAgentRepository(
        agents=[_agent(id=1, name="A"), _agent(id=2, name="B")],
    )

    result = await AgentService(repo).get_agents(None, user_id=1)

    assert [agent.name for agent in result] == ["A", "B"]
