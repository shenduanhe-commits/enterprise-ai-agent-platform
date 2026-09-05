from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.tools import BUILTIN_TOOLS
from app.ai.tools.base import BaseTool
from app.core.exceptions import BusinessException, NotFoundException
from app.models.tool import Tool
from app.repositories.agent_repository import AgentRepository
from app.repositories.tool_repository import ToolRepository


@dataclass
class CatalogRow:
    name: str
    description: str
    schema: dict
    source: str
    mcp_url: str | None
    requires_hitl: bool
    enabled: bool = True


class ToolService:
    def __init__(
        self,
        tools: ToolRepository,
        agents: AgentRepository,
    ):
        self.tools = tools
        self.agents = agents

    async def sync_catalog(self, db: AsyncSession, mcp_tools: list[BaseTool]) -> int:
        rows = _builtin_rows() + [_mcp_row(tool) for tool in mcp_tools]
        for row in rows:
            await self.tools.upsert(
                db,
                name=row.name,
                description=row.description,
                schema=row.schema,
                source=row.source,
                mcp_url=row.mcp_url,
                requires_hitl=row.requires_hitl,
                enabled=row.enabled,
            )
        await self.tools.disable_missing_mcp(db, [tool.name for tool in mcp_tools])
        await db.commit()
        return len(rows)

    async def list_tools(self, db: AsyncSession) -> list[Tool]:
        return await self.tools.list_all(db)

    async def bind_agent_tools(
        self,
        db: AsyncSession,
        *,
        agent_id: int,
        user_id: int,
        tool_ids: list[int],
    ) -> list[int]:
        agent = await self.agents.get_by_id(db, agent_id, user_id)
        if not agent:
            raise NotFoundException("智能体不存在")
        unique_ids = list(dict.fromkeys(tool_ids))
        found = await self.tools.list_by_ids(db, unique_ids)
        if len(found) != len(unique_ids):
            raise BusinessException("工具不存在")
        await self.tools.replace_agent_tools(db, agent_id, unique_ids)
        await db.commit()
        return unique_ids

    async def selected_names_for_agent(
        self, db: AsyncSession, agent_id: int
    ) -> list[str] | None:
        if not await self.tools.agent_has_bindings(db, agent_id):
            return None
        return await self.tools.list_bound_enabled_names(db, agent_id)


def _builtin_rows() -> list[CatalogRow]:
    return [
        CatalogRow(
            name=tool.name,
            description=tool.description,
            schema=tool.schema,
            source="builtin",
            mcp_url=None,
            requires_hitl=bool(getattr(tool, "requires_approval", False)),
        )
        for tool in BUILTIN_TOOLS
    ]


def _mcp_row(tool: BaseTool) -> CatalogRow:
    return CatalogRow(
        name=tool.name,
        description=tool.description,
        schema=tool.schema,
        source="mcp",
        mcp_url=getattr(tool, "mcp_url", None),
        requires_hitl=bool(getattr(tool, "requires_approval", False)),
    )
