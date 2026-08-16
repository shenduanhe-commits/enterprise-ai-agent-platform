import asyncio

from app.core.database import AsyncSessionLocal
from app.repositories.agent_repository import AgentRepository
from app.schemas.agent import AgentCreate
from app.services.agent_service import AgentService


async def main():

    async with AsyncSessionLocal() as db:
        service = AgentService(AgentRepository())

        agent = await service.create_agent(
            db,
            AgentCreate(
                name="客服助手",
                description="企业客服 Agent",
                provider="mock",
                model_name="gpt-5",
                system_prompt="你是客服专家",
            ),
            user_id=1,
        )

        print(agent)


asyncio.run(main())
