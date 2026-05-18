"""vertex type column

Revision ID: 20260517_0005
Revises: 20260517_0004
Create Date: 2026-05-17
"""

from typing import Sequence, Union

from alembic import op

revision: str = "20260517_0005"
down_revision: Union[str, None] = "20260517_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE nav_vertices
        ADD COLUMN IF NOT EXISTS type VARCHAR(64);
        """
    )
    op.execute("ALTER TABLE nav_vertices DROP COLUMN IF EXISTS metadata;")


def downgrade() -> None:
    op.execute("ALTER TABLE nav_vertices DROP COLUMN IF EXISTS type;")
    op.execute(
        """
        ALTER TABLE nav_vertices
        ADD COLUMN IF NOT EXISTS metadata JSONB NOT NULL DEFAULT '{}';
        """
    )
