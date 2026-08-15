import asyncio

from app.core.database import AsyncSessionLocal
from app.models.user import User
from sqlalchemy import select


async def main():

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User))

        user = result.scalars().first()

        print(user.email)

        print(user.agents)


asyncio.run(main())
