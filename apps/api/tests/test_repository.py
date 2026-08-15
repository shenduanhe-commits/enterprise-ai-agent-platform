import asyncio

from app.core.database import AsyncSessionLocal
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate


async def main():

    async with AsyncSessionLocal() as db:
        repo = UserRepository()

        user = await repo.create(
            db, UserCreate(email="admin@eaap.com", password_hash="test")
        )

        print(user.id)
        print(user.email)


asyncio.run(main())
