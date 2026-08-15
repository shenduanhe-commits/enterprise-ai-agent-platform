import asyncio

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.repositories.user_repository import UserRepository


async def main():

    async with AsyncSessionLocal() as db:
        repo = UserRepository()

        user = await repo.create(
            db,
            email="admin@eaap.com",
            password_hash=hash_password("plaintext1"),
        )

        print(user.id)
        print(user.email)


asyncio.run(main())
