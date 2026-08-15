from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.repositories.agent_repository import AgentRepository
from app.schemas.agent import AgentCreate, AgentResponse


class AgentService:
    def __init__(self, repository: AgentRepository):
        self.repository = repository

    async def create_agent(
        self, db: AsyncSession, agent_data: AgentCreate
    ) -> AgentResponse:

        agent = await self.repository.create(db, agent_data)

        return AgentResponse.model_validate(agent)

    async def get_agent(self, db: AsyncSession, agent_id: int) -> AgentResponse:

        agent = await self.repository.get_by_id(db, agent_id)

        if not agent:
            raise NotFoundException("智能体不存在")

        return AgentResponse.model_validate(agent)

    async def get_agents(self, db: AsyncSession) -> list[AgentResponse]:

        agents = await self.repository.get_all(db)

        return [AgentResponse.model_validate(agent) for agent in agents]
