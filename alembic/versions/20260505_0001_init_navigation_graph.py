"""init navigation graph

Revision ID: 20260505_0001
Revises: None
Create Date: 2026-05-05
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260505_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgrouting;")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS nav_vertices (
            id INTEGER PRIMARY KEY,
            floor INTEGER NOT NULL,
            x DOUBLE PRECISION NOT NULL,
            y DOUBLE PRECISION NOT NULL,
            geom geometry(Point, 3857) NOT NULL,
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_nav_vertices_floor ON nav_vertices(floor);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_nav_vertices_geom ON nav_vertices USING GIST(geom);")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS nav_edges (
            id INTEGER PRIMARY KEY,
            source INTEGER NOT NULL REFERENCES nav_vertices(id) ON DELETE CASCADE,
            target INTEGER NOT NULL REFERENCES nav_vertices(id) ON DELETE CASCADE,
            cost DOUBLE PRECISION NOT NULL CHECK (cost >= 0),
            reverse_cost DOUBLE PRECISION NOT NULL CHECK (reverse_cost >= 0)
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_nav_edges_source ON nav_edges(source);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_nav_edges_target ON nav_edges(target);")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS nav_edges;")
    op.execute("DROP TABLE IF EXISTS nav_vertices;")
