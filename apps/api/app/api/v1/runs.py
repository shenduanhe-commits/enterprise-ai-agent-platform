from fastapi import APIRouter

from app.ai.dependencies import AgentExecutorDep
from app.core.dependencies import CurrentUser, DbSession
from app.repositories.agent_repository import AgentRepository
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.run_span_repository import RunSpanRepository
from app.schemas.chat import ChatResponse
from app.schemas.run import ResumeRequest, RunResponse, RunSpanResponse
from app.services.agent_service import AgentService
from app.services.conversation_service import ConversationService
from app.services.run_span_service import RunSpanService

router = APIRouter(prefix="/runs", tags=["Runs"])

conversation_service = ConversationService(ConversationRepository())
agent_service = AgentService(AgentRepository())
span_service = RunSpanService(RunSpanRepository())


@router.get("/{run_id}", response_model=RunResponse)
async def get_run(
    run_id: int,
    current_user: CurrentUser,
    db: DbSession,
    executor: AgentExecutorDep,
):
    conversation = await conversation_service.get_conversation(
        db, run_id, current_user.id
    )
    agent = await agent_service.get_agent(
        db, conversation.agent_id, current_user.id
    )
    status = await executor.get_run_status(agent, conversation)
    return RunResponse(
        run_id=str(run_id),
        status=status["status"],
        pending=status.get("pending"),
    )


@router.post("/{run_id}/resume", response_model=ChatResponse)
async def resume_run(
    run_id: int,
    body: ResumeRequest,
    current_user: CurrentUser,
    db: DbSession,
    executor: AgentExecutorDep,
):
    conversation = await conversation_service.get_conversation(
        db, run_id, current_user.id
    )
    agent = await agent_service.get_agent(
        db, conversation.agent_id, current_user.id
    )
    return await executor.resume(
        db,
        agent,
        conversation,
        [item.model_dump() for item in body.decisions],
    )


@router.get("/{run_id}/spans", response_model=list[RunSpanResponse])
async def list_run_spans(
    run_id: int,
    current_user: CurrentUser,
    db: DbSession,
):
    await conversation_service.get_conversation(db, run_id, current_user.id)
    return await span_service.list_spans(db, run_id)
