from anthropic import AsyncAnthropic

from app.ai.type import AIMessage

from .base import BaseLLMProvider


class AnthropicProvider(BaseLLMProvider):
    def __init__(
        self,
        api_key: str,
    ):

        self.client = AsyncAnthropic(api_key=api_key)

    async def chat(
        self,
        model: str,
        messages: list[AIMessage],
        tools=None,
    ) -> AIMessage:

        response = await self.client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[message.model_dump() for message in messages],
        )

        return AIMessage(
            role=response.content[0].type,
            content=response.content[0].text or "",
        )
