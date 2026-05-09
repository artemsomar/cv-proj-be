from pydantic import BaseModel, Field


class GraphVersionCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)


class GraphVersionResponse(BaseModel):
    id: int
    name: str
    status: str


class VertexUpsertItem(BaseModel):
    id: int
    floor: int = Field(ge=0)
    x: float
    y: float
    snap_radius: float = Field(default=1.0, gt=0)
    metadata: dict = Field(default_factory=dict)


class EdgeUpsertItem(BaseModel):
    id: int
    source: int
    target: int
    cost: float = Field(ge=0)
    reverse_cost: float = Field(ge=0)
    corridor_width: float = Field(default=1.0, gt=0)


class BatchUpsertVerticesRequest(BaseModel):
    vertices: list[VertexUpsertItem]


class BatchUpsertEdgesRequest(BaseModel):
    edges: list[EdgeUpsertItem]


class VertexResponse(BaseModel):
    id: int
    floor: int
    x: float
    y: float
    snap_radius: float
    metadata: dict


class EdgeResponse(BaseModel):
    id: int
    source: int
    target: int
    cost: float
    reverse_cost: float
    corridor_width: float


class BatchVerticesResponse(BaseModel):
    vertices: list[VertexResponse]


class BatchEdgesResponse(BaseModel):
    edges: list[EdgeResponse]


class PublishResponse(BaseModel):
    version_id: int
    status: str


class ValidateResponse(BaseModel):
    is_valid: bool
    errors: list[str]
