from datetime import UTC, datetime

from sqlalchemy import delete, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.schemas.conversation import ConversationCreate


class ConversationRepository:
    async def create(
        self, db: AsyncSession, conversation_data: ConversationCreate
    ) -> Conversation:
        conversation = Conversation(**conversation_data.model_dump())
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        return conversation

    async def get_by_id(
        self,
        db: AsyncSession,
        conversation_id: int,
        user_id: int | None = None,
    ) -> Conversation | None:
        query = select(Conversation).where(Conversation.id == conversation_id)
        if user_id is not None:
            query = query.where(Conversation.user_id == user_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_all(
        self, db: AsyncSession, user_id: int, agent_id: int | None = None
    ) -> list[Conversation]:
        query = select(Conversation).where(Conversation.user_id == user_id)
        if agent_id is not None:
            query = query.where(Conversation.agent_id == agent_id)
        result = await db.execute(query.order_by(desc(Conversation.updated_at)))
        return result.scalars().all()

    async def update(
        self, db: AsyncSession, conversation_id: int, conversation_name: str
    ) -> Conversation | None:
        conversation = await self.get_by_id(db, conversation_id)
        if not conversation:
            return None
        conversation.name = conversation_name
        conversation.updated_at = datetime.now(UTC)
        await db.commit()
        await db.refresh(conversation)
        return conversation

    async def delete(self, db: AsyncSession, conversation_id: int) -> bool:
        result = await db.execute(
            delete(Conversation).where(Conversation.id == conversation_id)
        )
        await db.commit()
        return result.rowcount > 0
