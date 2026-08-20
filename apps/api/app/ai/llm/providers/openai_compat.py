from app.ai.type import AIMessage


def parse_openai_chat_message(message) -> AIMessage:
    """把 OpenAI 兼容 SDK 的 message 转成内部 AIMessage（含 tool_calls）。"""
    tool_calls = None
    if message.tool_calls:
        tool_calls = [
            {
                "id": call.id,
                "function": {
                    "name": call.function.name,
                    "arguments": call.function.arguments,
                },
            }
            for call in message.tool_calls
        ]

    return AIMessage(
        role=message.role,
        content=message.content,
        tool_calls=tool_calls,
    )
