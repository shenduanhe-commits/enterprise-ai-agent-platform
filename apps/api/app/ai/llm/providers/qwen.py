from openai import APIError, AsyncOpenAI

from app.ai.llm.providers.base import BaseLLMProvider
from app.ai.type import AIMessage
from app.core.exceptions import LLMException


class QwenProvider(BaseLLMProvider):
    def __init__(
        self,
        api_key: str,
        base_url: str,
    ):
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
        )

    async def chat(
        self,
        model: str,
        messages: list[AIMessage],
        tools: list[dict] | None = None,
    ) -> AIMessage:
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    message.model_dump(exclude_none=True) for message in messages
                ],
                tools=tools,
            )
        except APIError as e:
            raise LLMException(f"Failed to chat with Qwen: {e}") from e
        try:
            message = response.choices[0].message

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
        except Exception as e:
            raise LLMException(f"Failed to parse Qwen response: {e}") from e
