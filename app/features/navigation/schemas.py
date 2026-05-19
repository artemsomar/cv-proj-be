from typing import Literal

from pydantic import BaseModel, Field


class UserPosition(BaseModel):
    x: float
    y: float
    floor: int = Field(ge=0)


class Destination(BaseModel):
    x: float
    y: float
    floor: int = Field(ge=0)


class NavigationRouteRequest(BaseModel):
    current_position: UserPosition
    heading_degrees: float = Field(ge=0, lt=360)
    destination: Destination


class RouteVertex(BaseModel):
    id: int
    floor: int
    x: float
    y: float
    snap_radius: float


class RouteSegment(BaseModel):
    step: int
    from_vertex_id: int
    to_vertex_id: int
    from_floor: int
    to_floor: int
    distance: float
    bearing_degrees: float
    floor_change: int
    direction: Literal["straight", "left", "right", "back", "stairs_up", "stairs_down"]


class NavigationRouteResponse(BaseModel):
    path_vertex_ids: list[int]
    total_cost: float
    vertices: list[RouteVertex]
    segments: list[RouteSegment]
    llm_instructions: str


class InstructionStep(BaseModel):
    text: str
    direction: Literal["straight", "left", "right", "back", "stairs_up", "stairs_down"]


class NavigationInstructionsResponse(BaseModel):
    instructions: list[InstructionStep]
    segments: list[RouteSegment]


class VertexItem(BaseModel):
    id: int
    name: str | None
    type: str | None
    floor: int
    x: float
    y: float


class VerticesListResponse(BaseModel):
    items: list[VertexItem]
    total: int
