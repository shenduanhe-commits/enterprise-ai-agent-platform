from abc import ABC, abstractmethod

from app.ai.type import AIMessage


class BaseLLMProvider(ABC):
    """
    Abstract interface for LLM providers.
    """

    @abstractmethod
    async def chat(
        self,
        model: str,
        messages: list[AIMessage],
        tools: list[dict] | None = None,
    ) -> AIMessage:
        """
        Execute chat completion.
        """
