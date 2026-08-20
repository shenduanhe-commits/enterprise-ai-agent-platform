from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.repositories.conversation_repository import ConversationRepository
from app.schemas.conversation import ConversationCreate, ConversationResponse


class ConversationService:
    def __init__(self, repository: ConversationRepository):
        self.repository = repository

    # 创建对话
    async def create_conversation(
        self, db: AsyncSession, conversation_data: ConversationCreate
    ) -> ConversationResponse:
        conversation = await self.repository.create(db, conversation_data)
        return ConversationResponse.model_validate(conversation)

    # 获取对话
    async def get_conversation(
        self, db: AsyncSession, conversation_id: int, user_id: int
    ) -> ConversationResponse:
        conversation = await self.repository.get_by_id(
            db, conversation_id, user_id=user_id
        )
        if not conversation:
            raise NotFoundException("对话不存在")
        return ConversationResponse.model_validate(conversation)

    # 获取所有对话
    async def get_all_conversations(
        self, db: AsyncSession, user_id: int, agent_id: int | None = None
    ) -> list[ConversationResponse]:
        conversations = await self.repository.get_all(db, user_id, agent_id)
        return [
            ConversationResponse.model_validate(conversation)
            for conversation in conversations
        ]

    # 更新对话
    async def update_conversation(
        self, db: AsyncSession, conversation_id: int, conversation_name: str
    ) -> ConversationResponse:
        conversation = await self.repository.update(
            db, conversation_id, conversation_name
        )
        if not conversation:
            raise NotFoundException("对话不存在")
        return ConversationResponse.model_validate(conversation)

    # 删除对话
    async def delete_conversation(self, db: AsyncSession, conversation_id: int) -> bool:
        result = await self.repository.delete(db, conversation_id)
        if not result:
            raise NotFoundException("对话不存在")
        return result
