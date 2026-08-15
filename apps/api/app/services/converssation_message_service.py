from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.conversation_message_repository import (
    ConversationMessageRepository,
)
from app.schemas.conversation_message import (
    ConversationMessageCreate,
    ConversationMessageResponse,
)


class ConversationMessageService:
    def __init__(self, repository: ConversationMessageRepository):
        self.repository = repository

    # 创建对话消息
    async def create_conversation_message(
        self, db: AsyncSession, conversation_message_data: ConversationMessageCreate
    ) -> ConversationMessageResponse:
        conversation_message = await self.repository.create(
            db, conversation_message_data
        )
        return ConversationMessageResponse.model_validate(conversation_message)

    # 获取最近对话消息
    async def get_recent_conversation_messages(
        self, db: AsyncSession, conversation_id: int, limit: int = 10
    ) -> list[ConversationMessageResponse]:
        conversation_messages = await self.repository.get_recent_messages(
            db, conversation_id, limit
        )
        return [
            ConversationMessageResponse.model_validate(conversation_message)
            for conversation_message in conversation_messages
        ]
