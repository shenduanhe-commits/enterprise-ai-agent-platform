from fastapi import APIRouter

from app.ai.dependencies import AgentExecutorDep
from app.core.dependencies import CurrentUser, DbSession
from app.repositories.agent_repository import AgentRepository
from app.repositories.conversation_repository import ConversationRepository
from app.schemas import AgentCreate, AgentResponse
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.conversation import ConversationCreate, ConversationResponse
from app.services.agent_service import AgentService
from app.services.conversation_service import ConversationService

router = APIRouter(prefix="/agents", tags=["Agents"])

service = AgentService(AgentRepository())
conversation_service = ConversationService(ConversationRepository())


@router.post("", response_model=AgentResponse)
async def create_agent(
    agent_data: AgentCreate, current_user: CurrentUser, db: DbSession
):

    return await service.create_agent(db, agent_data, current_user.id)


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: int, current_user: CurrentUser, db: DbSession):

    return await service.get_agent(db, agent_id, current_user.id)


@router.get("", response_model=list[AgentResponse])
async def get_agents(current_user: CurrentUser, db: DbSession):

    return await service.get_agents(db, current_user.id)


@router.post("/{agent_id}/chat", response_model=ChatResponse)
async def chat_with_agent(
    agent_id: int,
    request: ChatRequest,
    current_user: CurrentUser,
    db: DbSession,
    executor: AgentExecutorDep,
):

    agent = await service.get_agent(db, agent_id, current_user.id)

    conversation: ConversationResponse | None = None

    if request.conversation_id is None:
        conversation = await conversation_service.create_conversation(
            db,
            ConversationCreate(
                agent_id=agent_id,
                user_id=current_user.id,
                name=request.user_message,
            ),
        )
    else:
        conversation = await conversation_service.get_conversation(
            db, request.conversation_id, current_user.id
        )

    return await executor.execute(
        db,
        agent,
        conversation,
        user_message=request.user_message,
        variables=request.variables,
    )
