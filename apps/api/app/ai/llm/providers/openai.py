from openai import AsyncOpenAI

from app.ai.type import AIMessage

from .base import BaseLLMProvider


class OpenAIProvider(BaseLLMProvider):
    def __init__(
        self,
        api_key: str,
    ):

        self.client = AsyncOpenAI(api_key=api_key)

    async def chat(
        self,
        model: str,
        messages: list[AIMessage],
        tools: list[dict] | None = None,
    ) -> AIMessage:

        response = await self.client.chat.completions.create(
            model=model,
            messages=[message.model_dump() for message in messages],
            tools=tools,
        )

        return AIMessage(
            role=response.choices[0].message.role,
            content=response.choices[0].message.content,
        )
