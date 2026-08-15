from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.type import AIMessage
from app.core.exceptions import BusinessException
from app.repositories.prompt_repository import PromptRepository


class PromptManager:
    """
    Responsible for building prompts.
    """

    def __init__(
        self,
        repository: PromptRepository,
    ):
        self.repository = repository

    async def build(
        self,
        db: AsyncSession,
        agent,
        variables: dict[str, Any] | None = None,
    ) -> AIMessage:
        """
        Build final system prompt.
        """
        prompt = await self.repository.get_latest_by_agent(db, agent.id)
        if prompt:
            return AIMessage(role="system", content=prompt.template)
        else:
            system_prompt = agent.system_prompt or ""
            if variables:
                system_prompt = self._render(system_prompt, variables)
            return AIMessage(role="system", content=system_prompt)

    def _render(self, template: str, variables: dict[str, Any]) -> str:
        try:
            return template.format(**variables)
        except Exception as e:
            raise BusinessException(f"提示词参数缺失或格式错误: {e}") from e
