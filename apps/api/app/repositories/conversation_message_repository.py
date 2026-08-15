from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation_message import (
    ConversationMessage,
)
from app.schemas.conversation_message import (
    ConversationMessageCreate,
)


class ConversationMessageRepository:
    """
    Repository for conversation messages.
    """

    async def create(
        self,
        db: AsyncSession,
        message: ConversationMessageCreate,
    ) -> ConversationMessage:

        db_message = ConversationMessage(
            role=message.role,
            content=message.content,
            conversation_id=message.conversation_id,
        )
        db.add(db_message)

        await db.commit()

        await db.refresh(db_message)

        return db_message

    async def get_recent_messages(
        self,
        db: AsyncSession,
        conversation_id: int,
        limit: int = 10,
    ) -> list[ConversationMessage]:

        stmt = (
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == conversation_id)
            .order_by(
                ConversationMessage.created_at.desc(),
                ConversationMessage.id.desc(),
            )
            .limit(limit)
        )

        result = await db.execute(stmt)
        messages = result.scalars().all()
        return list(reversed(messages))
