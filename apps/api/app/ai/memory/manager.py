from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.type import AIMessage
from app.repositories.conversation_message_repository import (
    ConversationMessageRepository,
)
from app.schemas.conversation_message import (
    ConversationMessageCreate,
    ConversationMessageResponse,
)


class MemoryManager:
    """
    Manage agent conversation memory.
    """

    def __init__(
        self,
        repository: ConversationMessageRepository,
    ):
        self.repository = repository

    async def get_recent_messages(
        self,
        db: AsyncSession,
        conversation_id: int,
        limit: int = 10,
    ) -> list[AIMessage]:
        """
        Load conversation history.
        """

        records = await self.repository.get_recent_messages(
            db=db,
            conversation_id=conversation_id,
            limit=limit,
        )

        return [
            AIMessage(
                role=item.role,
                content=item.content,
            )
            for item in records
        ]

    async def create_message(
        self,
        db: AsyncSession,
        conversation_id: int,
        user_message: str,
        assistant_message: str,
    ) -> ConversationMessageResponse:
        """
        Save conversation messages.
        """
        user_message_create = ConversationMessageCreate(
            conversation_id=conversation_id, role="user", content=user_message
        )
        assistant_message_create = ConversationMessageCreate(
            conversation_id=conversation_id, role="assistant", content=assistant_message
        )

        await self.repository.create(db, user_message_create)
        conversation_message = await self.repository.create(
            db, assistant_message_create
        )
        return ConversationMessageResponse.model_validate(conversation_message)
