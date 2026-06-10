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
    NearestVertexRequest,
    NearestVertexResponse,
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
        items = [VertexItem(id=r.id, name=r.name, type=r.type, floor=r.floor + 1, x=r.x, y=r.y) for r in rows]
        return VerticesListResponse(items=items, total=len(items))

    async def find_nearest_vertex(self, payload: NearestVertexRequest) -> NearestVertexResponse:
        result = await self.repository.get_nearest_vertex(
            x=payload.x, y=payload.y, floor=payload.floor - 1
        )
        v = result.vertex
        return NearestVertexResponse(
            id=v.id,
            name=v.name,
            type=v.type,
            floor=v.floor + 1,
            x=v.x,
            y=v.y,
            snap_radius=v.snap_radius,
            distance=round(result.distance, 4),
        )

    async def build_route(self, payload: NavigationRouteRequest) -> NavigationRouteResponse:
        source_id = await self.repository.get_nearest_vertex_id(
            x=payload.current_position.x,
            y=payload.current_position.y,
            floor=payload.current_position.floor - 1,
        )
        target_id = await self.repository.get_nearest_vertex_id(
            x=payload.destination.x,
            y=payload.destination.y,
            floor=payload.destination.floor - 1,
        )
        path_vertex_ids = await self.repository.get_route_vertex_ids(
            source_id=source_id, target_id=target_id
        )
        vertices = await self.repository.get_vertices_by_ids(path_vertex_ids)
        total_cost = self.repository.estimate_total_cost(vertices)
        segments = self._build_route_segments(vertices, payload.heading_degrees)
        ai_segments = await self._build_ai_segments(segments, vertices, path_vertex_ids)
        _, merged_ai = self._merge_straight_segments(segments, ai_segments)
        instructions = await self.narrator.build_route_instructions(
            RouteNarrationInput(
                heading_degrees=payload.heading_degrees,
                total_distance=total_cost,
                vertices=[
                    {"name": v.name, "type": v.type, "floor": v.floor + 1}
                    for v in vertices
                ],
                segments=merged_ai,
            )
        )

        return NavigationRouteResponse(
            path_vertex_ids=path_vertex_ids,
            total_cost=round(total_cost, 2),
            vertices=[
                RouteVertex(
                    id=v.id,
                    floor=v.floor + 1,
                    x=v.x,
                    y=v.y,
                    snap_radius=v.snap_radius,
                )
                for v in vertices
            ],
            segments=[RouteSegment(**{**seg, "from_floor": seg["from_floor"] + 1, "to_floor": seg["to_floor"] + 1}) for seg in segments],
            llm_instructions=instructions,
        )

    async def build_instructions(self, payload: NavigationRouteRequest) -> NavigationInstructionsResponse:
        source_id = await self.repository.get_nearest_vertex_id(
            x=payload.current_position.x,
            y=payload.current_position.y,
            floor=payload.current_position.floor - 1,
        )
        target_id = await self.repository.get_nearest_vertex_id(
            x=payload.destination.x,
            y=payload.destination.y,
            floor=payload.destination.floor - 1,
        )
        path_vertex_ids = await self.repository.get_route_vertex_ids(
            source_id=source_id, target_id=target_id
        )
        vertices = await self.repository.get_vertices_by_ids(path_vertex_ids)
        total_cost = self.repository.estimate_total_cost(vertices)
        segments = self._build_route_segments(vertices, payload.heading_degrees)
        ai_segments = await self._build_ai_segments(segments, vertices, path_vertex_ids)
        merged_segments, merged_ai = self._merge_straight_segments(segments, ai_segments)
        steps = await self.narrator.build_route_instructions_list(
            RouteNarrationInput(
                heading_degrees=payload.heading_degrees,
                total_distance=total_cost,
                vertices=[
                    {"name": v.name, "type": v.type, "floor": v.floor + 1}
                    for v in vertices
                ],
                segments=merged_ai,
            )
        )
        return NavigationInstructionsResponse(
            instructions=[
                InstructionStep(text=text, direction=seg["direction"])
                for text, seg in zip(steps, merged_segments)
            ],
            segments=[
                RouteSegment(**{**seg, "from_floor": seg["from_floor"] + 1, "to_floor": seg["to_floor"] + 1})
                for seg in merged_segments
            ],
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
            destination = end.name if end.type in ("room", "exit") else None

            def _near_end(v: VertexDTO) -> bool:
                return ((v.x - end.x) ** 2 + (v.y - end.y) ** 2) ** 0.5 <= end.snap_radius

            ai_segments.append({
                "step": s["step"],
                "direction": s["direction"],
                "from_floor": s["from_floor"],
                "to_floor": s["to_floor"],
                "destination": destination,
                "rooms_left": [v.name for v, side in nearby if side == "left" and v.name and not _near_end(v)],
                "rooms_right": [v.name for v, side in nearby if side == "right" and v.name and not _near_end(v)],
            })
        return ai_segments

    @staticmethod
    def _merge_straight_segments(
        segments: list[dict], ai_segments: list[dict]
    ) -> tuple[list[dict], list[dict]]:
        def _to_nearby(ai_seg: dict) -> list[dict]:
            return (
                [{"name": r, "side": "left"} for r in ai_seg.get("rooms_left", [])]
                + [{"name": r, "side": "right"} for r in ai_seg.get("rooms_right", [])]
            )

        merged_segs: list[dict] = []
        merged_ai: list[dict] = []
        i = 0
        while i < len(segments):
            seg = segments[i]
            ai_seg = ai_segments[i]
            if seg["direction"] != "straight":
                merged_segs.append(seg)
                merged_ai.append({**ai_seg, "nearby_rooms": _to_nearby(ai_seg)})
                i += 1
                continue
            group_s = [seg]
            group_ai = [ai_seg]
            j = i + 1
            while (
                j < len(segments)
                and segments[j]["direction"] == "straight"
                and segments[j]["from_floor"] == seg["from_floor"]
            ):
                group_s.append(segments[j])
                group_ai.append(ai_segments[j])
                j += 1
            if len(group_s) == 1:
                merged_segs.append(seg)
                merged_ai.append(ai_seg)
            else:
                first, last = group_s[0], group_s[-1]
                merged_segs.append({
                    "step": first["step"],
                    "from_vertex_id": first["from_vertex_id"],
                    "to_vertex_id": last["to_vertex_id"],
                    "from_floor": first["from_floor"],
                    "to_floor": last["to_floor"],
                    "distance": round(sum(s["distance"] for s in group_s), 2),
                    "bearing_degrees": last["bearing_degrees"],
                    "floor_change": last["to_floor"] - first["from_floor"],
                    "direction": "straight",
                })
                def _unique(items: list) -> list:
                    seen: set = set()
                    return [x for x in items if not (x in seen or seen.add(x))]  # type: ignore[func-returns-value]
                def _sample(items: list, n: int = 3) -> list:
                    if len(items) <= n:
                        return items
                    step = (len(items) - 1) / (n - 1)
                    return [items[round(i * step)] for i in range(n)]
                rooms_left = _sample(_unique([r for s in group_ai for r in s["rooms_left"]]))
                rooms_right = _sample(_unique([r for s in group_ai for r in s["rooms_right"]]))
                nearby = (
                    [{"name": r, "side": "left"} for r in rooms_left]
                    + [{"name": r, "side": "right"} for r in rooms_right]
                )
                merged_ai.append({
                    "step": group_ai[0]["step"],
                    "direction": "straight",
                    "from_floor": group_ai[0]["from_floor"],
                    "to_floor": group_ai[-1]["to_floor"],
                    "destination": group_ai[-1].get("destination"),
                    "nearby_rooms": nearby,
                })
            i = j

        # Drop empty straight segments that immediately follow stairs
        final_segs: list[dict] = []
        final_ai: list[dict] = []
        for idx, (seg, ai_seg) in enumerate(zip(merged_segs, merged_ai)):
            is_empty_straight = (
                seg["direction"] == "straight"
                and not ai_seg.get("nearby_rooms")
                and not ai_seg.get("destination")
            )
            prev_is_stairs = idx > 0 and merged_segs[idx - 1]["direction"] in ("stairs_up", "stairs_down")
            if is_empty_straight and prev_is_stairs:
                continue
            final_segs.append(seg)
            final_ai.append(ai_seg)
        return final_segs, final_ai

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
            if index == 1:
                reference = heading_degrees
            elif segments[-1]["direction"] in ("stairs_up", "stairs_down"):
                reference = (segments[-1]["bearing_degrees"] + 180) % 360
            else:
                reference = segments[-1]["bearing_degrees"]
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
