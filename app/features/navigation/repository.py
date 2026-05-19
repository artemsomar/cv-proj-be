from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.navigation.dto import VertexDTO
from app.features.navigation.models import GraphVersion, NavVertex


class NavigationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_published_version_id(self) -> int:
        version_id = (
            await self.db.execute(
                select(GraphVersion.id).where(GraphVersion.status == "published").limit(1)
            )
        ).scalar_one_or_none()
        if version_id is None:
            raise ValueError("No published graph version found.")
        return int(version_id)

    async def get_nearest_vertex_id(self, *, x: float, y: float, floor: int) -> int:
        version_id = await self.get_published_version_id()
        point = func.ST_SetSRID(func.ST_MakePoint(x, y), 3857)
        query: Select = (
            select(NavVertex.id)
            .where(NavVertex.version_id == version_id, NavVertex.floor == floor)
            .order_by(func.ST_Distance(NavVertex.geom, point))
            .limit(1)
        )
        result = (await self.db.execute(query)).scalar_one_or_none()
        if result is None:
            raise ValueError(f"No vertices found on floor={floor}")
        return int(result)

    async def get_route_vertex_ids(self, *, source_id: int, target_id: int) -> list[int]:
        version_id = await self.get_published_version_id()
        dijkstra_rows = func.pgr_dijkstra(
            f"SELECT id, source, target, cost, reverse_cost FROM nav_edges WHERE version_id = {version_id}",
            source_id,
            target_id,
            False,
        ).table_valued("seq", "path_seq", "node", "edge", "cost", "agg_cost")
        query: Select = (
            select(dijkstra_rows.c.node)
            .where(dijkstra_rows.c.node != -1)
            .order_by(dijkstra_rows.c.seq)
        )
        result = await self.db.execute(query)
        return [int(row.node) for row in result]

    async def get_vertices_by_ids(self, vertex_ids: list[int]) -> list[VertexDTO]:
        if not vertex_ids:
            return []
        version_id = await self.get_published_version_id()

        query: Select = select(NavVertex).where(
            NavVertex.version_id == version_id, NavVertex.id.in_(vertex_ids)
        )
        rows = (await self.db.execute(query)).scalars().all()
        by_id = {
            int(row.id): VertexDTO(
                id=int(row.id),
                name=row.name,
                type=row.type,
                floor=int(row.floor),
                x=float(row.x),
                y=float(row.y),
                snap_radius=float(row.snap_radius),
            )
            for row in rows
        }
        return [by_id[vertex_id] for vertex_id in vertex_ids if vertex_id in by_id]

    async def get_nearby_rooms_for_segment(
        self,
        *,
        ax: float,
        ay: float,
        bx: float,
        by: float,
        floor: int,
        exclude_ids: list[int],
        radius: float = 10.0,
    ) -> list[tuple[VertexDTO, str]]:
        version_id = await self.get_published_version_id()
        line = func.ST_SetSRID(
            func.ST_MakeLine(func.ST_MakePoint(ax, ay), func.ST_MakePoint(bx, by)),
            3857,
        )
        filters = [
            NavVertex.version_id == version_id,
            NavVertex.floor == floor,
            NavVertex.type.in_(["room", "exit"]),
            func.ST_DWithin(NavVertex.geom, line, radius),
        ]
        if exclude_ids:
            filters.append(NavVertex.id.not_in(exclude_ids))
        rows = (await self.db.execute(select(NavVertex).where(*filters))).scalars().all()

        dx = bx - ax
        dy = by - ay
        result: list[tuple[VertexDTO, str]] = []
        for row in rows:
            cross = dx * (float(row.y) - ay) - dy * (float(row.x) - ax)
            side = "left" if cross > 0 else "right"
            result.append((
                VertexDTO(
                    id=int(row.id),
                    name=row.name,
                    type=row.type,
                    floor=int(row.floor),
                    x=float(row.x),
                    y=float(row.y),
                    snap_radius=float(row.snap_radius),
                ),
                side,
            ))
        return result

    async def get_rooms(self) -> list[NavVertex]:
        version_id = await self.get_published_version_id()
        query = (
            select(NavVertex)
            .where(NavVertex.version_id == version_id, NavVertex.type == "room")
            .order_by(NavVertex.id)
        )
        return list((await self.db.execute(query)).scalars().all())

    @staticmethod
    def estimate_total_cost(vertices: list[VertexDTO]) -> float:
        if len(vertices) < 2:
            return 0.0
        total = 0.0
        for idx in range(1, len(vertices)):
            dx = vertices[idx].x - vertices[idx - 1].x
            dy = vertices[idx].y - vertices[idx - 1].y
            total += (dx * dx + dy * dy) ** 0.5
        return total
