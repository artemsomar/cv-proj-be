"""graph versioning

Revision ID: 20260506_0002
Revises: 20260505_0001
Create Date: 2026-05-06
"""

from typing import Sequence, Union

from alembic import op

revision: str = "20260506_0002"
down_revision: Union[str, None] = "20260505_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS graph_versions (
            id SERIAL PRIMARY KEY,
            name VARCHAR(128) NOT NULL UNIQUE,
            status VARCHAR(16) NOT NULL DEFAULT 'draft'
        );
        """
    )
    op.execute(
        """
        INSERT INTO graph_versions (name, status)
        VALUES ('initial-published', 'published')
        ON CONFLICT (name) DO NOTHING;
        """
    )

    op.execute("ALTER TABLE nav_edges DROP CONSTRAINT IF EXISTS nav_edges_source_fkey;")
    op.execute("ALTER TABLE nav_edges DROP CONSTRAINT IF EXISTS nav_edges_target_fkey;")

    op.execute("ALTER TABLE nav_vertices ADD COLUMN IF NOT EXISTS version_id INTEGER;")
    op.execute("UPDATE nav_vertices SET version_id = 1 WHERE version_id IS NULL;")
    op.execute("ALTER TABLE nav_vertices ALTER COLUMN version_id SET NOT NULL;")
    op.execute(
        """
        ALTER TABLE nav_vertices
        ADD CONSTRAINT fk_nav_vertices_version
        FOREIGN KEY (version_id) REFERENCES graph_versions(id) ON DELETE CASCADE;
        """
    )
    op.execute("ALTER TABLE nav_vertices DROP CONSTRAINT IF EXISTS nav_vertices_pkey;")
    op.execute(
        "ALTER TABLE nav_vertices ADD CONSTRAINT pk_nav_vertices PRIMARY KEY (version_id, id);"
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_nav_vertices_version_id ON nav_vertices(version_id);")

    op.execute("ALTER TABLE nav_edges ADD COLUMN IF NOT EXISTS version_id INTEGER;")
    op.execute("UPDATE nav_edges SET version_id = 1 WHERE version_id IS NULL;")
    op.execute("ALTER TABLE nav_edges ALTER COLUMN version_id SET NOT NULL;")
    op.execute(
        """
        ALTER TABLE nav_edges
        ADD CONSTRAINT fk_nav_edges_version
        FOREIGN KEY (version_id) REFERENCES graph_versions(id) ON DELETE CASCADE;
        """
    )
    op.execute("ALTER TABLE nav_edges DROP CONSTRAINT IF EXISTS nav_edges_pkey;")
    op.execute("ALTER TABLE nav_edges ADD CONSTRAINT pk_nav_edges PRIMARY KEY (version_id, id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_nav_edges_version_id ON nav_edges(version_id);")


def downgrade() -> None:
    op.execute("ALTER TABLE nav_edges DROP CONSTRAINT IF EXISTS pk_nav_edges;")
    op.execute("ALTER TABLE nav_edges ADD CONSTRAINT nav_edges_pkey PRIMARY KEY (id);")
    op.execute("ALTER TABLE nav_edges DROP CONSTRAINT IF EXISTS fk_nav_edges_version;")
    op.execute("ALTER TABLE nav_edges DROP COLUMN IF EXISTS version_id;")

    op.execute("ALTER TABLE nav_vertices DROP CONSTRAINT IF EXISTS pk_nav_vertices;")
    op.execute("ALTER TABLE nav_vertices ADD CONSTRAINT nav_vertices_pkey PRIMARY KEY (id);")
    op.execute("ALTER TABLE nav_vertices DROP CONSTRAINT IF EXISTS fk_nav_vertices_version;")
    op.execute("ALTER TABLE nav_vertices DROP COLUMN IF EXISTS version_id;")
    op.execute(
        """
        ALTER TABLE nav_edges
        ADD CONSTRAINT nav_edges_source_fkey
        FOREIGN KEY (source) REFERENCES nav_vertices(id) ON DELETE CASCADE;
        """
    )
    op.execute(
        """
        ALTER TABLE nav_edges
        ADD CONSTRAINT nav_edges_target_fkey
        FOREIGN KEY (target) REFERENCES nav_vertices(id) ON DELETE CASCADE;
        """
    )

    op.execute("DROP TABLE IF EXISTS graph_versions;")
