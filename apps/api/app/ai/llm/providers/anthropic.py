import json

from anthropic import APIError, AsyncAnthropic

from app.ai.llm.providers.base import BaseLLMProvider
from app.ai.type import AIMessage
from app.core.exceptions import LLMException


def to_anthropic_tools(tools: list[dict] | None) -> list[dict] | None:
    if not tools:
        return None
    converted = []
    for tool in tools:
        fn = tool.get("function", tool) if isinstance(tool, dict) else tool
        converted.append(
            {
                "name": fn["name"],
                "description": fn.get("description") or "",
                "input_schema": fn.get("parameters")
                or {"type": "object", "properties": {}},
            }
        )
    return converted


def _parse_tool_arguments(raw) -> dict:
    if isinstance(raw, dict):
        return raw
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def to_anthropic_payload(messages: list[AIMessage]) -> tuple[str, list[dict]]:
    """把内部 messages 拆成 Anthropic 的 system + messages。"""
    system_parts: list[str] = []
    converted: list[dict] = []

    for msg in messages:
        if msg.role == "system":
            if msg.content:
                system_parts.append(msg.content)
            continue

        if msg.role == "tool":
            block = {
                "type": "tool_result",
                "tool_use_id": msg.tool_call_id,
                "content": msg.content or "",
            }
            if (
                converted
                and converted[-1]["role"] == "user"
                and isinstance(converted[-1]["content"], list)
                and converted[-1]["content"]
                and converted[-1]["content"][0].get("type") == "tool_result"
            ):
                converted[-1]["content"].append(block)
            else:
                converted.append({"role": "user", "content": [block]})
            continue

        if msg.role == "assistant":
            content: list[dict] = []
            if msg.content:
                content.append({"type": "text", "text": msg.content})
            for call in msg.tool_calls or []:
                content.append(
                    {
                        "type": "tool_use",
                        "id": call["id"],
                        "name": call["function"]["name"],
                        "input": _parse_tool_arguments(call["function"]["arguments"]),
                    }
                )
            converted.append(
                {
                    "role": "assistant",
                    "content": content or [{"type": "text", "text": ""}],
                }
            )
            continue

        converted.append({"role": "user", "content": msg.content or ""})

    return "\n\n".join(system_parts), converted


def parse_anthropic_content(blocks) -> AIMessage:
    texts: list[str] = []
    tool_calls: list[dict] = []

    for block in blocks:
        btype = getattr(block, "type", None)
        if btype is None and isinstance(block, dict):
            btype = block.get("type")

        if btype == "text":
            text = getattr(block, "text", None)
            if text is None and isinstance(block, dict):
                text = block.get("text")
            texts.append(text or "")
        elif btype == "tool_use":
            call_id = getattr(block, "id", None)
            name = getattr(block, "name", None)
            inp = getattr(block, "input", None)
            if isinstance(block, dict):
                call_id = call_id or block.get("id")
                name = name or block.get("name")
                inp = inp if inp is not None else block.get("input")
            tool_calls.append(
                {
                    "id": call_id,
                    "function": {
                        "name": name,
                        "arguments": json.dumps(inp or {}, ensure_ascii=False),
                    },
                }
            )

    return AIMessage(
        role="assistant",
        content="".join(texts) or None,
        tool_calls=tool_calls or None,
    )


class AnthropicProvider(BaseLLMProvider):
    def __init__(self, api_key: str):
        self.client = AsyncAnthropic(api_key=api_key)

    async def chat(
        self,
        model: str,
        messages: list[AIMessage],
        tools: list[dict] | None = None,
        response_format: dict | None = None,
    ) -> AIMessage:
        system, anth_messages = to_anthropic_payload(messages)
        _ = response_format
        kwargs: dict = {
            "model": model,
            "max_tokens": 1024,
            "messages": anth_messages,
        }
        if system:
            kwargs["system"] = system
        anth_tools = to_anthropic_tools(tools)
        if anth_tools:
            kwargs["tools"] = anth_tools

        try:
            response = await self.client.messages.create(**kwargs)
        except APIError as e:
            raise LLMException(f"Failed to chat with Anthropic: {e}") from e
        try:
            return parse_anthropic_content(response.content)
        except Exception as e:
            raise LLMException(f"Failed to parse Anthropic response: {e}") from e
