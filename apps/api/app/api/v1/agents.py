from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.dependencies import AgentExecutorDep
from app.core.dependencies import CurrentUser, DbSession
from app.core.exceptions import EAAPException
from app.core.sse import format_sse
from app.repositories.agent_repository import AgentRepository
from app.repositories.conversation_repository import ConversationRepository
from app.schemas import AgentCreate, AgentResponse
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.conversation import ConversationCreate, ConversationResponse
from app.schemas.user import UserResponse
from app.services.agent_service import AgentService
from app.services.conversation_service import ConversationService

router = APIRouter(prefix="/agents", tags=["Agents"])

service = AgentService(AgentRepository())
conversation_service = ConversationService(ConversationRepository())


async def _get_agent_and_conversation(
    db: AsyncSession,
    agent_id: int,
    request: ChatRequest,
    current_user: UserResponse,
) -> tuple[AgentResponse, ConversationResponse]:
    agent = await service.get_agent(db, agent_id, current_user.id)

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

    return agent, conversation


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

    agent, conversation = await _get_agent_and_conversation(
        db, agent_id, request, current_user
    )

    return await executor.execute(
        db,
        agent,
        conversation,
        user_message=request.user_message,
        variables=request.variables,
    )


@router.post("/{agent_id}/chat/stream")
async def chat_with_agent_stream(
    agent_id: int,
    request: ChatRequest,
    current_user: CurrentUser,
    db: DbSession,
    executor: AgentExecutorDep,
):
    # 鉴权、找 Agent、建会话：必须在 StreamingResponse 之前完成。
    # 这样 401/404 仍走原来的 JSON 错误体，而不是塞进 SSE 流里。
    agent, conversation = await _get_agent_and_conversation(
        db, agent_id, request, current_user
    )

    async def generate():
        try:
            async for event, data in executor.execute_stream(
                db,
                agent,
                conversation,
                user_message=request.user_message,
                variables=request.variables,
            ):
                yield format_sse(event, data)
        except EAAPException as e:
            yield format_sse("error", {"code": e.code, "message": e.message})

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
