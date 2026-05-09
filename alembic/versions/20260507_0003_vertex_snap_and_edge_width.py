"""vertex snap radius and edge corridor width

Revision ID: 20260507_0003
Revises: 20260506_0002
Create Date: 2026-05-07
"""

from typing import Sequence, Union

from alembic import op

revision: str = "20260507_0003"
down_revision: Union[str, None] = "20260506_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE nav_vertices
        ADD COLUMN IF NOT EXISTS snap_radius DOUBLE PRECISION NOT NULL DEFAULT 1.0;
        """
    )
    op.execute(
        """
        ALTER TABLE nav_edges
        ADD COLUMN IF NOT EXISTS corridor_width DOUBLE PRECISION NOT NULL DEFAULT 1.0;
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE nav_edges DROP COLUMN IF EXISTS corridor_width;")
    op.execute("ALTER TABLE nav_vertices DROP COLUMN IF EXISTS snap_radius;")
