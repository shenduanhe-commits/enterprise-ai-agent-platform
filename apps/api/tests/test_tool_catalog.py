from types import SimpleNamespace

import pytest

from app.ai.dependencies import agent_id_for_tools, get_tool_manager
from app.ai.tools.base import BaseTool


class FakeMcpTool(BaseTool):
    name = "lookup_order"
    description = "mock"

    async def execute(self, **kwargs):
        return "ok"


def _request(mcp_tools=None, **path_params):
    return SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(mcp_tools=mcp_tools)),
        path_params=path_params,
    )


class FakeConversations:
    def __init__(self, row=None):
        self.row = row

    async def get_by_id(self, db, conversation_id, user_id=None):
        if self.row is not None and self.row.id == int(conversation_id):
            return self.row
        return None


def test_assemble_all_when_names_none():
    manager = get_tool_manager(_request([FakeMcpTool()]), None)
    names = {tool.name for tool in manager.list_tools()}
    assert names == {"calculator", "send_email", "lookup_order"}


def test_assemble_empty_binding_has_no_tools():
    manager = get_tool_manager(_request([FakeMcpTool()]), [])
    assert manager.list_tools() == []


def test_assemble_subset_skips_missing():
    manager = get_tool_manager(
        _request([FakeMcpTool()]),
        ["calculator", "lookup_order", "nope"],
    )
    assert [tool.name for tool in manager.list_tools()] == [
        "calculator",
        "lookup_order",
    ]


@pytest.mark.asyncio
async def test_agent_id_none_without_path():
    assert await agent_id_for_tools(_request(), None) is None


@pytest.mark.asyncio
async def test_agent_id_from_chat_path():
    assert await agent_id_for_tools(_request(agent_id="3"), None) == 3


@pytest.mark.asyncio
async def test_agent_id_from_run_id_uses_conversation():
    conversations = FakeConversations(SimpleNamespace(id=9, agent_id=3))
    assert (
        await agent_id_for_tools(
            _request(run_id="9"), None, conversations=conversations
        )
        == 3
    )


@pytest.mark.asyncio
async def test_agent_id_missing_when_run_unknown():
    assert (
        await agent_id_for_tools(
            _request(run_id="9"), None, conversations=FakeConversations()
        )
        is None
    )


@pytest.mark.asyncio
async def test_agent_id_prefers_path_over_run():
    conversations = FakeConversations(SimpleNamespace(id=9, agent_id=99))
    assert (
        await agent_id_for_tools(
            _request(agent_id="3", run_id="9"),
            None,
            conversations=conversations,
        )
        == 3
    )
