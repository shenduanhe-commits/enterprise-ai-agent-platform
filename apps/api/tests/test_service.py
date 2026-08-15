import asyncio

from app.core.database import AsyncSessionLocal
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate
from app.services.user_service import UserService


async def main():

    async with AsyncSessionLocal() as db:
        service = UserService(UserRepository())

        user = await service.create_user(
            db, UserCreate(email="service@eaap.com", password="plaintext1")
        )

        print(user)


asyncio.run(main())
