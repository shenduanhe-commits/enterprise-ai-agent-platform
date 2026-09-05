from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import AsyncExitStack, asynccontextmanager
from pathlib import Path
from typing import Any

from mcp import Client, StdioServerParameters
from mcp.client.streamable_http import streamable_http_client
from mcp.shared._httpx_utils import create_mcp_http_client

from app.ai.mcp.mcp_tool import McpTool, schema_as_dict
from app.ai.mcp.servers import MCP_TIMEOUT, all_mcp_servers
from app.ai.tools.base import BaseTool

logger = logging.getLogger(__name__)

_API_ROOT = str(Path(__file__).resolve().parents[3])


def http_headers_from_spec(spec: dict[str, Any]) -> dict[str, str]:
    raw = spec.get("headers")
    if not isinstance(raw, dict):
        return {}
    headers: dict[str, str] = {}
    for key, value in raw.items():
        if value is None or value == "":
            continue
        headers[str(key)] = str(value)
    return headers


@asynccontextmanager
async def _http_transport(url: str, headers: dict[str, str]) -> AsyncIterator[object]:
    async with create_mcp_http_client(headers=headers) as http:
        async with streamable_http_client(url, http_client=http) as streams:
            yield streams


def _client_target(spec: dict[str, Any]) -> object:
    kind = spec.get("kind")
    if kind == "http":
        url = spec["url"]
        headers = http_headers_from_spec(spec)
        if not headers:
            return url
        return _http_transport(url, headers)
    if kind == "stdio":
        return StdioServerParameters(
            command=spec["command"],
            args=list(spec.get("args") or []),
            cwd=spec.get("cwd") or _API_ROOT,
        )
    if kind == "inprocess":
        return spec["factory"]()
    raise ValueError(f"unknown MCP kind: {kind!r}")


async def create_mcp_clients(
    stack: AsyncExitStack,
    servers: list[dict[str, Any]] | None = None,
) -> list[tuple[str, Client]]:
    timeout = max(1.0, float(MCP_TIMEOUT))
    opened: list[tuple[str, Client]] = []
    for spec in servers if servers is not None else all_mcp_servers():
        name = spec.get("name") or "unnamed"
        try:
            client = await stack.enter_async_context(
                Client(_client_target(spec), read_timeout_seconds=timeout)
            )
        except Exception:
            logger.exception("MCP %s unavailable", name)
            continue
        opened.append((name, client))
    return opened


async def register_mcp_tools(clients: list[Client]) -> list[BaseTool]:
    tools: list[BaseTool] = []
    seen: set[str] = set()
    for client in clients:
        try:
            tools_result = await client.list_tools()
        except Exception:
            logger.exception("MCP tools/list failed; skip this server")
            continue
        for item in tools_result.tools:
            name = item.name
            if name in seen:
                logger.warning("skip duplicate MCP tool %s", name)
                continue
            seen.add(name)
            tools.append(
                McpTool(
                    client,
                    name=name,
                    description=item.description or name,
                    input_schema=schema_as_dict(
                        getattr(item, "input_schema", None)
                        or getattr(item, "inputSchema", None)
                    ),
                )
            )
    return tools
