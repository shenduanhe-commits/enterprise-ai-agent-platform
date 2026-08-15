from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.conversation import Conversation
    from app.models.prompt import Prompt
    from app.models.user import User


class AgentStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    ARCHIVED = "archived"


class Agent(Base):
    __tablename__ = "agent"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String(100), nullable=False)

    provider: Mapped[str] = mapped_column(String(100), nullable=False)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    model_name: Mapped[str] = mapped_column(String(100), nullable=False)

    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)

    created_by: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)

    creator: Mapped[User] = relationship(back_populates="agents")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50), default=AgentStatus.ACTIVE.value, nullable=False
    )
    prompts: Mapped[list[Prompt]] = relationship(
        back_populates="agent",
        cascade="all, delete-orphan",
    )
    conversations: Mapped[list[Conversation]] = relationship(back_populates="agent")
