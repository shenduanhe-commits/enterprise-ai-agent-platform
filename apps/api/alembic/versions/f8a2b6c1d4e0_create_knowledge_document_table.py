"""create knowledge_document table

Revision ID: f8a2b6c1d4e0
Revises: e7c1d4a90b2f
Create Date: 2026-08-31

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f8a2b6c1d4e0"
down_revision: Union[str, Sequence[str], None] = "e7c1d4a90b2f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "knowledge_document",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("owner_user_id", sa.Integer(), nullable=False),
        sa.Column("agent_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("source_uri", sa.String(length=500), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["owner_user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["agent_id"], ["agent.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_knowledge_document_owner_user_id"),
        "knowledge_document",
        ["owner_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_knowledge_document_agent_id"),
        "knowledge_document",
        ["agent_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_knowledge_document_agent_id"), table_name="knowledge_document"
    )
    op.drop_index(
        op.f("ix_knowledge_document_owner_user_id"), table_name="knowledge_document"
    )
    op.drop_table("knowledge_document")
