"""create tool and agent_tool tables

Revision ID: c3f9a1d8e4b2
Revises: f8a2b6c1d4e0
Create Date: 2026-09-04

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c3f9a1d8e4b2"
down_revision: Union[str, Sequence[str], None] = "f8a2b6c1d4e0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tool",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("schema", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("source", sa.String(length=20), nullable=False),
        sa.Column("mcp_url", sa.String(length=500), nullable=True),
        sa.Column("requires_hitl", sa.Boolean(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "agent_tool",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("agent_id", sa.Integer(), nullable=False),
        sa.Column("tool_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agent.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tool_id"], ["tool.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("agent_id", "tool_id"),
    )
    op.create_index(
        op.f("ix_agent_tool_agent_id"), "agent_tool", ["agent_id"], unique=False
    )
    op.create_index(
        op.f("ix_agent_tool_tool_id"), "agent_tool", ["tool_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_agent_tool_tool_id"), table_name="agent_tool")
    op.drop_index(op.f("ix_agent_tool_agent_id"), table_name="agent_tool")
    op.drop_table("agent_tool")
    op.drop_table("tool")
