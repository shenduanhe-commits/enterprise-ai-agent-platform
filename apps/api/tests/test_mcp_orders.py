from contextlib import AsyncExitStack

import pytest
from mcp import Client
from mcp.server.mcpserver import MCPServer

from app.ai.mcp.client import (
    _client_target,
    create_mcp_clients,
    http_headers_from_spec,
    register_mcp_tools,
)
from app.ai.mcp.local_mcp_server.orders import create_order_server, lookup_order
from app.ai.mcp.mcp_tool import McpTool
from app.ai.mcp.servers import all_mcp_servers
from app.ai.tools.builtin.calculator import CalculatorTool
from app.ai.tools.manager import ToolManager


def test_lookup_order_catalog():
    assert "笔记本" in lookup_order("ord-1001")
    assert "查无此单" in lookup_order("ORD-9999")


def test_all_mcp_servers_merge_kinds():
    specs = all_mcp_servers()
    assert {spec["kind"] for spec in specs} <= {"http", "stdio", "inprocess"}
    assert any(
        spec["kind"] == "inprocess" and spec["name"] == "orders" for spec in specs
    )


@pytest.mark.asyncio
async def test_inprocess_client_lists_and_calls_lookup_order():
    async with Client(create_order_server()) as client:
        tools = await register_mcp_tools([client])
        assert [tool.name for tool in tools] == ["lookup_order"]
        assert tools[0].schema["function"]["name"] == "lookup_order"
        text = await tools[0].execute(order_id="ORD-1001")
        assert "已发货" in text
        assert "笔记本" in text


@pytest.mark.asyncio
async def test_chat_manager_can_take_mcp_tools():
    manager = ToolManager()
    manager.register(CalculatorTool())
    async with Client(create_order_server()) as client:
        for tool in await register_mcp_tools([client]):
            manager.register(tool)
    assert manager.get("calculator") is not None
    assert manager.get("lookup_order") is not None


@pytest.mark.asyncio
async def test_register_degrades_when_list_fails():
    class Boom:
        async def list_tools(self):
            raise RuntimeError("server down")

    assert await register_mcp_tools([Boom()]) == []


@pytest.mark.asyncio
async def test_mcp_tool_call_degrades_on_error():
    class BoomClient:
        async def call_tool(self, name, arguments):
            raise RuntimeError("server down")

    tool = McpTool(
        BoomClient(),
        name="lookup_order",
        description="lookup",
        input_schema={"type": "object", "properties": {}},
    )
    assert (await tool.execute(order_id="ORD-1001")).startswith("mcp unavailable")


@pytest.mark.asyncio
async def test_mock_chat_uses_lookup_order_when_registered():
    from app.ai.llm.providers.mock import MockLLMProvider
    from app.ai.type import AIMessage

    async with Client(create_order_server()) as client:
        tools = await register_mcp_tools([client])
        schemas = [tool.schema for tool in tools]
        provider = MockLLMProvider()
        first = await provider.chat(
            "mock-model",
            [AIMessage(role="user", content="查一下订单 ORD-1001")],
            tools=schemas,
        )
        assert first.tool_calls
        assert first.tool_calls[0]["function"]["name"] == "lookup_order"
        result = await tools[0].execute(order_id="ORD-1001")
        second = await provider.chat(
            "mock-model",
            [
                AIMessage(role="user", content="查一下订单 ORD-1001"),
                first,
                AIMessage(
                    role="tool",
                    tool_call_id="call_lookup_order_1",
                    content=result,
                ),
            ],
            tools=schemas,
        )
        assert "笔记本" in (second.content or "")
        assert "计算结果" not in (second.content or "")


def _create_ping_server() -> MCPServer:
    server = MCPServer("eaap-ping")

    def ping(name: str) -> str:
        """Echo a ping for multi-server tests."""
        return f"pong {name}"

    server.add_tool(ping)
    return server


@pytest.mark.asyncio
async def test_register_merges_two_servers():
    async with (
        Client(create_order_server()) as orders,
        Client(_create_ping_server()) as ping,
    ):
        names = {tool.name for tool in await register_mcp_tools([orders, ping])}
    assert names == {"lookup_order", "ping"}


@pytest.mark.asyncio
async def test_register_keeps_others_when_one_list_fails():
    class Boom:
        async def list_tools(self):
            raise RuntimeError("server down")

    async with Client(create_order_server()) as orders:
        names = {tool.name for tool in await register_mcp_tools([Boom(), orders])}
    assert names == {"lookup_order"}


@pytest.mark.asyncio
async def test_register_skips_duplicate_tool_names():
    async with (
        Client(create_order_server()) as first,
        Client(create_order_server()) as second,
    ):
        tools = await register_mcp_tools([first, second])
    assert [tool.name for tool in tools] == ["lookup_order"]


@pytest.mark.asyncio
async def test_create_mcp_clients_skips_failed_server():
    def boom_factory():
        raise RuntimeError("server down")

    async with AsyncExitStack() as stack:
        pairs = await create_mcp_clients(
            stack,
            [
                {"kind": "inprocess", "name": "orders", "factory": create_order_server},
                {"kind": "inprocess", "name": "boom", "factory": boom_factory},
            ],
        )
    assert [name for name, _ in pairs] == ["orders"]


def test_http_headers_from_spec_skips_empty():
    assert http_headers_from_spec({"url": "http://x/mcp"}) == {}
    assert http_headers_from_spec({"headers": "Bearer x"}) == {}
    assert http_headers_from_spec(
        {"headers": {"Authorization": "Bearer t", "X-Empty": ""}}
    ) == {"Authorization": "Bearer t"}


def test_http_target_without_headers_is_url():
    assert _client_target({"kind": "http", "url": "http://x/mcp"}) == "http://x/mcp"


def test_http_target_with_headers_is_transport():
    target = _client_target(
        {
            "kind": "http",
            "url": "http://x/mcp",
            "headers": {"Authorization": "Bearer t"},
        }
    )
    assert target != "http://x/mcp"
    assert hasattr(target, "__aenter__")
