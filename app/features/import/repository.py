from sqlalchemy import and_, func, literal, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from .schemas import EdgeUpsertItem, VertexUpsertItem
from app.features.navigation.models import GraphVersion, NavEdge, NavVertex


class ImportRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_version(self, *, name: str) -> GraphVersion:
        version = GraphVersion(name=name, status="draft")
        self.db.add(version)
        await self.db.flush()
        return version

    async def get_version(self, *, version_id: int) -> GraphVersion | None:
        return await self.db.get(GraphVersion, version_id)

    async def clone_version(self, *, source: GraphVersion, cloned_name: str) -> GraphVersion:
        clone = GraphVersion(name=cloned_name, status="draft")
        self.db.add(clone)
        await self.db.flush()

        await self.db.execute(
            insert(NavVertex).from_select(
                ["id", "version_id", "floor", "x", "y", "snap_radius", "geom", "metadata"],
                select(
                    NavVertex.id,
                    literal(clone.id),
                    NavVertex.floor,
                    NavVertex.x,
                    NavVertex.y,
                    NavVertex.snap_radius,
                    NavVertex.geom,
                    NavVertex.props,
                ).where(NavVertex.version_id == source.id),
            )
        )
        await self.db.execute(
            insert(NavEdge).from_select(
                ["id", "version_id", "source", "target", "cost", "reverse_cost", "corridor_width"],
                select(
                    NavEdge.id,
                    literal(clone.id),
                    NavEdge.source,
                    NavEdge.target,
                    NavEdge.cost,
                    NavEdge.reverse_cost,
                    NavEdge.corridor_width,
                ).where(NavEdge.version_id == source.id),
            )
        )
        return clone

    async def upsert_vertices(
        self, *, version_id: int, vertices: list[VertexUpsertItem]
    ) -> list[NavVertex]:
        if not vertices:
            return []

        rows = [
            {
                "id": item.id,
                "version_id": version_id,
                "floor": item.floor,
                "x": item.x,
                "y": item.y,
                "snap_radius": item.snap_radius,
                "geom": func.ST_SetSRID(func.ST_MakePoint(item.x, item.y), 3857),
                "props": item.metadata,
            }
            for item in vertices
        ]
        stmt = insert(NavVertex).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=[NavVertex.version_id, NavVertex.id],
            set_={
                "floor": stmt.excluded.floor,
                "x": stmt.excluded.x,
                "y": stmt.excluded.y,
                "snap_radius": stmt.excluded.snap_radius,
                "geom": stmt.excluded.geom,
                NavVertex.props: stmt.excluded.metadata,
            },
        )
        await self.db.execute(stmt)
        return await self.get_vertices_by_ids(
            version_id=version_id, vertex_ids=[item.id for item in vertices]
        )

    async def upsert_edges(self, *, version_id: int, edges: list[EdgeUpsertItem]) -> list[NavEdge]:
        if not edges:
            return []

        rows = [
            {
                "id": item.id,
                "version_id": version_id,
                "source": item.source,
                "target": item.target,
                "cost": item.cost,
                "reverse_cost": item.reverse_cost,
                "corridor_width": item.corridor_width,
            }
            for item in edges
        ]
        stmt = insert(NavEdge).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=[NavEdge.version_id, NavEdge.id],
            set_={
                "source": stmt.excluded.source,
                "target": stmt.excluded.target,
                "cost": stmt.excluded.cost,
                "reverse_cost": stmt.excluded.reverse_cost,
                "corridor_width": stmt.excluded.corridor_width,
            },
        )
        await self.db.execute(stmt)
        return await self.get_edges_by_ids(
            version_id=version_id, edge_ids=[item.id for item in edges]
        )

    async def get_vertices_by_ids(
        self, *, version_id: int, vertex_ids: list[int]
    ) -> list[NavVertex]:
        rows = (
            (
                await self.db.execute(
                    select(NavVertex).where(
                        NavVertex.version_id == version_id,
                        NavVertex.id.in_(vertex_ids),
                    )
                )
            )
            .scalars()
            .all()
        )
        by_id = {row.id: row for row in rows}
        return [by_id[vertex_id] for vertex_id in vertex_ids if vertex_id in by_id]

    async def get_edges_by_ids(self, *, version_id: int, edge_ids: list[int]) -> list[NavEdge]:
        rows = (
            (
                await self.db.execute(
                    select(NavEdge).where(
                        NavEdge.version_id == version_id,
                        NavEdge.id.in_(edge_ids),
                    )
                )
            )
            .scalars()
            .all()
        )
        by_id = {row.id: row for row in rows}
        return [by_id[edge_id] for edge_id in edge_ids if edge_id in by_id]

    async def validate_version(self, *, version_id: int) -> list[str]:
        errors: list[str] = []

        vertices_count = (
            await self.db.execute(
                select(func.count())
                .select_from(NavVertex)
                .where(NavVertex.version_id == version_id)
            )
        ).scalar_one()
        edges_count = (
            await self.db.execute(
                select(func.count()).select_from(NavEdge).where(NavEdge.version_id == version_id)
            )
        ).scalar_one()
        if vertices_count == 0:
            errors.append("Version has no vertices.")
        if edges_count == 0:
            errors.append("Version has no edges.")

        source_vertex = aliased(NavVertex)
        target_vertex = aliased(NavVertex)
        broken_edges_count = (
            await self.db.execute(
                select(func.count())
                .select_from(NavEdge)
                .outerjoin(
                    source_vertex,
                    and_(
                        source_vertex.version_id == NavEdge.version_id,
                        source_vertex.id == NavEdge.source,
                    ),
                )
                .outerjoin(
                    target_vertex,
                    and_(
                        target_vertex.version_id == NavEdge.version_id,
                        target_vertex.id == NavEdge.target,
                    ),
                )
                .where(NavEdge.version_id == version_id)
                .where((source_vertex.id.is_(None)) | (target_vertex.id.is_(None)))
            )
        ).scalar_one()
        if broken_edges_count > 0:
            errors.append(
                f"Found {broken_edges_count} edge(s) with missing source/target vertices."
            )

        return errors

    async def publish_version(self, *, version_id: int) -> None:
        await self.db.execute(
            update(GraphVersion).values(status="archived").where(GraphVersion.status == "published")
        )
        await self.db.execute(
            update(GraphVersion).values(status="published").where(GraphVersion.id == version_id)
        )
