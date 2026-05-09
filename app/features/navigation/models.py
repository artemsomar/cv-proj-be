from geoalchemy2 import Geometry
from sqlalchemy import Float, ForeignKey, Integer, PrimaryKeyConstraint, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class GraphVersion(Base):
    __tablename__ = "graph_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, index=True, default="draft")


class NavVertex(Base):
    __tablename__ = "nav_vertices"
    __table_args__ = (PrimaryKeyConstraint("version_id", "id", name="pk_nav_vertices"),)

    id: Mapped[int] = mapped_column(Integer, nullable=False)
    version_id: Mapped[int] = mapped_column(
        ForeignKey("graph_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    floor: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    x: Mapped[float] = mapped_column(Float, nullable=False)
    y: Mapped[float] = mapped_column(Float, nullable=False)
    snap_radius: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    geom: Mapped[str] = mapped_column(Geometry(geometry_type="POINT", srid=3857), nullable=False)
    props: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)


class NavEdge(Base):
    __tablename__ = "nav_edges"
    __table_args__ = (PrimaryKeyConstraint("version_id", "id", name="pk_nav_edges"),)

    id: Mapped[int] = mapped_column(Integer, nullable=False)
    version_id: Mapped[int] = mapped_column(
        ForeignKey("graph_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    target: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    cost: Mapped[float] = mapped_column(Float, nullable=False)
    reverse_cost: Mapped[float] = mapped_column(Float, nullable=False)
    corridor_width: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
