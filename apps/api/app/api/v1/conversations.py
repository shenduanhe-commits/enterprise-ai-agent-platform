from fastapi import APIRouter

from app.core.dependencies import CurrentUser, DbSession
from app.repositories.conversation_message_repository import (
    ConversationMessageRepository,
)
from app.repositories.conversation_repository import ConversationRepository
from app.schemas.conversation import ConversationResponse
from app.schemas.conversation_message import ConversationMessageResponse
from app.services.conversation_message_service import ConversationMessageService
from app.services.conversation_service import ConversationService

router = APIRouter(prefix="/conversations", tags=["Conversations"])

conversation_service = ConversationService(ConversationRepository())
message_service = ConversationMessageService(ConversationMessageRepository())


@router.get("", response_model=list[ConversationResponse])
async def list_conversations(
    current_user: CurrentUser,
    db: DbSession,
    agent_id: int | None = None,
):
    return await conversation_service.get_all_conversations(
        db, current_user.id, agent_id
    )


@router.get(
    "/{conversation_id}/messages",
    response_model=list[ConversationMessageResponse],
)
async def list_conversation_messages(
    conversation_id: int,
    current_user: CurrentUser,
    db: DbSession,
):
    await conversation_service.get_conversation(db, conversation_id, current_user.id)
    return await message_service.get_recent_conversation_messages(
        db, conversation_id, limit=100
    )
