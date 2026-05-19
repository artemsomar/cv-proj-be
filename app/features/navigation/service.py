import math

from app.features.ai.dto import RouteNarrationInput
from app.features.ai.service import AIRouteNarrationService
from app.features.navigation.dto import VertexDTO
from app.features.navigation.repository import NavigationRepository
from app.features.navigation.schemas import (
    InstructionStep,
    NavigationInstructionsResponse,
    NavigationRouteRequest,
    NavigationRouteResponse,
    RouteSegment,
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
        segments = self._build_route_segments(vertices, payload.heading_degrees)
        ai_segments = await self._build_ai_segments(segments, vertices, path_vertex_ids)
        instructions = await self.narrator.build_route_instructions(
            RouteNarrationInput(
                heading_degrees=payload.heading_degrees,
                total_distance=total_cost,
                vertices=[
                    {"name": v.name, "type": v.type, "floor": v.floor}
                    for v in vertices
                ],
                segments=ai_segments,
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
            segments=[RouteSegment(**seg) for seg in segments],
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
        segments = self._build_route_segments(vertices, payload.heading_degrees)
        ai_segments = await self._build_ai_segments(segments, vertices, path_vertex_ids)
        steps = await self.narrator.build_route_instructions_list(
            RouteNarrationInput(
                heading_degrees=payload.heading_degrees,
                total_distance=total_cost,
                vertices=[
                    {"name": v.name, "type": v.type, "floor": v.floor}
                    for v in vertices
                ],
                segments=ai_segments,
            )
        )
        return NavigationInstructionsResponse(
            instructions=[
                InstructionStep(text=text, direction=seg["direction"])
                for text, seg in zip(steps, segments)
            ],
            segments=[RouteSegment(**seg) for seg in segments],
        )

    async def _build_ai_segments(
        self,
        segments: list[dict],
        vertices: list[VertexDTO],
        path_vertex_ids: list[int],
    ) -> list[dict]:
        vertices_by_id = {v.id: v for v in vertices}
        ai_segments = []
        for s in segments:
            start = vertices_by_id[s["from_vertex_id"]]
            end = vertices_by_id[s["to_vertex_id"]]
            nearby = await self.repository.get_nearby_rooms_for_segment(
                ax=start.x, ay=start.y,
                bx=end.x, by=end.y,
                floor=s["from_floor"],
                exclude_ids=path_vertex_ids,
            )
            ai_segments.append({
                "step": s["step"],
                "direction": s["direction"],
                "from_floor": s["from_floor"],
                "to_floor": s["to_floor"],
                "rooms_left": [v.name for v, side in nearby if side == "left" and v.name],
                "rooms_right": [v.name for v, side in nearby if side == "right" and v.name],
            })
        return ai_segments

    @staticmethod
    def _calculate_direction(bearing: float, reference: float, floor_change: int) -> str:
        if floor_change > 0:
            return "stairs_up"
        if floor_change < 0:
            return "stairs_down"
        relative = (bearing - reference + 360) % 360
        if relative < 45 or relative >= 315:
            return "straight"
        if relative < 135:
            return "right"
        if relative < 225:
            return "back"
        return "left"

    @staticmethod
    def _build_route_segments(vertices: list[VertexDTO], heading_degrees: float) -> list[dict]:
        segments: list[dict] = []
        for index in range(1, len(vertices)):
            start = vertices[index - 1]
            end = vertices[index]
            dx = end.x - start.x
            dy = end.y - start.y
            distance = (dx * dx + dy * dy) ** 0.5
            bearing = (math.degrees(math.atan2(dx, dy)) + 360) % 360
            floor_change = end.floor - start.floor
            reference = heading_degrees if index == 1 else segments[-1]["bearing_degrees"]
            direction = NavigationService._calculate_direction(bearing, reference, floor_change)
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
                    "direction": direction,
                }
            )
        return segments
