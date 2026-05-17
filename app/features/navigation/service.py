import math

from app.features.ai.dto import RouteNarrationInput
from app.features.ai.service import AIRouteNarrationService
from app.features.navigation.dto import VertexDTO
from app.features.navigation.repository import NavigationRepository
from app.features.navigation.schemas import (
    NavigationInstructionsResponse,
    NavigationRouteRequest,
    NavigationRouteResponse,
    RouteVertex,
    VertexItem,
    VerticesListResponse,
)


class NavigationService:
    def __init__(self, repository: NavigationRepository, narrator: AIRouteNarrationService) -> None:
        self.repository = repository
        self.narrator = narrator

    async def list_vertices(self) -> VerticesListResponse:
        rows = await self.repository.get_rooms()
        items = [VertexItem(id=r.id, name=r.name, type=r.type, floor=r.floor, x=r.x, y=r.y) for r in rows]
        return VerticesListResponse(items=items, total=len(items))

    async def build_route(self, payload: NavigationRouteRequest) -> NavigationRouteResponse:
        source_id = await self.repository.get_nearest_vertex_id(
            x=payload.current_position.x,
            y=payload.current_position.y,
            floor=payload.current_position.floor,
        )
        target_id = await self.repository.get_nearest_vertex_id(
            x=payload.destination.x,
            y=payload.destination.y,
            floor=payload.destination.floor,
        )
        path_vertex_ids = await self.repository.get_route_vertex_ids(
            source_id=source_id, target_id=target_id
        )
        vertices = await self.repository.get_vertices_by_ids(path_vertex_ids)
        total_cost = self.repository.estimate_total_cost(vertices)
        instructions = await self.narrator.build_route_instructions(
            RouteNarrationInput(
                heading_degrees=payload.heading_degrees,
                total_distance=total_cost,
                vertices=[
                    {
                        "name": v.name,
                        "type": v.type,
                        "floor": v.floor,
                        "x": round(v.x, 2),
                        "y": round(v.y, 2),
                    }
                    for v in vertices
                ],
                segments=self._build_route_segments(vertices),
            )
        )

        return NavigationRouteResponse(
            path_vertex_ids=path_vertex_ids,
            total_cost=round(total_cost, 2),
            vertices=[
                RouteVertex(
                    id=v.id,
                    floor=v.floor,
                    x=v.x,
                    y=v.y,
                    snap_radius=v.snap_radius,
                )
                for v in vertices
            ],
            llm_instructions=instructions,
        )

    async def build_instructions(self, payload: NavigationRouteRequest) -> NavigationInstructionsResponse:
        source_id = await self.repository.get_nearest_vertex_id(
            x=payload.current_position.x,
            y=payload.current_position.y,
            floor=payload.current_position.floor,
        )
        target_id = await self.repository.get_nearest_vertex_id(
            x=payload.destination.x,
            y=payload.destination.y,
            floor=payload.destination.floor,
        )
        path_vertex_ids = await self.repository.get_route_vertex_ids(
            source_id=source_id, target_id=target_id
        )
        vertices = await self.repository.get_vertices_by_ids(path_vertex_ids)
        total_cost = self.repository.estimate_total_cost(vertices)
        steps = await self.narrator.build_route_instructions_list(
            RouteNarrationInput(
                heading_degrees=payload.heading_degrees,
                total_distance=total_cost,
                vertices=[
                    {
                        "name": v.name,
                        "type": v.type,
                        "floor": v.floor,
                        "x": round(v.x, 2),
                        "y": round(v.y, 2),
                    }
                    for v in vertices
                ],
                segments=self._build_route_segments(vertices),
            )
        )
        return NavigationInstructionsResponse(instructions=steps)

    @staticmethod
    def _build_route_segments(vertices: list[VertexDTO]) -> list[dict]:
        segments: list[dict] = []
        for index in range(1, len(vertices)):
            start = vertices[index - 1]
            end = vertices[index]
            dx = end.x - start.x
            dy = end.y - start.y
            distance = (dx * dx + dy * dy) ** 0.5
            bearing = (math.degrees(math.atan2(dx, dy)) + 360) % 360
            floor_change = end.floor - start.floor
            segments.append(
                {
                    "step": index,
                    "from_vertex_id": start.id,
                    "to_vertex_id": end.id,
                    "from_floor": start.floor,
                    "to_floor": end.floor,
                    "distance": round(distance, 2),
                    "bearing_degrees": round(bearing, 1),
                    "floor_change": floor_change,
                }
            )
        return segments
