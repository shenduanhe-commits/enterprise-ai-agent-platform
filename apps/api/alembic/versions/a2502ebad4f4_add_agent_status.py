"""add agent status

Revision ID: a2502ebad4f4
Revises: 123ba82433db
Create Date: 2026-08-04 20:09:17.939156

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a2502ebad4f4"
down_revision: str | Sequence[str] | None = "123ba82433db"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1) 先加可空列，避免已有行立刻违反 NOT NULL
    op.add_column("agents", sa.Column("status", sa.String(length=50), nullable=True))
    # 2) 回填旧数据
    op.execute("UPDATE agents SET status = 'active' WHERE status IS NULL")
    # 3) 再改为非空
    op.alter_column(
        "agents", "status", existing_type=sa.String(length=50), nullable=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("agents", "status")
