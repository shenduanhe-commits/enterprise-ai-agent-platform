from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prompt import Prompt


class PromptRepository:
    async def get_latest_by_agent(
        self,
        db: AsyncSession,
        agent_id: int,
    ) -> Prompt | None:

        result = await db.execute(
            select(Prompt)
            .where(Prompt.agent_id == agent_id)
            .order_by(Prompt.version.desc())
        )

        return result.scalars().first()
