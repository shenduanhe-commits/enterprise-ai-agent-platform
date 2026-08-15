import asyncio

from app.core.database import AsyncSessionLocal
from app.repositories.agent_repository import AgentRepository
from app.schemas.agent import AgentCreate


async def main():

    async with AsyncSessionLocal() as db:
        repository = AgentRepository()

        agent = await repository.create(
            db,
            AgentCreate(
                name="合同审查助手",
                description="分析企业合同风险",
                model_name="gpt-5",
                system_prompt="你是一名专业合同律师",
                created_by=1,
            ),
        )

        print(agent.id)
        print(agent.name)

        agents = await repository.get_all(db)

        print(len(agents))


asyncio.run(main())
