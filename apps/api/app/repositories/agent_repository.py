from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.schemas.agent import AgentCreate


class AgentRepository:
    async def create(self, db: AsyncSession, agent_data: AgentCreate) -> Agent:

        agent = Agent(
            name=agent_data.name,
            description=agent_data.description,
            provider=agent_data.provider,
            model_name=agent_data.model_name,
            system_prompt=agent_data.system_prompt,
            created_by=agent_data.created_by,
        )

        db.add(agent)

        await db.commit()

        await db.refresh(agent)

        return agent

    async def get_by_id(self, db: AsyncSession, agent_id: int) -> Agent | None:

        result = await db.execute(select(Agent).where(Agent.id == agent_id))

        return result.scalar_one_or_none()

    async def get_all(self, db: AsyncSession) -> list[Agent]:

        result = await db.execute(select(Agent))

        return result.scalars().all()
