from fastapi import APIRouter

from app.core.dependencies import CurrentUser, DbSession
from app.repositories.agent_repository import AgentRepository
from app.repositories.tool_repository import ToolRepository
from app.schemas.tool import AgentToolsUpdate, ToolResponse
from app.services.tool_service import ToolService

router = APIRouter(tags=["Tools"])

service = ToolService(ToolRepository(), AgentRepository())


@router.get("/tools", response_model=list[ToolResponse])
async def list_tools(current_user: CurrentUser, db: DbSession):
    _ = current_user
    rows = await service.list_tools(db)
    return [ToolResponse.model_validate(row) for row in rows]


@router.put("/agents/{agent_id}/tools", response_model=list[int])
async def bind_agent_tools(
    agent_id: int,
    body: AgentToolsUpdate,
    current_user: CurrentUser,
    db: DbSession,
):
    return await service.bind_agent_tools(
        db,
        agent_id=agent_id,
        user_id=current_user.id,
        tool_ids=body.tool_ids,
    )
