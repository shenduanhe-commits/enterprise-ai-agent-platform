from fastapi import APIRouter, HTTPException

from app.ai.dependencies import AgentExecutorDep
from app.core.dependencies import DbSession
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
async def create_agent(agent_data: AgentCreate, db: DbSession):

    return await service.create_agent(db, agent_data)


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: int, db: DbSession):

    agent = await service.get_agent(db, agent_id)

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return agent


@router.get("", response_model=list[AgentResponse])
async def get_agents(db: DbSession):

    return await service.get_agents(db)


@router.post("/{agent_id}/chat", response_model=ChatResponse)
async def chat_with_agent(
    agent_id: int, request: ChatRequest, db: DbSession, executor: AgentExecutorDep
):

    agent = await service.get_agent(db, agent_id)

    conversation: ConversationResponse | None = None

    if request.conversation_id is None:
        conversation = await conversation_service.create_conversation(
            db,
            ConversationCreate(
                agent_id=agent_id,
                user_id=request.user_id,
                name=request.user_message,
            ),
        )
    else:
        conversation = await conversation_service.get_conversation(
            db, request.conversation_id
        )

    result = await executor.execute(
        db,
        agent,
        conversation,
        user_message=request.user_message,
        variables=request.variables,
    )

    return result
