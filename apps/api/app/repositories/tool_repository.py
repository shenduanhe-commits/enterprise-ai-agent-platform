from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tool import AgentTool, Tool


class ToolRepository:
    async def upsert(
        self,
        db: AsyncSession,
        *,
        name: str,
        description: str,
        schema: dict,
        source: str,
        mcp_url: str | None,
        requires_hitl: bool,
        enabled: bool,
    ) -> None:
        stmt = insert(Tool).values(
            name=name,
            description=description,
            schema=schema,
            source=source,
            mcp_url=mcp_url,
            requires_hitl=requires_hitl,
            enabled=enabled,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[Tool.name],
            set_={
                "description": stmt.excluded.description,
                "schema": stmt.excluded.schema,
                "source": stmt.excluded.source,
                "mcp_url": stmt.excluded.mcp_url,
                "requires_hitl": stmt.excluded.requires_hitl,
                "enabled": stmt.excluded.enabled,
            },
        )
        await db.execute(stmt)

    async def disable_missing_mcp(self, db: AsyncSession, present_names: list[str]) -> None:
        stmt = update(Tool).where(Tool.source == "mcp")
        if present_names:
            stmt = stmt.where(Tool.name.notin_(present_names))
        await db.execute(stmt.values(enabled=False))

    async def list_all(self, db: AsyncSession) -> list[Tool]:
        result = await db.execute(select(Tool).order_by(Tool.id))
        return list(result.scalars().all())

    async def list_by_ids(self, db: AsyncSession, tool_ids: list[int]) -> list[Tool]:
        if not tool_ids:
            return []
        result = await db.execute(select(Tool).where(Tool.id.in_(tool_ids)))
        return list(result.scalars().all())

    async def agent_has_bindings(self, db: AsyncSession, agent_id: int) -> bool:
        result = await db.execute(
            select(AgentTool.id).where(AgentTool.agent_id == agent_id).limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def list_bound_enabled_names(
        self, db: AsyncSession, agent_id: int
    ) -> list[str]:
        result = await db.execute(
            select(Tool.name)
            .join(AgentTool, AgentTool.tool_id == Tool.id)
            .where(AgentTool.agent_id == agent_id, Tool.enabled.is_(True))
        )
        return list(result.scalars().all())

    async def replace_agent_tools(
        self, db: AsyncSession, agent_id: int, tool_ids: list[int]
    ) -> None:
        await db.execute(delete(AgentTool).where(AgentTool.agent_id == agent_id))
        for tool_id in tool_ids:
            db.add(AgentTool(agent_id=agent_id, tool_id=tool_id))
