from app.ai.llm.providers.base import BaseLLMProvider
from app.ai.type import AIMessage


class MockLLMProvider(BaseLLMProvider):
    """
    Fake LLM provider for development.
    """

    async def chat(
        self,
        messages: list[AIMessage],
        tools: list[dict] | None = None,
    ) -> AIMessage:

        last_message = messages[-1]

        # return f"Mock AI Response: received '{last_message.content}'"
        return AIMessage(
            role="assistant",
            content=f"Mock AI Response: received '{last_message.content}'",
        )
