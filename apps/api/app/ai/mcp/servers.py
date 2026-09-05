from __future__ import annotations

from typing import Any

from app.ai.mcp.local_mcp_server.orders import create_order_server

# MCP 是否启用
MCP_ENABLED = True
# MCP 超时时间
MCP_TIMEOUT = 10.0

# 加服务：丢进对应 list，带 kind。启动时三类会拼成一张表再连 Client。
HTTP_SERVERS: list[dict[str, Any]] = [
    # {
    #     "kind": "http",
    #     "name": "crm",
    #     "url": "http://localhost:3100/mcp",
    #     "headers": {"Authorization": "Bearer change-me"},  # 可省略
    # },
]

STDIO_SERVERS: list[dict[str, Any]] = [
    # {
    #     "kind": "stdio",
    #     "name": "orders-stdio",
    #     "command": sys.executable,
    #     "args": ["-m", "app.ai.mcp.local_mcp_server.orders"],
    #     "cwd": "apps/api",  # 可省略，默认 API 根目录
    # },
]

INPROCESS_SERVERS: list[dict[str, Any]] = [
    {"kind": "inprocess", "name": "orders", "factory": create_order_server},
]


def all_mcp_servers() -> list[dict[str, Any]]:
    return (
        [{**spec, "kind": spec.get("kind") or "http"} for spec in HTTP_SERVERS]
        + [{**spec, "kind": spec.get("kind") or "stdio"} for spec in STDIO_SERVERS]
        + [
            {**spec, "kind": spec.get("kind") or "inprocess"}
            for spec in INPROCESS_SERVERS
        ]
    )
