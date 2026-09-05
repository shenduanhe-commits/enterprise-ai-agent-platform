from types import SimpleNamespace

import pytest

from app.ai.tools.base import BaseTool
from app.core.exceptions import BusinessException, NotFoundException
from app.services.tool_service import ToolService


class FakeMcpTool(BaseTool):
    name = "lookup_order"
    description = "查订单"
    requires_approval = False

    async def execute(self, **kwargs):
        return "ok"

    @property
    def schema(self):
        return {"type": "function", "function": {"name": self.name}}


class FakeToolRepository:
    def __init__(self):
        self.upserts: list[dict] = []
        self.disabled_mcp: list[list[str]] = []
        self.bindings: dict[int, list[int]] = {}
        self.tools_by_id: dict[int, SimpleNamespace] = {
            1: SimpleNamespace(id=1, name="calculator", enabled=True),
            2: SimpleNamespace(id=2, name="lookup_order", enabled=True),
        }
        self.committed = False

    async def upsert(self, db, **row):
        self.upserts.append(row)

    async def disable_missing_mcp(self, db, present_names):
        self.disabled_mcp.append(present_names)

    async def list_all(self, db):
        return list(self.tools_by_id.values())

    async def list_by_ids(self, db, tool_ids):
        return [self.tools_by_id[i] for i in tool_ids if i in self.tools_by_id]

    async def agent_has_bindings(self, db, agent_id):
        return agent_id in self.bindings

    async def list_bound_enabled_names(self, db, agent_id):
        ids = self.bindings.get(agent_id, [])
        return [self.tools_by_id[i].name for i in ids if self.tools_by_id[i].enabled]

    async def replace_agent_tools(self, db, agent_id, tool_ids):
        self.bindings[agent_id] = list(tool_ids)


class FakeAgentRepository:
    def __init__(self, agent=None):
        self.agent = agent

    async def get_by_id(self, db, agent_id, user_id):
        return self.agent


class FakeDb:
    def __init__(self):
        self.commits = 0

    async def commit(self):
        self.commits += 1


@pytest.mark.asyncio
async def test_sync_catalog_upserts_builtin_and_mcp():
    tools = FakeToolRepository()
    db = FakeDb()
    count = await ToolService(tools, FakeAgentRepository()).sync_catalog(
        db, [FakeMcpTool()]
    )
    names = [row["name"] for row in tools.upserts]
    assert "calculator" in names
    assert "send_email" in names
    assert "lookup_order" in names
    assert count == 3
    assert tools.disabled_mcp == [["lookup_order"]]
    assert db.commits == 1
    calc = next(row for row in tools.upserts if row["name"] == "calculator")
    assert calc["source"] == "builtin"
    lookup = next(row for row in tools.upserts if row["name"] == "lookup_order")
    assert lookup["source"] == "mcp"
    email = next(row for row in tools.upserts if row["name"] == "send_email")
    assert email["requires_hitl"] is True


@pytest.mark.asyncio
async def test_bind_rejects_unknown_tool_and_missing_agent():
    tools = FakeToolRepository()
    service = ToolService(tools, FakeAgentRepository(agent=None))
    with pytest.raises(NotFoundException):
        await service.bind_agent_tools(
            FakeDb(), agent_id=9, user_id=1, tool_ids=[1]
        )
    service = ToolService(
        tools, FakeAgentRepository(agent=SimpleNamespace(id=1))
    )
    with pytest.raises(BusinessException):
        await service.bind_agent_tools(
            FakeDb(), agent_id=1, user_id=1, tool_ids=[1, 99]
        )


@pytest.mark.asyncio
async def test_bind_and_selected_names():
    tools = FakeToolRepository()
    db = FakeDb()
    service = ToolService(
        tools, FakeAgentRepository(agent=SimpleNamespace(id=3))
    )
    assert await service.selected_names_for_agent(db, 3) is None
    ids = await service.bind_agent_tools(
        db, agent_id=3, user_id=1, tool_ids=[1, 2, 1]
    )
    assert ids == [1, 2]
    assert await service.selected_names_for_agent(db, 3) == [
        "calculator",
        "lookup_order",
    ]
