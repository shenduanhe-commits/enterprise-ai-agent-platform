from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.repositories.agent_repository import AgentRepository
from app.schemas.agent import AgentCreate, AgentResponse


class AgentService:
    def __init__(self, repository: AgentRepository):
        self.repository = repository

    async def create_agent(
        self, db: AsyncSession, agent_data: AgentCreate, user_id: int
    ) -> AgentResponse:

        agent = await self.repository.create(db, agent_data, created_by=user_id)

        return AgentResponse.model_validate(agent)

    async def get_agent(
        self, db: AsyncSession, agent_id: int, user_id: int
    ) -> AgentResponse:

        agent = await self.repository.get_by_id(db, agent_id, user_id)

        if not agent:
            raise NotFoundException("智能体不存在")

        return AgentResponse.model_validate(agent)

    async def get_agents(self, db: AsyncSession, user_id: int) -> list[AgentResponse]:

        agents = await self.repository.get_all(db, user_id)

        return [AgentResponse.model_validate(agent) for agent in agents]
