from openai import APIError, AsyncOpenAI

from app.ai.llm.providers.base import BaseLLMProvider
from app.ai.llm.providers.openai_compat import parse_openai_chat_message
from app.ai.type import AIMessage
from app.core.exceptions import LLMException


class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)

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
            raise LLMException(f"Failed to chat with OpenAI: {e}") from e
        try:
            return parse_openai_chat_message(response.choices[0].message)
        except Exception as e:
            raise LLMException(f"Failed to parse OpenAI response: {e}") from e
