"""vertex name column

Revision ID: 20260517_0004
Revises: 20260507_0003
Create Date: 2026-05-17
"""

from typing import Sequence, Union

from alembic import op

revision: str = "20260517_0004"
down_revision: Union[str, None] = "20260507_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE nav_vertices
        ADD COLUMN IF NOT EXISTS name VARCHAR(256);
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE nav_vertices DROP COLUMN IF EXISTS name;")
