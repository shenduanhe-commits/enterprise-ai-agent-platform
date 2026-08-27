from app.ai.llm.providers.base import BaseLLMProvider
from app.ai.type import AIMessage
from app.core.exceptions import LLMException


class LLMGateway:
    def __init__(self, providers: dict[str, BaseLLMProvider]):
        self.providers = providers

    async def chat(
        self,
        provider: str,
        model: str,
        messages: list[AIMessage],
        tools: list[dict] | None = None,
        response_format: dict | None = None,
    ) -> AIMessage:

        llm_provider = self.providers.get(provider)
        if not llm_provider:
            raise LLMException(f"Unsupported provider: {provider}")

        kwargs = {
            "model": model,
            "messages": messages,
            "tools": tools,
        }
        if response_format:
            kwargs["response_format"] = response_format
        return await llm_provider.chat(**kwargs)
