from __future__ import annotations

import json
from typing import Any

from mcp import Client
from mcp_types import CallToolResult

from app.ai.tools.base import BaseTool


class McpTool(BaseTool):
    """Wrap one MCP tool as a process-local BaseTool. execute always goes through tools/call."""

    def __init__(
        self,
        client: Client,
        *,
        name: str,
        description: str,
        input_schema: dict[str, Any],
    ):
        self.name = name
        self.description = description
        self._client = client
        self._input_schema = input_schema

    async def execute(self, **kwargs):
        try:
            result = await self._client.call_tool(self.name, kwargs)
        except Exception as exc:  # noqa: BLE001 — 远端挂了必须降级成字符串，不能炸 Runtime
            return f"mcp unavailable: {exc}"
        return format_call_result(result)

    @property
    def schema(self) -> dict:
        parameters = self._input_schema or {
            "type": "object",
            "properties": {},
            "required": [],
        }
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": parameters,
            },
        }


# 格式化MCP工具调用结果
def format_call_result(result: CallToolResult) -> str:
    if result.is_error:
        texts = _text_blocks(result)
        return texts or "mcp tool error"
    if result.structured_content is not None:
        data = result.structured_content
        if isinstance(data, str):
            return data
        return json.dumps(data, ensure_ascii=False)
    return _text_blocks(result) or ""


# 格式化MCP工具调用结果中的文本块
def _text_blocks(result: CallToolResult) -> str:
    lines: list[str] = []
    for block in result.content or []:
        text = getattr(block, "text", None)
        if text:
            lines.append(text)
    return "\n".join(lines)


# 将MCP工具调用结果中的文本块转换为字典
def schema_as_dict(value: object) -> dict[str, Any]:
    if value is None:
        return {"type": "object", "properties": {}, "required": []}
    if isinstance(value, dict):
        return value
    dump = getattr(value, "model_dump", None)
    if callable(dump):
        data = dump(by_alias=True)
        if isinstance(data, dict):
            return data
    return {"type": "object", "properties": {}, "required": []}
