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


class NavigationRouteResponse(BaseModel):
    path_vertex_ids: list[int]
    total_cost: float
    vertices: list[RouteVertex]
    llm_instructions: str


class VertexItem(BaseModel):
    id: int
    name: str | None
    type: str | None


class VerticesListResponse(BaseModel):
    items: list[VertexItem]
    total: int
