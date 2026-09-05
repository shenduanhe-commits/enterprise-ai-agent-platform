from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base


class Tool(Base):
    __tablename__ = "tool"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    schema: Mapped[dict] = mapped_column(JSONB, nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    mcp_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    requires_hitl: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    agent_links: Mapped[list[AgentTool]] = relationship(
        back_populates="tool",
        cascade="all, delete-orphan",
    )


class AgentTool(Base):
    __tablename__ = "agent_tool"
    __table_args__ = (UniqueConstraint("agent_id", "tool_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    agent_id: Mapped[int] = mapped_column(
        ForeignKey("agent.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tool_id: Mapped[int] = mapped_column(
        ForeignKey("tool.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    tool: Mapped[Tool] = relationship(back_populates="agent_links")
